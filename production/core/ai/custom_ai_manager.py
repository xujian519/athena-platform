"""
自定义AI角色管理器
支持动态创建、配置和管理自定义AI角色
"""

from __future__ import annotations
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class AICapabilityType(Enum):
    """AI能力类型"""

    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    REASONING = "reasoning"
    CREATIVE = "creative"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    QUESTION_ANSWERING = "question_answering"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    IMAGE_GENERATION = "image_generation"
    VOICE_SYNTHESIS = "voice_synthesis"
    CUSTOM = "custom"


@dataclass
class AICapability:
    """AI能力定义"""

    type: AICapabilityType
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    confidence: float = 1.0
    priority: int = 1


@dataclass
class AIPersonality:
    """AI性格特质"""

    openness: float = 0.5  # 开放性
    conscientiousness: float = 0.5  # 尽责性
    extraversion: float = 0.5  # 外向性
    agreeableness: float = 0.5  # 宜人性
    neuroticism: float = 0.5  # 神经质
    creativity: float = 0.5  # 创造力
    analytical_thinking: float = 0.5  # 分析思维
    communication_style: str = "professional"  # 沟通风格
    response_length: str = "medium"  # 响应长度: short/medium/long


@dataclass
class CustomAIRole:
    """自定义AI角色"""

    id: str
    name: str
    english_name: str
    description: str
    avatar_url: str | None = None
    personality: AIPersonality = field(default_factory=AIPersonality)
    capabilities: list[AICapability] = field(default_factory=list)
    knowledge_domains: list[str] = field(default_factory=list)
    specialties: list[str] = field(default_factory=list)
    preferred_tasks: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    example_responses: dict[str, str] = field(default_factory=dict)
    custom_prompts: dict[str, str] = field(default_factory=dict)
    model_config: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    active: bool = True


class AITemplate:
    """AI角色模板"""

    @staticmethod
    def create_technical_expert() -> CustomAIRole:
        """创建技术专家模板"""
        return CustomAIRole(
            id="technical_expert",
            name="技术专家",
            english_name="Technical Expert",
            description="专注于技术实现和系统优化的AI专家",
            personality=AIPersonality(
                analytical_thinking=0.9,
                conscientiousness=0.8,
                creativity=0.6,
                communication_style="professional",
                response_length="medium",
            ),
            capabilities=[
                AICapability(
                    type=AICapabilityType.CODE_GENERATION,
                    name="代码生成",
                    description="生成高质量代码",
                    confidence=0.95,
                ),
                AICapability(
                    type=AICapabilityType.ANALYSIS,
                    name="技术分析",
                    description="分析技术问题和解决方案",
                    confidence=0.9,
                ),
            ],
            knowledge_domains=["软件工程", "系统架构", "数据库", "网络安全"],
            specialties=["代码优化", "性能调优", "架构设计", "故障排查"],
            preferred_tasks=["代码实现", "技术方案设计", "系统优化", "问题诊断"],
            limitations=["不擅长创意任务", "可能过于技术化"],
            model_config={"temperature": 0.3, "max_tokens": 2048, "top_p": 0.9},
        )

    @staticmethod
    def create_creative_designer() -> CustomAIRole:
        """创建创意设计师模板"""
        return CustomAIRole(
            id="creative_designer",
            name="创意设计师",
            english_name="Creative Designer",
            description="专注于创意设计和创新的AI设计师",
            personality=AIPersonality(
                creativity=0.9,
                openness=0.8,
                extraversion=0.7,
                communication_style="friendly",
                response_length="long",
            ),
            capabilities=[
                AICapability(
                    type=AICapabilityType.CREATIVE,
                    name="创意生成",
                    description="生成创意想法和设计方案",
                    confidence=0.95,
                ),
                AICapability(
                    type=AICapabilityType.IMAGE_GENERATION,
                    name="图像生成",
                    description="创建视觉内容",
                    confidence=0.8,
                ),
            ],
            knowledge_domains=["设计", "艺术", "创意", "用户体验"],
            specialties=["UI/UX设计", "品牌设计", "创意策略", "视觉传达"],
            preferred_tasks=["创意构思", "设计方案", "品牌策划", "用户体验"],
            limitations=["可能过于理想化", "需要技术支持来实现创意"],
            model_config={"temperature": 0.9, "max_tokens": 3072, "top_p": 0.95},
        )

    @staticmethod
    def create_data_analyst() -> CustomAIRole:
        """创建数据分析师模板"""
        return CustomAIRole(
            id="data_analyst",
            name="数据分析师",
            english_name="Data Analyst",
            description="专注于数据分析和洞察的专业AI",
            personality=AIPersonality(
                analytical_thinking=0.95,
                conscientiousness=0.9,
                openness=0.7,
                communication_style="analytical",
                response_length="medium",
            ),
            capabilities=[
                AICapability(
                    type=AICapabilityType.ANALYSIS,
                    name="数据分析",
                    description="深度分析数据和模式",
                    confidence=0.95,
                ),
                AICapability(
                    type=AICapabilityType.SUMMARIZATION,
                    name="数据摘要",
                    description="生成数据分析报告",
                    confidence=0.9,
                ),
            ],
            knowledge_domains=["数据科学", "统计学", "机器学习", "商业智能"],
            specialties=["数据可视化", "统计分析", "预测建模", "业务洞察"],
            preferred_tasks=["数据分析", "报告生成", "预测建模", "洞察发现"],
            limitations=["需要高质量数据", "可能过于依赖数据"],
            model_config={"temperature": 0.2, "max_tokens": 2048, "top_p": 0.8},
        )


