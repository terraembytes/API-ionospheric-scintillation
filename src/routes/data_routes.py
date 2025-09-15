from fastapi import APIRouter, Depends
import pandas as pd
from typing import Annotated
from services.data_processor import IsmrQueryToolAPIClient, get_ISMR_API_client
from utils.helpers import verificar_parametros_iguais

router = APIRouter(tags=["data"])

params = {
    'start': None,
    'end': None,
    'station': None
}

dados: any = None

@router.get("/data/{start}/{end}/{station}")
async def get_data(
    start: str,
    end: str, 
    station: str,
    api_client: Annotated[IsmrQueryToolAPIClient, Depends(get_ISMR_API_client)]
):
    global dados
    if verificar_parametros_iguais(params, start, end, station):
        print('retornando dados repetidos')
        return {'data': dados}
    else:
        params['start'] = start
        params['end'] = end
        params['station'] = station
        print('Buscando os dados...')
        data = await api_client.get_dados(start=start, end=end, station=station)
        processed_data = [{"Date": item['time_utc'], 'Svid': item['svid'], 'S4': item['s4'], 'Elevation': item['elev']} for item in data.get('data', [])]
        dados = processed_data
        return {'data': processed_data}

@router.get("/data/{start}/{end}/{station}?elev={elev}")
def get_single_item(item_id: int):
    return {f"Exibindo as informações do item {item_id}"}