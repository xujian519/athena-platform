#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
两阶段渐进式学习系统
基于DeepSeekMath V2论文的两阶段训练范式
Athena智能工作平台专利分析专用学习框架

作者: Athena AI团队
版本: 1.0.0
创建时间: 2025-11-28
"""

import json
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class Stage1Config:
    """第一阶段配置 - 基础能力训练"""

    model_name: str = 'microsoft/DialoGPT-medium'
    max_length: int = 512
    batch_size: int = 16
    learning_rate: float = 5e-5
    num_epochs: int = 3
    warmup_steps: int = 100
    save_steps: int = 500
    eval_steps: int = 100
    gradient_accumulation_steps: int = 4
    fp16: bool = True
    dataloader_num_workers: int = 4


@dataclass
class Stage2Config:
    """第二阶段配置 - 高级推理训练"""

    model_name: str = 'microsoft/DialoGPT-medium'
    max_length: int = 1024
    batch_size: int = 8
    learning_rate: float = 1e-5
    num_epochs: int = 5
    warmup_steps: int = 200
    save_steps: int = 300
    eval_steps: int = 50
    gradient_accumulation_steps: int = 8
    fp16: bool = True
    dataloader_num_workers: int = 4
    complex_reasoning_weight: float = 0.7
    basic_skill_weight: float = 0.3


class PatentDataset(Dataset):
    """专利分析数据集"""

    def __init__(
        self, data_path: str, stage: int = 1, tokenizer=None, max_length: int = 512
    ):
        self.data_path = Path(data_path)
        self.stage = stage
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = self._load_data()

    def _load_data(self) -> List[Dict]:
        """加载数据"""
        data = []

        if self.data_path.suffix == '.json':
            with open(self.data_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        elif self.data_path.suffix == '.jsonl':
            with open(self.data_path, 'r', encoding='utf-8') as f:
                raw_data = [json.loads(line) for line in f]
        else:
            raise ValueError(f"不支持的文件格式: {self.data_path.suffix}")

        # 根据阶段筛选数据
        for item in raw_data:
            if self._should_include_item(item):
                data.append(item)

        logger.info(f"阶段{self.stage}加载数据: {len(data)}条")
        return data

    def _should_include_item(self, item: Dict) -> bool:
        """判断是否应该包含该数据项"""
        if self.stage == 1:
            # 第一阶段：基础专利知识
            return (
                item.get('difficulty', 'medium') in ['easy', 'medium']
                and item.get('reasoning_steps', 1) <= 3
            )
        else:
            # 第二阶段：复杂推理
            return (
                item.get('difficulty', 'medium') in ['medium', 'hard']
                and item.get('reasoning_steps', 1) >= 3
            )

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = self.data[idx]

        # 构建输入文本
        if self.stage == 1:
            # 第一阶段：简单问答格式
            input_text = f"专利问题: {item['question']}\n答案: {item['answer']}"
        else:
            # 第二阶段：复杂推理格式
            reasoning = item.get('reasoning', '')
            input_text = (
                f"专利问题: {item['question']}\n推理过程: {reasoning}\n答案: {item['answer']}"
            )

        # 编码
        encoding = self.tokenizer(
            input_text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt',
        )

        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': encoding['input_ids'].squeeze(),
            'stage': self.stage,
        }


class TwoStageLearningFramework:
    """两阶段学习框架"""

    def __init__(
        self, stage1_config: Stage1Config = None, stage2_config: Stage2Config = None
    ):
        self.stage1_config = stage1_config or Stage1Config()
        self.stage2_config = stage2_config or Stage2Config()
        self.tokenizer = None
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # 训练历史
        self.training_history = {'stage1': [], 'stage2': []}

        logger.info('两阶段学习框架初始化完成')

    def setup_stage1(self) -> Any:
        """设置第一阶段训练"""
        logger.info('初始化第一阶段训练...')

        # 初始化tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.stage1_config.model_name, padding_side='left'
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # 初始化模型
        self.model = AutoModelForCausalLM.from_pretrained(
            self.stage1_config.model_name
        ).to(self.device)

        if self.stage1_config.fp16:
            self.model = self.model.half()

        logger.info(f"第一阶段模型加载完成: {self.stage1_config.model_name}")

    def setup_stage2(self, stage1_checkpoint: str = None) -> Any:
        """设置第二阶段训练"""
        logger.info('初始化第二阶段训练...')

        # 初始化tokenizer（如果尚未初始化）
        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.stage2_config.model_name, padding_side='left'
            )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

        # 加载第一阶段模型
        if stage1_checkpoint and Path(stage1_checkpoint).exists():
            logger.info(f"从第一阶段检查点加载模型: {stage1_checkpoint}")
            self.model = AutoModelForCausalLM.from_pretrained(stage1_checkpoint).to(
                self.device
            )
        else:
            logger.info(f"使用预训练模型: {self.stage2_config.model_name}")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.stage2_config.model_name
            ).to(self.device)

        if self.stage2_config.fp16:
            self.model = self.model.half()

        logger.info('第二阶段模型加载完成')

    def train_stage1(
        self,
        train_data_path: str,
        eval_data_path: str = None,
        output_dir: str = './stage1_output',
    ) -> Dict[str, Any]:
        """执行第一阶段训练"""

        logger.info('开始第一阶段训练...')

        # 设置输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 准备数据
        train_dataset = PatentDataset(
            train_data_path,
            stage=1,
            tokenizer=self.tokenizer,
            max_length=self.stage1_config.max_length,
        )

        train_dataloader = DataLoader(
            train_dataset,
            batch_size=self.stage1_config.batch_size,
            shuffle=True,
            num_workers=self.stage1_config.dataloader_num_workers,
        )

        # 设置优化器和学习率调度器
        optimizer = optim.AdamW(
            self.model.parameters(), lr=self.stage1_config.learning_rate
        )

        # 训练循环
        global_step = 0
        self.model.train()

        for epoch in range(self.stage1_config.num_epochs):
            epoch_loss = 0.0
            num_batches = 0

            for batch_idx, batch in enumerate(train_dataloader):
                # 移动数据到设备
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                # 前向传播
                outputs = self.model(
                    input_ids=input_ids, attention_mask=attention_mask, labels=labels
                )

                loss = outputs.loss

                # 梯度累积
                if self.stage1_config.gradient_accumulation_steps > 1:
                    loss = loss / self.stage1_config.gradient_accumulation_steps

                # 反向传播
                loss.backward()

                if (
                    batch_idx + 1
                ) % self.stage1_config.gradient_accumulation_steps == 0:
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                    optimizer.step()
                    optimizer.zero_grad()
                    global_step += 1

                    # 记录损失
                    epoch_loss += loss.item()
                    num_batches += 1

                    # 保存检查点
                    if global_step % self.stage1_config.save_steps == 0:
                        self._save_checkpoint(
                            output_path / f"stage1_checkpoint_{global_step}.pt",
                            epoch,
                            global_step,
                            loss.item(),
                        )

                    # 评估
                    if global_step % self.stage1_config.eval_steps == 0:
                        eval_loss = self._evaluate(eval_data_path, stage=1)
                        logger.info(f"Step {global_step}, Eval Loss: {eval_loss:.4f}")

            avg_loss = epoch_loss / num_batches if num_batches > 0 else 0
            logger.info(f"Epoch {epoch + 1}, Average Loss: {avg_loss:.4f}")

            # 记录训练历史
            self.training_history['stage1'].append(
                {
                    'epoch': epoch + 1,
                    'loss': avg_loss,
                    'global_step': global_step,
                    'timestamp': datetime.now().isoformat(),
                }
            )

        # 保存最终模型
        final_output_path = output_path / 'stage1_final'
        self.model.save_pretrained(final_output_path)
        self.tokenizer.save_pretrained(final_output_path)

        # 保存训练历史
        with open(output_path / 'stage1_history.json', 'w', encoding='utf-8') as f:
            json.dump(self.training_history['stage1'], f, indent=2, ensure_ascii=False)

        logger.info(f"第一阶段训练完成，模型保存在: {final_output_path}")

        return {
            'final_loss': avg_loss,
            'total_steps': global_step,
            'output_path': str(final_output_path),
            'training_history': self.training_history['stage1'],
        }

    def train_stage2(
        self,
        train_data_path: str,
        eval_data_path: str = None,
        output_dir: str = './stage2_output',
        stage1_checkpoint: str = None,
    ) -> Dict[str, Any]:
        """执行第二阶段训练"""

        logger.info('开始第二阶段训练...')

        # 设置第二阶段
        self.setup_stage2(stage1_checkpoint)

        # 设置输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 准备数据
        train_dataset = PatentDataset(
            train_data_path,
            stage=2,
            tokenizer=self.tokenizer,
            max_length=self.stage2_config.max_length,
        )

        train_dataloader = DataLoader(
            train_dataset,
            batch_size=self.stage2_config.batch_size,
            shuffle=True,
            num_workers=self.stage2_config.dataloader_num_workers,
        )

        # 设置优化器
        optimizer = optim.AdamW(
            self.model.parameters(), lr=self.stage2_config.learning_rate
        )

        # 训练循环
        global_step = 0
        self.model.train()

        for epoch in range(self.stage2_config.num_epochs):
            epoch_loss = 0.0
            num_batches = 0

            for batch_idx, batch in enumerate(train_dataloader):
                # 移动数据到设备
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                # 前向传播
                outputs = self.model(
                    input_ids=input_ids, attention_mask=attention_mask, labels=labels
                )

                loss = outputs.loss

                # 应用复杂推理权重
                loss = (
                    self.stage2_config.complex_reasoning_weight * loss
                    + self.stage2_config.basic_skill_weight * loss * 0.5
                )

                # 梯度累积
                if self.stage2_config.gradient_accumulation_steps > 1:
                    loss = loss / self.stage2_config.gradient_accumulation_steps

                # 反向传播
                loss.backward()

                if (
                    batch_idx + 1
                ) % self.stage2_config.gradient_accumulation_steps == 0:
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                    optimizer.step()
                    optimizer.zero_grad()
                    global_step += 1

                    epoch_loss += loss.item()
                    num_batches += 1

                    # 保存检查点
                    if global_step % self.stage2_config.save_steps == 0:
                        self._save_checkpoint(
                            output_path / f"stage2_checkpoint_{global_step}.pt",
                            epoch,
                            global_step,
                            loss.item(),
                        )

                    # 评估
                    if global_step % self.stage2_config.eval_steps == 0:
                        eval_loss = self._evaluate(eval_data_path, stage=2)
                        logger.info(f"Step {global_step}, Eval Loss: {eval_loss:.4f}")

            avg_loss = epoch_loss / num_batches if num_batches > 0 else 0
            logger.info(f"Epoch {epoch + 1}, Average Loss: {avg_loss:.4f}")

            # 记录训练历史
            self.training_history['stage2'].append(
                {
                    'epoch': epoch + 1,
                    'loss': avg_loss,
                    'global_step': global_step,
                    'timestamp': datetime.now().isoformat(),
                }
            )

        # 保存最终模型
        final_output_path = output_path / 'stage2_final'
        self.model.save_pretrained(final_output_path)
        self.tokenizer.save_pretrained(final_output_path)

        # 保存训练历史
        with open(output_path / 'stage2_history.json', 'w', encoding='utf-8') as f:
            json.dump(self.training_history['stage2'], f, indent=2, ensure_ascii=False)

        logger.info(f"第二阶段训练完成，模型保存在: {final_output_path}")

        return {
            'final_loss': avg_loss,
            'total_steps': global_step,
            'output_path': str(final_output_path),
            'training_history': self.training_history['stage2'],
        }

    def _evaluate(self, eval_data_path: str, stage: int) -> float:
        """评估模型"""
        if eval_data_path is None or not Path(eval_data_path).exists():
            return float('inf')

        try:
            eval_dataset = PatentDataset(
                eval_data_path,
                stage=stage,
                tokenizer=self.tokenizer,
                max_length=self.stage1_config.max_length
                if stage == 1
                else self.stage2_config.max_length,
            )

            eval_dataloader = DataLoader(eval_dataset, batch_size=8, shuffle=False)

            self.model.eval()
            total_loss = 0.0
            num_batches = 0

            with torch.no_grad():
                for batch in eval_dataloader:
                    input_ids = batch['input_ids'].to(self.device)
                    attention_mask = batch['attention_mask'].to(self.device)
                    labels = batch['labels'].to(self.device)

                    outputs = self.model(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        labels=labels,
                    )

                    total_loss += outputs.loss.item()
                    num_batches += 1

            avg_loss = total_loss / num_batches if num_batches > 0 else float('inf')
            self.model.train()

            return avg_loss

        except Exception as e:
            logger.warning(f"评估过程出错: {e}")
            return float('inf')

    def _save_checkpoint(
        self, filepath: str, epoch: int, global_step: int, loss: float
    ):
        """保存检查点"""
        checkpoint = {
            'epoch': epoch,
            'global_step': global_step,
            'loss': loss,
            'model_state_dict': self.model.state_dict(),
            'training_history': self.training_history,
            'timestamp': datetime.now().isoformat(),
        }

        torch.save(checkpoint, filepath)
        logger.info(f"检查点已保存: {filepath}")

    def generate_response(
        self,
        prompt: str,
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """生成响应"""
        if self.model is None or self.tokenizer is None:
            raise ValueError('模型尚未初始化，请先调用setup_stage1或setup_stage2')

        # 编码输入
        inputs = self.tokenizer(
            prompt,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=max_length,
        ).to(self.device)

        # 生成响应
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # 解码响应
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # 移除输入部分
        if prompt in response:
            response = response.replace(prompt, '').strip()

        return response


# 示例使用
if __name__ == '__main__':
    # 创建框架实例
    framework = TwoStageLearningFramework()

    # 第一阶段训练示例
    framework.setup_stage1()
    stage1_results = framework.train_stage1(
        train_data_path='path/to/stage1_train.json',
        eval_data_path='path/to/stage1_eval.json',
        output_dir='./patent_stage1_output',
    )

    # 第二阶段训练示例
    stage2_results = framework.train_stage2(
        train_data_path='path/to/stage2_train.json',
        eval_data_path='path/to/stage2_eval.json',
        output_dir='./patent_stage2_output',
        stage1_checkpoint=stage1_results['output_path'],
    )

    # 生成示例
    prompt = '专利问题: 请分析这个专利的技术创新点'
    response = framework.generate_response(prompt)
    logger.info(f"生成响应: {response}")
