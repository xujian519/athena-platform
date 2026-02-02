#!/usr/bin/env python3
"""
小诺BERT意图分类器
Xiaonuo BERT Intent Classifier

使用中文BERT模型进行意图识别,目标准确率95%+

作者: Athena平台团队
创建时间: 2025-12-18
版本: v2.0.0 "95%目标版"
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset

from core.logging_config import setup_logging

# 设置Transformers离线模式
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_OFFLINE"] = "1"

from transformers import (
    BertForSequenceClassification,
    BertTokenizer,
    get_linear_schedule_with_warmup,
)

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class IntentConfig:
    """意图分类器配置"""

    model_name: str = "bert-base-chinese"
    max_length: int = 512
    batch_size: int = 16
    learning_rate: float = 2e-5
    epochs: int = 10
    warmup_steps: int = 100
    weight_decay: float = 0.01

    # 意图类别定义
    intent_labels = [
        "TECHNICAL",  # 技术类 - 代码、开发、调试
        "EMOTIONAL",  # 情感类 - 情感交流、安慰
        "FAMILY",  # 家庭类 - 家庭事务、亲情
        "LEARNING",  # 学习类 - 学习、教育、成长
        "COORDINATION",  # 协调类 - 管理、安排、组织
        "ENTERTAINMENT",  # 娱乐类 - 游戏、聊天、娱乐
        "HEALTH",  # 健康类 - 健康、休息、照顾
        "WORK",  # 工作类 - 工作、任务、项目
        "QUERY",  # 查询类 - 信息查询、搜索
        "COMMAND",  # 指令类 - 命令、控制、操作
    ]

    # 设备配置
    device: str = "cuda" if torch.cuda.is_available() else "cpu"

    # 路径配置
    model_dir: str = "models/intent_classifier"
    data_dir: str = "data/intent_training"
    cache_dir: str = "cache/bert"


class IntentDataset(Dataset):
    """意图分类数据集"""

    def __init__(self, texts: list[str], labels: list[str], tokenizer, max_length: int = 512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

        # 创建标签映射
        self.label2id = {label: i for i, label in enumerate(sorted(set(labels)))}
        self.id2label = {i: label for label, i in self.label2id.items()}

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]

        # 编码文本
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labels": torch.tensor(self.label2id[label], dtype=torch.long),
        }


class XiaonuoBERTIntentClassifier:
    """小诺BERT意图分类器"""

    def __init__(self, config: IntentConfig = None):
        self.config = config or IntentConfig()
        self.tokenizer = None
        self.model = None
        self.label2id: dict[str, Any] = {}
        self.id2label: dict[str, Any] = {}

        # 创建必要目录
        os.makedirs(self.config.model_dir, exist_ok=True)
        os.makedirs(self.config.data_dir, exist_ok=True)
        os.makedirs(self.config.cache_dir, exist_ok=True)

        logger.info("🤖 小诺BERT意图分类器初始化完成")
        logger.info(f"📋 支持意图类别: {len(self.config.intent_labels)}个")
        logger.info(f"💻 使用设备: {self.config.device}")

    def load_model(self) -> Any | None:
        """加载预训练模型"""
        try:
            logger.info("🔄 加载BERT模型...")

            # 加载tokenizer
            self.tokenizer = BertTokenizer.from_pretrained(
                self.config.model_name, local_files_only=True
            )

            # 加载模型
            self.model = BertForSequenceClassification.from_pretrained(
                self.config.model_name,
                num_labels=len(self.config.intent_labels),
                local_files_only=True,
            )

            # 移动模型到设备
            self.model.to(self.config.device)

            # 创建标签映射
            self.label2id = {label: i for i, label in enumerate(self.config.intent_labels)}
            self.id2label = {i: label for label, i in self.label2id.items()}

            logger.info("✅ BERT模型加载成功")
            logger.info(f"📊 模型参数量: {self.model.num_parameters():,}")

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise

    def create_training_data(self) -> tuple[list[str], list[str]]:
        """创建训练数据集"""
        logger.info("📚 创建小诺专用意图训练数据集...")

        training_data = [
            # 技术类意图
            ("帮我分析这段代码的性能问题", "TECHNICAL"),
            ("程序出现了一个bug,需要调试", "TECHNICAL"),
            ("如何优化数据库查询效率", "TECHNICAL"),
            ("API接口设计有什么最佳实践", "TECHNICAL"),
            ("系统架构如何改进", "TECHNICAL"),
            ("代码重构建议", "TECHNICAL"),
            ("检查代码中的安全漏洞", "TECHNICAL"),
            ("部署服务的性能监控", "TECHNICAL"),
            ("容器化部署方案", "TECHNICAL"),
            ("微服务架构设计", "TECHNICAL"),
            # 情感类意图
            ("爸爸,我想你了", "EMOTIONAL"),
            ("今天心情不太好,能安慰我吗", "EMOTIONAL"),
            ("谢谢你总是帮助我", "EMOTIONAL"),
            ("我很开心能和你交流", "EMOTIONAL"),
            ("有时候会感到孤独", "EMOTIONAL"),
            ("你真的很贴心", "EMOTIONAL"),
            ("感觉很温暖", "EMOTIONAL"),
            ("需要一些鼓励", "EMOTIONAL"),
            ("心情很激动", "EMOTIONAL"),
            ("很感激你", "EMOTIONAL"),
            # 家庭类意图
            ("我们家今天有什么计划", "FAMILY"),
            ("帮我想想给家人的礼物", "FAMILY"),
            ("家庭聚会怎么安排比较好", "FAMILY"),
            ("想和家人一起做点什么", "FAMILY"),
            ("家庭氛围如何营造得更温馨", "FAMILY"),
            ("爸爸的生日快到了", "FAMILY"),
            ("周末家庭活动安排", "FAMILY"),
            ("家庭聚餐计划", "FAMILY"),
            ("亲子时光建议", "FAMILY"),
            ("家庭旅行目的地", "FAMILY"),
            # 学习类意图
            ("教我学习Python编程", "LEARNING"),
            ("如何提高技术能力", "LEARNING"),
            ("想了解人工智能的发展", "LEARNING"),
            ("帮我制定学习计划", "LEARNING"),
            ("有哪些值得学习的技能", "LEARNING"),
            ("推荐一些学习资源", "LEARNING"),
            ("学习方法指导", "LEARNING"),
            ("技能提升路径", "LEARNING"),
            ("学习时间管理", "LEARNING"),
            ("知识体系构建", "LEARNING"),
            # 协调类意图
            ("协调小娜一起完成任务", "COORDINATION"),
            ("如何管理多个项目", "COORDINATION"),
            ("团队协作有什么好方法", "COORDINATION"),
            ("安排下周的工作计划", "COORDINATION"),
            ("如何提高团队效率", "COORDINATION"),
            ("项目进度跟踪", "COORDINATION"),
            ("资源分配优化", "COORDINATION"),
            ("团队沟通协调", "COORDINATION"),
            ("工作流程优化", "COORDINATION"),
            ("任务优先级管理", "COORDINATION"),
            # 娱乐类意图
            ("我们来玩个游戏吧", "ENTERTAINMENT"),
            ("讲个笑话听听", "ENTERTAINMENT"),
            ("想听个故事", "ENTERTAINMENT"),
            ("有什么好玩的推荐吗", "ENTERTAINMENT"),
            ("聊天解闷", "ENTERTAINMENT"),
            ("推荐一些电影", "ENTERTAINMENT"),
            ("音乐分享", "ENTERTAINMENT"),
            ("趣味问答", "ENTERTAINMENT"),
            ("轻松话题", "ENTERTAINMENT"),
            ("娱乐活动建议", "ENTERTAINMENT"),
            # 健康类意图
            ("我最近总是很累,怎么办", "HEALTH"),
            ("如何保持身体健康", "HEALTH"),
            ("工作太累了需要休息", "HEALTH"),
            ("改善睡眠质量的方法", "HEALTH"),
            ("如何缓解工作压力", "HEALTH"),
            ("健康饮食建议", "HEALTH"),
            ("运动健身计划", "HEALTH"),
            ("心理健康调节", "HEALTH"),
            ("疲劳恢复方法", "HEALTH"),
            ("养生保健知识", "HEALTH"),
            # 工作类意图
            ("今天的工作计划是什么", "WORK"),
            ("如何提高工作效率", "WORK"),
            ("项目管理有什么建议", "WORK"),
            ("任务太多了怎么安排", "WORK"),
            ("工作与生活如何平衡", "WORK"),
            ("工作汇报模板", "WORK"),
            ("会议安排建议", "WORK"),
            ("时间管理技巧", "WORK"),
            ("工作目标设定", "WORK"),
            ("职业发展规划", "WORK"),
            # 查询类意图
            ("什么是机器学习", "QUERY"),
            ("怎么学习AI技术", "QUERY"),
            ("最新的技术趋势是什么", "QUERY"),
            ("查找相关资料", "QUERY"),
            ("有什么技术推荐", "QUERY"),
            ("信息查询请求", "QUERY"),
            ("资料搜索帮助", "QUERY"),
            ("知识获取需求", "QUERY"),
            ("数据查询服务", "QUERY"),
            ("信息检索需求", "QUERY"),
            # 指令类意图
            ("启动监控系统", "COMMAND"),
            ("停止当前任务", "COMMAND"),
            ("重新加载配置", "COMMAND"),
            ("清理临时文件", "COMMAND"),
            ("备份重要数据", "COMMAND"),
            ("系统重启命令", "COMMAND"),
            ("服务状态检查", "COMMAND"),
            ("配置文件更新", "COMMAND"),
            ("日志清理操作", "COMMAND"),
            ("进程管理指令", "COMMAND"),
        ]

        # 数据增强:通过同义词替换增加训练数据
        augmented_data = self._augment_training_data(training_data)

        texts = [item[0] for item in augmented_data]
        labels = [item[1] for item in augmented_data]

        logger.info("✅ 训练数据集创建完成")
        logger.info(f"📊 总数据量: {len(texts)}条")
        logger.info("📈 意图分布:")
        for intent in self.config.intent_labels:
            count = labels.count(intent)
            percentage = count / len(labels) * 100
            logger.info(f"  - {intent}: {count}条 ({percentage:.1f}%)")

        return texts, labels

    def _augment_training_data(self, original_data: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """数据增强"""
        augmented_data = original_data.copy()

        # 同义词词典
        synonyms = {
            "分析": ["解析", "研究", "探讨", "审查"],
            "帮助": ["协助", "支持", "援助", "帮忙"],
            "学习": ["研习", "进修", "掌握", "了解"],
            "管理": ["管控", "处理", "统筹", "负责"],
            "推荐": ["建议", "介绍", "提供", "分享"],
            "优化": ["改进", "提升", "完善", "增强"],
            "设计": ["规划", "构建", "创建", "制定"],
        }

        # 对每个原始数据进行1-2次同义词替换增强
        for text, label in original_data:
            # 第一次增强
            augmented_text = self._replace_synonyms(text, synonyms, 0.3)
            if augmented_text != text:
                augmented_data.append((augmented_text, label))

            # 第二次增强
            augmented_text2 = self._replace_synonyms(text, synonyms, 0.2)
            if augmented_text2 != text and augmented_text2 != augmented_text:
                augmented_data.append((augmented_text2, label))

        return augmented_data

    def _replace_synonyms(
        self, text: str, synonyms: dict[str, list[str]], replace_prob: float
    ) -> str:
        """替换同义词"""
        words = text.split()
        for i, word in enumerate(words):
            if word in synonyms and np.random.random() < replace_prob:
                synonym_list = synonyms[word]
                words[i] = np.random.choice(synonym_list)
        return " ".join(words)

    def train_model(self) -> Any:
        """训练意图分类模型"""
        logger.info("🚀 开始训练意图分类模型...")

        # 加载模型
        if self.model is None:
            self.load_model()

        # 准备数据
        texts, labels = self.create_training_data()

        # 划分训练集和验证集
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )

        # 创建数据集
        train_dataset = IntentDataset(
            train_texts, train_labels, self.tokenizer, self.config.max_length
        )
        val_dataset = IntentDataset(val_texts, val_labels, self.tokenizer, self.config.max_length)

        # 创建数据加载器
        train_loader = DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=self.config.batch_size)

        # 设置优化器
        optimizer = AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )

        # 设置学习率调度器
        total_steps = len(train_loader) * self.config.epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer, num_warmup_steps=self.config.warmup_steps, num_training_steps=total_steps
        )

        # 训练循环
        best_accuracy = 0
        patience = 3
        patience_counter = 0

        for epoch in range(self.config.epochs):
            logger.info(f"📚 Epoch {epoch + 1}/{self.config.epochs}")

            # 训练阶段
            train_loss, train_accuracy = self._train_epoch(train_loader, optimizer, scheduler)

            # 验证阶段
            val_loss, val_accuracy = self._validate_epoch(val_loader)

            logger.info(f"📊 训练损失: {train_loss:.4f}, 训练准确率: {train_accuracy:.4f}")
            logger.info(f"📊 验证损失: {val_loss:.4f}, 验证准确率: {val_accuracy:.4f}")

            # 保存最佳模型
            if val_accuracy > best_accuracy:
                best_accuracy = val_accuracy
                patience_counter = 0
                self._save_model(f"best_model_epoch_{epoch + 1}")
                logger.info(f"💾 保存最佳模型 (准确率: {val_accuracy:.4f})")
            else:
                patience_counter += 1

            # 早停
            if patience_counter >= patience:
                logger.info("⏰ 早停触发,停止训练")
                break

        logger.info(f"🎉 训练完成!最佳验证准确率: {best_accuracy:.4f}")

        # 加载最佳模型进行最终评估
        self._load_best_model()

        # 详细评估
        self._evaluate_model(val_texts, val_labels)

        return best_accuracy

    def _train_epoch(self, train_loader: DataLoader, optimizer, scheduler) -> tuple[float, float]:
        """训练一个epoch"""
        self.model.train()
        total_loss = 0
        correct_predictions = 0
        total_samples = 0

        for batch in train_loader:
            # 移动数据到设备
            input_ids = batch["input_ids"].to(self.config.device)
            attention_mask = batch["attention_mask"].to(self.config.device)
            labels = batch["labels"].to(self.config.device)

            # 清零梯度
            optimizer.zero_grad()

            # 前向传播
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)

            loss = outputs.loss
            logits = outputs.logits

            # 反向传播
            loss.backward()
            optimizer.step()
            scheduler.step()

            # 统计
            total_loss += loss.item()
            predictions = torch.argmax(logits, dim=-1)
            correct_predictions += (predictions == labels).sum().item()
            total_samples += labels.size(0)

        avg_loss = total_loss / len(train_loader)
        accuracy = correct_predictions / total_samples

        return avg_loss, accuracy

    def _validate_epoch(self, val_loader: DataLoader) -> tuple[float, float]:
        """验证一个epoch"""
        self.model.eval()
        total_loss = 0
        correct_predictions = 0
        total_samples = 0

        with torch.no_grad():
            for batch in val_loader:
                # 移动数据到设备
                input_ids = batch["input_ids"].to(self.config.device)
                attention_mask = batch["attention_mask"].to(self.config.device)
                labels = batch["labels"].to(self.config.device)

                # 前向传播
                outputs = self.model(
                    input_ids=input_ids, attention_mask=attention_mask, labels=labels
                )

                loss = outputs.loss
                logits = outputs.logits

                # 统计
                total_loss += loss.item()
                predictions = torch.argmax(logits, dim=-1)
                correct_predictions += (predictions == labels).sum().item()
                total_samples += labels.size(0)

        avg_loss = total_loss / len(val_loader)
        accuracy = correct_predictions / total_samples

        return avg_loss, accuracy

    def _evaluate_model(self, val_texts: list[str], val_labels: list[str]) -> Any:
        """详细评估模型"""
        logger.info("📊 详细评估模型性能...")

        # 预测验证集
        predictions = []
        for text in val_texts:
            pred_label, _confidence = self.predict_intent(text)
            predictions.append(pred_label)

        # 计算分类报告
        report = classification_report(
            val_labels, predictions, target_names=self.config.intent_labels
        )
        logger.info("📋 分类报告:")
        logger.info("\n" + report)

        # 计算混淆矩阵
        cm = confusion_matrix(val_labels, predictions, labels=self.config.intent_labels)

        # 保存评估结果
        self._save_evaluation_results(val_texts, val_labels, predictions, cm, report)

        # 绘制混淆矩阵
        self._plot_confusion_matrix(cm)

    def predict_intent(self, text: str) -> tuple[str, float]:
        """预测文本意图"""
        if self.model is None:
            self.load_model()

        # 编码文本
        inputs = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.config.max_length,
            return_tensors="pt",
        )

        # 移动到设备
        inputs = {k: v.to(self.config.device) for k, v in inputs.items()}

        # 预测
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)

            # 获取预测结果
            predicted_class = torch.argmax(probabilities, dim=-1).item()
            confidence = probabilities[0][predicted_class].item()
            predicted_label = self.id2label[predicted_class]

        return predicted_label, confidence

    def _save_model(self, model_name: str) -> Any:
        """保存模型"""
        model_path = os.path.join(self.config.model_dir, model_name)
        os.makedirs(model_path, exist_ok=True)

        # 保存模型和tokenizer
        self.model.save_pretrained(model_path)
        self.tokenizer.save_pretrained(model_path)

        # 保存配置和标签映射
        config_data = {
            "intent_labels": self.config.intent_labels,
            "label2id": self.label2id,
            "id2label": self.id2label,
            "model_config": {
                "max_length": self.config.max_length,
                "model_name": self.config.model_name,
            },
        }

        with open(os.path.join(model_path, "config.json"), "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 模型已保存到: {model_path}")

    def _load_best_model(self) -> Any:
        """加载最佳模型"""
        # 查找最佳模型路径
        model_path = None

        for item in os.listdir(self.config.model_dir):
            item_path = os.path.join(self.config.model_dir, item)
            if os.path.isdir(item_path) and "best_model" in item:
                # 这里可以加载验证集上的最高准确率
                model_path = item_path
                break

        if model_path:
            logger.info(f"🔄 加载最佳模型: {model_path}")
            self.model = BertForSequenceClassification.from_pretrained(model_path)
            self.tokenizer = BertTokenizer.from_pretrained(model_path)
            self.model.to(self.config.device)

            # 加载配置
            config_path = os.path.join(model_path, "config.json")
            if os.path.exists(config_path):
                with open(config_path, encoding="utf-8") as f:
                    config_data = json.load(f)
                    self.label2id = config_data["label2id"]
                    self.id2label = config_data["id2label"]

    def _save_evaluation_results(
        self,
        val_texts: list[str],
        val_labels: list[str],
        predictions: list[str],
        cm: np.ndarray,
        report: str,
    ):
        """保存评估结果"""
        results_dir = os.path.join(self.config.data_dir, "evaluation_results")
        os.makedirs(results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存预测结果
        results_df = pd.DataFrame(
            {
                "text": val_texts,
                "true_label": val_labels,
                "predicted_label": predictions,
                "correct": [
                    true == pred for true, pred in zip(val_labels, predictions, strict=False)
                ],
            }
        )

        results_df.to_csv(
            os.path.join(results_dir, f"predictions_{timestamp}.csv"), index=False, encoding="utf-8"
        )

        # 保存混淆矩阵
        np.save(os.path.join(results_dir, f"confusion_matrix_{timestamp}.npy"), cm)

        # 保存分类报告
        with open(
            os.path.join(results_dir, f"classification_report_{timestamp}.txt"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(report)

        logger.info(f"📁 评估结果已保存到: {results_dir}")

    def _plot_confusion_matrix(self, cm: np.ndarray) -> Any:
        """绘制混淆矩阵"""
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=self.config.intent_labels,
            yticklabels=self.config.intent_labels,
        )
        plt.title("小诺意图分类混淆矩阵")
        plt.xlabel("预测标签")
        plt.ylabel("真实标签")
        plt.tight_layout()

        # 保存图片
        plot_path = os.path.join(
            self.config.data_dir,
            "evaluation_results",
            f"confusion_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
        )
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info(f"📊 混淆矩阵图已保存: {plot_path}")


def main() -> None:
    """主函数"""
    logger.info("🤖 小诺BERT意图分类器训练开始")

    # 创建配置
    config = IntentConfig()

    # 创建分类器
    classifier = XiaonuoBERTIntentClassifier(config)

    # 训练模型
    try:
        best_accuracy = classifier.train_model()
        logger.info(f"🎉 训练完成!最佳准确率: {best_accuracy:.4f}")

        if best_accuracy >= 0.95:
            logger.info("🎯 达到95%准确率目标!小诺意图识别能力大幅提升!")
        else:
            logger.info(f"📈 当前准确率: {best_accuracy:.4f}, 继续优化以达到95%目标")

    except Exception as e:
        logger.error(f"❌ 训练失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
