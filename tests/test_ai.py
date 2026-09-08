def _start_session(client, headers):
    resp = client.post(
        "/api/session/start",
        json={"app_name": "Instagram", "device_model": "iQOO 13", "android_version": "15"},
        headers=headers,
    )
    return resp.json()["data"]["session_id"]


def _post_metric(client, headers, session_id, **overrides):
    payload = {
        "session_id": session_id,
        "fps": 58.5,
        "memory_usage": 40.0,
        "battery_usage": 2.0,
        "cpu_usage": 40.0,
        "temperature": 35.0,
        "frame_drops": 1,
    }
    payload.update(overrides)
    client.post("/api/metrics", json=payload, headers=headers)


def test_analyze_low_fps(client, auth_headers):
    headers = auth_headers("ai1@example.com")
    session_id = _start_session(client, headers)
    _post_metric(client, headers, session_id, fps=15)

    resp = client.post("/api/ai/analyze", json={"session_id": session_id}, headers=headers)
    assert resp.status_code == 200
    issue_types = [r["issue_type"] for r in resp.json()["data"]["reports"]]
    assert "PERFORMANCE" in issue_types


def test_analyze_high_cpu(client, auth_headers):
    headers = auth_headers("ai2@example.com")
    session_id = _start_session(client, headers)
    _post_metric(client, headers, session_id, cpu_usage=95)

    resp = client.post("/api/ai/analyze", json={"session_id": session_id}, headers=headers)
    issue_types = [r["issue_type"] for r in resp.json()["data"]["reports"]]
    assert "CPU" in issue_types


def test_analyze_high_memory(client, auth_headers):
    headers = auth_headers("ai3@example.com")
    session_id = _start_session(client, headers)
    _post_metric(client, headers, session_id, memory_usage=90)

    resp = client.post("/api/ai/analyze", json={"session_id": session_id}, headers=headers)
    issue_types = [r["issue_type"] for r in resp.json()["data"]["reports"]]
    assert "MEMORY" in issue_types


def test_analyze_no_issues(client, auth_headers):
    headers = auth_headers("ai4@example.com")
    session_id = _start_session(client, headers)
    _post_metric(client, headers, session_id)

    resp = client.post("/api/ai/analyze", json={"session_id": session_id}, headers=headers)
    issue_types = [r["issue_type"] for r in resp.json()["data"]["reports"]]
    assert issue_types == ["UNKNOWN"]


def test_get_reports_after_analyze(client, auth_headers):
    headers = auth_headers("ai5@example.com")
    session_id = _start_session(client, headers)
    _post_metric(client, headers, session_id, fps=10)
    client.post("/api/ai/analyze", json={"session_id": session_id}, headers=headers)

    resp = client.get(f"/api/ai/report/{session_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]["reports"]) >= 1
