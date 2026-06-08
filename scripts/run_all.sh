#!/data/data/com.termux/files/usr/bin/bash

set -e

cd ~/elmino || exit 1

echo "=================================="
echo "STEP 1: START SERVER"
echo "=================================="
bash scripts/run_server.sh

echo
echo "=================================="
echo "STEP 2: RUN BASIC TEST"
echo "=================================="
bash scripts/test_game_flow.sh

echo
echo "=================================="
echo "STEP 3: CLEAN QUEUE"
echo "=================================="
sqlite3 elmino.db "DELETE FROM queue_entries;"

echo
echo "=================================="
echo "STEP 4: RUN ANSWER FLOW TEST"
echo "=================================="
bash scripts/test_answer_flow.sh

echo
echo "=================================="
echo "ALL TESTS PASSED"
echo "=================================="
