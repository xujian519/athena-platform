#!/usr/bin/env python3
"""
端到端神经网络模型
End-to-End Neural Network Model

实现感知→认知→执行的端到端优化:
1. 感知编码器 (Perception Encoder)
2. 认知编码器 (Cognition Encoder)
3. 执行解码器 (Execution Decoder)
4. 共享表示空间 (Latent Space)

作者: 小诺·双鱼公主
创建时间: 2026-01-01
版本: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import (
    BertModel,
    ViTModel,
)


logger = logging.getLogger(__name__)


class ModelSize(Enum):
    """模型规模"""

    TINY = "tiny"  # 50M参数
    SMALL = "small"  # 200M参数
    MEDIUM = "medium"  # 500M参数
    LARGE = "large"  # 1B参数
    XLARGE = "xlarge"  # 3B参数


@dataclass
class ModelConfig:
    """模型配置"""

    # 模型规模
    size: ModelSize = ModelSize.SMALL

    # 感知编码器配置
    text_encoder: str = "bert-base-chinese"
    image_encoder: str = "google/vit-base-patch16-224"
    audio_encoder: str | None = None  # 可选

    # 认知编码器配置
    cognition_layers: int = 6
    cognition_heads: int = 8
    cognition_d_model: int = 512
    cognition_d_ff: int = 2048

    # 执行解码器配置
    execution_layers: int = 6
    execution_heads: int = 8
    execution_d_model: int = 512
    execution_d_ff: int = 2048

    # 共享表示空间
    latent_dim: int = 512

    # 其他
    dropout: float = 0.1
    max_seq_len: int = 512
    vocab_size: int = 50257  # GPT-2 vocab size

    # 设备
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


@dataclass
class ModelInput:
    """模型输入"""

    # 文本输入
    input_ids: torch.Tensor  # [batch, seq_len]
    attention_mask: torch.Tensor  # [batch, seq_len]

    # 图像输入 (可选)
    pixel_values: torch.Tensor | None = None  # [batch, C, H, W]

    # 音频输入 (可选)
    audio_values: torch.Tensor | None = None

    # 元数据
    task_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelOutput:
    """模型输出"""

    # 预测的动作序列
    predicted_actions: torch.Tensor  # [batch, action_seq_len, vocab_size]

    # 共享表示
    latent_repr: torch.Tensor  # [batch, seq_len, latent_dim]

    # 置信度
    confidence: torch.Tensor  # [batch]

    # 其他
    hidden_states: tuple[torch.Tensor, ...] | None = None
    attentions: tuple[torch.Tensor, ...] | None = None


# ==================== 感知编码器 ====================


class TextEncoder(nn.Module):
    """文本编码器"""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config

        # 使用预训练BERT
        self.bert = BertModel.from_pretrained(config.text_encoder)

        # 投影到共享表示空间
        self.projection = nn.Linear(self.bert.config.hidden_size, config.latent_dim)

        self.dropout = nn.Dropout(config.dropout)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """
        编码文本

        Args:
            input_ids: [batch, seq_len]
            attention_mask: [batch, seq_len]

        Returns:
            encoded: [batch, seq_len, latent_dim]
        """
        # BERT编码
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)

        # 取最后一层隐藏状态
        hidden_state = outputs.last_hidden_state  # [batch, seq_len, hidden_size]

        # 投影到共享空间
        encoded = self.projection(hidden_state)  # [batch, seq_len, latent_dim]
        encoded = self.dropout(encoded)

        return encoded


class ImageEncoder(nn.Module):
    """图像编码器"""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config

        # 使用预训练ViT
        self.vit = ViTModel.from_pretrained(config.image_encoder)

        # 投影到共享表示空间
        self.projection = nn.Linear(self.vit.config.hidden_size, config.latent_dim)

        self.dropout = nn.Dropout(config.dropout)

    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        """
        编码图像

        Args:
            pixel_values: [batch, C, H, W]

        Returns:
            encoded: [batch, num_patches, latent_dim]
        """
        # ViT编码
        outputs = self.vit(pixel_values=pixel_values)

        # 取最后一层隐藏状态
        hidden_state = outputs.last_hidden_state  # [batch, num_patches, hidden_size]

        # 投影到共享空间
        encoded = self.projection(hidden_state)
        encoded = self.dropout(encoded)

        return encoded


class MultimodalFusion(nn.Module):
    """多模态融合模块"""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.latent_dim = config.latent_dim

        # 融合策略: cross-attention
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=self.latent_dim,
            num_heads=config.cognition_heads,
            dropout=config.dropout,
            batch_first=True,
        )

        self.layer_norm = nn.LayerNorm(self.latent_dim)
        self.dropout = nn.Dropout(config.dropout)

    def forward(
        self, text_encoded: torch.Tensor, image_encoded: torch.Tensor | None = None
    ) -> torch.Tensor:
        """
        融合多模态输入

        Args:
            text_encoded: [batch, text_len, latent_dim]
            image_encoded: [batch, img_len, latent_dim] (可选)

        Returns:
            fused: [batch, text_len, latent_dim]
        """
        fused = text_encoded

        # 如果有图像,进行cross-attention融合
        if image_encoded is not None:
            # query: text, key/value: image
            fused_image, _ = self.cross_attention(
                query=text_encoded, key=image_encoded, value=image_encoded
            )

            # 残差连接 + 层归一化
            fused = self.layer_norm(fused + fused_image)
            fused = self.dropout(fused)

        return fused


class PerceptionEncoder(nn.Module):
    """感知编码器 (整合所有模态)"""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config

        # 各模态编码器
        self.text_encoder = TextEncoder(config)
        self.image_encoder = ImageEncoder(config)
        self.fusion = MultimodalFusion(config)

    def forward(self, inputs: ModelInput) -> torch.Tensor:
        """
        感知编码

        Args:
            inputs: 模型输入

        Returns:
            encoded: [batch, seq_len, latent_dim]
        """
        # 1. 文本编码
        text_encoded = self.text_encoder(inputs.input_ids, inputs.attention_mask)

        # 2. 图像编码 (可选)
        image_encoded = None
        if inputs.pixel_values is not None:
            image_encoded = self.image_encoder(inputs.pixel_values)

        # 3. 多模态融合
        fused = self.fusion(text_encoded, image_encoded)

        return fused


# ==================== 认知编码器 ====================


class CognitionEncoder(nn.Module):
    """认知编码器"""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config

        # Transformer编码器层
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.cognition_d_model,
            nhead=config.cognition_heads,
            dim_feedforward=config.cognition_d_ff,
            dropout=config.dropout,
            batch_first=True,
        )

        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=config.cognition_layers)

        self.layer_norm = nn.LayerNorm(config.cognition_d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        认知编码

        Args:
            x: [batch, seq_len, d_model]

        Returns:
            encoded: [batch, seq_len, d_model]
        """
        # Transformer编码
        encoded = self.transformer(x)

        # 层归一化
        encoded = self.layer_norm(encoded)

        return encoded


