from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.base import Base
from app.db.models import LineItemModel, MealSessionModel
from app.api import routes
from app.api.routes import router


app = FastAPI(title="等锅叫号 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def create_development_tables():
    Base.metadata.create_all(bind=routes.engine)
