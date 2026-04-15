#!/usr/bin/env python3
"""
专利审查指南集成模块
为知识图谱API服务添加审查指南查询功能
"""

import json
from typing import Any

import requests
from fastapi import HTTPException

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class GuidelineIntegration:
    """专利审查指南集成类"""

    def __init__(self, qdrant_host="localhost", qdrant_port=6333):
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.collection_name = "patent_guideline"
        self.base_url = f"http://{qdrant_host}:{qdrant_port}"

        # 加载知识图谱数据
        self.graph_data = self._load_graph_data()

    def _load_graph_data(self) -> dict[str, Any]:
        """加载知识图谱数据"""
        try:
            with open("/Users/xujian/Athena工作平台/data/guideline_graph/patent_guideline_graph.json", encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载知识图谱数据失败: {e}")
            return {"nodes": [], "relationships": [], "metadata": {}}

    def search_guidelines(self, query: str, limit: int = 5, threshold: float = 0.7) -> list[dict]:
        """
        搜索相关的审查指南内容

        Args:
            query: 查询文本
            limit: 返回结果数量限制
            threshold: 相似度阈值

        Returns:
            匹配的审查指南内容列表
        """
        try:
            # 生成查询向量（简化版本，实际应使用BERT）
            query_vector = self._generate_query_vector(query)

            # 搜索Qdrant
            search_url = f"{self.base_url}/collections/{self.collection_name}/search"
            payload = {
                "vector": query_vector,
                "limit": limit,
                "score_threshold": threshold,
                "with_payload": True
            }

            response = requests.post(search_url, json=payload)
            response.raise_for_status()

            results = response.json().get("result", [])

            # 格式化结果
            formatted_results = []
            for result in results:
                payload = result.get("payload", {})
                formatted_result = {
                    "id": payload.get("original_id", ""),
                    "score": result.get("score", 0),
                    "node_type": payload.get("node_type", ""),
                    "title": payload.get("title", ""),
                    "level": payload.get("level", 1),
                    "keywords": payload.get("keywords", [])
                }
                formatted_results.append(formatted_result)

            return formatted_results

        except Exception as e:
            logger.error(f"搜索审查指南失败: {e}")
            raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}") from e

    def _generate_query_vector(self, text: str) -> list[float]:
        """
        生成查询向量（简化版本）
        实际应用中应使用BERT等预训练模型
        """
        import hashlib

        import numpy as np

        # 基于文本hash生成伪向量（仅用于演示）
        text_hash = hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()
        seed = int(text_hash[:8], 16) % (2**32)

        np.random.seed(seed)
        vector = np.random.normal(0, 1, 768)
        vector = vector / np.linalg.norm(vector)

        return vector.tolist()

    def get_related_rules(self, node_id: str) -> list[dict]:
        """
        获取相关的审查规则

        Args:
            node_id: 节点ID

        Returns:
            相关规则列表
        """
        rules = []

        # 查找该节点的规则
        for node in self.graph_data.get("nodes", []):
            if node["id"] == node_id and node.get("rules"):
                for rule in node["rules"]:
                    rules.append({
                        "content": rule,
                        "section_title": node.get("properties", {}).get("title", ""),
                        "section_id": node_id
                    })

        return rules

    def get_section_details(self, section_id: str) -> dict[str, Any]:
        """
        获取章节详细信息

        Args:
            section_id: 章节ID

        Returns:
            章节详细信息
        """
        for node in self.graph_data.get("nodes", []):
            if node["id"] == section_id:
                return {
                    "id": node["id"],
                    "type": node["type"],
                    "properties": node.get("properties", {}),
                    "rules": node.get("properties", {}).get("rules", []),
                    "examples": node.get("properties", {}).get("examples", [])
                }

        return {}

    def get_guideline_structure(self) -> dict[str, Any]:
        """
        获取审查指南结构

        Returns:
            审查指南的层次结构
        """
        structure = {
            "title": self.graph_data.get("metadata", {}).get("title", "专利审查指南"),
            "sections": []
        }

        # 构建层次结构
        sections = [n for n in self.graph_data.get("nodes", [])
                   if n.get("type") in ["Part", "Chapter", "Section"]]

        # 按level和ID排序
        sections.sort(key=lambda x: (x.get("properties", {}).get("level", 1), x["id"]))

        for section in sections:
            section_info = {
                "id": section["id"],
                "type": section.get("type"),
                "title": section.get("properties", {}).get("title", ""),
                "level": section.get("properties", {}).get("level", 1),
                "keywords": section.get("properties", {}).get("keywords", []),
                "rule_count": len(section.get("properties", {}).get("rules", [])),
                "example_count": len(section.get("properties", {}).get("examples", []))
            }
            structure["sections"].append(section_info)

        return structure

    def extract_rules_by_topic(self, topic: str, limit: int = 10) -> list[dict]:
        """
        根据主题提取相关规则

        Args:
            topic: 主题关键词
            limit: 返回规则数量限制

        Returns:
            相关规则列表
        """
        all_rules = []

        # 搜索相关内容
        search_results = self.search_guidelines(topic, limit=limit, threshold=0.6)

        # 收集规则
        for result in search_results:
            rules = self.get_related_rules(result["id"])
            all_rules.extend(rules)

        # 去重并限制数量
        seen = set()
        unique_rules = []
        for rule in all_rules:
            rule_key = (rule["content"], rule["section_title"])
            if rule_key not in seen:
                seen.add(rule_key)
                unique_rules.append(rule)
                if len(unique_rules) >= limit:
                    break

        return unique_rules

    def generate_dynamic_prompt(self, context: str, max_rules: int = 5) -> str:
        """
        基于上下文生成动态提示词

        Args:
            context: 上下文信息
            max_rules: 最大规则数量

        Returns:
            生成的提示词
        """
        # 搜索相关规则
        rules = self.extract_rules_by_topic(context, limit=max_rules)

        if not rules:
            return "未找到相关的审查指南规则。"

        # 构建提示词
        prompt_parts = [
            "基于专利审查指南，请注意以下相关规则：\n",
            "=" * 50
        ]

        for i, rule in enumerate(rules, 1):
            prompt_parts.append(f"\n{i}. 规则内容：{rule['content']}")
            prompt_parts.append(f"   来源章节：{rule['section_title']}")

        prompt_parts.extend([
            "\n" + "=" * 50,
            "\n请在审查过程中严格遵循上述规则。"
        ])

        return "\n".join(prompt_parts)

