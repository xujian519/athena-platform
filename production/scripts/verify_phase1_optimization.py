#!/usr/bin/env python3
"""
Athena智能体意图识别系统 - Phase 1 验证脚本
Phase 1 Verification Script

验证快速修复阶段的任务完成情况

作者: Athena平台团队
创建时间: 2025-12-29
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'


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


class Phase1Verifier:
    """Phase 1 验证器"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 1: 快速修复",
            "tasks": {},
            "overall_status": "unknown"
        }

    def add_result(self, task_name: str, status: str, details: str = "", metrics: dict = None) -> None:
        """添加验证结果"""
        self.results["tasks"][task_name] = {
            "status": status,  # passed, failed, warning
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics or {}
        }

    async def verify_bert_ner_loading(self):
        """验证BERT NER加载"""
        print_section("任务1: 修复BERT NER加载问题")

        try:
            from core.nlp.xiaonuo_ner_parameter_extractor import (
                NERModelConfig,
                XiaonuoNERParameterExtractor,
            )

            config = NERModelConfig()
            extractor = XiaonuoNERParameterExtractor(config)

            # 检查增强NER是否加载
            has_enhanced_ner = extractor.enhanced_ner is not None
            use_bert_ner = extractor.use_bert_ner

            if has_enhanced_ner:
                print_success("增强NER模块已加载")

                # 获取模型信息
                if hasattr(extractor.enhanced_ner, 'get_model_info'):
                    info = extractor.enhanced_ner.get_model_info()
                    print_info(f"  模型: {info.get('model_name')}")
                    print_info(f"  设备: {info.get('device')}")
                    print_info(f"  模型加载: {info.get('model_loaded')}")
                    print_info(f"  Tokenizer加载: {info.get('tokenizer_loaded')}")

                    if info.get('model_loaded') and info.get('tokenizer_loaded'):
                        print_success("BERT模型完全加载成功")
                        self.add_result("bert_ner_loading", "passed", "BERT NER成功加载", info)
                    else:
                        print_warning("BERT模型部分加载")
                        self.add_result("bert_ner_loading", "warning", "BERT NER部分加载", info)
                else:
                    print_warning("无法获取模型信息")
                    self.add_result("bert_ner_loading", "warning", "无法获取模型信息")

            elif use_bert_ner:
                print_success("BERT模式已启用")
                self.add_result("bert_ner_loading", "passed", "BERT模式启用")
            else:
                print_warning("使用规则模式")
                self.add_result("bert_ner_loading", "warning", "使用规则模式而非BERT")

            # 测试实体提取
            print_info("测试实体提取...")
            result = extractor.extract_parameters("我的邮箱是test@example.com，电话13812345678", "test")

            entity_count = len(result.entities)
            print_success(f"提取到 {entity_count} 个实体")

            if entity_count >= 2:
                print_success("实体识别工作正常")
                self.add_result("bert_ner_loading", "passed", f"实体识别正常 (识别{entity_count}个实体)", {"entity_count": entity_count})
            else:
                print_warning(f"实体识别数量偏少 ({entity_count}个)")
                self.add_result("bert_ner_loading", "warning", f"实体识别数量偏少 ({entity_count}个)", {"entity_count": entity_count})

        except Exception as e:
            print_error(f"BERT NER验证失败: {e}")
            self.add_result("bert_ner_loading", "failed", str(e))

    async def verify_tool_call_framework(self):
        """验证工具调用框架"""
        print_section("任务2: 建立工具调用框架")

        try:
            from core.tools.tool_call_manager import call_tool, get_tool_manager

            manager = get_tool_manager()

            # 检查工具数量
            tool_count = len(manager.tools)
            print_success("工具调用管理器已创建")
            print_info(f"  已注册工具: {tool_count}个")

            if tool_count >= 5:
                print_success("工具注册数量达标")
            else:
                print_warning(f"工具注册数量不足 (目标: 5+, 实际: {tool_count})")

            # 测试工具调用
            print_info("测试工具调用...")
            result = await call_tool("code_analyzer", {
                "code": "def hello(): print('Hello')",
                "language": "python"
            })

            if result.status.value == "success":
                print_success(f"工具调用成功: {result.tool_name}")
                print_info(f"  执行时间: {result.execution_time:.3f}秒")
                self.add_result("tool_call_framework", "passed", f"工具调用成功 ({result.execution_time:.3f}秒)", {
                    "tool_count": tool_count,
                    "execution_time": result.execution_time
                })
            else:
                print_error(f"工具调用失败: {result.error}")
                self.add_result("tool_call_framework", "failed", result.error)

            # 检查统计
            stats = manager.get_stats()
            print_info(f"  总调用数: {stats['total_calls']}")
            print_info(f"  成功率: {stats['success_rate']:.2%}")
            print_info(f"  平均执行时间: {stats['avg_execution_time']:.3f}秒")

            # 检查日志
            log_dir = Path("logs/tool_calls")
            if log_dir.exists():
                log_files = list(log_dir.glob("*.jsonl"))
                print_success(f"调用日志已创建 ({len(log_files)}个文件)")
            else:
                print_warning("调用日志目录不存在")

        except Exception as e:
            print_error(f"工具调用框架验证失败: {e}")
            self.add_result("tool_call_framework", "failed", str(e))

    async def verify_parameter_validation(self):
        """验证参数验证规则"""
        print_section("任务3: 完善参数验证规则")

        try:
            from core.nlp.xiaonuo_ner_parameter_extractor import (
                EntityType,
                NERModelConfig,
                XiaonuoNERParameterExtractor,
            )

            config = NERModelConfig()
            extractor = XiaonuoNERParameterExtractor(config)

            # 测试用例
            test_cases = [
                {
                    "name": "URL参数",
                    "text": "访问网站 https://example.com 获取信息",
                    "expected_type": EntityType.URL
                },
                {
                    "name": "邮箱参数",
                    "text": "发送邮件到 user@example.com",
                    "expected_type": EntityType.EMAIL
                },
                {
                    "name": "电话参数",
                    "text": "联系电话 13812345678",
                    "expected_type": EntityType.PHONE
                },
                {
                    "name": "端口参数",
                    "text": "服务运行在端口 8080",
                    "expected_type": EntityType.PORT
                }
            ]

            passed_cases = 0
            total_cases = len(test_cases)

            for test_case in test_cases:
                print_info(f"测试: {test_case['name']}")
                result = extractor.extract_parameters(test_case['text'], "test")

                # 检查是否识别到预期实体 (使用枚举比较)
                found = False
                for entity in result.entities:
                    if entity.entity_type == test_case['expected_type']:
                        print_success(f"  识别到 {entity.entity_type.value}: {entity.text}")
                        found = True
                        passed_cases += 1
                        break

                if not found:
                    print_warning(f"  未识别到 {test_case['expected_type'].value}")

            success_rate = passed_cases / total_cases
            print_info(f"参数验证通过率: {success_rate:.2%}")

            if success_rate >= 0.75:
                print_success("参数验证规则工作正常")
                self.add_result("parameter_validation", "passed", f"参数验证通过率 {success_rate:.2%}", {
                    "passed_cases": passed_cases,
                    "total_cases": total_cases,
                    "success_rate": success_rate
                })
            else:
                print_warning(f"参数验证通过率偏低 ({success_rate:.2%})")
                self.add_result("parameter_validation", "warning", f"参数验证通过率偏低 ({success_rate:.2%})", {
                    "passed_cases": passed_cases,
                    "total_cases": total_cases,
                    "success_rate": success_rate
                })

        except Exception as e:
            print_error(f"参数验证检查失败: {e}")
            self.add_result("parameter_validation", "failed", str(e))

    async def verify_training_data_samples(self):
        """验证训练样本数量"""
        print_section("任务4: 增加训练样本500+")

        try:
            from core.nlp.xiaonuo_enhanced_intent_classifier import XiaonuoEnhancedIntentClassifier

            classifier = XiaonuoEnhancedIntentClassifier()

            # 获取训练数据
            texts, labels = classifier.create_expanded_training_data()

            sample_count = len(texts)
            print_success(f"训练样本数量: {sample_count}条")

            # 检查是否达到目标
            target = 800  # 从400增加到800
            if sample_count >= target:
                print_success(f"训练样本数量达标 (目标: {target}+, 实际: {sample_count})")
                self.add_result("training_data_samples", "passed", f"训练样本充足 ({sample_count}条)", {
                    "sample_count": sample_count,
                    "target": target
                })
            else:
                print_warning(f"训练样本数量不足 (目标: {target}+, 实际: {sample_count})")
                self.add_result("training_data_samples", "warning", f"训练样本不足 ({sample_count}/{target})", {
                    "sample_count": sample_count,
                    "target": target
                })

            # 显示意图分布
            from collections import Counter
            intent_dist = Counter(labels)
            print_info("意图分布:")
            for intent, count in intent_dist.items():
                print(f"  {intent}: {count}条")

        except Exception as e:
            print_error(f"训练数据验证失败: {e}")
            self.add_result("training_data_samples", "failed", str(e))

    def calculate_overall_status(self) -> Any:
        """计算总体状态"""
        tasks = self.results["tasks"]
        total = len(tasks)
        passed = sum(1 for t in tasks.values() if t["status"] == "passed")
        failed = sum(1 for t in tasks.values() if t["status"] == "failed")
        warnings = sum(1 for t in tasks.values() if t["status"] == "warning")

        self.results["summary"] = {
            "total_tasks": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings
        }

        if failed > 0:
            self.results["overall_status"] = "failed"
        elif warnings > 0:
            self.results["overall_status"] = "warnings"
        else:
            self.results["overall_status"] = "passed"

    def print_summary(self) -> Any:
        """打印摘要"""
        print_section("Phase 1 验证摘要")

        summary = self.results["summary"]
        status = self.results["overall_status"]

        if status == "passed":
            print_success("总体状态: 通过 (所有任务完成)")
        elif status == "warnings":
            print_warning("总体状态: 通过但有警告 (部分任务需改进)")
        else:
            print_error("总体状态: 失败 (有任务未完成)")

        print()
        print("任务详情:")
        for task_name, result in self.results["tasks"].items():
            status_icon = "✓" if result["status"] == "passed" else ("✗" if result["status"] == "failed" else "⚠")
            status_color = Colors.GREEN if result["status"] == "passed" else (Colors.RED if result["status"] == "failed" else Colors.YELLOW)
            print(f"  {status_color}{status_icon}{Colors.NC} {task_name}: {result['details']}")

    def save_report(self) -> None:
        """保存验证报告"""
        import json

        report_dir = Path("logs/production")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"phase1_verification_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print_info(f"\n报告已保存: {report_file}")

    async def run_all_verifications(self):
        """运行所有验证"""
        print_section("Athena智能体意图识别系统 - Phase 1 验证")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 执行验证
        await self.verify_bert_ner_loading()
        await self.verify_tool_call_framework()
        await self.verify_parameter_validation()
        await self.verify_training_data_samples()

        # 生成报告
        self.calculate_overall_status()
        self.print_summary()
        self.save_report()


async def main():
    """主函数"""
    verifier = Phase1Verifier()
    await verifier.run_all_verifications()

    # 返回退出码
    status = verifier.results["overall_status"]
    if status == "passed":
        return 0
    elif status == "warnings":
        return 1
    else:
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
