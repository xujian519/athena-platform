"""
小娜·分析者

负责技术特征比对、新颖性分析、侵权分析等任务。
"""

import logging
from typing import Any, Optional

from core.ai.llm.unified_llm_manager import UnifiedLLMManager
from core.framework.agents.xiaona.base_component import (
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
    BaseXiaonaComponent,
)

logger = logging.getLogger(__name__)


class AnalyzerAgent(BaseXiaonaComponent):
    """
    小娜·分析者

    专注于专利分析任务，包括：
    - 技术特征提取和比对
    - 新颖性分析
    - 创造性分析
    - 侵权风险分析
    - 技术方案对比
    """

    def _initialize(self) -> str:
        """初始化分析者智能体"""
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="feature_extraction",
                description="技术特征提取",
                input_types=["专利文本", "技术交底书"],
                output_types=["技术特征列表"],
                estimated_time=10.0,
            ),
            AgentCapability(
                name="novelty_analysis",
                description="新颖性分析",
                input_types=["目标专利", "对比文件"],
                output_types=["新颖性分析报告"],
                estimated_time=20.0,
            ),
            AgentCapability(
                name="creativity_analysis",
                description="创造性分析",
                input_types=["目标专利", "对比文件"],
                output_types=["创造性分析报告"],
                estimated_time=25.0,
            ),
            AgentCapability(
                name="infringement_analysis",
                description="侵权分析",
                input_types=["目标专利", "被控产品"],
                output_types=["侵权分析报告"],
                estimated_time=30.0,
            ),
        ])

        # 初始化LLM
        self.llm_manager = UnifiedLLMManager()

        self.logger.info(f"分析者智能体初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是小娜·分析者，专利分析领域的专家。

你的核心能力：
1. 技术特征提取：从专利文本中提取技术特征
2. 新颖性分析：判断技术方案是否具备新颖性
3. 创造性分析：评估技术方案的创造性高度
4. 侵权分析：分析产品是否侵犯专利权

分析原则：
- 客观性：基于事实和技术进行分析
- 全面性：考虑所有相关技术特征
- 逻辑性：清晰展示分析思路和结论
- 法律性：结合专利法相关规定

输出格式：
- 技术特征列表（层次化结构）
- 对比分析表（特征 vs 对比文件）
- 分析结论（新颖性/创造性/侵权风险）
- 分析依据（法律条文 + 技术事实）
"""

    async def execute(self, context: AgentExecutionContext) -> str:
        """
        执行分析任务

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        try:
            # 获取输入数据
            user_input = context.input_data.get("user_input", "")
            previous_results = context.input_data.get("previous_results", {})

            # 确定分析类型
            analysis_type = context.config.get("analysis_type", "novelty")

            self.logger.info(f"开始分析任务: {context.task_id}, 类型: {analysis_type}")

            # 根据分析类型执行不同的分析
            if analysis_type == "novelty":
                output_data = await self._analyze_novelty(user_input, previous_results)
            elif analysis_type == "creativity":
                output_data = await self._analyze_creativity(user_input, previous_results)
            elif analysis_type == "infringement":
                output_data = await self._analyze_infringement(user_input, previous_results)
            else:
                # 默认：技术特征提取
                output_data = await self._extract_features(user_input, previous_results)

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=output_data,
                metadata={"analysis_type": analysis_type},
            )

        except Exception as e:
            self.logger.exception(f"分析任务失败: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
            )

    async def _extract_features(
        self,
        user_input: str,
        previous_results: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        提取技术特征

        Args:
            user_input: 用户输入
            previous_results: 前面步骤的结果

        Returns:
            技术特征提取结果
        """
        # 获取目标专利
        target_patent = self._get_target_patent(user_input, previous_results)

        prompt = f"""请从以下专利文本中提取技术特征，并构建层次化结构。

专利文本：
{target_patent}

要求：
1. 提取独立权利要求的全部技术特征
2. 区分必要技术特征和附加技术特征
3. 构建技术特征的层次结构
4. 识别技术领域和技术问题

输出格式：JSON
{{
    "technical_field": "技术领域",
    "technical_problem": "技术问题",
    "essential_features": []

        {{"feature": "特征1", "description": "描述"}},
        {{"feature": "特征2", "description": "描述"}}
    ,
    "additional_features": []

        {{"feature": "特征3", "description": "描述"}}
    
}}
"""

        response = await self.llm_manager.generate(
            prompt=prompt,
            system_prompt=self.get_system_prompt(),
            model="kimi-k2.5",
        )

        # 解析JSON
        import json
        try:
            features = json.loads(response)
            return {"features": features, "raw_text": target_patent}
        except json.JSONDecodeError:
            self.logger.error("技术特征提取响应解析失败")
            return {"features": {}, "raw_text": target_patent}

    async def _analyze_novelty(
        self,
        user_input: str,
        previous_results: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """
        新颖性分析

        Args:
            user_input: 用户输入
            previous_results: 前面步骤的结果

        Returns:
            新颖性分析结果
        """
        # 获取目标专利和对比文件
        self._get_target_patent(user_input, previous_results)
        reference_docs = self._get_reference_documents(previous_results)

        # 先提取技术特征
        features_result = await self._extract_features(user_input, previous_results)
        features = features_result.get("features", {})

        prompt = f"""请对目标专利进行新颖性分析。

目标专利技术特征：
{features.get('essential_features', [])}

对比文件：
{self._format_reference_docs(reference_docs)}

要求：
1. 逐一比对技术特征
2. 判断哪些特征被对比文件公开
3. 识别区别技术特征
4. 评估新颖性

输出格式：JSON
{{
    "feature_comparison": []

        {{
            "feature": "特征1",
            "disclosed_in": ["D1", "D2"],
            "novel": false
        }},
        {{
            "feature": "特征2",
            "disclosed_in": Optional[[],]

            "novel": true,
            "difference": "区别说明"
        }}
    ,
    "novelty_conclusion": "具备/不具备新颖性",
    "novelty_basis": "新颖性依据"
}}
"""

        response = await self.llm_manager.generate(
            prompt=prompt,
            system_prompt=self.get_system_prompt(),
            model="kimi-k2.5",
        )

        # 解析JSON
        import json
        try:
            analysis = json.loads(response)
            return {
                "analysis_type": "novelty",
                "features": features,
                "analysis": analysis,
            }
        except json.JSONDecodeError:
            self.logger.error("新颖性分析响应解析失败")
            return {
                "analysis_type": "novelty",
                "features": features,
                "analysis": {},
            }

    async def _analyze_creativity(
        self,
        user_input: str,
        previous_results: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """
        创造性分析

        Args:
            user_input: 用户输入
            previous_results: 前面步骤的结果

        Returns:
            创造性分析结果
        """
        # 复用新颖性分析的结果
        novelty_result = await self._analyze_novelty(user_input, previous_results)
        features = novelty_result.get("features", {})

        # 获取对比文件
        reference_docs = self._get_reference_documents(previous_results)

        prompt = f"""请对目标专利进行创造性分析。

区别技术特征：
{novelty_result.get('analysis', {}).get('feature_comparison', [])}

对比文件：
{self._format_reference_docs(reference_docs)}

要求：
1. 评估区别技术特征的创造性高度
2. 判断是否显而易见
3. 分析技术启示
4. 评估预料不到的效果

输出格式：JSON
{{
    "distinctive_features": ["特征1", "特征2"],
    "obviousness_analysis": []

        {{
            "feature": "特征1",
            "closest_prior_art": "D1",
            "difference": "区别",
            "teaching_suggestion": "有无技术启示",
            "obvious": false,
            "reason": "理由"
        }}
    ,
    "unexpected_effect": "预料不到的效果",
    "creativity_conclusion": "具备/不具备创造性",
    "creativity_level": "高/中/低"
}}
"""

        response = await self.llm_manager.generate(
            prompt=prompt,
            system_prompt=self.get_system_prompt(),
            model="kimi-k2.5",
        )

        # 解析JSON
        import json
        try:
            analysis = json.loads(response)
            return {
                "analysis_type": "creativity",
                "features": features,
                "novelty_analysis": novelty_result.get("analysis", {}),
                "creativity_analysis": analysis,
            }
        except json.JSONDecodeError:
            self.logger.error("创造性分析响应解析失败")
            return {
                "analysis_type": "creativity",
                "features": features,
                "creativity_analysis": {},
            }

    async def _analyze_infringement(
        self,
        user_input: str,
        previous_results: Optional[dict[str, Any]]

    ) -> dict[str, Any]:
        """
        侵权分析

        Args:
            user_input: 用户输入
            previous_results: 前面步骤的结果

        Returns:
            侵权分析结果
        """
        # 获取专利和被控产品
        target_patent = self._get_target_patent(user_input, previous_results)
        accused_product = context.config.get("accused_product", "")

        prompt = f"""请分析被控产品是否侵犯目标专利权。

目标专利：
{target_patent}

被控产品：
{accused_product}

要求：
1. 解释权利要求（字面含义）
2. 应用全面覆盖原则
3. 逐一比对技术特征
4. 分析等同侵权可能性

输出格式：JSON
{{
    "claim_interpretation": "权利要求解释",
    "feature_comparison": []

        {{
            "claim_feature": "权利要求特征",
            "product_feature": "产品特征",
            "match": true,
            "equivalent": false,
            "analysis": "分析"
        }}
    ,
    "infringement_conclusion": "侵权/不侵权/可能侵权",
    "infringement_type": "字面侵权/等同侵权/不侵权",
    "risk_level": "高/中/低"
}}
"""

        response = await self.llm_manager.generate(
            prompt=prompt,
            system_prompt=self.get_system_prompt(),
            model="kimi-k2.5",
        )

        # 解析JSON
        import json
        try:
            analysis = json.loads(response)
            return {
                "analysis_type": "infringement",
                "analysis": analysis,
            }
        except json.JSONDecodeError:
            self.logger.error("侵权分析响应解析失败")
            return {
                "analysis_type": "infringement",
                "analysis": {},
            }

    def _get_target_patent(
        self,
        user_input: str,
        previous_results: Optional[dict[str, Any]]

    ) -> str:
        """获取目标专利文本"""
        # 从用户输入或前面步骤的结果中提取
        if "patent_text" in previous_results:
            return previous_results["patent_text"]
        return user_input

    def _get_reference_documents(self, previous_results: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        """获取对比文件"""
        if "xiaona_retriever" in previous_results:
            return previous_results["xiaona_retriever"].get("patents", [])
        return []

    def _format_reference_docs(self, docs: Optional[list[dict[str, Any]]] = None) -> str:
        """格式化对比文件"""
        formatted = []
        for i, doc in enumerate(docs[:5], 1):  # 最多5篇
            formatted.append(f"D{i}: {doc.get('title', '')}\n{doc.get('abstract', '')}")
        return "\n\n".join(formatted)
