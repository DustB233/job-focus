from fastapi.testclient import TestClient


def test_list_sources_returns_registry_rows(client: TestClient) -> None:
    response = client.get("/api/sources")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 4
    assert any(
        source["source"] == "greenhouse" and source["externalIdentifier"] == "northstar"
        for source in payload
    )


def test_create_enable_disable_and_sync_source(client: TestClient) -> None:
    create_response = client.post(
        "/api/sources",
        json={
            "source": "lever",
            "externalIdentifier": "atlas",
            "displayName": "Lever / Atlas",
            "isActive": True,
        },
    )

    assert create_response.status_code == 201
    created_source = create_response.json()
    assert created_source["source"] == "lever"
    assert created_source["externalIdentifier"] == "atlas"
    assert created_source["isActive"] is True

    disable_response = client.post(f"/api/sources/{created_source['id']}/disable")
    assert disable_response.status_code == 200
    assert disable_response.json()["isActive"] is False

    enable_response = client.post(f"/api/sources/{created_source['id']}/enable")
    assert enable_response.status_code == 200
    assert enable_response.json()["isActive"] is True

    sync_response = client.post(f"/api/sources/{created_source['id']}/sync")
    assert sync_response.status_code == 200
    assert sync_response.json()["lastSyncRequestedAt"] is not None


def test_create_source_rejects_manual_only_provider(client: TestClient) -> None:
    response = client.post(
        "/api/sources",
        json={
            "source": "manual",
            "externalIdentifier": "linkedin",
            "displayName": "LinkedIn Manual Link",
            "isActive": True,
        },
    )

    assert response.status_code == 422
