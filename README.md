# Elmino API

A simple backend API for managing players in the Elmino project.

## Tech Stack
- FastAPI
- SQLite
- SQLAlchemy
- Uvicorn

## Features
- Get all players
- Get player by ID
- Add player
- Update player
- Delete player
- Persistent data storage with SQLite
- Swagger API docs

## Run the project

uvicorn main:app --host 0.0.0.0 --port 8000

## API Docs
http://127.0.0.1:8000/docs

## Endpoints
- GET /
- GET /players
- GET /players/{player_id}
- POST /players
- PUT /players/{player_id}
- DELETE /players/{player_id}

## Notes
- Data is stored in elmino.db
- API is ready for connection to Flutter or other clients
