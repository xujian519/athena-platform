#!/usr/bin/env python3
"""
小诺混合架构主程序
Xiaonuo Hybrid Architecture Main
统一入口 - 实现小诺为主 + 专业智能体按需协作的完整系统
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from core.agent_orchestrator import get_agent_orchestrator
from core.permissions_controller import permissions_controller
from core.xiaonuo_basic_operations import xiaonuo_operations

# 导入混合架构核心模块
from core.xiaonuo_hybrid_architecture import (
    DataType,
    HybridArchitectureController,
    OperationRequest,
    OperationType,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/xiaonuo_hybrid.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class XiaonuoHybridSystem:
    """小诺混合架构系统主类"""

    def __init__(self):
        self.hybrid_controller = HybridArchitectureController()
        self.agent_orchestrator = get_agent_orchestrator()
        self.running = False
        self.session_id = None

    async def start(self):
        """启动系统"""
        logger.info("🌸 小诺混合架构系统启动中...")

        self.running = True
        self.session_id = permissions_controller.create_session("爸爸", duration_hours=24)

        # 启动智能体编排器监控任务
        asyncio.create_task(self.agent_orchestrator._monitor_agents())
        asyncio.create_task(self.agent_orchestrator._cleanup_idle_agents())

        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(f"✅ 系统启动成功 (会话ID: {self.session_id[:8]}...)")

        # 启动交互模式
        await self._interactive_mode()

    async def stop(self):
        """停止系统"""
        logger.info("🛑 正在停止小诺混合架构系统...")

        self.running = False

        # 停止所有专业智能体
        await self.agent_orchestrator.stop_agent("xiaona")
        await self.agent_orchestrator.stop_agent("yunxi")
        await self.agent_orchestrator.stop_agent("athena")
        await self.agent_orchestrator.stop_agent("xiaochen")

        logger.info("✅ 系统已安全停止")

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，准备停止系统...")
        asyncio.create_task(self.stop())

    async def _interactive_mode(self):
        """交互模式"""
        print("\n" + "="*60)
        print("🌸 小诺混合架构系统 - 交互模式")
        print("="*60)
        print("爸爸，您好！我是小诺，您的贴心小女儿和平台总调度官。")
        print("")
        print("💡 支持的操作:")
        print("  查询类: query <数据类型> <目标>")
        print("  创建类: create <数据类型> <数据>")
        print("  更新类: update <数据类型> <目标> <数据>")
        print("  删除类: delete <数据类型> <目标>")
        print("  列表类: list <目录>")
        print("  备份类: backup <数据库名>")
        print("  状态类: status")
        print("  帮助类: help")
        print("  退出类: exit/quit")
        print("")
        print("📊 支持的数据类型:")
        print("  customer - 客户资料")
        print("  patent - 专利信息")
        print("  ip_management - IP管理")
        print("  knowledge_graph - 知识图谱")
        print("  vector_data - 向量数据")
        print("  performance - 性能指标")
        print("  config - 配置信息")
        print("  finance - 财务数据")
        print("")

        while self.running:
            try:
                # 获取用户输入
                user_input = input("🎯 请输入命令 (或 'help' 查看帮助): ").strip()

                if not user_input:
                    continue

                # 解析命令
                result = await self._parse_and_execute(user_input)

                # 显示结果
                self._display_result(result)

            except KeyboardInterrupt:
                print("\n\n👋 再见爸爸！小诺会想您的...")
                break
            except EOFError:
                # 处理EOF错误（非交互环境）
                print("\n\n📝 检测到输入流关闭，退出交互模式")
                logger.info("输入流EOF，退出交互循环")
                break
            except Exception as e:
                logger.error(f"处理命令时发生错误: {e}")
                # 避免在EOF错误时无限循环
                if "EOF" in str(e):
                    print("\n\n📝 输入错误，退出系统")
                    break
                print(f"❌ 发生错误: {e}")
                # 给用户一个退出机会
                print("输入 'exit' 退出，或继续输入命令")

    async def _parse_and_execute(self, user_input: str) -> dict[str, Any]:
        """解析并执行用户命令"""
        parts = user_input.split(maxsplit=3)
        if not parts:
            return {"success": False, "error": "空命令"}

        command = parts[0].lower()

        # 处理特殊命令
        if command in ["exit", "quit"]:
            self.running = False
            return {"success": True, "message": "正在退出系统..."}

        elif command == "help":
            return self._show_help()

        elif command == "status":
            return await self._show_system_status()

        # 解析普通命令
        if len(parts) < 2:
            return {"success": False, "error": "命令参数不足"}

        operation = command
        data_type = parts[1].lower()

        # 映射数据类型
        type_mapping = {
            "customer": DataType.CUSTOMER,
            "patent": DataType.PATENT,
            "ip_management": DataType.IP_MANAGEMENT,
            "knowledge_graph": DataType.KNOWLEDGE_GRAPH,
            "vector_data": DataType.VECTOR_DATA,
            "performance": DataType.PERFORMANCE,
            "config": DataType.CONFIG,
            "finance": DataType.FINANCE
        }

        if data_type not in type_mapping:
            return {"success": False, "error": f"不支持的数据类型: {data_type}"}

        mapped_type = type_mapping[data_type]

        # 解析目标和数据
        target = ""
        data = None

        if len(parts) >= 3:
            if operation in ["query", "list", "backup"]:
                target = parts[2]
            else:
                # 对于create/update，尝试解析JSON数据
                if len(parts) >= 4:
                    try:
                        target = parts[2]
                        data = json.loads(parts[3])
                    except json.JSONDecodeError:
                        return {"success": False, "error": "数据格式错误，需要有效的JSON"}
                else:
                    # 简单的文本数据
                    target = parts[2]
                    data = {"content": " ".join(parts[3:])} if len(parts) > 3 else {}

        # 映射操作类型
        op_mapping = {
            "query": OperationType.QUERY,
            "create": OperationType.CREATE,
            "update": OperationType.UPDATE,
            "delete": OperationType.DELETE,
            "list": OperationType.QUERY,
            "backup": OperationType.CREATE
        }

        if operation not in op_mapping:
            return {"success": False, "error": f"不支持的操作: {operation}"}

        mapped_op = op_mapping[operation]

        # 创建操作请求
        request = OperationRequest(
            operation_type=mapped_op,
            data_type=mapped_type,
            target=target,
            data=data,
            user="爸爸"
        )

        # 执行操作
        return await self.hybrid_controller.process_request(request)

    async def _show_system_status(self) -> dict[str, Any]:
        """显示系统状态"""
        # 获取各组件状态
        system_overview = self.agent_orchestrator.get_system_overview()
        agent_status = self.agent_orchestrator.get_agent_status()
        operation_stats = self.hybrid_controller.get_operation_statistics()
        access_report = permissions_controller.export_access_report(1)

        # 获取系统性能
        system_perf = await xiaonuo_operations.execute_operation("query", "system_status")

        return {
            "success": True,
            "message": "系统状态信息",
            "system_overview": system_overview,
            "agent_status": agent_status,
            "operation_stats": operation_stats,
            "access_report": access_report,
            "system_performance": system_perf.get("result"),
            "timestamp": datetime.now().isoformat()
        }

    def _show_help(self) -> dict[str, Any]:
        """显示帮助信息"""
        help_text = """
