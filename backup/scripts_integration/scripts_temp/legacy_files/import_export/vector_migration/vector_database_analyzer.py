#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量数据库全面分析工具
Vector Database Comprehensive Analyzer

扫描和分析项目中所有向量库和向量文件
"""

import hashlib
import json
import logging
import os
import pickle
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/xujian/Athena工作平台/documentation/logs/vector_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VectorDatabaseAnalyzer:
    """向量数据库分析器"""

    def __init__(self):
        self.project_root = '/Users/xujian/Athena工作平台'
        self.vector_data = []
        self.duplicate_groups = []
        self.low_quality_files = []
        self.analysis_stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'duplicate_files': 0,
            'duplicate_size_mb': 0,
            'low_quality_files': 0,
            'low_quality_size_mb': 0,
            'vector_formats': {},
            'dimensions': {},
            'errors': []
        }

    def run_comprehensive_analysis(self):
        """运行全面的向量分析"""
        logger.info('🔍 向量数据库全面分析工具')
        logger.info(str('=' * 60))

        # 1. 扫描所有向量文件
        logger.info("\n1️⃣ 扫描向量文件...")
        self.scan_vector_files()

        # 2. 分析向量质量和重复性
        logger.info("\n2️⃣ 分析向量质量和重复性...")
        self.analyze_vector_quality()

        # 3. 检测重复数据
        logger.info("\n3️⃣ 检测重复数据...")
        self.detect_duplicates()

        # 4. 评估数据质量
        logger.info("\n4️⃣ 评估数据质量...")
        self.assess_data_quality()

        # 5. 生成分析报告
        logger.info("\n5️⃣ 生成分析报告...")
        self.generate_analysis_report()

        logger.info(f"\n✅ 向量分析完成!")
        logger.info(f"   总文件数: {self.analysis_stats['total_files']}")
        logger.info(f"   总大小: {self.analysis_stats['total_size_mb']:.1f} MB")
        logger.info(f"   重复文件: {self.analysis_stats['duplicate_files']}")
        logger.info(f"   低质量文件: {self.analysis_stats['low_quality_files']}")
        logger.info(f"   分析报告: /Users/xujian/Athena工作平台/VECTOR_ANALYSIS_REPORT.md")

        return True

    def scan_vector_files(self):
        """扫描所有向量文件"""
        vector_patterns = [
            '*.npy', '*.npz',      # NumPy arrays
            '*.pkl', '*.pickle',   # Pickle files
            '*vector*.json',       # JSON vector files
            '*embedding*.json',    # JSON embedding files
            '*vector*.db',         # SQLite vector databases
            '*embedding*.db',      # SQLite embedding databases
            'faiss.index',         # FAISS indexes
            '*.ivf', '*.pq',       # IVF and PQ files
            'vectors/',            # Vector directories
            'embeddings/',         # Embedding directories
            '*technical_vectors*', # Technical term vectors
            '*专利无效向量库*'      # Patent invalid vector library
        ]

        logger.info(f"   📁 扫描目录: {self.project_root}")

        for root, dirs, files in os.walk(self.project_root):
            # 跳过一些不相关的目录
            if any(skip in root.lower() for skip in ['.git', '__pycache__', 'node_modules', '.venv']):
                continue

            for file in files:
                file_path = Path(root) / file
                file_lower = file.lower()

                # 检查是否是向量相关文件
                is_vector_file = (
                    any(pattern.replace('*', '') in file_lower for pattern in vector_patterns) or
                    'vector' in file_lower or
                    'embedding' in file_lower or
                    '向量' in file or
                    file.endswith(('.npy', '.npz', '.pkl', '.pickle')) and file_path.stat().st_size > 1024
                )

                if is_vector_file:
                    self.analyze_vector_file(file_path)

    def analyze_vector_file(self, file_path: Path):
        """分析单个向量文件"""
        try:
            file_size = file_path.stat().st_size
            file_info = {
                'path': str(file_path),
                'name': file_path.name,
                'size_mb': file_size / (1024 * 1024),
                'format': self.detect_file_format(file_path),
                'relative_path': str(file_path).replace(self.project_root + '/', ''),
                'modified_time': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }

            # 尝试读取向量数据
            vector_info = self.extract_vector_info(file_path)
            file_info.update(vector_info)

            self.vector_data.append(file_info)
            self.analysis_stats['total_files'] += 1
            self.analysis_stats['total_size_mb'] += file_info['size_mb']

            # 统计格式
            fmt = file_info['format']
            self.analysis_stats['vector_formats'][fmt] = self.analysis_stats['vector_formats'].get(fmt, 0) + 1

            # 统计维度
            if 'dimensions' in vector_info:
                dim = vector_info['dimensions']
                self.analysis_stats['dimensions'][dim] = self.analysis_stats['dimensions'].get(dim, 0) + 1

        except Exception as e:
            error_msg = f"分析文件失败 {file_path}: {str(e)}"
            logger.error(error_msg)
            self.analysis_stats['errors'].append(error_msg)

    def detect_file_format(self, file_path: Path) -> str:
        """检测文件格式"""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()

        if suffix in ['.npy', '.npz']:
            return 'numpy'
        elif suffix in ['.pkl', '.pickle']:
            return 'pickle'
        elif suffix == '.json':
            return 'json'
        elif suffix == '.db':
            return 'sqlite'
        elif 'faiss' in name or suffix in ['.ivf', '.pq']:
            return 'faiss'
        elif 'vector' in name or 'embedding' in name:
            return 'vector'
        else:
            return 'unknown'

    def extract_vector_info(self, file_path: Path) -> Dict[str, Any]:
        """提取向量信息"""
        info = {}
        format_type = self.detect_file_format(file_path)

        try:
            if format_type == 'numpy':
                if file_path.suffix == '.npz':
                    data = np.load(file_path)
                    if isinstance(data, np.lib.npyio.NpzFile):
                        # 获取第一个数组的形状
                        first_key = list(data.keys())[0]
                        array = data[first_key]
                        info['dimensions'] = array.shape[-1] if len(array.shape) > 1 else array.shape[0]
                        info['vector_count'] = len(array)
                        info['data_type'] = str(array.dtype)
                else:
                    array = np.load(file_path)
                    info['dimensions'] = array.shape[-1] if len(array.shape) > 1 else array.shape[0]
                    info['vector_count'] = len(array)
                    info['data_type'] = str(array.dtype)

            elif format_type == 'pickle':
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                    if isinstance(data, np.ndarray):
                        info['dimensions'] = data.shape[-1] if len(data.shape) > 1 else data.shape[0]
                        info['vector_count'] = len(data)
                    elif isinstance(data, dict):
                        # 尝试找到向量数据
                        for key, value in data.items():
                            if isinstance(value, np.ndarray) and len(value.shape) >= 2:
                                info['dimensions'] = value.shape[-1]
                                info['vector_count'] = len(value)
                                break

            elif format_type == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_path.stat().st_size > 50 * 1024 * 1024:  # 大于50MB的JSON文件不解析
                        info['large_file'] = True
                    else:
                        data = json.load(f)
                        if isinstance(data, list) and len(data) > 0:
                            # 假设第一个元素包含向量信息
                            first_item = data[0]
                            if isinstance(first_item, dict):
                                for key, value in first_item.items():
                                    if isinstance(value, list) and len(value) > 10:
                                        info['dimensions'] = len(value)
                                        info['vector_count'] = len(data)
                                        break

            elif format_type == 'sqlite':
                try:
                    conn = sqlite3.connect(str(file_path))
                    cursor = conn.cursor()

                    # 检查表结构
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()

                    for table_name, in tables:
                        if 'vector' in table_name.lower() or 'embedding' in table_name.lower():
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            count = cursor.fetchone()[0]
                            if count > 0:
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                                row = cursor.fetchone()
                                for i, value in enumerate(row):
                                    if isinstance(value, bytes) and len(value) > 100:
                                        # 可能是向量数据
                                        try:
                                            vector = np.frombuffer(value, dtype=np.float32)
                                            if len(vector) > 10:  # 合理的向量维度
                                                info['dimensions'] = len(vector)
                                                info['vector_count'] = count
                                                break
                                        except:
                                            continue

                    conn.close()
                except:
                    pass

        except Exception as e:
            logger.debug(f"提取向量信息失败 {file_path}: {str(e)}")

        return info

    def analyze_vector_quality(self):
        """分析向量质量"""
        for file_info in self.vector_data:
            quality_score = self.calculate_quality_score(file_info)
            file_info['quality_score'] = quality_score

            if quality_score < 30:  # 低质量阈值
                self.low_quality_files.append(file_info)
                self.analysis_stats['low_quality_files'] += 1
                self.analysis_stats['low_quality_size_mb'] += file_info['size_mb']

    def calculate_quality_score(self, file_info: Dict[str, Any]) -> int:
        """计算质量分数 (0-100)"""
        score = 100

        # 文件大小检查
        size_mb = file_info['size_mb']
        if size_mb < 0.1:  # 小于100KB，可能不完整
            score -= 30
        elif size_mb > 1000:  # 大于1GB，可能有重复或低效存储
            score -= 20

        # 格式检查
        format_type = file_info['format']
        if format_type == 'unknown':
            score -= 40
        elif format_type == 'json':
            score -= 20  # JSON格式存储向量效率较低

        # 维度检查
        if 'dimensions' in file_info:
            dim = file_info['dimensions']
            if dim < 10 or dim > 2000:  # 异常维度
                score -= 25

        # 向量数量检查
        if 'vector_count' in file_info:
            count = file_info['vector_count']
            if count < 100:  # 向量太少
                score -= 15
            elif count > 10000000:  # 向量太多，可能有重复
                score -= 10

        # 文件名检查
        name = file_info['name'].lower()
        if any(x in name for x in ['temp', 'tmp', 'test', 'backup', 'old', 'duplicate']):
            score -= 25

        # 路径检查
        path = file_info['relative_path'].lower()
        if any(x in path for x in ['backup', 'temp', 'cache', 'old', 'deprecated']):
            score -= 20

        return max(0, score)

    def detect_duplicates(self):
        """检测重复数据"""
        # 按文件大小和格式分组
        size_groups = {}
        for file_info in self.vector_data:
            key = (file_info['size_mb'], file_info['format'])
            if key not in size_groups:
                size_groups[key] = []
            size_groups[key].append(file_info)

        # 检查可能的重复
        for (size, format_type), files in size_groups.items():
            if len(files) > 1 and size > 1:  # 大于1MB且有多個文件
                # 检查文件名相似性
                similar_groups = self.group_similar_files(files)
                for group in similar_groups:
                    if len(group) > 1:
                        self.duplicate_groups.append(group)
                        self.analysis_stats['duplicate_files'] += len(group) - 1
                        self.analysis_stats['duplicate_size_mb'] += size * (len(group) - 1)

    def group_similar_files(self, files: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """按相似性分组文件"""
        groups = []
        used = set()

        for i, file1 in enumerate(files):
            if i in used:
                continue

            group = [file1]
            used.add(i)

            for j, file2 in enumerate(files):
                if j in used or i == j:
                    continue

                # 检查文件名相似性
                if self.are_files_similar(file1, file2):
                    group.append(file2)
                    used.add(j)

            groups.append(group)

        return groups

    def are_files_similar(self, file1: Dict[str, Any], file2: Dict[str, Any]) -> bool:
        """检查两个文件是否相似"""
        name1 = file1['name'].lower()
        name2 = file2['name'].lower()

        # 检查文件名相似性
        common_parts = ['vector', 'embedding', 'embedding', '向量', '专利', 'patent', 'legal', 'law']

        for part in common_parts:
            if part in name1 and part in name2:
                return True

        # 检查路径相似性
        path1 = file1['relative_path'].lower()
        path2 = file2['relative_path'].lower()

        if path1.split('/')[:-1] == path2.split('/')[:-1]:  # 同一目录
            return True

        return False

    def assess_data_quality(self):
        """评估数据质量"""
        # 检查向量维度一致性
        dimensions_count = {}
        for file_info in self.vector_data:
            if 'dimensions' in file_info:
                dim = file_info['dimensions']
                dimensions_count[dim] = dimensions_count.get(dim, 0) + 1

        # 识别异常维度
        common_dims = sorted(dimensions_count.items(), key=lambda x: x[1], reverse=True)
        if len(common_dims) > 5:
            # 维度种类太多，可能有质量问题
            for dim, count in common_dims[5:]:
                for file_info in self.vector_data:
                    if file_info.get('dimensions') == dim and file_info.get('quality_score', 100) > 50:
                        file_info['quality_score'] -= 15
                        if file_info not in self.low_quality_files:
                            self.low_quality_files.append(file_info)
                            self.analysis_stats['low_quality_files'] += 1
                            self.analysis_stats['low_quality_size_mb'] += file_info['size_mb']

    def generate_analysis_report(self):
        """生成分析报告"""
        report_file = '/Users/xujian/Athena工作平台/VECTOR_ANALYSIS_REPORT.md'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 向量数据库分析报告\n\n")
            f.write(f"**分析时间**: {datetime.now().isoformat()}\n")
            f.write(f"**分析工程师**: Athena AI Assistant\n\n")
            f.write("---\n\n")

            f.write("## 📊 分析概览\n\n")
            f.write(f"- **总文件数**: {self.analysis_stats['total_files']}\n")
            f.write(f"- **总大小**: {self.analysis_stats['total_size_mb']:.1f} MB\n")
            f.write(f"- **重复文件**: {self.analysis_stats['duplicate_files']} 个\n")
            f.write(f"- **重复数据大小**: {self.analysis_stats['duplicate_size_mb']:.1f} MB\n")
            f.write(f"- **低质量文件**: {self.analysis_stats['low_quality_files']} 个\n")
            f.write(f"- **低质量数据大小**: {self.analysis_stats['low_quality_size_mb']:.1f} MB\n\n")

            # 文件格式统计
            f.write("## 📁 文件格式分布\n\n")
            for fmt, count in sorted(self.analysis_stats['vector_formats'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"- **{fmt}**: {count} 个文件\n")

            # 向量维度统计
            if self.analysis_stats['dimensions']:
                f.write("\n## 🎯 向量维度分布\n\n")
                for dim, count in sorted(self.analysis_stats['dimensions'].items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- **{dim}维**: {count} 个文件\n")

            # 大文件列表
            large_files = sorted(self.vector_data, key=lambda x: x['size_mb'], reverse=True)[:20]
            if large_files:
                f.write("\n## 📦 大文件列表 (前20个)\n\n")
                f.write("| 文件路径 | 大小 | 格式 | 向量数量 | 维度 | 质量分数 |\n")
                f.write("|----------|------|------|----------|------|----------|\n")

                for file_info in large_files:
                    path = file_info['relative_path']
                    size = f"{file_info['size_mb']:.1f} MB"
                    fmt = file_info['format']
                    count = file_info.get('vector_count', 'N/A')
                    dim = file_info.get('dimensions', 'N/A')
                    score = file_info.get('quality_score', 'N/A')

                    f.write(f"| {path} | {size} | {fmt} | {count} | {dim} | {score} |\n")

            # 重复文件
            if self.duplicate_groups:
                f.write("\n## 🔄 重复文件组\n\n")
                for i, group in enumerate(self.duplicate_groups[:10], 1):
                    f.write(f"### 重复组 {i}\n\n")
                    total_size = sum(f['size_mb'] for f in group)
                    f.write(f"总大小: {total_size:.1f} MB\n\n")

                    for file_info in group:
                        f.write(f"- `{file_info['relative_path']}` ({file_info['size_mb']:.1f} MB)\n")
                    f.write("\n")

            # 低质量文件
            if self.low_quality_files:
                f.write("\n## ⚠️ 低质量文件\n\n")
                f.write("| 文件路径 | 大小 | 格式 | 质量分数 | 问题 |\n")
                f.write("|----------|------|------|----------|------|\n")

                for file_info in sorted(self.low_quality_files, key=lambda x: x['quality_score'])[:20]:
                    path = file_info['relative_path']
                    size = f"{file_info['size_mb']:.1f} MB"
                    fmt = file_info['format']
                    score = file_info.get('quality_score', 0)

                    # 分析问题
                    issues = []
                    if file_info['size_mb'] < 0.1:
                        issues.append('文件过小')
                    if file_info['format'] == 'json':
                        issues.append('JSON格式效率低')
                    if 'temp' in path or 'tmp' in path:
                        issues.append('临时文件')
                    if 'backup' in path:
                        issues.append('备份文件')

                    issue_str = ', '.join(issues) if issues else '数据质量问题'

                    f.write(f"| {path} | {size} | {fmt} | {score} | {issue_str} |\n")

            # 优化建议
            f.write("\n## 💡 优化建议\n\n")

            total_redundant = self.analysis_stats['duplicate_size_mb'] + self.analysis_stats['low_quality_size_mb']

            if total_redundant > 100:
                f.write("### 🎯 立即优化 (高优先级)\n\n")
                f.write(f"1. **删除重复文件**: 可释放 {self.analysis_stats['duplicate_size_mb']:.1f} MB\n")
                f.write(f"2. **清理低质量文件**: 可释放 {self.analysis_stats['low_quality_size_mb']:.1f} MB\n")
                f.write(f"3. **总计可释放**: {total_redundant:.1f} MB\n\n")

            f.write("### 🔧 格式优化建议\n\n")

            format_counts = self.analysis_stats['vector_formats']
            if format_counts.get('json', 0) > 0:
                f.write("- **JSON格式优化**: 将JSON向量文件转换为NumPy或SQLite格式\n")

            if format_counts.get('pickle', 0) > 0:
                f.write("- **Pickle文件**: 考虑转换为更标准的NumPy格式\n")

            f.write("\n### 📚 存储优化建议\n\n")
            f.write("- **向量压缩**: 使用PCA或量化技术减少向量大小\n")
            f.write("- **索引优化**: 使用FAISS等高效的向量索引\n")
            f.write("- **分层存储**: 热数据使用快速存储，冷数据使用压缩存储\n\n")

            f.write("## 🚀 下一步行动\n\n")
            f.write("1. **创建清理脚本**: 自动删除重复和低质量文件\n")
            f.write("2. **格式转换**: 将低效格式转换为高效格式\n")
            f.write("3. **建立监控**: 防止未来产生重复数据\n")
            f.write("4. **定期维护**: 建立定期清理和优化机制\n")

        logger.info(f"\n📋 详细分析报告已生成: {report_file}")

def main():
    """主函数"""
    analyzer = VectorDatabaseAnalyzer()

    try:
        success = analyzer.run_comprehensive_analysis()

        if success:
            logger.info(f"\n🎉 向量数据库分析完成!")
            logger.info(f"发现重复和低质量数据的详细信息已保存到报告文件")
        else:
            logger.info(f"\n❌ 分析过程中遇到问题")

    except KeyboardInterrupt:
        logger.info(f"\n⚠️ 分析被用户中断")
    except Exception as e:
        logger.info(f"\n❌ 分析失败: {str(e)}")

if __name__ == '__main__':
    main()