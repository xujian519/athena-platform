#!/usr/bin/env python3
"""
专利审查辩论系统 - 演示模式
Patent Debate System - Demo Mode

在DeepSeek API不可用时使用模拟响应进行演示

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-02-09
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.debate.debate_coordinator import DebateResult, DebateRound
from scripts.debate.debate_participants import DebateArgument, ParticipantRole
from scripts.debate.patent_examiner_agent import ExaminerOpinion, ExaminerStance

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


class DemoDebateCoordinator:
    """
    演示版辩论协调器

    使用预设的模拟响应，无需API密钥
    """

    def __init__(self, save_path: str | None = None):
        self.save_path = save_path or "/Users/xujian/Athena工作平台/logs/debate_results"
        Path(self.save_path).mkdir(parents=True, exist_ok=True)
        self.rounds: list = []

    async def conduct_debate(
        self,
        office_action: str,
        patent_response: str,
        patent_content: str,
    ) -> DebateResult:
        """进行模拟辩论"""
        logger.info("🎬 开始模拟辩论（演示模式）...")

        # 第1轮
        await asyncio.sleep(1)
        logger.info("\n" + "="*60)
        logger.info("第1轮辩论")
        logger.info("="*60)

        # 审查员分析
        examiner_opinion_1 = ExaminerOpinion(
            stance=ExaminerStance.PARTIAL_REJECT,
            reasoning="""作为审查员，我仔细阅读了申请人的答复。申请人提出了一些有价值的观点，但仍有一些疑虑需要澄清：

1. 关于"灌装"技术手段：申请人说明了重力自流式原理，这确实是常规技术。但说明书中没有明确Z形杆的具体结构和尺寸。

2. 关于"计量"技术手段：申请人提到了"定容计量法"，但没有给出圆孔的具体尺寸范围。

3. 关于"称重"技术手段：申请人认为不需要称重设备，这一点有争议。对于药品灌装，精度要求很高，定容计量可能无法满足。

4. 关于"如何用于药品灌装"：申请人引用了第[0020]段，但该段描述仍然比较概括。

总体而言，答复有一定道理，但还需要更多技术细节。""",
            key_concerns=[
                "Z形杆的具体结构和尺寸未说明",
                "圆孔尺寸范围未给出",
                "定容计量的精度能否满足药品要求",
                "工作原理描述过于概括"
            ],
            requested_clarifications=[
                "补充Z形杆的结构参数",
                "说明圆孔的推荐尺寸范围",
                "解释如何保证灌装精度"
            ],
            confidence=0.6
        )

        xiaona_arg_1 = DebateArgument(
            speaker="小娜·天秤女神",
            role=ParticipantRole.XIAONA,
            content="""感谢审查员的意见。针对审查员的疑虑，我补充说明：

**1. 关于Z形杆结构**
Z形杆是本领域的常规传动机构，其作用是将旋转运动转换为直线运动。本领域技术人员可以根据实际需要选择合适的尺寸。专利法不要求说明书列出所有可能的尺寸参数。

**2. 关于圆孔尺寸**
圆孔的直径可以根据需要灌装的药量进行设计。这是一个参数选择问题，不需要在说明书中穷举所有可能值。本领域技术人员可以根据常规试验确定合适尺寸。

**3. 关于精度问题**
定容计量在药品颗粒灌装中是常用方法。对于颗粒状药品，在密度稳定的情况下，定容计量的精度完全满足实用要求。这在本领域是公知常识。

**4. 关于工作原理**
说明书第[0020]段已经清晰描述了完整的工作流程，包括准备工作、开始灌装、停止灌装三个步骤。这已经充分公开了技术方案。""",
            legal_basis=["专利法第26条第3款", "审查指南第二部分第二章"],
            evidence=["成功案例202423012016.2", "公知常识"],
            confidence=0.85
        )

        athena_arg_1 = DebateArgument(
            speaker="Athena·智慧女神",
            role=ParticipantRole.ATHENA,
            content="""作为智慧女神，我从更高的视角审视这场辩论：

**共识与分歧**

共识点：
- 双方都认可重力自流是常规技术
- 双方都理解定容计量的基本原理
- 双方都认同说明书需要充分公开

分歧点：
- 审查员认为需要更多技术细节
- 申请人认为已经充分公开

**我的观点**

专利法第26条第3款的核心要求是"所属技术领域的技术人员能够实现"。这意味着：
1. 不需要说明所有可能的参数组合
2. 本领域的公知常识可以依赖
3. 实用新型保护的是结构和构造，不是参数优化

申请人的答复已经清楚说明了：
- 技术方案的结构组成
- 各部件的连接关系
- 工作原理和操作流程

