"""
llm - LLM集成模块

提供大语言模型集成,支持:
1. GLM-4.7 (智谱AI)
2. DeepSeek (深度求索)
3. 计划生成
4. 动态调整建议
5. 并行任务识别

主要组件:
- GLM47Client: GLM-4.7客户端

作者: Athena AI Platform
版本: v1.0.0
"""


from __future__ import annotations
__all__ = [
    # GLM-4.7
    "GLM47Client",
    "get_glm47_client",
]

__version__ = "1.0.0"
__author__ = "Athena AI Platform"
