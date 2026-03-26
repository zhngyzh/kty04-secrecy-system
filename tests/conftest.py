import os
import time
import uuid
from typing import Any, Dict, Optional, Tuple

import pytest
import requests


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--base-url",
        action="store",
        default="http://localhost:5000",
        help="Base URL of running backend service.",
    )
    parser.addoption(
        "--run-performance",
        action="store_true",
        default=False,
        help="Run performance test suite.",
    )
    parser.addoption(
        "--admin-username",
        action="store",
        default=os.getenv("E2E_ADMIN_USERNAME"),
        help="Admin username used for privileged flows.",
    )
    parser.addoption(
        "--admin-password",
        action="store",
        default=os.getenv("E2E_ADMIN_PASSWORD"),
        help="Admin password used for privileged flows.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "functional: functional API tests")
    config.addinivalue_line("markers", "performance: performance-oriented API tests")
    config.addinivalue_line("markers", "requires_admin: requires admin credentials")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-performance"):
        return
    skip_perf = pytest.mark.skip(reason="need --run-performance option to run")
    for item in items:
        if "performance" in item.keywords:
            item.add_marker(skip_perf)


@pytest.fixture(scope="session")
def base_url(pytestconfig: pytest.Config) -> str:
    return str(pytestconfig.getoption("--base-url")).rstrip("/")


@pytest.fixture(scope="session")
def api_base(base_url: str) -> str:
    return f"{base_url}/api"


@pytest.fixture(scope="session")
def timeout_s() -> int:
    return 12


@pytest.fixture(scope="session", autouse=True)
def ensure_server_available(base_url: str, timeout_s: int) -> None:
    try:
        resp = requests.get(f"{base_url}/api/health", timeout=timeout_s)
        resp.raise_for_status()
    except Exception as exc:
        pytest.exit(f"backend service is unavailable at {base_url}: {exc}", returncode=2)


@pytest.fixture
def unique_suffix() -> str:
    return f"{int(time.time())}_{uuid.uuid4().hex[:6]}"


def _request_json(
    method: str,
    url: str,
    *,
    expected_status: Tuple[int, ...],
    timeout_s: int,
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    resp = requests.request(
        method=method,
        url=url,
        headers=headers,
        json=json_body,
        timeout=timeout_s,
    )
    if resp.status_code not in expected_status:
        raise AssertionError(
            f"{method} {url} -> {resp.status_code}, expected={expected_status}, body={resp.text[:400]}"
        )
    try:
        return resp.json()
    except Exception as exc:
        raise AssertionError(f"{method} {url} returned non-JSON body: {exc}") from exc


@pytest.fixture
def api_call(api_base: str, timeout_s: int):
    def _call(
        method: str,
        path: str,
        *,
        expected_status: Tuple[int, ...] = (200,),
        headers: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return _request_json(
            method=method,
            url=f"{api_base}{path}",
            expected_status=expected_status,
            timeout_s=timeout_s,
            headers=headers,
            json_body=payload,
        )

    return _call


@pytest.fixture
def make_headers():
    def _headers(user_id: int, token: str) -> Dict[str, str]:
        return {
            "X-User-ID": str(user_id),
            "X-Token": token,
            "Content-Type": "application/json",
        }

    return _headers


@pytest.fixture
def admin_session(api_call, make_headers, unique_suffix, pytestconfig: pytest.Config):
    """
    Acquire an admin session.
    Priority:
    1) login with --admin-username/--admin-password
    2) register a fresh account and use it only if it becomes admin (empty DB case)
    """
    username = pytestconfig.getoption("--admin-username")
    password = pytestconfig.getoption("--admin-password")

    if username and password:
        login = api_call(
            "POST",
            "/auth/login",
            payload={"username": username, "password": password},
        )
        if login.get("success") and login.get("role") == "admin":
            return {
                "user_id": login["user_id"],
                "token": login["token"],
                "headers": make_headers(login["user_id"], login["token"]),
                "username": login.get("username", username),
            }
        pytest.skip("provided admin credentials are invalid or not admin role")

    reg = api_call(
        "POST",
        "/auth/register",
        payload={
            "username": f"pytest_admin_{unique_suffix}",
            "password": "pass1234",
            "display_name": f"pytest_admin_{unique_suffix}",
            "department": "测试部",
        },
    )

    if reg.get("success") and reg.get("role") == "admin":
        return {
            "user_id": reg["user_id"],
            "token": reg["token"],
            "headers": make_headers(reg["user_id"], reg["token"]),
            "username": reg.get("username"),
        }

    pytest.skip(
        "admin session unavailable: use empty DB or provide --admin-username/--admin-password"
    )
