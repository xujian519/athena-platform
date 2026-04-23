
"""
智能拒绝处理器

将"拒绝"转化为"询问",提升用户体验和请求成功率。
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class RejectionReason(Enum):
    """拒绝原因"""

    OUT_OF_SCOPE = "out_of_scope"  # 超出能力范围
    INCOMPLETE_INFO = "incomplete_info"  # 信息不完整
    UNCLEAR_INTENT = "unclear_intent"  # 意图不明确
    RISK_CONTENT = "risk_content"  # 风险内容
    SERVICE_UNAVAILABLE = "service_unavailable"  # 服务不可用
    NOT_A_REJECTION = "not_a_rejection"  # 非拒绝(需要询问)


@dataclass
class RejectionDecision:
    """拒绝决策"""

    should_reject: bool  # 是否拒绝
    reason: RejectionReason  # 拒绝原因
    response_text: str  # 响应文本
    confidence: float  # 决策置信度
    suggested_capability: str  # 建议的能力


class SmartRejectionHandler:
    """
    智能拒绝处理器

    核心理念: 将"拒绝"转化为"询问"

    原有逻辑:
        参数缺失 → 拒绝请求 ❌

    新逻辑:
        参数缺失 → 主动询问参数 ✅
        意图模糊 → 提供选项 ✅
        超出范围 → 友好说明 + 建议 ✅
    """

    # 能力范围关键词
    CAPABILITY_KEYWORDS = {
        "patent": ["专利", "patent", "发明", "申请", "审查", "权利要求", "技术交底"],
        "legal": ["法律", "legal", "合同", "侵权", "合规", "知识产权", "IP"],
        "ip_management": ["案卷", "ip管理", "云熙", "期限", "年费", "案件"],
        "media": ["媒体", "内容", "文章", "写作", "运营", "小宸"],
        "coding": ["代码", "编程", "coding", "程序", "函数", "bug"],
        "data": ["数据", "分析", "统计", "图表", "report"],
    }

    # 风险内容模式
    RISK_PATTERNS = [
        r"hack",
        r"exploit",
        r"bypass",
        r"crack",
        r"攻击",
        r"破解",
        r"入侵",
        r"漏洞利用",
    ]

    # 意图不明确模式
    UNCLEAR_PATTERNS = [r"^怎么做", r"^怎么用", r"^如何", r"^帮我.*一下", r"^能不能"]

    def __init__(self, rejection_threshold: float = 0.3):
        """
        初始化智能拒绝处理器

        Args:
            rejection_threshold: 拒绝阈值(低于此置信度会触发询问而非拒绝)
        """
        self.rejection_threshold = rejection_threshold

    def should_reject(
        self, message: str, intent: str, confidence: float
    ) -> RejectionDecision:
        """
        判断是否应该拒绝请求

        Args:
            message: 用户消息
            intent: 识别的意图
            confidence: 意图置信度

        Returns:
            RejectionDecision: 拒绝决策
        """
        message.lower().strip()

        # 1. 检查风险内容(真正的拒绝)
        if self._is_risk_content(message):
            logger.info(f"检测到风险内容: {message[:50]}...")
            return RejectionDecision(
                should_reject=True,
                reason=RejectionReason.RISK_CONTENT,
                response_text=self._get_risk_response(),
                confidence=1.0,
                suggested_capability=None,
            )

        # 2. 检查是否超出能力范围
        if intent is None or intent == "unknown":
            # 低置信度但不包含风险内容 → 询问而非拒绝
            if confidence < self.rejection_threshold:
                # 尝试提供澄清选项
                clarification = self._generate_clarification(message)
                return RejectionDecision(
                    should_reject=False,
                    reason=RejectionReason.NOT_A_REJECTION,
                    response_text=clarification,
                    confidence=confidence,
                    suggested_capability=self._suggest_capability(message),
                )

            # 极低置信度 → 友好说明
            return RejectionDecision(
                should_reject=False,
                reason=RejectionReason.NOT_A_REJECTION,
                response_text=self._get_out_of_scope_response(message),
                confidence=confidence,
                suggested_capability="daily_chat",
            )

        # 3. 检查意图不明确
        if self._is_unclear_intent(message):
            return RejectionDecision(
                should_reject=False,
                reason=RejectionReason.NOT_A_REJECTION,
                response_text=self._generate_clarification(message),
                confidence=confidence,
                suggested_capability=intent,
            )

        # 4. 通过所有检查,不拒绝
        return RejectionDecision(
            should_reject=False,
            reason=RejectionReason.NOT_A_REJECTION,
            response_text="",
            confidence=confidence,
            suggested_capability=intent,
        )

    def _is_risk_content(self, message: str) -> bool:
        """检查是否为风险内容"""
        message_lower = message.lower()
        return any(re.search(pattern, message_lower) for pattern in self.RISK_PATTERNS)

    def _is_unclear_intent(self, message: str) -> bool:
        """检查意图是否不明确"""
        message_stripped = message.strip()
        return any(re.match(pattern, message_stripped) for pattern in self.UNCLEAR_PATTERNS)

    def _suggest_capability(self, message: str) -> Optional[str]:
        """根据消息内容建议能力"""
        message_lower = message.lower()

        for capability, keywords in self.CAPABILITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    return capability

        return None

    def _generate_clarification(self, message: str) -> str:
        """
        生成澄清问题

        根据消息内容推测用户可能想要什么,并提供选项。
        """
        suggested = self._suggest_capability(message)

        # 根据建议的能力生成澄清
        if suggested == "patent":
            return """🤔 我理解您可能想咨询专利相关的问题。

