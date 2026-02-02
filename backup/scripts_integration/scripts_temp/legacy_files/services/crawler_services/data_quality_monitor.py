#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量监控系统
Data Quality Monitoring System

建立知识图谱数据质量监控和预警机制
"""

import json
import logging
import os
import sqlite3
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/xujian/Athena工作平台/documentation/logs/data_quality_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """质量指标"""
    kg_type: str
    timestamp: str
    total_entities: int
    total_relations: int
    file_size_mb: float
    empty_tables: int
    duplicate_entities: int
    duplicate_relations: int
    missing_references: int
    data_integrity_score: float
    issues: List[str]
    warnings: List[str]
    recommendations: List[str]

@dataclass
class QualityThresholds:
    """质量阈值"""
    min_entities: int = 10
    min_relations: int = 10
    max_empty_tables_ratio: float = 0.3
    max_duplicate_ratio: float = 0.05
    min_integrity_score: float = 80.0
    max_file_size_mb: float = 1000.0

class DataQualityMonitor:
    """数据质量监控器"""

    def __init__(self):
        self.project_root = '/Users/xujian/Athena工作平台'
        self.monitoring_dirs = [
            '/Users/xujian/Athena工作平台/data/professional_knowledge_graphs',
            '/Users/xujian/Athena工作平台/data/merged_knowledge_graphs'
        ]
        self.metrics_history = defaultdict(list)
        self.thresholds = QualityThresholds()
        self.alert_threshold = QualityThresholds(
            min_entities=5,
            min_relations=5,
            max_empty_tables_ratio=0.5,
            max_duplicate_ratio=0.1,
            min_integrity_score=70.0,
            max_file_size_mb=500.0
        )

    def scan_all_knowledge_graphs(self) -> Dict[str, QualityMetrics]:
        """扫描所有知识图谱"""
        logger.info('🔍 数据质量监控系统启动')
        logger.info(str('=' * 50))

        all_metrics = {}

        for monitoring_dir in self.monitoring_dirs:
            if not Path(monitoring_dir).exists():
                continue

            logger.info(f"\n📁 扫描目录: {monitoring_dir}")

            for db_file in Path(monitoring_dir).glob('*.db'):
                kg_type = db_file.stem.replace('_rebuilt', '').replace('_merged', '')
                logger.info(f"   🔎 分析: {kg_type}")

                try:
                    metrics = self.analyze_knowledge_graph(db_file, kg_type)
                    all_metrics[kg_type] = metrics

                    # 检查是否需要告警
                    self.check_quality_alerts(metrics)

                    # 保存历史记录
                    self.metrics_history[kg_type].append(metrics)

                    logger.info(f"      📊 实体: {metrics.total_entities:,}, 关系: {metrics.total_relations:,}")
                    logger.info(f"      🏆 完整性评分: {metrics.data_integrity_score:.1f}/100")

                except Exception as e:
                    logger.error(f"分析 {kg_type} 失败: {e}")
                    logger.info(f"      ❌ 分析失败: {str(e)}")

        # 生成监控报告
        self.generate_monitoring_report(all_metrics)

        return all_metrics

    def analyze_knowledge_graph(self, db_path: Path, kg_type: str) -> QualityMetrics:
        """分析单个知识图谱质量"""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        timestamp = datetime.now().isoformat()
        file_size_mb = db_path.stat().st_size / (1024 * 1024)

        # 基础统计
        total_entities = 0
        total_relations = 0
        empty_tables = 0
        duplicate_entities = 0
        duplicate_relations = 0
        missing_references = 0
        issues = []
        warnings = []
        recommendations = []

        try:
            # 获取表列表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]

            # 分析每个表
            for table in tables:
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]

                if table == 'entities':
                    total_entities = count
                    # 检查重复实体
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) - COUNT(DISTINCT id) FROM {table}")
                            cursor.execute(f"SELECT COUNT(*) - COUNT(DISTINCT id) FROM {table}")
                    duplicate_entities = cursor.fetchone()[0]

                    # 检查引用完整性
                    if count > 0:
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE id IS NULL OR id = ''")
                                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE id IS NULL OR id = ''")
                        null_ids = cursor.fetchone()[0]
                        if null_ids > 0:
                            issues.append(f"{table}表有 {null_ids} 个空ID记录")

                elif table == 'relations':
                    total_relations = count
                    # 检查重复关系
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) - COUNT(DISTINCT id) FROM {table}")
                            cursor.execute(f"SELECT COUNT(*) - COUNT(DISTINCT id) FROM {table}")
                    duplicate_relations = cursor.fetchone()[0]

                    # 检查引用完整性
                    if total_entities > 0:
        # TODO: 检查SQL注入风险 - cursor.execute(f"""
                                cursor.execute(f"""
                            SELECT COUNT(*) FROM {table} r
                            LEFT JOIN entities e ON r.source_id = e.id
                            WHERE e.id IS NULL
                        """)
                        missing_source = cursor.fetchone()[0]

        # TODO: 检查SQL注入风险 - cursor.execute(f"""
                                cursor.execute(f"""
                            SELECT COUNT(*) FROM {table} r
                            LEFT JOIN entities e ON r.target_id = e.id
                            WHERE e.id IS NULL
                        """)
                        missing_target = cursor.fetchone()[0]

                        missing_references = missing_source + missing_target
                        if missing_references > 0:
                            issues.append(f"关系表有 {missing_references} 个无效引用")

                # 检查空表
                if count == 0:
                    empty_tables += 1

            # 计算完整性评分
            integrity_score = self.calculate_integrity_score(
                total_entities, total_relations, empty_tables,
                len(tables), duplicate_entities, duplicate_relations,
                missing_references, file_size_mb, issues
            )

            # 生成警告和建议
            self.generate_warnings_and_recommendations(
                total_entities, total_relations, empty_tables,
                len(tables), duplicate_entities, duplicate_relations,
                file_size_mb, integrity_score, issues, warnings, recommendations
            )

        except Exception as e:
            logger.error(f"分析 {kg_type} 时出错: {e}")
            issues.append(f"分析过程出错: {str(e)}")
            integrity_score = 0.0

        finally:
            conn.close()

        return QualityMetrics(
            kg_type=kg_type,
            timestamp=timestamp,
            total_entities=total_entities,
            total_relations=total_relations,
            file_size_mb=file_size_mb,
            empty_tables=empty_tables,
            duplicate_entities=duplicate_entities,
            duplicate_relations=duplicate_relations,
            missing_references=missing_references,
            data_integrity_score=integrity_score,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations
        )

    def calculate_integrity_score(self, entities: int, relations: int, empty_tables: int,
                                 total_tables: int, dup_entities: int, dup_relations: int,
                                 missing_refs: int, file_size_mb: float, issues: List[str]) -> float:
        """计算数据完整性评分"""
        score = 100.0

        # 基础数据评分 (40分)
        if entities < self.thresholds.min_entities:
            score -= 20
        if relations < self.thresholds.min_relations:
            score -= 20

        # 空表评分 (20分)
        empty_ratio = empty_tables / max(total_tables, 1)
        if empty_ratio > self.thresholds.max_empty_tables_ratio:
            score -= 20 * (empty_ratio / self.thresholds.max_empty_tables_ratio)

        # 重复数据评分 (20分)
        total_records = entities + relations
        duplicate_ratio = (dup_entities + dup_relations) / max(total_records, 1)
        if duplicate_ratio > self.thresholds.max_duplicate_ratio:
            score -= 20 * (duplicate_ratio / self.thresholds.max_duplicate_ratio)

        # 引用完整性评分 (10分)
        if missing_refs > 0:
            score -= min(10, missing_refs / 100)

        # 文件大小评分 (10分)
        if file_size_mb > self.thresholds.max_file_size_mb:
            score -= min(10, (file_size_mb / self.thresholds.max_file_size_mb - 1) * 10)

        # 问题扣分
        score -= min(20, len(issues) * 2)

        return max(0.0, score)

    def generate_warnings_and_recommendations(self, entities: int, relations: int,
                                              empty_tables: int, total_tables: int,
                                              dup_entities: int, dup_relations: int,
                                              file_size_mb: float, score: float,
                                              issues: List[str], warnings: List[str],
                                              recommendations: List[str]):
        """生成警告和建议"""
        # 生成警告
        if entities < self.alert_threshold.min_entities:
            warnings.append('实体数量过少，可能影响知识图谱的完整性')

        if relations < self.alert_threshold.min_relations:
            warnings.append('关系数量过少，知识图谱连接性不足')

        if empty_tables / max(total_tables, 1) > self.alert_threshold.max_empty_tables_ratio:
            warnings.append('空表比例过高，存在未使用的数据结构')

        if dup_entities > 0 or dup_relations > 0:
            warnings.append(f"存在重复数据: {dup_entities} 个重复实体, {dup_relations} 个重复关系")

        if file_size_mb > self.alert_threshold.max_file_size_mb:
            warnings.append(f"文件体积较大: {file_size_mb:.1f}MB，可能影响查询性能")

        # 生成建议
        if score < 50:
            recommendations.append('数据质量较差，建议进行数据重建或清理')
        elif score < 70:
            recommendations.append('数据质量一般，建议进行数据优化和补充')
        elif score < 90:
            recommendations.append('数据质量良好，建议定期维护和更新')
        else:
            recommendations.append('数据质量优秀，保持当前维护策略')

        if dup_entities > 0:
            recommendations.append('清理重复数据，提高数据唯一性')

        if file_size_mb > 500:
            recommendations.append('考虑数据压缩或分区存储以优化性能')

    def check_quality_alerts(self, metrics: QualityMetrics):
        """检查质量告警"""
        alert_level = 'info'
        message = f"{metrics.kg_type}: 质量评分 {metrics.data_integrity_score:.1f}"

        if metrics.data_integrity_score < self.alert_threshold.min_integrity_score:
            alert_level = 'critical'
            message += ' - 质量严重问题'
            logger.critical(f"🚨 {message}")
        elif metrics.data_integrity_score < 80:
            alert_level = 'warning'
            message += ' - 质量需要关注'
            logger.warning(f"⚠️ {message}")
        else:
            logger.info(f"✅ {message}")

        # 记录关键问题
        if metrics.issues:
            logger.error(f"🐛 {metrics.kg_type} 发现问题: {', '.join(metrics.issues)}")

    def generate_monitoring_report(self, all_metrics: Dict[str, QualityMetrics]):
        """生成监控报告"""
        report_file = '/Users/xujian/Athena工作平台/DATA_QUALITY_MONITORING_REPORT.md'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 数据质量监控报告\n\n")
            f.write(f"**监控时间**: {datetime.now().isoformat()}\n")
            f.write(f"**监控工程师**: Athena AI Assistant\n\n")
            f.write("---\n\n")

            f.write("## 📊 监控概览\n\n")
            f.write(f"- **监控图谱数量**: {len(all_metrics)}\n")

            # 统计质量分布
            high_quality = sum(1 for m in all_metrics.values() if m.data_integrity_score >= 90)
            medium_quality = sum(1 for m in all_metrics.values() if 70 <= m.data_integrity_score < 90)
            low_quality = sum(1 for m in all_metrics.values() if m.data_integrity_score < 70)

            f.write(f"- **高质量图谱**: {high_quality} 个 (≥90分)\n")
            f.write(f"- **中等质量图谱**: {medium_quality} 个 (70-89分)\n")
            f.write(f"- **低质量图谱**: {low_quality} 个 (<70分)\n")
            f.write(f"- **平均质量评分**: {sum(m.data_integrity_score for m in all_metrics.values()) / len(all_metrics):.1f}\n\n")

            f.write("## 📈 质量详情\n\n")

            for kg_type, metrics in sorted(all_metrics.items(), key=lambda x: x[1].data_integrity_score):
                status = '🟢' if metrics.data_integrity_score >= 90 else '🟡' if metrics.data_integrity_score >= 70 else '🔴'

                f.write(f"### {status} {kg_type}\n\n")
                f.write(f"**质量评分**: {metrics.data_integrity_score:.1f}/100\n")
                f.write(f"**实体数量**: {metrics.total_entities:,}\n")
                f.write(f"**关系数量**: {metrics.total_relations:,}\n")
                f.write(f"**文件大小**: {metrics.file_size_mb:.1f} MB\n")
                f.write(f"**空表数量**: {metrics.empty_tables}\n")
                f.write(f"**重复实体**: {metrics.duplicate_entities}\n")
                f.write(f"**重复关系**: {metrics.duplicate_relations}\n")
                f.write(f"**无效引用**: {metrics.missing_references}\n\n")

                if metrics.warnings:
                    f.write("**⚠️ 警告**:\n")
                    for warning in metrics.warnings:
                        f.write(f"- {warning}\n")
                    f.write("\n")

                if metrics.recommendations:
                    f.write("**💡 建议**:\n")
                    for rec in metrics.recommendations:
                        f.write(f"- {rec}\n")
                    f.write("\n")

                f.write("---\n\n")

            f.write("## 🔍 质量趋势分析\n\n")
            f.write("建议定期运行此监控系统以跟踪质量变化趋势。\n")

        logger.info(f"📄 监控报告已保存: {report_file}")

def main():
    """主函数"""
    monitor = DataQualityMonitor()

    logger.info('🔬 启动数据质量监控...')

    # 执行扫描
    metrics = monitor.scan_all_knowledge_graphs()

    logger.info(f"\n🎯 监控完成!")
    logger.info(f"   扫描图谱: {len(metrics)} 个")

    # 显示统计
    high_quality = sum(1 for m in metrics.values() if m.data_integrity_score >= 90)
    medium_quality = sum(1 for m in metrics.values() if 70 <= m.data_integrity_score < 90)
    low_quality = sum(1 for m in metrics.values() if m.data_integrity_score < 70)

    logger.info(f"   高质量: {high_quality} 个")
    logger.info(f"   中等质量: {medium_quality} 个")
    logger.info(f"   低质量: {low_quality} 个")

    avg_score = sum(m.data_integrity_score for m in metrics.values()) / len(metrics)
    logger.info(f"   平均评分: {avg_score:.1f}/100")

if __name__ == '__main__':
    main()