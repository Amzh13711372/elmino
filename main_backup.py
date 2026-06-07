from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

app = FastAPI()

DATABASE_URL = "sqlite:///./elmino.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class PlayerDB(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    score = Column(Integer, nullable=False)

Base.metadata.create_all(bind=engine)

class Player(BaseModel):
    id: int
    name: str
    score: int

@app.get("/")
def home():
    return {"message": "Elmino API is running with SQLite"}

@app.get("/players")
def get_players():
    db = SessionLocal()
    players = db.query(PlayerDB).all()
    result = [{"id": p.id, "name": p.name, "score": p.score} for p in players]
    db.close()
    return result

@app.get("/players/{player_id}")
def get_player(player_id: int):
    db = SessionLocal()
    player = db.query(PlayerDB).filter(PlayerDB.id == player_id).first()
    db.close()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return {"id": player.id, "name": player.name, "score": player.score}

@app.post("/players")
def add_player(player: Player):
    db = SessionLocal()

    existing_player = db.query(PlayerDB).filter(PlayerDB.id == player.id).first()
    if existing_player:
        db.close()
        raise HTTPException(status_code=400, detail="ID already exists")

    new_player = PlayerDB(id=player.id, name=player.name, score=player.score)
    db.add(new_player)
    db.commit()
    db.refresh(new_player)

    result = {
        "message": "Player added",
        "player": {
            "id": new_player.id,
            "name": new_player.name,
            "score": new_player.score
        }
    }

    db.close()
    return result

@app.put("/players/{player_id}")
def update_player(player_id: int, updated_player: Player):
    db = SessionLocal()
    player = db.query(PlayerDB).filter(PlayerDB.id == player_id).first()

    if not player:
        db.close()
        raise HTTPException(status_code=404, detail="Player not found")

    player.id = updated_player.id
    player.name = updated_player.name
    player.score = updated_player.score

    db.commit()
    db.refresh(player)

    result = {
        "message": "Player updated",
        "player": {
            "id": player.id,
            "name": player.name,
            "score": player.score
        }
    }

    db.close()
    return result

@app.delete("/players/{player_id}")
def delete_player(player_id: int):
    db = SessionLocal()
    player = db.query(PlayerDB).filter(PlayerDB.id == player_id).first()

    if not player:
        db.close()
        raise HTTPException(status_code=404, detail="Player not found")

    db.delete(player)
    db.commit()
    db.close()

    return {"message": "Player deleted"}
