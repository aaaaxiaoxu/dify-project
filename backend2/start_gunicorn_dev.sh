#!/usr/bin/env bash
set -euo pipefail

# macOS + gunicorn fork 时，若已加载含 ObjC 的运行库可能触发崩溃；开发环境可关闭 fork 安全检查
if [[ "$(uname -s)" == "Darwin" ]]; then
  export OBJC_DISABLE_INITIALIZE_FORK_SAFETY="${OBJC_DISABLE_INITIALIZE_FORK_SAFETY:-YES}"
fi

export FLASK_CONFIG="${FLASK_CONFIG:-development}"
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8080}"

# macOS 上多线程 worker 偶发与 fork 相关崩溃，开发环境改为单线程更稳
GUNICORN_THREADS=4
if [[ "$(uname -s)" == "Darwin" ]]; then
  GUNICORN_THREADS=1
fi

GUNICORN_ARGS=(
  --bind "${HOST}:${PORT}"
  --workers 1
  --threads "${GUNICORN_THREADS}"
  --access-logfile -
  --error-logfile -
)

if [[ "${FLASK_CONFIG}" != "production" ]]; then
  GUNICORN_ARGS+=(--reload)
fi

exec python3 -m gunicorn "${GUNICORN_ARGS[@]}" wsgi:app