# ==================== 执行解码器 ====================


class ExecutionDecoder(nn.Module):
    """执行解码器"""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config

        # Transformer解码器层
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=config.execution_d_model,
            nhead=config.execution_heads,
            dim_feedforward=config.execution_d_ff,
            dropout=config.dropout,
            batch_first=True,
        )

        self.transformer = nn.TransformerDecoder(decoder_layer, num_layers=config.execution_layers)

        # 输出投影到词表
        self.output_projection = nn.Linear(config.execution_d_model, config.vocab_size)

        self.layer_norm = nn.LayerNorm(config.execution_d_model)

    def forward(
        self, latent_repr: torch.Tensor, target_actions: torch.Tensor | None = None
    ) -> torch.Tensor:
        """
        执行解码

        Args:
            latent_repr: [batch, seq_len, d_model] (来自认知层)
            target_actions: [batch, target_len, vocab_size] (训练时)

        Returns:
            logits: [batch, seq_len, vocab_size]
        """
        if target_actions is not None:
            # 训练模式: Teacher Forcing
            # target_actions需要嵌入,这里简化处理
            decoded = self.transformer(tgt=target_actions, memory=latent_repr)
        else:
            # 推理模式: 自回归
            # 这里简化,实际需要实现完整的autoregressive decoding
            decoded = self.transformer(tgt=latent_repr, memory=latent_repr)

        # 层归一化
        decoded = self.layer_norm(decoded)

        # 投影到词表
        logits = self.output_projection(decoded)

        return logits


