#!/usr/bin/env python3
from __future__ import annotations
"""
意图识别数据生成器
Intent Recognition Data Generator
大规模生成高质量训练数据
"""

import json
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from core.async_main import async_main


class IntentDataGenerator:
    """意图数据生成器"""

    def __init__(self):
        # 意图类别定义
        self.intent_classes = {
            "PATENT_ANALYSIS": "专利分析",
            "PATENT_SEARCH": "专利搜索",
            "LEGAL_QUERY": "法律查询",
            "LEGAL_ADVICE": "法律建议",
            "TECHNICAL_EXPLANATION": "技术解释",
            "TECHNICAL_TROUBLESHOOTING": "技术故障排除",
            "EMOTIONAL": "情感表达",
            "EMOTIONAL_SUPPORT": "情感支持",
            "FAMILY_CHAT": "家庭聊天",
            "WORK_COORDINATION": "工作协调",
            "LEARNING_REQUEST": "学习请求",
            "SYSTEM_CONTROL": "系统控制",
            "ENTERTAINMENT": "娱乐",
            "HEALTH_CHECK": "健康检查",
        }

        # 词汇库
        self.word_banks = self._init_word_banks()

        # 模板库
        self.templates = self._init_templates()

        # 爸爸诺诺特色词汇
        self.special_words = {
            "爸爸": ["爸爸", "父亲", "老爸", "爹地"],
            "诺诺": ["诺诺", "小诺", "诺宝", "女儿"],
            "称呼": ["帮爸爸", "帮我", "请", "麻烦", "能否"],
        }

    def _init_word_banks(self) -> Any:
        """初始化词汇库"""
        return {
            "PATENT_ANALYSIS": {
                "动作": ["分析", "研究", "评估", "审查", "解析", "剖析", "探讨", "阐述"],
                "对象": ["专利", "发明", "技术方案", "创新点", "核心技术", "技术特征"],
                "修饰": ["的", "这个", "该项", "这款", "上述"],
                "疑问": ["如何", "怎样", "什么", "哪里", "为什么"],
                "要求": ["详细", "深入", "全面", "专业", "准确"],
            },
            "LEGAL_QUERY": {
                "动作": ["解释", "说明", "查询", "了解", "检索", "查找"],
                "对象": ["法律", "法规", "条款", "规定", "条文", "条例"],
                "修饰": ["的", "这个", "该项", "相关"],
                "疑问": ["如何", "怎样", "什么", "含义", "内容"],
                "领域": ["知识产权", "合同法", "专利法", "劳动法", "刑法"],
            },
            "TECHNICAL_EXPLANATION": {
                "动作": ["解释", "说明", "讲解", "阐述", "分析", "剖析"],
                "对象": ["算法", "程序", "代码", "技术", "方案", "架构"],
                "修饰": ["的", "这个", "该项", "这段"],
                "疑问": ["如何", "怎样", "什么", "为什么"],
                "技术词": ["机器学习", "深度学习", "数据库", "网络", "系统"],
            },
            "EMOTIONAL": {
                "情感词": ["爱", "谢谢", "感动", "温暖", "贴心", "陪伴", "支持"],
                "对象": ["爸爸", "诺诺", "你", "大家"],
                "程度": ["很", "非常", "特别", "真的", "超", "超级"],
                "表达": ["我", "你", "我们"],
                "连接": ["的", "和", "与"],
            },
            "SYSTEM_CONTROL": {
                "动作": ["启动", "停止", "重启", "开启", "关闭", "运行"],
                "对象": ["服务", "系统", "程序", "应用", "进程", "功能"],
                "修饰": ["这个", "那个", "相关"],
                "要求": ["立即", "马上", "现在", "稍后"],
                "系统词": ["服务器", "数据库", "应用服务", "后台服务"],
            },
        }

    def _init_templates(self) -> Any:
        """初始化模板库"""
        return {
            "PATENT_ANALYSIS": [
                "{动作}{修饰}{对象}{要求}分析",
                "请{动作}{对象}的创新点",
                "{修饰}{对象}{疑问}{动作}",
                "{动作}{对象}{要求}的技术内容",
                "{对象}的{疑问}{要求}{动作}",
            ],
            "LEGAL_QUERY": [
                "{动作}{修饰}{领域}{对象}",
                "{修饰}{对象}{疑问}意思",
                "请{动作}{对象}{要求}",
                "{领域}{修饰}{对象}{疑问}",
                "{动作}{对象}的{要求}规定",
            ],
            "TECHNICAL_EXPLANATION": [
                "{动作}{修饰}{技术词}{对象}",
                "{对象}{疑问}如何工作",
                "请{动作}{修饰}{对象}",
                "{修饰}{对象}的{疑问}{动作}",
                "{技术词}{对象}{要求}说明",
            ],
            "EMOTIONAL": [
                "{程度}{情感词}{对象}",
                "{表达}{情感词}{对象}",
                "{对象}{程度}{情感词}",
                "感谢{对象}{程度}{情感词}",
                "有{对象}{连接}{程度}{情感词}",
            ],
            "SYSTEM_CONTROL": [
                "{动作}{修饰}{系统词}",
                "{要求}{动作}{修饰}{对象}",
                "{修饰}{对象}{疑问}{动作}",
                "请{动作}{修饰}{对象}",
                "{对象}{要求}{动作}",
            ],
        }

    def generate_intent_data(self, intent: str, count: int = 1000) -> list[dict]:
        """生成特定意图的数据"""
        data = []

        # 获取词汇库
        self.word_banks.get(intent, {})

        # 获取模板
        templates = self.templates.get(intent, ["{action} {object}"])

        for _i in range(count):
            # 生成方法
            method = random.choice(["template", "variation", "context"])

            if method == "template" and templates:
                text = self._generate_from_template(intent, templates)
            elif method == "variation":
                text = self._generate_variation(intent)
            else:
                text = self._generate_with_context(intent)

            # 清理文本
            text = self._clean_text(text)

            # 确保多样性
            if text not in [d["text"] for d in data]:
                data.append(
                    {
                        "text": text,
                        "intent": intent,
                        "source": "generated",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return data[:count]

    def _generate_from_template(self, intent: str, templates: list[str]) -> str:
        """从模板生成"""
        template = random.choice(templates)
        words = self.word_banks.get(intent, {})

        # 替换占位符
        text = template.format(**self._random_word_selection(words))

        # 添加爸爸诺诺特色
        if random.random() < 0.3:  # 30%概率添加
            text = self._add_xiaonuo_style(text)

        return text

    def _generate_variation(self, intent: str) -> str:
        """生成变体"""
        base_samples = self._get_base_samples(intent)
        if not base_samples:
            templates = self.templates.get(intent, ["请分析这个"])
            return self._generate_from_template(intent, templates)

        base = random.choice(base_samples)

        # 应用变换
        transformations = [
            self._add_politeness,
            self._change_wording,
            self._add_emotion,
            self._add_context,
        ]

        text = base
        for _ in range(random.randint(1, 3)):
            transform = random.choice(transformations)
            text = transform(text)

        return text

    def _generate_with_context(self, intent: str) -> str:
        """生成带上下文的文本"""
        contexts = {
            "PATENT_ANALYSIS": [
                "我刚收到一个专利申请,",
                "在研究技术文档时,",
                "评估项目价值时,",
                "做技术调研时,",
            ],
            "LEGAL_QUERY": [
                "在起草合同时,",
                "遇到法律问题时,",
                "需要法律建议时,",
                "在准备诉讼材料时,",
            ],
            "TECHNICAL_EXPLANATION": [
                "看代码时遇到问题,",
                "学习新技术时,",
                "系统设计过程中,",
                "调试程序时,",
            ],
            "EMOTIONAL": [
                "今天心情特别好的时候,",
                "想到家的温暖时,",
                "感受到关心时,",
                "在困难时期得到支持时,",
            ],
            "SYSTEM_CONTROL": [
                "部署新服务时,",
                "系统出现问题时,",
                "做系统维护时,",
                "优化性能时,",
            ],
        }

        context = random.choice(contexts.get(intent, [""]))
        base = self._generate_variation(intent)

        return f"{context}{base}"

    def _random_word_selection(self, words: dict) -> dict:
        """随机选择词汇"""
        selected = {}
        for category, word_list in words.items():
            if word_list:
                selected[category] = random.choice(word_list)
            else:
                selected[category] = ""
        return selected

    def _add_xiaonuo_style(self, text: str) -> str:
        """添加诺诺风格"""
        styles = [f"爸爸,{text}", f"{text},爸爸", f"诺诺{text}", f"{text},诺诺", text]
        return random.choice(styles)

    def _add_politeness(self, text: str) -> str:
        """添加礼貌用语"""
        politeness = ["请", "麻烦您", "能否", "可以吗", "好吗"]
        if random.random() < 0.5:
            return f"{random.choice(politeness)}{text}"
        return text

    def _change_wording(self, text: str) -> str:
        """改变措辞"""
        replacements = {
            "分析": ["研究", "查看", "审查"],
            "解释": ["说明", "阐述", "讲解"],
            "帮助": ["协助", "支持"],
            "这个": ["该项", "这款", "这个"],
        }

        for old, new_list in replacements.items():
            if old in text and random.random() < 0.3:
                text = text.replace(old, random.choice(new_list))

        return text

    def _add_emotion(self, text: str) -> str:
        """添加情感色彩"""
        emotions = ["😊", "🤔", "💪", "❓", "✨"]
        if random.random() < 0.2:
            return f"{text} {random.choice(emotions)}"
        return text

    def _add_context(self, text: str) -> str:
        """添加上下文"""
        contexts = ["现在我想", "我需要", "请帮我想想", "我正在考虑", "关于"]
        if random.random() < 0.3:
            return f"{random.choice(contexts)},{text}"
        return text

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空格
        text = re.sub(r"\s+", " ", text)

        # 移除特殊字符
        text = re.sub(r"[^\w\s\u4e00-\u9fff]", "", text)

        # 首尾去空格
        text = text.strip()

        return text

    def _get_base_samples(self, intent: str) -> list[str]:
        """获取基础样本"""
        base_samples = {
            "PATENT_ANALYSIS": [
                "分析这个专利",
                "研究技术创新点",
                "评估专利价值",
                "解释专利内容",
                "审查技术方案",
            ],
            "LEGAL_QUERY": [
                "解释法律条款",
                "查询相关规定",
                "了解法律责任",
                "说明法律条文",
                "检索法律信息",
            ],
            "TECHNICAL_EXPLANATION": [
                "解释算法原理",
                "说明代码逻辑",
                "分析技术方案",
                "讲解系统架构",
                "阐述实现方式",
            ],
            "EMOTIONAL": ["谢谢爸爸", "我爱你", "很感动", "很温暖", "感谢支持"],
            "SYSTEM_CONTROL": ["启动服务", "重启系统", "查看状态", "停止进程", "监控应用"],
        }
        return base_samples.get(intent, [])

    def generate_all_intents(self, samples_per_intent: int = 1000) -> list[dict]:
        """生成所有意图的数据"""
        all_data = []

        for intent in self.intent_classes:
            print(f"📝 生成 {intent} 数据...")
            intent_data = self.generate_intent_data(intent, samples_per_intent)
            all_data.extend(intent_data)
            print(f"  ✅ 生成 {len(intent_data)} 条")

        # 打乱数据
        random.shuffle(all_data)

        return all_data

    def save_data(self, data: list[dict], filepath: str) -> None:
        """保存数据"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ 数据已保存到: {filepath}")


@async_main
async def main():
    """主程序"""
    print("🎯 意图识别数据生成器")
    print("=" * 50)

    generator = IntentDataGenerator()

    # 生成数据
    print("\n📝 生成训练数据...")
    data = generator.generate_all_intents(samples_per_intent=1000)

    print(f"\n📊 总计生成: {len(data)} 条数据")

    # 统计
    intent_counts = {}
    for item in data:
        intent_counts[item["intent"]] = intent_counts.get(item["intent"], 0) + 1

    print("\n📋 各意图数据量:")
    for intent, count in sorted(intent_counts.items()):
        print(f"  {intent}: {count}")

    # 保存数据
    print("\n💾 保存数据...")
    generator.save_data(
        data, "/Users/xujian/Athena工作平台/data/intent_recognition/training_data.json"
    )

    # 划分训练测试集
    split_idx = int(len(data) * 0.8)
    train_data = data[:split_idx]
    test_data = data[split_idx:]

    generator.save_data(
        train_data, "/Users/xujian/Athena工作平台/data/intent_recognition/train_data.json"
    )

    generator.save_data(
        test_data, "/Users/xujian/Athena工作平台/data/intent_recognition/test_data.json"
    )

    print("\n✅ 完成!")
    print(f"  训练集: {len(train_data)} 条")
    print(f"  测试集: {len(test_data)} 条")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
