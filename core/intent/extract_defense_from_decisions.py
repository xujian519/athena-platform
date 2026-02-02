#!/usr/bin/env python3
"""
从专利无效决定书中提取成功辩护样本
Extract Successful Defense Samples from Patent Invalidation Decisions

功能:
1. 解析专利无效宣告请求审查决定
2. 识别专利权人成功的答辩
3. 提取关键辩护论据和表述
4. 生成意图识别训练数据

作者: Athena平台团队
版本: v1.0.0
创建: 2026-01-13
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any



@dataclass
class DefenseSample:
    """辩护样本数据结构"""

    original_text: str  # 原始答辩文本
    case_number: str  # 案号
    defense_type: str  # 辩护类型
    success: bool  # 是否成功
    key_arguments: list[str] = field(default_factory=list)  # 关键论据
    legal_basis: list[str] = field(default_factory=list)  # 法律依据
    extracted_queries: list[str] = field(default_factory=list)  # 生成的用户查询


class InvalidationDefenseExtractor:
    """从无效决定书中提取成功辩护的提取器"""

    def __init__(self, data_dir: str | None = None):
        """初始化提取器

        Args:
            data_dir: 数据目录路径
        """
        if data_dir is None:
            self.data_dir = Path("/Users/xujian/Athena工作平台/data")
        else:
            self.data_dir = Path(data_dir)

        # 成功辩护的关键词模式
        self.success_patterns = [
            r"维持.*有效",
            r"继续维持.*专利权",
            r"在.*基础上.*维持.*有效",
            r"驳回.*无效宣告请求",
            r"专利权人.*主张.*成立",
            r"撤销.*无效决定",
        ]

        # 辩护内容识别模式
        self.defense_section_patterns = [
            r"专利权人.*意见陈述",
            r"专利权人.*答辩",
            r"专利权人.*认为",
            r"专利权人.*称[::]",
            r"意见陈述书中.*称[::]",
        ]

        # 各种辩护类型的关键词
        self.defense_types = {
            "NOVELTY_DEFENSE": [  # 新颖性辩护
                r"不属于.*公开",
                r"存在区别.*技术特征",
                r"并未.*公开",
                r"不同.*技术领域",
            ],
            "CREATIVITY_DEFENSE": [  # 创造性辩护
                r"显而易见.*不成立",
                r"非显而易见",
                r"结合.*启示",
                r"技术效果.*显著",
                r"预料不到.*效果",
            ],
            "SUPPORT_DEFENSE": [  # 支持度辩护
                r"说明书.*支持",
                r"能够.*实现",
                r"充分公开",
                r"所属技术领域.*技术人员",
            ],
            "SCOPE_DEFENSE": [  # 保护范围辩护
                r"权利要求.*解释",
                r"字面含义",
                r"等同.*特征",
                r"限定.*作用",
            ],
            "PROCEDURAL_DEFENSE": [  # 程序性辩护
                r"证据.*不能接受",
                r"超出.*期限",
                r"举证.*责任",
                r"听证.*权利",
            ],
        }

        # 统计信息
        self.stats = {
            "total_files": 0,
            "success_cases": 0,
            "failed_cases": 0,
            "unclear_cases": 0,
            "extracted_defenses": 0,
        }

    def is_successful_defense(self, decision_text: str) -> bool:
        """判断是否为成功的辩护

        Args:
            decision_text: 决定书文本

        Returns:
            bool: 是否成功
        """
        # 检查成功关键词
        return any(re.search(pattern, decision_text) for pattern in self.success_patterns)

    def extract_defense_sections(self, decision_text: str) -> list[str]:
        """提取答辩章节

        Args:
            decision_text: 决定书全文

        Returns:
            list[str]: 答辩文本列表
        """
        defense_sections = []

        # 按段落分割
        paragraphs = decision_text.split("\n\n")

        current_defense = []
        in_defense_section = False

        for para in paragraphs:
            # 检查是否进入答辩章节
            for pattern in self.defense_section_patterns:
                if re.search(pattern, para):
                    in_defense_section = True
                    break

            # 如果在答辩章节中
            if in_defense_section:
                # 检查是否离开答辩章节(进入决定理由)
                if re.search(r"决定理由|决定如下|本委认为", para):
                    if current_defense:
                        defense_sections.append("\n".join(current_defense))
                        current_defense = []
                    in_defense_section = False
                else:
                    current_defense.append(para)

        # 添加最后一个答辩
        if current_defense:
            defense_sections.append("\n".join(current_defense))

        return defense_sections

    def classify_defense_type(self, defense_text: str) -> str:
        """分类辩护类型

        Args:
            defense_text: 答辩文本

        Returns:
            str: 辩护类型
        """
        scores = {}

        for defense_type, patterns in self.defense_types.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, defense_text))
                score += matches
            scores[defense_type] = score

        # 返回得分最高的类型
        if scores:
            max_type = max(scores, key=scores.get)
            if scores[max_type] > 0:
                return max_type

        return "GENERAL_DEFENSE"

    def extract_key_arguments(self, defense_text: str) -> list[str]:
        """提取关键论据

        Args:
            defense_text: 答辩文本

        Returns:
            list[str]: 关键论据列表
        """
        arguments = []

        # 提取论据模式
        argument_patterns = [
            r"[其该][专利发明].*?[^。?!]*?",
            r"技术特征.*?[^。?!]*?",
            r"区别.*?在于.*?",
            r"不同于.*?[^。?!]*?",
            r"对比文件.*?[^。?!]*?",
        ]

        for pattern in argument_patterns:
            matches = re.findall(pattern, defense_text)
            arguments.extend(matches[:3])  # 每种模式最多取3个

        return arguments[:10]  # 最多返回10个论据

    def generate_user_queries(self, defense_sample: DefenseSample) -> list[str]:
        """基于辩护样本生成用户查询

        Args:
            defense_sample: 辩护样本

        Returns:
            list[str]: 生成的用户查询
        """
        queries = []

        # 1. 通用答辩查询
        queries.extend(
            [
                "如何进行无效宣告答辩",
                f"{defense_sample.defense_type.replace('_', ' ')}的答辩策略",
                "无效答辩意见书的撰写要点",
            ]
        )

        # 2. 基于关键论据生成查询
        for arg in defense_sample.key_arguments[:3]:
            if len(arg) > 5:
                queries.append(f"如何论证:{arg[:30]}...")
                queries.append(f"针对'{arg[:20]}...'的答辩方法")

        # 3. 基于辩护类型生成特定查询
        defense_type_queries = {
            "NOVELTY_DEFENSE": [
                "新颖性无效宣告如何答辩",
                "如何反驳新颖性问题",
                "区别技术特征如何主张",
            ],
            "CREATIVITY_DEFENSE": [
                "创造性无效宣告如何答辩",
                "非显而易见性如何论证",
                "技术效果如何证明具有创造性",
            ],
            "SUPPORT_DEFENSE": [
                "说明书支持度如何辩护",
                "如何证明专利充分公开",
                "支持度问题如何答辩",
            ],
            "SCOPE_DEFENSE": [
                "权利要求解释规则如何运用",
                "保护范围如何界定",
                "等同原则在无效答辩中如何运用",
            ],
        }

        queries.extend(defense_type_queries.get(defense_sample.defense_type, []))

        return queries

    def process_decision_file(self, file_path: Path) -> list[DefenseSample]:
        """处理单个决定书文件

        Args:
            file_path: 文件路径

        Returns:
            list[DefenseSample]: 提取的辩护样本
        """
        samples = []

        try:
            # 读取文件
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # 提取文本内容(从各个层级中)
            content_parts = []
            case_number = "UNKNOWN"

            # 从 case_info 提取案号
            if "case_info" in data:
                case_info = data["case_info"]
                if isinstance(case_info, dict) and "case_id" in case_info:
                    case_number = case_info["case_id"]
                content_parts.append(str(case_info))

            # 从 layer1, layer2, layer3 提取内容
            for layer_key in ["layer1", "layer2", "layer3"]:
                if layer_key in data:
                    layer_content = data[layer_key]
                    if isinstance(layer_content, str):
                        content_parts.append(layer_content)
                    elif isinstance(layer_content, dict):
                        content_parts.extend(layer_content.values())
                    elif isinstance(layer_content, list):
                        content_parts.extend([str(item) for item in layer_content])

            # 合并所有内容
            content = "\n\n".join(content_parts)

            # 判断是否成功
            is_success = self.is_successful_defense(content)

            # 只提取成功的案例
            if is_success:
                # 提取答辩章节
                defense_sections = self.extract_defense_sections(content)

                for defense_text in defense_sections:
                    if len(defense_text) < 50:  # 过滤太短的文本
                        continue

                    # 分类辩护类型
                    defense_type = self.classify_defense_type(defense_text)

                    # 提取关键论据
                    key_arguments = self.extract_key_arguments(defense_text)

                    # 创建样本
                    sample = DefenseSample(
                        original_text=defense_text,
                        case_number=case_number,
                        defense_type=defense_type,
                        success=is_success,
                        key_arguments=key_arguments,
                    )

                    # 生成用户查询
                    sample.extracted_queries = self.generate_user_queries(sample)

                    samples.append(sample)

            # 更新统计
            self.stats["total_files"] += 1
            if is_success:
                self.stats["success_cases"] += 1
            else:
                self.stats["failed_cases"] += 1

            self.stats["extracted_defenses"] += len(samples)

        except Exception as e:
            print(f"处理文件失败 {file_path}: {e}")

        return samples

    def extract_from_directory(self, directory: str | None = None) -> list[DefenseSample]:
        """从目录中批量提取

        Args:
            directory: 目录路径

        Returns:
            list[DefenseSample]: 所有提取的样本
        """
        if directory is None:
            # 默认处理专利判决书目录
            directory = self.data_dir / "patent_judgments/processed"
        else:
            directory = Path(directory)

        all_samples = []

        print(f"🔍 开始扫描目录: {directory}")

        # 获取所有子目录和JSON文件(支持两种结构)
        json_files = []

        # 查找所有 *_structured.json 文件
        for item in directory.iterdir():
            if item.is_dir():
                # 子目录中的文件
                subdir_files = list(item.glob("*_structured.json"))
                json_files.extend(subdir_files)
            elif item.suffix == ".json" and "structured" in item.name:
                # 根目录中的文件
                json_files.append(item)

        print(f"📂 找到 {len(json_files)} 个结构化文件")

        for i, file_path in enumerate(json_files, 1):
            if i % 100 == 0:
                print(f"  进度: {i}/{len(json_files)}")

            samples = self.process_decision_file(file_path)
            all_samples.extend(samples)

        return all_samples

    def export_training_data(self, samples: list[DefenseSample], output_file: str | None = None) -> Any:
        """导出为训练数据格式

        Args:
            samples: 辩护样本列表
            output_file: 输出文件路径
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = (
                self.data_dir / f"intent_training/invalidation_defense_training_{timestamp}.json"
            )

        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 转换为训练数据格式
        training_data = []

        for sample in samples:
            # 每个样本生成多个训练对
            for query in sample.extracted_queries:
                training_data.append(
                    {
                        "text": query,
                        "intent": "INVALIDATION_DEFENSE",
                        "metadata": {
                            "case_number": sample.case_number,
                            "defense_type": sample.defense_type,
                            "source": "invalidation_decision",
                            "confidence": "high" if sample.success else "medium",
                        },
                    }
                )

        # 保存
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 训练数据已保存到: {output_file}")
        print(f"   总样本数: {len(training_data)}")
        print(f"   来源案例数: {len(samples)}")

        return output_file

    def print_statistics(self) -> Any:
        """打印统计信息"""
        print("\n" + "=" * 70)
        print("📊 提取统计")
        print("=" * 70)
        print(f"总处理文件数: {self.stats['total_files']}")
        print(
            f"成功辩护案例: {self.stats['success_cases']} ({self.stats['success_cases']/max(self.stats['total_files'],1)*100:.1f}%)"
        )
        print(f"失败辩护案例: {self.stats['failed_cases']}")
        print(f"提取辩护样本: {self.stats['extracted_defenses']}")
        print("=" * 70)


def main() -> None:
    """主程序"""
    print("🎯 从专利无效决定书提取成功辩护样本")
    print("=" * 70)

    # 初始化提取器
    extractor = InvalidationDefenseExtractor()

    # 提取样本
    samples = extractor.extract_from_directory()

    # 打印统计
    extractor.print_statistics()

    # 显示一些样本示例
    if samples:
        print("\n📋 样本示例 (前3个):")
        print("=" * 70)
        for i, sample in enumerate(samples[:3], 1):
            print(f"\n样本 {i}:")
            print(f"  案号: {sample.case_number}")
            print(f"  类型: {sample.defense_type}")
            print(f"  成功: {sample.success}")
            print(f"  辩护文本: {sample.original_text[:100]}...")
            print(f"  关键论据: {sample.key_arguments[:2]}")
            print("  生成查询:")
            for query in sample.extracted_queries[:3]:
                print(f"    - {query}")

    # 导出训练数据
    if samples:
        extractor.export_training_data(samples)
        print("\n✅ 完成!训练数据已生成,可以用于重新训练意图识别模型。")
    else:
        print("\n⚠️ 未提取到任何样本,请检查数据源。")


if __name__ == "__main__":
    main()