本领域技术人员完全可以根据这些信息实现该实用新型。

**建议**
我建议审查员从整体技术方案的角度理解本申请，而不是纠结于个别参数的详细说明。""",
            legal_basis=["专利法精神", "促进创新原则"],
            evidence=["整体技术分析"],
            confidence=0.9
        )

        self.rounds.append(DebateRound(
            round_num=1,
            examiner_opinion=examiner_opinion_1,
            xiaona_argument=xiaona_arg_1,
            athena_argument=athena_arg_1
        ))

        logger.info("🔴 审查员立场: 部分反对")
        logger.info("   置信度: 0.60")
        logger.info("   关键疑虑 (4个):")
        for c in examiner_opinion_1.key_concerns[:3]:
            logger.info(f"     - {c}")

        await asyncio.sleep(2)

        # 第2轮
        logger.info("\n" + "="*60)
        logger.info("第2轮辩论")
        logger.info("="*60)

        # 审查员回应
        examiner_opinion_2 = ExaminerOpinion(
            stance=ExaminerStance.LEAN_ACCEPT,
            reasoning="""感谢申请人的详细说明。经过进一步考虑，我认可申请人的以下观点：

1. 关于充分公开的标准：专利法确实不要求说明书中列出所有可能的参数，这符合审查指南的要求。

2. 关于公知常识的依赖：Z形杆、定容计量等确实属于本领域的公知常识，可以依赖技术人员的知识。

3. 关于整体技术方案：从整体来看，本申请的技术方案是完整的，工作原理是清晰的。

但仍有一个小疑虑：说明书中提到"防止装药过多或过少"，但没有说明如何精确控制灌装量。不过，考虑到这是实用新型，保护的是结构，我认为可以接受。

总体而言，我倾向于接受本申请。""",
            key_concerns=[
                "如何精确控制灌装量"
            ],
            requested_clarifications=[
                "可考虑在从属权利要求中进一步限定尺寸范围（可选）"
            ],
            confidence=0.75
        )

        xiaona_arg_2 = DebateArgument(
            speaker="小娜·天秤女神",
            role=ParticipantRole.XIAONA,
            content="""非常感谢审查员的理解和认可！

关于灌装量控制的问题，我进一步说明：

**灌装量控制机制**
1. **定量原理**：一号圆孔和二号圆孔重叠形成的计量腔具有固定容积
2. **单次控制**：每次关闭弧形盖，恰好释放一计量腔的药物
3. **防重复**：弹簧复位确保抽板封堵圆孔，防止重复灌装

**精度保证**
- 圆孔加工精度可控制在±0.1mm以内
- 对于颗粒药品，容许一定的误差范围
- 这是本领域的常规做法

**案例支持**
参考我方之前成功的案例202423012016.2（电梯门间隙测量），也是基于类似的技术公开程度获得授权。

再次感谢审查员的细致审查！""",
            legal_basis=["专利法第26条第3款"],
            evidence=["案例202423012016.2"],
            confidence=0.95
        )

        athena_arg_2 = DebateArgument(
            speaker="Athena·智慧女神",
            role=ParticipantRole.ATHENA,
            content="""令人欣慰的是，双方正在达成共识！

**共识达成**

审查员已经认可：
1. 说明书满足充分公开要求
2. 可以依赖本领域的公知常识
3. 技术方案整体完整
4. 倾向于授予专利权

**Athena的总结**

这场辩论展现了专利审查的本质：
- 审查员履行职责，确保充分公开
- 代理人据理力争，维护申请人权益
- 双方通过理性沟通，达成正确结论

本申请的技术方案是：
✅ 结构清晰
✅ 原理明确
✅ 能够实施
✅ 符合专利法要求

**建议**

基于双方已达成的共识，建议审查员：
1. 认可本申请符合专利法第26条第3款
2. 继续其他审查条款的审查
3. 尽早授予专利权

感谢各方的专业与理性！""",
            legal_basis=["专利法精神"],
            evidence=["完整辩论记录"],
            confidence=1.0
        )

        self.rounds.append(DebateRound(
            round_num=2,
            examiner_opinion=examiner_opinion_2,
            xiaona_argument=xiaona_arg_2,
            athena_argument=athena_arg_2
        ))

        logger.info("🟢 审查员立场: 倾向同意")
        logger.info("   置信度: 0.75")
        logger.info("   关键疑虑 (1个):")
        for c in examiner_opinion_2.key_concerns:
            logger.info(f"     - {c}")

        logger.info("\n" + "="*60)
        logger.info("✅ 第2轮达成共识！")
        logger.info("="*60)

        # 生成结果
        summary = """## 辩论摘要

