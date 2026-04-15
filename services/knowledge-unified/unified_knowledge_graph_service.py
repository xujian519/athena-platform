#!/usr/bin/env python3
"""
统一知识图谱服务
Unified Knowledge Graph Service

整合三个知识图谱作为专利业务的动态提示词和规则来源
1. patent_knowledge_graph.db (SQLite大规模专利知识图谱)
2. patent_legal_kg_simple (专利法律法规知识图谱)
3. patent_guideline (审查指南知识图谱)

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import asyncio
import json
import logging

logger = logging.getLogger(__name__)
import sqlite3
from pathlib import Path
from typing import Any

import networkx as nx

from core.logging_config import setup_logging

try:
    from qdrant_client import QdrantClient
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False
    logger.warning("Qdrant client not installed")
import jieba
import jieba.analyse

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

class UnifiedKnowledgeService:
    """统一知识图谱服务"""

    def __init__(self):
        """初始化"""
        # 知识图谱路径
        self.sqlite_kg_path = "/Users/xujian/Athena工作平台/data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db"
        self.legal_kg_path = "/Users/xujian/Athena工作平台/data/patent_legal_kg_simple"
        self.guideline_collection = "patent_guideline"

        # 连接初始化
        self.sqlite_conn = None
        self.legal_graph = None
        self.qdrant_client = None

        # 缓存
        self.novelty_rules_cache = {}
        self.creativity_rules_cache = {}
        self.procedure_rules_cache = {}

        # 初始化jieba
        jieba.initialize()
        logger.info("统一知识图谱服务初始化完成")

    def connect_all_sources(self) -> Any:
        """连接所有知识源"""
        logger.info("连接所有知识源...")

        # 1. 连接SQLite知识图谱
        self.sqlite_conn = sqlite3.connect(self.sqlite_kg_path)
        logger.info("✅ SQLite知识图谱已连接")

        # 2. 加载法律知识图谱
        self._load_legal_kg()
        logger.info("✅ 法律知识图谱已加载")

        # 3. 连接Qdrant (审查指南)
        self.qdrant_client = QdrantClient(host="localhost", port=6333)
        logger.info("✅ Qdrant已连接")

        return True

    def _load_legal_kg(self) -> Any:
        """加载法律知识图谱"""
        graph_path = Path(self.legal_kg_path) / "knowledge_graph.graphml"
        if graph_path.exists():
            self.legal_graph = nx.read_graphml(str(graph_path))
        else:
            # 从JSON重建
            self.legal_graph = nx.DiGraph()
            entities_path = Path(self.legal_kg_path) / "entities.json"
            relations_path = Path(self.legal_kg_path) / "relationships.json"

            with open(entities_path, encoding='utf-8') as f:
                entities = json.load(f)
            with open(relations_path, encoding='utf-8') as f:
                relations = json.load(f)

            for entity in entities.values():
                self.legal_graph.add_node(
                    entity['id'],
                    name=entity.get('name', ''),
                    type=entity.get('type', ''),
                    description=entity.get('description', '')
                )

            for rel in relations:
                self.legal_graph.add_edge(
                    rel['source'],
                    rel['target'],
                    type=rel.get('type', ''),
                    description=rel.get('description', '')
                )

    async def generate_dynamic_prompts(self, patent_text: str, context: str = "") -> dict[str, Any]:
        """生成动态提示词"""
        logger.info("为专利文本生成动态提示词...")

        # 1. 分析专利文本关键词
        keywords = self._extract_keywords(patent_text)

        # 2. 根据关键词提取相关规则
        novelty_rules = await self._extract_novelty_rules(keywords)
        creativity_rules = await self._extract_creativity_rules(keywords)
        procedure_rules = await self._extract_procedure_rules(keywords)

        # 3. 从审查指南搜索相关内容
        guideline_content = await self._search_guidelines(patent_text, keywords)

        # 4. 构建动态提示词
        dynamic_prompts = {
            "patent_analysis": self._build_analysis_prompt(patent_text, keywords),
            "novelty_assessment": self._build_novelty_prompt(novelty_rules),
            "creativity_assessment": self._build_creativity_prompt(creativity_rules),
            "procedure_guidance": self._build_procedure_prompt(procedure_rules),
            "guideline_references": self._build_guideline_prompt(guideline_content),
            "decision_support": self._build_decision_support_prompt(keywords, context)
        }

        return dynamic_prompts

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 使用jieba提取关键词
        keywords = jieba.analyse.extract_tags(text, top_k=20, with_weight=True)

        # 添加专利领域特定关键词
        patent_terms = [
            "新颖性", "创造性", "实用性", "现有技术", "抵触申请",
            "权利要求", "说明书", "技术方案", "技术效果",
            "实施例", "优先权", "申请日", "公开日"
        ]

        all_keywords = [kw[0] for kw in keywords]
        for term in patent_terms:
            if term in text and term not in all_keywords:
                all_keywords.append(term)

        return all_keywords[:20]  # 限制关键词数量

    async def _extract_novelty_rules(self, keywords: list[str]) -> list[dict]:
        """提取新颖性规则"""
        rules = []

        # 1. 从SQLite知识图谱提取
        sql_rules = self._extract_sqlite_novelty_rules(keywords)
        rules.extend(sql_rules)

        # 2. 从法律知识图谱提取
        legal_rules = self._extract_legal_novelty_rules(keywords)
        rules.extend(legal_rules)

        return self._deduplicate_rules(rules)

    def _extract_sqlite_novelty_rules(self, keywords: list[str]) -> list[dict]:
        """从SQLite提取新颖性规则"""
        rules = []

        # 构建查询条件
        conditions = []
        for keyword in keywords:
            conditions.append(f"(name LIKE '%{keyword}%' OR value LIKE '%{keyword}%')")

        # 包含新颖性相关的关键词
        novelty_keywords = ["新颖性", "现有技术", "A22", "申请日", "优先权", "抵触申请"]
        for keyword in novelty_keywords:
            conditions.append(f"(name LIKE '%{keyword}%' OR value LIKE '%{keyword}%')")

        if not conditions:
            return rules

        query = f"""
        SELECT DISTINCT name, value, entity_type, properties
        FROM patent_entities
        WHERE ({' OR '.join(conditions[:20])})  -- 限制条件数量
        AND entity_type = '法律条款'
        LIMIT 100
        """

        cursor = self.sqlite_conn.cursor()
        cursor.execute(query)

        for row in cursor.fetchall():
            rules.append({
                'source': 'SQLite知识图谱',
                'type': '法律条款',
                'title': row[0] or '',
                'content': row[1] or '',
                'category': '新颖性',
                'properties': json.loads(row[3]) if row[3] else {}
            })

        return rules

    def _extract_legal_novelty_rules(self, keywords: list[str]) -> list[dict]:
        """从法律知识图谱提取新颖性规则"""
        rules = []

        # 查找相关节点
        related_nodes = []
        for node_id, data in self.legal_graph.nodes(data=True):
            node_text = f"{data.get('name', '')} {data.get('description', '')}"
            if any(keyword in node_text for keyword in keywords + ['新颖性', '现有技术']):
                related_nodes.append((node_id, data))

        # 提取规则
        for node_id, data in related_nodes:
            rules.append({
                'source': '法律法规知识图谱',
                'type': data.get('type', ''),
                'title': data.get('name', ''),
                'content': data.get('description', ''),
                'category': '新颖性',
                'node_id': node_id
            })

        return rules

    async def _extract_creativity_rules(self, keywords: list[str]) -> list[dict]:
        """提取创造性规则"""
        rules = []

        creativity_keywords = ["创造性", "进步性", "显而易见", "技术启示", "A23"]

        # 从SQLite提取
        conditions = []
        for keyword in keywords + creativity_keywords:
            conditions.append(f"(name LIKE '%{keyword}%' OR value LIKE '%{keyword}%')")

        if conditions:
            query = f"""
            SELECT DISTINCT name, value, entity_type
            FROM patent_entities
            WHERE ({' OR '.join(conditions[:15])})
            LIMIT 50
            """

            cursor = self.sqlite_conn.cursor()
            cursor.execute(query)

            for row in cursor.fetchall():
                rules.append({
                    'source': 'SQLite知识图谱',
                    'type': row[2] or '',
                    'title': row[0] or '',
                    'content': row[1] or '',
                    'category': '创造性'
                })

        return rules

    async def _extract_procedure_rules(self, keywords: list[str]) -> list[dict]:
        """提取程序规则"""
        rules = []

        procedure_keywords = ["审查", "流程", "程序", "申请", "答复", "修改"]

        # 从法律知识图谱提取
        for _node_id, data in self.legal_graph.nodes(data=True):
            if data.get('type') == 'procedure' or any(kw in data.get('name', '') for kw in procedure_keywords):
                rules.append({
                    'source': '法律法规知识图谱',
                    'type': '程序规定',
                    'title': data.get('name', ''),
                    'content': data.get('description', ''),
                    'category': '程序规则'
                })

        return rules

    async def _search_guidelines(self, patent_text: str, keywords: list[str]) -> list[dict]:
        """搜索审查指南"""
        try:
            # 使用Qdrant搜索审查指南
            search_results = []

            # 构建查询向量（这里简化处理，实际应该使用embedding）
            query_text = " ".join(keywords[:10])

            # 搜索相似文档
            hits = self.qdrant_client.search(
                collection_name=self.guideline_collection,
                query_vector=self._text_to_vector(query_text),  # 需要实现向量转换
                limit=5
            )

            for hit in hits:
                search_results.append({
                    'score': hit.score,
                    'content': hit.payload.get('content', '')[:500],
                    'source': '审查指南'
                })

            return search_results
        except Exception as e:
            logger.error(f"搜索审查指南失败: {e}")
            return []

    def _text_to_vector(self, text: str) -> list[float]:
        """文本转向量（简化版）"""
        # 这里应该使用实际的embedding模型
        # 简化起见，返回固定长度的随机向量
        import hashlib
        hash_obj = hashlib.md5(text.encode('utf-8'), usedforsecurity=False)
        vector = []
        for i in range(768):  # 假设768维
            byte_idx = i % 16
            vector.append(ord(hash_obj.digest()[byte_idx]) / 255.0)
        return vector

    def _deduplicate_rules(self, rules: list[dict]) -> list[dict]:
        """去重规则"""
        seen = set()
        unique_rules = []

        for rule in rules:
            key = (rule['source'], rule['category'], rule['title'])
            if key not in seen:
                seen.add(key)
                unique_rules.append(rule)

        return unique_rules

    def _build_analysis_prompt(self, patent_text: str, keywords: list[str]) -> str:
        """构建分析提示词"""
        prompt = f"""
