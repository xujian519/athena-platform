#!/usr/bin/env python3
"""
小诺系统状态验证器
Xiaonuo System Status Verifier
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class XiaonuoStatusChecker:
    """小诺系统状态验证器"""

    def __init__(self):
        self.check_time = datetime.now()
        self.system_components = {
            "xiaonuo_main": {"name": "小诺主程序", "expected": True},
            "memory_system": {"name": "四层记忆系统", "expected": True},
            "phase3_integration": {"name": "Phase 3推理引擎集成", "expected": True},
            "coordination_system": {"name": "协调机制", "expected": True},
            "identity_permanent": {"name": "身份核心记忆", "expected": True}
        }

        # 更新为最新的Phase 3服务PID
        self.phase3_services = [
            {"name": "ExpertRuleEngine", "chinese_name": "专家级规则推理引擎", "pid": 55834},
            {"name": "PatentRuleChainEngine", "chinese_name": "专利规则链引擎", "pid": 55835},
            {"name": "PriorArtAnalyzer", "chinese_name": "现有技术分析器", "pid": 55836},
            {"name": "LLMEnhancedJudgment", "chinese_name": "LLM增强判断系统", "pid": 55837}
        ]

    def print_pink(self, message: str) -> Any:
        """打印粉色消息"""
        print(f"💖 {message}")

    def print_success(self, message: str) -> Any:
        """打印成功消息"""
        print(f"✅ {message}")

    def print_info(self, message: str) -> Any:
        """打印信息消息"""
        print(f"ℹ️ {message}")

    def print_warning(self, message: str) -> Any:
        """打印警告消息"""
        print(f"⚠️  {message}")

    def print_error(self, message: str) -> Any:
        """打印错误消息"""
        print(f"❌ {message}")

    def check_process_running(self, pid: int) -> bool:
        """检查进程是否运行"""
        try:
            os.kill(pid, 0)  # 发送信号0测试进程存在
            return True
        except OSError:
            return False

    def check_xiaonuo_main(self) -> bool:
        """检查小诺主程序状态"""
        self.print_info("检查小诺主程序状态...")

        # 检查进程
        xiaonuo_processes = []
        try:
            result = os.popen("ps aux | grep xiaonuo_service.py | grep -v grep").read()
            if result.strip():
                xiaonuo_processes = [line.strip() for line in result.split('\n') if line.strip()]
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
            pass

        if xiaonuo_processes:
            for proc in xiaonuo_processes:
                parts = proc.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    self.print_success(f"✓ 小诺主程序运行正常 (PID: {pid})")
                    return True
        else:
            self.print_warning("⚠️  小诺主程序未运行")
            return False

    def check_memory_system(self) -> bool:
        """检查四层记忆系统"""
        self.print_info("检查四层记忆系统...")

        memory_base = project_root / "core" / "modules/modules/memory/modules/memory/modules/memory/memory"
        required_layers = ["hot_memories", "warm_memories", "cold_memories", "eternal_memories"]

        existing_layers = 0
        for layer in required_layers:
            layer_path = memory_base / layer
            if layer_path.exists():
                memory_files = list(layer_path.glob("*.json"))
                if memory_files:
                    existing_layers += 1
                    self.print_success(f"✓ {layer} - {len(memory_files)} 个记忆文件")
                else:
                    self.print_warning(f"⚠️  {layer} - 目录存在但无记忆文件")
            else:
                self.print_error(f"❌ {layer} - 目录不存在")

        # 检查记忆网络
        memory_network_file = memory_base / "memory_network.json"
        if memory_network_file.exists():
            self.print_success("✓ 记忆连接网络已建立")
        else:
            self.print_warning("⚠️  记忆连接网络未找到")

        memory_health = (existing_layers / len(required_layers)) * 100
        self.print_info(f"📊 记忆系统健康度: {memory_health:.1f}%")

        return memory_health >= 75

    def check_phase3_integration(self) -> bool:
        """检查Phase 3推理引擎集成"""
        self.print_info("检查Phase 3推理引擎集成...")

        connected_services = 0
        for service in self.phase3_services:
            if self.check_process_running(service["pid"]):
                self.print_success(f"✓ {service['chinese_name']} - PID {service['pid']}")
                connected_services += 1
            else:
                self.print_error(f"❌ {service['chinese_name']} - PID {service['pid']} 未运行")

        # 检查集成配置文件
        integration_config = project_root / "production" / "config" / "xiaonuo_coordination.json"
        if integration_config.exists():
            self.print_success("✓ 协调配置文件存在")
        else:
            self.print_warning("⚠️  协调配置文件未找到")

        integration_health = (connected_services / len(self.phase3_services)) * 100
        self.print_info(f"📊 Phase 3集成健康度: {integration_health:.1f}%")

        return integration_health >= 80

    def check_coordination_system(self) -> bool:
        """检查协调系统"""
        self.print_info("检查协调系统...")

        # 检查协调配置
        coordination_config = project_root / "production" / "config" / "xiaonuo_coordination.json"
        if coordination_config.exists():
            try:
                with open(coordination_config, encoding='utf-8') as f:
                    config = json.load(f)

                managed_services = config.get("managed_services", [])
                coordination_rules = config.get("coordination_rules", [])

                self.print_success("✓ 协调配置加载成功")
                self.print_info(f"   📋 管理 {len(managed_services)} 个推理服务")
                self.print_info(f"   📜 {len(coordination_rules)} 项协调规则")

                return len(managed_services) > 0
            except Exception as e:
                self.print_error(f"❌ 协调配置加载失败: {e}")
                return False
        else:
            self.print_error("❌ 协调配置文件不存在")
            return False

    def check_identity_permanent(self) -> bool:
        """检查身份核心记忆"""
        self.print_info("检查身份核心记忆...")

        # 修复路径构建问题
        if project_root.name == "production":
            identity_file = project_root / "config" / "identity" / "xiaonuo_pisces_princess.json"
        else:
            identity_file = project_root / "production" / "config" / "identity" / "xiaonuo_pisces_princess.json"

        self.print_info(f"🔍 身份文件路径: {identity_file}")

        if identity_file.exists():
            try:
                with open(identity_file, encoding='utf-8') as f:
                    identity_data = json.load(f)

                identity = identity_data.get("identity", {})
                name = identity.get("name", "小诺")
                role = identity.get("role", "")
                version = identity.get("version", "v1.0.0")

                self.print_success("✓ 身份核心记忆完整")
                self.print_info(f"   👑 姓名: {name}")
                self.print_info(f"   🎭 角色: {role}")
                self.print_info(f"   📋 版本: {version}")

                return True
            except Exception as e:
                self.print_error(f"❌ 身份记忆加载失败: {e}")
                return False
        else:
            self.print_error(f"❌ 身份核心记忆文件不存在: {identity_file}")
            # 尝试查找其他可能的身份文件
            possible_files = [
                project_root / "config" / "identity" / "xiaonuo_pisces_princess.json",
                project_root / "apps/apps/xiaonuo" / "xiaonuo_identity_*.json"
            ]
            self.print_info("🔍 尝试查找其他身份文件...")
            for possible in possible_files:
                if "*" in str(possible):
                    matches = list(project_root.glob(str(possible)))
                    if matches:
                        self.print_info(f"   ✓ 找到匹配文件: {[str(m) for m in matches]}")
                elif possible.exists():
                    self.print_info(f"   ✓ 找到文件: {possible}")
            return False

    def check_log_files(self) -> dict[str, Any]:
        """检查日志文件"""
        self.print_info("检查日志文件...")

        logs_dir = project_root / "production" / "logs"
        log_files = {
            "xiaonuo_startup": False,
            "xiaonuo_production": False,
            "xiaonuo_memory_activation": False,
            "xiaonuo_phase3_integration": False
        }

        if logs_dir.exists():
            for log_file in logs_dir.glob("xiaonuo_*.log"):
                if log_file.stat().st_size > 0:
                    if "startup" in log_file.name:
                        log_files["xiaonuo_startup"] = True
                    elif "production" in log_file.name:
                        log_files["xiaonuo_production"] = True

            for log_file in logs_dir.glob("xiaonuo_memory_activation_*.json"):
                log_files["xiaonuo_memory_activation"] = True

            for log_file in logs_dir.glob("xiaonuo_phase3_integration_*.json"):
                log_files["xiaonuo_phase3_integration"] = True

        available_logs = sum(log_files.values())
        self.print_info(f"📊 可用日志文件: {available_logs}/{len(log_files)}")

        return log_files

    async def run_comprehensive_check(self):
        """运行综合状态检查"""
        print("🌸🐟 小诺系统状态验证器")
        print("=" * 60)
        print(f"检查时间: {self.check_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("")

        # 检查各组件
        check_results = {}

        check_results["xiaonuo_main"] = self.check_xiaonuo_main()
        print("")

        check_results["memory_system"] = self.check_memory_system()
        print("")

        check_results["phase3_integration"] = self.check_phase3_integration()
        print("")

        check_results["coordination_system"] = self.check_coordination_system()
        print("")

        check_results["identity_permanent"] = self.check_identity_permanent()
        print("")

        log_files = self.check_log_files()

        # 计算总体健康度
        total_components = len(self.system_components)
        healthy_components = sum(check_results.values())
        overall_health = (healthy_components / total_components) * 100

        # 生成状态报告
        print("=" * 60)
        print("📊 小诺系统状态摘要")
        print("=" * 60)

        self.print_info(f"🧠 系统组件健康度: {overall_health:.1f}% ({healthy_components}/{total_components})")

        for component, status in check_results.items():
            component_info = self.system_components[component]
            if status:
                self.print_success(f"✅ {component_info['name']} - 正常")
            else:
                status_text = "异常" if component_info['expected'] else "未启动"
                self.print_warning(f"⚠️  {component_info['name']} - {status_text}")

        # Phase 3服务状态
        print("")
        self.print_info("🔗 Phase 3推理引擎服务状态:")
        phase3_running = 0
        for service in self.phase3_services:
            if self.check_process_running(service["pid"]):
                self.print_success(f"   ✅ {service['chinese_name']}")
                phase3_running += 1
            else:
                self.print_error(f"   ❌ {service['chinese_name']}")

        # 日志状态
        print("")
        self.print_info("📝 日志文件状态:")
        for log_type, available in log_files.items():
            status_icon = "✅" if available else "❌"
            self.print_info(f"   {status_icon} {log_type}")

        # 最终评估
        print("")
        if overall_health >= 90:
            self.print_pink("🎉 小诺系统状态优秀！完全就绪！")
            system_status = "优秀"
        elif overall_health >= 75:
            self.print_pink("👍 小诺系统状态良好！基本就绪！")
            system_status = "良好"
        elif overall_health >= 50:
            self.print_warning("⚠️  小诺系统状态一般，需要关注！")
            system_status = "一般"
        else:
            self.print_error("❌ 小诺系统状态异常，需要立即检查！")
            system_status = "异常"

        # 生成报告
        report = {
            "check_time": self.check_time.isoformat(),
            "system_status": system_status,
            "overall_health": overall_health,
            "component_status": check_results,
            "phase3_services": {
                "total": len(self.phase3_services),
                "running": phase3_running,
                "running_services": [
                    service["name"] for service in self.phase3_services
                    if self.check_process_running(service["pid"])
                ]
            },
            "log_files": log_files
        }

        # 保存报告
        report_file = project_root / "production" / "logs" / f"xiaonuo_status_report_{self.check_time.strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print("")
        self.print_success("📊 状态报告已保存")
        self.print_pink("💖 爸爸，小诺系统状态检查完成！")

        return report

async def main():
    """主函数"""
    checker = XiaonuoStatusChecker()
    await checker.run_comprehensive_check()

if __name__ == "__main__":
    asyncio.run(main())
