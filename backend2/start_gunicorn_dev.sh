#!/usr/bin/env bash
set -euo pipefail

# macOS + gunicorn fork 时，若已加载含 ObjC 的运行库可能触发崩溃；开发环境可关闭 fork 安全检查
if [[ "$(uname -s)" == "Darwin" ]]; then
  export OBJC_DISABLE_INITIALIZE_FORK_SAFETY="${OBJC_DISABLE_INITIALIZE_FORK_SAFETY:-YES}"
fi

export FLASK_CONFIG="${FLASK_CONFIG:-development}"
export PORT="${PORT:-8080}"

# macOS 上多线程 worker 偶发与 fork 相关崩溃，开发环境改为单线程更稳
GUNICORN_THREADS=4
if [[ "$(uname -s)" == "Darwin" ]]; then
  GUNICORN_THREADS=1
fi

# 开发环境推荐单 worker + reload，日志直接输出到终端
exec python3 -m gunicorn \
  --bind "127.0.0.1:${PORT}" \
  --workers 1 \
  --threads "${GUNICORN_THREADS}" \
  --reload \
  --access-logfile - \
  --error-logfile - \
  wsgi:app

