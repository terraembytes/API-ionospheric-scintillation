from typing import Union
from fastapi import FastAPI
from routes import data_routes
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Lista de origens permitidas
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Permite as origens da lista
    allow_credentials=True,
    allow_methods=["*"], # Permite todos os métodos (GET, POST, etc)
    allow_headers=["*"], # Permite todos os cabeçalhos
)

app.include_router(data_routes.router, prefix="/api")

@app.get("/")
def read_root():
    return {"Hello World!"}