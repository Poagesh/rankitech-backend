from fastapi import FastAPI
from app.api import routes

app = FastAPI(title="Rankitech Backend")
app.include_router(routes.router)
