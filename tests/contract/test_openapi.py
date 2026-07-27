from modoroco.interfaces.api import create_app


def test_openapi_documents_security_idempotency_and_sse() -> None:
    contract = create_app().openapi()
    assert contract["openapi"] == "3.1.0"
    schemes = contract["components"]["securitySchemes"]
    assert schemes["ModorocoApiKey"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
    }
    create_family = contract["paths"]["/v1/families"]["post"]
    assert create_family["security"] == [{"ModorocoApiKey": []}]
    assert any(
        parameter["name"] == "idempotency-key"
        and parameter["in"] == "header"
        and parameter["required"]
        for parameter in create_family["parameters"]
    )
    command = contract["paths"]["/v1/sessions/{session_id}/commands"]["post"]
    assert any(
        parameter["name"] == "idempotency-key" and parameter["required"]
        for parameter in command["parameters"]
    )
    stream = contract["paths"]["/v1/sessions/{session_id}/stream"]["get"]
    assert "200" in stream["responses"]
