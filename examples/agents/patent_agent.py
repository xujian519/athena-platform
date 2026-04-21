"""
Patent Agent - 专利分析Agent示例
================================

这是一个专利领域的Agent示例，展示如何创建垂直领域的专业Agent。
包含专利检索、分析和报告生成等功能。

功能：专利检索、分析、报告生成

作者: Athena平台团队
版本: 1.0.0

依赖:
- core.llm.unified_llm_manager (可选)
"""

from typing import Any, Dict, List, Optional
import logging
from datetime import datetime
import re

from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class PatentAgent(BaseXiaonaComponent):
    """
    专利分析Agent

    专利领域的专业Agent，提供：
    - 专利检索：根据关键词检索相关专利
    - 专利分析：分析专利内容和技术要点
    - 报告生成：生成专利分析报告

    Attributes:
        llm: LLM管理器（可选）
        patent_db: 模拟专利数据库

    Examples:
        >>> agent = PatentAgent(agent_id="patent_001")
        >>> result = await agent.execute(context)
    """

    __version__ = "1.0.0"
    __category__ = "patent"

    # 模拟专利数据库
    MOCK_PATENTS = [
        {
            "patent_id": "CN123456789A",
            "title": "一种基于人工智能的自动驾驶方法",
            "abstract": "本发明公开了一种基于人工智能的自动驾驶方法...",
            "applicant": "某科技公司",
            "date": "2024-01-15",
            "claims": 5,
        },
        {
            "patent_id": "CN987654321A",
            "title": "自动驾驶车辆的环境感知系统",
            "abstract": "本发明涉及自动驾驶技术领域...",
            "applicant": "某汽车公司",
            "date": "2024-02-20",
            "claims": 8,
        },
        {
            "patent_id": "CN112233445A",
            "title": "自动驾驶中的路径规划算法",
            "abstract": "本发明提供一种路径规划算法...",
            "applicant": "某研究院",
            "date": "2024-03-10",
            "claims": 6,
        },
    ]

    def _initialize(self) -> None:
        """初始化Agent"""
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="search",
                description="检索相关专利",
                input_types=["关键词", "技术领域"],
                output_types=["专利列表", "检索统计"],
                estimated_time=10.0,
            ),
            AgentCapability(
                name="analyze",
                description="分析专利内容",
                input_types=["专利号", "专利文档"],
                output_types=["分析报告", "技术要点"],
                estimated_time=15.0,
            ),
            AgentCapability(
                name="compare",
                description="对比多个专利",
                input_types=["专利列表"],
                output_types=["对比报告", "相似度分析"],
                estimated_time=20.0,
            ),
            AgentCapability(
                name="validate_patent_id",
                description="验证专利号格式",
                input_types=["专利号"],
                output_types=["验证结果"],
                estimated_time=1.0,
            ),
        ])

        # 初始化LLM（可选）
        try:
            from core.llm.unified_llm_manager import UnifiedLLMManager
            self.llm = UnifiedLLMManager()
            self.llm_available = True
        except ImportError:
            self.llm = None
            self.llm_available = False

        # 专利号格式正则
        self.patent_id_pattern = re.compile(
            r'^[A-Z]{2}\d{9}[A-Z]$|^\d{10}\.\d$'
        )

        # 统计
        self.search_count = 0
        self.analyze_count = 0

        logger.info(f"PatentAgent初始化完成: {self.agent_id}, LLM可用: {self.llm_available}")

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是PatentAgent，一个专业的专利分析助手。

核心能力：
- search: 根据关键词检索相关专利
- analyze: 分析专利内容和技术要点
- compare: 对比多个专利的异同
- validate_patent_id: 验证专利号格式

专业知识：
- 熟悉专利法及相关规定
- 了解专利检索技巧
- 掌握专利分析方法
- 能够识别技术创新点

工作原则：
- 准确理解技术内容
- 客观分析专利价值
- 保护客户机密信息
- 提供专业建议

