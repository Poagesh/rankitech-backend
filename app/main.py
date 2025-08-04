# app/main.py
from fastapi import FastAPI
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
app.include_router(routes.router)
