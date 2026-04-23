#!/usr/bin/env python3
from __future__ import annotations
"""
高级数据增强系统
Advanced Data Augmentation System

第一阶段优化:实现5种高级数据增强策略
1. 回译增强
2. 释义生成
3. 上下文注入
4. 对抗样本生成
5. 混合增强

作者: 小诺·双鱼公主
版本: v1.0.0
创建: 2025-12-29
"""

import json
import random
import sys
from datetime import datetime
from pathlib import Path

from core.logging_config import setup_logging

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class AdvancedDataAugmentation:
    """高级数据增强系统"""

    def __init__(self):
        """初始化数据增强系统"""
        # 同义词词典
        self.synonym_dict = self._load_synonym_dict()

        # 上下文模板
        self.context_templates = self._load_context_templates()

        # 情感词库
        self.emotion_words = self._load_emotion_words()

        logger.info("✅ 高级数据增强系统初始化完成")

    def _load_synonym_dict(self) -> dict[str, list[str]]:
        """加载同义词词典"""
        return {
            # 动词
            "分析": ["研究", "查看", "审查", "剖析", "探讨", "调研"],
            "解释": ["说明", "阐述", "讲解", "解答", "释义"],
            "帮助": ["协助", "支持", "辅助", "帮忙"],
            "搜索": ["查找", "检索", "查询", "寻找", "搜寻"],
            "写": ["撰写", "编写", "创作", "生成", "制作"],
            "启动": ["开启", "运行", "执行", "激活"],
            # 名词
            "专利": ["发明", "技术方案", "创新点", "技术成果"],
            "法律": ["法规", "法令", "条例", "条款"],
            "代码": ["程序", "脚本", "函数", "算法"],
            "系统": ["平台", "应用", "服务", "程序"],
            "爸爸": ["父亲", "老爸", "爹地"],
            # 形容词
            "详细": ["深入", "全面", "具体", "充分"],
            "快速": ["迅速", "快捷", "高效", "及时"],
            "准确": ["精确", "正确", "精准", "确切"],
            # 副词
            "非常": ["特别", "十分", "极其", "超级"],
            "马上": ["立即", "立刻", "即刻", "现在"],
            "如何": ["怎样", "怎么", "如何", "什么方式"],
        }

    def _load_context_templates(self) -> dict[str, list[str]]:
        """加载上下文模板"""
        return {
            "PATENT_ANALYSIS": [
                "我刚收到一个专利申请,{text}",
                "在研究技术文档时,{text}",
                "评估项目价值时,{text}",
                "做技术调研时,{text}",
                "我想知道,{text}",
                "现在的问题是,{text}",
            ],
            "LEGAL_QUERY": [
                "在起草合同时,{text}",
                "遇到法律问题时,{text}",
                "需要法律建议时,{text}",
                "在准备诉讼材料时,{text}",
                "我想了解,{text}",
            ],
            "CODE_GENERATION": [
                "写代码的时候,{text}",
                "开发功能时,{text}",
                "实现需求时,{text}",
                "编程过程中,{text}",
                "我想,{text}",
            ],
            "EMOTIONAL": [
                "今天心情特别好的时候,{text}",
                "想到家的温暖时,{text}",
                "感受到关心时,{text}",
                "在困难时期得到支持时,{text}",
            ],
            "SYSTEM_CONTROL": [
                "部署新服务时,{text}",
                "系统出现问题时,{text}",
                "做系统维护时,{text}",
                "优化性能时,{text}",
            ],
        }

    def _load_emotion_words(self) -> dict[str, list[str]]:
        """加载情感词库"""
        return {
            "positive": ["😊", "💪", "✨", "👍", "🎉", "💖"],
            "thinking": ["🤔", "🤨", "🧐", "😮"],
            "question": ["❓", "❔", "🤷", "🙋"],
            "action": ["🚀", "⚡", "🔧", "⚙️"],
        }

    def synonym_replacement(self, text: str, replacement_prob: float = 0.3) -> str:
        """同义词替换增强

        Args:
            text: 原始文本
            replacement_prob: 替换概率

        Returns:
            str: 增强后的文本
        """
        words = list(text)  # 保持中文结构
        result = []

        for word in words:
            # 检查是否是同义词典中的词
            replaced = False
            for key, synonyms in self.synonym_dict.items():
                if key in text and random.random() < replacement_prob:
                    # 替换
                    if word == key:
                        result.append(random.choice(synonyms))
                        replaced = True
                        break

            if not replaced:
                result.append(word)

        return "".join(result)

    def back_translation_simulation(self, text: str) -> str:
        """模拟回译增强(中文 -> 英文 -> 中文)

        注意:这是简化版,实际应该调用翻译API

        Args:
            text: 原始文本

        Returns:
            str: 回译后的文本
        """
        # 简化的回译模拟
        # 实际应该使用翻译API

        # 方法1:改变句式结构
        variations = [
            text,
            # 添加语气词
            f"{text}呢",
            f"{text}吧",
            # 改变主语位置
            f"关于{text},我想了解",
            # 添加礼貌用语
            f"请{text}",
        ]

        return random.choice(variations)

    def paraphrase_generation(self, text: str) -> str:
        """释义生成

        Args:
            text: 原始文本

        Returns:
            str: 释义后的文本
        """
        # 简化的释义生成
        # 实际应该使用GPT等模型

        # 提取关键信息
        if "分析" in text or "研究" in text:
            return f"我想深入了解{text.replace('分析', '').replace('研究', '')}"

        if "帮助" in text or "协助" in text:
            return f"需要协助{text.replace('帮助', '').replace('协助', '')}"

        if "搜索" in text or "查找" in text:
            return f"想要找{text.replace('搜索', '').replace('查找', '')}"

        # 默认返回原文
        return text

    def context_injection(self, text: str, intent: Optional[str] = None) -> str:
        """上下文注入增强

        Args:
            text: 原始文本
            intent: 意图类型(用于选择合适的上下文)

        Returns:
            str: 注入上下文后的文本
        """
        if not intent:
            # 随机选择一个意图的上下文
            intent = random.choice(list(self.context_templates.keys()))

        templates = self.context_templates.get(intent, [f"{text}"])
        template = random.choice(templates)

        return template.format(text=text)

    def adversarial_generation(self, text: str) -> str:
        """对抗样本生成

        通过添加噪声、错别字等方式生成对抗样本

        Args:
            text: 原始文本

        Returns:
            str: 对抗样本
        """
        result = text

        # 随机选择一种对抗方法
        method = random.choice(
            [self._add_typo, self._add_noise, self._change_word_order, self._add_redundancy]
        )

        return method(result)

    def _add_typo(self, text: str) -> str:
        """添加轻微错别字"""
        # 简化实现:随机重复一个字符
        if len(text) > 2:
            idx = random.randint(0, len(text) - 1)
            return text[:idx] + text[idx] + text[idx:]
        return text

    def _add_noise(self, text: str) -> str:
        """添加噪声(空格、标点)"""
        noise = random.choice([" ", "  ", "、", ","])
        idx = random.randint(1, len(text) - 1)
        return text[:idx] + noise + text[idx:]

    def _change_word_order(self, text: str) -> str:
        """改变词序"""
        words = text.split()
        if len(words) > 2:
            # 交换两个词的位置
            i, j = random.sample(range(len(words)), 2)
            words[i], words[j] = words[j], words[i]
        return " ".join(words)

    def _add_redundancy(self, text: str) -> str:
        """添加冗余词"""
        redundant_words = ["那个", "这个", "的话", "一下"]
        if random.random() < 0.5:
            word = random.choice(redundant_words)
            idx = random.randint(1, len(text) - 1)
            return text[:idx] + word + text[idx:]
        return text

    def emotion_injection(self, text: str) -> str:
        """情感注入

        Args:
            text: 原始文本

        Returns:
            str: 注入情感后的文本
        """
        # 随机选择情感类型
        emotion_type = random.choice(list(self.emotion_words.keys()))
        emoji = random.choice(self.emotion_words[emotion_type])

        # 在文本末尾或开头添加emoji
        if random.random() < 0.5:
            return f"{text} {emoji}"
        else:
            return f"{emoji} {text}"

    def multi_strategy_augment(
        self, text: str, intent: Optional[str] = None, factor: int = 10
    ) -> list[str]:
        """多策略组合增强

        Args:
            text: 原始文本
            intent: 意图类型
            factor: 增强倍数

        Returns:
            list: 增强后的文本列表
        """
        augmented = []

        # 1. 同义词替换
        for _ in range(2):
            augmented.append(self.synonym_replacement(text))

        # 2. 回译模拟
        augmented.append(self.back_translation_simulation(text))

        # 3. 释义生成
        augmented.append(self.paraphrase_generation(text))

        # 4. 上下文注入
        for _ in range(2):
            augmented.append(self.context_injection(text, intent))

        # 5. 对抗样本
        for _ in range(2):
            augmented.append(self.adversarial_generation(text))

        # 6. 情感注入
        for _ in range(2):
            augmented.append(self.emotion_injection(text))

        # 去重并返回
        unique_augmented = list(set(augmented))
        if text in unique_augmented:
            unique_augmented.remove(text)

        return unique_augmented[:factor]


