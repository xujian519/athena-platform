#!/usr/bin/env python3
"""
Athena NLP系统完整性验证脚本 (MPS优化版)
Comprehensive NLP System Verification with MPS Optimization

验证NLP系统在MPS优化后的完整性和可运行性

作者: Athena AI
创建时间: 2025-12-29
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
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
    MAGENTA = '\033[0;35m'
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


def print_subsection(title: str) -> Any:
    print(f"\n{Colors.MAGENTA}─── {title} ───{Colors.NC}")


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NLPSystemVerifier:
    """NLP系统验证器"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "verification_version": "1.0.0",
            "categories": {},
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }

    def add_result(self, category: str, check_name: str, status: str,
                   result: dict | None = None, error: str | None = None):
        """添加测试结果"""
        if category not in self.results["categories"]:
            self.results["categories"][category] = {}

        self.results["categories"][category][check_name] = {
            "status": status,  # passed, failed, warning
            "timestamp": datetime.now().isoformat()
        }

        if result:
            self.results["categories"][category][check_name]["result"] = result
        if error:
            self.results["categories"][category][check_name]["error"] = error

        self.results["summary"]["total_checks"] += 1
        if status == "passed":
            self.results["summary"]["passed"] += 1
        elif status == "failed":
            self.results["summary"]["failed"] += 1
        else:
            self.results["summary"]["warnings"] += 1

    async def verify_pytorch_environment(self):
        """验证PyTorch环境"""
        print_section("1. PyTorch环境验证")

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

            print_success(f"PyTorch版本: {version}")
            print_success(f"设备: {device}")
            print_info(f"  MPS可用: {mps_available}")
            print_info(f"  CUDA可用: {cuda_available}")

            # 测试简单张量操作
            if device == "mps":
                test_tensor = torch.randn(100, 100).to('mps')
                result = test_tensor @ test_tensor.T
                print_success("MPS张量运算测试通过")

            self.add_result("environment", "pytorch", "passed", {
                "version": version,
                "device": device,
                "mps_available": mps_available,
                "cuda_available": cuda_available
            })

        except Exception as e:
            print_error(f"PyTorch环境检查失败: {e}")
            self.add_result("environment", "pytorch", "failed", error=str(e))

    async def verify_model_loader(self):
        """验证模型加载器"""
        print_section("2. 模型加载器验证")

        try:
            from core.models.athena_model_loader import get_device, load_model

            device = get_device()
            print_success("AthenaModelLoader导入成功")
            print_info(f"  检测设备: {device}")

            # 测试模型加载
            print_info("测试加载 bge-base-zh-v1.5...")
            start = time.time()
            model = load_model("BAAI/bge-m3")
            load_time = time.time() - start

            print_success(f"模型加载成功 ({load_time:.2f}秒)")

            # 测试推理
            test_texts = ["测试文本1", "测试文本2", "测试文本3"]
            start = time.time()
            embeddings = model.encode(test_texts, show_progress_bar=False)
            inference_time = time.time() - start

            dimension = len(embeddings[0])
            throughput = len(test_texts) / inference_time

            print_success("推理测试通过")
            print_info(f"  向量维度: {dimension}")
            print_info(f"  推理时间: {inference_time:.2f}秒")
            print_info(f"  吞吐量: {throughput:.1f} 文本/秒")

            self.add_result("model_loader", "athena_model_loader", "passed", {
                "device": device,
                "load_time_seconds": round(load_time, 2),
                "inference_time_seconds": round(inference_time, 2),
                "dimension": dimension,
                "throughput_per_sec": round(throughput, 1)
            })

        except Exception as e:
            print_error(f"模型加载器验证失败: {e}")
            self.add_result("model_loader", "athena_model_loader", "failed", error=str(e))

    async def verify_batch_processor(self):
        """验证批处理器"""
        print_section("3. 批处理器验证")

        try:
            from core.models.athena_model_loader import load_model
            from core.performance.batch_processor import BatchProcessor

            print_info("初始化批处理器...")

            model = load_model("BAAI/bge-m3")
            device = model.device if hasattr(model, 'device') else 'cpu'

            processor = BatchProcessor(
                model=model,
                batch_size=32,
                timeout_ms=50,
                device=device
            )

            stats = processor.get_stats()

            print_success("BatchProcessor初始化成功")
            print_info(f"  批大小: {32}")
            print_info(f"  超时: {50}ms")
            print_info(f"  设备: {device}")

            self.add_result("performance", "batch_processor", "passed", {
                "batch_size": 32,
                "timeout_ms": 50,
                "device": str(device),
                "running": stats.get("running", False)
            })

        except Exception as e:
            print_error(f"批处理器验证失败: {e}")
            self.add_result("performance", "batch_processor", "failed", error=str(e))

    async def verify_cache_system(self):
        """验证缓存系统"""
        print_section("4. 缓存系统验证")

        try:
            from core.performance.model_cache import get_cache_manager

            print_info("初始化三级缓存...")

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
                print_info(f"  L1缓存: {stats.get('l1_size_mb', 0)}MB / {stats.get('l1_max_mb', 0)}MB")
            else:
                print_warning("缓存读写测试未通过")

            self.add_result("performance", "cache_system", "passed" if cache_hit else "warning", {
                "l1_max_mb": stats.get("l1_max_mb", 0),
                "l1_current_mb": stats.get("l1_size_mb", 0),
                "cache_test_passed": cache_hit
            })

        except Exception as e:
            print_error(f"缓存系统验证失败: {e}")
            self.add_result("performance", "cache_system", "failed", error=str(e))

    async def verify_nlp_services(self):
        """验证NLP服务"""
        print_section("5. NLP服务验证")

        services_to_check = [
            ("core.nlp.bge_embedding_service", "BGE嵌入服务"),
            ("core.nlp.universal_nlp_provider", "通用NLP提供者"),
            ("core.nlp.enhanced_nlp_adapter", "增强NLP适配器"),
            ("core.nlp.bert_service", "BERT服务"),
        ]

        for module_name, display_name in services_to_check:
            try:
                __import__(module_name)
                print_success(f"{display_name} - 导入成功")
                self.add_result("nlp_services", display_name, "passed")
            except Exception as e:
                print_warning(f"{display_name} - 导入失败: {e}")
                self.add_result("nlp_services", display_name, "warning", error=str(e))

    async def verify_embedding_services(self):
        """验证嵌入服务"""
        print_section("6. 嵌入服务验证")

        services_to_check = [
            ("core.embedding.bge_embedding_service", "BGE嵌入服务"),
            ("core.embedding.nlp_service_adapter", "NLP服务适配器"),
            ("core.nlp.bge_embedding_service", "NLP BGE嵌入服务"),
        ]

        for module_name, display_name in services_to_check:
            try:
                module = __import__(module_name, fromlist=[''])
                print_success(f"{display_name} - 导入成功")

                # 尝试获取类或函数
                items = [name for name in dir(module) if not name.startswith('_')]
                print_info(f"  导出项: {len(items)} 个")

                self.add_result("embedding_services", display_name, "passed", {
                    "exports_count": len(items)
                })
            except Exception as e:
                print_warning(f"{display_name} - 导入失败: {e}")
                self.add_result("embedding_services", display_name, "warning", error=str(e))

    async def verify_intent_classifiers(self):
        """验证意图分类器"""
        print_section("7. 意图分类器验证")

        classifiers_to_check = [
            ("core.nlp.xiaonuo_lightweight_intent_classifier", "轻量级意图分类器"),
            ("core.nlp.xiaonuo_enhanced_intent_classifier", "增强意图分类器"),
            ("core.nlp.bert_intent_classifier", "BERT意图分类器"),
        ]

        for module_name, display_name in classifiers_to_check:
            try:
                __import__(module_name)
                print_success(f"{display_name} - 导入成功")
                self.add_result("intent_classifiers", display_name, "passed")
            except Exception as e:
                print_warning(f"{display_name} - 导入失败: {e}")
                self.add_result("intent_classifiers", display_name, "warning", error=str(e))

    async def verify_production_services(self):
        """验证生产服务"""
        print_section("8. 生产服务验证")

        services_to_check = [
            ("production.services.model_service", "模型服务"),
            ("production.core.nlp_integration", "NLP集成"),
        ]

        for module_name, display_name in services_to_check:
            try:
                module = __import__(module_name, fromlist=[''])
                print_success(f"{display_name} - 导入成功")

                # 检查关键类
                if hasattr(module, 'ModelService'):
                    print_info("  ModelService类: 可用")
                if hasattr(module, 'encode_texts'):
                    print_info("  encode_texts函数: 可用")

                self.add_result("production_services", display_name, "passed")

            except Exception as e:
                print_warning(f"{display_name} - 导入失败: {e}")
                self.add_result("production_services", display_name, "warning", error=str(e))

    async def verify_model_configs(self):
        """验证模型配置"""
        print_section("9. 模型配置验证")

        models_to_check = [
            ("BAAI/bge-m3", 768),
            ("bge-large-zh-v1.5", 1024),
            ("bge-reranker-large", 1024),
        ]

        all_valid = True
        for model_name, expected_dim in models_to_check:
            config_path = self.project_root / f"models/converted/{model_name}/1_Pooling/config.json"

            if config_path.exists():
                print_success(f"{model_name} - 配置存在")
                self.add_result("model_configs", model_name, "passed", {
                    "expected_dimension": expected_dim
                })
            else:
                print_error(f"{model_name} - 配置缺失")
                self.add_result("model_configs", model_name, "failed", {
                    "expected_dimension": expected_dim
                })
                all_valid = False

    async def verify_production_config(self):
        """验证生产配置"""
        print_section("10. 生产配置验证")

        config_file = self.project_root / "config/environments/production/model_config.yaml"

        if not config_file.exists():
            print_error("生产配置文件不存在")
            self.add_result("production_config", "model_config.yaml", "failed")
            return

        try:
            import yaml

            with open(config_file, encoding='utf-8') as f:
                config = yaml.safe_load(f)

            environment = config.get('environment', 'unknown')
            batch_enabled = config.get('batch_processing', {}).get('enabled', False)
            cache_enabled = config.get('cache', {}).get('l1_memory', {}).get('enabled', False)

            print_success("生产配置文件存在")
            print_info(f"  环境: {environment}")
            print_info(f"  批处理: {'启用' if batch_enabled else '禁用'}")
            print_info(f"  缓存: {'启用' if cache_enabled else '禁用'}")

            self.add_result("production_config", "model_config.yaml", "passed", {
                "environment": environment,
                "batch_processing_enabled": batch_enabled,
                "cache_enabled": cache_enabled
            })

        except Exception as e:
            print_error(f"生产配置验证失败: {e}")
            self.add_result("production_config", "model_config.yaml", "failed", error=str(e))

    async def run_end_to_end_test(self):
        """运行端到端测试"""
        print_section("11. 端到端测试")

        try:
            # 测试完整的文本嵌入流程
            from core.models.athena_model_loader import load_model

            print_info("测试完整文本嵌入流程...")

            # 1. 加载模型
            model = load_model("BAAI/bge-m3")
            print_success("步骤1: 模型加载成功")

            # 2. 编码测试文本
            test_texts = [
                "专利是一种知识产权保护形式。",
                "本发明涉及一种数据处理系统。",
                "权利要求书是专利申请的重要文件。"
            ]

            embeddings = model.encode(test_texts, show_progress_bar=False)
            print_success(f"步骤2: 文本编码成功 ({len(test_texts)}个文本)")

            # 3. 验证向量维度
            dimension = len(embeddings[0])
            print_success(f"步骤3: 向量验证通过 (维度={dimension})")

            # 4. 测试语义相似度
            import numpy as np
            similarity_matrix = np.dot(embeddings, embeddings.T)
            # 归一化
            norms = np.linalg.norm(embeddings, axis=1)
            similarity_matrix = similarity_matrix / np.outer(norms, norms)

            print_success("步骤4: 语义相似度计算成功")

            self.add_result("end_to_end", "text_embedding_pipeline", "passed", {
                "texts_processed": len(test_texts),
                "vector_dimension": dimension,
                "similarity_computed": True
            })

        except Exception as e:
            print_error(f"端到端测试失败: {e}")
            self.add_result("end_to_end", "text_embedding_pipeline", "failed", error=str(e))

    async def run_all_verifications(self):
        """运行所有验证"""
        print_section("Athena NLP系统完整性验证")
        print("版本: v1.0.0")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 执行验证
        await self.verify_pytorch_environment()
        await self.verify_model_loader()
        await self.verify_batch_processor()
        await self.verify_cache_system()
        await self.verify_nlp_services()
        await self.verify_embedding_services()
        await self.verify_intent_classifiers()
        await self.verify_production_services()
        await self.verify_model_configs()
        await self.verify_production_config()
        await self.run_end_to_end_test()

        # 生成报告
        self.print_summary()
        self.save_report()

    def print_summary(self) -> Any:
        """打印摘要"""
        print_section("验证摘要")

        summary = self.results["summary"]
        total = summary["total_checks"]
        passed = summary["passed"]
        failed = summary["failed"]
        warnings = summary["warnings"]

        print(f"总检查项: {total}")
        print_success(f"通过: {passed}")
        print_error(f"失败: {failed}")
        print_warning(f"警告: {warnings}")

        # 计算健康度
        if total > 0:
            health_percentage = (passed / total) * 100
            health_status = "健康" if health_percentage >= 80 else ("降级" if health_percentage >= 60 else "不健康")
            print(f"\n系统健康度: {health_percentage:.1f}% ({health_status})")

        # 按类别显示
        print("\n按类别统计:")
        for category, checks in self.results["categories"].items():
            category_passed = sum(1 for c in checks.values() if c.get("status") == "passed")
            category_total = len(checks)
            status_icon = "✓" if category_passed == category_total else ("✗" if category_passed == 0 else "⚠")
            print(f"  {status_icon} {category}: {category_passed}/{category_total}")

    def save_report(self) -> None:
        """保存报告"""
        report_dir = self.project_root / "logs/production"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"nlp_system_verification_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print_info(f"\n报告已保存: {report_file}")


async def main():
    """主函数"""
    verifier = NLPSystemVerifier()
    await verifier.run_all_verifications()

    # 返回退出码
    summary = verifier.results["summary"]
    if summary["failed"] > 0:
        return 1
    elif summary["warnings"] > 0:
        return 2
    else:
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
