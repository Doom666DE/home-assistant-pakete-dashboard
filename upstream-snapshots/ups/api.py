"""Direct UPS tracking transport using libcurl's consistent TLS/HTTP profile.

Local compatibility patch for ha-ups 1.1.3. No browser process, browser cookies,
credentials, proxy, or disabled certificate verification are used. The existing
coordinator remains responsible for request budgets, caching and backoff.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from curl_cffi.requests import AsyncSession
from curl_cffi.requests.exceptions import RequestException

from .const import BOOTSTRAP_URL, COOKIE_XSRF, DEFAULT_LOCALE, HEADER_XSRF, TRACKING_API_URL

_LOGGER = logging.getLogger(__name__)
TRANSPORT_VERSION = "curl_cffi-0.16.3-v1"


class UPSApiError(Exception):
    """A tracking failure, compatible with the upstream coordinator."""

    def __init__(self, detail: str, *, status_code: int | None = None,
                 retry_after: float | None = None, timed_out: bool = False) -> None:
        super().__init__(f"UPS API request failed: {detail}")
        self.detail = detail
        self.status_code = status_code
        self.retry_after = retry_after
        self.timed_out = timed_out


def _check_response(response: Any) -> None:
    if response.status_code == 200:
        return
    try:
        retry_after = float(response.headers.get("Retry-After", ""))
    except (ValueError, TypeError):
        retry_after = None
    raise UPSApiError(f"HTTP {response.status_code}",
                      status_code=response.status_code, retry_after=retry_after)


def _parcel(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        raise UPSApiError("unexpected body (not a JSON object)")
    details = payload.get("trackDetails")
    if not isinstance(details, list) or not details or not isinstance(details[0], dict):
        raise UPSApiError("response carried no trackDetails")
    detail = details[0]
    if str(detail.get("errorCode")) == "504":
        return None
    if detail.get("errorCode"):
        raise UPSApiError(str(detail.get("errorText") or detail["errorCode"]))
    return detail


class UPSApiClient:
    """Keep the upstream constructor and request accounting interface."""

    def __init__(self, session: Any) -> None:
        # The upstream aiohttp session is still closed by its owner. Each lookup
        # owns and closes its libcurl session, including cancellation/error paths.
        self.requests_made = 0

    async def async_get_parcel(self, tracking_code: str, *, locale: str = DEFAULT_LOCALE) -> dict[str, Any] | None:
        language = locale.replace("_", "-")
        started = time.monotonic()
        try:
            async with AsyncSession(impersonate="chrome", max_clients=1, timeout=20) as session:
                response = await session.get(BOOTSTRAP_URL.format(locale=locale),
                    headers={"Accept-Language": f"{language},en;q=0.9"})
                _check_response(response)
                csrf = next((c.value for c in session.cookies.jar if c.name == COOKIE_XSRF), None)
                if not csrf:
                    raise UPSApiError("bootstrap returned no CSRF cookie; not sending tracking request", status_code=401)
                self.requests_made += 1
                response = await session.post(TRACKING_API_URL.format(locale=locale), json={
                    "Locale": locale, "TrackingNumber": [tracking_code],
                    "isBarcodeScanned": False, "Requester": "quic",
                    "ClientUrl": "https://www.ups.com/track", "returnToValue": "",
                    "AssociatedBcdnNumber": None,
                }, headers={HEADER_XSRF: csrf, "Accept": "application/json, text/plain, */*",
                    "Accept-Language": f"{language},en;q=0.9",
                    "Origin": "https://www.ups.com", "Referer": "https://www.ups.com/",
                    "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site"})
                _check_response(response)
                try:
                    payload = response.json()
                except ValueError as err:
                    raise UPSApiError("tracking response was not JSON") from err
                result = _parcel(payload)
                _LOGGER.debug("UPS direct libcurl lookup completed in %.2fs", time.monotonic() - started)
                return result
        except RequestException as err:
            # Avoid logging exception URLs or session details. Error 28 is
            # libcurl's timeout; the coordinator retains the cached parcel.
            code = getattr(err, "code", None)
            _LOGGER.debug("UPS libcurl request failed after %.2fs (code %s)", time.monotonic() - started, code)
            raise UPSApiError(f"libcurl transport error {code}", timed_out=code == 28) from err
