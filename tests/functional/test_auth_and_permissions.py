import pytest


@pytest.mark.functional
def test_health_check(api_call):
    data = api_call("GET", "/health")
    assert data.get("status") == "ok"


@pytest.mark.functional
def test_register_login_profile_flow(api_call, make_headers, unique_suffix):
    username = f"pytest_user_{unique_suffix}"
    password = "pass1234"

    reg = api_call(
        "POST",
        "/auth/register",
        payload={
            "username": username,
            "password": password,
            "display_name": username,
            "department": "测试部",
        },
    )
    assert reg.get("success") is True
    assert reg.get("user_id") is not None
    assert reg.get("token")

    login = api_call(
        "POST", "/auth/login", payload={"username": username, "password": password}
    )
    assert login.get("success") is True
    assert login.get("token")

    headers = make_headers(login["user_id"], login["token"])
    profile = api_call("GET", "/auth/profile", headers=headers)
    assert profile.get("success") is True
    assert profile.get("user", {}).get("username") == username


@pytest.mark.functional
def test_regular_user_cannot_access_admin_members_api(api_call, make_headers, unique_suffix):
    username = f"pytest_perm_{unique_suffix}"

    reg = api_call(
        "POST",
        "/auth/register",
        payload={
            "username": username,
            "password": "pass1234",
            "display_name": username,
            "department": "测试部",
        },
    )
    headers = make_headers(reg["user_id"], reg["token"])

    deny = api_call(
        "GET",
        "/members",
        headers=headers,
        expected_status=(401, 403),
    )
    assert deny.get("success") is False
