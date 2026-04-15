#!/usr/bin/env python3
"""
Athena生产环境模型服务健康检查脚本
Production Model Service Health Check Script

功能：
1. 检查模型服务状态
2. 验证模型加载情况
3. 测试推理性能
4. 检查缓存系统
5. 生成健康报告

作者: Athena AI
创建时间: 2025-12-29
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
sys.path.insert(0, str(PROJECT_ROOT))

# 颜色输出
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


def print_success(msg: str) -> Any:
    print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")


def print_error(msg: str) -> Any:
    print(f"{Colors.RED}[✗]{Colors.NC} {msg}")


def print_warning(msg: str) -> Any:
    print(f"{Colors.YELLOW}[⚠]{Colors.NC} {msg}")


def print_info(msg: str) -> Any:
    print(f"{Colors.BLUE}[i]{Colors.NC} {msg}")


def print_section(title: str) -> Any:
    print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
    print(f"{Colors.CYAN}{title}{Colors.NC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.NC}")


class ModelHealthChecker:
    """模型服务健康检查器"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "overall_status": "unknown"
        }

    def check_pytorch(self) -> dict[str, Any]:
        """检查PyTorch环境"""
        print_info("检查PyTorch环境...")

        try:
            import torch

            version = torch.__version__
            mps_available = torch.backends.mps.is_available()
            cuda_available = torch.cuda.is_available()

            device = "cpu"
            if mps_available:
                device = "mps"
            elif cuda_available:
                device = "cuda"

            result = {
                "status": "ok",
                "version": version,
                "device": device,
                "mps_available": mps_available,
                "cuda_available": cuda_available
            }

            print_success(f"PyTorch {version} - 设备: {device}")
            return result

        except ImportError as e:
            print_error(f"PyTorch导入失败: {e}")
            return {"status": "error", "error": str(e)}

    def check_model_loader(self) -> dict[str, Any]:
        """检查模型加载器"""
        print_info("检查模型加载器...")

        try:
            from core.models.athena_model_loader import AthenaModelLoader, get_device, load_model

            device = get_device()
            print_success(f"AthenaModelLoader导入成功 - 设备: {device}")

            return {
                "status": "ok",
                "device": device,
                "loader_available": True
            }

        except ImportError as e:
            print_error(f"模型加载器导入失败: {e}")
            return {"status": "error", "error": str(e)}

    def check_model_configs(self) -> dict[str, Any]:
        """检查模型配置文件"""
        print_info("检查模型配置文件...")

        models_to_check = [
            ("BAAI/bge-m3", 768),
            ("bge-large-zh-v1.5", 1024),
            ("bge-reranker-large", 1024)
        ]

        results = []
        all_exist = True

        for model_name, expected_dim in models_to_check:
            config_path = self.project_root / f"models/converted/{model_name}/1_Pooling/config.json"

            if config_path.exists():
                print_success(f"{model_name} - 配置存在")
                results.append({
                    "model": model_name,
                    "config_exists": True,
                    "expected_dimension": expected_dim
                })
            else:
                print_error(f"{model_name} - 配置缺失")
                results.append({
                    "model": model_name,
                    "config_exists": False,
                    "expected_dimension": expected_dim
                })
                all_exist = False

        return {
            "status": "ok" if all_exist else "degraded",
            "models": results
        }

    def check_model_loading(self) -> dict[str, Any]:
        """检查模型加载"""
        print_info("测试模型加载...")

        try:
            from core.models.athena_model_loader import load_model

            start_time = time.time()
            model = load_model("BAAI/bge-m3")
            load_time = time.time() - start_time

            # 测试推理
            test_texts = ["测试文本1", "测试文本2", "测试文本3"]
            start_time = time.time()
            embeddings = model.encode(test_texts, show_progress_bar=False)
            inference_time = time.time() - start_time

            dimension = len(embeddings[0])
            throughput = len(test_texts) / inference_time

            print_success(f"模型加载成功 - {load_time:.2f}秒")
            print_success(f"推理测试 - {inference_time:.2f}秒, {throughput:.1f} 文本/秒")
            print_success(f"向量维度 - {dimension}")

            return {
                "status": "ok",
                "load_time_seconds": round(load_time, 2),
                "inference_time_seconds": round(inference_time, 2),
                "dimension": dimension,
                "throughput_per_sec": round(throughput, 1)
            }

        except Exception as e:
            print_error(f"模型加载失败: {e}")
            return {"status": "error", "error": str(e)}

    def check_batch_processor(self) -> dict[str, Any]:
        """检查批处理器"""
        print_info("检查批处理器...")

        try:
            from core.models.athena_model_loader import load_model
            from core.performance.batch_processor import BatchProcessor

            model = load_model("BAAI/bge-m3")
            device = model.device if hasattr(model, 'device') else 'cpu'

            processor = BatchProcessor(
                model=model,
                batch_size=32,
                timeout_ms=50,
                device=device
            )

            stats = processor.get_stats()

            print_success("BatchProcessor导入成功")
            print_success("配置: batch_size=32, timeout=50ms")

            return {
                "status": "ok",
                "batch_size": 32,
                "timeout_ms": 50,
                "running": stats.get("running", False)
            }

        except ImportError as e:
            print_error(f"批处理器导入失败: {e}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            print_error(f"批处理器初始化失败: {e}")
            return {"status": "error", "error": str(e)}

    def check_cache_system(self) -> dict[str, Any]:
        """检查缓存系统"""
        print_info("检查缓存系统...")

        try:
            from core.performance.model_cache import get_cache_manager

            cache = get_cache_manager(
                l1_max_size_mb=500,
                enable_l2=False,
                enable_l3=True
            )

            # 测试缓存读写
            test_key = ("test_model", "test_text")
            test_value = [0.1] * 768

            cache.set("test_model", "test_text", test_value)
            retrieved = cache.get("test_model", "test_text")

            cache_hit = retrieved is not None

            stats = cache.get_stats()

            if cache_hit:
                print_success("缓存读写测试通过")
                print_success(f"L1缓存: {stats.get('l1_size_mb', 0)}MB / {stats.get('l1_max_mb', 0)}MB")

            return {
                "status": "ok" if cache_hit else "degraded",
                "l1_max_mb": stats.get("l1_max_mb", 0),
                "l1_current_mb": stats.get("l1_size_mb", 0),
                "cache_test_passed": cache_hit
            }

        except ImportError as e:
            print_error(f"缓存系统导入失败: {e}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            print_error(f"缓存系统初始化失败: {e}")
            return {"status": "error", "error": str(e)}

    def check_model_service(self) -> dict[str, Any]:
        """检查模型服务"""
        print_info("检查模型服务...")

        service_file = self.project_root / "production/services/model_service.py"

        if not service_file.exists():
            print_error("模型服务文件不存在")
            return {"status": "error", "error": "Service file not found"}

        try:
            from production.services.model_service import ModelService

            print_success("ModelService导入成功")

            return {
                "status": "ok",
                "service_available": True
            }

        except ImportError as e:
            print_error(f"模型服务导入失败: {e}")
            return {"status": "error", "error": str(e)}

    def check_production_config(self) -> dict[str, Any]:
        """检查生产配置"""
        print_info("检查生产配置...")

        config_file = self.project_root / "config/environments/production/model_config.yaml"

        if not config_file.exists():
            print_error("生产配置文件不存在")
            return {"status": "error", "error": "Config file not found"}

        try:
            import yaml

            with open(config_file, encoding='utf-8') as f:
                config = yaml.safe_load(f)

            environment = config.get('environment', 'unknown')
            batch_enabled = config.get('batch_processing', {}).get('enabled', False)
            cache_enabled = config.get('cache', {}).get('l1_memory', {}).get('enabled', False)

            print_success(f"环境: {environment}")
            print_success(f"批处理: {'启用' if batch_enabled else '禁用'}")
            print_success(f"缓存: {'启用' if cache_enabled else '禁用'}")

            return {
                "status": "ok",
                "environment": environment,
                "batch_processing_enabled": batch_enabled,
                "cache_enabled": cache_enabled
            }

        except Exception as e:
            print_error(f"配置文件读取失败: {e}")
            return {"status": "error", "error": str(e)}

    async def run_all_checks(self) -> dict[str, Any]:
        """运行所有健康检查"""
        print_section("Athena模型服务健康检查")

        # 执行各项检查
        self.results["checks"]["pytorch"] = self.check_pytorch()
        self.results["checks"]["model_loader"] = self.check_model_loader()
        self.results["checks"]["model_configs"] = self.check_model_configs()
        self.results["checks"]["model_loading"] = self.check_model_loading()
        self.results["checks"]["batch_processor"] = self.check_batch_processor()
        self.results["checks"]["cache_system"] = self.check_cache_system()
        self.results["checks"]["model_service"] = self.check_model_service()
        self.results["checks"]["production_config"] = self.check_production_config()

        # 计算总体状态
        error_count = sum(1 for c in self.results["checks"].values() if c.get("status") == "error")
        degraded_count = sum(1 for c in self.results["checks"].values() if c.get("status") == "degraded")

        if error_count > 0:
            self.results["overall_status"] = "error"
        elif degraded_count > 0:
            self.results["overall_status"] = "degraded"
        else:
            self.results["overall_status"] = "healthy"

        return self.results

    def print_summary(self) -> Any:
        """打印健康检查摘要"""
        print_section("健康检查摘要")

        status = self.results["overall_status"]

        if status == "healthy":
            print_success("总体状态: 健康 (所有检查通过)")
        elif status == "degraded":
            print_warning("总体状态: 降级 (部分检查未通过)")
        else:
            print_error("总体状态: 错误 (有检查失败)")

        print()
        print("详细结果:")
        for name, result in self.results["checks"].items():
            status_icon = "✓" if result.get("status") == "ok" else ("✗" if result.get("status") == "error" else "⚠")
            status_color = Colors.GREEN if result.get("status") == "ok" else (Colors.RED if result.get("status") == "error" else Colors.YELLOW)
            print(f"  {status_color}{status_icon}{Colors.NC} {name}")

    def save_report(self) -> None:
        """保存健康检查报告"""
        report_dir = self.project_root / "logs/production"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"model_health_check_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print_info(f"报告已保存: {report_file}")


async def main():
    """主函数"""
    checker = ModelHealthChecker()

    # 运行检查
    await checker.run_all_checks()

    # 打印摘要
    checker.print_summary()

    # 保存报告
    checker.save_report()

    # 返回退出码
    status = checker.results["overall_status"]
    if status == "healthy":
        return 0
    elif status == "degraded":
        return 1
    else:
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
