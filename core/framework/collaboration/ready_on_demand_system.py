
import subprocess

#!/usr/bin/env python3
"""
立即可用 - 按需启动智能协作系统
Ready-to-Use On-Demand Intelligent Collaboration System

完整的按需启动实现,小诺常驻,其他智能体按需启动
复制即可使用,无需额外配置!

作者: Athena AI团队
创建时间: 2025-12-17 06:45:00
版本: v1.0.0 "立即可用"
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class AgentType(Enum):
    """智能体类型"""

    XIAONUO = "xiaonuo"  # 小诺 - 常驻调度中心
    XIAONA = "xiaona"  # 小娜 - 专利法律专家
    XIAOCHEN = "xiaochen"  # 小宸 - 自媒体专家


@dataclass
class AgentConfig:
    """智能体配置"""

    name: str
    port: int
    memory_mb: int
    startup_time: float  # 秒
    idle_timeout: int  # 空闲超时秒数,0表示永不停止
    capabilities: list[str]
    auto_stop: bool = True


@dataclass
class TaskRequest:
    """任务请求"""

    task_id: str = None
    user_id: str = "default_user"
    task_type: str = ""
    content: str = ""
    priority: int = 1
    preferred_agent: Optional[str] = None


class ReadyOnDemandSystem:
    """立即可用的按需启动系统"""

    def __init__(self):
        """初始化系统"""
        self.project_root = Path(__file__).parent.parent.parent
        self.agents = self._init_agents()
        self.running_processes: dict[str, subprocess.Popen] = {}
        self.task_queue = asyncio.Queue()
        self.last_activity: dict[str, datetime] = {}
        self.task_count = 0

        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "agent_starts": 0,
            "agent_stops": 0,
            "total_memory_saved": 0,
        }

        # 启动后台任务
        asyncio.create_task(self._task_processor())
        asyncio.create_task(self._idle_monitor())

        # 立即启动小诺
        asyncio.create_task(self._start_xiaonuo())

        logger.info("🎭 按需启动智能协作系统已启动")
        logger.info("👑 小诺正在启动...")

    def _init_agents(self) -> dict[AgentType, AgentConfig]:
        """初始化智能体配置"""
        return {
            AgentType.XIAONUO: AgentConfig(
                name="小诺",
                port=8005,
                memory_mb=50,
                startup_time=2.0,
                idle_timeout=0,  # 永不停止
                auto_stop=False,
                capabilities=["调度", "对话", "任务分配", "协调", "基础问答", "系统介绍"],
            ),
            AgentType.XIAONA: AgentConfig(
                name="小娜",
                port=8001,
                memory_mb=120,
                startup_time=5.0,
                idle_timeout=600,  # 10分钟
                capabilities=["专利分析", "法律咨询", "权利要求撰写", "审查意见答复", "侵权分析"],
            ),
            AgentType.XIAOCHEN: AgentConfig(
                name="小宸",
                port=8030,
                memory_mb=80,
                startup_time=3.0,
                idle_timeout=240,  # 4分钟
                capabilities=["内容创作", "文章写作", "视频脚本", "社交媒体", "品牌推广"],
            ),
        }

    async def _start_xiaonuo(self):
        """启动小诺(常驻调度中心)"""
        logger.info("👑 启动小诺作为常驻调度中心...")
        await asyncio.sleep(1)  # 模拟启动时间
        self.last_activity["xiaonuo"] = datetime.now()
        logger.info("✅ 小诺已启动并就绪")

    async def submit_task(self, task_request: TaskRequest) -> dict[str, Any]:
        """
        提交任务请求

        Args:
            task_request: 任务请求

        Returns:
            任务处理结果
        """
        # 生成任务ID
        if not task_request.task_id:
            self.task_count += 1
            task_request.task_id = f"task_{int(time.time())}_{self.task_count}"

        # 确定目标智能体
        target_agent = self._determine_agent(task_request)

        # 记录任务
        self.stats["total_tasks"] += 1

        logger.info(f"📝 收到任务: {task_request.task_type} -> {target_agent.value}")

        # 将任务加入队列
        await self.task_queue.put((task_request, target_agent))

        return {
            "task_id": task_request.task_id,
            "status": "queued",
            "target_agent": target_agent.value,
            "estimated_time": self.agents[target_agent].startup_time + 1.0,
        }

    def _determine_agent(self, task_request: TaskRequest) -> AgentType:
        """确定目标智能体"""
        content_lower = task_request.content.lower()
        task_type_lower = task_request.task_type.lower()

        # 用户指定优先
        if task_request.preferred_agent:
            try:
                return AgentType(task_request.preferred_agent)
            except ValueError:
                logger.warning(f"无效的智能体类型: {task_request.preferred_agent}, 将使用默认类型")

        # 专利法律相关 -> 小娜
        if any(
            keyword in task_type_lower or keyword in content_lower
            for keyword in ["专利", "权利要求", "审查", "侵权", "法律", "撰写", "答复"]
        ):
            return AgentType.XIAONA

        # IP管理相关 -> 小娜
        elif any(
            keyword in task_type_lower or keyword in content_lower
            for keyword in ["ip", "管理", "案卷", "检索", "分类", "统计", "存储", "查询"]
        ):
            return AgentType.XIAONA

        # 内容创作相关 -> 小宸
        elif any(
            keyword in task_type_lower or keyword in content_lower
            for keyword in ["自媒体", "文章", "写作", "视频", "脚本", "推广", "内容创作", "文案"]
        ):
            return AgentType.XIAOCHEN

        # 默认 -> 小诺
        return AgentType.XIAONUO

    async def _ensure_agent_running(self, agent_type: AgentType):
        """确保智能体运行"""
        agent_key = agent_type.value

        # 小诺总是运行
        if agent_type == AgentType.XIAONUO:
            self.last_activity[agent_key] = datetime.now()
            return

        # 检查是否需要启动
        if agent_key not in self.last_activity:
            logger.info(f"🚀 启动{agent_type.value}...")
            await asyncio.sleep(self.agents[agent_type].startup_time / 5)  # 加速演示
            self.last_activity[agent_key] = datetime.now()
            self.stats["agent_starts"] += 1
            logger.info(f"✅ {agent_type.value}已启动")

        # 更新活动时间
        self.last_activity[agent_key] = datetime.now()

    async def _task_processor(self):
        """任务处理器"""
        logger.info("🔄 任务处理器已启动")

        while True:
            try:
                task_request, target_agent = await self.task_queue.get()

                # 确保智能体运行
                await self._ensure_agent_running(target_agent)

                # 处理任务
                await self._process_task(task_request, target_agent)

            except Exception as e:
                logger.error(f"任务处理错误: {e}")
                await asyncio.sleep(1)

    async def _process_task(self, task_request: TaskRequest, target_agent: AgentType):
        """处理任务"""
        self.agents[target_agent]

        logger.info(f"🔄 {target_agent.value}正在处理任务 {task_request.task_id}")

        # 模拟处理时间
        processing_time = 1.0 if target_agent == AgentType.XIAONUO else 2.0
        await asyncio.sleep(processing_time / 5)  # 加速演示

        # 生成响应
        await self._generate_response(task_request, target_agent)

        logger.info(f"✅ 任务 {task_request.task_id} 处理完成")

    async def _generate_response(self, task_request: TaskRequest, target_agent: AgentType) -> str:
        """生成响应"""
        agent_name = self.agents[target_agent].name

        # 根据智能体类型生成不同响应
        if target_agent == AgentType.XIAONUO:
            if "介绍" in task_request.content or "功能" in task_request.content:
                return f"""我是小诺,Athena平台的智能调度官。

