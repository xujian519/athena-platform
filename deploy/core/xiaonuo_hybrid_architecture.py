#!/usr/bin/env python3
"""
小诺混合架构控制器
Xiaonuo Hybrid Architecture Controller
实现小诺为主 + 专业智能体按需协作的混合架构
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OperationType(Enum):
    """操作类型枚举"""
    QUERY = "query"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BATCH = "batch"

class DataType(Enum):
    """数据类型枚举"""
    CUSTOMER = "customer"          # 客户资料
    PATENT = "patent"             # 专利相关
    IP_MANAGEMENT = "ip_management" # IP管理
    KNOWLEDGE_GRAPH = "knowledge_graph" # 知识图谱
    VECTOR_DATA = "vector_data"   # 向量数据
    PERFORMANCE = "performance"   # 性能指标
    CONFIG = "config"             # 配置信息
    FINANCE = "finance"           # 财务数据

class SecurityLevel(Enum):
    """安全级别枚举"""
    LOW = 1      # 基础操作
    MEDIUM = 2   # 专业操作
    HIGH = 3     # 敏感操作
    CRITICAL = 4 # 核心操作

@dataclass
class OperationRequest:
    """操作请求数据结构"""
    operation_type: OperationType
    data_type: DataType
    target: str  # 目标存储路径或ID
    data: dict[Any, Any] | None = None
    user: str = "爸爸"
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class StorageManager:
    """存储管理器 - 统一管理所有存储资源"""

    def __init__(self):
        self.storage_map = {
            DataType.CUSTOMER: {
                "path": "data/customer_data",
                "agent": "xiaonuo",
                "security_level": SecurityLevel.LOW,
                "databases": ["baochen_finance.db", "客户档案_*.json"]
            },
            DataType.PATENT: {
                "path": "data/patents",
                "agent": "xiaona",
                "security_level": SecurityLevel.MEDIUM,
                "databases": ["yunpat.db", "patent_legal_*"]
            },
            DataType.IP_MANAGEMENT: {
                "path": "services/yunxi-ip",
                "agent": "yunxi",
                "security_level": SecurityLevel.MEDIUM,
                "databases": ["baochen_ip.db"]
            },
            DataType.KNOWLEDGE_GRAPH: {
                "path": "data/knowledge_graph",
                "agent": "athena",
                "security_level": SecurityLevel.HIGH,
                "databases": ["knowledge_graph.db"]
            },
            DataType.VECTOR_DATA: {
                "path": "data/qdrant_storage",
                "agent": "athena",
                "security_level": SecurityLevel.MEDIUM,
                "databases": ["vectors_qdrant"]
            },
            DataType.PERFORMANCE: {
                "path": "data",
                "agent": "xiaonuo",
                "security_level": SecurityLevel.LOW,
                "databases": ["performance_metrics.db"]
            },
            DataType.CONFIG: {
                "path": "config",
                "agent": "xiaonuo",
                "security_level": SecurityLevel.HIGH,
                "databases": ["settings.json"]
            },
            DataType.FINANCE: {
                "path": "data",
                "agent": "xiaonuo",
                "security_level": SecurityLevel.HIGH,
                "databases": ["baochen_finance.db"]
            }
        }

    def get_storage_info(self, data_type: DataType) -> dict[str, Any]:
        """获取存储信息"""
        return self.storage_map.get(data_type, {})

class AgentManager:
    """智能体管理器 - 负责专业智能体的按需启动"""

    def __init__(self):
        self.agents = {
            "xiaonuo": {
                "name": "小诺",
                "role": "平台总调度官",
                "status": "active",
                "port": None,
                "capabilities": ["basic_operations", "coordination"]
            },
            "xiaona": {
                "name": "小娜·天秤女神",
                "role": "专利法律专家",
                "status": "inactive",
                "port": 8006,
                "startup_script": "services/xiaonuo/start_xiaona_legal_support.py"
            },
            "yunxi": {
                "name": "云熙·织女星",
                "role": "IP管理专家",
                "status": "inactive",
                "port": 8007,
                "startup_script": "services/yunxi-ip/yunxi_simple_api.py"
            },
            "athena": {
                "name": "Athena·智慧女神",
                "role": "平台核心智能体",
                "status": "inactive",
                "port": 8005,
                "startup_script": "core/athena_core_system.py"
            }
        }

    async def launch_agent(self, agent_name: str) -> bool:
        """按需启动专业智能体"""
        agent = self.agents.get(agent_name)
        if not agent:
            logger.error(f"未找到智能体: {agent_name}")
            return False

        if agent["status"] == "active":
            logger.info(f"智能体 {agent_name} 已在运行")
            return True

        try:
            logger.info(f"🚀 正在启动 {agent['name']} ({agent['role']})")
            # 这里添加实际的启动逻辑
            # subprocess.Popen([...]) 或 async subprocess
            agent["status"] = "active"
            logger.info(f"✅ {agent['name']} 启动成功")
            return True
        except Exception as e:
            logger.error(f"❌ 启动 {agent['name']} 失败: {e}")
            return False

    async def stop_agent(self, agent_name: str) -> bool:
        """停止专业智能体"""
        agent = self.agents.get(agent_name)
        if agent:
            agent["status"] = "inactive"
            logger.info(f"⏹️ {agent['name']} 已停止")
        return True

class HybridArchitectureController:
    """混合架构控制器 - 核心控制逻辑"""

    def __init__(self):
        self.storage_manager = StorageManager()
        self.agent_manager = AgentManager()
        self.operation_log = []

        # 配置操作复杂度阈值
        self.complexity_threshold = {
            OperationType.QUERY: 0.3,
            OperationType.CREATE: 0.5,
            OperationType.UPDATE: 0.6,
            OperationType.DELETE: 0.8,
            OperationType.BATCH: 0.9
        }

        # 配置需要双重验证的操作
        self.dual_verification_required = {
            (OperationType.DELETE, DataType.KNOWLEDGE_GRAPH),
            (OperationType.BATCH, DataType.PATENT),
            (OperationType.DELETE, DataType.CONFIG),
            (OperationType.UPDATE, DataType.CONFIG)
        }

    def calculate_complexity(self, request: OperationRequest) -> float:
        """计算操作复杂度"""
        base_complexity = self.complexity_threshold.get(request.operation_type, 0.5)

        # 根据数据类型调整复杂度
        type_multiplier = {
            DataType.CUSTOMER: 0.5,
            DataType.PERFORMANCE: 0.4,
            DataType.PATENT: 0.7,
            DataType.IP_MANAGEMENT: 0.7,
            DataType.KNOWLEDGE_GRAPH: 0.8,
            DataType.VECTOR_DATA: 0.6,
            DataType.CONFIG: 0.9,
            DataType.FINANCE: 0.8
        }

        complexity = base_complexity * type_multiplier.get(request.data_type, 0.5)

        # 根据数据大小调整
        if request.data:
            data_size = len(str(request.data))
            if data_size > 10000:  # 大数据量
                complexity *= 1.5
            elif data_size > 1000:  # 中等数据量
                complexity *= 1.2

        return min(complexity, 1.0)

    def determine_processing_strategy(self, request: OperationRequest) -> dict[str, Any]:
        """确定处理策略"""
        complexity = self.calculate_complexity(request)
        storage_info = self.storage_manager.get_storage_info(request.data_type)

        # 检查是否需要双重验证
        needs_dual_verification = (request.operation_type, request.data_type) in self.dual_verification_required

        strategy = {
            "complexity": complexity,
            "processing_mode": None,
            "primary_agent": None,
            "needs_specialist": False,
            "needs_dual_verification": needs_dual_verification,
            "security_level": storage_info.get("security_level", SecurityLevel.LOW)
        }

        # 确定处理模式
        if needs_dual_verification:
            strategy["processing_mode"] = "dual_verification"
            strategy["primary_agent"] = "xiaonuo"
            strategy["secondary_agent"] = storage_info.get("agent", "athena")
            strategy["needs_specialist"] = True
        elif complexity > 0.7:
            strategy["processing_mode"] = "specialist_agent"
            strategy["primary_agent"] = storage_info.get("agent", "xiaonuo")
            strategy["needs_specialist"] = True
        else:
            strategy["processing_mode"] = "xiaonuo_direct"
            strategy["primary_agent"] = "xiaonuo"
            strategy["needs_specialist"] = False

        return strategy

    async def process_request(self, request: OperationRequest) -> dict[str, Any]:
        """处理操作请求"""
        logger.info(f"🎯 收到请求: {request.operation_type.value} {request.data_type.value}")

        # 确定处理策略
        strategy = self.determine_processing_strategy(request)
        logger.info(f"📋 处理策略: {strategy['processing_mode']}")

        # 记录操作
        operation_record = {
            "request": request.__dict__,
            "strategy": strategy,
            "start_time": datetime.now().isoformat()
        }

        try:
            # 执行操作
            if strategy["processing_mode"] == "xiaonuo_direct":
                result = await self._process_xiaonuo_direct(request, strategy)
            elif strategy["processing_mode"] == "specialist_agent":
                result = await self._process_with_specialist(request, strategy)
            elif strategy["processing_mode"] == "dual_verification":
                result = await self._process_dual_verification(request, strategy)
            else:
                raise ValueError(f"未知的处理模式: {strategy['processing_mode']}")

            operation_record["success"] = True
            operation_record["result"] = result

        except Exception as e:
            logger.error(f"❌ 操作失败: {e}")
            operation_record["success"] = False
            operation_record["error"] = str(e)
            result = {"success": False, "error": str(e)}

        finally:
            operation_record["end_time"] = datetime.now().isoformat()
            self.operation_log.append(operation_record)

        return result

    async def _process_xiaonuo_direct(self, request: OperationRequest, strategy: dict) -> dict[str, Any]:
        """小诺直接处理"""
        logger.info(f"⚡ 小诺直接处理: {request.target}")

        # 这里实现小诺直接的操作逻辑
        # 例如：文件操作、简单数据库操作等

        return {
            "success": True,
            "message": "小诺已成功完成操作",
            "processor": "xiaonuo",
            "mode": "direct",
            "timestamp": datetime.now().isoformat()
        }

    async def _process_with_specialist(self, request: OperationRequest, strategy: dict) -> dict[str, Any]:
        """使用专业智能体处理"""
        specialist = strategy["primary_agent"]
        logger.info(f"🎓 启动专业智能体: {specialist}")

        # 启动专业智能体
        launch_success = await self.agent_manager.launch_agent(specialist)
        if not launch_success:
            raise RuntimeError(f"无法启动专业智能体: {specialist}")

        # 调用专业智能体的API
        result = await self._call_specialist_agent(specialist, request)

        # 完成后可以选择停止专业智能体
        # await self.agent_manager.stop_agent(specialist)

        return {
            "success": True,
            "message": f"{specialist}已成功处理操作",
            "processor": specialist,
            "mode": "specialist",
            "timestamp": datetime.now().isoformat(),
            "details": result
        }

    async def _process_dual_verification(self, request: OperationRequest, strategy: dict) -> dict[str, Any]:
        """双重验证处理"""
        primary = strategy["primary_agent"]
        secondary = strategy["secondary_agent"]

        logger.info(f"🔒 启动双重验证: {primary} + {secondary}")

        # 第一重验证 - 小诺
        primary_result = await self._process_xiaonuo_direct(request, strategy)

        # 第二重验证 - 专业智能体
        secondary_result = await self._process_with_specialist(request, strategy)

        # 比较两个结果
        if primary_result["success"] and secondary_result["success"]:
            return {
                "success": True,
                "message": "双重验证通过，操作已完成",
                "processors": [primary, secondary],
                "mode": "dual_verification",
                "primary_result": primary_result,
                "secondary_result": secondary_result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise RuntimeError("双重验证失败，操作被拒绝")

    async def _call_specialist_agent(self, agent_name: str, request: OperationRequest) -> dict[str, Any]:
        """调用专业智能体API"""
        # 这里实现具体的API调用逻辑
        # 可以是HTTP请求、进程间通信等

        self.agent_manager.agents.get(agent_name, {})

        # 模拟API调用
        await asyncio.sleep(0.1)  # 模拟网络延迟

        return {
            "agent": agent_name,
            "operation": request.operation_type.value,
            "target": request.target,
            "processed": True
        }

    def get_operation_statistics(self) -> dict[str, Any]:
        """获取操作统计信息"""
        total_operations = len(self.operation_log)
        successful_ops = sum(1 for op in self.operation_log if op.get("success", False))

        mode_stats = {}
        for op in self.operation_log:
            mode = op.get("strategy", {}).get("processing_mode", "unknown")
            mode_stats[mode] = mode_stats.get(mode, 0) + 1

        return {
            "total_operations": total_operations,
            "successful_operations": successful_ops,
            "success_rate": successful_ops / total_operations if total_operations > 0 else 0,
            "processing_modes": mode_stats,
            "last_operation": self.operation_log[-1] if self.operation_log else None
        }

# 使用示例
async def main():
    """主函数 - 演示混合架构的使用"""
    controller = HybridArchitectureController()

    print("🌸 小诺混合架构系统启动")
    print("=" * 50)

    # 示例操作
    test_requests = [
        OperationRequest(
            operation_type=OperationType.QUERY,
            data_type=DataType.CUSTOMER,
            target="查询客户资料"
        ),
        OperationRequest(
            operation_type=OperationType.CREATE,
            data_type=DataType.PATENT,
            target="创建专利记录",
            data={"patent_name": "测试专利", "applicant": "测试申请人"}
        ),
        OperationRequest(
            operation_type=OperationType.DELETE,
            data_type=DataType.CONFIG,
            target="删除核心配置"
        )
    ]

    for request in test_requests:
        print(f"\n🎯 处理请求: {request.operation_type.value} - {request.data_type.value}")
        result = await controller.process_request(request)
        print(f"✅ 结果: {result['message']}")
        print(f"📊 处理模式: {result.get('mode', 'N/A')}")

    # 显示统计信息
    stats = controller.get_operation_statistics()
    print("\n📈 操作统计:")
    print(f"   总操作数: {stats['total_operations']}")
    print(f"   成功率: {stats['success_rate']:.2%}")
    print(f"   处理模式分布: {stats['processing_modes']}")

if __name__ == "__main__":
    asyncio.run(main())
