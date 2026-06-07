from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/queue", tags=["Queue"])


@router.post("/join", response_model=schemas.QueueJoinResponse)
def join_queue(payload: schemas.QueueJoinRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_waiting = (
        db.query(models.GameQueueEntry)
        .filter(
            models.GameQueueEntry.user_id == payload.user_id,
            models.GameQueueEntry.status == "waiting"
        )
        .first()
    )
    if existing_waiting:
        raise HTTPException(status_code=400, detail="User is already in queue")

    queue_entry = models.GameQueueEntry(
        user_id=payload.user_id,
        stake=payload.stake,
        status="waiting"
    )
    db.add(queue_entry)
    db.commit()
    db.refresh(queue_entry)

    waiting_players = (
        db.query(models.GameQueueEntry)
        .filter(
            models.GameQueueEntry.stake == payload.stake,
            models.GameQueueEntry.status == "waiting"
        )
        .order_by(models.GameQueueEntry.created_at.asc())
        .all()
    )

    if len(waiting_players) < 3:
        return {
            "message": "Added to queue. Waiting for more players.",
            "game_id": None,
            "status": "waiting"
        }

    selected_players = waiting_players[:3]

    game = models.Game(
        stake=payload.stake,
        status="active",
        current_turn_user_id=selected_players[0].user_id,
        turn_deadline=datetime.now(timezone.utc) + timedelta(seconds=120)
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
        entry.status = "matched"

    db.commit()

    return {
        "message": "Game created successfully",
        "game_id": game.id,
        "status": "matched"
    }
