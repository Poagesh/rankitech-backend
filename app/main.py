# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes
from app.models import Base
from app.database import engine, SessionLocal  
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up... Creating tables")
    Base.metadata.create_all(bind=engine)

    yield  

    print("Shutting down... Cleaning up")
    try:
        db = SessionLocal()
        db.close()
        print("Database session closed.")
    except Exception as e:
        print("Error while closing DB session:", e)


app = FastAPI(title="Rankitech Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api", tags=["api"])
