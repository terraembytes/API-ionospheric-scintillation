from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated
from services.data_processor import IsmrQueryToolAPIClient, get_ISMR_API_client
from utils.helpers import group_s4, filter_constella_elev, cut_hour_range, constellation_filter, get_s4_higher_equals, transform_to_radian, convert_to_xyScale, create_cluster, get_polygons
from httpx import ReadTimeout
from services.temporary_memory import DataService, get_data_service
import traceback

router = APIRouter(tags=["data"])

params = {
    'start': None,
    'end': None,
    'station': None
}

dados = None

# rota padrão, podendo receber query params
@router.get("/v1/data/")
async def get_datas(
    elev: int, 
    elevType: int, 
    constellation: str, 
    start: str, 
    end: str, 
    station: str, 
    api_client: Annotated[IsmrQueryToolAPIClient, Depends(get_ISMR_API_client)],
    service: Annotated[DataService, Depends(get_data_service)],
    hour_range: int | None = Query(default=None, alias="hourRange"),
    date_selected: str | None = Query(default=None, alias="dateSelected")
    ):
    
    try:
        # Chama o método do serviço importado
        dados_brutos = await service.get_data(api_client, start, end, station)

        data_cut = cut_hour_range(hour_range, date_selected, dados_brutos)
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
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar os dados: {e}"
        )

# rota para o grafico de contagem do indice S4
@router.get("/v1/data/contGraphs/")
async def filter_cont_s4(
    elev: int, 
    elevType: int, 
    constellation: str, 
    time: str, 
    start: str, 
    end: str, 
    station: str, 
    api_client: Annotated[IsmrQueryToolAPIClient, Depends(get_ISMR_API_client)],
    service: Annotated[DataService, Depends(get_data_service)]
    ):
    try:
        dados_brutos = await service.get_data(api_client, start, end, station)
        
        data_filtered2 = filter_constella_elev(dados_brutos, constellation, elev, elevType)
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
    
@router.get("v1/data/skyplot-polygon/")
async def get_skyplot_polygon(
    constellation: str, 
    start: str, 
    end: str, 
    station: str, 
    api_client: Annotated[IsmrQueryToolAPIClient, Depends(get_ISMR_API_client)],
    service: Annotated[DataService, Depends(get_data_service)],
    hour_range: int | None = Query(default=None, alias="hourRange"),
    date_selected: str | None = Query(default=None, alias="dateSelected")
):
    try:
        dados_brutos = await service.get_data(api_client, start, end, station)

        data_cut = cut_hour_range(hour_range, date_selected, dados_brutos)
        data_constellation = constellation_filter(constellation, data_cut)
        data_s4 = get_s4_higher_equals(0.6, data_constellation)
        data_values_converted = transform_to_radian(data_s4)
        xy_scale = convert_to_xyScale(data_values_converted)
        clusters = create_cluster(xy_scale, 9, 5)
        list_polygons = get_polygons(clusters, xy_scale)

        return {'data': {'data': data_constellation, 'polygons': list_polygons}}

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