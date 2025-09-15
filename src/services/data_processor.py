import httpx
from typing import Optional
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

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

    def _is_token_expired(self) -> bool:
        safety_buffer = timedelta(minutes=30)
        # verifica se o token expirou ou está prestes a expirar
        return not self._token or datetime.now(timezone.utc) >= self._token_expires_at - safety_buffer
    
    async def _get_token(self) -> str:
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

            self._token = token_data['access_token']
            expires_in_response = token_data.get("expires_at")
            # convertendo a string no formato datetime do python
            expires_in = datetime.fromisoformat(expires_in_response)
            self._token_expires_at = expires_in

            print("Novo token adquirido")
            return self._token
        except httpx.HTTPStatusError as e:
            print(f'Erro ao obter o token: {e.response.status_code} - {e.response.text}')
            raise # sinaliza que houve uma execessão
    
    async def get_dados(self, start: str, end: str, station: str) -> dict:
        #verificando a validade do token
        if self._is_token_expired():
            print("Token expirado ou prestes a expirar! Renovando...")
            await self._get_token()

        header = {
            "Authorization": f'Bearer {self._token}',
            "type": "json",
            "fields": "time_utc,svid,s4,elev"
        }

        params = {
            "start": start,
            "end": end,
            "station": station
        }

        try:
            response = await self._client.get("api/v1/data/download/ismr/file", headers=header, params=params)
            response.raise_for_status()
            print('Retornando os dados...')
            return response.json()
        except httpx.HTTPStatusError as e:
            # verificando caso o token tenha dado erro
            if e.response.status_code == 401:
                print('Token invalido (fallback). Tentando renovar...')
                await self._get_token()
                # repete a requisição
                header = {"Authorization": f'Bearer {self._token}', "type": "json", "fields": "time_utc,svid,s4,elev"}
                response = await self._client.get("api/v1/data/download/ismr/file", header=header, params=params)
                response.raise_for_status()
                print('Retornando os dados...')
                return response.json()
            
            print(f"Erro ao buscar itens: {e.response.status_code} - {e.response.text}")
            raise

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