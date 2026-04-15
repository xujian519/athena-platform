"""
Athena平台 - 无效宣告规则知识库
集成自小诺工作的无效复审决定向量库项目
"""

import sys
from pathlib import Path

# 添加小诺工作的路径
xiaonuo_path = Path.home() / "小诺工作"
if str(xiaonuo_path) not in sys.path:
    sys.path.insert(0, str(xiaonuo_path))

# 导入检索器
from invalidation_rules import InvalidationRuleRetriever
from invalidation_rules.yunxi_integration import YunxiRuleHelper

__version__ = "1.0.0"
__all__ = ["InvalidationRuleRetriever", "YunxiRuleHelper"]
