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

usage() {
  cat <<'EOF'
Usage: ./scripts/bootstrap-rpi-workspace.sh [--skip-apt] [--voiceinput]

Prepare the NinjaClawBot workspace on Raspberry Pi OS by:
1. Installing the required system packages with apt
2. Creating .venv with /usr/bin/python3 -m venv --system-site-packages
3. Running uv sync --active --extra dev

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
if not ((3, 11) <= sys.version_info[:2] < (3, 13)):
    raise SystemExit("Expected /usr/bin/python3 to be Python 3.11 or 3.12 for NinjaClawBot.")
PY
}

venv_has_system_site_packages() {
  [[ -f "${VENV_DIR}/pyvenv.cfg" ]] && grep -Eq '^include-system-site-packages = true$' "${VENV_DIR}/pyvenv.cfg"
}

venv_uses_system_python() {
  [[ -x "${VENV_DIR}/bin/python" ]] || return 1
  "${VENV_DIR}/bin/python" - <<'PY' >/dev/null
import sys
raise SystemExit(0 if sys.base_prefix.startswith("/usr") else 1)
PY
}

venv_can_import_picamera2() {
  [[ -x "${VENV_DIR}/bin/python" ]] || return 1
  "${VENV_DIR}/bin/python" -c "import picamera2" >/dev/null 2>&1
}

ensure_venv() {
  local recreate=0

  if [[ ! -d "${VENV_DIR}" ]]; then
    recreate=1
    log "Creating workspace virtual environment."
  elif ! venv_has_system_site_packages; then
    recreate=1
    log "Recreating .venv so it inherits Raspberry Pi system packages."
  elif ! venv_uses_system_python; then
    recreate=1
    log "Recreating .venv so it uses /usr/bin/python3."
  elif ! venv_can_import_picamera2; then
    recreate=1
    log "Recreating .venv because Picamera2 is still not importable inside it."
  else
    log "Reusing existing compatible .venv."
  fi

  if (( recreate )); then
    rm -rf "${VENV_DIR}"
    (
      cd "${PROJECT_ROOT}"
      "${PYTHON_BIN}" -m venv --system-site-packages "${VENV_DIR}"
    )
  fi

  if ! venv_can_import_picamera2; then
    fail "Picamera2 is still not importable inside ${VENV_DIR}. Confirm that \`${PYTHON_BIN} -c 'import picamera2'\` works, then rerun this script."
  fi
}

install_system_packages() {
  if (( SKIP_APT )); then
    log "Skipping apt install step."
    return
  fi

  require_command sudo
  require_command apt
  log "Installing required Raspberry Pi system packages."
  sudo apt update
  sudo apt install -y "${APT_PACKAGES[@]}"
}

run_sync() {
  local sync_args=(--active --extra dev)
  if (( INCLUDE_VOICEINPUT )); then
    sync_args+=(--extra voiceinput)
  fi

  log "Syncing the NinjaClawBot workspace."
  (
    cd "${PROJECT_ROOT}"
    # Force uv to install into the verified .venv created above.
    source "${VENV_DIR}/bin/activate"
    uv sync "${sync_args[@]}"
  )
}

run_health_checks() {
  log "Running camera readiness checks."
  (
    cd "${PROJECT_ROOT}"
    "${VENV_DIR}/bin/python" -m pi5camera doctor
    "${VENV_DIR}/bin/python" -c "import ninjaclawbot, pi5camera, picamera2; print('imports-ok')"
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
  run_health_checks

  log "Workspace bootstrap completed."
}

main "$@"
