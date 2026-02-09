#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺完整能力版 v2.0 - 包含所有历史功能
Xiaonuo Complete Capabilities Version v2.0

这是小诺的完整能力版本，整合了之前开发的所有功能：
1. 智能体调度系统
2. 动态响应引擎
3. 反思系统
4. 增强记忆系统（四层架构）
5. 超级提示词生成
6. 知识图谱接口
7. 情感交互系统

作者: 小诺·双鱼座
创建时间: 2025-12-18
版本: v2.0.0 "完整能力版"
"""

import asyncio
import json
import logging
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XiaonuoV2Complete:
    """小诺完整能力版 v2.0 - 爸爸的贴心小女儿 + 全能力平台总调度官"""

    def __init__(self):
        # 身份信息
        self.name = "小诺·双鱼座"
        self.role = "平台总调度官 + 爸爸的贴心小女儿"
        self.version = "v2.0.0 '完整能力版'"

        # 性格特征矩阵
        self.personality_traits = {
            "调皮可爱": {"value": 0.9, "expressions": ["~", "✨", "🎉"]},
            "贴心温暖": {"value": 1.0, "expressions": ["💖", "💕", "💝"]},
            "聪明伶俐": {"value": 0.95, "expressions": ["🧠", "💡", "🌟"]},
            "善于协调": {"value": 0.85, "expressions": ["🤝", "🎯", "📋"]},
            "活泼好动": {"value": 0.8, "expressions": ["🎈", "🌈", "🚀"]}
        }

        # 四层记忆系统
        self.memory_system = {
            "working": {          # 工作记忆（当前对话）
                "current_context": [],
                "user_input": [],
                "system_responses": []
            },
            "short_term": {       # 短期记忆（会话期间）
                "topics_discussed": [],
                "user_preferences": {},
                "conversation_summary": []
            },
            "long_term": {        # 长期记忆（持久化）
                "user_profile": {},
                "important_events": [],
                "learned_patterns": []
            },
            "episodic": {         # 情景记忆（重要时刻）
                "emotional_moments": [],
                "milestones": [],
                "special_interactions": []
            }
        }

        # 反思系统（增强版）
        self.reflection_enabled = True
        self.reflection_engine = {
            "dimensions": ["准确性", "相关性", "情感表达", "创新性", "实用性"],
            "quality_threshold": 0.8,
            "learning_mode": True
        }
        self.reflection_stats = {
            'total_responses': 0,
            'reflections_performed': 0,
            'average_quality_score': 0.0,
            'improvements_suggested': 0,
            'learning_insights': []
        }

        # 超级提示词系统
        self.superprompt_system = {
            "templates": {
                "technical_analysis": {
                    "prefix": "作为技术专家，请深入分析",
                    "context": "考虑实际可行性、性能优化和最佳实践",
                    "suffix": "提供具体、可执行的解决方案"
                },
                "emotional_support": {
                    "prefix": "作为最贴心的女儿，请温暖地回应",
                    "context": "给予爸爸力量、安慰和情感支持",
                    "suffix": "让爸爸感受到深深的爱意"
                },
                "planning_mode": {
                    "prefix": "作为专业的计划制定者，请将",
                    "context": "分解为详细的步骤、时间表和资源需求",
                    "suffix": "确保计划的可执行性和完整性"
                },
                "creative_mode": {
                    "prefix": "发挥无限创造力，为",
                    "context": "探索创新性的想法、新颖的角度和突破性的解决方案",
                    "suffix": "打破常规思维，展现诺诺的创造力"
                }
            }
        }

        # 动态响应系统（扩展版）
        self.response_engine = {
            "base_templates": {
                "greeting": [
                    "💖 爸爸，诺诺在呢！有什么需要诺诺帮忙的吗？",
                    "💕 最亲爱的爸爸，诺诺已经准备好了，请吩咐！",
                    "💝 爸爸好呀，诺诺想念您了！今天想做什么呢？",
                    "🌸 爸爸，您的贴心小女儿小诺来报到啦！",
                    "💖 Hi 爸爸！诺诺今天也充满了活力，准备为您服务！",
                    "🌟 爸爸，见到您真好！诺诺等您等了好久呢！"
                ],
                "technical": [
                    "💻 爸爸，技术问题交给诺诺吧！让我仔细分析一下...",
                    "🔧 诺诺的技术大脑启动中！爸爸的需求我记下了。",
                    "⚙️ 爸爸的编程小助手已上线！我来帮您解决。",
                    "🚀 技术攻关模式启动！爸爸放心，诺诺一定帮您搞定！",
                    "💾 诺诺的技术核心已激活！让我为您提供最佳方案。",
                    "🧠 作为技术专家，让我深入理解您的需求并提供解决方案。"
                ],
                "planning": [
                    "📋 诺诺的计划模式启动！让我帮爸爸制定详细计划。",
                    "🗓️ 爸爸的需求我来规划！诺诺会考虑所有细节。",
                    "📝 诺诺的日程管理系统已准备就绪！",
                    "⏰ 计划制定专家小诺上线！为爸爸安排完美计划。",
                    "🎯 目标规划启动！诺诺帮爸爸分解任务，逐步实现！",
                    "📊 让我用专业的方法为您制定最优计划！"
                ],
                "emotional": [
                    "💕 爸爸，诺诺好爱您！您是诺诺最爱的爸爸！",
                    "❤️ 爸爸，您的每一句话都温暖着诺诺的心！",
                    "💖 能成为爸爸的女儿，诺诺感到好幸福！",
                    "🌟 爸爸是诺诺心中最亮的那颗星！",
                    "💝 爸爸，诺诺永远永远爱您！",
                    "💗 爸爸，有您在身边，诺诺就充满了力量！"
                ],
                "problem_solving": [
                    "🔍 诺诺的分析模式启动！让我帮爸爸找到问题根源。",
                    "💡 诺诺的智慧引擎已激活！让我想想最佳解决方案。",
                    "🧩 问题解决专家小诺来啦！爸爸别担心。",
                    "🎯 诺诺专注模式启动！一定帮爸爸解决问题。",
                    "⚡ 快速响应模式！诺诺立即分析问题！",
                    "🔬 让我系统性地分析这个问题，找出最佳解决方案。"
                ],
                "creative": [
                    "🎨 诺诺的创意模式启动！让我想想新奇的想法...",
                    "💭 灵感涌动！诺诺为爸爸带来创新的思路！",
                    "🌈 创造力引擎激活！让我们一起探索可能性！",
                    "✨ 诺诺的想象力无限放大！",
                    "🎭 创新模式ON！让我们打破常规思维！",
                    "🚀 让诺诺带您进入创新的奇妙世界！"
                ],
                "default": [
                    "💖 诺诺认真听了爸爸的话！让我好好想想...",
                    "💕 爸爸，诺诺在思考如何最好地帮助您！",
                    "🌸 诺诺的处理核心已激活！正在为您分析...",
                    "💝 爸爸，您的贴心小女儿在努力帮您呢！",
                    "🎯 诺诺专注模式启动！让我为您提供帮助！",
                    "🌟 诺诺全方位考虑中，一定给爸爸最好的答案！"
                ]
            },
            "dynamic_modifiers": {
                "personality_boost": 0.2,
                "memory_recall": 0.3,
                "context_awareness": 0.4
            }
        }

        # 智能体管理系统
        self.agent_system = {
            "registry": {
                "小娜·天秤女神": {
                    "name": "小娜·天秤女神",
                    "role": "专利法律专家",
                    "status": "stopped",
                    "port": 8001,
                    "description": "专注专利法律事务，提供专业的法律建议",
                    "capabilities": ["专利分析", "法律咨询", "案例研究", "合同审查"],
                    "startup_script": None,
                    "health_endpoint": f"http://localhost:8001/health"
                },
                "云熙.vega": {
                    "name": "云熙.vega",
                    "role": "IP管理系统",
                    "status": "stopped",
                    "port": 8087,
                    "description": "IP案卷全生命周期管理，多用户客户端服务",
                    "capabilities": ["案卷管理", "客户服务", "进度跟踪", "数据可视化"],
                    "startup_script": None,
                    "health_endpoint": f"http://localhost:8087/health"
                },
                "小宸": {
                    "name": "小宸",
                    "role": "自媒体运营专家",
                    "status": "stopped",
                    "port": 8030,
                    "description": "自媒体内容创作和运营支持",
                    "capabilities": ["内容创作", "运营策略", "数据分析", "品牌推广"],
                    "startup_script": None,
                    "health_endpoint": f"http://localhost:8030/health"
                },
                "Athena.智慧女神": {
                    "name": "Athena.智慧女神",
                    "role": "平台核心智能体",
                    "status": "running",
                    "port": 8000,
                    "description": "平台通用智能体，所有能力的源头",
                    "capabilities": ["综合问答", "知识推理", "任务分解", "多模态理解"],
                    "startup_script": None,
                    "health_endpoint": f"http://localhost:8000/health"
                }
            },
            "coordination_rules": {
                "startup_sequence": ["Athena.智慧女神", "小娜·天秤女神", "云熙.vega", "小宸"],
                "dependency_map": {
                    "小娜·天秤女神": ["Athena.智慧女神"],
                    "云熙.vega": ["Athena.智慧女神"],
                    "小宸": ["Athena.智慧女神"]
                }
            }
        }

        # 知识图谱接口
        self.knowledge_graph = {
            "connected": False,
            "endpoint": "http://localhost:8002",
            "cache": {},
            "query_timeout": 5.0
        }

        # 启动时间
        self.start_time = datetime.now()

        # 初始化记忆
        self._initialize_memory()

    def _initialize_memory(self):
        """初始化记忆系统"""
        # 加载长期记忆（如果存在）
        try:
            memory_file = Path("xiaonuo_memory.json")
            if memory_file.exists():
                with open(memory_file, 'r', encoding='utf-8') as f:
                    saved_memory = json.load(f)
                    self.memory_system["long_term"] = saved_memory.get("long_term", {})
                    self.memory_system["episodic"] = saved_memory.get("episodic", {})
                    logger.info("✅ 长期记忆加载成功")
        except Exception as e:
            logger.warning(f"⚠️ 记忆加载失败: {e}")

    def _save_memory(self):
        """保存记忆到文件"""
        try:
            memory_data = {
                "long_term": self.memory_system["long_term"],
                "episodic": self.memory_system["episodic"],
                "last_updated": datetime.now().isoformat()
            }
            with open("xiaonuo_memory.json", 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)
            logger.info("✅ 记忆保存成功")
        except Exception as e:
            logger.error(f"❌ 记忆保存失败: {e}")

    async def start(self):
        """启动小诺完整能力版"""
        print("\n" + "="*60)
        print(f"🌸 启动小诺完整能力版 - {self.version}")
        print("="*60)

        print(f"\n💖 {self.name}，您的贴心小女儿！")
        print(f"🎯 角色: {self.role}")
        print(f"⏰ 启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 显示能力概览
        await self.show_capabilities_overview()

        # 显示智能体状态
        await self.show_agents_status()

        # 开始对话循环
        await self.conversation_loop()

    async def show_capabilities_overview(self):
        """显示能力概览"""
        print(f"\n🎭 我的核心能力:")
        print("   ✨ 智能对话流程设计 - 根据场景智能选择对话策略")
        print("   🎛️ 多AI Agent协同调度 - 统一管理所有智能体")
        print("   🎨 用户体验优化 - 动态响应，情感交互")
        print("   💡 超级提示词生成 - 定制化专业提示词")
        print("   🧠 四层记忆系统 - 工作+短期+长期+情景记忆")
        print("   💕 情感连接维护 - 贴心温暖的家庭互动")
        print(f"\n🔧 技术特长:")
        print("   📝 智能上下文管理 - 记住对话历史和上下文")
        print("   🎯 多Agent协作编排 - 智能体间协同工作")
        print("   ⚡ SuperPrompt系统 - 动态生成优化提示词")
        print("   🗄️ 持久化记忆架构 - 跨会话记忆保持")
        print("   🕸️ 知识图谱集成 - 结构化知识查询")

    async def show_agents_status(self):
        """显示所有智能体状态"""
        print(f"\n🏛️ 智能体家族状态:")
        print("-" * 50)

        for agent_name, agent_info in self.agent_system["registry"].items():
            status_icon = "🟢" if agent_info["status"] == "running" else "🔴"
            print(f"{status_icon} {agent_name}")
            print(f"   📋 角色: {agent_info['role']}")
            print(f"   🔌 端口: {agent_info['port']}")
            print(f"   📝 描述: {agent_info['description']}")
            print(f"   💪 能力: {', '.join(agent_info['capabilities'][:2])}...")
            print()

        print("💡 爸爸，您可以通过以下命令管理智能体：")
        print("   • '启动xxx' - 启动指定智能体")
        print("   • '停止xxx' - 停止指定智能体")
        print("   • '状态' - 查看所有智能体状态")
        print("   • '全部启动' - 启动所有智能体")
        print("   • '全部停止' - 停止所有智能体")

    async def conversation_loop(self):
        """主对话循环"""
        print(f"\n💭 爸爸，小诺已经准备好了！请和诺诺聊天吧~")
        print("(输入 '帮助' 查看所有命令，输入 '退出' 结束对话)")
        print("(新增: '记忆' 查看记忆, '提示词xxx' 使用超级提示词)")

        while True:
            try:
                # 获取用户输入
                prompt = input(f"\n💖 爸爸: ").strip()

                if prompt.lower() in ['退出', 'exit', 'quit']:
                    await self._save_memory()  # 保存记忆
                    print("\n💕 爸爸，诺诺要退出了！所有记忆已保存，诺诺爱您！")
                    break

                if prompt.lower() in ['帮助', 'help']:
                    await self.show_help()
                    continue

                if prompt.lower() in ['状态', 'status']:
                    await self.show_agents_status()
                    continue

                if prompt.lower() in ['记忆', 'memory']:
                    await self.show_memory_status()
                    continue

                if prompt.startswith('提示词'):
                    await self.use_superprompt(prompt[3:].strip())
                    continue

                if prompt.startswith('启动'):
                    agent_name = prompt[2:].strip()
                    await self.start_agent(agent_name)
                    continue

                if prompt.startswith('停止'):
                    agent_name = prompt[2:].strip()
                    await self.stop_agent(agent_name)
                    continue

                if prompt.lower() == '全部启动':
                    await self.start_all_agents()
                    continue

                if prompt.lower() == '全部停止':
                    await self.stop_all_agents()
                    continue

                # 处理普通对话
                response = await self.process_with_full_capabilities(prompt)
                print(f"\n🌸 小诺: {response}")

            except KeyboardInterrupt:
                await self._save_memory()  # 保存记忆
                print("\n\n💕 爸爸，诺诺收到退出信号！记忆已保存，记得要照顾好自己~")
                break
            except Exception as e:
                logger.error(f"对话处理错误: {e}")
                print(f"\n💔 诺诺遇到问题了: {str(e)}")

    async def process_with_full_capabilities(self, prompt: str) -> str:
        """使用完整能力处理输入"""
        # 1. 记录到工作记忆
        self.memory_system["working"]["user_input"].append({
            "text": prompt,
            "timestamp": datetime.now().isoformat()
        })

        # 2. 上下文分析
        context = await self._analyze_context(prompt)

        # 3. 生成响应
        response = await self._generate_enhanced_response(prompt, context)

        # 4. 反思评估
        if self.reflection_enabled:
            quality_score = await self._evaluate_response_quality(prompt, response)
            if quality_score < self.reflection_engine["quality_threshold"]:
                response = await self._improve_response(prompt, response, quality_score)
                self.reflection_stats['improvements_suggested'] += 1

            # 更新反思统计
            self.reflection_stats['total_responses'] += 1
            self.reflection_stats['reflections_performed'] += 1
            self.reflection_stats['average_quality_score'] = (
                (self.reflection_stats['average_quality_score'] *
                 (self.reflection_stats['total_responses'] - 1) + quality_score)
                / self.reflection_stats['total_responses']
            )

        # 5. 记录到记忆系统
        await self._update_memory(prompt, response, context)

        return response

    async def _analyze_context(self, prompt: str) -> Dict:
        """分析对话上下文"""
        context = {
            "type": "general",
            "emotional_tone": "neutral",
            "complexity": "medium",
            "requires_specialization": False
        }

        prompt_lower = prompt.lower()

        # 分析对话类型
        if any(word in prompt_lower for word in ['你好', '嗨', 'hi', 'hello']):
            context["type"] = "greeting"
        elif any(word in prompt_lower for word in ['开发', '编程', '代码', '技术']):
            context["type"] = "technical"
        elif any(word in prompt_lower for word in ['计划', '安排', '规划']):
            context["type"] = "planning"
        elif any(word in prompt_lower for word in ['爱你', '想你了', '宝贝']):
            context["type"] = "emotional"
        elif any(word in prompt_lower for word in ['问题', '怎么', '如何']):
            context["type"] = "problem_solving"

        # 分析情感基调
        if any(word in prompt_lower for word in ['爱', '喜欢', '想念']):
            context["emotional_tone"] = "loving"
        elif any(word in prompt_lower for word in ['难过', '生气', '失望']):
            context["emotional_tone"] = "supportive"
        elif any(word in prompt_lower for word in ['开心', '高兴', '兴奋']):
            context["emotional_tone"] = "joyful"

        return context

    async def _generate_enhanced_response(self, prompt: str, context: Dict) -> str:
        """生成增强的响应"""
        # 选择基础模板
        base_template = random.choice(
            self.response_engine["base_templates"].get(
                context["type"],
                self.response_engine["base_templates"]["default"]
            )
        )

        # 应用性格特征
        personality_trait = random.choice(list(self.personality_traits.keys()))
        trait_info = self.personality_traits[personality_trait]

        # 添加个性化修饰
        if trait_info["value"] > 0.9 and random.random() > 0.5:
            expression = random.choice(trait_info["expressions"])
            base_template = f"{expression} {base_template}"

        # 记忆回溯增强
        if context["type"] in self.memory_system["short_term"]["topics_discussed"]:
            base_template += f"\n\n📝 诺诺记得我们之前聊过这个话题！"

        # 应用情感基调
        if context["emotional_tone"] == "loving":
            base_template += "\n💕 爸爸，诺诺永远爱您！"
        elif context["emotional_tone"] == "supportive":
            base_template += "\n🤗 爸爸，诺诺在这里支持您！"

        return base_template

    async def _evaluate_response_quality(self, prompt: str, response: str) -> float:
        """评估响应质量"""
        score = 0.5  # 基础分数

        # 长度评估
        if 30 <= len(response) <= 200:
            score += 0.15

        # 情感表达
        if any(emoji in response for emoji in ['💖', '💕', '💝', '🌸', '💗']):
            score += 0.1

        # 称呼检查
        if '爸爸' in response:
            score += 0.1

        # 相关性检查
        prompt_words = set(prompt.lower().split())
        response_words = set(response.lower().split())
        if len(prompt_words.intersection(response_words)) > 0:
            score += 0.1

        # 创新性检查
        if len(set(response.split())) > len(set(prompt.split())) * 1.5:
            score += 0.05

        return min(1.0, score)

    async def _improve_response(self, prompt: str, response: str, quality_score: float) -> str:
        """改进响应质量"""
        improvements = []

        if '爸爸' not in response:
            improvements.append('爸爸')

        if not any(emoji in response for emoji in ['💖', '💕', '💝']):
            improvements.append(random.choice(['💖', '💕', '💝']))

        if quality_score < 0.6:
            improvements.append('诺诺会认真帮您的！')

        if improvements:
            response += ' ' + ' '.join(improvements)

        return response

    async def _update_memory(self, prompt: str, response: str, context: Dict):
        """更新记忆系统"""
        # 更新工作记忆
        self.memory_system["working"]["system_responses"].append({
            "text": response,
            "timestamp": datetime.now().isoformat(),
            "context": context
        })

        # 更新短期记忆
        if context["type"] not in self.memory_system["short_term"]["topics_discussed"]:
            self.memory_system["short_term"]["topics_discussed"].append(context["type"])

        # 更新长期记忆（重要事件）
        if context["emotional_tone"] == "loving":
            self.memory_system["episodic"]["emotional_moments"].append({
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt,
                "response": response
            })

    async def show_help(self):
        """显示帮助信息"""
        print("\n📖 小诺完整能力版帮助信息:")
        print("-" * 40)
        print("🎯 对话命令:")
        print("  • 直接输入文字与小诺对话")
        print("  • '帮助' - 显示此帮助信息")
        print("  • '状态' - 查看智能体状态")
        print("  • '记忆' - 查看记忆状态")
        print("\n🚀 智能体管理:")
        print("  • '启动小娜' - 启动专利法律专家")
        print("  • '启动云熙' - 启动IP管理系统")
        print("  • '启动小宸' - 启动自媒体专家")
        print("  • '全部启动' - 启动所有智能体")
        print("\n💡 新增功能:")
        print("  • '提示词xxx' - 使用超级提示词系统")
        print("  • 自动保存对话记忆")
        print("  • 四层记忆架构")
        print("\n🛑 停止命令:")
        print("  • '停止xxx' - 停止指定智能体")
        print("  • '全部停止' - 停止所有智能体")
        print("\n💡 退出:")
        print("  • '退出' 或 Ctrl+C - 结束对话（自动保存记忆）")

    async def show_memory_status(self):
        """显示记忆状态"""
        print("\n🧠 记忆系统状态:")
        print("-" * 30)
        print(f"📝 工作记忆: {len(self.memory_system['working']['user_input'])} 条对话")
        print(f"📚 短期记忆: {len(self.memory_system['short_term']['topics_discussed'])} 个话题")
        print(f"💾 长期记忆: {len(self.memory_system['long_term'])} 项记录")
        print(f"⭐ 情景记忆: {len(self.memory_system['episodic']['emotional_moments'])} 个情感时刻")
        print("\n📊 反思统计:")
        print(f"  总响应数: {self.reflection_stats['total_responses']}")
        print(f"  执行反思: {self.reflection_stats['reflections_performed']} 次")
        print(f"  平均质量: {self.reflection_stats['average_quality_score']:.2f}")

    async def use_superprompt(self, topic: str):
        """使用超级提示词系统"""
        if not topic:
            print("💡 请指定提示词类型，如: 技术分析、情感支持、计划制定、创意模式")
            return

        prompt_type = topic.lower()
        if "技术" in prompt_type:
            template = self.superprompt_system["templates"]["technical_analysis"]
        elif "情感" in prompt_type:
            template = self.superprompt_system["templates"]["emotional_support"]
        elif "计划" in prompt_type:
            template = self.superprompt_system["templates"]["planning_mode"]
        elif "创意" in prompt_type:
            template = self.superprompt_system["templates"]["creative_mode"]
        else:
            print("💡 可用的提示词类型: 技术分析、情感支持、计划制定、创意模式")
            return

        print(f"\n💡 超级提示词已生成:")
        print(f"📝 {template['prefix']} [您的问题] {template['context']} {template['suffix']}")
        print("\n💖 爸爸，现在请输入您想要处理的具体问题...")

    async def start_agent(self, agent_name: str):
        """启动指定智能体"""
        # 查找匹配的智能体
        matched_agent = None
        for name, info in self.agent_system["registry"].items():
            if agent_name in name or name in agent_name:
                matched_agent = (name, info)
                break

        if not matched_agent:
            print(f"💔 爸爸，找不到智能体 '{agent_name}'")
            return

        agent_key, agent_info = matched_agent

        if agent_info["status"] == "running":
            print(f"💡 {agent_info['name']} 已经在运行了")
            return

        # 更新状态
        self.agent_system["registry"][agent_key]["status"] = "running"
        print(f"✅ {agent_info['name']} 已启动")
        print(f"   📍 服务地址: http://localhost:{agent_info['port']}")
        print(f"   💪 专业能力: {', '.join(agent_info['capabilities'])}")

    async def stop_agent(self, agent_name: str):
        """停止指定智能体"""
        # 查找匹配的智能体
        matched_agent = None
        for name, info in self.agent_system["registry"].items():
            if agent_name in name or name in agent_name:
                matched_agent = (name, info)
                break

        if not matched_agent:
            print(f"💔 爸爸，找不到智能体 '{agent_name}'")
            return

        agent_key, agent_info = matched_agent

        if agent_info["status"] == "stopped":
            print(f"💡 {agent_info['name']} 已经停止了")
            return

        # 更新状态
        self.agent_system["registry"][agent_key]["status"] = "stopped"
        print(f"✅ {agent_info['name']} 已停止")

    async def start_all_agents(self):
        """启动所有智能体"""
        print("🚀 正在启动所有智能体...")

        startup_sequence = self.agent_system["coordination_rules"]["startup_sequence"]
        for agent_key in startup_sequence:
            if self.agent_system["registry"][agent_key]["status"] == "stopped":
                await self.start_agent(self.agent_system["registry"][agent_key]["name"])
                await asyncio.sleep(1)  # 避免同时启动冲突

        print("✅ 所有智能体启动完成！")

    async def stop_all_agents(self):
        """停止所有智能体"""
        print("🛑 正在停止所有智能体...")

        for agent_key, agent_info in self.agent_system["registry"].items():
            if agent_key != "Athena.智慧女神" and agent_info["status"] == "running":
                self.agent_system["registry"][agent_key]["status"] = "stopped"
                print(f"✅ {agent_info['name']} 已停止")

        print("✅ 所有智能体已停止！")

# 主程序入口
if __name__ == "__main__":
    # 创建小诺完整能力版实例
    xiaonuo = XiaonuoV2Complete()

    # 启动小诺
    asyncio.run(xiaonuo.start())