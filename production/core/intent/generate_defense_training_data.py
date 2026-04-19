#!/usr/bin/env python3
"""
从专利判决书中提取无效辩护样本并生成训练数据
Generate Invalidation Defense Training Data from Patent Judgments

简化版本:直接从判决书中提取成功辩护案例,生成意图识别训练数据

作者: Athena平台团队
版本: v1.0.0-simplified
创建: 2026-01-13
"""

from __future__ import annotations
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def extract_text_from_json(data: Any) -> str:
    """递归提取JSON中的所有文本内容"""
    texts = []

    if isinstance(data, str):
        texts.append(data)
    elif isinstance(data, dict):
        for value in data.values():
            texts.extend(extract_text_from_json(value))
    elif isinstance(data, list):
        for item in data:
            texts.extend(extract_text_from_json(item))

    return "\n".join(texts)


def is_successful_defense(text: str) -> bool:
    """判断是否为成功的辩护"""
    success_patterns = [
        r"维持.*有效",
        r"继续维持.*专利权",
        r"在.*基础上.*维持.*有效",
        r"驳回.*无效宣告请求",
        r"专利权人.*主张.*成立",
        r"撤销.*无效决定",
    ]
    return any(re.search(pattern, text) for pattern in success_patterns)


def contains_defense_content(text: str) -> bool:
    """判断是否包含答辩内容"""
    defense_patterns = [
        r"专利权人.*意见陈述",
        r"专利权人.*答辩",
        r"专利权人.*认为",
        r"专利权人.*称[::]",
        r"意见陈述书.*称[::]",
        r"上诉人.*称[::].*专利",
    ]
    return any(re.search(pattern, text) for pattern in defense_patterns)


def generate_defense_queries() -> list[str]:
    """生成无效辩护相关的用户查询模板"""
    return [
        # 通用辩护查询
        "如何进行无效宣告答辩",
        "无效答辩意见书的撰写要点",
        "专利无效宣告程序的应对策略",
        "无效答辩中的常用论据",
        "如何反驳无效宣告请求",
        # 新颖性辩护
        "新颖性无效宣告如何答辩",
        "如何反驳新颖性问题",
        "区别技术特征如何主张",
        "对比文件未公开如何论证",
        # 创造性辩护
        "创造性无效宣告如何答辩",
        "非显而易见性如何论证",
        "技术效果如何证明具有创造性",
        "如何反驳显而易见的指控",
        # 支持度辩护
        "说明书支持度如何辩护",
        "如何证明专利充分公开",
        "支持度问题如何答辩",
        "权利要求是否得到说明书支持",
        # 保护范围辩护
        "权利要求解释规则如何运用",
        "保护范围如何界定",
        "等同原则在无效答辩中如何运用",
        "字面解释与等同解释的区别",
        # 程序性辩护
        "无效答辩期限是多久",
        "无效程序中如何补充证据",
        "口头审理程序如何应对",
        "无效答辩材料如何准备",
    ]


def process_judgment_file(file_path: Path) -> list[dict[str, Any]]:
    """处理单个判决书文件"""
    training_samples = []

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # 提取所有文本
        full_text = extract_text_from_json(data)

        # 判断是否包含成功的辩护
        if is_successful_defense(full_text) and contains_defense_content(full_text):
            # 提取案号
            case_number = "UNKNOWN"
            if "case_info" in data and isinstance(data["case_info"], dict):
                case_number = data["case_info"].get("case_id", "UNKNOWN")

            # 生成训练样本
            queries = generate_defense_queries()

            for query in queries:
                training_samples.append(
                    {
                        "text": query,
                        "intent": "INVALIDATION_DEFENSE",
                        "metadata": {
                            "case_number": case_number,
                            "source": "patent_judgment",
                            "confidence": "high",
                            "extracted_from": str(file_path.name),
                        },
                    }
                )

    except Exception as e:
        print(f"处理文件失败 {file_path.name}: {e}")

    return training_samples


def main() -> None:
    """主程序"""
    print("=" * 80)
    print("🎯 从专利判决书生成无效辩护训练数据")
    print("=" * 80)

    # 数据目录
    data_dir = Path("/Users/xujian/Athena工作平台/data/patent_judgments/processed")

    # 查找所有结构化JSON文件
    print(f"\n🔍 扫描目录: {data_dir}")

    json_files = []
    for item in data_dir.iterdir():
        if item.is_dir():
            subdir_files = list(item.glob("*_structured.json"))
            json_files.extend(subdir_files)

    print(f"📂 找到 {len(json_files)} 个结构化文件")

    # 处理文件
    all_training_data = []
    success_cases = 0

    print("\n⏳ 处理中...")

    for i, file_path in enumerate(json_files, 1):
        if i % 500 == 0:
            print(f"  进度: {i}/{len(json_files)} ({i/len(json_files)*100:.1f}%)")

        samples = process_judgment_file(file_path)
        if samples:
            success_cases += 1
            all_training_data.extend(samples)

    # 统计
    print("\n" + "=" * 80)
    print("📊 处理统计")
    print("=" * 80)
    print(f"总文件数: {len(json_files)}")
    print(f"成功辩护案例: {success_cases} ({success_cases/len(json_files)*100:.1f}%)")
    print(f"生成训练样本: {len(all_training_data)}")

    # 保存训练数据
    if all_training_data:
        output_dir = Path("/Users/xujian/Athena工作平台/data/intent_training")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"invalidation_defense_training_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_training_data, f, ensure_ascii=False, indent=2)

        print("\n✅ 训练数据已保存到:")
        print(f"   {output_file}")
        print("\n📋 下一步:")
        print("   1. 将此数据合并到现有训练集")
        print("   2. 重新训练意图识别模型")
        print("   3. 评估模型在INVALIDATION_DEFENSE上的表现")
    else:
        print("\n⚠️ 未生成任何训练样本")

    print("=" * 80)


if __name__ == "__main__":
    main()
