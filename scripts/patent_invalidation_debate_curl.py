#!/usr/bin/env python3
"""
专利无效宣告动态辩论系统 - 使用curl调用

功能：
1. 使用本地oMLX模型进行动态辩论
2. 使用subprocess调用curl（避免Python HTTP库兼容性问题）
3. 优化的上下文长度，适合本地模型

作者：Athena平台
日期：2026-04-23
"""

import json
import asyncio
import subprocess
from typing import Dict, List
from datetime import datetime
from pathlib import Path


class CurlPatentDebateAgent:
    """使用curl的本地模型辩论代理"""

    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.api_url = "http://localhost:8009/v1/chat/completions"
        self.api_key = "xj781102@"
        self.model = "Qwen3.5-27B-4bit"
        self.debate_history: List[Dict] = []

    def _call_omlx(self, user_message: str) -> str:
        """使用curl调用oMLX"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 800,
            "temperature": 0.8
        }

        # 构建curl命令
        curl_cmd = [
            "curl", "-s", "-X", "POST", self.api_url,
            "-H", "Content-Type: application/json",
            "-H", f"Authorization: Bearer {self.api_key}",
            "-d", json.dumps(payload),
            "--max-time", "120"  # 120秒超时
        ]

        try:
            result = subprocess.run(
                curl_cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3分钟总超时
            )

            if result.returncode == 0:
                response = json.loads(result.stdout)
                return response["choices"][0]["message"]["content"]
            else:
                return f"[Curl失败]：{result.stderr[:200]}"

        except subprocess.TimeoutExpired:
            return "[超时]：本地模型响应时间过长"
        except Exception as e:
            return f"[异常]：{str(e)}"

    def generate_response(self, opponent_argument: str, round_num: int) -> str:
        """生成辩论回应"""

        user_content = f"""你是{self.name}。

# 对方刚才的观点（第{round_num}轮）：
{opponent_argument[-600:] if len(opponent_argument) > 600 else opponent_argument}

# 核心法律依据：
- 专利法第22条第3款：创造性定义
- 审查指南第二部分第四章§3.2：三步法
- 审查指南第二部分第四章§6.2：避免事后诸葛亮

# 核心对比文件：
- D1（CN208647230U）：包装机物料输送机构
- D2（CN201198403Y）：斜杆传动，教导斜向导向→间距变化
- E1（CN206156248U）：三段式可调轨道，确认宽度调节是常规需求

# 目标专利核心：
- 两条斜向滑轨432间距从左往右逐渐缩短
- 纵向+斜向同步调节
- 一驱三调结构

请针对对方观点反驳。长度：200-400字。直接输出。
"""

        content = self._call_omlx(user_content)

        # 记录历史
        self.debate_history.append({
            "round": round_num,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        return content


class CurlPatentDebateManager:
    """使用curl的辩论管理器"""

    def __init__(self):
        print("🔧 本地模型配置：")
        print(f"   API地址：http://localhost:8009/v1")
        print(f"   模型：Qwen3.5-27B-4bit")
        print(f"   使用方式：subprocess + curl")

        # 创建系统提示词
        self.requester_prompt = self._create_requester_prompt()
        self.patentee_prompt = self._create_patentee_prompt()

        # 创建代理
        self.requester_agent = CurlPatentDebateAgent(
            "济南力邦（无效请求人）",
            "requester",
            self.requester_prompt
        )

        self.patentee_agent = CurlPatentDebateAgent(
            "广东冠一（专利权人）",
            "patentee",
            self.patentee_prompt
        )

        self.debate_log: List[Dict] = []

    def _create_requester_prompt(self) -> str:
        return """你是济南力邦（无效请求人）的专利律师，对专利201921401279.9提出无效宣告。

核心观点：
1. D1（CN208647230U）是最接近的现有技术
2. D1未公开：纵向调节单元42、斜向调节单元43、两条斜向滑轨432间距从左往右逐渐缩短
3. D2（CN201198403Y）教导"斜向导向→间距变化"原理
4. "间距逐渐缩短"是斜楔机构几何必然
5. 对方陷入"事后诸葛亮"

