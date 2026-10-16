#!/bin/bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="${PORT:-4173}"
BASE_URL="http://127.0.0.1:${PORT}"
RUNTIME_DIR="${APP_DIR}/.runtime"
PID_FILE="${RUNTIME_DIR}/server-${PORT}.pid"
LOG_FILE="${RUNTIME_DIR}/server-${PORT}.log"

mkdir -p "$RUNTIME_DIR"

if ! NODE_BIN="$(/bin/zsh -lic 'command -v node' 2>/dev/null | tail -n 1)" || [[ -z "$NODE_BIN" ]]; then
  osascript -e 'display alert "未找到 Node.js" message "请安装 Node.js，并确认在终端运行 node --version 正常。"'
  exit 1
fi

if [[ ! -d "${APP_DIR}/node_modules" ]]; then
  osascript -e 'display alert "尚未安装项目依赖" message "请先在 webapp 目录运行 npm install。"'
  exit 1
fi

if curl --silent --fail --max-time 2 "${BASE_URL}/api/health" >/dev/null; then
  open "$BASE_URL"
  exit 0
fi

if /usr/sbin/lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  osascript -e "display alert \"端口 ${PORT} 已被占用\" message \"占用进程不是本项目的健康服务。请关闭占用进程，或使用 PORT=其他端口 启动。\""
  exit 1
fi

cd "$APP_DIR"
nohup env PORT="$PORT" "$NODE_BIN" server.js >>"$LOG_FILE" 2>&1 </dev/null &
SERVER_PID=$!
printf '%s\n' "$SERVER_PID" >"$PID_FILE"

for _ in $(seq 1 40); do
  if curl --silent --fail --max-time 2 "${BASE_URL}/api/health" >/dev/null; then
    open "$BASE_URL"
    exit 0
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    break
  fi
  sleep 0.25
done

if kill -0 "$SERVER_PID" 2>/dev/null; then
  kill "$SERVER_PID" 2>/dev/null || true
fi
rm -f "$PID_FILE"
osascript -e "display alert \"应用启动失败\" message \"请查看日志：${LOG_FILE}\""
exit 1
