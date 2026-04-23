#!/usr/bin/env python3
"""
专利无效宣告辩论系统

功能：
1. 创建两个智能体：无效请求人代理（济南力邦）和被请求人代理（广东冠一）
2. 围绕专利201921401279.9的无效宣告进行至少5轮辩论
3. 使用真实的LLM和法条画像

作者：Athena平台
日期：2026-04-23
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 设置路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 避免导入有问题的模块，直接使用简单的LLM调用
try:
    from openai import AsyncOpenAI
except ImportError:
    print("错误：需要安装openai库")
    print("请运行：pip install openai")
    sys.exit(1)

# 从.env文件读取API密钥
def load_api_key():
    """从.env文件加载Anthropic API密钥"""
    env_file = Path("/Users/xujian/Athena工作平台/.env")
    if env_file.exists():
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('anthropic_api_key='):
                    return line.split('=', 1)[1].strip()
    # 如果.env文件中没有，尝试从环境变量读取
    return os.environ.get("ANTHROPIC_API_KEY", "")


class PatentDebateAgent:
    """专利辩论代理基类"""

    def __init__(self, name: str, role: str, client: AsyncOpenAI, system_prompt: str, model: str = "claude-sonnet-4-20250514"):
        self.name = name
        self.role = role  # "invalidation_requester" 或 "patentee"
        self.client = client
        self.model = model
        self.system_prompt = system_prompt
        self.debate_history: list[dict] = []

    async def generate_response(self, opponent_argument: str, round_num: int) -> str:
        """生成辩论回应"""

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""现在是第{round_num}轮辩论。

对方刚才的观点：
{opponent_argument}

请根据你的角色立场，针对对方的观点进行反驳，并进一步阐述你的法律依据。
要求：
1. 必须引用具体的法条和审查指南条款
2. 必须引用具体的对比文件（D1、D2、E1）和段落号
3. 必须使用专业的专利律师语言
4. 必须指出对方论证中的法律逻辑错误
5. 长度：500-800字
"""}
        ]

        try:
            # 调用LLM（使用Anthropic API）
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                messages=messages
            )

            content = response.content[0].text

            # 记录历史
            self.debate_history.append({
                "round": round_num,
                "role": self.role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })

            return content

        except Exception as e:
            return f"[生成回应失败]: {str(e)}"


class InvalidationRequesterAgent(PatentDebateAgent):
    """无效请求人代理（济南力邦方）"""

    @classmethod
    def create(cls, client: AsyncOpenAI) -> 'InvalidationRequesterAgent':
        system_prompt = """你是济南力邦（无效请求人）的专利律师，正在对专利201921401279.9（广东冠一机械科技有限公司）提出无效宣告请求。

你的核心观点：
1. 权利要求1-10均不具备创造性，违反专利法第22条第3款
2. 最接近的现有技术是D1（CN208647230U）
3. D1公开了机架、物料限位板、物料传送带安装空间、调节机构存在、驱动机构存在这5个基本特征
4. D1未公开：纵向调节单元42、斜向调节单元43、两条斜向滑轨432的间距从左往右逐渐缩短
5. D2（CN201198403Y）教导了"斜向导向→间距变化"的技术原理
6. E1（CN206156248U）确认了包装机械中宽度调节是常规技术需求
7. 伞齿轮传动、螺杆螺母、手轮、皮带传动、伺服电机等都是公知常识
8. 斜楔机构原理是几何学必然，无需创造性劳动

你的辩论策略：
1. 强调三步法的正确适用
2. 强调D2的技术教导具有普遍适用性
3. 强调斜向滑轨间距逐渐缩短是几何学必然
4. 指出对方陷入"事后诸葛亮"误区
5. 指出对方混淆了"结构差异"与"创造性高度"

法律依据：
- 专利法第22条第3款（创造性定义）
- 审查指南第二部分第四章§3.2（三步法）
- 审查指南第二部分第四章§3.2.1（技术启示判断）
- 审查指南第二部分第四章§6.2（避免事后诸葛亮）

语言风格：专业、理性、攻击性强但基于法律"""

        return cls("济南力邦代理律师", "invalidation_requester", client, system_prompt)


class PatenteeAgent(PatentDebateAgent):
    """被请求人代理（广东冠一方）"""

    @classmethod
    def create(cls, client: AsyncOpenAI) -> 'PatenteeAgent':
        system_prompt = """你是广东冠一机械科技有限公司（专利权人）的专利律师，正在为专利201921401279.9进行有效辩护。

你的核心观点：
1. 权利要求1-10具备创造性，符合专利法第22条第3款
2. 目标专利与D1存在根本性结构差异，不是简单改进
3. D1的"物料限位板横向间距调节机构"与目标专利的"纵向+斜向同步调节"是不同技术路线
4. D2应用于瓶坯机械手领域（夹紧固定），与包装机传送（动态调节）技术问题不同
5. D2说明书未明确使用"逐渐变化"术语，间距变化隐含于结构设计中
6. "两条斜向滑轨432的间距从左往右逐渐缩短"是目标专利的核心创新点
7. 目标专利解决了"纵向和斜向方向同步精确调节"的技术难题
8. 目标专利实现了"一驱三调"（一个驱动单元同时驱动纵向和斜向调节）的创新结构
9. 请求人陷入"事后诸葛亮"误区，用目标专利反推D1、D2存在技术启示
10. D1、D2、E1均未教导"间距逐渐缩短"的具体设置方式

你的辩论策略：
1. 强调技术领域的差异（包装机传送 vs 瓶坯机械手）
2. 强调技术问题的差异（动态调节 vs 夹紧固定）
3. 强调技术手段的差异（纵向+斜向同步 vs 单向调节）
4. 强调技术效果的差异（间距逐渐缩短 vs 等间距调节）
5. 指出D2未明确教导"间距逐渐缩短"
6. 指出对方存在"事后诸葛亮"错误
7. 强调目标专利的结构创新性和技术进步性

法律依据：
- 专利法第22条第3款（创造性定义）
- 审查指南第二部分第四章§3.2.1（技术启示判断）
- 审查指南第二部分第四章§6.2（避免事后诸葛亮）
- (2020)最高法知行终185号（反向教导判例）
- (2019)最高法行再268号（反向教导认定标准）

语言风格：专业、坚定、防御性强但基于技术事实"""

        return cls("广东冠一代理律师", "patentee", client, system_prompt)


