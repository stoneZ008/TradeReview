def test_health_check(client):
    """测试健康检查接口"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
