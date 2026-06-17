#!/data/data/com.termux/files/usr/bin/bash

cd ~/elmino || exit 1

mkdir -p logs

if [ -f .server.pid ]; then
  OLD_PID=$(cat .server.pid)
  if ps -p "$OLD_PID" > /dev/null 2>&1; then
    echo "Stopping old server process: $OLD_PID"
    kill "$OLD_PID"
    sleep 2
  fi
  rm -f .server.pid
fi

echo "Starting server..."
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/server.log 2>&1 &
echo $! > .server.pid

echo "Waiting for server to become ready..."

READY=0
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  if curl -s http://127.0.0.1:8000/openapi.json > logs/ready_check.json; then
    if [ -s logs/ready_check.json ]; then
      READY=1
      break
    fi
  fi
  sleep 1
done

echo "Server started. PID: $(cat .server.pid)"
echo "Log file: logs/server.log"
echo "Last 20 log lines:"
tail -n 20 logs/server.log

if [ "$READY" -ne 1 ]; then
  echo
  echo "FAIL: server did not become ready in time"
  exit 1
fi

echo
echo "PASS: server is ready"
