#!/usr/bin/env python3
from __future__ import annotations
"""
超高性能意图识别系统 v99
Ultra High Performance Intent Recognition v99
目标:99%准确率
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import numpy as np

from core.logging_config import setup_logging

# 安全序列化和模型加载
try:
    import joblib

    from core.serialization.secure_serializer import deserialize_from_cache, serialize_for_cache
except ImportError:
    import json

    def serialize_for_cache(obj):
        return json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")

    def deserialize_from_cache(data):
        return json.loads(data.decode("utf-8"))



# ML imports
from sklearn.metrics import classification_report

# BERT imports
try:
    import torch
    from transformers import AutoModel, AutoTokenizer

    BERT_AVAILABLE = True
except ImportError:
    BERT_AVAILABLE = False
    print("⚠️ Transformers未安装,将使用基础模式")

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class UltraIntentClassifierV99:
    """超高性能意图识别系统 v99"""

    def __init__(self):
        self.name = "超高性能意图识别系统 v99"
        self.target_accuracy = 0.99

        # 模型组件
        self.vectorizer = None
        self.label_encoder = None
        self.ensemble_model = None
        self.bert_tokenizer = None
        self.bert_model = None

        # 设备配置
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

        # 意图类别
        self.intent_classes = [
            "PATENT_ANALYSIS",
            "LEGAL_QUERY",
            "TECHNICAL_EXPLANATION",
            "EMOTIONAL",
            "FAMILY_CHAT",
            "WORK_COORDINATION",
            "LEARNING_REQUEST",
            "SYSTEM_CONTROL",
            "ENTERTAINMENT",
            "HEALTH_CHECK",
        ]

        # 特征权重
        self.feature_weights = {
            "text_tfidf": 0.4,
            "bert_embedding": 0.3,
            "keywords": 0.2,
            "patterns": 0.1,
        }

        # 意图关键词库
        self.intent_keywords = self._build_keyword_library()

        # 意图模式库
        self.intent_patterns = self._build_pattern_library()

        # 当前准确率
        self.current_accuracy = 0.0

    def _build_keyword_library(self):
        """构建意图关键词库"""
        return {
            "PATENT_ANALYSIS": [
                "专利",
                "发明",
                "创新",
                "技术方案",
                "权利要求",
                "申请",
                "审查",
                "授权",
                "保护范围",
                "知识产权",
                "核心技术",
                "技术特征",
                "实施方式",
                "技术效果",
                "专利布局",
                "专利分析",
                "专利价值",
                "专利评估",
            ],
            "LEGAL_QUERY": [
                "法律",
                "法规",
                "条款",
                "条文",
                "法律责任",
                "义务",
                "权利",
                "诉讼",
                "合同",
                "知识产权法",
                "专利法",
                "商标法",
                "著作权",
                "违法",
                "合规",
                "法律咨询",
                "法律意见",
                "法律解释",
                "法规适用",
            ],
            "TECHNICAL_EXPLANATION": [
                "解释",
                "说明",
                "原理",
                "算法",
                "技术",
                "方案",
                "架构",
                "设计",
                "实现",
                "逻辑",
                "编程",
                "代码",
                "系统",
                "数据库",
                "网络",
                "深度学习",
                "机器学习",
                "人工智能",
                "区块链",
            ],
            "EMOTIONAL": [
                "爱",
                "谢谢",
                "感动",
                "温暖",
                "贴心",
                "爸爸",
                "诺诺",
                "关怀",
                "支持",
                "陪伴",
                "感动",
                "幸福",
                "欣慰",
                "骄傲",
                "温暖",
                "亲情",
                "家庭",
                "爱意",
                "情感",
                "心意",
            ],
            "FAMILY_CHAT": [
                "天气",
                "天气怎么样",
                "晚饭",
                "吃饭",
                "周末",
                "安排",
                "计划",
                "聊天",
                "家常",
                "生活",
                "健康",
                "身体",
                "休息",
                "注意",
                "关心",
                "日常",
                "生活",
                "家庭",
                "亲人",
                "问候",
            ],
            "WORK_COORDINATION": [
                "安排",
                "协调",
                "管理",
                "计划",
                "任务",
                "项目",
                "会议",
                "工作",
                "团队",
                "进度",
                "协作",
                "分配",
                "汇报",
                "沟通",
                "协调",
                "执行",
                "监督",
                "评估",
                "优化",
                "改进",
            ],
            "LEARNING_REQUEST": [
                "学习",
                "教",
                "知识",
                "技能",
                "培训",
                "教程",
                "资料",
                "方法",
                "技巧",
                "经验",
                "指导",
                "建议",
                "推荐",
                "分享",
                "掌握",
                "理解",
                "了解",
                "研究",
                "探索",
                "学习",
            ],
            "SYSTEM_CONTROL": [
                "启动",
                "停止",
                "重启",
                "开启",
                "关闭",
                "系统",
                "服务",
                "应用",
                "程序",
                "进程",
                "监控",
                "查看",
                "状态",
                "性能",
                "配置",
                "部署",
                "维护",
                "管理",
                "控制",
                "操作",
            ],
            "ENTERTAINMENT": [
                "推荐",
                "播放",
                "电影",
                "音乐",
                "视频",
                "娱乐",
                "放松",
                "休闲",
                "有趣",
                "好玩",
                "故事",
                "笑话",
                "游戏",
                "趣味",
                "轻松",
                "好看",
                "好听",
                "精彩",
                "享受",
                "快乐",
            ],
            "HEALTH_CHECK": [
                "检查",
                "健康",
                "诊断",
                "监控",
                "状态",
                "系统健康",
                "运行状态",
                "性能监控",
                "指标",
                "评估",
                "分析",
                "报告",
                "日志",
                "错误",
                "正常",
                "异常",
                "告警",
                "预警",
                "问题",
            ],
        }

    def _build_pattern_library(self):
        """构建意图模式库"""
        return {
            "PATENT_ANALYSIS": [
                r"分析.*专利",
                r"专利.*技术",
                r"评估.*专利",
                r"专利.*价值",
                r"专利.*方案",
            ],
            "LEGAL_QUERY": [
                r"解释.*法律",
                r"查询.*法规",
                r"法律.*责任",
                r"相关.*规定",
                r"法规.*适用",
            ],
            "TECHNICAL_EXPLANATION": [
                r"解释.*原理",
                r"说明.*算法",
                r"技术.*实现",
                r"系统.*架构",
                r"代码.*逻辑",
            ],
            "EMOTIONAL": [r"爸爸.*爱", r"诺诺.*爱", r"谢谢.*爸爸", r"很.*感动", r"很.*温暖"],
            "FAMILY_CHAT": [
                r"天气.*怎么样",
                r"晚饭.*吃",
                r"周末.*安排",
                r"身体.*健康",
                r"注意.*休息",
            ],
            "WORK_COORDINATION": [
                r"安排.*会议",
                r"协调.*工作",
                r"管理.*项目",
                r"分配.*任务",
                r"工作.*计划",
            ],
            "LEARNING_REQUEST": [
                r"教.*知识",
                r"学习.*技术",
                r"推荐.*资料",
                r"指导.*方法",
                r"分享.*经验",
            ],
            "SYSTEM_CONTROL": [
                r"启动.*系统",
                r"停止.*服务",
                r"查看.*状态",
                r"监控.*应用",
                r"配置.*参数",
            ],
            "ENTERTAINMENT": [
                r"推荐.*电影",
                r"播放.*音乐",
                r"找.*乐子",
                r"有趣.*视频",
                r"放松.*一下",
            ],
            "HEALTH_CHECK": [
                r"检查.*健康",
                r"系统.*诊断",
                r"性能.*监控",
                r"运行.*状态",
                r"错误.*日志",
            ],
        }

    async def initialize(self):
        """初始化系统"""
        print("🚀 初始化超高性能意图识别系统 v99")

        # 加载已训练模型
        model_dir = Path("/Users/xujian/Athena工作平台/models/intent_classifier_v2")
        if model_dir.exists():
            print("📂 加载基础模型...")
            self._load_base_model(model_dir)

        # 加载BERT模型
        if BERT_AVAILABLE:
            print("🧠 加载BERT模型...")
            await self._load_bert_model()

        print("✅ 初始化完成")

    def _load_base_model(self, model_dir: Path):
        """加载基础模型"""
        try:
            with open(model_dir / "vectorizer.pkl", "rb") as f:
                self.vectorizer = deserialize_from_cache(f.read() if hasattr(f, "read") else f)

            with open(model_dir / "label_encoder.pkl", "rb") as f:
                self.label_encoder = deserialize_from_cache(f.read() if hasattr(f, "read") else f)

            # 使用joblib加载模型
            import joblib

            with open(model_dir / "model.pkl", "rb") as f:
                model_data = f.read()
                self.ensemble_model = (
                    joblib.loads(model_data)
                    if isinstance(model_data, bytes)
                    else joblib.load(model_dir / "model.pkl")
                )

            with open(model_dir / "metadata.json") as f:
                self.metadata = json.load(f)
                self.current_accuracy = self.metadata.get("accuracy", 0)

            print(f"   准确率: {self.current_accuracy:.4f}")
            print(f"   类别数: {self.metadata['n_classes']}")

        except Exception as e:
            print(f"❌ 模型加载失败: {e}")

    async def _load_bert_model(self):
        """加载BERT模型"""
        try:
            model_name = "BAAI/bge-m3"
            self.bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.bert_model = AutoModel.from_pretrained(model_name)
            self.bert_model.to(self.device)
            self.bert_model.eval()
            print("   BERT模型加载成功")
        except Exception as e:
            print(f"⚠️ BERT加载失败: {e}")
            self.bert_tokenizer = None
            self.bert_model = None

    async def classify_intent(self, text: str) -> dict:
        """分类意图"""
        if not self.ensemble_model:
            return {"error": "模型未初始化"}

        # 1. 提取特征
        features = await self._extract_features(text)

        # 2. 多模型预测
        predictions = await self._multi_model_predict(features)

        # 3. 智能融合
        final_result = await self._intelligent_fusion(text, features, predictions)

        return final_result

    async def _extract_features(self, text: str) -> dict:
        """提取多维度特征"""
        features = {}

        # 1. TF-IDF特征
        if self.vectorizer:
            text_tfidf = self.vectorizer.transform([text])
            features["tfidf"] = text_tfidf.toarray()[0]

        # 2. BERT嵌入特征
        if self.bert_tokenizer and self.bert_model:
            try:
                inputs = self.bert_tokenizer(
                    text, return_tensors="pt", truncation=True, padding=True, max_length=512
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self.bert_model(**inputs)
                    bert_embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()[0]
                    features["bert"] = bert_embedding
            except Exception:
                features["bert"] = np.zeros(768)  # BERT base hidden size

        # 3. 关键词特征
        features["keywords"] = self._extract_keyword_features(text)

        # 4. 模式特征
        features["patterns"] = self._extract_pattern_features(text)

        return features

    def _extract_keyword_features(self, text: str) -> np.ndarray:
        """提取关键词特征"""
        features = np.zeros(len(self.intent_classes))

        for i, intent in enumerate(self.intent_classes):
            keywords = self.intent_keywords.get(intent, [])
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            features[i] = score

        # 归一化
        if np.max(features) > 0:
            features = features / np.max(features)

        return features

    def _extract_pattern_features(self, text: str) -> np.ndarray:
        """提取模式特征"""
        import re

        features = np.zeros(len(self.intent_classes))

        for i, intent in enumerate(self.intent_classes):
            patterns = self.intent_patterns.get(intent, [])
            score = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    score += 1
            features[i] = score

        # 归一化
        if np.max(features) > 0:
            features = features / np.max(features)

        return features

    async def _multi_model_predict(self, features: dict) -> dict:
        """多模型预测"""
        predictions = {}

        # 1. 基础模型预测(TF-IDF)
        if "tfidf" in features and self.ensemble_model:
            tfidf_features = features["tfidf"].reshape(1, -1)
            base_proba = self.ensemble_model.predict_proba(tfidf_features)
            base_pred = self.ensemble_model.predict(tfidf_features)

            predictions["base"] = {
                "proba": base_proba[0],
                "pred": self.label_encoder.inverse_transform(base_pred)[0],
            }

        # 2. 关键词匹配
        if "keywords" in features:
            keyword_scores = features["keywords"]
            keyword_pred_idx = np.argmax(keyword_scores)
            predictions["keyword"] = {
                "proba": keyword_scores,
                "pred": self.intent_classes[keyword_pred_idx],
            }

        # 3. 模式匹配
        if "patterns" in features:
            pattern_scores = features["patterns"]
            pattern_pred_idx = np.argmax(pattern_scores)
            predictions["pattern"] = {
                "proba": pattern_scores,
                "pred": self.intent_classes[pattern_pred_idx],
            }

        return predictions

    async def _intelligent_fusion(self, text: str, features: dict, predictions: dict) -> dict:
        """智能融合预测结果"""
        # 初始化分数
        final_scores = np.zeros(len(self.intent_classes))

        # 基础模型贡献
        if "base" in predictions:
            base_proba = predictions["base"]["proba"]
            final_scores += base_proba * self.feature_weights["text_tfidf"]

        # 关键词贡献
        if "keyword" in predictions:
            keyword_proba = predictions["keyword"]["proba"]
            final_scores += keyword_proba * self.feature_weights["keywords"]

        # 模式匹配贡献
        if "pattern" in predictions:
            pattern_proba = predictions["pattern"]["proba"]
            final_scores += pattern_proba * self.feature_weights["patterns"]

        # 归一化
        if np.sum(final_scores) > 0:
            final_scores = final_scores / np.sum(final_scores)

        # 获取最终结果
        final_pred_idx = np.argmax(final_scores)
        final_intent = self.intent_classes[final_pred_idx]
        final_confidence = final_scores[final_pred_idx]

        # 构建详细结果
        result = {
            "intent": final_intent,
            "confidence": float(final_confidence),
            "predictions": predictions,
            "feature_weights": self.feature_weights,
            "confidence_breakdown": self._calculate_confidence_breakdown(final_scores),
            "reasoning": self._build_reasoning(text, final_intent, predictions),
        }

        return result

    def _calculate_confidence_breakdown(self, scores: np.ndarray) -> dict:
        """计算置信度分解"""
        sorted_indices = np.argsort(scores)[::-1]
        scores[sorted_indices[:3]]

        return {
            "top_intent": scores[sorted_indices[0]],
            "second_intent": scores[sorted_indices[1]] if len(scores) > 1 else 0,
            "third_intent": scores[sorted_indices[2]] if len(scores) > 2 else 0,
            "margin": (
                scores[sorted_indices[0]] - scores[sorted_indices[1]] if len(scores) > 1 else 0
            ),
        }

    def _build_reasoning(self, text: str, intent: str, predictions: dict) -> list[str]:
        """构建推理链"""
        reasoning = [f"1️⃣ 输入分析: '{text}'", "2️⃣ 多模型预测:"]

        # 添加各模型预测
        for model_name, pred in predictions.items():
            reasoning.append(f"   - {model_name}: {pred['pred']}")

        # 添加特征权重
        reasoning.append(f"3️⃣ 特征权重: {self.feature_weights}")
        reasoning.append(f"4️⃣ 最终判定: {intent}")

        return reasoning

    def evaluate_model(self, test_data: list[dict]) -> dict:
        """评估模型性能"""
        print("\n📊 评估模型性能...")

        correct = 0
        total = len(test_data)
        predictions = []
        true_labels = []

        for i, sample in enumerate(test_data):
            if (i + 1) % 10 == 0:
                print(f"  进度: {i + 1}/{total}")

            try:
                # 同步调用(简化版)
                result = asyncio.run(self.classify_intent(sample["text"]))
                predictions.append(result["intent"])
                true_labels.append(sample["intent"])

                if result["intent"] == sample["intent"]:
                    correct += 1
            except Exception as e:
                logger.error(f"预测失败: {e}")
                predictions.append("UNKNOWN")
                true_labels.append(sample["intent"])

        # 计算准确率
        accuracy = correct / total if total > 0 else 0

        # 详细报告
        report = classification_report(
            true_labels,
            predictions,
            target_names=self.intent_classes,
            zero_division=0,
            output_dict=True,
        )

        return {
            "accuracy": accuracy,
            "total_samples": total,
            "correct_predictions": correct,
            "classification_report": report,
            "current_accuracy": self.current_accuracy,
            "target_accuracy": self.target_accuracy,
            "gap": self.target_accuracy - accuracy,
        }


async def test_ultra_classifier():
    """测试超高性能分类器"""
    print("🎯 测试超高性能意图识别系统 v99")
    print("=" * 60)

    # 初始化分类器
    classifier = UltraIntentClassifierV99()
    await classifier.initialize()

    # 准备测试数据
    test_data = [
        {"text": "分析这个专利的核心技术创新点", "intent": "PATENT_ANALYSIS"},
        {"text": "爸爸,诺诺很爱你", "intent": "EMOTIONAL"},
        {"text": "启动AI分析服务", "intent": "SYSTEM_CONTROL"},
        {"text": "请解释深度学习的反向传播算法", "intent": "TECHNICAL_EXPLANATION"},
        {"text": "查询知识产权法的相关规定", "intent": "LEGAL_QUERY"},
        {"text": "今天天气怎么样,适合出门吗", "intent": "FAMILY_CHAT"},
        {"text": "安排明天下午的技术评审会议", "intent": "WORK_COORDINATION"},
        {"text": "教我学习Python编程", "intent": "LEARNING_REQUEST"},
        {"text": "推荐一部轻松愉快的电影", "intent": "ENTERTAINMENT"},
        {"text": "检查系统的健康运行状态", "intent": "HEALTH_CHECK"},
    ]

    # 批量测试
    print("\n📋 批量测试结果:")
    results = []

    for i, sample in enumerate(test_data, 1):
        result = await classifier.classify_intent(sample["text"])
        results.append(result)

        is_correct = result["intent"] == sample["intent"]

        print(f"\n--- 测试 {i} ---")
        print(f"输入: {sample['text']}")
        print(f"期望: {sample['intent']}")
        print(f"预测: {result['intent']}")
        print(f"置信度: {result['confidence']:.2%}")
        print(f"结果: {'✅ 正确' if is_correct else '❌ 错误'}")

        # 显示置信度分解
        breakdown = result["confidence_breakdown"]
        print(
            f"置信度分解: Top1={breakdown['top_intent']:.2%}, "
            f"Top2={breakdown['second_intent']:.2%}, "
            f"Margin={breakdown['margin']:.2%}"
        )

    # 计算总体准确率
    correct = sum(
        1
        for r in results
        if r["intent"]
        == next(
            s["intent"]
            for s in test_data
            if s["text"]
            == next(
                k["text"]
                for k in [
                    {"text": r["predictions"]["base"]["pred"], "predictions": r["predictions"]}
                    for k in [r]
                ]
                if k["text"] == next(r["predictions"]["base"]["pred"] for r in [r])
            )
        )
    )

    accuracy = correct / len(test_data)

    # 评估模型
    evaluation = classifier.evaluate_model(test_data)

    print("\n" + "=" * 60)
    print("📊 最终评估结果:")
    print(f"   测试准确率: {accuracy:.4f} ({accuracy:.2%})")
    print(f"   模型准确率: {evaluation['accuracy']:.4f} ({evaluation['accuracy']:.2%})")
    print(f"   目标准确率: {classifier.target_accuracy:.2%}")
    print(f"   提升空间: {(classifier.target_accuracy - accuracy):.4f}")

    if accuracy >= 0.9:
        print("\n🎉 成功突破90%!继续努力可达到99%!")
    elif accuracy >= 0.8:
        print("\n✅ 超过80%,优化效果显著!")
    else:
        print("\n⚠️  需要进一步优化")

    # 保存评估结果
    results_dir = Path("/Users/xujian/Athena工作平台/evaluations")
    results_dir.mkdir(parents=True, exist_ok=True)

    evaluation_result = {
        "test_accuracy": accuracy,
        "evaluation": evaluation,
        "test_results": results,
        "timestamp": datetime.now().isoformat(),
        "model_version": "v99",
    }

    with open(
        results_dir / f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w"
    ) as f:
        json.dump(evaluation_result, f, ensure_ascii=False, indent=2)

    print("\n💾 评估结果已保存")


async def main():
    """主程序"""
    await test_ultra_classifier()


# 入口点: @async_main装饰器已添加到main函数
