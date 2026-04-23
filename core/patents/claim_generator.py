from __future__ import annotations
"""
专利权利要求生成器

基于论文2《Patentformer》和论文3《Can LLMs Generate High-Quality Claims?》
实现高质量权利要求生成功能。

核心功能：
1. 从发明描述生成基础权利要求
2. 生成从属权利要求
3. 技术术语规范化
4. 法律规则验证
5. 多格式输出
"""

import json
from dataclasses import dataclass, field
from enum import Enum


class ClaimType(Enum):
    """权利要求类型"""
    INDEPENDENT = "independent"  # 独立权利要求
    DEPENDENT = "dependent"  # 从属权利要求


class InventionType(Enum):
    """发明类型"""
    DEVICE = "device"  # 装置/产品
    METHOD = "method"  # 方法/工艺
    SYSTEM = "system"  # 系统/组合物
    COMPOSITION = "composition"  # 化学组合物
    USE = "use"  # 用途


@dataclass
class TechnicalFeature:
    """技术特征"""
    name: str
    type: str  # "component", "function", "relationship", "parameter"
    value: Optional[str] = None
    source: Optional[str] = None  # 在原文中的位置


@dataclass
class ClaimDraft:
    """权利要求草稿"""
    claim_number: int
    claim_type: ClaimType
    text: str
    features: list[TechnicalFeature] = field(default_factory=list)
    parent_ref: Optional[int] = None  # 引用的父权利要求号
    confidence: float = 0.5  # 生成置信度

    def to_dict(self) -> dict:
        return {
            "claim_number": self.claim_number,
            "claim_type": self.claim_type.value,
            "text": self.text,
            "parent_ref": self.parent_ref,
            "confidence": self.confidence,
            "features": [
                {"name": f.name, "type": f.type, "value": f.value}
                for f in self.features
            ]
        }


@dataclass
class ClaimsSet:
    """权利要求集合"""
    invention_title: str
    invention_type: InventionType
    independent_claims: list[ClaimDraft] = field(default_factory=list)
    dependent_claims: list[ClaimDraft] = field(default_factory=list)

    @property
    def total_claims(self) -> int:
        return len(self.independent_claims) + len(self.dependent_claims)

    @property
    def broadest_claim(self) -> ClaimDraft:
        """获取最宽的权利要求（通常第1项独立权利要求）"""
        if self.independent_claims:
            return self.independent_claims[0]
        return None

    def to_dict(self) -> dict:
        return {
            "invention_title": self.invention_title,
            "invention_type": self.invention_type.value,
            "total_claims": self.total_claims,
            "independent_claims": [c.to_dict() for c in self.independent_claims],
            "dependent_claims": [c.to_dict() for c in self.dependent_claims]
        }