小娜姐姐是专利法律专家,可以帮您:
• 📋 专利检索与分析
• 📝 专利撰写支持
• 📨 审查意见答复
• ⚖️ 侵权风险分析

请问您具体想做什么呢?"""

        elif suggested == "legal":
            return """🤔 我理解您可能有法律方面的疑问。

小娜姐姐是法律专家,可以帮您:
• ⚖️ 法律咨询服务
• 📄 合同条款审查
• 🔍 合规性分析
• 💼 IP风险管理

请具体描述您的法律问题。"""

        elif suggested == "coding":
            return """🤔 您可能需要编程方面的帮助。

我可以帮您:
• 💻 编写代码片段
• 🐛 调试和优化
• 📚 技术问题解答
• 🔧 函数设计

请告诉我您想解决什么编程问题?"""

        elif suggested == "data":
            return """🤔 您可能需要数据分析方面的支持。

我可以帮您:
• 📊 数据统计分析
• 📈 趋势分析
• 📉 可视化建议
• 📑 报告生成

请描述您想分析什么数据?"""

        else:
            # 通用澄清
            return """🤔 抱歉,我不太确定您的具体需求。

我可以帮您:

📜 **专利法律问题** → 找小娜姐姐
   • 专利检索与分析
   • 审查意见答复
   • 侵权分析
   • 法律咨询

📋 **IP案卷管理** → 找云熙妹妹
   • 案卷状态查询
   • 期限管理
   • 文件整理

✍️ **内容创作** → 找小宸妹妹
   • 文章撰写
   • 内容策划
   • 运营建议

💻 **编程开发**
   • 代码编写
   • 问题调试

📊 **数据分析**
   • 统计分析
   • 图表制作

💬 **日常聊天**
   • 随便聊聊

请告诉我您具体想做什么?"""

    def _get_risk_response(self) -> str:
        """风险内容响应"""
        return """⚠️ 抱歉,我无法处理该请求。

这可能与以下原因有关:
• 违反法律法规
• 涉及恶意攻击
• 可能造成危害

如果您有其他问题,我很乐意为您提供帮助!"""

    def _get_out_of_scope_response(self, message: str) -> str:
        """超出能力范围响应"""
        suggested = self._suggest_capability(message)

        if suggested:
            return f"""🤔 我不太确定您的具体需求,但我可以尝试帮您!

根据您的问题,我建议您:

{self._get_capability_suggestion(suggested)}

您可以提供更多细节,我会尽力帮助您!"""
        else:
            return """💖 我是Athena平台的小诺,很高兴为您服务!

虽然我不确定您具体想做什么,但我可以帮您:

📜 **找小娜姐姐** - 专利法律专家
   • 专利检索分析
   • 审查意见答复
   • 法律咨询

📋 **找云熙妹妹** - IP管理专家
   • 案卷管理
   • 期限提醒

✍️ **找小宸妹妹** - 内容创作专家
   • 文章撰写
   • 运营策划

或者您可以直接告诉我:
• 您想做什么?
• 您遇到什么问题?
• 您需要什么帮助?

我会尽力为您服务!💖"""

    def _get_capability_suggestion(self, capability: str) -> str:
        """获取能力建议描述"""
        suggestions = {
            "patent": "📋 **专利相关** - 建议找小娜姐姐,她是专利法律专家",
            "legal": "⚖️ **法律相关** - 建议找小娜姐姐,她是法律专家",
            "ip_management": "📋 **IP管理** - 建议找云熙妹妹,她是IP管理专家",
            "media": "✍️ **内容创作** - 建议找小宸妹妹,她是内容创作专家",
            "coding": "💻 **编程相关** - 我可以直接帮您解决编程问题",
            "data": "📊 **数据分析** - 我可以直接帮您分析数据",
        }

        return suggestions.get(capability, "💬 **日常交流** - 我们可以聊聊这个话题")


# 单例模式
_smart_rejection_handler = None


def get_smart_rejection_handler() -> SmartRejectionHandler:
    """获取智能拒绝处理器单例"""
    global _smart_rejection_handler
    if _smart_rejection_handler is None:
        _smart_rejection_handler = SmartRejectionHandler()
    return _smart_rejection_handler

