#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业知识图谱质量评估器
Professional Knowledge Graph Quality Assessor

评估合并后的专业知识图谱质量，确定重建需求
"""

import json
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProfessionalKGQualityAssessor:
    """专业知识图谱质量评估器"""

    def __init__(self):
        self.project_root = '/Users/xujian/Athena工作平台'
        self.merged_kg_dir = '/Users/xujian/Athena工作平台/data/merged_knowledge_graphs'
        self.professional_types = [
            'legal', 'patent_judgment', 'patent_reconsideration',
            'technical', 'trademark', 'patent_invalid', 'patent_legal'
        ]
        self.assessment_results = {}
        self.rebuild_recommendations = {}

    def assess_all_professional_kgs(self) -> Dict[str, Any]:
        """评估所有专业知识图谱的质量"""
        logger.info('🔍 专业知识图谱质量评估')
        logger.info(str('=' * 50))

        # 检查合并后的专业图谱
        merged_files = list(Path(self.merged_kg_dir).glob('*.db'))

        logger.info(f"发现 {len(merged_files)} 个合并后的图谱文件")

        for file_path in merged_files:
            kg_type = self.identify_professional_type(file_path)
            if kg_type:
                logger.info(f"\n📊 评估 {kg_type} 知识图谱...")
                quality_score = self.assess_single_kg(file_path, kg_type)
                self.assessment_results[kg_type] = quality_score

        # 生成重建建议
        self.generate_rebuild_recommendations()

        return {
            'assessed_kgs': len(self.assessment_results),
            'results': self.assessment_results,
            'rebuild_recommendations': self.rebuild_recommendations
        }

    def identify_professional_type(self, file_path: Path) -> str:
        """识别专业知识图谱类型"""
        name = file_path.stem.lower()

        if 'legal' in name:
            return 'legal'
        elif 'patent_judgment' in name:
            return 'patent_judgment'
        elif 'patent_reconsideration' in name:
            return 'patent_reconsideration'
        elif 'technical' in name:
            return 'technical'
        elif 'trademark' in name:
            return 'trademark'
        elif 'patent_invalid' in name:
            return 'patent_invalid'
        elif 'patent_legal' in name:
            return 'patent_legal'
        elif 'athena_main' in name:
            return 'athena_main'  # 主图谱包含所有专业领域
        else:
            return 'unknown'

    def assess_single_kg(self, file_path: Path, kg_type: str) -> Dict[str, Any]:
        """评估单个知识图谱质量"""
        assessment = {
            'kg_type': kg_type,
            'file_path': str(file_path),
            'file_size': file_path.stat().st_size,
            'overall_score': 0,
            'data_completeness': 0,
            'structure_quality': 0,
            'domain_coverage': 0,
            'data_accuracy': 0,
            'issues': [],
            'strengths': [],
            'recommendations': []
        }

        try:
            conn = sqlite3.connect(str(file_path))
            cursor = conn.cursor()

            # 获取表结构
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]

            # 数据完整性评估 (30分)
            completeness = self.assess_data_completeness(cursor, tables, kg_type)
            assessment['data_completeness'] = completeness

            # 结构质量评估 (25分)
            structure = self.assess_structure_quality(cursor, tables, kg_type)
            assessment['structure_quality'] = structure

            # 领域覆盖度评估 (25分)
            coverage = self.assess_domain_coverage(cursor, tables, kg_type)
            assessment['domain_coverage'] = coverage

            # 数据准确性评估 (20分)
            accuracy = self.assess_data_accuracy(cursor, tables, kg_type)
            assessment['data_accuracy'] = accuracy

            # 计算总分
            assessment['overall_score'] = (
                completeness * 0.3 + structure * 0.25 +
                coverage * 0.25 + accuracy * 0.2
            )

            # 识别问题和优势
            self.identify_issues_and_strengths(assessment, cursor, tables)

            conn.close()

        except Exception as e:
            logger.error(f"评估 {file_path} 时出错: {e}")
            assessment['issues'].append(f"数据库访问错误: {str(e)}")
            assessment['overall_score'] = 0

        return assessment

    def assess_data_completeness(self, cursor: sqlite3.Cursor, tables: List[str], kg_type: str) -> float:
        """评估数据完整性"""
        score = 0
        max_score = 100

        # 基础表存在性 (30分)
        required_tables = self.get_required_tables(kg_type)
        existing_required = [t for t in required_tables if t in tables]
        score += (len(existing_required) / len(required_tables)) * 30

        # 数据记录数量 (40分)
        if 'entities' in tables:
            cursor.execute('SELECT COUNT(*) FROM entities')
            entity_count = cursor.fetchone()[0]
            if entity_count > 100000:
                score += 40
            elif entity_count > 10000:
                score += 30
            elif entity_count > 1000:
                score += 20
            elif entity_count > 100:
                score += 10

        # 关系完整性 (30分)
        if 'relations' in tables:
            cursor.execute('SELECT COUNT(*) FROM relations')
            relation_count = cursor.fetchone()[0]
            if relation_count > 50000:
                score += 30
            elif relation_count > 5000:
                score += 25
            elif relation_count > 500:
                score += 20
            elif relation_count > 50:
                score += 15
            elif relation_count > 0:
                score += 10

        return min(score, max_score)

    def assess_structure_quality(self, cursor: sqlite3.Cursor, tables: List[str], kg_type: str) -> float:
        """评估结构质量"""
        score = 0
        max_score = 100

        # 标准表结构 (30分)
        standard_tables = ['entities', 'relations', 'triples', 'nodes', 'edges']
        existing_standard = [t for t in standard_tables if t in tables]
        score += (len(existing_standard) / len(standard_tables)) * 30

        # 表字段完整性 (40分)
        for table in ['entities', 'relations']:
            if table in tables:
        # TODO: 检查SQL注入风险 - cursor.execute(f"PRAGMA table_info({table})")
                        cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                required_columns = self.get_required_columns(table, kg_type)
                existing_required = [c for c in required_columns if c in columns]
                score += (len(existing_required) / len(required_columns)) * 20

        # 索引存在性 (30分)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [idx[0] for idx in cursor.fetchall()]
        if len(indexes) > 0:
            score += min((len(indexes) / 5) * 30, 30)

        return min(score, max_score)

    def assess_domain_coverage(self, cursor: sqlite3.Cursor, tables: List[str], kg_type: str) -> float:
        """评估领域覆盖度"""
        score = 0
        max_score = 100

        # 根据不同领域类型评估
        if kg_type == 'legal':
            score = self.assess_legal_coverage(cursor, tables)
        elif kg_type == 'patent_judgment':
            score = self.assess_patent_judgment_coverage(cursor, tables)
        elif kg_type == 'patent_reconsideration':
            score = self.assess_patent_reconsideration_coverage(cursor, tables)
        elif kg_type == 'technical':
            score = self.assess_technical_coverage(cursor, tables)
        elif kg_type == 'trademark':
            score = self.assess_trademark_coverage(cursor, tables)
        elif kg_type == 'patent_invalid':
            score = self.assess_patent_invalid_coverage(cursor, tables)
        elif kg_type == 'patent_legal':
            score = self.assess_patent_legal_coverage(cursor, tables)
        else:
            # 通用评估
            score = self.assess_general_coverage(cursor, tables)

        return min(score, max_score)

    def assess_data_accuracy(self, cursor: sqlite3.Cursor, tables: List[str], kg_type: str) -> float:
        """评估数据准确性"""
        score = 80  # 基础分

        # 检查空值比例
        for table in ['entities', 'relations']:
            if table in tables:
                try:
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    total = cursor.fetchone()[0]

                    if total > 0:
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE id IS NULL OR id = ''")
                                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE id IS NULL OR id = ''")
                        null_ids = cursor.fetchone()[0]

                        if null_ids > 0:
                            score -= (null_ids / total) * 30
                except:
                    pass

        # 检查重复数据
        if 'entities' in tables:
            try:
                cursor.execute('SELECT COUNT(*) - COUNT(DISTINCT id) FROM entities')
                duplicates = cursor.fetchone()[0]
                if duplicates > 0:
                    score -= min(duplicates * 2, 20)
            except:
                pass

        return max(score, 0)

    def get_required_tables(self, kg_type: str) -> List[str]:
        """获取必需的表"""
        base_tables = ['entities', 'relations']

        type_specific = {
            'legal': ['legal_cases', 'legal_statutes'],
            'patent_judgment': ['patent_cases', 'judgment_documents'],
            'patent_reconsideration': ['reconsideration_cases', 'review_documents'],
            'technical': ['technical_terms', 'term_definitions'],
            'trademark': ['trademark_registrations', 'trademark_classes'],
            'patent_invalid': ['invalidity_cases', 'evidence_documents'],
            'patent_legal': ['patent_laws', 'legal_procedures']
        }

        return base_tables + type_specific.get(kg_type, [])

    def get_required_columns(self, table: str, kg_type: str) -> List[str]:
        """获取必需的字段"""
        if table == 'entities':
            return ['id', 'type', 'title', 'properties']
        elif table == 'relations':
            return ['id', 'source_id', 'target_id', 'type', 'properties']
        else:
            return ['id', 'properties']

    # 专项覆盖度评估方法
    def assess_legal_coverage(self, cursor: sqlite3.Cursor, tables: List[str]) -> float:
        """评估法律图谱覆盖度"""
        score = 0

        # 检查法律法规、案例等
        if 'legal_cases' in tables:
            cursor.execute('SELECT COUNT(DISTINCT type) FROM legal_cases')
            case_types = cursor.fetchone()[0]
            score += min(case_types * 10, 30)

        # 检查法条引用
        if 'entities' in tables:
            cursor.execute("SELECT COUNT(*) FROM entities WHERE type LIKE '%law%' OR type LIKE '%statute%'")
            law_count = cursor.fetchone()[0]
            if law_count > 1000:
                score += 40
            elif law_count > 100:
                score += 25
            elif law_count > 10:
                score += 15

        score += 30  # 基础分
        return min(score, 100)

    def assess_patent_judgment_coverage(self, cursor: sqlite3.Cursor, tables: List[str]) -> float:
        """评估专利判决图谱覆盖度"""
        score = 0

        if 'entities' in tables:
            cursor.execute("SELECT COUNT(*) FROM entities WHERE type LIKE '%patent%' OR type LIKE '%judgment%'")
            patent_count = cursor.fetchone()[0]
            if patent_count > 10000:
                score += 50
            elif patent_count > 1000:
                score += 35
            elif patent_count > 100:
                score += 20

        score += 30  # 基础分
        return min(score, 100)

    def assess_patent_reconsideration_coverage(self, cursor: sqlite3.Cursor, tables: List[str]) -> float:
        """评估专利复审图谱覆盖度"""
        score = 0

        if 'entities' in tables:
            cursor.execute("SELECT COUNT(*) FROM entities WHERE type LIKE '%reconsideration%' OR type LIKE '%review%'")
            review_count = cursor.fetchone()[0]
            if review_count > 5000:
                score += 50
            elif review_count > 500:
                score += 35
            elif review_count > 50:
                score += 20

        score += 30  # 基础分
        return min(score, 100)

    def assess_technical_coverage(self, cursor: sqlite3.Cursor, tables: List[str]) -> float:
        """评估技术术语图谱覆盖度"""
        score = 0

        if 'entities' in tables:
            cursor.execute("SELECT COUNT(*) FROM entities WHERE type LIKE '%technical%' OR type LIKE '%term%'")
            term_count = cursor.fetchone()[0]
            if term_count > 50000:
                score += 50
            elif term_count > 5000:
                score += 35
            elif term_count > 500:
                score += 20

        score += 30  # 基础分
        return min(score, 100)

    def assess_trademark_coverage(self, cursor: sqlite3.Cursor, tables: List[str]) -> float:
        """评估商标图谱覆盖度"""
        score = 0

        if 'entities' in tables:
            cursor.execute("SELECT COUNT(*) FROM entities WHERE type LIKE '%trademark%' OR type LIKE '%brand%'")
            trademark_count = cursor.fetchone()[0]
            if trademark_count > 1000:
                score += 50
            elif trademark_count > 100:
                score += 35
            elif trademark_count > 10:
                score += 20

        score += 30  # 基础分
        return min(score, 100)

    def assess_patent_invalid_coverage(self, cursor: sqlite3.Cursor, tables: List[str]) -> float:
        """评估专利无效图谱覆盖度"""
        return 60  # 临时返回基础分

    def assess_patent_legal_coverage(self, cursor: sqlite3.Cursor, tables: List[str]) -> float:
        """评估专利法律图谱覆盖度"""
        return 60  # 临时返回基础分

    def assess_general_coverage(self, cursor: sqlite3.Cursor, tables: List[str]) -> float:
        """通用覆盖度评估"""
        score = 60

        if 'entities' in tables:
            cursor.execute('SELECT COUNT(*) FROM entities')
            entity_count = cursor.fetchone()[0]
            if entity_count > 1000:
                score += 20
            elif entity_count > 100:
                score += 10

        return min(score, 100)

    def identify_issues_and_strengths(self, assessment: Dict[str, Any], cursor: sqlite3.Cursor, tables: List[str]):
        """识别问题和优势"""
        # 识别问题
        if assessment['data_completeness'] < 50:
            assessment['issues'].append('数据完整性不足，缺少重要表或记录')

        if assessment['structure_quality'] < 60:
            assessment['issues'].append('结构质量较差，缺少标准表结构')

        if assessment['domain_coverage'] < 50:
            assessment['issues'].append('领域覆盖度不足，数据范围有限')

        if assessment['data_accuracy'] < 70:
            assessment['issues'].append('数据准确性问题，存在空值或重复')

        # 识别优势
        if assessment['data_completeness'] > 80:
            assessment['strengths'].append('数据完整性优秀')

        if assessment['structure_quality'] > 80:
            assessment['strengths'].append('结构设计合理')

        if assessment['domain_coverage'] > 80:
            assessment['strengths'].append('领域覆盖全面')

        if assessment['data_accuracy'] > 90:
            assessment['strengths'].append('数据质量高，准确性好')

    def generate_rebuild_recommendations(self):
        """生成重建建议"""
        logger.info(f"\n📋 生成重建建议...")

        for kg_type, assessment in self.assessment_results.items():
            score = assessment['overall_score']

            if score < 60:
                self.rebuild_recommendations[kg_type] = {
                    'need_rebuild': True,
                    'priority': 'high',
                    'reason': f"质量评分过低 ({score:.1f}/100)，需要重新构建",
                    'assessment': assessment
                }
            elif score < 75:
                self.rebuild_recommendations[kg_type] = {
                    'need_rebuild': False,
                    'priority': 'medium',
                    'reason': f"质量一般 ({score:.1f}/100)，建议优化补充",
                    'assessment': assessment
                }
            else:
                self.rebuild_recommendations[kg_type] = {
                    'need_rebuild': False,
                    'priority': 'low',
                    'reason': f"质量良好 ({score:.1f}/100)，可保持现状",
                    'assessment': assessment
                }

    def generate_assessment_report(self) -> str:
        """生成评估报告"""
        report_file = '/Users/xujian/Athena工作平台/PROFESSIONAL_KG_ASSESSMENT_REPORT.md'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 专业知识图谱质量评估报告\n\n")
            f.write(f"**评估时间**: {datetime.now().isoformat()}\n")
            f.write(f"**评估工程师**: Athena AI Assistant\n\n")
            f.write("---\n\n")

            f.write("## 📊 评估概览\n\n")
            f.write(f"- **评估图谱数量**: {len(self.assessment_results)}\n")
            f.write(f"- **需要重建的图谱**: {sum(1 for r in self.rebuild_recommendations.values() if r['need_rebuild'])}\n")
            f.write(f"- **建议优化的图谱**: {sum(1 for r in self.rebuild_recommendations.values() if r['priority'] == 'medium')}\n")
            f.write(f"- **质量良好的图谱**: {sum(1 for r in self.rebuild_recommendations.values() if r['priority'] == 'low')}\n\n")

            f.write("## 📈 各图谱评估结果\n\n")

            for kg_type, assessment in self.assessment_results.items():
                recommendation = self.rebuild_recommendations[kg_type]

                f.write(f"### {kg_type.upper()}\n\n")
                f.write(f"**总体评分**: {assessment['overall_score']:.1f}/100\n")
                f.write(f"**数据完整性**: {assessment['data_completeness']:.1f}/100\n")
                f.write(f"**结构质量**: {assessment['structure_quality']:.1f}/100\n")
                f.write(f"**领域覆盖度**: {assessment['domain_coverage']:.1f}/100\n")
                f.write(f"**数据准确性**: {assessment['data_accuracy']:.1f}/100\n\n")

                f.write(f"**处理建议**: {recommendation['reason']}\n\n")

                if assessment['strengths']:
                    f.write("**优势**:\n")
                    for strength in assessment['strengths']:
                        f.write(f"- ✅ {strength}\n")
                    f.write("\n")

                if assessment['issues']:
                    f.write("**问题**:\n")
                    for issue in assessment['issues']:
                        f.write(f"- ⚠️ {issue}\n")
                    f.write("\n")

                f.write("---\n\n")

            f.write("## 🚀 重建计划\n\n")

            high_priority = [kg for kg, rec in self.rebuild_recommendations.items()
                           if rec['priority'] == 'high' and rec['need_rebuild']]

            if high_priority:
                f.write("### 高优先级重建图谱\n\n")
                for kg in high_priority:
                    rec = self.rebuild_recommendations[kg]
                    f.write(f"- **{kg}**: {rec['reason']}\n")
                f.write("\n")

            medium_priority = [kg for kg, rec in self.rebuild_recommendations.items()
                             if rec['priority'] == 'medium']

            if medium_priority:
                f.write("### 中优先级优化图谱\n\n")
                for kg in medium_priority:
                    rec = self.rebuild_recommendations[kg]
                    f.write(f"- **{kg}**: {rec['reason']}\n")
                f.write("\n")

            f.write("## 💡 后续建议\n\n")
            f.write("1. **优先重建**: 按优先级重建质量较差的专业图谱\n")
            f.write("2. **数据补充**: 为中等质量图谱补充缺失的数据\n")
            f.write("3. **持续监控**: 建立数据质量监控机制\n")
            f.write("4. **定期更新**: 制定定期数据更新计划\n\n")

        return report_file

def main():
    """主函数"""
    assessor = ProfessionalKGQualityAssessor()

    logger.info('🔬 专业知识图谱质量评估器')
    logger.info(str('=' * 50))

    # 执行评估
    results = assessor.assess_all_professional_kgs()

    # 显示结果
    logger.info(f"\n📊 评估结果概览:")
    logger.info(f"   评估图谱: {results['assessed_kgs']} 个")
    logger.info(f"   需要重建: {sum(1 for r in results['rebuild_recommendations'].values() if r['need_rebuild'])} 个")

    for kg_type, rec in results['rebuild_recommendations'].items():
        status = '🔴 需要重建' if rec['need_rebuild'] else '🟡 建议优化' if rec['priority'] == 'medium' else '🟢 质量良好'
        logger.info(f"   {kg_type}: {status} ({rec['assessment']['overall_score']:.1f}/100)")

    # 生成报告
    logger.info(f"\n📄 生成评估报告...")
    report_file = assessor.generate_assessment_report()
    logger.info(f"✅ 评估报告已保存: {report_file}")

    logger.info(f"\n🎉 专业图谱质量评估完成!")

if __name__ == '__main__':
    main()