# 全局实例
guideline_integration = GuidelineIntegration()

# FastAPI路由示例
def add_guideline_routes(app) -> None:
    """添加审查指南相关路由"""

    @app.get("/api/v2/guidelines/search", summary="搜索审查指南")
    async def search_guidelines(
        query: str,
        limit: int = 5,
        threshold: float = 0.7
    ):
        """
        搜索相关的专利审查指南内容

        Args:
            query: 查询关键词
            limit: 返回结果数量
            threshold: 相似度阈值
        """
        results = guideline_integration.search_guidelines(query, limit, threshold)
        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results)
        }

    @app.get("/api/v2/guidelines/rules/{node_id}", summary="获取章节规则")
    async def get_section_rules(node_id: str):
        """获取指定章节的审查规则"""
        rules = guideline_integration.get_related_rules(node_id)
        return {
            "status": "success",
            "node_id": node_id,
            "rules": rules,
            "count": len(rules)
        }

    @app.get("/api/v2/guidelines/structure", summary="获取指南结构")
    async def get_guideline_structure():
        """获取专利审查指南的层次结构"""
        structure = guideline_integration.get_guideline_structure()
        return {
            "status": "success",
            "structure": structure
        }

    @app.post("/api/v2/guidelines/prompt", summary="生成动态提示词")
    async def generate_prompt(context: str, max_rules: int = 5):
        """
        基于上下文生成审查提示词

        Args:
            context: 审查上下文
            max_rules: 最大规则数量
        """
        prompt = guideline_integration.generate_dynamic_prompt(context, max_rules)
        return {
            "status": "success",
            "context": context,
            "prompt": prompt,
            "generated_rules": min(max_rules, len(prompt.split('\n')))
        }

    @app.get("/api/v2/guidelines/extract-rules", summary="提取主题规则")
    async def extract_rules_by_topic(topic: str, limit: int = 10):
        """
        根据主题提取相关审查规则

        Args:
            topic: 主题关键词
            limit: 返回规则数量
        """
        rules = guideline_integration.extract_rules_by_topic(topic, limit)
        return {
            "status": "success",
            "topic": topic,
            "rules": rules,
            "count": len(rules)
        }

# 使用示例
if __name__ == "__main__":
    # 创建集成实例
    integration = GuidelineIntegration()

    # 测试搜索
    results = integration.search_guidelines("发明专利申请")
    print("\n搜索结果:")
    for r in results:
        print(f"- {r['title']} (相似度: {r['score']:.3f})")

    # 测试提示词生成
    prompt = integration.generate_dynamic_prompt("申请文件格式审查")
    print("\n生成的提示词:")
    print(prompt)