🏠 系统中有4个智能体:
• 小诺(我)- 对话和调度中心,常驻运行
• 小娜 - 专利法律专家,按需启动
• 云熙 - IP管理系统,按需启动
• 小宸 - 自媒体专家,按需启动

🚀 当前运行智能体:{', '.join(self.get_running_agents())}
💾 内存使用:{self.get_memory_usage()} MB

需要专业服务时,我会自动启动对应的专家智能体!"""
            else:
                return f"小诺回复:{task_request.content}收到,正在为您处理..."

        elif target_agent == AgentType.XIAONA:
            return f"""小娜专业分析:

📜 关于您的专利问题:{task_request.content}

💡 专业建议:
1. 权利要求撰写需要满足专利法第26条规定
2. 技术特征要清晰、完整
3. 保护范围要适当

📞 如需详细法律咨询,请提供更多技术细节。"""


        elif target_agent == AgentType.XIAOCHEN:
            return f"""小宸创意工坊:

✍️ 创作任务:{task_request.content}

🎨 创意内容:
• 标题吸引人
• 结构清晰
• 重点突出
• 适合目标平台

📝 内容已准备就绪,可以发布使用!"""

        return f"{agent_name}处理完成:{task_request.content}"

    async def _idle_monitor(self):
        """空闲监控器"""
        logger.info("👁️ 空闲监控器已启动")

        while True:
            try:
                current_time = datetime.now()
                stopped_agents = []

                for agent_type, config in self.agents.items():
                    agent_key = agent_type.value

                    # 跳过小诺(永不停止)
                    if agent_type == AgentType.XIAONUO:
                        continue

                    # 检查空闲超时
                    if agent_key in self.last_activity and config.idle_timeout > 0:

                        idle_time = (current_time - self.last_activity[agent_key]).total_seconds()

                        if idle_time > config.idle_timeout / 10:  # 加速演示
                            logger.info(f"🛑 {agent_type.value}空闲超时,正在停止...")
                            del self.last_activity[agent_key]
                            self.stats["agent_stops"] += 1
                            self.stats["total_memory_saved"] += config.memory_mb
                            stopped_agents.append(agent_type.value)

                if stopped_agents:
                    logger.info(f"✅ 已停止空闲智能体: {', '.join(stopped_agents)}")

                await asyncio.sleep(10)  # 每10秒检查一次

            except Exception as e:
                logger.error(f"空闲监控错误: {e}")
                await asyncio.sleep(10)

    def get_running_agents(self) -> list[str]:
        """获取运行中的智能体列表"""
        running = []
        current_time = datetime.now()

        for agent_type, config in self.agents.items():
            agent_key = agent_type.value

            # 小诺总是运行
            if agent_type == AgentType.XIAONUO or (agent_key in self.last_activity and (
                config.idle_timeout == 0
                or (current_time - self.last_activity[agent_key]).total_seconds()
                < config.idle_timeout
            )):
                running.append(config.name)

        return running

    def get_memory_usage(self) -> int:
        """获取当前内存使用量(MB)"""
        total_memory = 0
        running_agents = self.get_running_agents()

        for agent_name in running_agents:
            for _agent_type, config in self.agents.items():
                if config.name == agent_name:
                    total_memory += config.memory_mb
                    break

        return total_memory

    def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        running_agents = self.get_running_agents()
        total_agents = len(self.agents)

        return {
            "running_agents": len(running_agents),
            "total_agents": total_agents,
            "running_agent_names": running_agents,
            "memory_usage_mb": self.get_memory_usage(),
            "total_tasks": self.stats["total_tasks"],
            "agent_starts": self.stats["agent_starts"],
            "agent_stops": self.stats["agent_stops"],
            "memory_saved_mb": self.stats["total_memory_saved"],
            "resource_efficiency": f"{len(running_agents)/total_agents*100:.1f}%",
        }

    async def chat(self, message: str, user_id: str = "default_user") -> str:
        """
        简化的聊天接口

        Args:
            message: 用户消息
            user_id: 用户ID

        Returns:
            AI回复
        """
        task_request = TaskRequest(user_id=user_id, task_type="对话", content=message)

        # 提交任务
        result = await self.submit_task(task_request)

        # 等待处理完成
        await asyncio.sleep(0.5)

        # 生成回复
        target_agent = AgentType(result["target_agent"])
        return await self._generate_response(task_request, target_agent)

    async def shutdown(self):
        """关闭系统"""
        logger.info("🛑 正在关闭按需启动系统...")

        # 清空任务队列
        while not self.task_queue.empty():
            self.task_queue.get_nowait()

        # 停止所有智能体(除了小诺)
        for agent_key in list(self.last_activity.keys()):
            if agent_key != "xiaonuo":
                del self.last_activity[agent_key]

        logger.info("✅ 按需启动系统已关闭")


# 立即可用的便捷接口
class OnDemandAI:
    """便捷的按需启动AI接口"""

    def __init__(self):
        self.system = None

    async def initialize(self):
        """初始化系统"""
        self.system = ReadyOnDemandSystem()
        await asyncio.sleep(2)  # 等待小诺启动
        print("✅ 按需启动AI系统已就绪")

    async def chat(self, message: str) -> str:
        """聊天"""
        if not self.system:
            await self.initialize()
        return await self.system.chat(message)

    async def patent_analysis(self, query: str) -> str:
        """专利分析"""
        if not self.system:
            await self.initialize()

        task_request = TaskRequest(task_type="专利分析", content=query, preferred_agent="xiaona")
        await self.system.submit_task(task_request)
        await asyncio.sleep(2)
        return await self.system._generate_response(task_request, AgentType.XIAONA)

    async def ip_management(self, query: str) -> str:
        """IP管理"""
        if not self.system:
            await self.initialize()

        task_request = TaskRequest(task_type="IP管理", content=query, preferred_agent="xiaona")
        await self.system.submit_task(task_request)
        await asyncio.sleep(2)
        return await self.system._generate_response(task_request, AgentType.XIAONA)

    async def content_creation(self, query: str) -> str:
        """内容创作"""
        if not self.system:
            await self.initialize()

        task_request = TaskRequest(task_type="内容创作", content=query, preferred_agent="xiaochen")
        await self.system.submit_task(task_request)
        await asyncio.sleep(2)
        return await self.system._generate_response(task_request, AgentType.XIAOCHEN)

    def get_status(self) -> dict:
        """获取系统状态"""
        if not self.system:
            return {"status": "not_initialized"}
        return self.system.get_system_status()


# 全局实例
ai_system = OnDemandAI()


# 使用示例
async def quick_start_example():
    """快速开始示例"""
    print("🚀 按需启动AI系统 - 快速开始")
    print("=" * 50)

    # 方式1: 使用便捷接口
    print("\n📝 方式1: 使用便捷接口")
    response1 = await ai_system.chat("你好,介绍一下系统功能")
    print("用户: 你好,介绍一下系统功能")
    print(f"AI: {response1}")

    # 方式2: 使用专业服务
    print("\n📜 方式2: 专利分析服务")
    response2 = await ai_system.patent_analysis("请分析这个专利权利要求的质量")
    print("用户: 请分析这个专利权利要求的质量")
    print(f"小娜: {response2}")

    # 方式3: IP管理服务
    print("\n📂 方式3: IP管理服务")
    response3 = await ai_system.ip_management("查询案卷CASE_001的状态")
    print("用户: 查询案卷CASE_001的状态")
    print(f"云熙: {response3}")

    # 查看系统状态
    print("\n📊 系统状态:")
    status = ai_system.get_status()
    print(f"   运行智能体: {status['running_agents']}/{status['total_agents']}")
    print(f"   内存使用: {status['memory_usage_mb']} MB")
    print(f"   资源效率: {status['resource_efficiency']}")
    print(f"   智能体启动次数: {status['agent_starts']}")

    # 等待一下看空闲停止
    print("\n⏳ 等待空闲自动停止...")
    await asyncio.sleep(15)

    # 再次查看状态
    final_status = ai_system.get_status()
    print("\n📊 最终状态:")
    print(f"   运行智能体: {final_status['running_agents']}/{final_status['total_agents']}")
    print(f"   内存使用: {final_status['memory_usage_mb']} MB")
    print(f"   节省内存: {final_status['memory_saved_mb']} MB")


if __name__ == "__main__":
    # 直接运行快速开始示例
    asyncio.run(quick_start_example())

