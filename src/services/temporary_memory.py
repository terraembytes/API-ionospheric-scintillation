import asyncio
from typing import Dict
from datetime import datetime, timezone, timedelta
from services.data_processor import IsmrQueryToolAPIClient

class DataService:
    def __init__(self):
        # Cache armazena: {(start, end, station): dados_processados}
        self._cache: Dict[tuple, list] = {}
        self._cache_lock = asyncio.Lock()
        # Cache token para armazenar o token da requisicao
        self._cache_token: str | None = None
        self._token_expires_at: datetime | None = None
        self._token_lock = asyncio.Lock()

    def _is_token_expired(self) -> bool:
        if self._token_expires_at is None:
            return True
        safety_buffer = timedelta(minutes=5)
        return datetime.now(timezone.utc) >= self._token_expires_at - safety_buffer

    async def get_data(self, api_client: IsmrQueryToolAPIClient, start: str, end: str, station: str):
        cache_key = (start, end, station)

        async with self._cache_lock:
            if cache_key in self._cache:
                print(f"Cache hit: Usando dados em memória para {cache_key}")
                return self._cache[cache_key]

            try:
                print(f"Cache miss: Buscando na API ISMR para {cache_key}...")
                async with self._token_lock:
                    if self._is_token_expired is None or self._is_token_expired():
                        print("Buscando novo token...")
                        self._cache_token, self._token_expires_at = await api_client._get_token()

                data = await api_client.get_dados(start=start, end=end, station=station, token=self._cache_token)
        
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