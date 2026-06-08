#!/data/data/com.termux/files/usr/bin/bash

BASE_URL="http://127.0.0.1:8000"

echo "=============================="
echo "ELMINO ANSWER EDGE CASE TEST"
echo "=============================="
echo

extract_json_field() {
  local json="$1"
  local field="$2"
  echo "$json" | sed -n "s/.*\"$field\":\([^,}]*\).*/\1/p" | tr -d '" '
}

echo "[1] Create 4 users"

USER1_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d '{"name":"edge_user_1"}')

USER2_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d '{"name":"edge_user_2"}')

USER3_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d '{"name":"edge_user_3"}')

USER4_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d '{"name":"edge_user_4"}')

USER1_ID=$(extract_json_field "$USER1_RESPONSE" "id")
USER2_ID=$(extract_json_field "$USER2_RESPONSE" "id")
USER3_ID=$(extract_json_field "$USER3_RESPONSE" "id")
USER4_ID=$(extract_json_field "$USER4_RESPONSE" "id")

echo "Users: $USER1_ID, $USER2_ID, $USER3_ID, outsider=$USER4_ID"
echo

if [ -z "$USER1_ID" ] || [ -z "$USER2_ID" ] || [ -z "$USER3_ID" ] || [ -z "$USER4_ID" ]; then
  echo "FAIL: user creation failed"
  exit 1
fi

echo "[2] Clean queue"
sqlite3 elmino.db "DELETE FROM queue_entries;"
echo

echo "[3] Join queue and create game"

JOIN1=$(curl -s -X POST "$BASE_URL/queue/join" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER1_ID,\"stake\":10}")

JOIN2=$(curl -s -X POST "$BASE_URL/queue/join" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER2_ID,\"stake\":10}")

JOIN3=$(curl -s -X POST "$BASE_URL/queue/join" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER3_ID,\"stake\":10}")

GAME_ID=$(extract_json_field "$JOIN1" "game_id")
if [ -z "$GAME_ID" ] || [ "$GAME_ID" = "null" ]; then
  GAME_ID=$(extract_json_field "$JOIN2" "game_id")
fi
if [ -z "$GAME_ID" ] || [ "$GAME_ID" = "null" ]; then
  GAME_ID=$(extract_json_field "$JOIN3" "game_id")
fi

if [ -z "$GAME_ID" ] || [ "$GAME_ID" = "null" ]; then
  echo "FAIL: game not created"
  exit 1
fi

echo "Game ID: $GAME_ID"
echo

GAME_STATE=$(curl -s "$BASE_URL/games/$GAME_ID")
CURRENT_TURN_USER_ID=$(extract_json_field "$GAME_STATE" "current_turn_user_id")
CURRENT_QUESTION_ID=$(extract_json_field "$GAME_STATE" "current_question_id")

echo "Current turn user: $CURRENT_TURN_USER_ID"
echo "Current question: $CURRENT_QUESTION_ID"
echo

if [ -z "$CURRENT_TURN_USER_ID" ] || [ -z "$CURRENT_QUESTION_ID" ]; then
  echo "FAIL: initial game state missing"
  exit 1
fi

echo "[4] Test wrong user answers"
WRONG_USER_ID="$USER2_ID"
if [ "$WRONG_USER_ID" = "$CURRENT_TURN_USER_ID" ]; then
  WRONG_USER_ID="$USER3_ID"
fi

WRONG_USER_RESPONSE=$(curl -s -X POST "$BASE_URL/games/$GAME_ID/answer" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $WRONG_USER_ID,
    \"question_id\": $CURRENT_QUESTION_ID,
    \"selected_option\": 0
  }")

echo "$WRONG_USER_RESPONSE"
echo

if ! echo "$WRONG_USER_RESPONSE" | grep -qi "turn"; then
  echo "FAIL: wrong user test did not return turn-related error"
  exit 1
fi

echo "[5] Test outsider user answers"

OUTSIDER_RESPONSE=$(curl -s -X POST "$BASE_URL/games/$GAME_ID/answer" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $USER4_ID,
    \"question_id\": $CURRENT_QUESTION_ID,
    \"selected_option\": 0
  }")

echo "$OUTSIDER_RESPONSE"
echo

if ! echo "$OUTSIDER_RESPONSE" | grep -Eqi "not.*player|not.*participant|turn"; then
  echo "FAIL: outsider user test did not return expected error"
  exit 1
fi

echo "[6] Test wrong question_id"

BAD_QUESTION_ID=$((CURRENT_QUESTION_ID + 999))

WRONG_QUESTION_RESPONSE=$(curl -s -X POST "$BASE_URL/games/$GAME_ID/answer" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $CURRENT_TURN_USER_ID,
    \"question_id\": $BAD_QUESTION_ID,
    \"selected_option\": 0
  }")

echo "$WRONG_QUESTION_RESPONSE"
echo

if ! echo "$WRONG_QUESTION_RESPONSE" | grep -Eqi "question|invalid"; then
  echo "FAIL: wrong question_id test did not return expected error"
  exit 1
fi

echo "[7] Finish game normally"

TURN_USER="$CURRENT_TURN_USER_ID"
QUESTION_ID="$CURRENT_QUESTION_ID"
GAME_STATUS="active"
TURN_COUNT=1

while [ "$GAME_STATUS" != "finished" ] && [ "$TURN_COUNT" -le 30 ]; do
  RESPONSE=$(curl -s -X POST "$BASE_URL/games/$GAME_ID/answer" \
    -H "Content-Type: application/json" \
    -d "{
      \"user_id\": $TURN_USER,
      \"question_id\": $QUESTION_ID,
      \"selected_option\": 0
    }")

  echo "Turn $TURN_COUNT response: $RESPONSE"

  GAME_STATUS=$(extract_json_field "$RESPONSE" "game_status")
  NEXT_TURN=$(extract_json_field "$RESPONSE" "next_turn_user_id")
  NEXT_QUESTION=$(extract_json_field "$RESPONSE" "current_question_id")

  if [ "$GAME_STATUS" = "finished" ]; then
    break
  fi

  TURN_USER="$NEXT_TURN"
  QUESTION_ID="$NEXT_QUESTION"
  TURN_COUNT=$((TURN_COUNT + 1))
done

if [ "$GAME_STATUS" != "finished" ]; then
  echo "FAIL: game did not finish"
  exit 1
fi

echo
echo "[8] Test answering after game finished"

AFTER_FINISH_RESPONSE=$(curl -s -X POST "$BASE_URL/games/$GAME_ID/answer" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $USER1_ID,
    \"question_id\": 1,
    \"selected_option\": 0
  }")

echo "$AFTER_FINISH_RESPONSE"
echo

if ! echo "$AFTER_FINISH_RESPONSE" | grep -Eqi "finished|ended|not active"; then
  echo "FAIL: post-finish answer test did not return expected error"
  exit 1
fi

echo "PASS: edge cases behaved correctly"
