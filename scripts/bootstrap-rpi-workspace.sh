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
  liblgpio-dev
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
3. Running uv sync --active --extra dev
4. Injecting the Raspberry Pi system dist-packages path into .venv so
   picamera2 and libcamera remain importable even if uv replaces the
   venv interpreter

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

venv_can_import() {
  [[ -x "${VENV_DIR}/bin/python" ]] || return 1
  "${VENV_DIR}/bin/python" -c "$1" >/dev/null 2>&1
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

  # Confirm picamera2 is importable immediately after venv creation.
  if ! venv_can_import "import libcamera, picamera2"; then
    local venv_output
    local system_output
    venv_output=$("${VENV_DIR}/bin/python" -c "import libcamera, picamera2" 2>&1 || true)
    system_output=$("${PYTHON_BIN}" -c "import libcamera, picamera2" 2>&1 || true)
    fail "Picamera2 is not importable right after venv creation. .venv: ${venv_output}. system: ${system_output}"
  fi
  log "Venv created. picamera2 importable: OK"
}

run_sync() {
  local sync_args=(--active --extra dev)
  if (( INCLUDE_VOICEINPUT )); then
    sync_args+=(--extra voiceinput)
  fi

  # Detect the system Python version and write it to .python-version so uv
  # uses the same interpreter that /usr/bin/python3 provides.  Without this,
  # a stale .python-version (e.g. "3.11") forces uv to download a managed
  # Python that cannot see system site-packages (picamera2, libcamera).
  local system_pyver
  system_pyver=$("${PYTHON_BIN}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
  echo "${system_pyver}" > "${PROJECT_ROOT}/.python-version"
  log "Set .python-version to ${system_pyver} (matching system Python)."

  log "Syncing the NinjaClawBot workspace."
  (
    cd "${PROJECT_ROOT}"
    source "${VENV_DIR}/bin/activate"
    uv sync "${sync_args[@]}"
  )
}

inject_system_dist_packages() {
  # After uv sync, the venv interpreter may have been replaced by uv-managed
  # Python.  When that happens, include-system-site-packages=true resolves to
  # the managed Python's system paths, NOT /usr/lib/python3/dist-packages
  # where picamera2 and libcamera live.
  #
  # Fix: unconditionally place a .pth file in the venv's site-packages that
  # adds the Raspberry Pi system dist-packages to sys.path.

  log "Ensuring Raspberry Pi system dist-packages are on the venv path."

  # 1. Ensure pyvenv.cfg has include-system-site-packages = true.
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

  # 2. Discover where the system Python keeps its dist-packages.
  local system_dist_paths
  system_dist_paths=$("${PYTHON_BIN}" -c "
import site, os
paths = []
for p in site.getsitepackages():
    if os.path.isdir(p):
        paths.append(p)
# Also include the Debian-standard path even if site doesn't list it.
debian_path = '/usr/lib/python3/dist-packages'
if os.path.isdir(debian_path) and debian_path not in paths:
    paths.append(debian_path)
print('\\n'.join(paths))
" 2>/dev/null || true)

  if [[ -z "${system_dist_paths}" ]]; then
    log "WARNING: Could not discover system dist-packages paths."
    return
  fi

  # 3. Get the venv's own site-packages directory.
  local venv_site_dir
  venv_site_dir=$("${VENV_DIR}/bin/python" -c "import site; print(site.getsitepackages()[0])" 2>/dev/null || true)
  if [[ -z "${venv_site_dir}" ]] || [[ ! -d "${venv_site_dir}" ]]; then
    log "WARNING: Could not find venv site-packages directory."
    return
  fi

  # 4. Write a .pth file that adds each system path.
  local pth_file="${venv_site_dir}/raspberry-pi-system-packages.pth"
  echo "${system_dist_paths}" > "${pth_file}"
  log "Created ${pth_file}"

  # 5. Verify picamera2 is now importable.
  if venv_can_import "import libcamera, picamera2"; then
    log "picamera2 is importable after path injection: OK"
  else
    local import_output
    import_output=$("${VENV_DIR}/bin/python" -c "import libcamera, picamera2" 2>&1 || true)
    fail "picamera2 still not importable after path injection. ${import_output}"
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
  inject_system_dist_packages
  run_health_checks

  log "Workspace bootstrap completed."
}

main "$@"
