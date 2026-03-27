#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="/usr/bin/python3"
VENV_DIR="${PROJECT_ROOT}/.venv"
SKIP_APT=0

APT_PACKAGES=(
  python3-picamera2
  python3-venv
  python3-dev
  build-essential
  cmake
  pkg-config
  libopenblas-dev
  liblapack-dev
)

OPTIONAL_CAMERA_APT_PACKAGES=(
  python3-libcamera
)

OPTIONAL_RECOGNITION_APT_PACKAGES=(
  python3-scipy
  python3-dlib
  python3-face-recognition
  python3-face-recognition-models
)

RECOGNITION_PIP_FALLBACK=0

usage() {
  cat <<'EOF'
Usage: ./scripts/bootstrap-rpi-standalone.sh [--skip-apt]

Prepare standalone pi5camera on Raspberry Pi OS by:
1. Installing the required system packages with apt
2. Creating .venv with /usr/bin/python3 -m venv --system-site-packages
3. Running uv sync --active --extra dev

Options:
  --skip-apt   Skip the apt install step
  --help       Show this help message
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
    raise SystemExit("Expected /usr/bin/python3 to be Python 3.11 or 3.12 for pi5camera.")
PY
}

venv_can_import_picamera2() {
  [[ -x "${VENV_DIR}/bin/python" ]] || return 1
  "${VENV_DIR}/bin/python" -c "import libcamera, picamera2" >/dev/null 2>&1
}

venv_can_import_face_recognition() {
  [[ -x "${VENV_DIR}/bin/python" ]] || return 1
  "${VENV_DIR}/bin/python" -c "import face_recognition" >/dev/null 2>&1
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

system_python_can_import() {
  local import_code="$1"
  "${PYTHON_BIN}" -c "${import_code}" >/dev/null 2>&1
}

install_fallback_recognition_stack() {
  log "Installing the Python recognition fallback into .venv."
  (
    cd "${PROJECT_ROOT}"
    source "${VENV_DIR}/bin/activate"
    uv pip install \
      --python "${VENV_DIR}/bin/python" \
      --reinstall \
      "face-recognition>=1.3"
  )
}

ensure_venv() {
  log "Recreating standalone pi5camera virtual environment."
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

install_system_packages() {
  if (( SKIP_APT )); then
    log "Skipping apt install step."
    return
  fi

  require_command sudo
  require_command apt
  require_command apt-cache
  log "Installing required Raspberry Pi camera packages."
  sudo apt update

  local packages=("${APT_PACKAGES[@]}")
  local optional_package
  while IFS= read -r optional_package; do
    [[ -n "${optional_package}" ]] || continue
    packages+=("${optional_package}")
  done < <(list_available_optional_packages "${OPTIONAL_CAMERA_APT_PACKAGES[@]}")
  while IFS= read -r optional_package; do
    [[ -n "${optional_package}" ]] || continue
    packages+=("${optional_package}")
  done < <(list_available_optional_packages "${OPTIONAL_RECOGNITION_APT_PACKAGES[@]}")

  sudo apt install -y "${packages[@]}"
}

run_sync() {
  log "Syncing the standalone pi5camera environment."
  (
    cd "${PROJECT_ROOT}"
    # Force uv to install into the verified .venv created above.
    source "${VENV_DIR}/bin/activate"
    uv sync --active --extra dev
  )
}

ensure_system_site_packages() {
  log "Ensuring system-site-packages access for Picamera2."

  # 1. Re-ensure pyvenv.cfg has include-system-site-packages = true in case
  #    uv sync overwrote it.
  local CFG="${VENV_DIR}/pyvenv.cfg"
  if [[ -f "${CFG}" ]]; then
    if grep -q 'include-system-site-packages = false' "${CFG}" 2>/dev/null; then
      sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' "${CFG}"
    elif ! grep -q 'include-system-site-packages' "${CFG}" 2>/dev/null; then
      echo 'include-system-site-packages = true' >> "${CFG}"
    fi
  fi

  # 2. Write a .pth file into the venv site-packages so system dist-packages
  #    are always on sys.path even if pyvenv.cfg gets overwritten later by uv.
  local PY_VERSION
  PY_VERSION=$("${VENV_DIR}/bin/python" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
  local SITE_DIR="${VENV_DIR}/lib/python${PY_VERSION}/site-packages"
  local PTH_FILE="${SITE_DIR}/_pi5camera_system_packages.pth"
  if [[ -d "${SITE_DIR}" ]]; then
    "${PYTHON_BIN}" -c "import site; print('\n'.join(site.getsitepackages()))" > "${PTH_FILE}"
    log "Wrote ${PTH_FILE}"
  fi
}

ensure_face_recognition_stack() {
  ensure_system_site_packages

  if venv_can_import_face_recognition; then
    log "face_recognition is importable in .venv."
    return
  fi

  if system_python_can_import "import face_recognition"; then
    local import_output
    import_output=$("${VENV_DIR}/bin/python" -c "import face_recognition" 2>&1 || true)
    fail "face_recognition is importable in /usr/bin/python3 but not inside ${VENV_DIR}. ${import_output}"
  fi

  log "System recognition packages are not available; using the Python fallback."
  RECOGNITION_PIP_FALLBACK=1
  install_fallback_recognition_stack

  if venv_can_import_face_recognition; then
    log "face_recognition import repaired."
    return
  fi

  local import_output
  import_output=$("${VENV_DIR}/bin/python" -c "import face_recognition" 2>&1 || true)
  fail "face_recognition is still not importable inside ${VENV_DIR}. ${import_output}"
}

run_health_checks() {
  log "Running standalone camera readiness checks."
  (
    cd "${PROJECT_ROOT}"
    "${VENV_DIR}/bin/python" -m pi5camera doctor
    "${VENV_DIR}/bin/python" -c "import pi5camera, libcamera, picamera2, face_recognition; print('imports-ok')"
  )
}

main() {
  while (($# > 0)); do
    case "$1" in
      --skip-apt)
        SKIP_APT=1
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
  ensure_face_recognition_stack
  run_health_checks

  if (( RECOGNITION_PIP_FALLBACK )); then
    log "Recognition is using the Python fallback inside .venv because system apt packages were unavailable."
  fi
  log "Standalone pi5camera bootstrap completed."
}

main "$@"
