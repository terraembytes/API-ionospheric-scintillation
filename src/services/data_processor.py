import requests
import os
from dotenv import load_dotenv
import datetime
# https://api-ismrquerytool.fct.unesp.br/

url = "https://api-ismrquerytool.fct.unesp.br/"

url_token = url + "api/v1/user/token"
url_get_data = url + "api/v1/data/download/ismr/file"

# carrega os dados do arquivo .env
load_dotenv()

email = os.getenv('TOKEN_EMAIL')
senha = os.getenv('TOKEN_PASSWORD')

token = any
time_now = any

def create_token():
    res = requests.post(url_token, json={"email": email, "password": senha})
    return res

def verify_expired_token():
    time = datetime.datetime.now().time()

    if(time >= (time_now + datetime.timedelta(minutes=15))):
        token = create_token()
        time_now = time_now = datetime.datetime.now().time()

if(token == any):
    token = create_token()
    time_now = datetime.datetime.now().time()

