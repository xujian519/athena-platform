#!/usr/bin/env python3
"""
快速训练数据生成器
Quick Training Data Generator

为意图识别系统生成高质量的训练数据

作者: 小诺·双鱼公主
版本: v1.0.0
创建: 2025-12-29
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any



def generate_intent_dataset() -> Any:
    """生成意图识别训练数据集"""

    # 意图类别和样本定义
    intent_samples = {
        "PATENT_SEARCH": [
            "检索人工智能相关专利",
            "搜索机器学习现有技术",
            "查新区块链技术专利",
            "查找深度学习相关专利",
            "专利数据库检索",
            "现有技术对比文件",
            "专利性分析检索",
            "技术方案查新",
            "专利申请前检索",
            "专利布局分析",
            "搜索这个技术的专利",
            "帮我查专利",
            "找一下相关专利文献",
            "专利检索查询",
            "现有技术查找",
            "查专利有没有类似的",
            "我要申请专利,先查一下",
            "专利查重",
            "技术专利搜索",
            "专利信息查询",
            "查找相关发明",
            "搜索类似技术方案",
            # 变体
            "帮我查查这个技术的专利",
            "看看有没有相关专利",
            "搜索一下专利",
            "专利检索",
            "查专利",
            "现有技术调研",
            "技术查新",
            "专利文献检索",
            "找专利",
            "查相关技术",
            "专利搜索",
            "我要查专利",
            "专利查询",
            "技术方案检索",
            "查一下专利",
        ],
        "OPINION_RESPONSE": [
            "审查意见怎么答复",
            "如何回复审查员意见",
            "审查意见通知书答复",
            "专利审查意见答复策略",
            "驳回意见答复",
            "补正请求处理",
            "专利法第26条答复",
            "不清楚答复",
            "不支持答复",
            "公开不充分答复",
            "审查意见回复",
            "答复审查员",
            "怎么答复审查意见",
            "审查意见答复模板",
            "专利审查答复",
            "答复OA",
            "审查意见应对",
            # 变体
            "收到审查意见怎么办",
            "审查员意见怎么回",
            "OA答复",
            "审查意见通知书",
            "答复审查意见",
            "专利审查意见",
            "驳回答复",
            "审查意见怎么处理",
            "审查意见回复策略",
        ],
        "PATENT_DRAFTING": [
            "撰写发明专利申请",
            "写专利申请文件",
            "专利权利要求书撰写",
            "专利说明书撰写",
            "技术交底书撰写",
            "专利申请文档准备",
            "发明点描述撰写",
            "技术特征撰写",
            "保护范围界定",
            "专利申请格式",
            "写个专利",
            "专利怎么写",
            "撰写专利",
            "专利撰写",
            "专利申请撰写",
            "专利文件起草",
            "写专利申请书",
            # 变体
            "帮我写专利",
            "专利申请书",
            "专利文档撰写",
            "写发明专利",
            "怎么写专利",
            "专利说明书写",
            "权利要求书怎么写",
            "专利申请文件",
            "撰写专利文档",
        ],
        "CODE_GENERATION": [
            "帮我写代码",
            "生成Python函数",
            "编写算法实现",
            "创建代码框架",
            "实现功能代码",
            "开发接口程序",
            "编写脚本工具",
            "代码生成器",
            "自动生成代码",
            "程序设计编码",
            "写代码",
            "生成代码",
            "编写程序",
            "实现算法",
            "开发功能",
            "代码实现",
            # 变体
            "帮我写个函数",
            "写段代码",
            "生成一下代码",
            "代码编写",
            "编程实现",
            "写个脚本",
            "函数生成",
            "实现这个功能",
            "写程序",
            "代码怎么写",
            "编程",
        ],
        "PROBLEM_SOLVING": [
            "系统启动不了了",
            "程序有错误",
            "系统崩溃修复",
            "代码调试问题",
            "bug修复方法",
            "故障诊断排查",
            "错误解决",
            "异常处理",
            "系统故障排除",
            "问题诊断",
            "解决bug",
            "调试程序",
            "系统错误",
            "程序报错",
            # 变体
            "系统出问题了",
            "程序报错怎么办",
            "调试代码",
            "修复bug",
            "排查故障",
            "系统不正常",
            "代码有错",
            "解决问题",
            "系统故障",
            "错误处理",
            "调试问题",
        ],
        "CREATIVE_WRITING": [
            "帮我写个故事",
            "创作文案内容",
            "编写创意内容",
            "生成文章内容",
            "创作广告文案",
            "写小说脚本",
            "内容创作",
            "文案编写",
            "创意输出",
            "文字创作",
            "写文章",
            "创作文案",
            "编写内容",
            "文案创作",
            # 变体
            "写个故事",
            "创作内容",
            "写文案",
            "文章写作",
            "创意写作",
            "内容生成",
            "文案撰写",
            "写创意文案",
        ],
        "DATA_ANALYSIS": [
            "分析数据报告",
            "统计分析结果",
            "数据可视化",
            "生成数据图表",
            "研究报告分析",
            "数据挖掘",
            "趋势分析",
            "统计报告",
            "数据洞察",
            "分析数据",
            "数据分析",
            "统计分析",
            "数据报告",
            "研究分析",
            # 变体
            "分析这些数据",
            "数据统计",
            "生成图表",
            "数据报表",
            "分析报告",
            "统计结果",
            "数据研究",
            "可视化分析",
            "趋势研究",
            "数据洞察分析",
        ],
        "LEGAL_QUERY": [
            "解释法律条款",
            "查询相关规定",
            "了解法律责任",
            "说明法律条文",
            "检索法律信息",
            "法律咨询",
            "法律问题",
            "法规查询",
            "法律解释",
            "了解法律",
            # 变体
            "法律是什么",
            "法律规定",
            "法律条文",
            "查询法律",
            "法律问题咨询",
            "法律说明",
            "法规解释",
            "法律信息",
            "法律知识",
        ],
        "EMOTIONAL": [
            "谢谢爸爸",
            "我爱你",
            "很感动",
            "很温暖",
            "感谢支持",
            "辛苦了",
            "太好了",
            "真棒",
            # 变体
            "谢谢",
            "感谢",
            "爱爸爸",
            "温暖",
            "感动",
            "支持",
            "太棒了",
            "真好",
        ],
        "SYSTEM_CONTROL": [
            "启动服务",
            "重启系统",
            "查看状态",
            "停止进程",
            "监控应用",
            "系统管理",
            "服务控制",
            "进程管理",
            # 变体
            "启动系统",
            "重启服务",
            "查看系统状态",
            "停止服务",
            "监控系统",
            "管理服务",
            "控制进程",
        ],
    }

    # 生成完整数据集
    all_data = []

    for intent, samples in intent_samples.items():
        # 基础样本
        for sample in samples:
            all_data.append(
                {
                    "text": sample,
                    "intent": intent,
                    "source": "manual",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # 生成变体(每种样本生成2-3个变体)
        for sample in samples[:10]:  # 只对前10个样本生成变体
            for _ in range(random.randint(2, 4)):
                variant = generate_variant(sample)
                all_data.append(
                    {
                        "text": variant,
                        "intent": intent,
                        "source": "generated_variant",
                        "original_text": sample,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

    # 打乱数据
    random.shuffle(all_data)

    return all_data


def generate_variant(text: str) -> str:
    """生成文本变体"""
    variants = []

    # 添加礼貌用语
    politeness_prefix = ["请", "麻烦", "能否", "可以"]
    politeness_suffix = ["吗", "吧", "呢"]

    # 添加称呼
    prefixes = ["爸爸,", "诺诺,", ""]

    # 变体1: 添加礼貌用语
    if random.random() < 0.3:
        prefix = random.choice(politeness_prefix)
        variant = f"{prefix}{text}"
        variants.append(variant)

    # 变体2: 添加语气词
    if random.random() < 0.3:
        suffix = random.choice(politeness_suffix)
        variant = f"{text}{suffix}"
        variants.append(variant)

    # 变体3: 添加称呼
    if random.random() < 0.3:
        prefix = random.choice(prefixes)
        variant = f"{prefix}{text}"
        variants.append(variant)

    # 变体4: 简化表述
    if random.random() < 0.3:
        # 去掉修饰词
        simplified = text
        for remove_word in ["帮我", "帮我", "一下", "这个", "那个"]:
            simplified = simplified.replace(remove_word, "")
        simplified = simplified.strip()
        if simplified and simplified != text:
            variants.append(simplified)

    # 如果没有生成变体,返回原文
    if not variants:
        return text

    return random.choice(variants)


def save_dataset(data: list, filepath: str) -> None:
    """保存数据集"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 数据已保存到: {filepath}")


