#!/data/data/com.termux/files/usr/bin/bash

BASE_URL="http://127.0.0.1:8000"

echo "=============================="
echo "ELMINO ANSWER FLOW TEST"
echo "=============================="
echo

extract_json_field() {
  local json="$1"
  local field="$2"
  echo "$json" | sed -n "s/.*\"$field\":\([^,}]*\).*/\1/p" | tr -d '" '
}

echo "[1] Create 3 users"

USER1_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d '{"name":"test_user_1"}')

USER2_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d '{"name":"test_user_2"}')

USER3_RESPONSE=$(curl -s -X POST "$BASE_URL/users/" \
  -H "Content-Type: application/json" \
  -d '{"name":"test_user_3"}')

USER1_ID=$(extract_json_field "$USER1_RESPONSE" "id")
USER2_ID=$(extract_json_field "$USER2_RESPONSE" "id")
USER3_ID=$(extract_json_field "$USER3_RESPONSE" "id")

echo "Users: $USER1_ID, $USER2_ID, $USER3_ID"
echo

if [ -z "$USER1_ID" ] || [ -z "$USER2_ID" ] || [ -z "$USER3_ID" ]; then
  echo "FAIL: user creation failed"
  echo "$USER1_RESPONSE"
  echo "$USER2_RESPONSE"
  echo "$USER3_RESPONSE"
  exit 1
fi

echo "[2] Join queue"

JOIN1=$(curl -s -X POST "$BASE_URL/queue/join" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER1_ID,\"stake\":10}")

JOIN2=$(curl -s -X POST "$BASE_URL/queue/join" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER2_ID,\"stake\":10}")

JOIN3=$(curl -s -X POST "$BASE_URL/queue/join" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":$USER3_ID,\"stake\":10}")

echo "Join1: $JOIN1"
echo "Join2: $JOIN2"
echo "Join3: $JOIN3"

GAME_ID=$(extract_json_field "$JOIN1" "game_id")

if [ -z "$GAME_ID" ] || [ "$GAME_ID" = "null" ]; then
  GAME_ID=$(extract_json_field "$JOIN2" "game_id")
fi

if [ -z "$GAME_ID" ] || [ "$GAME_ID" = "null" ]; then
  GAME_ID=$(extract_json_field "$JOIN3" "game_id")
fi

if [ -z "$GAME_ID" ] || [ "$GAME_ID" = "null" ]; then
  echo
  echo "FAIL: game_id not created"
  exit 1
fi

echo "Game ID: $GAME_ID"
echo

echo "[3] Submit answers until game finishes"

GAME_STATUS="active"
TURN=1

GAME_STATE=$(curl -s "$BASE_URL/games/$GAME_ID")
CURRENT_TURN_USER_ID=$(extract_json_field "$GAME_STATE" "current_turn_user_id")
CURRENT_QUESTION_ID=$(extract_json_field "$GAME_STATE" "current_question_id")

if [ -z "$CURRENT_TURN_USER_ID" ] || [ -z "$CURRENT_QUESTION_ID" ]; then
  echo "FAIL: initial game state missing"
  echo "$GAME_STATE"
  exit 1
fi

while [ "$GAME_STATUS" != "finished" ] && [ "$TURN" -le 30 ]; do
  echo "Turn $TURN -> user_id=$CURRENT_TURN_USER_ID, question_id=$CURRENT_QUESTION_ID"

  ANSWER_RESPONSE=$(curl -s -X POST "$BASE_URL/games/$GAME_ID/answer" \
    -H "Content-Type: application/json" \
    -d "{
      \"user_id\": $CURRENT_TURN_USER_ID,
      \"question_id\": $CURRENT_QUESTION_ID,
      \"selected_option\": 0
    }")

  echo "Answer response: $ANSWER_RESPONSE"

  GAME_STATUS=$(extract_json_field "$ANSWER_RESPONSE" "game_status")
  NEXT_TURN_USER_ID=$(extract_json_field "$ANSWER_RESPONSE" "next_turn_user_id")
  NEXT_QUESTION_ID=$(extract_json_field "$ANSWER_RESPONSE" "current_question_id")

  if [ "$GAME_STATUS" = "finished" ]; then
    break
  fi

  if [ -z "$NEXT_TURN_USER_ID" ] || [ -z "$NEXT_QUESTION_ID" ]; then
    echo
    echo "FAIL: next turn data missing"
    exit 1
  fi

  CURRENT_TURN_USER_ID="$NEXT_TURN_USER_ID"
  CURRENT_QUESTION_ID="$NEXT_QUESTION_ID"
  TURN=$((TURN + 1))
done

echo
echo "[4] Final game status"
FINAL_STATUS=$(curl -s "$BASE_URL/games/$GAME_ID")
echo "$FINAL_STATUS"
echo

FINAL_GAME_STATUS=$(extract_json_field "$FINAL_STATUS" "status")
FINAL_WINNER=$(extract_json_field "$FINAL_STATUS" "winner_user_id")
FINAL_TURN=$(extract_json_field "$FINAL_STATUS" "current_turn_user_id")
FINAL_QUESTION=$(extract_json_field "$FINAL_STATUS" "current_question_id")

if [ "$FINAL_GAME_STATUS" != "finished" ]; then
  echo "FAIL: game is still not finished"
  exit 1
fi

if [ "$FINAL_WINNER" != "null" ]; then
  echo "FAIL: expected winner_user_id=null but got $FINAL_WINNER"
  exit 1
fi

if [ "$FINAL_TURN" != "null" ]; then
  echo "FAIL: expected current_turn_user_id=null but got $FINAL_TURN"
  exit 1
fi

if [ "$FINAL_QUESTION" != "null" ]; then
  echo "FAIL: expected current_question_id=null but got $FINAL_QUESTION"
  exit 1
fi

echo "PASS: game finished successfully"
echo "winner_user_id=$FINAL_WINNER"
echo "current_turn_user_id=$FINAL_TURN"
echo "current_question_id=$FINAL_QUESTION"

