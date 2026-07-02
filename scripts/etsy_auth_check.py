import os

import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("ETSY_API_KEY")
secret = os.getenv("ETSY_SHARED_SECRET")

url = "https://openapi.etsy.com/v3/application/listings/active"
headers = {
    "x-api-key": f"{key}:{secret}",
    "Accept": "application/json",
}
params = {"keywords": "baseball coach gift", "limit": 1}

response = requests.get(url, headers=headers, params=params, timeout=30)
print("Status:", response.status_code)
print(response.text[:2000])
