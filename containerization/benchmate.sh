#!/usr/bin/env bash

set -euo pipefail

RUNTIME="docker"
USE_COMPOSE=0
MODE="cpu-nodb"
CUSTOM_IMAGE=""
DB_DIR=""
DB_NAME="benchmate"
DB_PORT="5544"
CONTAINER_DB_DIR="/work/pgdata"
DOCKER_EXTRA_ARGS=()
SINGULARITY_EXTRA_ARGS=()
SHOW_COMMAND=0

# Flags explicitly set by user
FLAG_GPU=0
FLAG_DB=0
USER_SET_MODE=0

usage() {
  cat <<'EOF'
Usage:
  containerization/benchmate.sh [options] [-- command...]

Container Profiles:
  1. cpu-nodb  : No database, no GPU (default)
  2. gpu-nodb  : No database, with GPU
  3. cpu-db    : With database, no GPU
  4. gpu-db    : With database, with GPU

Options:
  --mode MODE                 One of: cpu-nodb, gpu-nodb, cpu-db, gpu-db (default: cpu-nodb)
  --gpu                       Enable GPU mode (switches profile to gpu-nodb or gpu-db)
  --db                        Enable PostgreSQL database support (switches profile to cpu-db or gpu-db)
  --no-db                     Disable PostgreSQL database support
  --compose                   Use 'docker compose' to launch the designated service
  --runtime RUNTIME           docker or singularity (default: docker)
  --db-dir PATH               Host path to the PostgreSQL data directory (required when DB enabled)
  --container IMAGE_OR_SIF    Docker image name or Singularity .sif path
  --db-name NAME              PostgreSQL database name to create/reuse (default: benchmate)
  --db-port PORT              PostgreSQL port inside the container (default: 5544)
  --container-db-dir PATH     Mount point inside the container (default: /work/pgdata)
  --docker-arg ARG            Extra argument to pass to docker run (repeatable)
  --singularity-arg ARG       Extra argument to pass to singularity exec (repeatable)
  --bind SPEC                 Convenience alias that appends '--bind SPEC' to singularity exec
  --show-command              Print the fully expanded runtime command before execution
  -h, --help                  Show this message

Examples:
  containerization/benchmate.sh --mode cpu-nodb -- python script.py
  containerization/benchmate.sh --gpu --db --db-dir ./pgdata -- bash
  containerization/benchmate.sh --compose --mode gpu-db --db-dir ./pgdata
EOF
}

log() {
  printf '[benchmate] %s\n' "$*"
}

fail() {
  printf '[benchmate] ERROR: %s\n' "$*" >&2
  exit 1
}

# Parse options
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-}"
      USER_SET_MODE=1
      shift 2
      ;;
    --gpu)
      FLAG_GPU=1
      shift
      ;;
    --db)
      FLAG_DB=1
      shift
      ;;
    --no-db)
      FLAG_DB=0
      shift
      ;;
    --compose)
      USE_COMPOSE=1
      shift
      ;;
    --runtime)
      RUNTIME="${2:-}"
      shift 2
      ;;
    --db-dir)
      DB_DIR="${2:-}"
      shift 2
      ;;
    --container|--image)
      CUSTOM_IMAGE="${2:-}"
      shift 2
      ;;
    --db-name)
      DB_NAME="${2:-}"
      shift 2
      ;;
    --db-port)
      DB_PORT="${2:-}"
      shift 2
      ;;
    --container-db-dir)
      CONTAINER_DB_DIR="${2:-}"
      shift 2
      ;;
    --docker-arg)
      DOCKER_EXTRA_ARGS+=("${2:-}")
      shift 2
      ;;
    --singularity-arg)
      SINGULARITY_EXTRA_ARGS+=("${2:-}")
      shift 2
      ;;
    --bind)
      SINGULARITY_EXTRA_ARGS+=(--bind "${2:-}")
      shift 2
      ;;
    --show-command)
      SHOW_COMMAND=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      break
      ;;
  esac
done

# Resolve profile mode from flags if --mode was not explicitly passed
if [[ "${USER_SET_MODE}" -eq 0 ]]; then
  if [[ "${FLAG_GPU}" -eq 1 && "${FLAG_DB}" -eq 1 ]]; then
    MODE="gpu-db"
  elif [[ "${FLAG_GPU}" -eq 1 && "${FLAG_DB}" -eq 0 ]]; then
    MODE="gpu-nodb"
  elif [[ "${FLAG_GPU}" -eq 0 && "${FLAG_DB}" -eq 1 ]]; then
    MODE="cpu-db"
  else
    MODE="cpu-nodb"
  fi
fi

# Validate target mode
case "${MODE}" in
  cpu-nodb|gpu-nodb|cpu-db|gpu-db) ;;
  *) fail "Unknown mode '${MODE}'. Choose from: cpu-nodb, gpu-nodb, cpu-db, gpu-db" ;;
esac

# Resolve image name
IMAGE="${CUSTOM_IMAGE:-ccm-benchmate:${MODE}}"

# Determine DB requirements based on mode
HAS_DB=0
if [[ "${MODE}" == "cpu-db" || "${MODE}" == "gpu-db" ]]; then
  HAS_DB=1
fi

HAS_GPU=0
if [[ "${MODE}" == "gpu-nodb" || "${MODE}" == "gpu-db" ]]; then
  HAS_GPU=1
fi

