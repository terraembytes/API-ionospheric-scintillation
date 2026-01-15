from typing import Dict, List
from services.data_processor import IsmrQueryToolAPIClient

class DataService:
    def __init__(self):
        # Cache armazena: {(start, end, station): dados_processados}
        self._cache: Dict[tuple, list] = {}

    async def get_data(self, api_client: IsmrQueryToolAPIClient, start: str, end: str, station: str):
        cache_key = (start, end, station)

        if cache_key in self._cache:
            print(f"Cache hit: Usando dados em memória para {cache_key}")
            return self._cache[cache_key]

        print(f"Cache miss: Buscando na API ISMR para {cache_key}...")
        try:
            data = await api_client.get_dados(start=start, end=end, station=station)
            
            processed_data = [
                {
                    "Date": item.get('time_utc'), 
                    'Svid': item.get('svid'), 
                    'S4': item.get('s4'), 
                    'Elevation': item.get('elev'), 
                    'Azimute': item.get('azim'), 
                    'Intensity': item.get('avg_cn0_l1')
                } 
                for item in data.get('data', [])
            ]
            
            self._cache[cache_key] = processed_data
            return processed_data

        except Exception as e:
            raise e

data_service = DataService()

# Função de Dependência para o FastAPI
def get_data_service():
    return data_service