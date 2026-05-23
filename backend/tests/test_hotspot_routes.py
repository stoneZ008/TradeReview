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
    app.config.update(
        {
            "TESTING": True,
        }
    )

    with app.test_client() as client:
        yield client


class TestHotspotRoutes:
    def test_get_sectors_default(self, client):
        response = client.get("/api/hotspot/sectors?limit=10")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "data" in data
        assert "total" in data

    def test_get_sectors_legacy_concept_param_ignored(self, client):
        response = client.get("/api/hotspot/sectors?type=concept&limit=10")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

    def test_get_sector_detail(self, client):
        response = client.get("/api/hotspot/sector/AI")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "stocks" in data
        assert "attribution" in data

    def test_get_sector_detail_with_type(self, client):
        response = client.get("/api/hotspot/sector/半导体?type=industry")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

    def test_get_stock_attribution(self, client):
        response = client.get("/api/hotspot/attribution/000001?name=测试股票")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "data" in data

    def test_get_market_overview(self, client):
        response = client.get("/api/hotspot/market-overview")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "data" in data
        d = data["data"]
        assert "market_status" in d
        assert "total_turnover" in d
        assert "total_turnover_text" in d
        assert "is_bull_market" in d
        assert "bull_market_score" in d
        assert "bull_market_reasons" in d
        assert "bull_market_summary" in d
        assert isinstance(d["bull_market_reasons"], list)

    def test_market_overview_fallback(self, client):
        with patch("hotspot_fetcher.get_market_metrics", side_effect=Exception("boom")):
            response = client.get("/api/hotspot/market-overview")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        d = data["data"]
        assert "total_turnover_text" in d
        assert "is_bull_market" in d
        assert "bull_market_reasons" in d

    def test_refresh_cache(self, client):
        response = client.post("/api/hotspot/refresh")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

    def test_refresh_cache_with_type(self, client):
        response = client.post("/api/hotspot/refresh", json={"type": "industry_sectors"})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

    def test_removed_hot_stocks_endpoint(self, client):
        response = client.get("/api/hotspot/stocks?limit=10")
        assert response.status_code == 404

    def test_removed_fund_flow_endpoint(self, client):
        response = client.get("/api/hotspot/fund-flow")
        assert response.status_code == 404


class TestHotspotResponseFormat:
    def test_sector_response_format(self, client):
        response = client.get("/api/hotspot/sectors?limit=5")
        data = json.loads(response.data)

        if len(data["data"]) > 0:
            sector = data["data"][0]
            assert "name" in sector
            assert "change_pct" in sector
            assert "rank" in sector
            assert "is_mock" in sector
