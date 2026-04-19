#!/usr/bin/env python3
"""
合并所有训练数据集,生成最终的超大训练集
Merge all training datasets into final comprehensive set

合并:
1. comprehensive_500 (500个)
2. notes_clarity_disclosure (247个)
3. 现有的其他数据集

目标:生成覆盖面最全的DSPy训练数据集

作者: 小娜·天秤女神
创建时间: 2025-12-29
版本: 1.0.0
"""

from __future__ import annotations
import json
import logging
import random
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class TrainingDataMerger:
    """训练数据合并器"""

    def __init__(self, data_dir: str = "core/intelligence/dspy/data"):
        """初始化合并器

        Args:
            data_dir: 数据目录
        """
        self.data_dir = Path(data_dir)

    def load_all_datasets(self) -> list[dict[str, Any]]:
        """加载所有数据集

        Returns:
            合并后的案例列表
        """
        logger.info("=" * 60)
        logger.info("加载所有训练数据集")
        logger.info("=" * 60)

        all_cases = []

        # 数据集列表
        datasets = [
            ("training_data_comprehensive_500.json", "多源综合500案例"),
            ("training_data_notes_clarity_disclosure.json", "笔记清楚性/充分公开247案例"),
            ("training_data_production_docx_100.json", "DOCX文件100案例"),
            ("training_data_real_100_enhanced.json", "Qdrant增强100案例"),
            ("training_data.json", "合成数据50案例"),
        ]

        for filename, description in datasets:
            file_path = self.data_dir / filename
            if not file_path.exists():
                logger.warning(f"文件不存在: {filename}")
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)

                cases = data.get("cases", [])
                logger.info(f"加载 {description}: {len(cases)} 个案例")

                # 标记数据源
                for case in cases:
                    if "_source" not in case:
                        case["_source"] = filename.replace(".json", "")

                all_cases.extend(cases)

            except Exception as e:
                logger.error(f"加载 {filename} 失败: {e}")
                continue

        logger.info(f"\n总共加载 {len(all_cases)} 个案例")
        return all_cases

    def deduplicate_cases(self, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """去重案例

        Args:
            cases: 原始案例列表

        Returns:
            去重后的案例列表
        """
        logger.info("去重案例...")

        seen_ids = set()
        unique_cases = []

        for case in cases:
            case_id = case.get("_id", case.get("case_id", ""))
            if case_id and case_id not in seen_ids:
                seen_ids.add(case_id)
                unique_cases.append(case)

        removed = len(cases) - len(unique_cases)
        logger.info(f"去重完成: 移除 {removed} 个重复案例")

        return unique_cases

    def balance_distribution(
        self, cases: list[dict[str, Any]], target_count: int = 800
    ) -> list[dict[str, Any]]:
        """平衡案例分布

        Args:
            cases: 原始案例列表
            target_count: 目标数量

        Returns:
            平衡后的案例列表
        """
        logger.info("=" * 60)
        logger.info("平衡案例分布")
        logger.info("=" * 60)

        # 统计当前分布
        by_type = defaultdict(list)
        for case in cases:
            case_type = case.get("case_type", "unknown")
            by_type[case_type].append(case)

        logger.info("\n原始案例类型分布:")
        for case_type, type_cases in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
            logger.info(f"  {case_type}: {len(type_cases)}")

        # 目标分布
        target_distribution = {
            "creative": 250,  # 31.25%
            "novelty": 150,  # 18.75%
            "disclosure": 150,  # 18.75%
            "clarity": 150,  # 18.75%
            "procedural": 80,  # 10.0%
            "complex": 20,  # 2.5%
        }

        balanced = []

        # 按目标分布采样
        for case_type, target_num in target_distribution.items():
            available = by_type.get(case_type, [])

            if len(available) >= target_num:
                # 有足够的案例,随机采样
                sampled = random.sample(available, target_num)
                balanced.extend(sampled)
                logger.info(f"{case_type}: 采样 {target_num}/{len(available)}")
            else:
                # 案例不足,全部使用
                balanced.extend(available)
                logger.info(f"{case_type}: 全部使用 {len(available)}/{target_num} (不足)")

                # 如果还不足,从其他类型补充
                shortage = target_num - len(available)
                if shortage > 0:
                    # 从相似的类型补充
                    if case_type == "disclosure":
                        supplement_source = "creative"
                    elif case_type == "clarity":
                        supplement_source = "procedural"
                    else:
                        supplement_source = "creative"

                    source_cases = [
                        c for c in by_type.get(supplement_source, []) if c not in balanced
                    ]

                    if source_cases:
                        supplement_count = min(shortage, len(source_cases))
                        supplement = random.sample(source_cases, supplement_count)

                        # 修改案例类型
                        for i in range(supplement_count):
                            case_copy = supplement[i].copy()
                            case_copy["case_type"] = case_type
                            orig_id = case_copy.get("_id", case_copy.get("case_id", f"case_{i}"))
                            case_copy["_id"] = f"{orig_id}_SUPP"
                            balanced.append(case_copy)

                        logger.info(
                            f"{case_type}: 从 {supplement_source} 补充 {supplement_count} 个"
                        )

        # 确保总数不超过目标
        final_cases = balanced[:target_count]

        # 统计最终分布
        by_type_final = Counter(c["case_type"] for c in final_cases)
        logger.info("\n最终案例类型分布:")
        for case_type, count in by_type_final.most_common():
            pct = count / len(final_cases) * 100
            logger.info(f"  {case_type}: {count} ({pct:.1f}%)")

        return final_cases

    def generate_final_dataset(
        self, target_count: int = 800, output_dir: str = "core/intelligence/dspy/data"
    ) -> list[dict[str, Any]]:
        """生成最终数据集

        Args:
            target_count: 目标案例数量
            output_dir: 输出目录

        Returns:
            最终案例列表
        """
        logger.info("=" * 60)
        logger.info(f"生成最终训练数据集 (目标: {target_count} 个案例)")
        logger.info("=" * 60)

        # 1. 加载所有数据集
        all_cases = self.load_all_datasets()

        if not all_cases:
            logger.error("没有可用的数据")
            return []

        # 2. 去重
        unique_cases = self.deduplicate_cases(all_cases)

        # 3. 平衡分布
        balanced_cases = self.balance_distribution(unique_cases, target_count)

        # 4. 确保数据质量
        quality_cases = self._ensure_quality(balanced_cases)

        logger.info(f"\n最终生成 {len(quality_cases)} 个高质量案例")

        # 5. 统计信息
        self._print_statistics(quality_cases)

        # 6. 保存数据
        self._save_final_dataset(quality_cases, output_dir)

        return quality_cases

    def _ensure_quality(self, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """确保数据质量

        Args:
            cases: 原始案例列表

        Returns:
            质量检查后的案例列表
        """
        logger.info("检查数据质量...")

        quality_cases = []

        for case in cases:
            # 检查必需字段
            required_fields = ["_id", "case_type", "technical_field", "background", "legal_issues"]
            if all(case.get(field) for field in required_fields):
                # 确保文本长度合理
                if len(case.get("text", "")) >= 100:
                    quality_cases.append(case)

        removed = len(cases) - len(quality_cases)
        logger.info(f"质量检查: 移除 {removed} 个不合格案例")

        return quality_cases

    def _print_statistics(self, cases: list[dict[str, Any]]) -> Any:
        """打印统计信息"""
        logger.info("\n" + "=" * 60)
        logger.info("最终数据统计")
        logger.info("=" * 60)

        # 案例类型分布
        type_counter = Counter(c["case_type"] for c in cases)
        logger.info("\n案例类型分布:")
        for case_type, count in type_counter.most_common():
            pct = count / len(cases) * 100
            logger.info(f"  {case_type}: {count} ({pct:.1f}%)")

        # 技术领域分布
        field_counter = Counter(c["technical_field"] for c in cases)
        logger.info("\n技术领域分布 (Top 15):")
        for field, count in field_counter.most_common(15):
            pct = count / len(cases) * 100
            logger.info(f"  {field}: {count} ({pct:.1f}%)")

        # 决定结果分布
        outcome_counter = Counter(c.get("decision_outcome", "未知") for c in cases)
        logger.info("\n决定结果分布:")
        for outcome, count in outcome_counter.most_common(10):
            pct = count / len(cases) * 100
            logger.info(f"  {outcome}: {count} ({pct:.1f}%)")

        # 数据源分布
        source_counter = Counter(c.get("_source", "unknown") for c in cases)
        logger.info("\n数据源分布:")
        for source, count in source_counter.most_common(10):
            pct = count / len(cases) * 100
            logger.info(f"  {source}: {count} ({pct:.1f}%)")

        # 字符统计
        char_counts = [c.get("char_count", len(c.get("text", ""))) for c in cases]
        logger.info("\n文本长度统计:")
        logger.info(f"  平均: {sum(char_counts) / len(char_counts):.0f} 字符")
        logger.info(f"  最小: {min(char_counts)} 字符")
        logger.info(f"  最大: {max(char_counts)} 字符")

    def _save_final_dataset(self, cases: list[dict[str, Any]], output_dir: str) -> Any:
        """保存最终数据集"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. 保存JSON格式
        json_file = output_path / f"training_data_FINAL_800_{timestamp}.json"

        data = {
            "metadata": {
                "total_cases": len(cases),
                "source": "Merged: Comprehensive 500 + Notes 247 + Others",
                "generated_at": datetime.now().isoformat(),
                "extraction_method": "comprehensive_merged",
                "dataset_version": "FINAL_800",
            },
            "cases": cases,
        }

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n已保存JSON格式到: {json_file}")

        # 2. 保存DSPy格式
        dspy_file = output_path / f"training_data_FINAL_800_{timestamp}_dspy.py"

        with open(dspy_file, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("# -*- coding: utf-8 -*-\n")
            f.write('"""\n')
            f.write("DSPy训练数据 - 最终完整版800案例\n")
            f.write(f"生成时间: {datetime.now().isoformat()}\n")
            f.write(f"案例数量: {len(cases)}\n")
            f.write("数据来源: 综合多源数据集 (DOCX + Qdrant + 笔记 + 合成)\n")
            f.write('"""\n\n')
            f.write("import dspy\n")
            f.write("from typing import List, Dict, Any\n\n")
            f.write("# DSPy训练数据集 - 最终完整版\n")
            f.write("trainset: list[dspy.Example] = [\n")

            for i, case in enumerate(cases):
                f.write("    dspy.Example(\n")
                f.write(f"        case_id='{case['_id']}',\n")
                f.write(f"        case_type='{case['case_type']}',\n")
                f.write(f"        technical_field='{case['technical_field']}',\n")
                f.write(f"        patent_number='{case['patent_number']}',\n")
                f.write(f"        decision_outcome='{case['decision_outcome']}',\n")

                # 输入字段
                background_text = case["background"][:200].replace("'''", "\\'\\'\\'")
                f.write(f"        background='''{background_text}''',\n")

                # 输出字段
                legal_issues_str = str(case["legal_issues"])
                f.write(f"        legal_issues={legal_issues_str},\n")

                reasoning_text = case.get("decision_reasoning", case.get("dispute_details", ""))[
                    :300
                ]
                reasoning_text = reasoning_text.replace("'''", "\\'\\'\\'")
                f.write(f"        reasoning='''{reasoning_text}'''\n")
                f.write("    ).with_inputs('background', 'technical_field', 'patent_number'),\n\n")

                # 每100个案例添加一个注释
                if (i + 1) % 100 == 0:
                    f.write(f"    # 已加载 {i + 1} 个案例\n\n")

            f.write("]\n")

        logger.info(f"已保存DSPy格式到: {dspy_file}")

        # 3. 创建latest软链接
        latest_json = output_path / "training_data_FINAL_800_latest.json"
        latest_dspy = output_path / "training_data_FINAL_800_latest_dspy.py"

        try:
            if latest_json.exists():
                latest_json.unlink()
            if latest_dspy.exists():
                latest_dspy.unlink()

            import shutil

            shutil.copy(json_file, latest_json)
            shutil.copy(dspy_file, latest_dspy)

            logger.info("已创建latest软链接")
        except Exception as e:
            logger.warning(f"创建软链接失败: {e}")


def main() -> None:
    """主函数"""
    merger = TrainingDataMerger()

    # 生成最终数据集
    cases = merger.generate_final_dataset(target_count=800)

    print("\n" + "=" * 60)
    print("最终训练数据集生成完成!")
    print("=" * 60)
    print(f"总案例数: {len(cases)}")


if __name__ == "__main__":
    main()
