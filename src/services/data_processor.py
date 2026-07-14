import io
import csv
import zipfile
import json

import httpx
from typing import Optional
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import logging
from exceptions.ISMR_exception import ISMRDataFetchError

logger = logging.getLogger(__name__)

class IsmrQueryToolAPIClient:
    def __init__(self, url_base: str, user_email: str, user_password: str):
        # configurando o time_out
        time_config = httpx.Timeout(30.0, connect=60.0)

        # Inicializa o cliente HTTPX com suporte a HTTP/2
        self._client = httpx.AsyncClient(base_url = url_base, http2 = True, verify=False, timeout=time_config)
        self._client_email = user_email
        self._client_password = user_password
        self._token: Optional[str] = None
        self._token_expires_at: datetime

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self._client.aclose()
    
    async def _get_token(self) -> tuple[str, datetime]:
        # request body da API ISMR
        login_data = {
            "email": self._client_email,
            "password": self._client_password
        }

        try:
            response = await self._client.post("api/v1/user/token", json=login_data)
            # armazena uma resposta da API, se deu tudo certo, vai fazer nada, mas caso tenha um erro 4xx ou 5xx irá salvar o erro
            response.raise_for_status()
            # armazenando os dados do token
            token_data = response.json()

            token = token_data['access_token']
            expires_in_response = token_data.get("expires_at")
            # convertendo a string no formato datetime do python
            expires_in = datetime.fromisoformat(expires_in_response)

            print("Novo token adquirido")
            return token, expires_in
        except httpx.HTTPStatusError as e:
            print(f'Erro ao obter o token: {e.response.status_code} - {e.response.text}')
            raise # sinaliza que houve uma execessão
    
    async def get_dados(self, start: str, end: str, station: str, token: str) -> dict:

        header = {
            "Authorization": f'Bearer {token}',
            # "type": "json",
            # "fields": "time_utc,svid,s4,elev,azim,avg_cn0_l1"
        }

        params = {
            "start": start,
            "end": end,
            "station": station
        }
        try:
            response = await self._client.get("api/v1/data/download/ismr/file", headers=header, params=params)
            response.raise_for_status()
            print('Descompactando os dados...')
            
            zip_buffer = io.BytesIO(response.content)

            consolidated_data = []

            with zipfile.ZipFile(zip_buffer) as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith('.ismr'):
                        with zip_ref.open(file) as extracted_file:
                            text_content = io.TextIOWrapper(extracted_file, encoding='utf-8-sig')
                            csv_reader = csv.DictReader(text_content)
                            for row in csv_reader:
                                consolidated_data.append(dict(row))
            return {"data": consolidated_data}
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            logger.error(f"Erro {status} na API da ISMR para estação {station}")
            raise ISMRDataFetchError(f"Falha no servidor de origem dos dados ISMR", original_status=status)
        except httpx.RequestError as e:
            logger.error(f"Falha de conexão ao tentar acessar a ISMR: {e}")
            raise ISMRDataFetchError("Não foi possível conectar ao serviço de dados externo (ISMR)")

async def get_ISMR_API_client():
    # carregando as credenciais das variaveis ambiente
    # carrega os dados do arquivo .env
    load_dotenv()
    
    email = os.getenv('TOKEN_EMAIL')
    senha = os.getenv('TOKEN_PASSWORD')
    url = os.getenv('URL_ISMR_API')

    client = IsmrQueryToolAPIClient(
        url_base=url,
        user_email=email,
        user_password=senha
    )

    try:
        yield client
    finally:
        await client.close()