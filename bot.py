from src.api.roostoo_client import RoostooClient
from src.config import ROOSTOO_API_KEY, ROOSTOO_SECRET_KEY

client = RoostooClient(
    api_key=ROOSTOO_API_KEY,
    secret_key=ROOSTOO_SECRET_KEY,
)

print(client.get_server_time())
print(client.get_exchange_info())
print(client.get_ticker("BTC/USD"))
print(client.get_balance())
print(client.get_pending_count())

# print(client.place_order("BNB/USD", "BUY", 1, order_type="MARKET"))
# print(client.query_order(pair="BNB/USD", pending_only=False))
# print(client.cancel_order(pair="BNB/USD"))