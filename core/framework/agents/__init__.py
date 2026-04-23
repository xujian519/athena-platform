
"""
Athena智能体模块

提供统一的智能体接口和具体实现。

Version: 2.0.0
Author: Athena Team
"""

# ============ 新版统一接口 (v2.0.0) ============
from .base import (
    # 数据模型
    AgentCapability,
    AgentMetadata,
    # 注册中心
    AgentRegistry,
    AgentRequest,
    AgentResponse,
    # 枚举
    AgentStatus,
    # 基类
    BaseAgent,
    HealthStatus,
)
from .factory import (
    AgentAutoLoader,
    # 工厂
    AgentFactory,
    # 便捷函数
    create_agent_from_config,
    create_agents_from_yaml,
)

# ============ 新版智能体实现 ============
try:
    from .xiaonuo.xiaonuo_agent_v2 import XiaonuoAgentV2 as XiaonuoAgent
except ImportError:
    XiaonuoAgent = None

try:
    from .athena_advisor import AthenaAdvisorAgent
except ImportError:
    AthenaAdvisorAgent = None

# ============ 旧版接口 (向后兼容) ============
try:
    from .base_agent import AgentResponse as LegacyAgentResponse
    from .base_agent import AgentUtils
except ImportError:
    LegacyAgentResponse = None
    AgentUtils = None

try:
    from .athena import AthenaAgent
except ImportError:
    AthenaAgent = None

try:
    from .xiaonuo_pisces_princess import XiaonuoPiscesPrincessAgent
except ImportError:
    XiaonuoPiscesPrincessAgent = None

try:
    from .xiaochen_sagittarius_enhanced import XiaochenSagittariusEnhancedAgent
except ImportError:
    XiaochenSagittariusEnhancedAgent = None

# ============ 版本信息 ============
__version__ = "2.0.0"

# ============ 公共API ============

def get_agent(name: str, version: str = "v2"):
    """
    获取智能体实例

    Args:
        name: 智能体名称
        version: 版本 ("v1" 旧版, "v2" 新版)

    Returns:
        智能体实例
    """
    if version == "v2":
        return AgentRegistry.get(name)
    else:
        # 旧版兼容逻辑
        if name == "athena" and AthenaAgent:
            return AthenaAgent
        elif name == "xiaonuo" and XiaonuoPiscesPrincessAgent:
            return XiaonuoPiscesPrincessAgent
        elif name == "xiaochen" and XiaochenSagittariusEnhancedAgent:
            return XiaochenSagittariusEnhancedAgent
        return None


def list_agents(version: str = "v2") -> str:
    """
    列出可用智能体

    Args:
        version: 版本 ("v1" 旧版, "v2" 新版)

    Returns:
        智能体名称列表
    """
    if version == "v2":
        return AgentRegistry.list_agents()
    else:
        agents = []
        if AthenaAgent:
            agents.append("athena")
        if XiaonuoPiscesPrincessAgent:
            agents.append("xiaonuo")
        if XiaochenSagittariusEnhancedAgent:
            agents.append("xiaochen")