def main() -> None:
    """主程序"""
    print("🎯 快速训练数据生成器")
    print("=" * 60)

    # 生成数据
    print("\n📝 生成训练数据...")
    data = generate_intent_dataset()

    print(f"📊 总计生成: {len(data)} 条数据")

    # 统计
    intent_counts = {}
    for item in data:
        intent = item["intent"]
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    print("\n📋 各意图数据量:")
    for intent, count in sorted(intent_counts.items(), key=lambda x: -x[1]):
        print(f"  {intent}: {count}")

    # 保存完整数据
    print("\n💾 保存数据...")
    save_dataset(data, "/Users/xujian/Athena工作平台/data/intent_recognition/training_data.json")

    # 划分训练集和测试集
    split_idx = int(len(data) * 0.8)
    train_data = data[:split_idx]
    test_data = data[split_idx:]

    save_dataset(train_data, "/Users/xujian/Athena工作平台/data/intent_recognition/train_data.json")

    save_dataset(test_data, "/Users/xujian/Athena工作平台/data/intent_recognition/test_data.json")

    print("\n✅ 完成!")
    print(f"  训练集: {len(train_data)} 条")
    print(f"  测试集: {len(test_data)} 条")

    # 保存数据统计
    stats = {
        "total_samples": len(data),
        "train_samples": len(train_data),
        "test_samples": len(test_data),
        "intent_distribution": intent_counts,
        "generated_at": datetime.now().isoformat(),
    }

    stats_file = "/Users/xujian/Athena工作平台/data/intent_recognition/data_stats.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\n📊 统计信息: {stats_file}")


if __name__ == "__main__":
    main()