class PatentClaimGenerator:
    """
    专利权利要求生成器

    结合论文2的生成技术和论文3的质量评估，生成高质量权利要求。
    """

    def __init__(self, llm_client=None, knowledge_base=None):
        """
        初始化生成器

        Args:
            llm_client: LLM客户端
            knowledge_base: 专利知识库（可选）
        """
        self.llm = llm_client
        self.knowledge_base = knowledge_base
        self._init_templates()

    def _init_templates(self):
        """初始化权利要求模板"""
        self.templates = {
            InventionType.DEVICE: self._device_template,
            InventionType.METHOD: self._method_template,
            InventionType.SYSTEM: self._system_template,
            InventionType.COMPOSITION: self._composition_template,
            InventionType.USE: self._use_template
        }

    def generate(self,
               description: str,
               invention_type: InventionType = InventionType.DEVICE,
               num_independent: int = 1,
               num_dependent: int = 5,
               include_detailed_features: bool = True) -> ClaimsSet:
        """
        生成完整的权利要求集合

        Args:
            description: 发明描述
            invention_type: 发明类型
            num_independent: 独立权利要求数量
            num_dependent: 从属权利要求数量
            include_detailed_features: 是否包含详细特征列表

        Returns:
            ClaimsSet: 生成的权利要求集合
        """
        # 步骤1: 提取技术特征
        features = self._extract_features(description)

        # 步骤2: 生成独立权利要求
        independent_claims = []
        for i in range(num_independent):
            claim = self._generate_independent_claim(
                i + 1, features, invention_type, description
            )
            independent_claims.append(claim)

        # 步骤3: 生成从属权利要求
        dependent_claims = []
        if num_dependent > 0 and independent_claims:
            for i in range(num_dependent):
                # 确定从属权利要求归属
                parent_idx = i % len(independent_claims)
                parent = independent_claims[parent_idx]

                claim = self._generate_dependent_claim(
                    len(independent_claims) + i + 1,
                    parent,
                    features,
                    invention_type
                )
                dependent_claims.append(claim)

        return ClaimsSet(
            invention_title=self._extract_title(description),
            invention_type=invention_type,
            independent_claims=independent_claims,
            dependent_claims=dependent_claims
        )

    def _extract_features(self, description: str) -> list[TechnicalFeature]:
        """从发明描述中提取技术特征"""
        prompt = f"""
你是一位技术分析专家。请从以下发明描述中提取技术特征。

发明描述:
{description}

请以JSON格式返回技术特征列表，每个特征包含:
- name: 特征名称
- type: 特征类型 (component/function/relationship/parameter)
- value: 特征值或描述
- source: 在原文中的大致位置

示例格式:
[
    {"name": "光伏板", "type": "component", "value": "太阳能转换装置", "source": "第1段"},
    {"name": "充电控制", "type": "function", "value": "协调充放电过程", "source": "第3段"}
]
        """

        response = self.llm.generate(prompt)

        try:
            features_data = json.loads(response)
            return [
                TechnicalFeature(
                    name=f.get("name", ""),
                    type=f.get("type", ""),
                    value=f.get("value"),
                    source=f.get("source", "")
                )
                for f in features_data
            ]
        except json.JSONDecodeError:
            # 解析失败，返回空特征列表
            return []

    def _generate_independent_claim(self,
                                  claim_number: int,
                                  features: list[TechnicalFeature],
                                  invention_type: InventionType,
                                  description: str) -> ClaimDraft:
        """生成独立权利要求"""
        template_func = self.templates.get(invention_type, self._device_template)

        prompt = f"""
你是一位资深专利代理人。请根据以下信息生成第{claim_number}项独立权利要求。

发明类型: {invention_type.value}
技术特征: {self._format_features(features)}
发明描述: {description}

要求：
1. 使用标准专利法术语
2. 结构完整：前序部分 + 过渡短语 + 主体部分
3. 技术特征描述清晰
4. 满足单一性要求
5. 使用"所述"进行指代

{template_func(claim_number)}

请只返回权利要求文本，不要其他解释。
        """

        response = self.llm.generate(prompt)

        return ClaimDraft(
            claim_number=claim_number,
            claim_type=ClaimType.INDEPENDENT,
            text=response.strip(),
            features=features,
            confidence=0.8
        )

    def _generate_dependent_claim(self,
                               claim_number: int,
                               parent_claim: ClaimDraft,
                               features: list[TechnicalFeature],
                               invention_type: InventionType) -> ClaimDraft:
        """生成从属权利要求"""
        # 选择一个特征作为附加
        additional_feature = None
        available_features = [f for f in features if f not in parent_claim.features]

        if available_features:
            additional_feature = available_features[claim_number % len(available_features)]

        prompt = f"""
你是一位资深专利代理人。请生成第{claim_number}项从属权利要求。

父权利要求（第{parent_claim.claim_number}项）:
{parent_claim.text}

可用的附加特征:
{self._format_features(features)}

要求：
1. 正确引用父权利要求："根据权利要求{parent_claim.claim_number}所述..."
2. 附加一个或多个技术特征到父权利要求
3. 使用"所述"指代父权利要求中的特征
4. 保持法律术语一致性

请只返回权利要求文本，格式：
{claim_number}. 根据权利要求{parent_claim.claim_number}所述的[装置/方法]，其特征还在于：
    [附加特征描述]

        """

        response = self.llm.generate(prompt)

        return ClaimDraft(
            claim_number=claim_number,
            claim_type=ClaimType.DEPENDENT,
            text=response.strip(),
            features=parent_claim.features + ([additional_feature] if additional_feature else []),
            parent_ref=parent_claim.claim_number,
            confidence=0.7
        )

    def _format_features(self, features: list[TechnicalFeature]) -> str:
        """格式化特征列表"""
        if not features:
            return "  （无明确特征）"

        lines = []
        for f in features:
            lines.append(f"  - {f.type}: {f.name}" + (f" ({f.value})" if f.value else ""))
        return "\n".join(lines)

    def _extract_title(self, description: str) -> str:
        """从描述中提取标题"""
        # 简单处理：取第一句话或前50字
        first_line = description.strip().split('\n')[0]
        if len(first_line) > 50:
            first_line = first_line[:47] + "..."
        return first_line

    # ==================== 模板方法 ====================

    @staticmethod
    def _device_template(claim_number: int) -> str:
        """装置类权利要求模板"""
        return f"""
{claim_number}. 一种[装置名称]，其特征在于：
    [组件1]，
    与所述[组件1]连接的[组件2]，
    与所述[组件2]通信连接的[组件3]，
    [功能描述]。
        """

    @staticmethod
    def _method_template(claim_number: int) -> str:
        """方法类权利要求模板"""
        return f"""
{claim_number}. 一种[方法名称]，包括以下步骤：
    [步骤1描述]；
    [步骤2描述]；
    [步骤3描述]；
    以及
    [步骤4描述]。

其中，[步骤1]在[条件]下进行。
        """

    @staticmethod
    def _system_template(claim_number: int) -> str:
        """系统类权利要求模板"""
        return f"""
{claim_number}. 一种[系统名称]，包括：
    [模块/单元1]；
    [模块/单元2]；以及
    [模块/单元3]；
其中，[模块/单元1]被配置为[功能1]，
    所述[模块/单元2]被配置为[功能2]。
        """

    @staticmethod
    def _composition_template(claim_number: int) -> str:
        """组合物类权利要求模板"""
        return f"""
{claim_number}. 一种[组合物名称]，包括：
    [组分1]，其含量为[范围1]；
    [组分2]，其含量为[范围2]；
    以及
    [组分3]，其含量为[范围3]。
        """

    @staticmethod
    def _use_template(claim_number: int) -> str:
        """用途类权利要求模板"""
        return f"""
{claim_number}. [化合物/产品]在[用途]中的用途，
其特征在于：
[用途特征描述]。
        """