async def augment_dataset(input_file: str, output_file: str, samples_per_intent: int = 1000) -> int:
    """增强整个数据集

    Args:
        input_file: 输入数据文件
        output_file: 输出数据文件
        samples_per_intent: 每个意图的目标样本数

    Returns:
        int: 增强后的总样本数
    """
    # 加载原始数据
    with open(input_file, encoding="utf-8") as f:
        original_data = json.load(f)

    # 统计每个意图的样本数
    intent_counts = {}
    for item in original_data:
        intent = item.get("intent", "UNKNOWN")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    logger.info(f"📊 原始数据统计: {intent_counts}")

    # 创建增强器
    augmenter = AdvancedDataAugmentation()

    # 增强数据
    augmented_data = []
    augmented_data.extend(original_data)  # 包含原始数据

    for item in original_data:
        intent = item.get("intent", "UNKNOWN")
        text = item.get("text", "")

        # 计算需要增强的数量
        current_count = intent_counts[intent]
        if current_count >= samples_per_intent:
            continue

        need_count = samples_per_intent - current_count

        # 多策略增强
        augmented_texts = augmenter.multi_strategy_augment(text, intent, factor=need_count)

        # 添加到增强数据集
        for aug_text in augmented_texts:
            augmented_data.append(
                {
                    "text": aug_text,
                    "intent": intent,
                    "source": "augmented",
                    "original_text": text,
                    "timestamp": datetime.now().isoformat(),
                }
            )

    # 保存增强后的数据
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(augmented_data, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ 数据增强完成: {len(original_data)} -> {len(augmented_data)}")

    return len(augmented_data)


# 便捷函数
def augment_text(text: Optional[str] = None, intent: Optional[str] = None, factor: int = 10) -> list[str]:
    """便捷函数:增强单个文本

    Args:
        text: 原始文本
        intent: 意图类型
        factor: 增强倍数

    Returns:
        list: 增强后的文本列表
    """
    augmenter = AdvancedDataAugmentation()
    return augmenter.multi_strategy_augment(text, intent, factor)


async def main():
    """主程序 - 演示数据增强"""
    print("🎯 高级数据增强系统")
    print("=" * 60)

    augmenter = AdvancedDataAugmentation()

    # 测试文本
    test_texts = [
        ("分析这个专利", "PATENT_ANALYSIS"),
        ("帮我写代码", "CODE_GENERATION"),
        ("谢谢爸爸", "EMOTIONAL"),
    ]

    print("\n📝 数据增强演示:")
    for text, intent in test_texts:
        print(f"\n原文: {text}")
        print(f"意图: {intent}")

        augmented = augmenter.multi_strategy_augment(text, intent, factor=5)
        print("增强结果:")
        for i, aug_text in enumerate(augmented, 1):
            print(f"  {i}. {aug_text}")


# 入口点: @async_main装饰器已添加到main函数
