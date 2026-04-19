# 测试指南

> Athena浏览器自动化服务 - 测试指南

本文档提供完整的测试说明，包括单元测试、集成测试和性能测试。

---

## 目录

- [测试结构](#测试结构)
- [运行测试](#运行测试)
- [编写测试](#编写测试)
- [测试覆盖率](#测试覆盖率)
- [CI/CD集成](#cicd集成)

---

## 测试结构

```
tests/
├── __init__.py
├── conftest.py              # pytest配置和fixtures
├── test_api.py              # API集成测试
├── test_browser.py          # 浏览器操作测试
├── test_exceptions.py       # 异常处理测试
├── test_concurrency.py      # 并发控制测试
├── test_security.py         # 安全功能测试
└── test_performance.py      # 性能测试
```

---

## 运行测试

### 安装测试依赖

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx
```

### 运行所有测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_api.py -v

# 运行特定测试函数
pytest tests/test_api.py::test_health_check -v

# 运行特定标记的测试
pytest tests/ -m unit          # 只运行单元测试
pytest tests/ -m integration   # 只运行集成测试
pytest tests/ -m performance   # 只运行性能测试
```

### 带覆盖率报告

```bash
# 生成HTML覆盖率报告
pytest tests/ --cov=core --cov=api --cov-report=html

# 查看报告
open htmlcov/index.html

# 终端输出覆盖率
pytest tests/ --cov=core --cov-report=term-missing
```

### 详细输出

```bash
# 显示打印输出
pytest tests/ -v -s

# 显示最慢的10个测试
pytest tests/ --durations=10

# 遇到第一个错误时停止
pytest tests/ -x

# 失败后继续运行
pytest tests/ --continue-on-collection-errors
```

---

## 编写测试

### pytest配置

**conftest.py：**
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from core.playwright_engine import PlaywrightEngine
from core.session_manager import SessionManager
from config.browser_config import BrowserConfig


@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def browser_engine():
    """创建浏览器引擎（用于测试）"""
    config = BrowserConfig(headless=True)
    engine = PlaywrightEngine(config)
    await engine.initialize()
    yield engine
    await engine.shutdown()


@pytest.fixture
def session_manager():
    """创建会话管理器"""
    return SessionManager()


@pytest.fixture
def mock_page():
    """模拟页面对象"""
    page = MagicMock()
    page.url = "https://www.example.com"
    page.title = "Example Page"
    page.viewport_size = {"width": 1920, "height": 1080}
    page.close = AsyncMock()
    return page


@pytest.fixture
def mock_context():
    """模拟浏览器上下文"""
    context = MagicMock()
    context.new_page = AsyncMock()
    return context
```

### 单元测试示例

```python
import pytest
from core.exceptions import SessionError, ErrorCode


class TestSessionManager:
    """测试会话管理器"""

    def test_create_session(self, session_manager, mock_page, mock_context):
        """测试创建会话"""
        session = asyncio.run(session_manager.create_session(
            mock_page,
            mock_context,
            "test_context"
        ))

        assert session is not None
        assert session.session_id is not None
        assert session.context_id == "test_context"

    def test_get_session(self, session_manager):
        """测试获取会话"""
        # 先创建会话
        session = asyncio.run(session_manager.create_session(
            MagicMock(),
            MagicMock(),
            "test_context"
        ))

        # 获取会话
        retrieved = asyncio.run(session_manager.get_session(session.session_id))
        assert retrieved.session_id == session.session_id

    def test_delete_session(self, session_manager, mock_page, mock_context):
        """测试删除会话"""
        session = asyncio.run(session_manager.create_session(
            mock_page,
            mock_context,
            "test_context"
        ))

        deleted = asyncio.run(session_manager.delete_session(session.session_id))
        assert deleted is True

        # 验证已删除
        retrieved = asyncio.run(session_manager.get_session(session.session_id))
        assert retrieved is None
```

### 集成测试示例

```python
import pytest
import httpx


class TestAPIEndpoints:
    """测试API端点"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8030/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_navigate_flow(self):
        """测试导航流程"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 导航到百度
            response = await client.post(
                "http://localhost:8030/api/v1/navigate",
                json={"url": "https://www.baidu.com"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "title" in data
```

### 异常测试示例

```python
import pytest
from core.exceptions import SessionLimitExceededError


class TestExceptionHandling:
    """测试异常处理"""

    def test_session_limit_exceeded(self, session_manager):
        """测试会话限制超限"""
        from unittest.mock import AsyncMock, MagicMock

        # 设置低限制
        from config import settings
        original_limit = settings.MAX_CONCURRENT_SESSIONS
        settings.MAX_CONCURRENT_SESSIONS = 1

        try:
            # 创建第一个会话
            asyncio.run(session_manager.create_session(
                MagicMock(),
                MagicMock(),
                "ctx1"
            ))

            # 尝试创建第二个会话应该失败
            with pytest.raises(SessionLimitExceededError):
                asyncio.run(session_manager.create_session(
                    MagicMock(),
                    MagicMock(),
                    "ctx2"
                ))
        finally:
            settings.MAX_CONCURRENT_SESSIONS = original_limit
```

### 性能测试示例

```python
import pytest
import time


class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_navigation_performance(self):
        """测试并发导航性能"""
        import httpx

        async def navigate_task(i):
            async with httpx.AsyncClient(timeout=30.0) as client:
                start = time.monotonic()
                response = await client.post(
                    "http://localhost:8030/api/v1/navigate",
                    json={"url": "https://www.baidu.com"}
                )
                duration = time.monotonic() - start
                return duration

        # 并发执行10次导航
        durations = await asyncio.gather(*[navigate_task(i) for i in range(10)])

        # 验证性能
        avg_duration = sum(durations) / len(durations)
        assert avg_duration < 5.0  # 平均应该 < 5秒
```

### 安全测试示例

```python
import pytest
from fastapi import HTTPException
from api.middleware.auth_middleware import verify_jwt_token
from unittest.mock import Mock


class TestSecurity:
    """安全测试"""

    @pytest.mark.asyncio
    async def test_jwt_validation(self):
        """测试JWT验证"""
        # 缺少认证应该返回401
        with pytest.raises(HTTPException) as exc_info:
            await verify_jwt_token(None)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_javascript_sandbox(self):
        """测试JavaScript沙箱"""
        from api.routes.browser_routes import validate_javascript_safety

        # 危险操作应该被拒绝
        is_safe, error = validate_javascript_safety("window.location.href = 'evil.com'")
        assert is_safe is False
        assert "window.location" in error
```

---

## 测试覆盖率

### 覆盖率目标

| 模块 | 目标覆盖率 | 当前覆盖率 |
|------|-----------|-----------|
| `core/playwright_engine.py` | 80% | 65% |
| `core/session_manager.py` | 85% | 75% |
| `core/browser_manager.py` | 80% | 70% |
| `core/task_executor.py` | 75% | 60% |
| `api/routes/` | 85% | 80% |
| `core/concurrency.py` | 85% | 85% |
| `core/exceptions.py` | 90% | 95% |

### 查看覆盖率报告

```bash
# 生成详细覆盖率报告
pytest tests/ --cov=core --cov=api --cov-report=term-missing --cov-report=html

# 在浏览器中查看
open htmlcov/index.html
```

### 提升覆盖率建议

1. **添加边界测试**
```python
# 测试边界值
@pytest.mark.parametrize("limit", [1, 10, 100, 1000])
async def test_session_limit(limit):
    settings.MAX_CONCURRENT_SESSIONS = limit
    # 测试...
```

2. **添加异常路径测试**
```python
# 测试所有异常分支
async def test_navigation_with_invalid_url():
    result = await navigate("invalid-url")
    assert result["success"] is False
    assert "error" in result
```

3. **添加并发场景测试**
```python
# 测试并发安全
async def test_concurrent_session_creation():
    tasks = [create_session() for _ in range(100)]
    await asyncio.gather(*tasks)
    # 验证结果...
```

---

## CI/CD集成

### GitHub Actions配置

**.github/workflows/test.yml：**
```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov

    - name: Install Playwright
      run: playwright install --with-deps chromium

    - name: Run tests
      run: |
        pytest tests/ \
          --cov=core \
          --cov=api \
          --cov-report=xml \
          --cov-report=html \
          --junitxml=test-results.xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
```

### 本地CI脚本

**scripts/run_ci.sh：**
```bash
#!/bin/bash
set -e

echo "🚀 开始CI测试..."

# 格式检查
echo "📝 代码格式检查..."
black . --check
ruff check .

# 类型检查
echo "🔍 类型检查..."
mypy core/ api/

# 运行测试
echo "🧪 运行测试..."
pytest tests/ -v --cov=core --cov=api --cov-report=html

# 检查覆盖率
echo "📊 检查覆盖率..."
COVERAGE=$(pytest tests/ --cov=core --quiet --cov-report=term)
echo "覆盖率: $COVERAGE"

echo "✅ CI测试完成！"
```

---

## 测试最佳实践

### 1. 使用fixtures重用代码

```python
@pytest.fixture
async def authenticated_client():
    """创建已认证的客户端"""
    client = BrowserAutomationClient()
    token = await client.get_token("user123", ["read"])
    client.set_token(token)
    yield client
    await client.close()
```

### 2. 使用标记组织测试

```python
@pytest.mark.unit
def test_parse_url():
    """单元测试：URL解析"""
    pass

@pytest.mark.integration
async def test_full_navigation():
    """集成测试：完整导航流程"""
    pass

@pytest.mark.slow
@pytest.mark.performance
async def test_load_test():
    """性能测试：负载测试"""
    pass
```

### 3. 使用parametrize减少重复

```python
@pytest.mark.parametrize("url,expected_title", [
    ("https://www.baidu.com", "百度"),
    ("https://www.bing.com", "Bing"),
])
async def test_navigation_titles(url, expected_title):
    """测试导航标题"""
    result = await navigate(url)
    assert expected_title in result["title"]
```

### 4. 异步测试最佳实践

```python
# ✅ 好的做法
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None

# ❌ 避免
def test_async_operation():
    result = asyncio.run(async_function())  # 不推荐
```

---

## 调试测试

### 使用pdb调试

```bash
# 在测试中设置断点
def test_with_breakpoint():
    import pdb; pdb.set_trace()
    assert True
```

### 使用pytest的pdb选项

```bash
# 在失败时进入pdb
pytest tests/ --pdb

# 在开始时就进入pdb
pytest tests/ --trace
```

### 查看详细输出

```bash
# 显示print输出
pytest tests/ -v -s

# 显示local变量
pytest tests/ -v --tb=long
```

---

## 相关文档

- [API使用示例](./API_USAGE.md)
- [故障排查指南](./TROUBLESHOOTING.md)
- [部署指南](./DEPLOYMENT.md)