# ==================== 端到端模型 ====================


class EndToEndModel(nn.Module):
    """
    端到端神经网络模型

    架构: Perception Encoder → Cognition Encoder → Execution Decoder
    """

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config

        # 1. 感知编码器
        self.perception_encoder = PerceptionEncoder(config)

        # 2. 认知编码器
        self.cognition_encoder = CognitionEncoder(config)

        # 3. 执行解码器
        self.execution_decoder = ExecutionDecoder(config)

        # 4. 共享表示空间
        self.latent_space = nn.Sequential(
            nn.Linear(config.latent_dim, config.latent_dim), nn.ReLU(), nn.Dropout(config.dropout)
        )

        logger.info(f"🧠 端到端模型初始化完成 (规模: {config.size.value})")

    def forward(
        self, inputs: ModelInput, targets: dict[str, torch.Tensor] | None = None
    ) -> ModelOutput:
        """
        端到端前向传播

        Args:
            inputs: 模型输入
            targets: 目标输出 (训练时)

        Returns:
            ModelOutput: 模型输出
        """
        # 1. 感知编码
        perceptual_features = self.perception_encoder(inputs)

        # 2. 存入共享表示空间
        latent_repr = self.latent_space(perceptual_features)

        # 3. 认知处理
        cognitive_repr = self.cognition_encoder(latent_repr)

        # 4. 执行解码
        if self.training and targets is not None:
            # 训练模式: Teacher Forcing
            predicted_actions = self.execution_decoder(cognitive_repr, targets.get("actions"))
        else:
            # 推理模式: 自回归
            predicted_actions = self.execution_decoder(cognitive_repr)

        # 5. 计算置信度 (简化)
        confidence = torch.softmax(predicted_actions, dim=-1).max(dim=-1)[0]
        confidence = confidence.mean(dim=-1)  # [batch]

        return ModelOutput(
            predicted_actions=predicted_actions, latent_repr=latent_repr, confidence=confidence
        )

    @torch.no_grad()
    def generate_actions(
        self,
        inputs: ModelInput,
        max_length: int = 100,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 0.95,
    ) -> torch.Tensor:
        """
        自回归生成动作序列

        Args:
            inputs: 模型输入
            max_length: 最大生成长度
            temperature: 采样温度
            top_k: top-k采样
            top_p: nucleus采样

        Returns:
            actions: [batch, max_length]
        """
        self.eval()

        # 1. 编码输入
        perceptual_features = self.perception_encoder(inputs)
        latent_repr = self.latent_space(perceptual_features)
        cognitive_repr = self.cognition_encoder(latent_repr)

        # 2. 自回归生成
        batch_size = inputs.input_ids.size(0)
        device = inputs.input_ids.device

        # 初始化
        generated = torch.zeros(batch_size, 1, dtype=torch.long, device=device)

        for _i in range(max_length):
            # 解码
            logits = self.execution_decoder(cognitive_repr)

            # 取最后一个时间步
            logits = logits[:, -1, :] / temperature

            # Top-k过滤
            if top_k > 0:
                values, indices = torch.topk(logits, top_k)
                logits = torch.full_like(logits, float("-inf"))
                logits.scatter_(1, indices, values)

            # Top-p (nucleus) 过滤
            if top_p < 1.0:
                sorted_logits, sorted_indices = torch.sort(logits, descending=True)
                cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)

                # 移除累积概率超过top_p的token
                sorted_indices_to_remove = cumulative_probs > top_p
                sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                sorted_indices_to_remove[..., 0] = 0

                indices_to_remove = sorted_indices_to_remove.scatter(
                    1, sorted_indices, sorted_indices_to_remove
                )
                logits[indices_to_remove] = float("-inf")

            # 采样
            probs = F.softmax(logits, dim=-1)
            next_action = torch.multinomial(probs, num_samples=1)

            # 拼接
            generated = torch.cat([generated, next_action], dim=1)

            # 检查结束符 (这里简化处理)
            if (next_action == 0).all():
                break

        return generated


