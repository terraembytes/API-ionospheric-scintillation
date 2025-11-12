from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from services.data_processor import IsmrQueryToolAPIClient, get_ISMR_API_client
from utils.helpers import verificar_parametros_iguais, group_s4, constellation_filter, elevation_filter, filter_constella_elev
from httpx import ReadTimeout

router = APIRouter(tags=["data"])

params = {
    'start': None,
    'end': None,
    'station': None
}

dados = None

# rota padrão para os dados gerais
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
        try:
            data = await api_client.get_dados(start=start, end=end, station=station)
            processed_data = [{"Date": item['time_utc'], 'Svid': item['svid'], 'S4': item['s4'], 'Elevation': item['elev']} for item in data.get('data', [])]
            dados = processed_data
            return {'data': processed_data}
        except ReadTimeout: # demorou muito para responder
            raise HTTPException(
                status_code=504, 
                detail="A API externa (ISMR) demorou muito para responder."
            )
        except ConnectionError: # não conseguiu se conectar
            raise HTTPException(
                status_code=503,
                detail="Não foi possível conectar com a API externa (ISMR)"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao processar os dados: {e}"
            )


# rota de filtragem dos dados gerais
@router.get("/data/filters/geral/")
async def filter_geral_datas(elev: int = 0, elevType: int = 1, constellation: str = 'ALL'):
    if dados != None:
        data_filtered = filter_constella_elev(dados, constellation, elev, elevType)
    else:
        data_filtered = dados
        print("dados vazios...")
    return {'data': data_filtered}

# rota para o grafico de contagem do indice S4
@router.get("/data/filters/contGraphs/")
async def filter_cont_s4(elev: int, elevType: int, constellation: str, time: str, start: str, end: str, station: str, api_client: Annotated[IsmrQueryToolAPIClient, Depends(get_ISMR_API_client)]):
    global dados
    if dados != None:
        data_filtered2 = filter_constella_elev(dados, constellation, elev, elevType)
        print("Agrupando os valores de S4...")
        data_filtered3 = group_s4(data_filtered2, constellation, time)
        return {'data': data_filtered3}
    else:
        params['start'] = start
        params['end'] = end
        params['station'] = station
        print('Buscando os dados...')
        try:
            data = await api_client.get_dados(start=start, end=end, station=station)
            processed_data = [{"Date": item['time_utc'], 'Svid': item['svid'], 'S4': item['s4'], 'Elevation': item['elev']} for item in data.get('data', [])]
            dados = processed_data
            data_filtered2 = filter_constella_elev(dados, constellation, elev, elevType)
            print("Agrupando os valores de S4...")
            data_filtered3 = group_s4(data_filtered2, constellation, time)
            return {'data': data_filtered3}
        except ReadTimeout:
            raise HTTPException(
                status_code=504, 
                detail="A API externa (ISMR) demorou muito para responder."
            )
        except ConnectionError: # não conseguiu se conectar
            raise HTTPException(
                status_code=503,
                detail="Não foi possível conectar com a API externa (ISMR)"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao processar os dados: {e}"
            )