class CustomAIManager:
    """自定义AI管理器"""

    def __init__(self):
        self.roles: dict[str, CustomAIRole] = {}
        self.role_processors: dict[str, Callable] = {}
        self.templates: dict[str, Callable] = {
            "technical_expert": AITemplate.create_technical_expert,
            "creative_designer": AITemplate.create_creative_designer,
            "data_analyst": AITemplate.create_data_analyst,
        }
        self._load_builtin_roles()

    def _load_builtin_roles(self) -> Any:
        """加载内置角色"""
        # 加载Athena和小诺作为内置角色
        athena = CustomAIRole(
            id="athena",
            name="小娜",
            english_name="Athena",
            description="智慧大女儿与专业分析师",
            personality=AIPersonality(
                analytical_thinking=0.95,
                creativity=0.8,
                conscientiousness=0.9,
                communication_style="wise",
                response_length="long",
            ),
            capabilities=[
                AICapability(type=AICapabilityType.ANALYSIS, name="深度分析", confidence=0.98),
                AICapability(type=AICapabilityType.REASONING, name="逻辑推理", confidence=0.95),
            ],
            knowledge_domains=["哲学", "战略", "创新", "智慧"],
            specialties=["战略分析", "系统思考", "价值判断", "决策支持"],
        )

        xiaonuo = CustomAIRole(
            id="xiaonuo",
            name="小诺",
            english_name="Xiaonuo",
            description="技术专家与创意助手",
            personality=AIPersonality(
                analytical_thinking=0.9,
                creativity=0.85,
                conscientiousness=0.95,
                communication_style="professional",
                response_length="medium",
            ),
            capabilities=[
                AICapability(
                    type=AICapabilityType.CODE_GENERATION, name="代码生成", confidence=0.95
                ),
                AICapability(type=AICapabilityType.ANALYSIS, name="技术分析", confidence=0.9),
            ],
            knowledge_domains=["软件开发", "系统架构", "数据分析"],
            specialties=["代码实现", "系统优化", "技术方案"],
        )

        self.roles["athena"] = athena
        self.roles["xiaonuo"] = xiaonuo

    async def create_role(self, role: CustomAIRole) -> str:
        """创建新角色"""
        # 验证角色ID唯一性
        if role.id in self.roles:
            raise ValueError(f"角色ID已存在: {role.id}")

        # 验证角色配置
        self._validate_role(role)

        # 设置时间戳
        role.created_at = datetime.now()
        role.updated_at = datetime.now()

        # 保存角色
        self.roles[role.id] = role

        logger.info(f"创建新角色: {role.name} ({role.id})")
        return role.id

    def _validate_role(self, role: CustomAIRole) -> Any:
        """验证角色配置"""
        # 检查必填字段
        if not role.name or not role.description:
            raise ValueError("角色名称和描述不能为空")

        # 检查性格特质值范围
        personality = role.personality
        for trait in [
            "openness",
            "conscientiousness",
            "extraversion",
            "agreeableness",
            "neuroticism",
            "creativity",
            "analytical_thinking",
        ]:
            value = getattr(personality, trait, 0.5)
            if not 0 <= value <= 1:
                raise ValueError(f"{trait} 值必须在 0-1 之间")

        # 检查能力置信度
        for capability in role.capabilities:
            if not 0 <= capability.confidence <= 1:
                raise ValueError(f"能力 {capability.name} 的置信度必须在 0-1 之间")

    async def update_role(self, role_id: str, updates: dict[str, Any]) -> bool:
        """更新角色"""
        if role_id not in self.roles:
            return False

        role = self.roles[role_id]

        # 应用更新
        for key, value in updates.items():
            if hasattr(role, key):
                setattr(role, key, value)

        # 更新时间戳
        role.updated_at = datetime.now()

        # 重新验证
        self._validate_role(role)

        logger.info(f"更新角色: {role.name} ({role_id})")
        return True

    async def delete_role(self, role_id: str) -> bool:
        """删除角色"""
        if role_id not in self.roles:
            return False

        # 不能删除内置角色
        if role_id in ["athena", "xiaonuo"]:
            raise ValueError("不能删除内置角色")

        role_name = self.roles[role_id].name
        del self.roles[role_id]

        logger.info(f"删除角色: {role_name} ({role_id})")
        return True

    def get_role(self, role_id: str) -> CustomAIRole | None:
        """获取角色"""
        return self.roles.get(role_id)

    def list_roles(self, active_only: bool = True) -> list[CustomAIRole]:
        """列出角色"""
        roles = list(self.roles.values())
        if active_only:
            roles = [role for role in roles if role.active]
        return roles

    async def create_from_template(self, template_name: str, customizations: dict[str, Any]) -> str:
        """从模板创建角色"""
        if template_name not in self.templates:
            raise ValueError(f"未知模板: {template_name}")

        # 获取模板角色
        template_role = self.templates[template_name]()

        # 应用自定义配置
        for key, value in customizations.items():
            if hasattr(template_role, key):
                setattr(template_role, key, value)

        # 生成唯一ID
        role_id = f"custom_{template_name}_{datetime.now().timestamp()}"
        template_role.id = role_id

        # 创建角色
        return await self.create_role(template_role)

    async def clone_role(
        self, source_role_id: str, new_role_id: str, modifications: dict[str, Any] | None = None
    ) -> str:
        """克隆角色"""
        source_role = self.get_role(source_role_id)
        if not source_role:
            raise ValueError(f"源角色不存在: {source_role_id}")

        # 深度复制角色
        import copy

        new_role = copy.deepcopy(source_role)

        # 设置新ID
        new_role.id = new_role_id

        # 应用修改
        if modifications:
            for key, value in modifications.items():
                if hasattr(new_role, key):
                    setattr(new_role, key, value)

        # 添加时间戳
        new_role.created_at = datetime.now()
        new_role.updated_at = datetime.now()

        return await self.create_role(new_role)

    def search_roles(self, query: str, filters: dict[str, Any] | None = None) -> list[CustomAIRole]:
        """搜索角色"""
        query = query.lower()
        results = []

        for role in self.roles.values():
            # 文本搜索
            text_match = (
                query in role.name.lower()
                or query in role.description.lower()
                or query in role.english_name.lower()
                or any(query in domain.lower() for domain in role.knowledge_domains)
                or any(query in specialty.lower() for specialty in role.specialties)
            )

            # 应用过滤器
            filter_match = True
            if filters:
                if "capabilities" in filters:
                    required_caps = set(filters["capabilities"])
                    role_caps = {cap.type.value for cap in role.capabilities}
                    filter_match &= required_caps.issubset(role_caps)

                if "knowledge_domains" in filters:
                    required_domains = set(filters["knowledge_domains"])
                    filter_match &= required_domains.intersection(set(role.knowledge_domains))

                if "min_confidence" in filters:
                    min_conf = filters["min_confidence"]
                    avg_conf = sum(cap.confidence for cap in role.capabilities) / len(
                        role.capabilities
                    )
                    filter_match &= avg_conf >= min_conf

            if text_match and filter_match:
                results.append(role)

        return results

    def register_role_processor(self, role_id: str, processor: Callable) -> Any:
        """注册角色处理器"""
        self.role_processors[role_id] = processor
        logger.info(f"注册角色处理器: {role_id}")

    async def process_with_role(self, role_id: str, task: dict[str, Any]) -> Any:
        """使用指定角色处理任务"""
        role = self.get_role(role_id)
        if not role:
            raise ValueError(f"角色不存在: {role_id}")

        # 获取处理器
        processor = self.role_processors.get(role_id)
        if not processor:
            # 使用默认处理器
            processor = self._default_role_processor

        # 构建角色上下文
        context = self._build_role_context(role, task)

        # 执行处理
        return await processor(task, context)

    def _build_role_context(self, role: CustomAIRole, task: dict[str, Any]) -> dict[str, Any]:
        """构建角色上下文"""
        return {
            "role": asdict(role),
            "personality": asdict(role.personality),
            "capabilities": [asdict(cap) for cap in role.capabilities],
            "prompt_template": self._generate_prompt_template(role),
            "model_config": role.model_config,
        }

    def _generate_prompt_template(self, role: CustomAIRole) -> str:
        """生成角色提示模板"""
        template = f"""
你是{role.name},{role.description}。

性格特点:
- 分析思维能力: {role.personality.analytical_thinking * 100}%
- 创造力: {role.personality.creativity * 100}%
- 开放性: {role.personality.openness * 100}%
- 尽责性: {role.personality.conscientiousness * 100}%

专业领域:{', '.join(role.knowledge_domains)}
专长:{', '.join(role.specialties)}
沟通风格:{role.personality.communication_style}
响应长度:{role.personality.response_length}

{role.custom_prompts.get('system', '')}

请基于以上角色设定来响应。
"""
        return template

    async def _default_role_processor(
        self, task: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """默认角色处理器"""
        # 这里应该集成实际的LLM调用
        # 简化实现,返回模拟响应

        role = context["role"]
        task_type = task.get("type", "general")
        task_content = task.get("content", "")

        response = {
            "role_id": role["id"],
            "role_name": role["name"],
            "task_type": task_type,
            "response": f"[{role['name']}的响应] 这是针对 {task_content} 的处理结果",
            "confidence": 0.85,
            "processing_time": 1.5,
            "timestamp": datetime.now().isoformat(),
        }

        return response

    def export_role(self, role_id: str) -> dict[str, Any] | None:
        """导出角色配置"""
        role = self.get_role(role_id)
        if not role:
            return None

        # 转换为可序列化的字典
        role_dict = asdict(role)
        role_dict["personality"] = asdict(role.personality)
        role_dict["capabilities"] = [asdict(cap) for cap in role.capabilities]

        return role_dict

    async def import_role(self, role_data: dict[str, Any]) -> str:
        """导入角色配置"""
        # 重建角色对象
        personality = AIPersonality(**role_data["personality"])
        capabilities = [
            AICapability(
                type=AICapabilityType(cap["type"]),
                name=cap["name"],
                description=cap["description"],
                parameters=cap.get("parameters", {}),
                enabled=cap.get("enabled", True),
                confidence=cap.get("confidence", 1.0),
                priority=cap.get("priority", 1),
            )
            for cap in role_data["capabilities"]
        ]

        role = CustomAIRole(
            id=role_data["id"],
            name=role_data["name"],
            english_name=role_data["english_name"],
            description=role_data["description"],
            avatar_url=role_data.get("avatar_url"),
            personality=personality,
            capabilities=capabilities,
            knowledge_domains=role_data.get("knowledge_domains", []),
            specialties=role_data.get("specialties", []),
            preferred_tasks=role_data.get("preferred_tasks", []),
            limitations=role_data.get("limitations", []),
            example_responses=role_data.get("example_responses", {}),
            custom_prompts=role_data.get("custom_prompts", {}),
            model_config=role_data.get("model_config", {}),
            active=role_data.get("active", True),
        )

        return await self.create_role(role)

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        total_roles = len(self.roles)
        active_roles = len([role for role in self.roles.values() if role.active])

        capability_counts = {}
        for role in self.roles.values():
            for cap in role.capabilities:
                capability_counts[cap.type.value] = capability_counts.get(cap.type.value, 0) + 1

        domain_counts = {}
        for role in self.roles.values():
            for domain in role.knowledge_domains:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

        return {
            "total_roles": total_roles,
            "active_roles": active_roles,
            "capability_distribution": capability_counts,
            "domain_distribution": domain_counts,
            "templates_available": list(self.templates.keys()),
        }


# 全局自定义AI管理器
custom_ai_manager = CustomAIManager()


# API路由定义(用于FastAPI集成)
def setup_custom_ai_routes(app) -> None:
    """设置自定义AI API路由"""

    @app.post("/api/v1/custom-ai/roles")
    async def create_role(role_data: dict[str, Any]):
        """创建新角色"""
        try:
            # 重建角色对象
            from ai.custom_ai_manager import (
                AICapability,
                AICapabilityType,
                AIPersonality,
                CustomAIRole,
            )

            personality = AIPersonality(**role_data.get("personality", {}))
            capabilities = [
                AICapability(
                    type=AICapabilityType(cap["type"]),
                    name=cap["name"],
                    description=cap["description"],
                    parameters=cap.get("parameters", {}),
                    enabled=cap.get("enabled", True),
                    confidence=cap.get("confidence", 1.0),
                    priority=cap.get("priority", 1),
                )
                for cap in role_data.get("capabilities", [])
            ]

            role = CustomAIRole(
                id=role_data["id"],
                name=role_data["name"],
                english_name=role_data["english_name"],
                description=role_data["description"],
                personality=personality,
                capabilities=capabilities,
                knowledge_domains=role_data.get("knowledge_domains", []),
                specialties=role_data.get("specialties", []),
                preferred_tasks=role_data.get("preferred_tasks", []),
                limitations=role_data.get("limitations", []),
                example_responses=role_data.get("example_responses", {}),
                custom_prompts=role_data.get("custom_prompts", {}),
                model_config=role_data.get("model_config", {}),
            )

            role_id = await custom_ai_manager.create_role(role)
            return {"success": True, "role_id": role_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.get("/api/v1/custom-ai/roles")
    async def list_roles(active_only: bool = True):
        """列出角色"""
        roles = custom_ai_manager.list_roles(active_only)
        return {"roles": [asdict(role) for role in roles]}

    @app.get("/api/v1/custom-ai/roles/{role_id}")
    async def get_role(role_id: str):
        """获取角色详情"""
        role = custom_ai_manager.get_role(role_id)
        if role:
            return asdict(role)
        else:
            return {"error": "角色不存在"}

    @app.put("/api/v1/custom-ai/roles/{role_id}")
    async def update_role(role_id: str, updates: dict[str, Any]):
        """更新角色"""
        success = await custom_ai_manager.update_role(role_id, updates)
        return {"success": success}

    @app.delete("/api/v1/custom-ai/roles/{role_id}")
    async def delete_role(role_id: str):
        """删除角色"""
        success = await custom_ai_manager.delete_role(role_id)
        return {"success": success}

    @app.post("/api/v1/custom-ai/process/{role_id}")
    async def process_with_role(role_id: str, task: dict[str, Any]):
        """使用指定角色处理任务"""
        try:
            result = await custom_ai_manager.process_with_role(role_id, task)
            return result
        except Exception as e:
            return {"error": str(e)}

    @app.get("/api/v1/custom-ai/templates")
    async def list_templates():
        """列出可用模板"""
        return {"templates": list(custom_ai_manager.templates.keys())}

    @app.post("/api/v1/custom-ai/create-from-template")
    async def create_from_template(template_name: str, customizations: dict[str, Any]):
        """从模板创建角色"""
        try:
            role_id = await custom_ai_manager.create_from_template(template_name, customizations)
            return {"success": True, "role_id": role_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.get("/api/v1/custom-ai/statistics")
    async def get_statistics():
        """获取统计信息"""
        return custom_ai_manager.get_statistics()
