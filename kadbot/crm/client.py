"""
HTTP‑клиент Aspro.Cloud с сессией и ретраями.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests  # type: ignore
from requests.adapters import HTTPAdapter  # type: ignore
from urllib3.util.retry import Retry  # type: ignore

logger = logging.getLogger(__name__)


class AsproClient:
    def __init__(self, api_key: str, company: str, timeout: int = 15, retries: int = 3) -> None:
        self.api_key = api_key
        self.company = company
        self.timeout = timeout
        self.base_url = f"https://{company}.aspro.cloud/api/v1"
        self.session = requests.Session()
        retry = Retry(
            total=retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _with_key(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        p = {"api_key": self.api_key}
        if params:
            p.update(params)
        return p

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, params=self._with_key(params), timeout=self.timeout)
        return resp

    def post(self, path: str, data: Dict[str, Any]) -> requests.Response:
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = self.session.post(url, params=self._with_key(), data=data, headers=headers, timeout=self.timeout)
        return resp

    # High‑level API wrappers
    def create_comment(self, module: str, entity: str, entity_id: int, text: str) -> Optional[Dict[str, Any]]:
        path = f"/module/{module}/{entity}/{entity_id}/comments/create"
        data = {"text": text}
        resp = self.post(path, data)
        if resp.ok:
            return resp.json()
        logger.error("Aspro create_comment failed: %s - %s", resp.status_code, resp.text)
        return None

    def list_calendars(self) -> Optional[Dict[str, Any]]:
        path = "/module/calendar/calendar/list"
        resp = self.get(path)
        if resp.ok:
            return resp.json()
        logger.error("Aspro list_calendars failed: %s - %s", resp.status_code, resp.text)
        return None

    def create_calendar(self, name: str, description: str, type_: int, color: str, timezone: str) -> Optional[Dict[str, Any]]:
        path = "/module/calendar/calendar/create"
        data = {
            "name": name,
            "description": description,
            "type": type_,
            "color": color,
            "timezone": timezone,
        }
        resp = self.post(path, data)
        if resp.ok:
            return resp.json()
        logger.error("Aspro create_calendar failed: %s - %s", resp.status_code, resp.text)
        return None

    def create_task_event(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        path = "/module/task/tasks/create"
        resp = self.post(path, data)
        if resp.ok:
            return resp.json()
        logger.error("Aspro create_task_event failed: %s - %s", resp.status_code, resp.text)
        return None
