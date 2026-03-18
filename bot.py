from src.api.roostoo_client import RoostooClient
from src.config import ROOSTOO_API_KEY, ROOSTOO_SECRET_KEY
from src.logger import get_logger
from src.bot_loop import run_polling_loop

logger = get_logger()

def main():
    logger.info("Starting bot")
    
    client = RoostooClient(
        api_key=ROOSTOO_API_KEY,
        secret_key=ROOSTOO_SECRET_KEY,
        logger=logger
    )

    logger.info("Roostoo client created")

    print(client.get_server_time())
    # print(client.get_exchange_info())
    # print(client.get_ticker("BTC/USD"))
    # print(client.get_balance())
    # print(client.get_pending_count())

    # print(client.place_order("BNB/USD", "BUY", 1, order_type="MARKET"))
    # print(client.query_order(pair="BNB/USD", pending_only=False))
    # print(client.cancel_order(pair="BNB/USD"))

    run_polling_loop(
        client,
        pairs=["BTC/USD", "ETH/USD"],
        interval=10,
    )

if __name__ == "__main__":
    main()