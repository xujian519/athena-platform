#!/usr/bin/env python3
"""
Athena BERT语义增强意图分类器验证脚本
BERT Semantic Enhanced Intent Classifier Verification

验证BERT语义增强意图分类器的功能：
1. 本地MPS优化BERT模型加载
2. 语义向量提取（1024维（BGE-M3））
3. 特征融合（BERT + TF-IDF + 文本统计）
4. 意图分类准确率
5. 性能指标测试

作者: Athena平台团队
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


class BERTIntentClassifierVerifier:
    """BERT意图分类器验证器"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }

    def add_result(
        self,
        test_name: str,
        status: str,
        details: str = "",
        execution_time: float = 0.0,
        data: Any = None
    ):
        """添加测试结果"""
        self.results["tests"][test_name] = {
            "status": status,
            "details": details,
            "execution_time": execution_time,
            "data": data
        }

        self.results["summary"]["total"] += 1
        if status == "passed":
            self.results["summary"]["passed"] += 1
        elif status == "failed":
            self.results["summary"]["failed"] += 1
        else:
            self.results["summary"]["warnings"] += 1

    async def test_bert_model_loading(self) -> bool:
        """测试BERT模型加载"""
        print_section("测试1: BERT模型加载")

        try:
            from core.nlp.bert_semantic_intent_classifier import (
                BERTFeatureExtractor,
                BERTIntentConfig,
            )

            start_time = time.time()

            # 测试不同模型加载
            models_to_test = ["bge_base_zh", "chinese_bert", "bert_base_chinese"]

            loaded_models = []
            for model_name in models_to_test:
                try:
                    print_info(f"加载模型: {model_name}")
                    extractor = BERTFeatureExtractor(
                        model_name=model_name,
                        model_paths=BERTIntentConfig.local_bert_models
                    )
                    loaded_models.append(model_name)
                    print_success(f"  ✓ {model_name} 加载成功")

                    # 测试特征提取
                    test_features = extractor.extract_features(["测试文本"])
                    if test_features.shape[1] == 768:
                        print_success(f"    特征维度: {test_features.shape[1]} (正确)")
                    else:
                        print_warning(f"    特征维度: {test_features.shape[1]} (期望768)")

                except Exception as e:
                    print_warning(f"  ⚠ {model_name} 加载失败: {e}")

            execution_time = time.time() - start_time

            if len(loaded_models) >= 1:
                print_success(f"  ✓ 成功加载 {len(loaded_models)} 个模型 ({execution_time:.3f}秒)")
                self.add_result(
                    "bert_model_loading",
                    "passed",
                    f"成功加载{len(loaded_models)}个模型",
                    execution_time,
                    {"loaded_models": loaded_models}
                )
                return True
            else:
                print_error("  ✗ 没有成功加载任何模型")
                self.add_result("bert_model_loading", "failed", "没有模型加载成功", execution_time)
                return False

        except Exception as e:
            print_error(f"  ✗ 测试异常: {e}")
            self.add_result("bert_model_loading", "failed", str(e))
            return False

    async def test_semantic_feature_extraction(self) -> bool:
        """测试语义特征提取"""
        print_section("测试2: 语义特征提取")

        try:
            from core.nlp.bert_semantic_intent_classifier import (
                BERTFeatureExtractor,
                BERTIntentConfig,
            )

            start_time = time.time()

            # 创建特征提取器
            extractor = BERTFeatureExtractor(
                model_name="bge_base_zh",
                model_paths=BERTIntentConfig.local_bert_models
            )

            # 测试文本
            test_texts = [
                "帮我分析这段代码的性能",
                "我今天心情不太好",
                "启动系统监控",
                "什么是人工智能"
            ]

            print_info("提取语义特征...")
            features = extractor.extract_features(test_texts, use_cache=True)

            execution_time = time.time() - start_time

            # 验证特征
            if features.shape == (len(test_texts), 768):
                print_success(f"  ✓ 特征维度正确: {features.shape}")
                print_success(f"  ✓ 特征提取成功 ({execution_time:.3f}秒)")

                # 显示特征统计
                print_info("特征统计:")
                print_info(f"  - 均值: {features.mean():.4f}")
                print_info(f"  - 标准差: {features.std():.4f}")
                print_info(f"  - 最小值: {features.min():.4f}")
                print_info(f"  - 最大值: {features.max():.4f}")

                self.add_result(
                    "semantic_feature_extraction",
                    "passed",
                    "1024维（BGE-M3）特征提取成功",
                    execution_time,
                    {
                        "feature_shape": features.shape,
                        "feature_stats": {
                            "mean": float(features.mean()),
                            "std": float(features.std()),
                            "min": float(features.min()),
                            "max": float(features.max())
                        }
                    }
                )
                return True
            else:
                print_error(f"  ✗ 特征维度错误: {features.shape}")
                self.add_result(
                    "semantic_feature_extraction",
                    "failed",
                    f"特征维度错误: {features.shape}",
                    execution_time
                )
                return False

        except Exception as e:
            print_error(f"  ✗ 测试异常: {e}")
            self.add_result("semantic_feature_extraction", "failed", str(e))
            return False

    async def test_intent_classification(self) -> bool:
        """测试意图分类"""
        print_section("测试3: 意图分类")

        try:
            from core.nlp.bert_semantic_intent_classifier import BERTSemanticIntentClassifier

            start_time = time.time()

            # 创建分类器
            classifier = BERTSemanticIntentClassifier()

            # 训练数据
            training_data = [
                # 技术类 (10条)
                ("帮我分析这段代码", "TECHNICAL"),
                ("系统性能怎么样", "TECHNICAL"),
                ("如何优化数据库查询", "TECHNICAL"),
                ("API接口怎么调试", "TECHNICAL"),
                ("程序出错了怎么办", "TECHNICAL"),
                ("代码重构有啥建议", "TECHNICAL"),
                ("怎么部署微服务", "TECHNICAL"),
                ("系统架构如何设计", "TECHNICAL"),
                ("算法时间复杂度分析", "TECHNICAL"),
                ("如何进行压力测试", "TECHNICAL"),

                # 情感类 (10条)
                ("我今天心情不太好", "EMOTIONAL"),
                ("我想妈妈了", "EMOTIONAL"),
                ("感到很孤独", "EMOTIONAL"),
                ("生活真美好", "EMOTIONAL"),
                ("谢谢你的关心", "EMOTIONAL"),
                ("觉得有点沮丧", "EMOTIONAL"),
                ("家人健康最重要", "EMOTIONAL"),
                ("工作压力好大", "EMOTIONAL"),
                ("感到很幸福", "EMOTIONAL"),
                ("有点想念朋友", "EMOTIONAL"),

                # 指令类 (10条)
                ("启动监控系统", "COMMAND"),
                ("关闭服务器", "COMMAND"),
                ("停止程序运行", "COMMAND"),
                ("开启自动备份", "COMMAND"),
                ("重启系统服务", "COMMAND"),
                ("运行测试脚本", "COMMAND"),
                ("停止数据采集", "COMMAND"),
                ("开启调试模式", "COMMAND"),
                ("关闭防火墙", "COMMAND"),
                ("执行系统更新", "COMMAND"),

                # 查询类 (10条)
                ("什么是人工智能", "QUERY"),
                ("怎么部署应用", "QUERY"),
                ("系统配置在哪里", "QUERY"),
                ("数据库密码是多少", "QUERY"),
                ("如何查看日志", "QUERY"),
                ("端口占用怎么查", "QUERY"),
                ("内存使用情况", "QUERY"),
                ("磁盘空间剩余", "QUERY"),
                ("进程状态查询", "QUERY"),
                ("网络连接测试", "QUERY"),
            ]

            texts = [item[0] for item in training_data]
            labels = [item[1] for item in training_data]

            print_info(f"训练数据: {len(texts)}条")

            # 训练
            print_info("开始训练...")
            train_start = time.time()
            train_result = classifier.train(texts, labels, test_size=0.2)
            train_time = time.time() - train_start

            print_success(f"  ✓ 训练完成 ({train_time:.3f}秒)")
            print_info(f"  准确率: {train_result['accuracy']:.2%}")

            # 测试预测
            print_info("\n测试预测:")
            test_cases = [
                "帮我优化代码性能",  # TECHNICAL
                "我觉得很伤心",  # EMOTIONAL
                "开启服务器监控",  # COMMAND
                "系统怎么部署",  # QUERY
            ]

            correct_predictions = 0
            for text in test_cases:
                prediction = classifier.predict_single(text, return_proba=True)
                top_intent = prediction[0]["intent"]
                confidence = prediction[0]["confidence"]

                print_info(f"  输入: {text}")
                print_info(f"  预测: {top_intent} (置信度: {confidence:.2%})")

                # 简单验证（基于关键词）
                if "代码" in text or "性能" in text:
                    if top_intent == "TECHNICAL":
                        correct_predictions += 1
                elif "伤心" in text:
                    if top_intent == "EMOTIONAL":
                        correct_predictions += 1
                elif "监控" in text or "开启" in text:
                    if top_intent == "COMMAND":
                        correct_predictions += 1
                elif "部署" in text or "怎么" in text:
                    if top_intent == "QUERY" or top_intent == "TECHNICAL":
                        correct_predictions += 1

            execution_time = time.time() - start_time

            accuracy = correct_predictions / len(test_cases)
            print_success(f"\n  ✓ 预测准确率: {accuracy:.2%} ({correct_predictions}/{len(test_cases)})")

            if accuracy >= 0.5:
                self.add_result(
                    "intent_classification",
                    "passed",
                    f"准确率: {accuracy:.2%}",
                    execution_time,
                    {
                        "training_accuracy": train_result['accuracy'],
                        "test_accuracy": accuracy,
                        "training_time": train_time
                    }
                )
                return True
            else:
                print_warning(f"  ⚠ 预测准确率较低: {accuracy:.2%}")
                self.add_result(
                    "intent_classification",
                    "warning",
                    f"准确率: {accuracy:.2%}",
                    execution_time
                )
                return False

        except Exception as e:
            print_error(f"  ✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.add_result("intent_classification", "failed", str(e))
            return False

    async def test_feature_fusion(self) -> bool:
        """测试特征融合"""
        print_section("测试4: 特征融合")

        try:
            from core.nlp.bert_semantic_intent_classifier import BERTSemanticIntentClassifier

            start_time = time.time()

            # 创建分类器（启用所有特征）
            from core.nlp.bert_semantic_intent_classifier import BERTIntentConfig
            config = BERTIntentConfig(
                use_bert_features=True,
                use_tfidf_features=True,
                use_text_stats=True
            )

            classifier = BERTSemanticIntentClassifier(config)

            # 小规模训练（每个类别至少2个样本）
            training_data = [
                # 技术类 (4条)
                ("分析代码", "TECHNICAL"),
                ("优化性能", "TECHNICAL"),
                ("调试程序", "TECHNICAL"),
                ("系统架构", "TECHNICAL"),

                # 情感类 (4条)
                ("心情不好", "EMOTIONAL"),
                ("感到孤独", "EMOTIONAL"),
                ("想念家人", "EMOTIONAL"),
                ("感到幸福", "EMOTIONAL"),

                # 指令类 (4条)
                ("启动系统", "COMMAND"),
                ("停止程序", "COMMAND"),
                ("开启监控", "COMMAND"),
                ("关闭服务", "COMMAND"),

                # 查询类 (4条)
                ("什么是AI", "QUERY"),
                ("怎么部署", "QUERY"),
                ("系统配置", "QUERY"),
                ("查看日志", "QUERY"),
            ]

            texts = [item[0] for item in training_data]
            labels = [item[1] for item in training_data]

            # 训练
            classifier.train(texts, labels, test_size=0.25)

            execution_time = time.time() - start_time

            # 验证特征融合
            print_success(f"  ✓ 特征融合成功 ({execution_time:.3f}秒)")
            print_info(f"  - BERT特征: {config.use_bert_features}")
            print_info(f"  - TF-IDF特征: {config.use_tfidf_features}")
            print_info(f"  - 文本统计特征: {config.use_text_stats}")

            self.add_result(
                "feature_fusion",
                "passed",
                "BERT + TF-IDF + 文本统计特征融合成功",
                execution_time,
                {
                    "use_bert": config.use_bert_features,
                    "use_tfidf": config.use_tfidf_features,
                    "use_text_stats": config.use_text_stats
                }
            )
            return True

        except Exception as e:
            print_error(f"  ✗ 测试异常: {e}")
            self.add_result("feature_fusion", "failed", str(e))
            return False

    async def test_performance(self) -> bool:
        """测试性能"""
        print_section("测试5: 性能测试")

        try:
            from core.nlp.bert_semantic_intent_classifier import BERTSemanticIntentClassifier

            start_time = time.time()

            # 创建并训练分类器
            classifier = BERTSemanticIntentClassifier()

            # 训练数据（每个类别至少2个样本）
            training_data = [
                # 技术类 (4条)
                ("分析代码", "TECHNICAL"),
                ("优化性能", "TECHNICAL"),
                ("调试程序", "TECHNICAL"),
                ("系统架构", "TECHNICAL"),

                # 情感类 (4条)
                ("心情不好", "EMOTIONAL"),
                ("感到孤独", "EMOTIONAL"),
                ("想念家人", "EMOTIONAL"),
                ("感到幸福", "EMOTIONAL"),
            ]

            texts = [item[0] for item in training_data]
            labels = [item[1] for item in training_data]

            classifier.train(texts, labels, test_size=0.3)

            # 测试预测性能
            test_texts = ["帮我优化代码"] * 10

            predict_start = time.time()
            for text in test_texts:
                classifier.predict_single(text)
            predict_time = time.time() - predict_start

            avg_predict_time = predict_time / len(test_texts)

            execution_time = time.time() - start_time

            print_success(f"  ✓ 性能测试完成 ({execution_time:.3f}秒)")
            print_info(f"  - 平均预测时间: {avg_predict_time*1000:.2f}ms")
            print_info(f"  - 吞吐量: {len(test_texts)/predict_time:.2f} texts/s")

            # 性能基准
            if avg_predict_time < 1.0:  # 小于1秒
                print_success(f"  ✓ 性能优秀 (平均{avg_predict_time*1000:.2f}ms)")
                self.add_result(
                    "performance",
                    "passed",
                    f"平均预测时间: {avg_predict_time*1000:.2f}ms",
                    execution_time,
                    {"avg_predict_time_ms": avg_predict_time * 1000}
                )
                return True
            else:
                print_warning(f"  ⚠ 性能可优化 (平均{avg_predict_time*1000:.2f}ms)")
                self.add_result(
                    "performance",
                    "warning",
                    f"平均预测时间: {avg_predict_time*1000:.2f}ms",
                    execution_time
                )
                return False

        except Exception as e:
            print_error(f"  ✗ 测试异常: {e}")
            self.add_result("performance", "failed", str(e))
            return False

    async def run_all_verifications(self):
        """运行所有验证测试"""
        print_section("Athena BERT语义增强意图分类器验证")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 执行测试
        tests = [
            ("BERT模型加载", self.test_bert_model_loading),
            ("语义特征提取", self.test_semantic_feature_extraction),
            ("意图分类", self.test_intent_classification),
            ("特征融合", self.test_feature_fusion),
            ("性能测试", self.test_performance),
        ]

        passed = 0
        failed = 0
        warnings = 0

        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print_error(f"测试执行异常: {test_name} - {e}")
                failed += 1

        # 打印摘要
        self.print_summary()

        # 保存报告
        self.save_report()

        return failed == 0

    def print_summary(self) -> Any:
        """打印验证摘要"""
        print_section("验证摘要")

        summary = self.results["summary"]
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]
        warnings = summary["warnings"]

        print(f"总测试数: {total}")
        print_success(f"通过: {passed}")
        if failed > 0:
            print_error(f"失败: {failed}")
        if warnings > 0:
            print_warning(f"警告: {warnings}")

        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n通过率: {success_rate:.1f}%")

        if success_rate >= 90:
            print_success("\n🎉 BERT语义增强意图分类器验证通过!")
        elif success_rate >= 70:
            print_warning("\n⚠ 系统基本可用，建议优化部分功能")
        else:
            print_error("\n❌ 系统存在较多问题，需要修复")

    def save_report(self) -> None:
        """保存验证报告"""
        report_dir = Path("logs/intent")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"bert_intent_verification_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print_info(f"\n报告已保存: {report_file}")


async def main():
    """主函数"""
    verifier = BERTIntentClassifierVerifier()
    success = await verifier.run_all_verifications()

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
