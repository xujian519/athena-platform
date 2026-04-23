#!/usr/bin/env python3
from __future__ import annotations
"""
知识蒸馏引擎
Knowledge Distillation Engine

实现从规则系统到神经网络的知识转移:
1. 规则提取
2. 知识编码
3. 蒸馏训练
4. 保留验证

作者: 小诺·双鱼公主
创建时间: 2026-01-01
版本: 1.0.0
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

logger = logging.getLogger(__name__)


class DistillationMode(Enum):
    """蒸馏模式"""

    RULE_TO_NN = "rule_to_nn"  # 规则到神经网络
    NN_TO_NN = "nn_to_nn"  # 神经网络到神经网络
    ENSEMBLE_TO_SINGLE = "ensemble"  # 集成模型到单模型


@dataclass
class Rule:
    """规则定义"""

    name: str
    condition: str  # 条件表达式
    action: str  # 动作/输出
    priority: int = 1  # 优先级
    examples: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DistillationConfig:
    """蒸馏配置"""

    mode: DistillationMode = DistillationMode.RULE_TO_NN
    temperature: float = 3.0  # 温度参数
    alpha: float = 0.5  # 蒸馏损失权重
    beta: float = 0.5  # 任务损失权重
    learning_rate: float = 1e-3
    batch_size: int = 32
    epochs: int = 10
    save_path: str | None = None


class RuleExtractor:
    """
    规则提取器

    从现有系统中提取规则知识
    """

    def __init__(self):
        self.rules: list[Rule] = []

    def extract_from_ocr_optimizer(self) -> list[Rule]:
        """从OCR优化器提取规则"""
        rules = []

        # 文本纠错规则
        correction_rules = [
            Rule(
                name="数字符号转换",
                condition="text.contains('①②③④⑤⑥⑦⑧⑨⑩')",
                action="replace_with_chinese_numeral",
                priority=1,
                examples=["①②③ → 一二三", "⑩ → 十"],
                metadata={"category": "text_correction"},
            ),
            Rule(
                name="空格规范化",
                condition="text.contains_multiple_spaces()",
                action="remove_all_spaces",
                priority=2,
                examples=["这  是  测试 → 这是测试"],
                metadata={"category": "text_normalization"},
            ),
            Rule(
                name="标点符号规范化",
                condition="text.contains_chinese_punctuation()",
                action="convert_to_ascii",
                priority=1,
                examples=["[] → []", ", → ,"],
                metadata={"category": "text_normalization"},
            ),
        ]

        rules.extend(correction_rules)

        # 置信度计算规则
        confidence_rules = [
            Rule(
                name="中文比例加分",
                condition="chinese_ratio > 0.5",
                action="boost_confidence(+0.3)",
                priority=1,
                examples=["中文文本 → 置信度+0.3"],
                metadata={"category": "confidence_scoring"},
            ),
            Rule(
                name="常见汉字加分",
                condition="contains_common_chinese()",
                action="boost_confidence(+0.01)",
                priority=2,
                examples=["的、是一 → 置信度+0.01"],
                metadata={"category": "confidence_scoring"},
            ),
            Rule(
                name="文本长度验证",
                condition="10 <= length <= 100",
                action="boost_confidence(+0.1)",
                priority=2,
                examples=["10-100字符 → 置信度+0.1"],
                metadata={"category": "confidence_scoring"},
            ),
        ]

        rules.extend(confidence_rules)

        self.rules = rules
        logger.info(f"📋 提取了 {len(rules)} 条规则")

        return rules

    def extract_from_code(self, code_path: str) -> list[Rule]:
        """从代码中提取规则"""
        # 这里可以解析Python代码,提取if-else规则
        # 简化实现:返回空列表
        logger.info(f"📄 从代码提取规则: {code_path}")
        return []

    def save_rules(self, path: str):
        """保存规则到文件"""
        rules_data = [
            {
                "name": rule.name,
                "condition": rule.condition,
                "action": rule.action,
                "priority": rule.priority,
                "examples": rule.examples,
                "metadata": rule.metadata,
            }
            for rule in self.rules
        ]

        with open(path, "w", encoding="utf-8") as f:
            json.dump(rules_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 规则已保存: {path}")

    def load_rules(self, path: str) -> list[Rule]:
        """从文件加载规则"""
        with open(path, encoding="utf-8") as f:
            rules_data = json.load(f)

        self.rules = [
            Rule(
                name=data["name"],
                condition=data["condition"],
                action=data["action"],
                priority=data["priority"],
                examples=data["examples"],
                metadata=data["metadata"],
            )
            for data in rules_data
        ]

        logger.info(f"📂 加载了 {len(self.rules)} 条规则")
        return self.rules


class RuleEncoder(nn.Module):
    """
    规则编码器

    将规则编码为神经网络可理解的向量表示
    """

    def __init__(self, vocab_size: int = 10000, embed_dim: int = 256, hidden_dim: int = 512):
        super().__init__()

        # 规则文本编码
        self.embedding = nn.Embedding(vocab_size, embed_dim)

        # 条件编码器
        self.condition_encoder = nn.LSTM(
            embed_dim, hidden_dim, batch_first=True, bidirectional=True
        )

        # 动作编码器
        self.action_encoder = nn.LSTM(embed_dim, hidden_dim, batch_first=True, bidirectional=True)

        # 融合层
        self.fusion = nn.Linear(hidden_dim * 4, hidden_dim)

        # 输出头
        self.output = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, hidden_dim),
        )

    def forward(self, condition_ids: torch.Tensor, action_ids: torch.Tensor):
        """
        前向传播

        Args:
            condition_ids: 条则文本ID [batch, seq_len]
            action_ids: 动作文本ID [batch, seq_len]

        Returns:
            rule_vector: 规则向量表示 [batch, hidden_dim]
        """
        # 嵌入
        condition_emb = self.embedding(condition_ids)
        action_emb = self.embedding(action_ids)

        # 编码
        condition_hidden, _ = self.condition_encoder(condition_emb)
        action_hidden, _ = self.action_encoder(action_emb)

        # 取最后一个时间步
        condition_vec = condition_hidden[:, -1, :]
        action_vec = action_hidden[:, -1, :]

        # 拼接
        combined = torch.cat([condition_vec, action_vec], dim=-1)

        # 融合
        fused = self.fusion(combined)

        # 输出
        rule_vector = self.output(fused)

        return rule_vector


class RuleBasedTeacher(nn.Module):
    """
    基于规则的教师模型

    将规则系统包装为可微分的神经网络
    """

    def __init__(self, rules: list[Rule], vocab_size: int = 10000):
        super().__init__()

        self.rules = rules
        self.rule_encoder = RuleEncoder(vocab_size=vocab_size)

        # 规则权重 (可学习)
        self.rule_weights = nn.Parameter(torch.ones(len(rules)))

        logger.info(f"🎓 教师模型初始化: {len(rules)} 条规则")

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor):
        """
        前向传播

        Args:
            input_ids: 输入ID [batch, seq_len]
            attention_mask: 注意力掩码 [batch, seq_len]

        Returns:
            logits: 输出logits [batch, num_classes]
            soft_targets: 软目标 [batch, num_classes]
        """
        batch_size = input_ids.size(0)
        num_classes = 10  # 假设10个类别

        # 简化实现:基于规则的软目标
        # 实际应用中,这里会执行规则逻辑

        # 模拟规则输出
        soft_targets = torch.zeros(batch_size, num_classes, device=input_ids.device)

        # 根据规则生成输出
        for i, _rule in enumerate(self.rules):
            # 简化:为每个规则分配一个类别偏好
            weight = torch.sigmoid(self.rule_weights[i])

            # 假设每个规则偏向不同类别
            class_idx = i % num_classes
            soft_targets[:, class_idx] += weight * 0.5

        # 温度缩放
        temperature = 3.0
        soft_targets = F.softmax(soft_targets / temperature, dim=-1)

        return soft_targets, soft_targets


class StudentModel(nn.Module):
    """
    学生模型

    从教师模型学习的小型网络
    """

    def __init__(
        self,
        vocab_size: int = 10000,
        embed_dim: int = 128,
        hidden_dim: int = 256,
        num_classes: int = 10,
    ):
        super().__init__()

        # 嵌入层
        self.embedding = nn.Embedding(vocab_size, embed_dim)

        # 编码器
        self.encoder = nn.LSTM(
            embed_dim, hidden_dim, num_layers=2, batch_first=True, dropout=0.1, bidirectional=True
        )

        # 分类头
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, num_classes),
        )

        logger.info(
            f"👨‍🎓 学生模型初始化: vocab={vocab_size}, embed={embed_dim}, hidden={hidden_dim}"
        )

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor):
        """
        前向传播

        Args:
            input_ids: 输入ID [batch, seq_len]
            attention_mask: 注意力掩码 [batch, seq_len]

        Returns:
            logits: 输出logits [batch, num_classes]
        """
        # 嵌入
        emb = self.embedding(input_ids)

        # 编码
        hidden, _ = self.encoder(emb)

        # 取最后时间步
        pooled = hidden[:, -1, :]

        # 分类
        logits = self.classifier(pooled)

        return logits


class KnowledgeDistillation:
    """
    知识蒸馏引擎

    执行蒸馏训练和验证
    """

    def __init__(
        self, teacher_model: nn.Module, student_model: nn.Module, config: DistillationConfig
    ):
        self.teacher = teacher_model
        self.student = student_model
        self.config = config

        # 冻结教师参数
        for param in self.teacher.parameters():
            param.requires_grad = False

        # 优化器
        self.optimizer = torch.optim.Adam(self.student.parameters(), lr=config.learning_rate)

        # 学习率调度器
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=config.epochs
        )

        logger.info("🔥 知识蒸馏引擎初始化完成")

    def distillation_loss(
        self,
        student_logits: torch.Tensor,
        teacher_targets: torch.Tensor,
        true_labels: torch.Tensor,
        temperature: float,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        计算蒸馏损失

        Args:
            student_logits: 学生模型输出 [batch, num_classes]
            teacher_targets: 教师软目标 [batch, num_classes]
            true_labels: 真实标签 [batch]
            temperature: 温度参数

        Returns:
            total_loss: 总损失
            distill_loss: 蒸馏损失
            task_loss: 任务损失
        """
        # KL散度损失 (知识蒸馏)
        T = temperature

        # 学生软预测
        student_soft = F.log_softmax(student_logits / T, dim=-1)

        # 教师软目标 (已经经过温度缩放)
        teacher_soft = teacher_targets

        # KL散度
        distill_loss = F.kl_div(student_soft, teacher_soft, reduction="batchmean") * (T * T)

        # 任务损失 (交叉熵)
        task_loss = F.cross_entropy(student_logits, true_labels)

        # 加权组合
        total_loss = self.config.alpha * distill_loss + self.config.beta * task_loss

        return total_loss, distill_loss, task_loss

    def train_step(self, batch: dict[str, torch.Tensor]) -> dict[str, float]:
        """
        训练步骤

        Args:
            batch: 批次数据

        Returns:
            metrics: 指标字典
        """
        input_ids = batch["input_ids"]
        attention_mask = batch["attention_mask"]
        labels = batch["labels"]

        # 教师预测
        with torch.no_grad():
            _, teacher_targets = self.teacher(input_ids, attention_mask)

        # 学生预测
        student_logits = self.student(input_ids, attention_mask)

        # 计算损失
        loss, distill_loss, task_loss = self.distillation_loss(
            student_logits, teacher_targets, labels, self.config.temperature
        )

        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()

        # 梯度裁剪
        torch.nn.utils.clip_grad_norm_(self.student.parameters(), max_norm=1.0)

        self.optimizer.step()

        return {
            "loss": loss.item(),
            "distill_loss": distill_loss.item(),
            "task_loss": task_loss.item(),
        }

    @torch.no_grad()
    def evaluate(self, dataloader: DataLoader) -> dict[str, float]:
        """
        评估模型

        Args:
            dataloader: 数据加载器

        Returns:
            metrics: 评估指标
        """
        self.student.eval()

        total_loss = 0.0
        correct = 0
        total = 0

        for batch in dataloader:
            input_ids = batch["input_ids"]
            attention_mask = batch["attention_mask"]
            labels = batch["labels"]

            # 预测
            logits = self.student(input_ids, attention_mask)

            # 损失
            loss = F.cross_entropy(logits, labels)
            total_loss += loss.item() * input_ids.size(0)

            # 准确率
            preds = logits.argmax(dim=-1)
            correct += (preds == labels).sum().item()
            total += input_ids.size(0)

        self.student.train()

        return {"loss": total_loss / total, "accuracy": correct / total}

    def train(
        self,
        train_dataloader: DataLoader,
        val_dataloader: DataLoader | None = None,
        epochs: int | None = None,
    ) -> dict[str, list[float]]:
        """
        训练蒸馏模型

        Args:
            train_dataloader: 训练数据
            val_dataloader: 验证数据
            epochs: 训练轮数

        Returns:
            history: 训练历史
        """
        epochs = epochs or self.config.epochs

        history = {
            "train_loss": [],
            "train_distill_loss": [],
            "train_task_loss": [],
            "val_loss": [],
            "val_accuracy": [],
        }

        for epoch in range(epochs):
            # 训练
            epoch_metrics = {"loss": [], "distill_loss": [], "task_loss": []}

            for batch in train_dataloader:
                metrics = self.train_step(batch)

                for key, value in metrics.items():
                    epoch_metrics[key].append(value)

            # 记录训练指标
            for key in epoch_metrics:
                avg_value = np.mean(epoch_metrics[key])
                history[f"train_{key}"].append(avg_value)

            # 验证
            if val_dataloader:
                val_metrics = self.evaluate(val_dataloader)
                history["val_loss"].append(val_metrics["loss"])
                history["val_accuracy"].append(val_metrics["accuracy"])

            # 学习率调度
            self.scheduler.step()

            logger.info(
                f"Epoch {epoch+1}/{epochs}: "
                f"Loss={history['train_loss'][-1]:.4f}, "
                f"Distill={history['train_distill_loss'][-1]:.4f}, "
                f"Task={history['train_task_loss'][-1]:.4f}"
            )

        return history

    def compute_knowledge_retention(self, test_dataloader: DataLoader) -> dict[str, float]:
        """
        计算知识保留率

        Args:
            test_dataloader: 测试数据

        Returns:
            retention_metrics: 保留指标
        """
        self.teacher.eval()
        self.student.eval()

        teacher_correct = 0
        student_correct = 0
        agreement = 0
        total = 0

        for batch in test_dataloader:
            input_ids = batch["input_ids"]
            attention_mask = batch["attention_mask"]
            labels = batch["labels"]

            # 教师预测
            with torch.no_grad():
                _, teacher_targets = self.teacher(input_ids, attention_mask)
                teacher_preds = teacher_targets.argmax(dim=-1)

            # 学生预测
            with torch.no_grad():
                student_logits = self.student(input_ids, attention_mask)
                student_preds = student_logits.argmax(dim=-1)

            # 统计
            teacher_correct += (teacher_preds == labels).sum().item()
            student_correct += (student_preds == labels).sum().item()
            agreement += (teacher_preds == student_preds).sum().item()
            total += input_ids.size(0)

        teacher_acc = teacher_correct / total
        student_acc = student_correct / total
        agreement_rate = agreement / total

        # 知识保留率
        retention_rate = student_acc / teacher_acc if teacher_acc > 0 else 0

        return {
            "teacher_accuracy": teacher_acc,
            "student_accuracy": student_acc,
            "agreement_rate": agreement_rate,
            "knowledge_retention": retention_rate,
        }

    def save_student_model(self, path: str):
        """保存学生模型"""
        torch.save(
            {
                "model_state_dict": self.student.state_dict(),
                "config": self.config,
                "timestamp": datetime.now().isoformat(),
            },
            path,
        )

        logger.info(f"💾 学生模型已保存: {path}")

    def load_student_model(self, path: str):
        """加载学生模型"""
        checkpoint = torch.load(path)
        self.student.load_state_dict(checkpoint["model_state_dict"])
        logger.info(f"📂 学生模型已加载: {path}")


