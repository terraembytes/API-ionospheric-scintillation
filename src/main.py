from typing import Union
from fastapi import FastAPI
from routes import data_routes

app = FastAPI()
app.include_router(data_routes.router, prefix="/api")

@app.get("/")
def read_root():
    return {"Hello World!"}