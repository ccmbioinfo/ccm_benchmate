#!/usr/bin/env bash

set -euo pipefail

# Normalize the runtime environment inside the container so Postgres and
# Benchmate use the conda-installed binaries
export PATH="/opt/conda/bin:${PATH}"
export LANG="${LANG:-C.UTF-8}"
export LC_ALL="${LC_ALL:-C.UTF-8}"

DB_PORT="${BM_DB_PORT:-5544}"
DB_NAME="${BM_DB_NAME:-benchmate}"
DB_DIR="${BM_DB_DIR:-/work/pgdata}"
POSTGRES_LOG="${BM_POSTGRES_LOG:-${DB_DIR}/postgres.log}"

log() {
  printf '[benchmate-run] %s\n' "$*"
}

fail() {
  printf '[benchmate-run] ERROR: %s\n' "$*" >&2
  exit 1
}

# A Postgres cluster created by initdb will always contain these
is_valid_pgdata_dir() {
  [[ -f "${DB_DIR}/PG_VERSION" && -d "${DB_DIR}/base" && -d "${DB_DIR}/global" ]]
}


dir_is_empty() {
  [[ -z "$(find "${DB_DIR}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]
}

BM_ENABLE_DB="${BM_ENABLE_DB:-1}"

# If DB is disabled or initdb is absent, bypass PostgreSQL initialization
if [[ "${BM_ENABLE_DB}" == "0" ]] || ! command -v initdb >/dev/null 2>&1; then
  log "Database mode disabled or PostgreSQL not installed. Skipping DB setup."
  if [[ $# -eq 0 ]]; then
    set -- bash
  fi
  exec "$@"
fi

# Postgres initialization is not allowed as root, so fail early 
if [[ "$(id -u)" -eq 0 ]]; then
  fail "PostgreSQL cannot be initialized as root. Run as a non-root user."
fi

# If the user did not provide a command, start an interactive shell after setup
if [[ $# -eq 0 ]]; then
  set -- bash
fi

log "Using PostgreSQL data directory: ${DB_DIR}"

if [[ ! -e "${DB_DIR}" ]]; then
  log "Database directory does not exist. Creating ${DB_DIR}"
  mkdir -p "${DB_DIR}"
fi

if [[ ! -d "${DB_DIR}" ]]; then
  fail "${DB_DIR} exists but cannot be used as a PostgreSQL data directory."
fi

# Postgres requires strict permissions on PGDATA, some filesystems will
# refuse this change, so we warn if the final mode is still too permissive
chmod 700 "${DB_DIR}" 2>/dev/null || true
MODE="$(stat -c '%a' "${DB_DIR}" 2>/dev/null || true)"
if [[ -n "${MODE}" && "${MODE}" != "700" && "${MODE}" != "750" ]]; then
  log "Database directory mode is ${MODE}. PostgreSQL may reject this path unless the filesystem allows 700 or 750."
fi

if is_valid_pgdata_dir; then
  log "Existing PostgreSQL cluster detected. Reusing it."
elif dir_is_empty; then
  log "No PostgreSQL cluster found. Initializing a new cluster."
  initdb -D "${DB_DIR}"
else
  fail "Path ${DB_DIR} exists but is not a valid PostgreSQL data directory."
fi

if pg_ctl -D "${DB_DIR}" status >/dev/null 2>&1; then
  log "PostgreSQL is already running for ${DB_DIR}"
else
  log "Starting PostgreSQL on port ${DB_PORT}"
  pg_ctl -D "${DB_DIR}" -l "${POSTGRES_LOG}" -o "-p ${DB_PORT}" start
fi

log "Waiting for PostgreSQL to accept connections"
until pg_isready -p "${DB_PORT}" >/dev/null 2>&1; do
  sleep 1
done

if psql -p "${DB_PORT}" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
  log "Database ${DB_NAME} already exists"
else
  log "Creating database ${DB_NAME}"
  createdb -p "${DB_PORT}" "${DB_NAME}"
fi

log "Ensuring required PostgreSQL extensions are installed"
psql -p "${DB_PORT}" -d "${DB_NAME}" -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null
psql -p "${DB_PORT}" -d "${DB_NAME}" -c "CREATE EXTENSION IF NOT EXISTS rdkit;" >/dev/null

# Export the database URL for easy access, and run any additional commands provided
export DATABASE_URL="postgresql+psycopg2://localhost:${DB_PORT}/${DB_NAME}"
log "DATABASE_URL set to ${DATABASE_URL}"
log "Running command: $*"
exec "$@"