## 专利分析提示词

### 关键词识别
{', '.join(keywords[:10])}

### 分析要点
1. 技术领域识别
2. 技术问题分析
3. 技术方案理解
4. 技术效果评估

### 分析方向
- 确定专利类型（发明/实用新型/外观设计）
- 识别核心创新点
- 分析技术实现方式
- 评估产业化前景

### 待查证要点
请基于以下知识库进一步分析：
- 新颖性判断标准
- 创造性评估要点
- 实用性要求
- 申请程序要求
"""
        return prompt

    def _build_novelty_prompt(self, novelty_rules: list[dict]) -> str:
        """构建新颖性评估提示词"""
        prompt = """
## 新颖性评估提示词

### 核心原则
1. 现有技术判断标准（专利法第22条）
2. 申请日/优先权日的时间界限
3. 公开方式认定
4. 抵触申请的处理

### 相关规则
"""

        for rule in novelty_rules[:5]:  # 限制规则数量
            prompt += f"\n**{rule['title']}**\n"
            prompt += f"{rule['content'][:200]}...\n"
            prompt += f"来源: {rule['source']}\n\n"

        return prompt

    def _build_creativity_prompt(self, creativity_rules: list[dict]) -> str:
        """构建创造性评估提示词"""
        prompt = """
## 创造性评估提示词