输出格式：
结构化的专利分析报告
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行任务"""
        start_time = datetime.now()

        try:
            # 获取操作类型
            operation = context.input_data.get("operation", "search")

            if operation == "search":
                result = await self._search(context)
            elif operation == "analyze":
                result = await self._analyze(context)
            elif operation == "compare":
                result = await self._compare(context)
            elif operation == "validate_patent_id":
                result = self._validate_patent_id(context)
            else:
                raise ValueError(f"未知的操作类型: {operation}")

            execution_time = (datetime.now() - start_time).total_seconds()

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=result,
                execution_time=execution_time,
                metadata={
                    "operation": operation,
                },
            )

        except Exception as e:
            logger.exception(f"任务执行失败: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
            )

    async def _search(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """检索专利"""
        keywords = context.input_data.get("keywords", "")
        field = context.input_data.get("field", "")
        limit = context.input_data.get("limit", 10)

        if not keywords:
            raise ValueError("缺少关键词参数")

        self.search_count += 1

        # 模拟检索（实际应用中应连接真实专利数据库）
        results = []
        for patent in self.MOCK_PATENTS:
            # 简单匹配
            if keywords.lower() in patent["title"].lower() or keywords.lower() in patent["abstract"].lower():
                results.append({
                    "patent_id": patent["patent_id"],
                    "title": patent["title"],
                    "applicant": patent["applicant"],
                    "date": patent["date"],
                    "relevance": self._calculate_relevance(keywords, patent),
                })

        # 按相关性排序
        results.sort(key=lambda x: x["relevance"], reverse=True)

        # 限制结果数量
        results = results[:limit]

        return {
            "operation": "search",
            "keywords": keywords,
            "field": field,
            "results": results,
            "total": len(results),
            "search_count": self.search_count,
        }

    def _calculate_relevance(self, keywords: str, patent: Dict[str, Any]) -> float:
        """计算相关性分数"""
        score = 0.0
        keywords_lower = keywords.lower()

        # 标题匹配权重更高
        if keywords_lower in patent["title"].lower():
            score += 0.7

        # 摘要匹配
        if keywords_lower in patent["abstract"].lower():
            score += 0.3

        return score

    async def _analyze(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """分析专利"""
        patent_id = context.input_data.get("patent_id", "")
        patent_doc = context.input_data.get("patent_doc")

        if not patent_id and not patent_doc:
            raise ValueError("缺少patent_id或patent_doc参数")

        self.analyze_count += 1

        # 如果提供了专利号，查找专利
        if patent_id:
            patent = next((p for p in self.MOCK_PATENTS if p["patent_id"] == patent_id), None)
            if not patent:
                return {
                    "operation": "analyze",
                    "patent_id": patent_id,
                    "error": "专利不存在",
                }
        else:
            patent = patent_doc

        # 分析专利
        analysis = {
            "patent_id": patent["patent_id"],
            "title": patent["title"],
            "applicant": patent["applicant"],
            "filing_date": patent["date"],
            "claims_count": patent["claims"],
            "key_points": self._extract_key_points(patent),
            "technology_field": self._identify_field(patent),
            "innovation_level": self._assess_innovation(patent),
        }

        # 如果LLM可用，使用LLM增强分析
        if self.llm_available:
            enhanced_analysis = await self._enhance_with_llm(analysis)
            analysis["enhanced_insights"] = enhanced_analysis

        return {
            "operation": "analyze",
            "analysis": analysis,
            "analyze_count": self.analyze_count,
        }

    def _extract_key_points(self, patent: Dict[str, Any]) -> List[str]:
        """提取技术要点"""
        # 模拟提取（实际应用中应使用NLP）
        title = patent["title"]
        points = []

        if "人工智能" in title or "AI" in title:
            points.append("采用人工智能技术")
        if "自动驾驶" in title:
            points.append("应用于自动驾驶领域")
        if "算法" in title:
            points.append("涉及核心算法创新")

        if not points:
            points.append("详见专利说明书")

        return points

    def _identify_field(self, patent: Dict[str, Any]) -> str:
        """识别技术领域"""
        title = patent["title"].lower()

        if "自动驾驶" in title or "车辆" in title:
            return "交通运输 - 自动驾驶"
        elif "通信" in title or "网络" in title:
            return "通信技术"
        elif "医疗" in title or "药物" in title:
            return "医疗健康"
        else:
            return "通用技术"

    def _assess_innovation(self, patent: Dict[str, Any]) -> str:
        """评估创新水平"""
        claims = patent.get("claims", 0)

        if claims >= 8:
            return "高"
        elif claims >= 5:
            return "中"
        else:
            return "基础"

    async def _enhance_with_llm(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM增强分析"""
        try:
            prompt = f"""请分析以下专利，提供专业见解：

专利号：{analysis['patent_id']}
标题：{analysis['title']}
技术领域：{analysis['technology_field']}
创新水平：{analysis['innovation_level']}

请提供：
1. 技术价值评估
2. 市场前景分析
3. 可能的改进方向
"""

            response = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )

            return {
                "llm_analysis": response,
                "model_used": self.llm.model if hasattr(self.llm, 'model') else "unknown",
            }

        except Exception as e:
            logger.error(f"LLM分析失败: {e}")
            return {"error": str(e)}

    async def _compare(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """对比专利"""
        patent_ids = context.input_data.get("patent_ids", [])

        if not patent_ids:
            raise ValueError("缺少patent_ids参数")

        if len(patent_ids) < 2:
            raise ValueError("至少需要2个专利进行对比")

        # 获取专利
        patents = []
        for pid in patent_ids:
            patent = next((p for p in self.MOCK_PATENTS if p["patent_id"] == pid), None)
            if patent:
                patents.append(patent)

        if len(patents) < 2:
            return {
                "operation": "compare",
                "error": "有效专利数量不足",
            }

        # 对比分析
        comparison = {
            "patent_count": len(patents),
            "common_fields": self._find_common_fields(patents),
            "unique_features": self._find_unique_features(patents),
            "similarity_matrix": self._calculate_similarity(patents),
        }

        return {
            "operation": "compare",
            "comparison": comparison,
        }

    def _find_common_fields(self, patents: List[Dict[str, Any]]) -> List[str]:
        """查找共同技术领域"""
        fields = [self._identify_field(p) for p in patents]
        # 简化处理：返回第一个专利的领域
        return list(set(fields))

    def _find_unique_features(self, patents: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """查找各专利的独特之处"""
        return {
            p["patent_id"]: self._extract_key_points(p)
            for p in patents
        }

    def _calculate_similarity(self, patents: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算相似度矩阵"""
        # 简化处理：基于标题相似度
        result = {}
        for i, p1 in enumerate(patents):
            for j, p2 in enumerate(patents):
                if i < j:
                    key = f"{p1['patent_id']}_vs_{p2['patent_id']}"
                    # 简单相似度计算
                    similarity = len(set(p1['title']) & set(p2['title'])) / max(len(p1['title']), len(p2['title']))
                    result[key] = round(similarity, 2)
        return result

    def _validate_patent_id(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """验证专利号格式"""
        patent_id = context.input_data.get("patent_id", "")

        if not patent_id:
            raise ValueError("缺少patent_id参数")

        is_valid = bool(self.patent_id_pattern.match(patent_id))

        return {
            "operation": "validate_patent_id",
            "patent_id": patent_id,
            "is_valid": is_valid,
            "format": "CN格式 (如: CN123456789A)" if not is_valid else "符合格式要求",
        }

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            "search_count": self.search_count,
            "analyze_count": self.analyze_count,
        }


# 便捷函数
def create_patent_agent(agent_id: str = "patent_001") -> PatentAgent:
    """创建PatentAgent实例"""
    return PatentAgent(agent_id=agent_id)


# 测试入口
async def main():
    """测试入口"""
    import asyncio

    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 创建Agent
    agent = PatentAgent(agent_id="patent_test")

    print("=== Patent Agent测试 ===")

    # 测试检索
    print("\n=== 专利检索 ===")
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_SEARCH",
        input_data={
            "operation": "search",
            "keywords": "自动驾驶",
            "limit": 5,
        },
        config={},
        metadata={},
    )

    result = await agent.execute(context)
    print(f"检索到 {result.output_data['total']} 条相关专利")
    for patent in result.output_data['results']:
        print(f"  - {patent['patent_id']}: {patent['title']} (相关性: {patent['relevance']:.2f})")

    # 测试分析
    print("\n=== 专利分析 ===")
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_ANALYZE",
        input_data={
            "operation": "analyze",
            "patent_id": "CN123456789A",
        },
        config={},
        metadata={},
    )

    result = await agent.execute(context)
    analysis = result.output_data['analysis']
    print(f"专利号: {analysis['patent_id']}")
    print(f"标题: {analysis['title']}")
    print(f"技术领域: {analysis['technology_field']}")
    print(f"创新水平: {analysis['innovation_level']}")
    print(f"技术要点: {', '.join(analysis['key_points'])}")

    # 测试验证
    print("\n=== 专利号验证 ===")
    test_ids = ["CN123456789A", "INVALID_ID"]
    for tid in test_ids:
        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id=f"TASK_VALIDATE_{tid}",
            input_data={
                "operation": "validate_patent_id",
                "patent_id": tid,
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)
        status = "✓ 有效" if result.output_data['is_valid'] else "✗ 无效"
        print(f"  {tid}: {status}")

    # 统计
    print(f"\n=== 统计 ===")
    stats = agent.get_stats()
    print(f"检索次数: {stats['search_count']}")
    print(f"分析次数: {stats['analyze_count']}")


if __name__ == "__main__":
    asyncio.run(main())
