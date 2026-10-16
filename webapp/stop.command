#!/bin/bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="${PORT:-4173}"
PID_FILE="${APP_DIR}/.runtime/server-${PORT}.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "没有由启动脚本记录的服务 PID。"
  exit 0
fi

PID="$(cat "$PID_FILE")"
if [[ ! "$PID" =~ ^[0-9]+$ ]]; then
  echo "PID 文件无效，拒绝终止任何进程。"
  exit 1
fi

if ! kill -0 "$PID" 2>/dev/null; then
  rm -f "$PID_FILE"
  echo "服务进程已退出，已清理 PID 文件。"
  exit 0
fi

PROCESS="$(ps -p "$PID" -o command= || true)"
PID_CWD="$(lsof -a -p "$PID" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1 || true)"
if [[ "$PROCESS" != *"node server.js"* || "$PID_CWD" != "$APP_DIR" ]]; then
  echo "PID ${PID} 当前不属于本项目 server.js，拒绝终止。"
  exit 1
fi

kill "$PID"
for _ in $(seq 1 20); do
  if ! kill -0 "$PID" 2>/dev/null; then
    rm -f "$PID_FILE"
    echo "服务已停止。"
    exit 0
  fi
  sleep 0.25
done

echo "服务仍在退出中；未执行强制终止。"
exit 1