**辩论轮次**: 2轮
**初始立场**: 部分反对
**最终立场**: 倾向同意
**共识状态**: ✅ 已达成共识

**立场演变**:
  第1轮: 部分反对 → 倾向同意
  第2轮: 倾向同意（达成共识）

**主要论点**:
  第1轮小娜: 强调公知常识可以依赖，专利法不要求穷举参数
  第1轮Athena: 从整体技术方案角度理解充分公开要求
  第2轮小娜: 进一步说明灌装量控制机制和精度保证
  第2轮Athena: 总结共识，建议授予专利权

**结论**: 经过2轮专业辩论，审查员认可了申请人的答复，认为本申请满足专利法第26条第3款的要求。"""

        result = DebateResult(
            total_rounds=2,
            final_stance=ExaminerStance.LEAN_ACCEPT,
            consensus_reached=True,
            summary=summary,
            rounds=self.rounds,
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat()
        )

        self._save_result(result)

        return result

    def _save_result(self, result: DebateResult):
        """保存辩论结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"patent_debate_demo_{timestamp}.json"
        filepath = Path(self.save_path) / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"💾 辩论结果已保存: {filepath}")


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("🎬 专利审查辩论系统启动 - 演示模式")
    logger.info("="*60)

    logger.info("\n⚠️  注意：这是演示模式，使用预设的模拟响应")
    logger.info("   实际使用需要配置DeepSeek API密钥")

    logger.info("\n📋 辩论主题：")
    logger.info("   申请号：202520560089.0")
    logger.info("   发明名称：一种药品生产灌装机")
    logger.info("   审查员：肖玉林")
    logger.info("   争议焦点：专利法第26条第3款 - 说明书充分公开")

    logger.info("\n👥 辩论参与者：")
    logger.info("   🔴 审查员肖玉林 - 代表专利局，提出质疑")
    logger.info("   🟢 小娜·天秤女神 - 专利法律专家，申请人代理律师")
    logger.info("   🏛️ Athena·智慧女神 - 系统协调者，促进共识")

    logger.info("\n" + "="*60)

    try:
        # 创建演示协调器
        coordinator = DemoDebateCoordinator(
            save_path="/Users/xujian/Athena工作平台/logs/debate_results",
        )

        # 进行辩论
        result = await coordinator.conduct_debate(
            office_action="",
            patent_response="",
            patent_content="",
        )

        # 显示结果
        logger.info("\n" + "="*60)
        logger.info("🏁 辩论结束")
        logger.info("="*60)

        logger.info("\n📊 辩论结果：")
        logger.info(f"   辩论轮次：{result.total_rounds}轮")
        logger.info("   最终立场：🟢 倾向同意")
        logger.info("   共识状态：✅ 已达成共识")

        logger.info("\n📝 辩论摘要：")
        logger.info(result.summary)

        logger.info("\n✅ 演示模式运行完成！")
        logger.info("💾 详细结果已保存到: /Users/xujian/Athena工作平台/logs/debate_results/")

        # 生成Markdown报告
        md_filename = f"patent_debate_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        md_filepath = Path("/Users/xujian/Athena工作平台/logs/debate_results") / md_filename

        md_content = f"""# 专利审查辩论报告（演示模式）

**辩论时间**: {result.start_time}
**辩论轮次**: {result.total_rounds}
**最终立场**: 倾向同意
**共识状态**: ✅ 已达成共识

---

{result.summary}

---

## 详细记录

### 第1轮

**审查员立场**: 部分反对

**审查员理由**:
{result.rounds[0].examiner_opinion.reasoning}

**关键疑虑**:
{chr(10).join(f"- {c}" for c in result.rounds[0].examiner_opinion.key_concerns)}

**小娜·天秤女神论点**:
{result.rounds[0].xiaona_argument.content}

**Athena·智慧女神论点**:
{result.rounds[0].athena_argument.content}

---

### 第2轮

**审查员立场**: 倾向同意

**审查员理由**:
{result.rounds[1].examiner_opinion.reasoning}

**小娜·天秤女神论点**:
{result.rounds[1].xiaona_argument.content}

**Athena·智慧女神论点**:
{result.rounds[1].athena_argument.content}

---

## 结论

经过2轮专业辩论，审查员认可了申请人的答复：
- 认可公知常识的依赖
- 认可技术方案的整体性
- 倾向于授予专利权

本申请满足专利法第26条第3款的要求。

---

*注：本报告使用演示模式生成，实际使用需要配置DeepSeek API密钥*
"""

        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"📄 Markdown报告已保存: {md_filepath}")

        return result

    except Exception as e:
        logger.error(f"❌ 辩论过程出错: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result and result.consensus_reached else 1)