# ==================== 模型工厂 ====================


class ModelFactory:
    """模型工厂"""

    # 预定义配置
    PREDEFINED_CONFIGS = {
        ModelSize.TINY: ModelConfig(
            size=ModelSize.TINY,
            cognition_layers=2,
            cognition_heads=4,
            cognition_d_model=256,
            execution_layers=2,
            execution_heads=4,
            execution_d_model=256,
            latent_dim=256,
        ),
        ModelSize.SMALL: ModelConfig(
            size=ModelSize.SMALL,
            cognition_layers=4,
            cognition_heads=8,
            cognition_d_model=512,
            execution_layers=4,
            execution_heads=8,
            execution_d_model=512,
            latent_dim=512,
        ),
        ModelSize.MEDIUM: ModelConfig(
            size=ModelSize.MEDIUM,
            cognition_layers=6,
            cognition_heads=8,
            cognition_d_model=512,
            execution_layers=6,
            execution_heads=8,
            execution_d_model=512,
            latent_dim=512,
        ),
        ModelSize.LARGE: ModelConfig(
            size=ModelSize.LARGE,
            cognition_layers=12,
            cognition_heads=16,
            cognition_d_model=1024,
            execution_layers=12,
            execution_heads=16,
            execution_d_model=1024,
            latent_dim=1024,
        ),
    }

    @classmethod
    def create_model(
        cls, size: ModelSize | None = None, config: ModelConfig | None = None
    ) -> EndToEndModel:
        """
        创建模型

        Args:
            size: 模型规模
            config: 自定义配置 (可选)

        Returns:
            EndToEndModel
        """
        if config is None:
            config = cls.PREDEFINED_CONFIGS[size]

        model = EndToEndModel(config)
        logger.info(f"✅ 模型创建完成: {size.value}")

        return model

    @classmethod
    def load_pretrained(
        cls, checkpoint_path: str | None = None, config: ModelConfig | None = None
    ) -> EndToEndModel:
        """
        加载预训练模型

        Args:
            checkpoint_path: 检查点路径
            config: 模型配置

        Returns:
            EndToEndModel
        """
        # 加载检查点(无论config是否为None都需要加载model_state_dict)
        checkpoint = torch.load(checkpoint_path, map_location="cpu")

        # 如果config为None,从检查点加载配置
        if config is None:
            config = checkpoint.get("config", ModelConfig())

        model = cls.create_model(config=config)
        model.load_state_dict(checkpoint["model_state_dict"])  # type: ignore
        model.eval()

        logger.info(f"✅ 预训练模型加载完成: {checkpoint_path}")

        return model


# 导出
__all__ = [
    "CognitionEncoder",
    "EndToEndModel",
    "ExecutionDecoder",
    "ModelConfig",
    "ModelFactory",
    "ModelInput",
    "ModelOutput",
    "ModelSize",
    "PerceptionEncoder",
]


# ==================== 使用示例 ====================

if __name__ == "__main__":

    async def main():
        """测试端到端模型"""
        # 创建模型
        model = ModelFactory.create_model(ModelSize.SMALL)

        # 模型输入
        batch_size = 2
        seq_len = 128

        inputs = ModelInput(
            input_ids=torch.randint(0, 10000, (batch_size, seq_len)),
            attention_mask=torch.ones(batch_size, seq_len),
        )

        # 前向传播
        outputs = model(inputs)

        print(f"预测动作形状: {outputs.predicted_actions.shape}")
        print(f"共享表示形状: {outputs.latent_repr.shape}")
        print(f"置信度: {outputs.confidence}")

        # 生成动作
        actions = model.generate_actions(inputs, max_length=50)
        print(f"生成动作形状: {actions.shape}")

    asyncio.run(main())
