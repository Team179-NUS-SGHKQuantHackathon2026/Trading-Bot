from src.api.roostoo_client import RoostooClient
from src.config import ROOSTOO_API_KEY, ROOSTOO_SECRET_KEY

client = RoostooClient(
    api_key=ROOSTOO_API_KEY,
    secret_key=ROOSTOO_SECRET_KEY,
)

print(client.get_server_time())
print(client.get_exchange_info())
print(client.get_ticker("BTC/USD"))