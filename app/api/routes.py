from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas, tasks

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/jd/")
def add_jd(jd: schemas.JDInput, email: str, db: Session = Depends(get_db)):
    new_jd = models.JobDescription(**jd.dict())
    db.add(new_jd)
    db.commit()
    db.refresh(new_jd)
    tasks.process_matching.delay(new_jd.id, email)
    return {"msg": "JD added and processing started"}
