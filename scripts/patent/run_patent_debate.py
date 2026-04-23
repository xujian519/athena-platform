#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利审查辩论主程序
Patent Debate Main Script

启动审查员、小娜、Athena三方辩论

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-02-09
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.debate.debate_coordinator import DebateCoordinator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


# 审查意见（审查员肖玉林）
OFFICE_ACTION = """审查员认为本申请的说明书没有清楚完整地解释和说明"灌装、计量、称重"的技术手段，不清楚如何用于药品灌装的，对所属技术领域的技术人员来说，该手段是含糊不清的，根据说明书记载的内容无法具体实施，因此不符合专利法第26条第3款的规定。"""


# 申请人的答复
PATENT_RESPONSE = """# 第一次审查意见答复

申请人：山东圣旺药业股份有限公司
申请号：202520560089.0
发明创造名称：一种药品生产灌装机
审查员：肖玉林

## 一、答复意见

本申请的说明书已经对技术方案作出了清楚、完整的说明，所属技术领域的技术人员能够根据说明书实现本实用新型，完全符合专利法第26条第3款的规定。

### （一）关于专利法第26条第3款的说明

审查员认为说明书没有清楚完整地解释"灌装、计量、称重"的技术手段。这一观点需要澄清。

### 1. 关于"灌装"技术手段

本申请采用重力自流式灌装，这是颗粒物料灌装的常规技术手段。

**灌装原理**：
关闭弧形盖 → Z形杆带动抽板移动 → 一号圆孔与二号圆孔重叠 → 药物颗粒在重力作用下掉落 → 药瓶被灌装 → 打开弧形盖 → 弹簧复位 → 抽板封堵圆孔 → 灌装停止

**技术特点**：
- 控制方式：通过弧形盖的开关控制灌装的开始和停止
- 驱动机制：Z形杆将弧形盖的旋转运动转换为抽板的直线运动
- 密封保证：抽板与中空板的配合实现可靠的启闭
- 动力来源：重力驱动，药物颗粒自然掉落

### 2. 关于"计量"技术手段

本申请采用"定容计量法"，这是颗粒物料计量的常用方法。

**计量原理**：
- 固定容量：中空板的一号圆孔（610）和抽板的二号圆孔（611）形成固定容量的计量腔
- 精确控制：圆孔的直径和深度决定了每次灌装的药物颗粒量
- 单次计量：每次关闭弧形盖，圆孔重叠形成一个完整的计量单元

### 3. 关于"称重"技术手段

审查员认为没有说明"称重"的技术手段。实际上，本申请不需要称重设备。

本申请采用容量计量而非重量计量：
- 本申请是实用新型专利，保护的是产品的形状、构造或其结合
- 本申请采用固定容量计量而非重量计量
- 对于颗粒状药品，在一定密度范围内，容量与重量成正比关系
- 定容计量是简单可靠的计量方式，适用于颗粒物料

### 4. 关于"如何用于药品灌装"

说明书第[0020]段明确记载了工作原理，完整说明了药品灌装的流程：

**步骤1：准备工作**
通过进料口12倒入药物颗粒到储药仓61内部，把药瓶放置到固定盘10的顶部

**步骤2：开始灌装**
通过把手4关闭弧形盖3，弧形盖3带动Z形杆69、横板68、抽板67移动
一号圆孔610与二号圆孔611重叠，药物颗粒掉落到药瓶中

**步骤3：停止灌装**
打开弧形盖3，弹簧66带动抽板67复位，圆孔被封闭，灌装停止

## 二、结论

本申请的说明书已经对技术方案作出了清楚、完整的说明：
1. 结构清楚：各部件的结构、连接关系、配合关系清楚
2. 工作原理明确：详细说明了操作流程和工作机理
3. 技术手段完整：灌装、计量（定容计量）的技术手段已经说明
4. 能够实施：本领域技术人员可以根据说明书实现本实用新型

审查员关于"灌装、计量、称重"技术手段不清楚的异议，是对本申请技术方案的误解。本申请采用固定容量灌装这一本领域的常规技术手段，无需额外的称重设备即可实现灌装功能。

本申请完全符合专利法第26条第3款的规定，恳请审查员重新考虑并授予专利权。"""


