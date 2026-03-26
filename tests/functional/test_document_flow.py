import pytest


@pytest.mark.functional
@pytest.mark.requires_admin
def test_document_sign_verify_trace_flow(api_call, make_headers, admin_session, unique_suffix):
    admin_h = admin_session["headers"]

    # register normal user
    username = f"pytest_doc_user_{unique_suffix}"
    user = api_call(
        "POST",
        "/auth/register",
        payload={
            "username": username,
            "password": "pass1234",
            "display_name": username,
            "department": "研发部",
        },
    )
    user_h = make_headers(user["user_id"], user["token"])

    # create group
    group = api_call(
        "POST",
        "/groups",
        headers=admin_h,
        payload={
            "name": f"pytest_group_{unique_suffix}",
            "description": "pytest functional group",
            "classification_level": "机密",
        },
    )
    assert group.get("success") is True
    group_id = group["group_id"]

    # add member
    member = api_call(
        "POST",
        "/members",
        headers=admin_h,
        payload={
            "group_id": group_id,
            "name": username,
            "user_id": user["user_id"],
        },
    )
    assert member.get("success") is True

    # create document
    doc = api_call(
        "POST",
        "/documents",
        headers=admin_h,
        payload={
            "title": f"pytest_doc_{unique_suffix}",
            "content": "pytest confidential content",
            "classification_level": "机密",
            "group_id": group_id,
        },
    )
    assert doc.get("success") is True
    doc_id = doc["document_id"]

    # sign
    sign = api_call("POST", f"/documents/{doc_id}/sign", headers=user_h, payload={})
    assert sign.get("success") is True

    # verify
    verify = api_call("POST", f"/documents/{doc_id}/verify", headers=admin_h, payload={})
    assert verify.get("success") is True

    # fetch signatures and trace
    detail = api_call("GET", f"/documents/{doc_id}", headers=admin_h)
    signatures = detail.get("document", {}).get("signatures", [])
    assert signatures, "document signatures should not be empty after sign"
    sig_id = signatures[0]["id"]

    trace = api_call(
        "POST",
        f"/documents/{doc_id}/signatures/{sig_id}/trace",
        headers=admin_h,
        payload={},
    )
    assert trace.get("success") is True
    assert trace.get("signer_name")
