from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Game, GamePlayer, User

router = APIRouter(prefix="/games", tags=["Games"])


@router.post("/")
def create_game(db: Session = Depends(get_db)):
    game = Game(
        stake=0,
        status="waiting"
    )
    db.add(game)
    db.commit()
    db.refresh(game)

    return {
        "game_id": game.id,
        "status": game.status,
        "stake": game.stake
    }


@router.post("/join")
def join_game(user_id: int, game_id: int = 1, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(GamePlayer).filter(
        GamePlayer.game_id == game_id,
        GamePlayer.user_id == user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already joined this game")

    game_player = GamePlayer(
        game_id=game_id,
        user_id=user_id,
    )
    db.add(game_player)

    if game.status == "waiting":
        game.status = "active"

    db.commit()
    db.refresh(game)

    all_players = db.query(GamePlayer).filter(GamePlayer.game_id == game_id).all()

    return {
        "message": f"User {user_id} joined game {game_id}",
        "game_id": game.id,
        "status": game.status,
        "player_ids": [p.user_id for p in all_players]
    }


@router.get("/{game_id}")
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    game_players = db.query(GamePlayer).filter(GamePlayer.game_id == game_id).all()

    players = []
    for gp in game_players:
        user = db.query(User).filter(User.id == gp.user_id).first()

        player_data = {
            "user_id": gp.user_id,
            "name": user.name if user else None
        }

        if hasattr(gp, "current_game_score"):
            player_data["current_game_score"] = gp.current_game_score

        players.append(player_data)

    return {
        "id": game.id,
        "game_id": game.id,
        "status": game.status,
        "stake": game.stake,
        "players": players
    }

