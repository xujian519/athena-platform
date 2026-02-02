#!/usr/bin/env python3
"""
从无效决定书双向提取统一训练样本
Bidirectional Extraction from Invalidation Decisions

从同一份无效决定书中提取申请人和专利权人双视角的训练样本

作者: Athena平台团队
版本: v1.0.0
创建: 2026-01-13
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any



class BidirectionalInvalidationExtractor:
    """
    双向无效样本提取器

    核心创新:
    - 从决定书中提取申请人视角的查询(如何无效)
    - 从决定书中提取专利权人视角的查询(如何答辩)
    - 从决定书中提取程序性查询(通用查询)
    """

    # 成功辩护关键词
    SUCCESS_PATTERNS = [
        r"维持.*有效",
        r"继续维持.*专利权",
        r"在.*基础上.*维持.*有效",
        r"驳回.*无效宣告请求",
        r"专利权人.*主张.*成立",
    ]

    # 请求人主张标识
    APPLICANT_PATTERNS = [
        r"请求人.*认为[::]",
        r"请求人.*称[::]",
        r"请求人.*主张[::]",
        r"无效宣告请求人.*认为[::]",
        r"原告.*认为[::]",
    ]

    # 专利权人答辩标识
    OWNER_PATTERNS = [
        r"专利权人.*认为[::]",
        r"专利权人.*称[::]",
        r"专利权人.*答辩[::]",
        r"专利权人.*意见陈述[::]",
        r"被告.*认为[::]",
        r"被请求人.*答辩[::]",
    ]

    def __init__(self):
        """初始化提取器"""
        pass

    def extract_text_from_json(self, data: Any) -> str:
        """递归提取JSON中的所有文本内容"""
        texts = []

        if isinstance(data, str):
            texts.append(data)
        elif isinstance(data, dict):
            for value in data.values():
                texts.extend(self.extract_text_from_json(value))
        elif isinstance(data, list):
            for item in data:
                texts.extend(self.extract_text_from_json(item))

        return "\n".join(texts)

    def is_successful_defense(self, text: str) -> bool:
        """判断是否为成功的辩护"""
        return any(re.search(pattern, text) for pattern in self.SUCCESS_PATTERNS)

    def extract_applicant_sections(self, text: str) -> list[str]:
        """
        提取请求人主张部分

        返回: 请求人主张的文本段落列表
        """
        sections = []

        # 按请求人标识分割
        for pattern in self.APPLICANT_PATTERNS:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                start = match.start()
                # 提取从这个位置开始到下一个标识或段落的文本(约500字符)
                end = min(start + 500, len(text))
                section = text[start:end].strip()
                if len(section) > 20:  # 过滤太短的片段
                    sections.append(section)

        return sections

    def extract_owner_sections(self, text: str) -> list[str]:
        """
        提取专利权人答辩部分

        返回: 专利权人答辩的文本段落列表
        """
        sections = []

        # 按专利权人标识分割
        for pattern in self.OWNER_PATTERNS:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                start = match.start()
                # 提取从这个位置开始到下一个标识或段落的文本(约500字符)
                end = min(start + 500, len(text))
                section = text[start:end].strip()
                if len(section) > 20:  # 过滤太短的片段
                    sections.append(section)

        return sections

    def extract_procedural_sections(self, text: str) -> list[str]:
        """
        提取程序性描述

        返回: 程序性文本段落列表
        """
        sections = []

        # 程序性关键词
        procedural_patterns = [
            r"本案.*于.*进行了口头审理",
            r"口头审理.*举行",
            r"合议组.*认为",
            r"审查.*程序",
            r"审理.*阶段",
            r"决定.*作出",
        ]

        for pattern in procedural_patterns:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                start = max(0, match.start() - 50)
                end = min(match.end() + 200, len(text))
                section = text[start:end].strip()
                if len(section) > 20:
                    sections.append(section)

        return sections

    def generate_applicant_queries(self, section: str) -> list[str]:
        """
        从请求人主张生成申请人视角的查询

        输入: "请求人认为对比文件D1公开了权利要求1的技术特征A"
        输出: [
            "如何用D1无效权利要求1",
            "D1公开了哪些技术特征",
            "怎样证明没有新颖性"
        ]
        """
        queries = []

        # 提取关键实体
        d_refs = re.findall(r"D\d+", section)  # 对比文件引用
        claim_refs = re.findall(r"权利要求\d+", section)  # 权利要求引用

        # 新颖性相关
        if "公开" in section or " disclose" in section.lower():
            if d_refs:
                queries.append(f"如何用{d_refs[0]}进行无效宣告")
                queries.append(f"{d_refs[0]}公开了哪些技术特征")

            if claim_refs:
                queries.append(f"{claim_refs[0]}有新颖性吗")
                queries.append(f"如何证明{claim_refs[0]}没有新颖性")

            queries.append("对比文件如何用于无效")
            queries.append("怎样构建新颖性无效理由")

        # 创造性相关
        if "显而易见" in section or "结合" in section or "启示" in section:
            if d_refs and len(d_refs) > 1:
                queries.append(f"如何组合{d_refs[0]}和{d_refs[1]}进行无效")
                queries.append("多篇对比文件结合无效的方法")

            queries.append("如何论证专利缺乏创造性")
            queries.append("显而易见性无效理由如何主张")

        # 通用无效查询
        if "无效理由" in section or "无效宣告" in section:
            queries.append("无效理由怎么组织")
            queries.append("无效宣告理由书怎么写")

        return queries

    def generate_owner_queries(self, section: str) -> list[str]:
        """
        从专利权人答辩生成专利权人视角的查询

        输入: "专利权人认为D1未公开区别技术特征X"
        输出: [
            "如何反驳D1的指控",
            "区别技术特征怎么主张",
            "怎样维持专利有效"
        ]
        """
        queries = []

        # 新颖性辩护
        if "未公开" in section or "不存在" in section:
            d_refs = re.findall(r"D\d+", section)
            if d_refs:
                queries.append(f"如何反驳{d_refs[0]}的公开指控")
                queries.append(f"{d_refs[0]}真的公开了吗")

            queries.append("对比文件未公开如何论证")
            queries.append("区别技术特征如何主张")
            queries.append("新颖性答辩的论证方法")

        # 创造性辩护
        if "区别技术特征" in section or "技术效果" in section:
            queries.append("如何论证技术特征的区别")
            queries.append("技术效果如何证明")
            queries.append("创造性答辩的策略")

        # 通用答辩查询
        if "答辩" in section or "主张" in section:
            queries.append("无效答辩怎么写")
            queries.append("如何组织答辩论据")
            queries.append("如何维持专利权有效")

        return queries

    def generate_procedural_queries(self, section: str) -> list[str]:
        """
        从程序描述生成程序性查询

        输入: "本案于2025年3月10日进行了口头审理"
        输出: [
            "口头审理程序是怎样的",
            "口审需要准备什么"
        ]
        """
        queries = []

        # 口审程序
        if "口头审理" in section or "口审" in section:
            queries.append("口头审理程序是怎样的")
            queries.append("口审需要准备什么材料")
            queries.append("口头审理如何参加")

        # 审查期限
        if "期限" in section or "时间" in section or "日期" in section:
            queries.append("无效审查需要多长时间")
            queries.append("无效程序的期限规定")

        # 决定作出
        if "决定" in section:
            queries.append("无效决定何时作出")
            queries.append("如何查询无效案件进度")

        return queries

    def process_decision_file(self, file_path: Path) -> list[dict[str, Any]]:
        """
        处理单个决定书文件

        返回: 提取的训练样本列表
        """
        training_samples = []

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # 提取所有文本
            full_text = self.extract_text_from_json(data)

            # 判断是否为成功辩护案例
            if not self.is_successful_defense(full_text):
                return training_samples

            # 提取案号
            case_number = "UNKNOWN"
            if isinstance(data, dict) and "case_info" in data:
                if isinstance(data["case_info"], dict):
                    case_number = data["case_info"].get("case_id", "UNKNOWN")

            # 提取请求人部分并生成查询
            applicant_sections = self.extract_applicant_sections(full_text)
            for section in applicant_sections[:3]:  # 每个文件最多取3段
                queries = self.generate_applicant_queries(section)
                for query in queries:
                    training_samples.append(
                        {
                            "text": query,
                            "intent": "INVALIDATION_GROUNDS",  # 申请人主要是无效理由
                            "metadata": {
                                "case_number": case_number,
                                "scenario": "提起无效申请",
                                "role": "无效申请人",
                                "source_section": section[:100],
                                "tier": "extracted",
                                "confidence": "medium",
                                "domain": "patent_invalidation_unified",
                                "extracted_from": str(file_path.name),
                            },
                        }
                    )

            # 提取专利权人部分并生成查询
            owner_sections = self.extract_owner_sections(full_text)
            for section in owner_sections[:3]:
                queries = self.generate_owner_queries(section)
                for query in queries:
                    training_samples.append(
                        {
                            "text": query,
                            "intent": "INVALIDATION_DEFENSE",  # 专利权人主要是答辩
                            "metadata": {
                                "case_number": case_number,
                                "scenario": "应对无效宣告",
                                "role": "专利权人",
                                "source_section": section[:100],
                                "tier": "extracted",
                                "confidence": "medium",
                                "domain": "patent_invalidation_unified",
                                "extracted_from": str(file_path.name),
                            },
                        }
                    )

            # 提取程序部分并生成查询
            procedural_sections = self.extract_procedural_sections(full_text)
            for section in procedural_sections[:2]:
                queries = self.generate_procedural_queries(section)
                for query in queries:
                    training_samples.append(
                        {
                            "text": query,
                            "intent": "PROSECUTION_HISTORY_ESTOPPEL",  # 程序性问题
                            "metadata": {
                                "case_number": case_number,
                                "scenario": "审查程序",
                                "role": "双方通用",
                                "source_section": section[:100],
                                "tier": "extracted",
                                "confidence": "medium",
                                "domain": "patent_invalidation_unified",
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
    print("🎯 从无效决定书双向提取统一训练样本")
    print("=" * 80)

    extractor = BidirectionalInvalidationExtractor()

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

    # 为了演示,只处理前1000个文件
    # 实际使用时可以处理全部文件
    sample_files = json_files[:1000]
    print("⚠️ 演示模式: 只处理前1000个文件")

    # 处理文件
    all_training_data = []
    applicant_samples = 0
    owner_samples = 0
    procedural_samples = 0

    print("\n⏳ 处理中...")

    for i, file_path in enumerate(sample_files, 1):
        if i % 100 == 0:
            print(f"  进度: {i}/{len(sample_files)} ({i/len(sample_files)*100:.1f}%)")

        samples = extractor.process_decision_file(file_path)

        for sample in samples:
            role = sample["metadata"]["role"]
            if role == "无效申请人":
                applicant_samples += 1
            elif role == "专利权人":
                owner_samples += 1
            elif role == "双方通用":
                procedural_samples += 1

            all_training_data.append(sample)

    # 统计
    print("\n" + "=" * 80)
    print("📊 提取统计")
    print("=" * 80)
    print(f"处理文件数: {len(sample_files)}")
    print(f"总样本数: {len(all_training_data)}")
    print("\n角色分布:")
    print(
        f"  申请人样本: {applicant_samples} ({applicant_samples/len(all_training_data)*100:.1f}%)"
    )
    print(f"  专利权人样本: {owner_samples} ({owner_samples/len(all_training_data)*100:.1f}%)")
    print(
        f"  程序性样本: {procedural_samples} ({procedural_samples/len(all_training_data)*100:.1f}%)"
    )

    # 按意图统计
    intent_counts = {}
    for sample in all_training_data:
        intent = sample["intent"]
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    print("\n意图分布:")
    for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {intent}: {count}个")

    # 保存训练数据
    if all_training_data:
        output_dir = Path("/Users/xujian/Athena工作平台/data/intent_training")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"unified_invalidation_extracted_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_training_data, f, ensure_ascii=False, indent=2)

        print("\n✅ 训练数据已保存到:")
        print(f"   {output_file}")

        print("\n📋 下一步:")
        print("   1. 合并专家样本和提取样本")
        print("   2. 去重和质量过滤")
        print("   3. 合并到现有训练集")
        print("   4. 重新训练意图识别模型")
        print("   5. 验证全流程识别效果")
    else:
        print("\n⚠️ 未生成任何训练样本")

    print("=" * 80)


if __name__ == "__main__":
    main()