### 判断标准（专利法第22条）
1. 突出实质性特点
2. 显著进步
3. 技术启示原则

### 评估要点
"""

        for rule in creativity_rules[:3]:
            prompt += f"\n- {rule['title']}: {rule['content'][:100]}...\n"

        return prompt

    def _build_procedure_prompt(self, procedure_rules: list[dict]) -> str:
        """构建程序指导提示词"""
        prompt = """
## 专利申请程序指导

### 申请流程
1. 申请准备
2. 文件提交
3. 审查答复
4. 授权流程

### 注意事项
"""

        for rule in procedure_rules:
            prompt += f"\n- {rule['title']}\n"

        return prompt

    def _build_guideline_prompt(self, guideline_content: list[dict]) -> str:
        """构建审查指南提示词"""
        prompt = "## 审查指南参考\n\n"

        for content in guideline_content:
            prompt += f"### 相关审查指南（相似度: {content['score']:.3f}）\n"
            prompt += f"{content['content']}\n\n"

        return prompt

    def _build_decision_support_prompt(self, keywords: list[str], context: str) -> str:
        """构建决策支持提示词"""
        prompt = f"""
## 智能决策支持

### 当前专利关键词
{', '.join(keywords)}

### 应用场景
{context}

### 建议行动
1. 根据关键词匹配相关法条
2. 参考相似案例的处理方式
3. 遵循标准审查程序
4. 注意特殊情况处理

### 风险提示
- 注意时间节点要求
- 关注程序性规定
- 重视证据链完整
"""
        return prompt

    async def get_comprehensive_rules(self, query: str) -> dict[str, list[dict]]:
        """获取综合规则"""
        keywords = self._extract_keywords(query)

        return {
            'novelty': await self._extract_novelty_rules(keywords),
            'creativity': await self._extract_creativity_rules(keywords),
            'procedure': await self._extract_procedure_rules(keywords)
        }

    def close(self) -> Any:
        """关闭连接"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        logger.info("统一知识图谱服务已关闭")

# 全局实例
_unified_service = None

async def get_unified_knowledge_service():
    """获取统一知识图谱服务实例"""
    global _unified_service
    if _unified_service is None:
        _unified_service = UnifiedKnowledgeService()
        _unified_service.connect_all_sources()
    return _unified_service

# 测试代码
async def test_unified_service():
    """测试统一知识图谱服务"""
    service = UnifiedKnowledgeService()
    service.connect_all_sources()

    test_patent = """
    本发明涉及一种基于深度学习的图像识别方法，
    包括以下步骤：收集训练图像数据；构建深度神经网络模型；
    使用训练数据对模型进行训练；通过训练后的模型识别图像。
    本发明能够提高图像识别的准确率。
    """

    # 生成动态提示词
    prompts = await service.generate_dynamic_prompts(test_patent)

    print("=== 动态提示词生成结果 ===")
    print(f"分析提示词长度: {len(prompts['patent_analysis'])}")
    print(f"新颖性规则数: {len(prompts['novelty_assessment'])}")
    print(f"创造性规则数: {len(prompts['creativity_assessment'])}")

    service.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_unified_service())
