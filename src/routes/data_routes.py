from fastapi import APIRouter
import pandas as pd

router = APIRouter(tags=["data"])

@router.get("/data/")
def get_data():
    return {"lista com os dados"}

@router.get("/data/{item_id}")
def get_single_item(item_id: int):
    return {f"Exibindo as informações do item {item_id}"}