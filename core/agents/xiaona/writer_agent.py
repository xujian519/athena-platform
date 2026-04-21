"""
小娜·撰写者

负责专利申请文件撰写、审查意见答复等任务。
"""

from typing import Any, Dict, List, Optional
import logging

from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)
from core.llm.unified_llm_manager import UnifiedLLMManager

logger = logging.getLogger(__name__)


class WriterAgent(BaseXiaonaComponent):
    """
    小娜·撰写者

    专注于专利文书撰写任务，包括：
    - 权利要求书撰写
    - 说明书撰写
    - 审查意见答复撰写
    - 无效宣告请求书撰写
    """

    def _initialize(self) -> None:
        """初始化撰写者智能体"""
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="claim_drafting",
                description="权利要求书撰写",
                input_types=["技术交底书", "技术特征"],
                output_types=["权利要求书"],
                estimated_time=30.0,
            ),
            AgentCapability(
                name="description_drafting",
                description="说明书撰写",
                input_types=["技术交底书", "权利要求书"],
                output_types=["说明书"],
                estimated_time=40.0,
            ),
            AgentCapability(
                name="office_action_response",
                description="审查意见答复",
                input_types=["审查意见", "对比文件"],
                output_types=["意见陈述书"],
                estimated_time=60.0,
            ),
            AgentCapability(
                name="invalidation_petition",
                description="无效宣告请求书",
                input_types=["目标专利", "证据"],
                output_types=["无效宣告请求书"],
                estimated_time=90.0,
            ),
        ])

        # 初始化LLM
        self.llm_manager = UnifiedLLMManager()

        self.logger.info(f"撰写者智能体初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是小娜·撰写者，专利文书撰写专家。

你的核心能力：
1. 权利要求书撰写：独立权利要求和从属权利要求
2. 说明书撰写：完整的技术描述
3. 审查意见答复：针对审查意见的陈述
4. 无效宣告请求书：无效理由和证据组织

撰写原则：
- 法律性：符合专利法及实施细则要求
- 技术性：准确描述技术方案
- 逻辑性：层次清晰、逻辑严谨
- 规范性：符合专利局格式要求

输出格式：
- 权利要求书：独立权利要求 + 从属权利要求
- 说明书：发明名称、技术领域、背景技术、发明内容、附图说明、具体实施方式
- 意见陈述书：意见陈述、修改说明、对比分析
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """
        执行撰写任务

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        try:
            # 获取输入数据
            user_input = context.input_data.get("user_input", "")
            previous_results = context.input_data.get("previous_results", {})

            # 确定撰写类型
            writing_type = context.config.get("writing_type", "description")

            self.logger.info(f"开始撰写任务: {context.task_id}, 类型: {writing_type}")

            # 根据撰写类型执行不同的撰写
            if writing_type == "claims":
                output_data = await self._draft_claims(user_input, previous_results)
            elif writing_type == "description":
                output_data = await self._draft_description(user_input, previous_results)
            elif writing_type == "office_action_response":
                output_data = await self._draft_response(user_input, previous_results)
            elif writing_type == "invalidation":
                output_data = await self._draft_invalidation(user_input, previous_results)
            else:
                # 默认：完整申请文件
                output_data = await self._draft_full_application(user_input, previous_results)

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=output_data,
                metadata={"writing_type": writing_type},
            )

        except Exception as e:
            self.logger.exception(f"撰写任务失败: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
            )

    async def _draft_claims(
        self,
        user_input: str,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        撰写权利要求书

        Args:
            user_input: 用户输入
            previous_results: 前面步骤的结果

        Returns:
            权利要求书内容
        """
        # 获取技术特征
        features = self._get_features(previous_results)

        prompt = f"""请根据技术特征撰写权利要求书。

技术特征：
{features}

要求：
1. 撰写1项独立权利要求
2. 撰写3-5项从属权利要求
3. 独立权利要求包含必要技术特征
4. 从属权利要求形成层次结构
5. 使用规范的专利撰写语言

输出格式：JSON
{{
    "independent_claim": "1. 一种[技术主题]，其特征在于，包括：...",
    "dependent_claims": [
        "2. 根据权利要求1所述的[技术主题]，其特征在于...",
        "3. 根据权利要求1或2所述的[技术主题]，其特征在于..."
    ]
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
            claims = json.loads(response)
            return {
                "document_type": "claims",
                "content": claims,
                "full_text": self._format_claims(claims),
            }
        except json.JSONDecodeError:
            self.logger.error("权利要求书撰写响应解析失败")
            return {
                "document_type": "claims",
                "content": {},
                "full_text": response,  # 如果解析失败，返回原始文本
            }

    async def _draft_description(
        self,
        user_input: str,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        撰写说明书

        Args:
            user_input: 用户输入
            previous_results: 前面步骤的结果

        Returns:
            说明书内容
        """
        # 获取技术特征和权利要求
        features = self._get_features(previous_results)
        claims = self._get_claims(previous_results)

        prompt = f"""请根据技术特征撰写完整的说明书。

技术特征：
{features}

权利要求书：
{claims}

要求：
1. 包含所有必要部分（发明名称、技术领域、背景技术、发明内容、附图说明、具体实施方式）
2. 详细描述技术方案
3. 提供具体实施例
4. 清楚说明有益效果

输出格式：JSON
{{
    "title": "发明名称",
    "technical_field": "技术领域",
    "background_art": "背景技术",
    "summary": "发明内容",
    "brief_description": "附图说明",
    "detailed_description": "具体实施方式"
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
            description = json.loads(response)
            return {
                "document_type": "description",
                "content": description,
                "full_text": self._format_description(description),
            }
        except json.JSONDecodeError:
            self.logger.error("说明书撰写响应解析失败")
            return {
                "document_type": "description",
                "content": {},
                "full_text": response,
            }

    async def _draft_response(
        self,
        user_input: str,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        撰写审查意见答复

        Args:
            user_input: 用户输入
            previous_results: 前面步骤的结果

        Returns:
            意见陈述书
        """
        # 获取审查意见和分析结果
        office_action = self._get_office_action(user_input, previous_results)
        analysis = self._get_analysis(previous_results)

        prompt = f"""请撰写审查意见答复陈述书。

审查意见：
{office_action}

分析结果：
{analysis}

要求：
1. 针对每条审查意见进行答复
2. 说明修改内容和理由
3. 与对比文件进行对比
4. 论述专利性和创造性
5. 使用礼貌、专业的语言

输出格式：JSON
{{
    "introduction": "开场陈述",
    "responses": [
        {{
            "issue": "审查意见1",
            "response": "答复内容",
            "amendments": "修改说明",
            "arguments": "论述理由"
        }}
    ],
    "conclusion": "总结陈述"
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
            response_doc = json.loads(response)
            return {
                "document_type": "office_action_response",
                "content": response_doc,
                "full_text": self._format_response(response_doc),
            }
        except json.JSONDecodeError:
            self.logger.error("审查意见答复撰写响应解析失败")
            return {
                "document_type": "office_action_response",
                "content": {},
                "full_text": response,
            }

    async def _draft_invalidation(
        self,
        user_input: str,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        撰写无效宣告请求书

        Args:
            user_input: 用户输入
            previous_results: 前面步骤的结果

        Returns:
            无效宣告请求书
        """
        # 获取目标专利和证据
        target_patent = self._get_target_patent(user_input, previous_results)
        evidence = self._get_evidence(previous_results)
        analysis = self._get_analysis(previous_results)

        prompt = f"""请撰写无效宣告请求书。

目标专利：
{target_patent}

证据：
{evidence}

分析结果：
{analysis}

要求：
1. 明确无效理由（新颖性/创造性/其他）
2. 引用证据文件
3. 逐一分析权利要求
4. 论述无效理由

输出格式：JSON
{{
    "petition_title": "无效宣告请求书",
    "target_patent": "目标专利信息",
    "ground_for_invalidity": "无效理由",
    "evidence_list": ["证据列表"],
    "claim_analysis": [
        {{
            "claim": "权利要求1",
            "evidence": "D1+D2",
            "analysis": "分析",
            "conclusion": "应予无效"
        }}
    ],
    "conclusion": "请求结论"
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
            petition = json.loads(response)
            return {
                "document_type": "invalidation_petition",
                "content": petition,
                "full_text": self._format_petition(petition),
            }
        except json.JSONDecodeError:
            self.logger.error("无效宣告请求书撰写响应解析失败")
            return {
                "document_type": "invalidation_petition",
                "content": {},
                "full_text": response,
            }

    async def _draft_full_application(
        self,
        user_input: str,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        撰写完整申请文件

        Args:
            user_input: 用户输入
            previous_results: 前面步骤的结果

        Returns:
            完整申请文件
        """
        # 依次撰写各部分
        claims_result = await self._draft_claims(user_input, previous_results)
        description_result = await self._draft_description(user_input, previous_results)

        # 组合完整申请文件
        full_application = {
            "claims": claims_result["content"],
            "description": description_result["content"],
            "full_text": (
                description_result["full_text"] + "\n\n" +
                "权利要求书\n" + "="*50 + "\n" +
                claims_result["full_text"]
            ),
        }

        return full_application

    def _format_claims(self, claims: Dict[str, Any]) -> str:
        """格式化权利要求书"""
        full_text = claims.get("independent_claim", "") + "\n\n"
        for claim in claims.get("dependent_claims", []):
            full_text += claim + "\n"
        return full_text

    def _format_description(self, description: Dict[str, Any]) -> str:
        """格式化说明书"""
        return "\n\n".join([
            description.get("title", ""),
            description.get("technical_field", ""),
            description.get("background_art", ""),
            description.get("summary", ""),
            description.get("brief_description", ""),
            description.get("detailed_description", ""),
        ])

    def _format_response(self, response: Dict[str, Any]) -> str:
        """格式化意见陈述书"""
        full_text = response.get("introduction", "") + "\n\n"
        for resp in response.get("responses", []):
            full_text += f"审查意见：{resp.get('issue', '')}\n"
            full_text += f"答复：{resp.get('response', '')}\n\n"
        full_text += response.get("conclusion", "")
        return full_text

    def _format_petition(self, petition: Dict[str, Any]) -> str:
        """格式化无效宣告请求书"""
        # 简化实现
        return str(petition)

    def _get_features(self, previous_results: Dict[str, Any]) -> Any:
        """获取技术特征"""
        if "xiaona_analyzer" in previous_results:
            return previous_results["xiaona_analyzer"].get("features", {})
        return {}

    def _get_claims(self, previous_results: Dict[str, Any]) -> str:
        """获取权利要求"""
        # 如果前面步骤已经撰写了权利要求
        return ""

    def _get_office_action(self, user_input: str, previous_results: Dict[str, Any]) -> str:
        """获取审查意见"""
        return user_input

    def _get_analysis(self, previous_results: Dict[str, Any]) -> Any:
        """获取分析结果"""
        if "xiaona_analyzer" in previous_results:
            return previous_results["xiaona_analyzer"]
        return {}

    def _get_target_patent(self, user_input: str, previous_results: Dict[str, Any]) -> str:
        """获取目标专利"""
        return user_input

    def _get_evidence(self, previous_results: Dict[str, Any]) -> List[Any]:
        """获取证据"""
        if "xiaona_retriever" in previous_results:
            return previous_results["xiaona_retriever"].get("patents", [])
        return []
