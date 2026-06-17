# Elmino API

A backend API for managing players in the Elmino project.

## Tech Stack
- FastAPI
- SQLite
- SQLAlchemy
- Uvicorn
- Pytest

## Features
- Get all players
- Get player by ID
- Add player
- Update player
- Delete player
- Persistent data storage with SQLite
- Swagger API docs

## Project Structure
- `app/` - application source code
- `tests/` - test files
- `requirements.txt` - project dependencies
- `README.md` - project documentation

## Installation
Install dependencies with:


```bash
pip install -r requirements.txt

```

## Run the Project
Run the API server with:


```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000

```

## API Documentation
After running the server, open:


```text
http://127.0.0.1:8000/docs

```

## Run Tests
Run tests with:


```bash
pytest

```

## Main Endpoints
- `GET /`
- `GET /players`
- `GET /players/{player_id}`
- `POST /players`
- `PUT /players/{player_id}`
- `DELETE /players/{player_id}`

## Notes
- Data is stored locally in `elmino.db`
- The API can be connected to Flutter or other clients