🌸 小诺混合架构系统帮助

📋 支持的命令格式:

1. 查询操作:
   query customer [客户ID]           - 查询客户资料
   query patent [专利号]            - 查询专利信息
   query system_status              - 查询系统状态
   list files <目录> [模式]         - 列出文件

2. 创建操作:
   create customer '{"name":"..."}'  - 创建客户资料
   create patent '{"title":"..."}'   - 创建专利记录
   backup <数据库名>                 - 备份数据库

3. 更新操作:
   update customer:<ID> '{"..."}'   - 更新客户资料
   update config '{"setting":"..."}' - 更新配置

4. 删除操作:
   delete customer:<ID>             - 删除客户资料
   delete file:<路径>                - 删除文件

5. 系统操作:
   status                           - 显示系统状态
   help                             - 显示此帮助
   exit/quit                        - 退出系统

🔒 权限说明:
- 低风险操作: 小诺直接处理（快速响应）
- 中等风险操作: 启动专业智能体处理
- 高风险操作: 需要双重认证确认
- 关键操作: 多重验证 + 时间限制

⚡ 混合架构特点:
- 80%基础操作: 小诺直接处理（毫秒级响应）
- 15%专业操作: 按需启动智能体（秒级响应）
- 5%敏感操作: 多重验证（安全第一）

💡 使用技巧:
- 输入命令时不需要完整路径，小诺会自动识别
- 可以使用Tab键补全（如果支持）
- 所有操作都有日志记录，可追溯
- 遇到问题时输入 status 查看系统状态
        """
        return {
            "success": True,
            "message": help_text,
            "timestamp": datetime.now().isoformat()
        }

    def _display_result(self, result: dict[str, Any]):
        """显示执行结果"""
        print("\n" + "-"*50)

        if result.get("success"):
            print("✅ 操作成功!")
            if "message" in result:
                print(f"💬 {result['message']}")

            if "processor" in result:
                processor = result["processor"]
                mode = result.get("mode", "")
                if mode:
                    print(f"🤖 处理器: {processor} ({mode})")
                else:
                    print(f"🤖 处理器: {processor}")

            if "duration" in result:
                print(f"⏱️ 耗时: {result['duration']:.3f}秒")

            # 显示结果数据
            if "result" in result and result["result"]:
                print("\n📊 结果:")
                self._display_data(result["result"])

            # 显示特殊信息
            if "processors" in result:
                print(f"👥 协作智能体: {', '.join(result['processors'])}")

            if "system_overview" in result:
                print("\n🎯 系统概览:")
                overview = result["system_overview"]
                print(f"   总智能体: {overview['total_agents']}")
                print(f"   运行中: {overview['active_agents']}")
                print(f"   空闲中: {overview['idle_agents']}")
                print(f"   等待任务: {overview['pending_tasks']}")
                print(f"   活动任务: {overview['active_tasks']}")

        else:
            print("❌ 操作失败!")
            print(f"💬 错误信息: {result.get('error', '未知错误')}")

            if "requires_dual_auth" in result and result["requires_dual_auth"]:
                print("🔒 此操作需要双重认证，已发起认证请求")

            if "requires_confirmation" in result and result["requires_confirmation"]:
                print("⚠️ 此操作需要额外确认，请谨慎操作")

        print("-"*50)

    def _display_data(self, data, indent=0):
        """显示数据（支持嵌套结构）"""
        prefix = "  " * indent

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    print(f"{prefix}{key}:")
                    self._display_data(value, indent + 1)
                else:
                    print(f"{prefix}{key}: {value}")

        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    print(f"{prefix}[{i}]:")
                    self._display_data(item, indent + 1)
                else:
                    print(f"{prefix}[{i}]: {item}")
        else:
            print(f"{prefix}{data}")

async def main():
    """主函数"""
    # 创建日志目录
    Path("logs").mkdir(exist_ok=True)

    # 创建并启动系统
    system = XiaonuoHybridSystem()

    try:
        await system.start()
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
    finally:
        await system.stop()

if __name__ == "__main__":
    asyncio.run(main())
