import os 
import requests

api_key = os.environ.get("MINIMAX_API_KEY") # Type your api key

url = f'https://api.minimax.io/v1/get_voice'
headers = {
    'authority': 'api.minimax.io',
    'Authorization': f'Bearer {api_key}'
}

data = {
    'voice_type': 'system'
}

response = requests.post(url, headers=headers, data=data)
print(response.status_code)
if response.status_code == 200:
    print(response.json())