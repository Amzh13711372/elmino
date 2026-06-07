from fastapi import FastAPI
from app.database import engine
from app import models
from app.routers import users, categories, questions, games, play, queue

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Elmino API", version="0.3.0")


@app.get("/")
def root():
    return {"message": "Welcome to Elmino API"}


app.include_router(users.router)
app.include_router(categories.router)
app.include_router(questions.router)
app.include_router(games.router)
app.include_router(play.router)
app.include_router(queue.router)