ensure_db_dir() {
  if [[ "${HAS_DB}" -eq 1 ]]; then
    [[ -n "${DB_DIR}" ]] || fail "--db-dir is required for mode ${MODE}"

    if [[ ! -e "${DB_DIR}" ]]; then
      log "Creating database directory: ${DB_DIR}"
      mkdir -p "${DB_DIR}"
    fi

    [[ -d "${DB_DIR}" ]] || fail "${DB_DIR} exists but is not a directory"

    chmod 700 "${DB_DIR}" 2>/dev/null || true
    local mode
    mode="$(stat -c '%a' "${DB_DIR}" 2>/dev/null || true)"
    if [[ -n "${mode}" && "${mode}" != "700" && "${mode}" != "750" ]]; then
      log "Warning: Database directory mode is ${mode}."
    fi
  fi
}

build_passwd_file() {
  local passwd_file="./benchmate.passwd"

  {
    printf 'root:x:0:0:root:/root:/bin/bash\n'
    printf 'mambauser:x:57439:57439::/home/mambauser:/bin/bash\n'
    printf '%s:x:%s:%s:%s:%s:/bin/bash\n' "$(id -un)" "$(id -u)" "$(id -g)" "$(id -un)" "${HOME}"
  } > "${passwd_file}"

  printf '%s' "${passwd_file}"
}

run_compose() {
  ensure_db_dir
  export BM_HOST_DB_DIR="${DB_DIR:-./pgdata}"
  export BM_DB_NAME="${DB_NAME}"
  export BM_DB_PORT="${DB_PORT}"

  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local compose_file="${script_dir}/docker-compose.yml"

  log "Running Docker Compose service '${MODE}' from ${compose_file}"

  local cmd=(
    docker compose -f "${compose_file}" run --rm "${MODE}"
  )

  if [[ $# -gt 0 ]]; then
    cmd+=("$@")
  fi

  if [[ "${SHOW_COMMAND}" -eq 1 ]]; then
    log "Command: ${cmd[*]}"
  fi

  exec "${cmd[@]}"
}

run_docker() {
  ensure_db_dir

  local cmd=(
    docker run --rm -it --platform linux/amd64
  )

  if [[ "${HAS_GPU}" -eq 1 ]]; then
    cmd+=(--gpus all)
  fi

  if [[ "${HAS_DB}" -eq 1 ]]; then
    cmd+=(
      -v "${DB_DIR}:${CONTAINER_DB_DIR}"
      -e "BM_DB_DIR=${CONTAINER_DB_DIR}"
      -e "BM_DB_NAME=${DB_NAME}"
      -e "BM_DB_PORT=${DB_PORT}"
      -e "BM_ENABLE_DB=1"
    )
  else
    cmd+=(-e "BM_ENABLE_DB=0")
  fi

  if [[ ${#DOCKER_EXTRA_ARGS[@]} -gt 0 ]]; then
    cmd+=("${DOCKER_EXTRA_ARGS[@]}")
  fi

  cmd+=(
    "${IMAGE}"
    /opt/benchmate/containerization/benchmate-run.sh
  )

  if [[ $# -gt 0 ]]; then
    cmd+=("$@")
  fi

  log "Launching Docker image ${IMAGE} in profile '${MODE}'"
  if [[ "${HAS_DB}" -eq 1 ]]; then
    log "Mounting ${DB_DIR} at ${CONTAINER_DB_DIR}"
  fi

  if [[ "${SHOW_COMMAND}" -eq 1 ]]; then
    log "Command: ${cmd[*]}"
  fi

  exec "${cmd[@]}"
}

run_singularity() {
  ensure_db_dir
  local passwd_file
  passwd_file="$(build_passwd_file)"

  local cmd=(
    singularity exec
  )

  if [[ "${HAS_GPU}" -eq 1 ]]; then
    cmd+=(--nv)
  fi

  if [[ "${HAS_DB}" -eq 1 ]]; then
    cmd+=(
      --bind "${DB_DIR}:${CONTAINER_DB_DIR}"
      --bind "${passwd_file}:/etc/passwd"
    )
  fi

  if [[ ${#SINGULARITY_EXTRA_ARGS[@]} -gt 0 ]]; then
    cmd+=("${SINGULARITY_EXTRA_ARGS[@]}")
  fi

  local inner_env="export LANG=C.UTF-8 LC_ALL=C.UTF-8 PATH=/opt/conda/bin:\$PATH BM_ENABLE_DB=${HAS_DB};"
  if [[ "${HAS_DB}" -eq 1 ]]; then
    inner_env+=" export BM_DB_DIR='${CONTAINER_DB_DIR}' BM_DB_NAME='${DB_NAME}' BM_DB_PORT='${DB_PORT}';"
  fi

  local user_cmd
  if [[ $# -gt 0 ]]; then
    user_cmd="$(printf '%q ' "$@")"
  else
    user_cmd="bash"
  fi

  cmd+=(
    "${IMAGE}"
    bash -lc "${inner_env} /opt/benchmate/containerization/benchmate-run.sh ${user_cmd}"
  )

  log "Launching Singularity image ${IMAGE} in profile '${MODE}'"
  if [[ "${SHOW_COMMAND}" -eq 1 ]]; then
    log "Command: ${cmd[*]}"
  fi

  exec "${cmd[@]}"
}

if [[ $# -eq 0 ]]; then
  set -- bash
fi

if [[ "${USE_COMPOSE}" -eq 1 ]]; then
  run_compose "$@"
fi

case "${RUNTIME}" in
  docker)
    run_docker "$@"
    ;;
  singularity)
    [[ -f "${IMAGE}" ]] || fail "Singularity container not found: ${IMAGE}"
    run_singularity "$@"
    ;;
  *)
    fail "Unsupported runtime: ${RUNTIME}. Use docker or singularity."
    ;;
esac
