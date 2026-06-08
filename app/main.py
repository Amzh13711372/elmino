from fastapi import FastAPI
from app.database import Base, engine
from app.routers import users, queue, games, categories, questions

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Elmino API")

app.include_router(users.router)
app.include_router(queue.router)
app.include_router(games.router)
app.include_router(categories.router)
app.include_router(questions.router)

