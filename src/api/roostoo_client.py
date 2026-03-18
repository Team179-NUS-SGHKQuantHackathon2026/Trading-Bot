from __future__ import annotations

import hashlib
import hmac
import logging
import time
from decimal import Decimal, ROUND_DOWN
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
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.logger = logger

        self._exchange_info_cache: Optional[Dict[str, Any]] = None

    @staticmethod
    def _timestamp_ms() -> str:
        return str(int(time.time() * 1000))

    @staticmethod
    def _normalize_pair(pair_or_coin: str) -> str:
        pair_or_coin = pair_or_coin.strip().upper()
        return pair_or_coin if "/" in pair_or_coin else f"{pair_or_coin}/USD"
    
    def refresh_exchange_info_cache(self) -> Dict[str, Any]:
        data = self.get_exchange_info()
        self._exchange_info_cache = data
        return data

    def get_symbol_info(self, pair: str) -> Dict[str, Any]:
        normalized_pair = self._normalize_pair(pair)

        if self._exchange_info_cache is None:
            self.refresh_exchange_info_cache()

        trade_pairs = self._exchange_info_cache.get("TradePairs", {})
        if normalized_pair not in trade_pairs:
            raise ValueError(f"Pair not found in exchangeInfo: {normalized_pair}")

        return trade_pairs[normalized_pair]

    @staticmethod
    def _round_down_by_precision(value: Decimal, precision: int) -> Decimal:
        quantum = Decimal("1").scaleb(-precision)
        return value.quantize(quantum, rounding=ROUND_DOWN)

    def round_price(self, pair: str, price: float | str | Decimal) -> str:
        info = self.get_symbol_info(pair)
        precision = int(info["PricePrecision"])
        rounded = self._round_down_by_precision(Decimal(str(price)), precision)
        return format(rounded, f".{precision}f")

    def round_quantity(self, pair: str, quantity: float | str | Decimal) -> str:
        info = self.get_symbol_info(pair)
        precision = int(info["AmountPrecision"])
        rounded = self._round_down_by_precision(Decimal(str(quantity)), precision)
        return format(rounded, f".{precision}f")

    def is_tradable(self, pair: str) -> bool:
        info = self.get_symbol_info(pair)
        return bool(info["CanTrade"])

    def validate_limit_order(
        self,
        pair: str,
        price: float | str | Decimal,
        quantity: float | str | Decimal,
    ) -> None:
        info = self.get_symbol_info(pair)

        if not info["CanTrade"]:
            raise ValueError(f"{self._normalize_pair(pair)} is not tradable")

        rounded_price = Decimal(self.round_price(pair, price))
        rounded_quantity = Decimal(self.round_quantity(pair, quantity))
        min_order = Decimal(str(info["MiniOrder"]))

        if rounded_price <= 0:
            raise ValueError("Rounded price must be > 0")
        if rounded_quantity <= 0:
            raise ValueError("Rounded quantity must be > 0")

        notional = rounded_price * rounded_quantity
        if notional <= min_order:
            raise ValueError(
                f"Order value {notional} must be > MiniOrder {min_order}"
            )

    def _get_signed_headers(self, payload: Optional[Dict[str, Any]] = None):
        """
        Generate signed headers and totalParams for RCL_TopLevelCheck endpoints.
        """
        payload = dict(payload or {})
        payload["timestamp"] = self._timestamp_ms()

        sorted_keys = sorted(payload.keys())
        total_params = "&".join(f"{k}={payload[k]}" for k in sorted_keys)

        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            total_params.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        headers = {
            "RST-API-KEY": self.api_key,
            "MSG-SIGNATURE": signature,
        }

        return headers, payload, total_params

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, signed: bool = False) -> Dict[str, Any]:
        payload = dict(params or {})
        headers = {}

        if signed:
            headers, payload, _ = self._get_signed_headers(payload)

        if self.logger:
            self.logger.info(f"GET {path} | signed={signed} | params={payload}")

        resp = self.session.get(
            f"{self.base_url}{path}",
            params=payload,
            headers=headers,
            timeout=self.timeout,
        )

        if self.logger:
            self.logger.info(f"GET {path} | status={resp.status_code} | response={resp.text}")

        self._raise_for_http_error(resp)
        return resp.json()


    def _post(self, path: str, payload: Optional[Dict[str, Any]] = None, signed: bool = False) -> Dict[str, Any]:
        body_payload = dict(payload or {})
        headers = {}
        data: Any = body_payload

        if signed:
            headers, body_payload, total_params = self._get_signed_headers(body_payload)
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            data = total_params

        if self.logger:
            self.logger.info(f"POST {path} | signed={signed} | payload={body_payload}")

        resp = self.session.post(
            f"{self.base_url}{path}",
            headers=headers,
            data=data,
            timeout=self.timeout,
        )

        if self.logger:
            self.logger.info(f"POST {path} | status={resp.status_code} | response={resp.text}")

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

    # Public Endpoints
    def get_server_time(self) -> Dict[str, Any]:
        return self._get("/v3/serverTime")

    def get_exchange_info(self) -> Dict[str, Any]:
        return self._get("/v3/exchangeInfo")

    def get_ticker(self, pair: Optional[str] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"timestamp": self._timestamp_ms()}
        if pair:
            params["pair"] = self._normalize_pair(pair)
        return self._get("/v3/ticker", params)

    # Signed Endpoints
    def get_balance(self) -> Dict[str, Any]:
        return self._get("/v3/balance", signed=True)

    def get_pending_count(self) -> Dict[str, Any]:
        return self._get("/v3/pending_count", signed=True)

    def place_order(
        self,
        pair: str,
        side: str,
        quantity: float,
        *,
        order_type: str = "MARKET",
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        side = side.upper()
        order_type = order_type.upper()
        normalized_pair = self._normalize_pair(pair)

        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if order_type not in {"MARKET", "LIMIT"}:
            raise ValueError("order_type must be MARKET or LIMIT")

        if not self.is_tradable(normalized_pair):
            raise ValueError(f"{normalized_pair} is not tradable")

        rounded_quantity = self.round_quantity(normalized_pair, quantity)

        payload: Dict[str, Any] = {
            "pair": normalized_pair,
            "side": side,
            "type": order_type,
            "quantity": rounded_quantity,
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("LIMIT order requires price")
            self.validate_limit_order(normalized_pair, price, quantity)
            payload["price"] = self.round_price(normalized_pair, price)

        return self._post("/v3/place_order", payload, signed=True)

    def query_order(
        self,
        order_id: Optional[int] = None,
        pair: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        pending_only: Optional[bool] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}

        if order_id is not None:
            if pair is not None or offset is not None or limit is not None or pending_only is not None:
                raise ValueError("when order_id is provided, no other optional parameter is allowed")
            payload["order_id"] = str(order_id)
        else:
            if pair is not None:
                payload["pair"] = self._normalize_pair(pair)
            if offset is not None:
                payload["offset"] = str(offset)
            if limit is not None:
                payload["limit"] = str(limit)
            if pending_only is not None:
                payload["pending_only"] = "TRUE" if pending_only else "FALSE"

        return self._post("/v3/query_order", payload, signed=True)

    def cancel_order(
        self,
        order_id: Optional[int] = None,
        pair: Optional[str] = None,
    ) -> Dict[str, Any]:
        if order_id is not None and pair is not None:
            raise ValueError("only one of order_id or pair is allowed")

        payload: Dict[str, Any] = {}
        if order_id is not None:
            payload["order_id"] = str(order_id)
        elif pair is not None:
            payload["pair"] = self._normalize_pair(pair)

        return self._post("/v3/cancel_order", payload, signed=True)