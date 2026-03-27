#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="/usr/bin/python3"
VENV_DIR="${PROJECT_ROOT}/.venv"
SKIP_APT=0
INCLUDE_VOICEINPUT=0

APT_PACKAGES=(
  git
  curl
  ca-certificates
  python3-venv
  python3-dev
  build-essential
  cmake
  pkg-config
  swig
  i2c-tools
  python3-picamera2
  libportaudio2
  portaudio19-dev
  libopenblas-dev
  liblapack-dev
)

OPTIONAL_CAMERA_APT_PACKAGES=(
  python3-libcamera
)

usage() {
  cat <<'EOF'
Usage: ./scripts/bootstrap-rpi-workspace.sh [--skip-apt] [--voiceinput]

Prepare the NinjaClawBot workspace on Raspberry Pi OS by:
1. Installing the required system packages with apt
2. Creating .venv with /usr/bin/python3 -m venv --system-site-packages
3. Running uv sync --active --extra dev (with system Python preference)

Options:
  --skip-apt    Skip the apt install step
  --voiceinput  Include the optional voiceinput extra during uv sync
  --help        Show this help message
EOF
}

log() {
  printf '\n[%s] %s\n' "bootstrap" "$1"
}

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    fail "Required command not found: $1"
  fi
}

assert_linux() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    fail "This bootstrap script is intended for Raspberry Pi OS or another Linux system."
  fi
}

assert_python_version() {
  "$PYTHON_BIN" - <<'PY'
import sys
if not ((3, 11) <= sys.version_info[:2] < (3, 14)):
    raise SystemExit("Expected /usr/bin/python3 to be Python 3.11–3.13 for NinjaClawBot.")
PY
}

venv_can_import_picamera2() {
  [[ -x "${VENV_DIR}/bin/python" ]] || return 1
  "${VENV_DIR}/bin/python" -c "import libcamera, picamera2" >/dev/null 2>&1
}

list_available_optional_packages() {
  local -a packages=("$@")
  local package
  for package in "${packages[@]}"; do
    if apt-cache show "${package}" >/dev/null 2>&1; then
      printf '%s\n' "${package}"
    fi
  done
}

install_system_packages() {
  if (( SKIP_APT )); then
    log "Skipping apt install step."
    return
  fi

  require_command sudo
  require_command apt
  require_command apt-cache
  log "Installing required Raspberry Pi system packages."
  sudo apt update

  local packages=("${APT_PACKAGES[@]}")
  local optional_package
  while IFS= read -r optional_package; do
    [[ -n "${optional_package}" ]] || continue
    packages+=("${optional_package}")
  done < <(list_available_optional_packages "${OPTIONAL_CAMERA_APT_PACKAGES[@]}")

  sudo apt install -y "${packages[@]}"
}

ensure_venv() {
  log "Recreating workspace virtual environment with system Python."
  rm -rf "${VENV_DIR}"
  (
    cd "${PROJECT_ROOT}"
    "${PYTHON_BIN}" -m venv --system-site-packages "${VENV_DIR}"
  )
  if ! venv_can_import_picamera2; then
    local venv_output
    local system_output
    venv_output=$("${VENV_DIR}/bin/python" -c "import libcamera, picamera2" 2>&1 || true)
    system_output=$("${PYTHON_BIN}" -c "import libcamera, picamera2" 2>&1 || true)
    fail "Picamera2 is still not importable inside ${VENV_DIR}. .venv import output: ${venv_output}. /usr/bin/python3 import output: ${system_output}"
  fi
}

run_sync() {
  local sync_args=(--active --extra dev)
  if (( INCLUDE_VOICEINPUT )); then
    sync_args+=(--extra voiceinput)
  fi

  log "Syncing the NinjaClawBot workspace (using system Python)."
  (
    cd "${PROJECT_ROOT}"
    source "${VENV_DIR}/bin/activate"
    # Force uv to use the system Python interpreter so the venv retains
    # access to system site-packages (python3-picamera2, python3-libcamera).
    UV_PYTHON_PREFERENCE=system uv sync "${sync_args[@]}"
  )
}

ensure_system_site_packages() {
  log "Verifying system site-packages access in .venv."

  local CFG="${VENV_DIR}/pyvenv.cfg"
  if [[ -f "${CFG}" ]]; then
    if grep -q 'include-system-site-packages = false' "${CFG}" 2>/dev/null; then
      sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' "${CFG}"
      log "Re-enabled include-system-site-packages in pyvenv.cfg."
    elif ! grep -q 'include-system-site-packages' "${CFG}" 2>/dev/null; then
      echo 'include-system-site-packages = true' >> "${CFG}"
      log "Added include-system-site-packages to pyvenv.cfg."
    fi
  fi
}

run_health_checks() {
  log "Running camera readiness checks."
  (
    cd "${PROJECT_ROOT}"
    uv run pi5camera doctor
    uv run python -c "import ninjaclawbot, pi5camera, libcamera, picamera2, cv2; print('imports-ok')"
  )
}

main() {
  while (($# > 0)); do
    case "$1" in
      --skip-apt)
        SKIP_APT=1
        ;;
      --voiceinput)
        INCLUDE_VOICEINPUT=1
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        fail "Unknown argument: $1"
        ;;
    esac
    shift
  done

  assert_linux
  require_command uv

  if [[ ! -x "${PYTHON_BIN}" ]]; then
    fail "Expected Python interpreter not found: ${PYTHON_BIN}"
  fi

  assert_python_version
  install_system_packages
  ensure_venv
  run_sync
  ensure_system_site_packages
  run_health_checks

  log "Workspace bootstrap completed."
}

main "$@"
