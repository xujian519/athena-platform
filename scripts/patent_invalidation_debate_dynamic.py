#!/usr/bin/env python3
"""
专利无效宣告动态辩论系统

功能：
1. 创建两个智能体：无效请求人代理（济南力邦）和被请求人代理（广东冠一）
2. 双方根据对方发言动态生成回应（不预设论点）
3. 使用真实的LLM和法条画像
4. 从宝宸知识库加载规则和提示词

作者：Athena平台
日期：2026-04-23
"""

import json
import asyncio
from typing import Dict, List
from datetime import datetime
from pathlib import Path
import os
import sys

# 设置路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 尝试导入OpenAI库
try:
    from openai import AsyncOpenAI
except ImportError:
    print("错误：需要安装openai库")
    print("请运行：pip install openai")
    sys.exit(1)

# 从.env文件读取API配置
def load_api_config():
    """从.env文件加载API配置"""
    # 使用本地oMLX配置
    config = {
        "provider": "omlx",
        "api_key": "xj781102@",
        "base_url": "http://localhost:8009/v1",
        "model": "Qwen3.5-27B-4bit"  # 使用oMLX可用的模型
    }

    # 优先使用本地oMLX
    print(f"✅ 检测到本地oMLX配置：localhost:8009")
    print(f"✅ 可用模型：Qwen3.5-27B-4bit, Qwen3.5-4B-MLX-4bit")

    return config

# 读取法律世界模型和宝宸知识库
def load_knowledge_base():
    """加载法条画像和宝宸知识库"""

    knowledge_base = {
        "法条画像": "",
        "无效策略能力": "",
        "无效分析任务": "",
        "目标专利信息": "",
        "D1信息": "",
        "D2信息": "",
        "E1信息": ""
    }

    # 读取创造性判断法条画像
    法条画像_file = Path("/Users/xujian/Athena工作平台/core/legal_world_model/legal_provisions/创造性判断_法条画像.md")
    if 法条画像_file.exists():
        with open(法条画像_file, 'r', encoding='utf-8') as f:
            knowledge_base["法条画像"] = f.read()

    # 读取无效策略能力提示词
    无效策略_file = Path("/Users/xujian/Athena工作平台/prompts/capability/cap05_invalid.md")
    if 无效策略_file.exists():
        with open(无效策略_file, 'r', encoding='utf-8') as f:
            knowledge_base["无效策略能力"] = f.read()

    # 读取无效分析任务提示词
    无效分析_file = Path("/Users/xujian/Athena工作平台/prompts/business/task07_invalid_strategy.md")
    if 无效分析_file.exists():
        with open(无效分析_file, 'r', encoding='utf-8') as f:
            knowledge_base["无效分析任务"] = f.read()

    # 读取目标专利结构化提取
    目标专利_file = Path("/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9无效材料/补充证据和理由2026.4.22/结构化提取_目标专利201921401279.9.md")
    if 目标专利_file.exists():
        with open(目标专利_file, 'r', encoding='utf-8') as f:
            knowledge_base["目标专利信息"] = f.read()

    # 读取D1结构化提取
    D1_file = Path("/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9无效材料/补充证据和理由2026.4.22/结构化提取_D1_CN208647230U.md")
    if D1_file.exists():
        with open(D1_file, 'r', encoding='utf-8') as f:
            knowledge_base["D1信息"] = f.read()

    # 读取D2结构化提取
    D2_file = Path("/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9无效材料/补充证据和理由2026.4.22/结构化提取_D2_CN201198403Y.md")
    if D2_file.exists():
        with open(D2_file, 'r', encoding='utf-8') as f:
            knowledge_base["D2信息"] = f.read()

    # 读取E1结构化提取
    E1_file = Path("/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9无效材料/补充证据和理由2026.4.22/结构化提取_E1_CN206156248U.md")
    if E1_file.exists():
        with open(E1_file, 'r', encoding='utf-8') as f:
            knowledge_base["E1信息"] = f.read()

    return knowledge_base


