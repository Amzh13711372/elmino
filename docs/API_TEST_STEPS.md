# API Test Steps

## 1. Run server
uvicorn app.main:app --host 127.0.0.1 --port 8000

## 2. Check server
curl -i http://127.0.0.1:8000/users/

## 3. Join queue
curl -i -X POST http://127.0.0.1:8000/queue/join -H "Content-Type: application/json" -d '{"user_id":1,"stake":100}'
curl -i -X POST http://127.0.0.1:8000/queue/join -H "Content-Type: application/json" -d '{"user_id":2,"stake":100}'
curl -i -X POST http://127.0.0.1:8000/queue/join -H "Content-Type: application/json" -d '{"user_id":3,"stake":100}'

## 4. Check created game
curl -i http://127.0.0.1:8000/games/1
curl -i http://127.0.0.1:8000/games/2
curl -i http://127.0.0.1:8000/games/3

## 5. Activate manually if needed
sqlite3 elmino.db
UPDATE games SET status='active' WHERE id=GAME_ID;
SELECT id, status FROM games WHERE id=GAME_ID;
.quit

## 6. Get current question
curl -i http://127.0.0.1:8000/games/GAME_ID/question

## 7. Submit answer
curl -i -X POST http://127.0.0.1:8000/games/GAME_ID/answer -H "Content-Type: application/json" -d '{"user_id":USER_ID,"selected_option":3}'

## 8. Repeat question + answer
Until game status becomes finished

## 9. Check final result
curl -i http://127.0.0.1:8000/games/GAME_ID
