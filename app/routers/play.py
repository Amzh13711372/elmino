from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import models, schemas

router = APIRouter(prefix="/play", tags=["Play"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_next_player(game_id: int, current_user_id: int, db: Session):
    players = (
        db.query(models.GamePlayer)
        .filter(models.GamePlayer.game_id == game_id)
        .order_by(models.GamePlayer.id.asc())
        .all()
    )

    if not players:
        return None

    user_ids = [p.user_id for p in players]

    if current_user_id not in user_ids:
        return user_ids[0]

    current_index = user_ids.index(current_user_id)
    next_index = (current_index + 1) % len(user_ids)
    return user_ids[next_index]


def finish_game(game, winner_user_id: int, db: Session):
    players = (
        db.query(models.GamePlayer)
        .filter(models.GamePlayer.game_id == game.id)
        .all()
    )

    sorted_players = sorted(
        players,
        key=lambda p: p.current_game_score,
        reverse=True
    )

    for index, player in enumerate(sorted_players, start=1):
        player.rank = index
        user = db.query(models.User).filter(models.User.id == player.user_id).first()
        if user:
            if index == 1:
                user.score += 500
            elif index == 2:
                user.score += 200
            elif index == 3:
                user.score += 100

    game.status = "finished"
    game.current_turn_user_id = None
    game.turn_deadline = None

    db.commit()


@router.post("/answer")
def submit_answer(
    game_id: int,
    payload: schemas.AnswerRequest,
    db: Session = Depends(get_db)
):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game is not active")

    player = (
        db.query(models.GamePlayer)
        .filter(
            models.GamePlayer.game_id == game_id,
            models.GamePlayer.user_id == payload.user_id
        )
        .first()
    )
    if not player:
        raise HTTPException(status_code=404, detail="Player not in this game")

    if game.current_turn_user_id != payload.user_id:
        raise HTTPException(status_code=400, detail="It is not your turn")

    now = datetime.now(timezone.utc)

    if game.turn_deadline and now > game.turn_deadline:
        player.current_game_score = max(0, player.current_game_score - 50)

        next_user_id = get_next_player(game.id, payload.user_id, db)
        game.current_turn_user_id = next_user_id
        game.turn_deadline = now + timedelta(seconds=120)

        db.commit()

        return {
            "message": "Time is over. 50 points deducted.",
            "current_game_score": player.current_game_score,
            "next_turn_user_id": next_user_id,
            "turn_deadline": str(game.turn_deadline)
        }

    question = (
        db.query(models.Question)
        .order_by(models.Question.id.asc())
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="No questions found")

    if payload.answer.strip().lower() == question.correct_answer.strip().lower():
        player.current_game_score += 100
        result_message = "Correct answer. 100 points added."
    else:
        player.current_game_score = max(0, player.current_game_score - 50)
        result_message = "Wrong answer. 50 points deducted."

    if player.current_game_score >= 500:
        finish_game(game, payload.user_id, db)
        return {
            "message": "Game finished",
            "winner_user_id": payload.user_id,
            "final_score": player.current_game_score,
            "game_status": "finished"
        }

    next_user_id = get_next_player(game.id, payload.user_id, db)
    game.current_turn_user_id = next_user_id
    game.turn_deadline = now + timedelta(seconds=120)

    db.commit()

    return {
        "message": result_message,
        "current_game_score": player.current_game_score,
        "next_turn_user_id": next_user_id,
        "turn_deadline": str(game.turn_deadline)
    }

