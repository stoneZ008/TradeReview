def test_register_missing_fields(client):
    """测试注册缺少字段"""
    response = client.post('/api/auth/register', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_register_short_password(client):
    """测试注册密码过短"""
    response = client.post('/api/auth/register', json={
        'username': 'test',
        'email': 'test@example.com',
        'password': '123'
    })
    assert response.status_code == 400


def test_login_missing_fields(client):
    """测试登录缺少字段"""
    response = client.post('/api/auth/login', json={})
    assert response.status_code == 400
