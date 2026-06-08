from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter(prefix="/queue", tags=["Queue"])


class JoinQueueRequest(BaseModel):
    user_id: int
    stake: int


@router.post("/join")
def join_queue(payload: JoinQueueRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.stake <= 0:
        raise HTTPException(status_code=400, detail="stake must be greater than 0")

    existing_entry = (
        db.query(models.QueueEntry)
        .filter(models.QueueEntry.user_id == payload.user_id)
        .first()
    )
    if existing_entry:
        raise HTTPException(status_code=400, detail="User already in queue")

    queue_entry = models.QueueEntry(
        user_id=payload.user_id,
        stake=payload.stake
    )
    db.add(queue_entry)
    db.commit()

    waiting_players = (
        db.query(models.QueueEntry)
        .filter(models.QueueEntry.stake == payload.stake)
        .order_by(models.QueueEntry.joined_at)
        .all()
    )

    if len(waiting_players) < 3:
        return {
            "message": "Joined queue, waiting for more players",
            "game_id": None
        }

    selected_players = waiting_players[:3]

    game = models.Game(
        stake=payload.stake,
        status="active"
    )
    db.add(game)
    db.commit()
    db.refresh(game)

    for entry in selected_players:
        game_player = models.GamePlayer(
            game_id=game.id,
            user_id=entry.user_id,
            current_game_score=0
        )
        db.add(game_player)

    first_question = db.query(models.Question).order_by(models.Question.id).first()
    if not first_question:
        raise HTTPException(status_code=404, detail="No questions found")

    game.current_question_id = first_question.id
    game.current_turn_user_id = selected_players[0].user_id

    for entry in selected_players:
        db.delete(entry)

    db.commit()
    db.refresh(game)

    return {
        "message": "Game created and started",
        "game_id": game.id,
        "status": game.status
    }