# 专利申请内容摘要
PATENT_CONTENT = """
【发明名称】
一种药品生产灌装机

【技术领域】
本实用新型涉及灌装技术领域，具体为一种药品生产灌装机。

【背景技术】
现有的药品灌装机在灌装过程中容易出现装药过多或过少的问题，且药物颗粒容易溢出造成浪费。

【发明内容】
本实用新型提供一种药品生产灌装机，包括主机、储药仓、灌装机构等。

储药仓内部设置有灌装机构，灌装机构包括中空板、抽板、弧形盖、Z形杆和弹簧。

中空板上设有一号圆孔，抽板上设有二号圆孔。关闭弧形盖时，Z形杆带动抽板移动，使一号圆孔与二号圆孔重叠，药物颗粒在重力作用下掉落到药瓶中。

打开弧形盖时，弹簧带动抽板复位，圆孔被封闭，灌装停止。

【有益效果】
1. 防止装药过多或过少
2. 防止药物颗粒浪费
3. 结构简单，操作方便

【具体实施方式】
通过进料口倒入药物颗粒到储药仓内部，把药瓶放置到固定盘的顶部。
通过把手关闭弧形盖，弧形盖带动Z形杆、横板、抽板移动。
一号圆孔与二号圆孔重叠，药物颗粒掉落到药瓶中。
打开弧形盖，弹簧带动抽板复位，圆孔被封闭，灌装停止。
"""


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("🎬 专利审查辩论系统启动")
    logger.info("="*60)

    # 显示辩论主题
    logger.info("\n📋 辩论主题：")
    logger.info("   申请号：202520560089.0")
    logger.info("   发明名称：一种药品生产灌装机")
    logger.info("   审查员：肖玉林")
    logger.info("   争议焦点：专利法第26条第3款 - 说明书充分公开")

    # 显示参与者
    logger.info("\n👥 辩论参与者：")
    logger.info("   🔴 审查员肖玉林 - 代表专利局，提出质疑")
    logger.info("   🟢 小娜·天秤女神 - 专利法律专家，申请人代理律师")
    logger.info("   🏛️ Athena·智慧女神 - 系统协调者，促进共识")

    logger.info("\n" + "="*60)

    try:
        # 创建辩论协调器
        coordinator = DebateCoordinator(
            max_rounds=5,
            save_path="/Users/xujian/Athena工作平台/logs/debate_results",
        )

        # 进行辩论
        result = await coordinator.conduct_debate(
            office_action=OFFICE_ACTION,
            patent_response=PATENT_RESPONSE,
            patent_content=PATENT_CONTENT,
        )

        # 显示结果
        logger.info("\n" + "="*60)
        logger.info("🏁 辩论结束")
        logger.info("="*60)

        stance_emoji = {
            "fully_reject": "🔴 完全反对",
            "partial_reject": "🟠 部分反对",
            "neutral": "🟡 中立",
            "lean_accept": "🟢 倾向同意",
            "fully_accept": "✅ 完全同意",
        }

        final_stance_text = stance_emoji.get(result.final_stance, result.final_stance)

        logger.info(f"\n📊 辩论结果：")
        logger.info(f"   辩论轮次：{result.total_rounds}轮")
        logger.info(f"   最终立场：{final_stance_text}")
        logger.info(f"   共识状态：{'✅ 已达成共识' if result.consensus_reached else '❌ 未达成共识'}")

        logger.info(f"\n📝 辩论摘要：")
        logger.info(result.summary)

        # 关闭协调器
        await coordinator.close()

        logger.info("\n✅ 辩论系统运行完成！")
        logger.info(f"💾 详细结果已保存到: /Users/xujian/Athena工作平台/logs/debate_results/")

        return result

    except Exception as e:
        logger.error(f"❌ 辩论过程出错: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 运行主程序
    result = asyncio.run(main())

    # 退出
    sys.exit(0 if result and result.consensus_reached else 1)
