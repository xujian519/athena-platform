"""
智能体模块
提供各种AI智能体实现
"""

# 导入基础类和工具
from .base_agent import AgentResponse, AgentUtils, BaseAgent

# 导入具体的智能体实现
try:
    from .athena import AthenaAgent
except ImportError:
    AthenaAgent = None

# 导入其他智能体
try:
    from .xiaonuo_pisces_princess import XiaonuoPiscesPrincessAgent
except ImportError:
    XiaonuoPiscesPrincessAgent = None

try:
    from .xiaochen_sagittarius_enhanced import XiaochenSagittariusEnhancedAgent
except ImportError:
    XiaochenSagittariusEnhancedAgent = None

try:
    from .xiaona_professional_v4 import XiaonaProfessionalV4Agent
except ImportError:
    XiaonaProfessionalV4Agent = None

# 导出
__all__ = [
    "BaseAgent",
    "AgentUtils",
    "AgentResponse",
    "AthenaAgent",
    "XiaonuoPiscesPrincessAgent",
    "XiaochenSagittariusEnhancedAgent",
    "XiaonaProfessionalV4Agent",
]

# 版本信息
__version__ = "1.0.0"
