#!/usr/bin/env python3
from __future__ import annotations
"""
批处理推理模式提取器 - Batch Pattern Extractor
从实际无效决定文档中大规模提取推理模式

功能:
1. 扫描无效决定文档目录
2. 批量处理JSON格式的无效决定
3. 提取三步法推理模式
4. 构建推理模式库
5. 持久化存储模式库
6. 统计分析和可视化

版本: 1.0.0
创建时间: 2026-01-23
"""

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from tqdm import tqdm

from core.logging_config import setup_logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.legal_qa.pattern_extractor import (
    PatternExtractor,
    ReasoningPattern,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/Users/xujian/Athena工作平台/logs/pattern_extraction.log"),
        logging.StreamHandler(),
    ],
)
logger = setup_logging()

# 配置
SOURCE_DIR = Path("/Users/xujian/Athena工作平台/data/patent_judgments/processed")
OUTPUT_DIR = Path("/Users/xujian/Athena工作平台/data/reasoning_patterns")
BATCH_SIZE = 100


@dataclass
class ExtractionStatistics:
    """提取统计信息"""

    total_files: int = 0
    processed_files: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    total_patterns: int = 0
    by_technical_field: dict[str, int] = field(default_factory=dict)
    by_conclusion: dict[str, int] = field(default_factory=dict)
    avg_confidence: float = 0.0
    start_time: datetime | None = None
    end_time: datetime | None = None

    def duration(self) -> float:
        """计算耗时(秒)"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class BatchPatternExtractor:
    """批处理推理模式提取器"""

    def __init__(self, source_dir: Path, output_dir: Path):
        """
        初始化批处理提取器

        Args:
            source_dir: 源数据目录
            output_dir: 输出目录
        """
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化提取器
        self.extractor = PatternExtractor()

        # 统计信息
        self.stats = ExtractionStatistics()

        # 模式库
        self.pattern_library: list[ReasoningPattern] = []

        logger.info("✅ 批处理提取器初始化成功")
        logger.info(f"📂 源目录: {self.source_dir}")
        logger.info(f"📤 输出目录: {self.output_dir}")

    def scan_files(self) -> list[Path]:
        """
        扫描JSON文件

        Returns:
            JSON文件路径列表
        """
        logger.info("=" * 70)
        logger.info("🔍 扫描无效决定文档...")
        logger.info("=" * 70)

        json_files = list(self.source_dir.rglob("*_structured.json"))

        self.stats.total_files = len(json_files)

        logger.info(f"✅ 找到 {len(json_files):,} 个JSON文件")
        logger.info("=" * 70)

        return json_files

    def load_invalid_decision(self, file_path: Path) -> Optional[dict[str, Any]]:
        """
        加载无效决定JSON文件

        Args:
            file_path: JSON文件路径

        Returns:
            无效决定数据
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ 加载失败 {file_path.name}: {e}")
            return None

    def extract_text_from_decision(self, data: dict[str, Any]) -> str:
        """
        从无效决定数据中提取完整文本

        Args:
            data: 无效决定JSON数据

        Returns:
            完整文本
        """
        text_parts = []

        # 提取案件信息
        case_info = data.get("case_info", {})
        if case_info.get("case_type"):
            text_parts.append(case_info["case_type"])

        # 提取layer2内容(专利专业文档)
        layer2 = data.get("layer2", {})
        for _key, value in layer2.items():
            if isinstance(value, dict) and "focus_description" in value:
                text_parts.append(value["focus_description"])

        # 提取layer3内容(裁判文书和争议焦点)
        layer3 = data.get("layer3", [])
        if isinstance(layer3, list):
            for item in layer3:
                if isinstance(item, dict) and "dispute_focus" in item:
                    text_parts.append(item["dispute_focus"])

        return "\n\n".join(text_parts)

    def process_file(self, file_path: Path) -> bool:
        """
        处理单个文件

        Args:
            file_path: JSON文件路径

        Returns:
            是否成功提取
        """
        # 加载数据
        data = self.load_invalid_decision(file_path)
        if not data:
            self.stats.failed_extractions += 1
            return False

        try:
            # 提取文本
            text = self.extract_text_from_decision(data)

            if not text or len(text) < 100:
                logger.warning(f"⚠️ 文本过短,跳过: {file_path.name}")
                return False

            # 提取元数据
            case_info = data.get("case_info", {})
            metadata = {
                "decision_id": case_info.get("case_id", file_path.stem),
                "patent_number": self._extract_patent_number(text),
                "technical_field": self._classify_technical_field(text),
                "source_file": str(file_path),
            }

            # 解析无效决定
            decision = self.extractor.parse_decision(text, metadata)

            # 提取推理模式
            patterns = self.extractor.extract_patterns(decision)

            if patterns:
                self.stats.successful_extractions += 1
                self.stats.total_patterns += len(patterns)

                # 添加到模式库
                for pattern in patterns:
                    # 更新统计
                    field = pattern.technical_field
                    self.stats.by_technical_field[field] = (
                        self.stats.by_technical_field.get(field, 0) + 1
                    )

                    conclusion = pattern.conclusion.value
                    self.stats.by_conclusion[conclusion] = (
                        self.stats.by_conclusion.get(conclusion, 0) + 1
                    )

                self.pattern_library.extend(patterns)
                return True
            else:
                logger.warning(f"⚠️ 未提取到推理模式: {file_path.name}")
                return False

        except Exception as e:
            logger.error(f"❌ 处理失败 {file_path.name}: {e}")
            self.stats.failed_extractions += 1
            return False

    def _extract_patent_number(self, text: str) -> str:
        """提取专利号"""
        import re

        # 匹配中国专利号
        patterns = [r"CN\d{9}\.\d", r"CN\d{9}", r"CZ\d+\.\d", r"ZL\d{12}"]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return ""

    def _classify_technical_field(self, text: str) -> str:
        """分类技术领域"""
        # 技术领域关键词
        field_keywords = {
            "机械制造": ["机械", "传动", "结构", "装配", "加工", "成型", "齿轮", "轴承"],
            "电子通信": ["电子", "通信", "电路", "信号", "天线", "调制", "芯片", "半导体"],
            "计算机软件": ["计算机", "软件", "算法", "数据", "网络", "系统", "程序"],
            "化学材料": ["化学", "材料", "合成", "反应", "催化", "聚合物", "化合物"],
            "生物医药": ["医疗", "药物", "治疗", "诊断", "生物", "基因", "口腔"],
            "汽车工程": ["汽车", "车辆", "发动机", "制动", "转向", "悬挂"],
        }

        scores = {}
        for field_name, keywords in field_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[field_name] = score

        if scores:
            return max(scores, key=scores.get)

        return "其他"

    def run(self, max_files: Optional[int] = None) -> None:
        """
        运行批处理提取流程

        Args:
            max_files: 最大处理文件数(用于测试)
        """
        logger.info("\n" + "=" * 70)
        logger.info("🚀 开始批处理推理模式提取")
        logger.info("=" * 70)

        self.stats.start_time = datetime.now()

        # 扫描文件
        json_files = self.scan_files()

        if not json_files:
            logger.error("❌ 未找到JSON文件")
            return

        # 限制处理数量(用于测试)
        if max_files:
            json_files = json_files[:max_files]
            logger.info(f"📊 测试模式:仅处理前 {max_files} 个文件")

        # 批处理
        logger.info("\n" + "=" * 70)
        logger.info("📄 开始处理文件...")
        logger.info("=" * 70 + "\n")

        for i in range(0, len(json_files), BATCH_SIZE):
            batch = json_files[i : i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (len(json_files) + BATCH_SIZE - 1) // BATCH_SIZE

            logger.info(f"批次 {batch_num}/{total_batches} ({len(batch)} 个文件)")

            for file_path in tqdm(batch, desc=f"批次 {batch_num}", ncols=80):
                if self.process_file(file_path):
                    self.stats.processed_files += 1

            # 每批次后保存中间结果
            if batch_num % 10 == 0:
                self.save_patterns(f"patterns_batch_{batch_num}.json")
                logger.info(f"💾 已保存中间结果 (批次 {batch_num})")

        self.stats.end_time = datetime.now()

        # 保存最终结果
        self.save_patterns("patterns_final.json")
        self.save_statistics()

        # 显示统计信息
        self.print_statistics()

        logger.info("\n" + "=" * 70)
        logger.info("✅ 批处理提取完成")
        logger.info("=" * 70)

    def save_patterns(self, filename: str) -> None:
        """
        保存推理模式库

        Args:
            filename: 输出文件名
        """
        output_path = self.output_dir / filename

        # 转换为可序列化格式
        patterns_data = []
        for pattern in self.pattern_library:
            pattern_dict = asdict(pattern)
            # 转换枚举类型
            pattern_dict["conclusion"] = pattern.conclusion.value
            patterns_data.append(pattern_dict)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(patterns_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 已保存 {len(patterns_data)} 个推理模式到: {output_path}")

    def save_statistics(self) -> None:
        """保存统计信息"""
        stats_path = self.output_dir / "extraction_statistics.json"

        stats_data = {
            "total_files": self.stats.total_files,
            "processed_files": self.stats.processed_files,
            "successful_extractions": self.stats.successful_extractions,
            "failed_extractions": self.stats.failed_extractions,
            "total_patterns": self.stats.total_patterns,
            "by_technical_field": self.stats.by_technical_field,
            "by_conclusion": self.stats.by_conclusion,
            "avg_confidence": self.stats.avg_confidence,
            "duration_seconds": self.stats.duration(),
            "start_time": self.stats.start_time.isoformat() if self.stats.start_time else None,
            "end_time": self.stats.end_time.isoformat() if self.stats.end_time else None,
        }

        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 已保存统计信息到: {stats_path}")

    def print_statistics(self) -> None:
        """打印统计信息"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 提取统计信息")
        logger.info("=" * 70)

        logger.info(f"总文件数:       {self.stats.total_files:,}")
        logger.info(f"已处理文件:     {self.stats.processed_files:,}")
        logger.info(f"成功提取:       {self.stats.successful_extractions:,}")
        logger.info(f"失败提取:       {self.stats.failed_extractions:,}")
        logger.info(f"总模式数:       {self.stats.total_patterns:,}")
        logger.info(f"耗时:           {self.stats.duration():.1f}秒")
        logger.info(
            f"平均速度:       {self.stats.processed_files/self.stats.duration():.2f} 文件/秒"
            if self.stats.duration() > 0
            else ""
        )

        if self.stats.by_technical_field:
            logger.info("\n按技术领域分布:")
            for field, count in sorted(
                self.stats.by_technical_field.items(), key=lambda x: x[1], reverse=True
            ):
                logger.info(f"  {field}: {count:,}")

        if self.stats.by_conclusion:
            logger.info("\n按结论分布:")
            for conclusion, count in sorted(
                self.stats.by_conclusion.items(), key=lambda x: x[1], reverse=True
            ):
                logger.info(f"  {conclusion}: {count:,}")

        logger.info("=" * 70)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="批处理推理模式提取器")
    parser.add_argument("--max-files", type=int, default=None, help="最大处理文件数(用于测试)")
    parser.add_argument("--source-dir", type=str, default=str(SOURCE_DIR), help="源数据目录")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR), help="输出目录")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="批处理大小")

    args = parser.parse_args()

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 创建提取器
    extractor = BatchPatternExtractor(source_dir=Path(args.source_dir), output_dir=output_dir)

    try:
        # 运行批处理
        extractor.run(max_files=args.max_files)

    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断,保存中间结果...")
        extractor.save_patterns("patterns_interrupted.json")
        extractor.save_statistics()
        logger.info("✅ 中间结果已保存")

    except Exception as e:
        logger.error(f"❌ 批处理失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
