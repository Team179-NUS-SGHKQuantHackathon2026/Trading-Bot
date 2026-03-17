from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests


class RoostooHTTPError(RuntimeError):
    pass


class RoostooClient:
    def __init__(
        self,
        api_key: str,
        secret_key: str,
        base_url: str = "https://mock-api.roostoo.com",
        timeout: float = 10.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    @staticmethod
    def _timestamp_ms() -> str:
        return str(int(time.time() * 1000))

    @staticmethod
    def _normalize_pair(pair_or_coin: str) -> str:
        pair_or_coin = pair_or_coin.strip().upper()
        return pair_or_coin if "/" in pair_or_coin else f"{pair_or_coin}/USD"

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        resp = self.session.get(
            f"{self.base_url}{path}",
            params=params or {},
            timeout=self.timeout,
        )
        self._raise_for_http_error(resp)
        return resp.json()

    @staticmethod
    def _raise_for_http_error(resp: requests.Response) -> None:
        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            text = ""
            try:
                text = resp.text
            except Exception:
                pass
            raise RoostooHTTPError(f"HTTP {resp.status_code}: {text}") from exc

    def get_server_time(self) -> Dict[str, Any]:
        return self._get("/v3/serverTime")

    def get_exchange_info(self) -> Dict[str, Any]:
        return self._get("/v3/exchangeInfo")

    def get_ticker(self, pair: Optional[str] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"timestamp": self._timestamp_ms()}
        if pair:
            params["pair"] = self._normalize_pair(pair)
        return self._get("/v3/ticker", params)