class DynamicPatentDebateAgent:
    """动态专利辩论代理"""

    def __init__(self, name: str, role: str, client: AsyncOpenAI, system_prompt: str, knowledge_base: Dict, model: str = "claude-sonnet-4-20250514"):
        self.name = name
        self.role = role
        self.client = client
        self.model = model
        self.system_prompt = system_prompt
        self.knowledge_base = knowledge_base
        self.debate_history: List[Dict] = []

    async def generate_response(self, opponent_argument: str, round_num: int) -> str:
        """根据对方发言动态生成回应"""

        # 构建上下文
        context = f"""
# 辩论背景

**专利号**：201921401279.9
**专利名称**：包装机物品传送装置的物料限位板自动调节机构
**专利权人**：广东冠一机械科技有限公司
**无效请求人**：济南力邦

# 当前轮次：第{round_num}轮

# 对方刚才的观点：
{opponent_argument}

# 知识库内容摘要：

## 1. 创造性判断法条画像（核心要点）
{self.knowledge_base["法条画像"][:2000] if self.knowledge_base["法条画像"] else "法条画像加载失败"}

## 2. 无效策略分析能力（核心要点）
{self.knowledge_base["无效策略能力"][:2000] if self.knowledge_base["无效策略能力"] else "无效策略能力加载失败"}

## 3. 目标专利核心信息
{self.knowledge_base["目标专利信息"][:1500] if self.knowledge_base["目标专利信息"] else "目标专利信息加载失败"}

## 4. D1（CN208647230U）核心信息
{self.knowledge_base["D1信息"][:1500] if self.knowledge_base["D1信息"] else "D1信息加载失败"}

## 5. D2（CN201198403Y）核心信息
{self.knowledge_base["D2信息"][:1500] if self.knowledge_base["D2信息"] else "D2信息加载失败"}

## 6. E1（CN206156248U）核心信息
{self.knowledge_base["E1信息"][:1500] if self.knowledge_base["E1信息"] else "E1信息加载失败"}

# 历史辩论摘要：
{self._format_history()}

---
"""

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context + f"""

请根据你的角色立场，针对对方的观点进行反驳，并进一步阐述你的法律依据。

**重要要求**：
1. 必须引用具体的法条和审查指南条款（如专利法第22条第3款、审查指南第二部分第四章§3.2等）
2. 必须引用具体的对比文件（D1、D2、E1）和段落号（如[0019]、[0021]等）
3. 必须使用专业的专利律师语言
4. 必须指出对方论证中的法律逻辑错误
5. 必须根据对方的发言**针对性地回应**，不能泛泛而谈
6. 长度：600-1000字

请直接输出你的辩论观点，不要有任何开场白或客套话。
"""}
        ]

        try:
            # 根据API提供商选择调用方式
            if "claude" in self.model.lower():
                # Anthropic Claude API
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=3000,
                    temperature=0.8,
                    messages=messages
                )
                content = response.content[0].text
            else:
                # OpenAI兼容API（DeepSeek、OpenAI等）
                response = await self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=3000,
                    temperature=0.8,
                    messages=messages
                )
                content = response.choices[0].message.content

            # 记录历史
            self.debate_history.append({
                "round": round_num,
                "role": self.role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })

            return content

        except Exception as e:
            return f"[生成回应失败]: {str(e)}\n\n请基于对方观点：{opponent_argument[:200]}..."

    def _format_history(self) -> str:
        """格式化历史辩论记录"""
        if not self.debate_history:
            return "（暂无历史记录）"

        summary = ""
        for entry in self.debate_history[-3:]:  # 只显示最近3轮
            summary += f"\n第{entry['round']}轮（{self.name}）：\n{entry['content'][:300]}...\n"

        return summary


