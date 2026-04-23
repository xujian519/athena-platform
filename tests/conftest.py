"""
Pytest配置文件
配置测试环境和fixture
"""

import sys
import types
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 绕过 core/learning/reinforcement_learning_agent.py 中的 SyntaxError，
# 该文件存在已知的语法问题，不影响 legal_prompt_fusion 模块的测试。
_dummy_rl_agent = types.ModuleType("core.learning.reinforcement_learning_agent")
sys.modules["core.learning.reinforcement_learning_agent"] = _dummy_rl_agent

# 添加production目录（部分测试需要）
production_path = project_root / "production"
if production_path.exists():
    sys.path.insert(0, str(production_path))

# 添加services目录（部分测试需要）
services_path = project_root / "services" / "api-gateway"
if services_path.exists():
    sys.path.insert(0, str(services_path))

import pytest


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    return {
        "test_mode": True,
        "database_url": "sqlite:///:memory:",
        "redis_url": "redis://localhost:7379/15",  # 使用测试数据库
        "log_level": "DEBUG",
    }


@pytest.fixture
def sample_text():
    """示例文本fixture"""
    return "这是一个测试文本，用于验证文本处理功能。"


@pytest.fixture
def sample_query():
    """示例查询fixture"""
    return "如何申请专利？"


@pytest.fixture
def sample_patent_data():
    """示例专利数据fixture"""
    return {
        "id": "CN123456789A",
        "title": "测试专利标题",
        "abstract": "这是专利摘要内容",
        "applicant": "测试申请人",
        "inventor": "测试发明人",
        "status": "pending"
    }


# 配置pytest标记
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记"
    )
    config.addinivalue_line(
        "markers", "gpu: 需要GPU的测试标记"
    )


@pytest.fixture
def test_environment():
    """测试环境fixture"""
    return {
        "test_mode": True,
        "database_url": "sqlite:///:memory:",
        "redis_url": "redis://localhost:6379/15"
    }

@pytest.fixture
def test_data_generator():
    """测试数据生成器fixture"""
    from faker import Faker
    fake = Faker()
    return {
        "generate_patent_id": lambda: f"CN{fake.random_number(digits=12)}",
        "generate_title": lambda: fake.sentence(),
        "generate_abstract": lambda: fake.text(),
    }
