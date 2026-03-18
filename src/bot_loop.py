import time
from typing import Sequence

from src.api.roostoo_client import RoostooClient
from src.logger import get_logger


def run_polling_loop(client: RoostooClient, pairs: Sequence[str], interval: int = 10):
    logger = get_logger()
    latest_prices = {}

    while True:
        try:
            balance = client.get_balance()
            all_tickers = client.get_ticker()

            logger.info(f"Balance: {balance}")

            ticker_data = all_tickers.get("Data", {})

            for pair in pairs:
                normalized_pair = client._normalize_pair(pair)
                pair_ticker = ticker_data.get(normalized_pair)

                if pair_ticker is None:
                    logger.warning(f"No ticker data for {normalized_pair}")
                    continue

                last_price = pair_ticker.get("LastPrice")
                latest_prices[normalized_pair] = last_price

                logger.info(f"{normalized_pair} last price: {last_price}")

        except Exception as e:
            logger.exception(f"Polling loop failed: {e}")

        time.sleep(interval)