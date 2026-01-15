from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from services.data_processor import IsmrQueryToolAPIClient, get_ISMR_API_client
from utils.helpers import verificar_parametros_iguais, group_s4, filter_constella_elev, cut_hour_range
from httpx import ReadTimeout

router = APIRouter(tags=["data"])

params = {
    'start': None,
    'end': None,
    'station': None
}

dados = None

# rota padrão, podendo receber query params
@router.get("v1/data/")
async def get_datas(
    elev: int, 
    elevType: int, 
    constellation: str, 
    start: str, 
    end: str, 
    station: str, 
    hour_range: int | None,
    date_selected: str | None,
    api_client: Annotated[IsmrQueryToolAPIClient, Depends(get_ISMR_API_client)]
    ):
    global dados
    if dados != None and verificar_parametros_iguais(params, start, end, station):
        data_cut = cut_hour_range(hour_range, date_selected, dados)
        data_filtered = filter_constella_elev(data_cut, constellation, elev, elevType)
        return {'data': data_filtered}
    else:
        params['start'] = start
        params['end'] = end
        params['station'] = station
        print('Buscando os dados...')
        try:
            data = await api_client.get_dados(start=start, end=end, station=station)
            processed_data = [{"Date": item['time_utc'], 'Svid': item['svid'], 'S4': item['s4'], 'Elevation': item['elev', 'Azimute': item['azim'], 'Intensity': item['avg_cn0_l1']]} for item in data.get('data', [])]
            dados = processed_data
            data_cut = cut_hour_range(hour_range, date_selected, dados)
            data_filtered2 = filter_constella_elev(data_cut, constellation, elev, elevType)
            return {'data': data_filtered2}
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

# rota para o grafico de contagem do indice S4
@router.get("v1/data/contGraphs/")
async def filter_cont_s4(elev: int, elevType: int, constellation: str, time: str, start: str, end: str, station: str, api_client: Annotated[IsmrQueryToolAPIClient, Depends(get_ISMR_API_client)]):
    global dados
    if dados != None and verificar_parametros_iguais(params, start, end, station):
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