class PatentDebateManager:
    """专利辩论管理器"""

    def __init__(self):
        # 从.env文件加载API密钥
        api_key = load_api_key()
        if not api_key:
            raise ValueError("无法从.env文件或环境变量中找到ANTHROPIC_API_KEY")

        # 初始化OpenAI客户端（使用Anthropic API）
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.anthropic.com"
        )

        self.requester_agent = InvalidationRequesterAgent.create(self.client)
        self.patentee_agent = PatenteeAgent.create(self.client)
        self.debate_log: list[dict] = []

    async def conduct_debate(self, rounds: int = 5) -> dict:
        """进行多轮辩论"""

        print(f"\n{'='*80}")
        print("专利无效宣告辩论开始")
        print("专利号：201921401279.9")
        print("专利名称：包装机物品传送装置的物料限位板自动调节机构")
        print(f"辩论轮次：{rounds}轮")
        print(f"{'='*80}\n")

        # 第一轮：请求人开场陈述
        print("\n" + "="*80)
        print("【第1轮】无效请求人开场陈述")
        print("="*80)

        opening_statement = await self.requester_agent.generate_response(
            opponent_argument="（这是开场陈述，请阐述你方的主要无效理由）",
            round_num=1
        )

        print(opening_statement)
        self.debate_log.append({
            "round": 1,
            "speaker": "济南力邦（无效请求人）",
            "content": opening_statement
        })

        # 第2-2*rounds轮：交替辩论
        for i in range(2, 2 * rounds + 1):
            if i % 2 == 0:  # 偶数轮：被请求人回应
                print("\n" + "="*80)
                print(f"【第{i}轮】被请求人（广东冠一）回应")
                print("="*80)

                last_argument = self.requester_agent.debate_history[-1]["content"]
                response = await self.patentee_agent.generate_response(
                    opponent_argument=last_argument,
                    round_num=i
                )

                print(response)
                self.debate_log.append({
                    "round": i,
                    "speaker": "广东冠一（专利权人）",
                    "content": response
                })

            else:  # 奇数轮：请求人反驳
                print("\n" + "="*80)
                print(f"【第{i}轮】无效请求人（济南力邦）反驳")
                print("="*80)

                last_argument = self.patentee_agent.debate_history[-1]["content"]
                response = await self.requester_agent.generate_response(
                    opponent_argument=last_argument,
                    round_num=i
                )

                print(response)
                self.debate_log.append({
                    "round": i,
                    "speaker": "济南力邦（无效请求人）",
                    "content": response
                })

        # 保存辩论记录
        self.save_debate_log()

        return {
            "total_rounds": rounds,
            "requester_arguments": len(self.requester_agent.debate_history),
            "patentee_arguments": len(self.patentee_agent.debate_history),
            "debate_log": self.debate_log
        }

    def save_debate_log(self):
        """保存辩论记录到文件"""

        output_dir = Path("/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9无效材料/补充证据和理由2026.4.22")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存JSON格式
        json_file = output_dir / f"专利无效宣告辩论记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.debate_log, f, ensure_ascii=False, indent=2)

        # 保存Markdown格式
        md_file = output_dir / f"专利无效宣告辩论记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# 专利无效宣告辩论记录\n\n")
            f.write("**专利号**：201921401279.9\n")
            f.write("**专利名称**：包装机物品传送装置的物料限位板自动调节机构\n")
            f.write(f"**辩论时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**辩论轮次**：{len(self.debate_log)}轮\n\n")
            f.write("---\n\n")

            for entry in self.debate_log:
                f.write(f"## 【第{entry['round']}轮】{entry['speaker']}\n\n")
                f.write(f"{entry['content']}\n\n")
                f.write("---\n\n")

        print("\n辩论记录已保存：")
        print(f"- JSON格式：{json_file}")
        print(f"- Markdown格式：{md_file}")


async def main():
    """主函数"""

    print("\n🏛️  专利无效宣告辩论系统启动")
    print("=" * 80)

    # 创建辩论管理器
    manager = PatentDebateManager()

    # 进行5轮辩论
    result = await manager.conduct_debate(rounds=5)

    print("\n" + "=" * 80)
    print("🎊 辩论完成！")
    print("=" * 80)
    print(f"总轮次：{result['total_rounds']}")
    print(f"请求人发言次数：{result['requester_arguments']}")
    print(f"被请求人发言次数：{result['patentee_arguments']}")


if __name__ == "__main__":
    asyncio.run(main())