class RuleDataset(Dataset):
    """
    规则数据集

    用于蒸馏训练的数据集
    """

    def __init__(self, texts: list[str], labels: list[int], max_length: int = 128):
        self.texts = texts
        self.labels = labels
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx: int):
        self.texts[idx]
        label = self.labels[idx]

        # 简化:随机生成输入ID
        # 实际应用中需要使用tokenizer
        input_ids = torch.randint(0, 10000, (self.max_length,))
        attention_mask = torch.ones(self.max_length)

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": torch.tensor(label),
        }


# 导出
__all__ = [
    "DistillationConfig",
    "DistillationMode",
    "KnowledgeDistillation",
    "Rule",
    "RuleBasedTeacher",
    "RuleEncoder",
    "RuleExtractor",
    "StudentModel",
]


# 使用示例
if __name__ == "__main__":

    async def main():
        """测试知识蒸馏"""
        # 提取规则
        extractor = RuleExtractor()
        rules = extractor.extract_from_ocr_optimizer()

        # 保存规则
        extractor.save_rules("/tmp/ocr_rules.json")

        # 创建模型
        teacher = RuleBasedTeacher(rules)
        student = StudentModel()

        # 配置
        config = DistillationConfig(temperature=3.0, alpha=0.5, beta=0.5, epochs=5)

        # 蒸馏引擎
        distillation = KnowledgeDistillation(teacher, student, config)

        # 创建数据
        texts = ["测试文本"] * 100
        labels = [0] * 100
        dataset = RuleDataset(texts, labels)
        dataloader = DataLoader(dataset, batch_size=32)

        # 训练
        history = distillation.train(dataloader)

        print("✅ 知识蒸馏训练完成")
        print(f"   最终损失: {history['train_loss'][-1]:.4f}")

    asyncio.run(main())


