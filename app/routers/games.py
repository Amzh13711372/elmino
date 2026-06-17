from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter()


@router.post("/games/{game_id}/answer")
def submit_answer(
    game_id: int,
    payload: schemas.AnswerSubmit,
    db: Session = Depends(get_db)
):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game is not active")

    game_player = db.query(models.GamePlayer).filter(
        models.GamePlayer.game_id == game_id,
        models.GamePlayer.user_id == payload.user_id
    ).first()

    if not game_player:
        raise HTTPException(status_code=403, detail="User is not a participant in this game")

    if game.current_turn_user_id != payload.user_id:
        raise HTTPException(status_code=400, detail="It is not your turn")

    if payload.question_id != game.current_question_id:
        raise HTTPException(status_code=400, detail="Invalid question_id for current turn")

    question = db.query(models.Question).filter(
        models.Question.id == game.current_question_id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Current question not found")

    is_correct = payload.selected_option == question.correct_option

    if is_correct:
        game_player.current_game_score += 1

    players = db.query(models.GamePlayer).filter(
        models.GamePlayer.game_id == game.id
    ).all()

    player_ids = [p.user_id for p in players]

    current_index = player_ids.index(game_player.user_id)
    next_index = (current_index + 1) % len(player_ids)
    next_turn_user_id = player_ids[next_index]

    next_question = db.query(models.Question).filter(
        models.Question.id == game.current_question_id + 1
    ).first()

    if next_question:
        game.current_question_id = next_question.id
        game.current_turn_user_id = next_turn_user_id
    else:
        game.status = "finished"

        max_score = max(player.current_game_score for player in players)
        top_players = [
            player for player in players
            if player.current_game_score == max_score
        ]

        if len(top_players) == 1:
            game.winner_user_id = top_players[0].user_id
        else:
            game.winner_user_id = None

        game.current_turn_user_id = None
        game.current_question_id = None

    db.commit()
    db.refresh(game)

    return {
        "message": "Answer submitted successfully",
        "is_correct": is_correct,
        "your_score": game_player.current_game_score,
        "game_status": game.status,
        "winner_user_id": game.winner_user_id,
        "next_turn_user_id": game.current_turn_user_id,
        "current_question_id": game.current_question_id,
    }


@router.get("/games/{game_id}")
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    players = db.query(models.GamePlayer).filter(
        models.GamePlayer.game_id == game.id
    ).all()

    return {
        "id": game.id,
        "status": game.status,
        "stake": game.stake,
        "current_turn_user_id": game.current_turn_user_id,
        "current_question_id": game.current_question_id,
        "winner_user_id": game.winner_user_id,
        "players": [
            {
                "user_id": p.user_id,
                "score": p.current_game_score
            }
            for p in players
        ]
    }
