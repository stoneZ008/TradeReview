import pytest
import sys
import os
import json
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update({
        'TESTING': True,
    })
    
    with app.test_client() as client:
        yield client


class TestHotspotRoutes:
    def test_get_sectors_concept(self, client):
        response = client.get('/api/hotspot/sectors?type=concept&limit=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
        assert 'total' in data

    def test_get_sectors_industry(self, client):
        response = client.get('/api/hotspot/sectors?type=industry&limit=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True

    def test_get_sectors_limit(self, client):
        response = client.get('/api/hotspot/sectors?limit=5')
        data = json.loads(response.data)
        assert len(data['data']) <= 5

    def test_get_sector_detail(self, client):
        response = client.get('/api/hotspot/sector/AI')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'stocks' in data
        assert 'attribution' in data

    def test_get_sector_detail_with_type(self, client):
        response = client.get('/api/hotspot/sector/半导体?type=industry')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True

    def test_get_hot_stocks(self, client):
        response = client.get('/api/hotspot/stocks?limit=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data

    def test_get_stock_attribution(self, client):
        response = client.get('/api/hotspot/attribution/000001?name=测试股票')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data

    def test_get_fund_flow(self, client):
        response = client.get('/api/hotspot/fund-flow')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data

    def test_get_market_overview(self, client):
        response = client.get('/api/hotspot/market-overview')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data

    def test_refresh_cache(self, client):
        response = client.post('/api/hotspot/refresh')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True

    def test_refresh_cache_with_type(self, client):
        response = client.post('/api/hotspot/refresh', json={'type': 'hot_sectors'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True


class TestHotspotResponseFormat:
    def test_sector_response_format(self, client):
        response = client.get('/api/hotspot/sectors?limit=5')
        data = json.loads(response.data)
        
        if len(data['data']) > 0:
            sector = data['data'][0]
            assert 'name' in sector
            assert 'change_pct' in sector
            assert 'rank' in sector
            assert 'is_mock' in sector

    def test_stock_response_format(self, client):
        response = client.get('/api/hotspot/stocks?limit=5')
        data = json.loads(response.data)
        
        if len(data['data']) > 0:
            stock = data['data'][0]
            assert 'code' in stock
            assert 'name' in stock
            assert 'change_pct' in stock
            assert 'price' in stock

    def test_fund_flow_response_format(self, client):
        response = client.get('/api/hotspot/fund-flow')
        data = json.loads(response.data)
        
        if len(data['data']) > 0:
            fund = data['data'][0]
            assert 'main_net_inflow' in fund
            assert 'super_large_net_inflow' in fund
            assert 'large_net_inflow' in fund