# =============================================================================
# === 教师-学生模型类 ===
# =============================================================================

@dataclass
class TeacherStudentModel:
    """教师-学生模型"""

    teacher_model: Any  # 教师模型
    student_model: Any  # 学生模型
    distillation_config: DistillationConfig | None = None

    def train(
        self,
        train_data: Any,
        validation_data: Any | None = None,
    ) -> dict[str, Any]:
        """
        训练教师-学生模型

        Args:
            train_data: 训练数据
            validation_data: 验证数据

        Returns:
            训练历史
        """
        distillation = KnowledgeDistillation(
            self.teacher_model,
            self.student_model,
            self.distillation_config or DistillationConfig()
        )
        return distillation.train(train_data, validation_data)

    def get_student_accuracy(self, test_data: Any) -> float:
        """获取学生模型在测试数据上的准确率"""
        return 0.0  # 简化实现


# 创建便捷函数
def create_teacher_student_model(
    teacher_model: Any,
    student_model: Any,
    config: DistillationConfig | None = None,
) -> TeacherStudentModel:
    """创建教师-学生模型"""
    return TeacherStudentModel(
        teacher_model=teacher_model,
        student_model=student_model,
        distillation_config=config,
    )


__all__ = [
    "DistillationMode",
    "Rule",
    "RuleDataset",
    "DistillationConfig",
    "KnowledgeDistillation",
    "TeacherStudentModel",
    "create_teacher_student_model",
]
