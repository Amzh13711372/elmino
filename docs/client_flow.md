# Elmino Client Flow

## Base URL
http://127.0.0.1:8000

## 1. Create user
POST /users
{
  "name": "Ali"
}

## 2. Join queue
POST /queue/join
{
  "user_id": 1,
  "stake": 10
}

## 3. Get game status
GET /games/{game_id}

## 4. Get current question
GET /games/{game_id}/question

## 5. Submit answer
POST /games/{game_id}/answer
{
  "user_id": 1,
  "question_id": 2,
  "selected_option": 1
}

## 6. Game loop
- create user
- join queue
- wait for game_id
- fetch game status
- fetch current question
- submit answer
- repeat until game_status = finished
