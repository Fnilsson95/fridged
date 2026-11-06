"""
Passing test shows that the whole setup works, the app imports, the fixtures, etc
"""

def test_health(client):
    # Proves the app starts and the test setup works end to end.
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