任务：证明权利要求1-10不具备创造性。使用三步法，引用D1、D2、E1段落。"""

    def _create_patentee_prompt(self) -> str:
        return """你是广东冠一（专利权人）的专利律师，为专利201921401279.9辩护。

核心观点：
1. D1与目标专利存在根本性技术路线差异
2. D2未明确教导"间距逐渐缩短"（D2是"等间距平移"）
3. "间距逐渐缩短"需精确计算，需创造性劳动
4. 目标专利产生预料不到的技术效果
5. 对方对D2扩大化解释

任务：证明权利要求1-10具备创造性。强调技术路线差异，指出对方论证错误。"""

    async def conduct_debate(self, rounds: int = 5) -> Dict:
        """进行多轮辩论"""

        print(f"\n{'='*80}")
        print(f"专利无效宣告本地模型辩论开始")
        print(f"专利号：201921401279.9")
        print(f"辩论轮次：{rounds}轮")
        print(f"{'='*80}\n")

        # 第1轮
        print("\n" + "="*80)
        print("【第1轮】无效请求人开场陈述")
        print("="*80)

        opening = self.requester_agent.generate_response(
            opponent_argument="（这是开场陈述，请阐述你方的主要无效理由）",
            round_num=1
        )
        print(opening)
        self.debate_log.append({
            "round": 1,
            "speaker": "济南力邦（无效请求人）",
            "content": opening,
            "timestamp": datetime.now().isoformat()
        })

        # 后续轮次
        for i in range(2, 2 * rounds + 1):
            if i % 2 == 0:
                print("\n" + "="*80)
                print(f"【第{i}轮】被请求人（广东冠一）回应")
                print("="*80)

                last_arg = self.debate_log[-1]["content"]
                response = self.patentee_agent.generate_response(
                    opponent_argument=last_arg,
                    round_num=i
                )
                print(response)
                self.debate_log.append({
                    "round": i,
                    "speaker": "广东冠一（专利权人）",
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                print("\n" + "="*80)
                print(f"【第{i}轮】无效请求人（济南力邦）反驳")
                print("="*80)

                last_arg = self.debate_log[-1]["content"]
                response = self.requester_agent.generate_response(
                    opponent_argument=last_arg,
                    round_num=i
                )
                print(response)
                self.debate_log.append({
                    "round": i,
                    "speaker": "济南力邦（无效请求人）",
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                })

        # 保存记录
        self.save_debate_log()

        return {
            "total_rounds": rounds,
            "requester_count": len([x for x in self.debate_log if "请求人" in x["speaker"]]),
            "patentee_count": len([x for x in self.debate_log if "专利权人" in x["speaker"]]),
            "debate_log": self.debate_log
        }

    def save_debate_log(self):
        """保存辩论记录"""
        output_dir = Path("/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9无效材料/补充证据和理由2026.4.22")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Markdown格式
        md_file = output_dir / f"专利无效宣告辩论_curl_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# 专利无效宣告辩论记录（使用curl）\n\n")
            f.write(f"**专利号**：201921401279.9\n")
            f.write(f"**辩论时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**使用模型**：Qwen3.5-27B-4bit（本地oMLX）\n")
            f.write(f"**辩论轮次**：{len(self.debate_log)}轮\n\n")
            f.write("---\n\n")

            for entry in self.debate_log:
                f.write(f"## 【第{entry['round']}轮】{entry['speaker']}\n\n")
                f.write(f"{entry['content']}\n\n")
                f.write("---\n\n")

        print(f"\n✅ 辩论记录已保存：{md_file}")


async def main():
    """主函数"""
    print("\n🏛️  专利无效宣告本地模型辩论系统启动（curl版）")
    print("=" * 80)

    manager = CurlPatentDebateManager()
    result = await manager.conduct_debate(rounds=5)

    print("\n" + "=" * 80)
    print("🎊 辩论完成！")
    print("=" * 80)
    print(f"总轮次：{result['total_rounds']}")
    print(f"请求人发言：{result['requester_count']}次")
    print(f"被请求人发言：{result['patentee_count']}次")


if __name__ == "__main__":
    asyncio.run(main())