# ==================== 辅助函数 ====================

def generate_from_invention_disclosure(
        disclosure: str,
        llm_client,
        invention_type: InventionType = InventionType.DEVICE
) -> ClaimsSet:
    """
    便捷函数：从发明披露生成权利要求

    Args:
        disclosure: 发明披露文本
        llm_client: LLM客户端
        invention_type: 发明类型

    Returns:
        ClaimsSet: 生成的权利要求
    """
    generator = PatentClaimGenerator(llm_client=llm_client)
    return generator.generate(
        description=disclosure,
        invention_type=invention_type,
        num_independent=1,
        num_dependent=5
    )


def format_claims_for_filing(claims_set: ClaimsSet) -> str:
    """
    格式化权利要求用于提交

    Args:
        claims_set: 权利要求集合

    Returns:
        str: 格式化后的权利要求文本
    """
    output_lines = []
    output_lines.append("权利要求书")
    output_lines.append("=" * 40)
    output_lines.append("")

    # 输出独立权利要求
    for claim in claims_set.independent_claims:
        output_lines.append(f"{claim.text}")
        output_lines.append("")

    # 输出从属权利要求
    for claim in claims_set.dependent_claims:
        output_lines.append(f"{claim.text}")
        output_lines.append("")

    return "\n".join(output_lines)


def export_claims_json(claims_set: ClaimsSet, filepath: str):
    """导出权利要求为JSON文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(claims_set.to_dict(), f, ensure_ascii=False, indent=2)
