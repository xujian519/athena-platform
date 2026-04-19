import sys
from pathlib import Path

from fastapi import FastAPI

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import importlib.util

# 修复导入路径 - api-gateway目录包含连字符，需要使用importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient

# 动态加载gateway_extended模块
gateway_path = Path(__file__).parent.parent / "services" / "api-gateway" / "gateway_extended.py"
spec = importlib.util.spec_from_file_location("gateway_extended", gateway_path)
gateway_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway_module)
gateway_ext = gateway_module.gateway_ext


def create_app() -> TestClient:
    app = FastAPI()
    app.include_router(gateway_ext)
    return TestClient(app)


def test_batch_register_and_list_and_health():
    client = create_app()
    resp = client.post(
        "/api/services/batch_register",
        json={
            "services": [
                {
                    "name": "user_service",
                    "host": "127.0.0.1",
                    "port": 8081,
                    "metadata": {"env": "dev"},
                },
                {"name": "product_service", "host": "127.0.0.1", "port": 8082},
            ]
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True
    assert isinstance(data.get("data"), list)
    assert len(data["data"]) == 2

    resp2 = client.get("/api/services/instances")
    assert resp2.status_code == 200
    assert isinstance(resp2.json().get("data"), list)

    resp3 = client.get("/api/health")
    assert resp3.status_code == 200
    assert resp3.json().get("success") is True


def test_dependencies_and_routes_basic():
    client = create_app()
    resp = client.post(
        "/api/dependencies", json={"service": "user_service", "depends_on": ["auth_service"]}
    )
    assert resp.status_code in (200, 201)

    resp2 = client.post(
        "/api/routes", json={"id": "r1", "path": "/users", "target_service": "user_service"}
    )
    assert resp2.status_code in (200, 201)
    assert resp2.json().get("data", {}).get("id") == "r1"
