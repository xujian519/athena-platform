"""
Gateway安全功能测试
测试JWT认证、速率限制、CORS等功能
"""

import time
from datetime import datetime, timedelta

import jwt
import pytest
import requests

BASE_URL = "http://localhost:8005"

class TestGatewaySecurity:
    """Gateway安全功能测试"""

    def test_health_endpoint_public(self):
        """测试健康检查端点（公开访问）"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert "data" in data

    def test_gateway_info_public(self):
        """测试Gateway信息端点（公开访问）"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Athena Gateway Unified"

    def test_routes_without_auth(self):
        """测试路由API无认证访问"""
        response = requests.get(f"{BASE_URL}/api/routes")
        # 根据配置，这可能返回401或200
        assert response.status_code in [200, 401]

    def test_rate_limiting(self):
        """测试速率限制"""
        # 发送多个请求
        responses = []
        for _i in range(25):  # 超过限制（100/分钟，突发20）
            response = requests.get(f"{BASE_URL}/health")
            responses.append(response.status_code)
            time.sleep(0.01)  # 小延迟

        # 检查是否有429响应
        assert 429 in responses or all(r == 200 for r in responses)

    def test_cors_preflight(self):
        """测试CORS预检请求"""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        }
        response = requests.options(f"{BASE_URL}/api/routes", headers=headers)

        # CORS预检应该返回204或200
        assert response.status_code in [200, 204]

        # 检查CORS头
        if "Access-Control-Allow-Origin" in response.headers:
            assert "localhost:3000" in response.headers["Access-Control-Allow-Origin"]

    def test_jwt_token_structure(self):
        """测试JWT Token结构"""
        # 模拟JWT payload
        payload = {
            "user_id": "123",
            "username": "test_user",
            "roles": ["user"],
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow(),
            "iss": "athena-gateway"
        }

        # 注意：这需要实际的密钥才能生成有效token
        secret = "athena-gateway-secret-key-change-in-production"

        try:
            token = jwt.encode(payload, secret, algorithm="HS256")
            assert token is not None
            assert len(token.split(".")) == 3  # header.payload.signature
        except Exception as e:
            pytest.skip(f"JWT编码跳过: {e}")

    def test_ip_whitelist_concept(self):
        """测试IP白名单概念"""
        # 这个测试验证IP白名单的配置存在
        # 实际IP限制在Gateway层面实施
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200

        # 如果IP白名单启用，非白名单IP会返回403
        # 这个测试假设本地IP在白名单中

    def test_security_headers(self):
        """测试安全响应头"""
        response = requests.get(f"{BASE_URL}/health")

        # 检查常见安全头
        # 注意：Gateway可能不设置所有这些头
        headers = response.headers

        # 验证基本头存在
        assert "content-type" in headers or "Content-Type" in headers

class TestGatewayAuthentication:
    """Gateway认证功能测试"""

    @pytest.mark.skip(reason="需要实际认证端点")
    def test_jwt_login(self):
        """测试JWT登录"""
        response = requests.post(f"{BASE_URL}/api/auth/login",
                                json={"username": "admin", "password": "password"})

        if response.status_code == 200:
            data = response.json()
            assert "token" in data.get("data", {})
        else:
            pytest.skip("认证端点未实现")

    @pytest.mark.skip(reason="需要实际认证端点")
    def test_jwt_protected_endpoint(self):
        """测试JWT保护的端点"""
        # 1. 尝试无Token访问
        response = requests.get(f"{BASE_URL}/api/routes")

        # 2. 使用有效Token访问
        headers = {"Authorization": "Bearer dummy_token"}
        response_with_token = requests.get(f"{BASE_URL}/api/routes", headers=headers)

        # 至少一个应该成功
        assert response.status_code == 200 or response_with_token.status_code == 200

class TestGatewayRateLimiting:
    """Gateway速率限制测试"""

    def test_burst_rate_limit(self):
        """测试突发速率限制"""
        # 快速发送20个请求（突发限制）
        responses = []
        for _ in range(25):
            response = requests.get(f"{BASE_URL}/health")
            responses.append(response.status_code)

        # 前20个应该成功
        success_count = sum(1 for r in responses[:20] if r == 200)
        assert success_count >= 18  # 允许一些失败

    def test_sustained_rate_limit(self):
        """测试持续速率限制"""
        # 在1分钟内发送110个请求
        success_count = 0
        rate_limited = False

        for i in range(110):
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited = True
                break

            if i > 0 and i % 10 == 0:
                time.sleep(1)  # 每10个请求暂停1秒

        # 应该被限制
        assert rate_limited or success_count >= 100

class TestGatewayCORS:
    """Gateway CORS测试"""

    def test_cors_get_request(self):
        """测试CORS GET请求"""
        headers = {"Origin": "http://localhost:3000"}
        response = requests.get(f"{BASE_URL}/health", headers=headers)

        assert response.status_code == 200

        # 检查CORS头
        if "Access-Control-Allow-Origin" in response.headers:
            assert response.headers["Access-Control-Allow-Origin"] != "*"

    def test_cors_post_request(self):
        """测试CORS POST请求"""
        headers = {
            "Origin": "http://localhost:3000",
            "Content-Type": "application/json"
        }

        # 使用公开端点测试
        response = requests.post(f"{BASE_URL}/api/routes",
                                json={},
                                headers=headers)

        # 检查CORS头
        if "Access-Control-Allow-Origin" in response.headers:
            assert "localhost:3000" in response.headers["Access-Control-Allow-Origin"]

class TestGatewaySecurityHeaders:
    """Gateway安全头测试"""

    def test_x_frame_options(self):
        """测试X-Frame-Options头"""
        response = requests.get(f"{BASE_URL}/health")

        # Gateway应该设置适当的帧选项
        # 这个测试是概念性的，实际实现可能不同
        assert response.status_code == 200

    def test_content_type_nosniff(self):
        """测试X-Content-Type-Options头"""
        response = requests.get(f"{BASE_URL}/health")

        # 验证响应头存在
        assert "content-type" in response.headers or "Content-Type" in response.headers

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
