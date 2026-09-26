"""Smoke tests for the fixed /health and /specs contract shapes."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_specs_seeded_with_five_elements(client):
    resp = client.get("/specs")
    assert resp.status_code == 200
    specs = resp.json()
    assert len(specs) == 5
    names = {s["element_name"] for s in specs}
    assert names == {
        "ejection_fraction",
        "stenosis_severity",
        "troponin_level",
        "primary_diagnosis_code",
        "discharge_disposition",
    }
    for s in specs:
        assert s["strategy"] in ("rule", "llm")
        assert isinstance(s["requires_llm"], bool)
        assert 0.0 <= s["threshold"] <= 1.0
