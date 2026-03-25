#!/usr/bin/env bash
set -euo pipefail

export FLASK_CONFIG="${FLASK_CONFIG:-development}"
export PORT="${PORT:-8080}"

# 开发环境推荐单 worker + reload，日志直接输出到终端
exec python3 -m gunicorn \
  --bind "127.0.0.1:${PORT}" \
  --workers 1 \
  --threads 4 \
  --reload \
  --access-logfile - \
  --error-logfile - \
  wsgi:app

