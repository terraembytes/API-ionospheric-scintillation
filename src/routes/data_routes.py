from fastapi import APIRouter, Depends
from pydantic import BaseModel
import pandas as pd
from typing import Annotated, List
from services.data_processor import IsmrQueryToolAPIClient, get_ISMR_API_client
from utils.helpers import verificar_parametros_iguais

router = APIRouter(tags=["data"])

params = {
    'start': None,
    'end': None,
    'station': None
}

dados: any = None

dict_constellations = {
    'ALL': range(1, 177),
    'GPS': range(1, 37),
    'GLONASS': range(38, 68),
    'GALILEO': range(71, 102),
    'BeiDou': range(141, 177)
}

@router.get("/data/")
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

@router.get("/data/filters/geral/")
async def filter_geral_datas(elev: int = 0, elevType: int = 1, constellation: str = 'ALL'):
    global dados
    if dados != None:
        print("Filtrando por constelação...")
        if constellation != 'ALL':
            data_filtered1 = constellation_filter(constellation)
        else:
            data_filtered1 = dados
        print("Filtrando a elevação...")
        data_filtered = elevation_filter(elev, elevType, data_filtered1)
    else:
        data_filtered = dados
        print("dados vazios...")
    return {'data': data_filtered}

def constellation_filter(constellation: str) -> list[dict]:
    global dict_constellations, dados
    values = dict_constellations.get(constellation, [])
    data_copy = [linha for linha in dados if linha['Svid'] in values]
    return data_copy

def elevation_filter(elev: int, elevType: int, data_copy: list[dict]) -> list[dict]:
    data_pre_processed = [{**linha, 'Elevation': linha.get('Elevation') or 0} for linha in data_copy]
    match elevType:
        case 1:
            data_processed = [linha for linha in data_pre_processed if int(linha['Elevation']) >= elev]
            print(f"Filtrando a elevação >= {elev}")
        case 2:
            data_processed = [linha for linha in data_pre_processed if int(linha['Elevation']) <= elev]
            print(f"Filtrando a elevação <= {elev}")
        case 3:
            data_processed = [linha for linha in data_pre_processed if int(linha['Elevation']) == elev]
            print(f"Filtrando a elevação == {elev}")
        case 4:
            data_processed = [linha for linha in data_pre_processed if int(linha['Elevation']) > elev]
            print(f"Filtrando a elevação > {elev}")
        case 5:
            data_processed = [linha for linha in data_pre_processed if int(linha['Elevation']) >= elev]
            print(f"Filtrando a elevação < {elev}")
        case _:
            data_processed = []
            print("tipo de filtro invalido")
    return data_processed