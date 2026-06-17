#!/data/data/com.termux/files/usr/bin/bash

cd ~/elmino || exit 1

BASE_URL="http://127.0.0.1:8000"
TMP_DIR="logs/tmp"
mkdir -p "$TMP_DIR"

echo "=============================="
echo "ELMINO GAME FLOW TEST STARTED"
echo "=============================="

echo
echo "[1] Health check: openapi"
curl -s "$BASE_URL/openapi.json" > "$TMP_DIR/openapi.json"

if [ $? -ne 0 ]; then
  echo "FAIL: server is not reachable"
  exit 1
fi

if [ ! -s "$TMP_DIR/openapi.json" ]; then
  echo "FAIL: openapi response is empty"
  exit 1
fi

echo "PASS: server reachable"

echo
echo "[2] Create 3 users"
USER1=$(curl -s -X POST "$BASE_URL/users/" -H "Content-Type: application/json" -d '{"name":"Ali"}')
USER2=$(curl -s -X POST "$BASE_URL/users/" -H "Content-Type: application/json" -d '{"name":"Sara"}')
USER3=$(curl -s -X POST "$BASE_URL/users/" -H "Content-Type: application/json" -d '{"name":"Reza"}')

echo "User1 response: $USER1"
echo "User2 response: $USER2"
echo "User3 response: $USER3"

echo "$USER1" > "$TMP_DIR/user1.json"
echo "$USER2" > "$TMP_DIR/user2.json"
echo "$USER3" > "$TMP_DIR/user3.json"

USER1_ID=$(python - <<'PY'
import json
with open("logs/tmp/user1.json") as f:
    print(json.load(f)["id"])
PY
)

USER2_ID=$(python - <<'PY'
import json
with open("logs/tmp/user2.json") as f:
    print(json.load(f)["id"])
PY
)

USER3_ID=$(python - <<'PY'
import json
with open("logs/tmp/user3.json") as f:
    print(json.load(f)["id"])
PY
)

echo
echo "PASS: created users with ids $USER1_ID, $USER2_ID, $USER3_ID"

echo
echo "[3] Join queue with real payload"
JOIN1=$(curl -s -X POST "$BASE_URL/queue/join" -H "Content-Type: application/json" -d "{\"user_id\":$USER1_ID,\"stake\":10}")
JOIN2=$(curl -s -X POST "$BASE_URL/queue/join" -H "Content-Type: application/json" -d "{\"user_id\":$USER2_ID,\"stake\":10}")
JOIN3=$(curl -s -X POST "$BASE_URL/queue/join" -H "Content-Type: application/json" -d "{\"user_id\":$USER3_ID,\"stake\":10}")

echo "Join1: $JOIN1"
echo "Join2: $JOIN2"
echo "Join3: $JOIN3"

echo "$JOIN3" > "$TMP_DIR/join3.json"

GAME_ID=$(python - <<'PY'
import json
with open("logs/tmp/join3.json") as f:
    data = json.load(f)
    print(data["game_id"])
PY
)

echo
echo "PASS: game created with game_id=$GAME_ID"

echo
echo "[4] Get game status"
GAME_STATUS=$(curl -s "$BASE_URL/games/$GAME_ID")
echo "$GAME_STATUS"
echo "$GAME_STATUS" > "$TMP_DIR/game_status.json"

echo
echo "[5] List users"
curl -s "$BASE_URL/users/"
echo

echo
echo "=============================="
echo "BASIC TEST FINISHED"
echo "=============================="
echo "Game status fetched successfully if JSON printed above."