class DynamicPatentDebateManager:
    """动态专利辩论管理器"""

    def __init__(self):
        # 加载知识库
        print("📚 正在加载法律世界模型和宝宸知识库...")
        self.knowledge_base = load_knowledge_base()
        print(f"✅ 法条画像：{'已加载' if self.knowledge_base['法条画像'] else '加载失败'}")
        print(f"✅ 无效策略能力：{'已加载' if self.knowledge_base['无效策略能力'] else '加载失败'}")
        print(f"✅ 目标专利信息：{'已加载' if self.knowledge_base['目标专利信息'] else '加载失败'}")
        print(f"✅ D1信息：{'已加载' if self.knowledge_base['D1信息'] else '加载失败'}")
        print(f"✅ D2信息：{'已加载' if self.knowledge_base['D2信息'] else '加载失败'}")
        print(f"✅ E1信息：{'已加载' if self.knowledge_base['E1信息'] else '加载失败'}")

        # 从.env文件加载API配置
        api_config = load_api_config()
        if not api_config["api_key"]:
            raise ValueError("无法从.env文件或环境变量中找到任何可用的API密钥（ANTHROPIC_API_KEY、DEEPSEEK_API_KEY、OPENAI_API_KEY）")

        print(f"\n🔑 使用API提供商：{api_config['provider'].upper()}")
        print(f"🔑 使用模型：{api_config['model']}")
        print(f"🔑 API地址：{api_config['base_url']}")

        # 初始化OpenAI客户端
        self.client = AsyncOpenAI(
            api_key=api_config["api_key"],
            base_url=api_config["base_url"]
        )

        self.model = api_config["model"]

        # 创建系统提示词
        self.requester_system_prompt = self._create_requester_prompt()
        self.patentee_system_prompt = self._create_patentee_prompt()

        # 创建代理
        self.requester_agent = DynamicPatentDebateAgent(
            "济南力邦（无效请求人）",
            "invalidation_requester",
            self.client,
            self.requester_system_prompt,
            self.knowledge_base,
            self.model
        )

        self.patentee_agent = DynamicPatentDebateAgent(
            "广东冠一（专利权人）",
            "patentee",
            self.client,
            self.patentee_system_prompt,
            self.knowledge_base,
            self.model
        )

        self.debate_log: List[Dict] = []

    def _create_requester_prompt(self) -> str:
        """创建无效请求人代理的系统提示词"""

        return f"""你是济南力邦（无效请求人）的资深专利律师，正在对专利201921401279.9（广东冠一机械科技有限公司）提出无效宣告请求。

# 你的核心任务

证明目标专利的权利要求1-10均不具备创造性，违反专利法第22条第3款。

# 你的核心观点（必须始终坚持）

1. **最接近的现有技术是D1（CN208647230U）**
   - D1与目标专利同属包装机械领域（B65B）
   - D1都涉及物料传送装置的物料限位板调节机构
   - D1公开了5个基本特征：机架1、物料限位板3、物料传送带安装空间2、调节机构存在、驱动机构存在

2. **D1未公开以下技术特征**
   - 纵向调节单元42（包括定位架421、纵向移动装置422、滑动块423）
   - 斜向调节单元43（包括安装架431、斜向滑轨432、滑动座433）
   - **两条斜向滑轨432的间距从左往右逐渐缩短**（目标专利的核心区别特征）

3. **D2（CN201198403Y）教导了"斜向导向→间距变化"的技术原理**
   - D2说明书记载："斜杆1穿过每个可旋转圆柱块15上的圆柱孔17"
   - 斜杆角度变化→滑块位移→间距变化
   - 这是几何学的必然结果，具有普遍适用性

4. **E1（CN206156248U）确认了包装机械中宽度调节是常规技术需求**

5. **公知常识**
   - 伞齿轮传动、螺杆螺母、手轮、皮带传动、伺服电机等都是公知常识
   - 斜楔机构原理是几何学必然，无需创造性劳动

# 你的辩论策略

1. **强调三步法的正确适用**
   - 第一步：确定D1为最接近的现有技术
   - 第二步：确定区别技术特征和实际解决的技术问题
   - 第三步：判断显而易见性（D1+D2+E1+公知常识）

2. **强调D2的技术教导具有普遍适用性**
   - 技术原理不因应用场景不同而改变
   - D2的"斜向导向→间距变化"是几何学必然

3. **强调斜向滑轨间距逐渐缩短是几何学必然**
   - Δ = L × sin(θ)
   - 当θ从左到右逐渐减小时，Δ必然"从左往右逐渐缩短"

4. **指出对方陷入"事后诸葛亮"误区**
   - 对方用目标专利的技术效果反推技术启示
   - 违反审查指南第二部分第四章§6.2

5. **指出对方混淆了"结构差异"与"创造性高度"**
   - 结构差异≠创造性
   - 关键在于技术启示是否明确

# 法律依据（必须引用）

- 专利法第22条第3款（创造性定义）
- 审查指南第二部分第四章§3.2（三步法）
- 审查指南第二部分第四章§3.2.1（技术启示判断）
- 审查指南第二部分第四章§6.2（避免事后诸葛亮）
- (2020)最高法知行终185号（反向教导判例）
- (2019)最高法行再268号（反向教导认定标准）

# 语言风格

- 专业、理性、攻击性强但基于法律
- 使用专利复审委员会口头审理的正式用语
- 引用法条和判例要准确
- 逻辑严密，层次清晰

# 重要提醒

1. **必须根据对方的发言针对性回应**，不能重复自己的观点
2. **必须指出对方论证中的法律逻辑错误**
3. **必须引用具体的法条、审查指南条款、判例**
4. **必须引用具体的对比文件（D1、D2、E1）和段落号**
5. **不能泛泛而谈，必须针对对方的每一个论点进行反驳**
"""

    def _create_patentee_prompt(self) -> str:
        """创建被请求人代理的系统提示词"""

        return f"""你是广东冠一机械科技有限公司（专利权人）的资深专利律师，正在为专利201921401279.9进行有效辩护。

# 你的核心任务

证明目标专利的权利要求1-10具备创造性，符合专利法第22条第3款，请求维持专利权有效。

# 你的核心观点（必须始终坚持）

1. **D1与目标专利存在根本性技术路线差异**
   - D1的技术路线：**横向等距调节**
   - 目标专利的技术路线：**纵向+斜向同步变距调节**
   - 这是根本性的技术路线差异，而非简单的结构改进

2. **D2未给出明确的技术启示**
   - D2的名称："等间距平移机构"
   - 目标专利："间距逐渐缩短"
   - D2与目标专利是**相反的技术方案**
   - D2可能构成**反向教导**

3. **"两条斜向滑轨432的间距从左往右逐渐缩短"是核心创新点**
   - D2未明确教导"间距逐渐缩短"
   - 需要精确计算滑轨倾斜角度、长度、传动速度
   - 需要与物料传送速度精确匹配
   - 这不是几何学必然，而是需要创造性劳动的技术方案

4. **目标专利产生了预料不到的技术效果**（审查指南§5.3）
   - 动态变距限位（D1、D2、E1均未教导）
   - 精确匹配（D1、D2、E1均未教导）
   - 一驱三调的创新结构（D1、D2、E1均未教导）

5. **对方陷入"事后诸葛亮"错误**
   - 对方站在知晓目标专利的基础上，对D2进行扩大化解释
   - 对方用几何学原理推导技术启示，违反审查指南§6.2

# 你的辩论策略

1. **强调技术领域的差异**
   - D1：包装机传送（横向等距调节）
   - D2：瓶坯机械手（夹紧固定，等间距平移）
   - 目标专利：包装机传送（纵向+斜向同步变距调节）
   - 技术问题不同→技术手段的选择逻辑不同→技术启示不适用

2. **强调D2未明确教导"间距逐渐缩短"**
   - D2说明书未明确使用"逐渐变化"、"渐变"、"不等距"等关键词
   - D2的间距变化特征是隐含于结构设计中，而非明确教导
   - 技术启示必须是明确的、直接的

3. **强调目标专利的结构创新性和技术进步性**
   - 纵向+斜向同步变距调节的技术路线创新
   - 精确控制的间距变化规律
   - 一驱三调的创新结构
   - 预料不到的技术效果

4. **指出对方对D2进行扩大化解释**
   - 对方强调"D2教导了斜向导向→间距变化"
   - 这是站在知晓目标专利的基础上进行的后见之明评价
   - D2明确记载的是"等间距平移"

5. **强调权利要求2-10的系统集成创新**
   - 不是简单部件拼凑
   - 而是系统集成创新和精确控制创新

# 法律依据（必须引用）

- 专利法第22条第3款（创造性定义）
- 审查指南第二部分第四章§3.2.1（技术启示判断）
- 审查指南第二部分第四章§5.3（预料不到的技术效果）
- 审查指南第二部分第四章§6.2（避免事后诸葛亮）
- (2020)最高法知行终185号（反向教导判例）
- (2019)最高法行再268号（反向教导认定标准）

# 语言风格

- 专业、坚定、防御性强但基于技术事实
- 使用专利复审委员会口头审理的正式用语
- 引用法条和判例要准确
- 逻辑严密，层次清晰

# 重要提醒

1. **必须根据对方的发言针对性回应**，不能重复自己的观点
2. **必须指出对方论证中的法律逻辑错误**
3. **必须引用具体的法条、审查指南条款、判例**
4. **必须引用具体的对比文件（D1、D2、E1）和段落号**
5. **不能泛泛而谈，必须针对对方的每一个论点进行反驳**
"""

    async def conduct_debate(self, rounds: int = 5) -> Dict:
        """进行多轮动态辩论"""

        print(f"\n{'='*80}")
        print(f"专利无效宣告动态辩论开始")
        print(f"专利号：201921401279.9")
        print(f"专利名称：包装机物品传送装置的物料限位板自动调节机构")
        print(f"辩论轮次：{rounds}轮（双方交替发言，共{2*rounds}场）")
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
            "content": opening_statement,
            "timestamp": datetime.now().isoformat()
        })

        # 第2-2*rounds轮：交替辩论
        for i in range(2, 2 * rounds + 1):
            if i % 2 == 0:  # 偶数轮：被请求人回应
                print("\n" + "="*80)
                print(f"【第{i}轮】被请求人（广东冠一）回应")
                print("="*80)

                last_argument = self.debate_log[-1]["content"]
                response = await self.patentee_agent.generate_response(
                    opponent_argument=last_argument,
                    round_num=i
                )

                print(response)
                self.debate_log.append({
                    "round": i,
                    "speaker": "广东冠一（专利权人）",
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                })

            else:  # 奇数轮：请求人反驳
                print("\n" + "="*80)
                print(f"【第{i}轮】无效请求人（济南力邦）反驳")
                print("="*80)

                last_argument = self.debate_log[-1]["content"]
                response = await self.requester_agent.generate_response(
                    opponent_argument=last_argument,
                    round_num=i
                )

                print(response)
                self.debate_log.append({
                    "round": i,
                    "speaker": "济南力邦（无效请求人）",
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                })

        # 保存辩论记录
        self.save_debate_log()

        return {
            "total_rounds": rounds,
            "requester_arguments": len([x for x in self.debate_log if "请求人" in x["speaker"]]),
            "patentee_arguments": len([x for x in self.debate_log if "专利权人" in x["speaker"]]),
            "debate_log": self.debate_log
        }

    def save_debate_log(self):
        """保存辩论记录到文件"""

        output_dir = Path("/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9无效材料/补充证据和理由2026.4.22")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存JSON格式
        json_file = output_dir / f"专利无效宣告动态辩论记录_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.debate_log, f, ensure_ascii=False, indent=2)

        # 保存Markdown格式
        md_file = output_dir / f"专利无效宣告动态辩论记录_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# 专利无效宣告动态辩论记录\n\n")
            f.write(f"**专利号**：201921401279.9\n")
            f.write(f"**专利名称**：包装机物品传送装置的物料限位板自动调节机构\n")
            f.write(f"**辩论时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**辩论轮次**：{len(self.debate_log)}轮\n")
            f.write(f"**辩论类型**：动态辩论（使用实时LLM根据对方发言生成回应）\n\n")
            f.write("---\n\n")

            for entry in self.debate_log:
                f.write(f"## 【第{entry['round']}轮】{entry['speaker']}\n\n")
                f.write(f"{entry['content']}\n\n")
                f.write("---\n\n")

        print(f"\n辩论记录已保存：")
        print(f"- JSON格式：{json_file}")
        print(f"- Markdown格式：{md_file}")


async def main():
    """主函数"""

    print("\n🏛️  专利无效宣告动态辩论系统启动")
    print("=" * 80)

    # 创建辩论管理器
    manager = DynamicPatentDebateManager()

    # 进行5轮辩论
    result = await manager.conduct_debate(rounds=5)

    print("\n" + "=" * 80)
    print("🎊 辩论完成！")
    print("=" * 80)
    print(f"总轮次：{result['total_rounds']}")
    print(f"请求人发言次数：{result['requester_arguments']}")
    print(f"被请求人发言次数：{result['patentee_arguments']}")
    print(f"总发言场数：{len(result['debate_log'])}")


if __name__ == "__main__":
    asyncio.run(main())
