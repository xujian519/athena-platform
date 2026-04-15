#!/usr/bin/env python3

"""
Athena工作平台 - 数据管理工具
Data Management Tool for Athena Work Platform

功能:
- 数据目录分析
- 大文件查找和管理
- 重复数据检测
- 存储空间优化建议
- 数据备份和归档
"""

import argparse
import csv
import hashlib
import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import humanize
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """文件信息"""

    path: Path
    size: int
    modified: datetime
    md5: str = ''
    file_type: str = ''

    @property
    def size_human(self) -> str:
        return humanize.naturalsize(self.size)


@dataclass
class DataStats:
    """数据统计"""

    total_files: int = 0
    total_size: int = 0
    file_types: dict[str, int] = field(default_factory=dict)
    large_files: list[FileInfo] = field(default_factory=list)
    duplicate_files: dict[str, list[FileInfo]] = field(default_factory=dict)


class DataManager:
    """数据管理器"""

    def __init__(self, data_root: Path):
        self.data_root = data_root
        self.stats = DataStats()
        self.exclude_patterns = {'.DS_Store', 'Thumbs.db', '*.tmp', '*.temp'}
        self.default_neo4j_import = (
            self.data_root / 'knowledge_graph_neo4j' / 'raw_data' / 'neo4j_import'
        )

    def scan_directory(self, min_size_mb: int = 100) -> DataStats:
        """扫描数据目录"""
        logger.info(f"🔍 扫描数据目录: {self.data_root}")

        large_files = []
        file_types = {}
        total_size = 0
        file_count = 0

        # 遍历所有文件
        for file_path in self.data_root.rglob('*'):
            if file_path.is_file():
                # 跳过系统文件
                if any(file_path.match(pattern) for pattern in self.exclude_patterns):
                    continue

                try:
                    size = file_path.stat().st_size
                    modified = datetime.fromtimestamp(file_path.stat().st_mtime)

                    # 文件类型统计
                    ext = file_path.suffix.lower() or 'no_extension'
                    file_types[ext] = file_types.get(ext, 0) + 1

                    total_size += size
                    file_count += 1

                    # 大文件记录
                    if size >= min_size_mb * 1024 * 1024:
                        file_info = FileInfo(
                            path=file_path, size=size, modified=modified, file_type=ext
                        )
                        large_files.append(file_info)

                except OSError as e:
                    logger.info(f"⚠️ 无法访问文件 {file_path}: {e}")

        # 排序大文件
        large_files.sort(key=lambda x: x.size, reverse=True)

        # 更新统计
        self.stats.total_files = file_count
        self.stats.total_size = total_size
        self.stats.file_types = file_types
        self.stats.large_files = large_files[:50]  # 只保留前50个大文件

        return self.stats

    def find_duplicates(self) -> dict[str, list[FileInfo]]:
        """查找重复文件"""
        logger.info('🔍 查找重复文件...')

        file_hashes = {}

        for file_path in self.data_root.rglob('*'):
            if file_path.is_file() and file_path.stat().st_size > 0:
                # 计算文件哈希（仅对前10KB用于快速检测）
                try:
                    with open(file_path, 'rb') as f:
                        # 只读取前10KB计算快速哈希
                        sample = f.read(10240)
                        quick_hash = hashlib.md5(sample, usedforsecurity=False).hexdigest()

                    if quick_hash not in file_hashes:
                        file_hashes[quick_hash] = []
                    file_hashes[quick_hash].append(file_path)
                except OSError:
                    continue

        # 找出真正的重复文件
        duplicates = {}
        for files in file_hashes.values():
            if len(files) > 1:
                # 对可能重复的文件进行完整哈希计算
                full_hashes = {}
                for file_path in files:
                    try:
                        with open(file_path, 'rb') as f:
                            full_hash = hashlib.md5(f.read(), usedforsecurity=False).hexdigest()
                        if full_hash not in full_hashes:
                            full_hashes[full_hash] = []
                        full_hashes[full_hash].append(file_path)
                    except OSError:
                        continue

                # 添加真正的重复文件
                for hash_val, dup_files in full_hashes.items():
                    if len(dup_files) > 1:
                        duplicates[hash_val] = [
                            FileInfo(
                                path=f,
                                size=f.stat().st_size,
                                modified=datetime.fromtimestamp(f.stat().st_mtime),
                            )
                            for f in dup_files
                        ]

        self.stats.duplicate_files = duplicates
        return duplicates

    def analyze_storage(self) -> dict[str, Any]:
        """分析存储使用情况"""
        logger.info('📊 分析存储使用情况...')

        # 目录大小统计
        dir_sizes = {}
        for item in self.data_root.iterdir():
            if item.is_dir():
                size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                dir_sizes[item.name] = size

        # 排序
        sorted_dirs = sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True)

        return {
            'total_size': self.stats.total_size,
            'total_files': self.stats.total_files,
            'directory_sizes': sorted_dirs[:20],  # 前20个目录
            'file_types': dict(
                sorted(self.stats.file_types.items(), key=lambda x: x[1], reverse=True)
            ),
        }

    def generate_report(self) -> str:
        """生成数据报告"""
        report_lines = [
            '# Athena工作平台 - 数据分析报告',
            f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**数据目录**: {self.data_root}",
            '',
            '## 📊 总体统计',
            f"- **总文件数**: {self.stats.total_files:,}",
            f"- **总大小**: {humanize.naturalsize(self.stats.total_size)}",
            f"- **平均文件大小**: {humanize.naturalsize(self.stats.total_size // max(self.stats.total_files, 1))}",
            '',
        ]

        # 目录大小分析
        analysis = self.analyze_storage()
        report_lines.extend(['## 📁 目录大小排名 (前10)', ''])

        for dir_name, size in analysis['directory_sizes'][:10]:
            percentage = (size / self.stats.total_size) * 100
            report_lines.append(
                f"- **{dir_name}**: {humanize.naturalsize(size)} ({percentage:.1f}%)"
            )

        # 大文件列表
        if self.stats.large_files:
            report_lines.extend(['', '## 🗄️ 大文件列表 (>100MB)', ''])
            for file_info in self.stats.large_files[:20]:
                relative_path = file_info.path.relative_to(self.data_root)
                report_lines.append(
                    f"- **{relative_path}**: {file_info.size_human} "
                    f"({file_info.modified.strftime('%Y-%m-%d')})"
                )

        # 重复文件
        if self.stats.duplicate_files:
            report_lines.extend(['', '## 🔄 重复文件', ''])
            for _hash_val, files in self.stats.duplicate_files.items():
                total_size = sum(f.size for f in files)
                report_lines.append(
                    f"\n### 重复组 (总计: {humanize.naturalsize(total_size)})"
                )
                for file_info in files:
                    relative_path = file_info.path.relative_to(self.data_root)
                    report_lines.append(f"- {relative_path} ({file_info.size_human})")

        # 文件类型统计
        report_lines.extend(['', '## 📋 文件类型统计', ''])
        for ext, count in list(analysis['file_types'].items())[:15]:
            report_lines.append(f"- **{ext or '无扩展名'}**: {count} 个文件")

        # 优化建议
        report_lines.extend(
            [
                '',
                '## 💡 优化建议',
                '',
                '### 1. 立即执行',
                '- 删除系统临时文件 (.DS_Store, Thumbs.db)',
                '- 清理空目录',
                '- 压缩不常用的JSON文件',
                '',
                '### 2. 近期优化',
                '- 合并重复的向量数据文件',
                '- 将大文件压缩存储',
                '- 建立数据分层存储机制',
                '',
                '### 3. 长期规划',
                '- 实施数据生命周期管理',
                '- 建立自动归档机制',
                '- 考虑云存储冷数据',
                '',
                '---',
                f"*报告生成时间: {datetime.now()}*",
            ]
        )

        return "\n".join(report_lines)

    def clean_temp_files(self) -> int:
        """清理临时文件"""
        logger.info('🧹 清理临时文件...')

        cleaned_count = 0
        cleaned_size = 0

        for file_path in self.data_root.rglob('*'):
            if file_path.is_file():
                # 检查是否是临时文件
                if (
                    file_path.name.startswith('.')
                    or file_path.suffix in ['.tmp', '.temp', '.swp', '.bak']
                    or file_path.name in ['.DS_Store', 'Thumbs.db']
                ):

                    try:
                        size = file_path.stat().st_size
                        file_path.unlink()
                        cleaned_count += 1
                        cleaned_size += size
                        logger.info(f"  删除: {file_path.relative_to(self.data_root)}")
                    except OSError as e:
                        logger.info(f"  无法删除 {file_path}: {e}")

        if cleaned_count > 0:
            print(
                f"\n✅ 清理完成: 删除 {cleaned_count} 个文件, 释放 {humanize.naturalsize(cleaned_size)}"
            )
        else:
            logger.info("\n✅ 没有发现需要清理的临时文件")

        return cleaned_count

    def archive_old_files(self, days: int = 30, dry_run: bool = True):
        """归档旧文件"""
        logger.info(f"📦 归档 {days} 天前的文件...")

        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        archive_dir = (
            self.data_root / 'archive' / f"before_{datetime.now().strftime('%Y%m%d')}"
        )

        old_files = []

        for file_path in self.data_root.rglob('*'):
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff_date:
                    # 排除重要文件
                    if not any(part.startswith('.') for part in file_path.parts):
                        old_files.append(file_path)

        if old_files:
            logger.info(f"\n发现 {len(old_files)} 个文件可以归档")

            if not dry_run:
                archive_dir.mkdir(parents=True, exist_ok=True)
                for file_path in old_files:
                    try:
                        relative_path = file_path.relative_to(self.data_root)
                        dest_path = archive_dir / relative_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(file_path), str(dest_path))
                    except OSError as e:
                        logger.info(f"  无法移动 {file_path}: {e}")

                logger.info(f"✅ 归档完成: 文件已移动到 {archive_dir}")
            else:
                logger.info('🔍 这是一个预览模式，使用 --execute 来实际执行归档')
        else:
            logger.info("\n✅ 没有发现需要归档的文件")

    def unify_patent_kg(
        self, source_dirs: list[Path], output_dir: Path
    ) -> dict[str, int]:
        merged_patents = {}
        seen_patent_numbers = {}
        relations = set()
        for src in source_dirs:
            patents_csv = src / 'patents.csv'
            relations_csv = src / 'relations.csv'
            if patents_csv.exists():
                with open(patents_csv, encoding='utf-8') as f:
                    f.readline()
                    for line in f:
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) < 8:
                            continue
                        pid = parts[0]
                        source_file = parts[1]
                        file_name = parts[2]
                        try:
                            file_size = int(parts[3])
                        except ValueError:
                            file_size = 0
                        processed_time = parts[4]
                        patent_number = parts[5]
                        ptype = parts[6] or 'unknown'
                        if pid in merged_patents:
                            prev = merged_patents[pid]
                            prev_size = prev.get('file_size', 0)
                            prev_time = prev.get('processed_time', '')
                            choose_new = False
                            if file_size > prev_size:
                                choose_new = True
                            elif processed_time and processed_time > prev_time:
                                choose_new = True
                            if choose_new:
                                merged_patents[pid] = {
                                    'id': pid,
                                    'source_file': source_file,
                                    'file_name': file_name,
                                    'file_size': file_size,
                                    'processed_time': processed_time,
                                    'patent_number': patent_number,
                                    'type': ptype,
                                }
                        else:
                            merged_patents[pid] = {
                                'id': pid,
                                'source_file': source_file,
                                'file_name': file_name,
                                'file_size': file_size,
                                'processed_time': processed_time,
                                'patent_number': patent_number,
                                'type': ptype,
                            }
                        if patent_number:
                            if patent_number in seen_patent_numbers:
                                prev_id = seen_patent_numbers[patent_number]
                                if prev_id != pid:
                                    pass
                            else:
                                seen_patent_numbers[patent_number] = pid
            if relations_csv.exists():
                with open(relations_csv, encoding='utf-8') as f:
                    f.readline()
                    for line in f:
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) < 4:
                            continue
                        start_id = parts[0]
                        rel_type = parts[1]
                        end_id = parts[2]
                        end_type = parts[3]
                        if start_id in merged_patents:
                            relations.add((start_id, rel_type, end_id, end_type))
            batch_jsons = list(src.glob('batch_*.json'))
            for bf in batch_jsons:
                try:
                    with open(bf, encoding='utf-8') as jf:
                        data = json.load(jf)
                    for patent in data.get('patents', []):
                        pid = patent.get('id')
                        if not pid:
                            continue
                        source_file = patent.get('source_file', '')
                        file_name = patent.get('file_name', '')
                        file_size = int(patent.get('file_size', 0) or 0)
                        processed_time = patent.get('processed_time', '')
                        patent_number = patent.get('patent_number', '')
                        ptype = patent.get('type', 'unknown') or 'unknown'
                        if pid in merged_patents:
                            prev = merged_patents[pid]
                            prev_size = prev.get('file_size', 0)
                            prev_time = prev.get('processed_time', '')
                            choose_new = False
                            if file_size > prev_size:
                                choose_new = True
                            elif processed_time and processed_time > prev_time:
                                choose_new = True
                            if choose_new:
                                merged_patents[pid] = {
                                    'id': pid,
                                    'source_file': source_file,
                                    'file_name': file_name,
                                    'file_size': file_size,
                                    'processed_time': processed_time,
                                    'patent_number': patent_number,
                                    'type': ptype,
                                }
                        else:
                            merged_patents[pid] = {
                                'id': pid,
                                'source_file': source_file,
                                'file_name': file_name,
                                'file_size': file_size,
                                'processed_time': processed_time,
                                'patent_number': patent_number,
                                'type': ptype,
                            }
                        if patent_number:
                            if patent_number in seen_patent_numbers:
                                prev_id = seen_patent_numbers[patent_number]
                                if prev_id != pid:
                                    pass
                            else:
                                seen_patent_numbers[patent_number] = pid
                    for triple in data.get('all_triples', []):
                        subject = triple.get('subject')
                        predicate = triple.get('predicate')
                        obj = triple.get('object')
                        if subject and predicate and obj and subject in merged_patents:
                            if predicate == 'has_type':
                                relations.add(
                                    (subject, 'HAS_TYPE', f"TYPE_{obj}")
                                )
                            elif predicate == 'from_source':
                                relations.add(
                                    (
                                        subject,
                                        'FROM_SOURCE',
                                        f"SOURCE_{hash(obj)}",
                                        'Source',
                                    )
                                )
                            elif predicate == 'patent_number':
                                pass
                except Exception:
                    continue
        output_dir.mkdir(parents=True, exist_ok=True)
        patents_out = output_dir / 'patents_unified.csv'
        relations_out = output_dir / 'relations_unified.csv'
        with open(patents_out, 'w', encoding='utf-8') as f:
            f.write(
                "id,source_file,file_name,file_size,processed_time,patent_number,type\n"
            )
            for p in merged_patents.values():
                f.write(
                    f"{p['id']},{p['source_file']},{p['file_name']},{p['file_size']},{p['processed_time']},{p['patent_number']},{p['type']}\n"
                )
        with open(relations_out, 'w', encoding='utf-8') as f:
            f.write("start_id,relationship_type,end_id,end_type\n")
            for r in relations:
                f.write(f"{r[0]},{r[1]},{r[2]},{r[3]}\n")
        return {'patents': len(merged_patents), 'relations': len(relations)}

    def generate_patent_kg_import_cypher(self, unified_dir: Path) -> Path:
        cypher_path = unified_dir / 'patent_kg_unified_import.cypher'
        patents_csv = 'file:///patents_unified.csv'
        relations_csv = 'file:///relations_unified.csv'
        lines = []
        lines.append(
            'CREATE CONSTRAINT IF NOT EXISTS FOR (p:Patent) REQUIRE p.id IS UNIQUE;'
        )
        lines.append(
            "LOAD CSV WITH HEADERS FROM '"
            + patents_csv
            + "' AS row MERGE (p:Patent {id: row.id}) SET p.source_file=row.source_file, p.file_name=row.file_name, p.file_size=toInteger(row.file_size), p.processed_time=datetime(row.processed_time), p.patent_number=row.patent_number, p.type=row.type;"
        )
        lines.append(
            "LOAD CSV WITH HEADERS FROM '"
            + relations_csv
            + "' AS row MATCH (p:Patent {id: row.start_id}) CALL apoc.merge.node([row.end_type], {id: row.end_id}) YIELD node CALL apoc.create.relationship(p, row.relationship_type, {}, node) YIELD rel RETURN count(rel);"
        )
        with open(cypher_path, 'w', encoding='utf-8') as f:
            for l in lines:
                f.write(l + "\n")
        return cypher_path

    def import_unified_patent_kg_to_neo4j(
        self, unified_dir: Path, uri: str, user: str, password: str
    ) -> dict[str, int]:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        patents_file = unified_dir / 'patents_unified.csv'
        relations_file = unified_dir / 'relations_unified.csv'
        patents_rows = []
        relations_has_type = []
        relations_from_source = []
        with open(patents_file, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                patents_rows.append(
                    {
                        'id': row['id'],
                        'source_file': row['source_file'],
                        'file_name': row['file_name'],
                        'file_size': int(row['file_size'] or 0),
                        'processed_time': row['processed_time'],
                        'patent_number': row['patent_number'],
                        'type': row['type'],
                    }
                )
        with open(relations_file, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['relationship_type'] == 'HAS_TYPE':
                    end_id = row['end_id']
                    name = end_id.replace('TYPE_', '')
                    relations_has_type.append(
                        {'start_id': row['start_id'], 'name': name}
                    )
                elif row['relationship_type'] == 'FROM_SOURCE':
                    relations_from_source.append(
                        {'start_id': row['start_id'], 'end_id': row['end_id']}
                    )
        with driver.session() as session:
            session.run(
                'CREATE CONSTRAINT patent_id_unique IF NOT EXISTS FOR (p:Patent) REQUIRE p.id IS UNIQUE'
            )
            if patents_rows:
                session.run(
                    """
                    UNWIND $rows AS row
                    MERGE (p:Patent {id: row.id})
                    SET p.source_file = row.source_file,
                        p.file_name = row.file_name,
                        p.file_size = row.file_size,
                        p.processed_time = row.processed_time,
                        p.patent_number = row.patent_number,
                        p.type = row.type
                    """,
                    rows=patents_rows,
                )
            if relations_has_type:
                session.run(
                    """
                    UNWIND $rels AS row
                    MATCH (p:Patent {id: row.start_id})
                    MERGE (t:Type {name: row.name})
                    MERGE (p)-[:HAS_TYPE]->(t)
                    """,
                    rels=relations_has_type,
                )
            if relations_from_source:
                session.run(
                    """
                    UNWIND $rels AS row
                    MATCH (p:Patent {id: row.start_id})
                    MERGE (s:Source {id: row.end_id})
                    MERGE (p)-[:FROM_SOURCE]->(s)
                    """,
                    rels=relations_from_source,
                )
            count_patents = session.run(
                'MATCH (p:Patent) RETURN count(p) AS c'
            ).single()['c']
            count_relations = session.run(
                'MATCH ()-[r]->() RETURN count(r) AS c'
            ).single()['c']
        driver.close()
        return {'patents': count_patents, 'relations': count_relations}


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(description='Athena数据管理工具')
    parser.add_argument('--data-dir', default='data', help='数据目录路径')
    parser.add_argument('--min-size', type=int, default=100, help='大文件最小大小(MB)')
    parser.add_argument('--scan', action='store_true', help='扫描数据目录')
    parser.add_argument('--duplicates', action='store_true', help='查找重复文件')
    parser.add_argument('--report', action='store_true', help='生成分析报告')
    parser.add_argument('--clean', action='store_true', help='清理临时文件')
    parser.add_argument('--archive', type=int, metavar='DAYS', help='归档N天前的文件')
    parser.add_argument('--execute', action='store_true', help='执行归档操作')
    parser.add_argument(
        '--unify-patent-kg', action='store_true', help='合并并去重专利知识图谱CSV'
    )
    parser.add_argument(
        '--kg-dirs',
        nargs='*',
        help='知识图谱源目录列表，默认使用data目录中的neo4j_import',
    )
    parser.add_argument(
        '--kg-output', help='统一CSV输出目录，默认processed_data/unified_patent_kg'
    )
    parser.add_argument(
        '--import-unified-to-neo4j', action='store_true', help='将统一CSV导入Neo4j'
    )
    parser.add_argument('--neo4j-uri', default='bolt://localhost:7687')
    parser.add_argument('--neo4j-user', default='neo4j')
    parser.add_argument('--neo4j-password', default='password')
    parser.add_argument(
        '--delete-raw-json', action='store_true', help='导入成功后删除原始批次JSON'
    )
    parser.add_argument(
        '--json-dirs', nargs='*', help='批次JSON目录列表，默认 data/patent_kg_superfast'
    )

    args = parser.parse_args()

    # 创建数据管理器
    data_manager = DataManager(Path(args.data_dir))

    if args.scan or args.report or args.duplicates:
        # 扫描数据目录
        stats = data_manager.scan_directory(args.min_size)

        logger.info("\n📊 扫描完成:")
        logger.info(f"  总文件数: {stats.total_files:,}")
        logger.info(f"  总大小: {humanize.naturalsize(stats.total_size)}")
        logger.info(f"  大文件(>{args.min_size}MB): {len(stats.large_files)}")

    if args.duplicates:
        duplicates = data_manager.find_duplicates()
        if duplicates:
            logger.info(f"\n🔄 发现 {len(duplicates)} 组重复文件")
        else:
            logger.info("\n✅ 没有发现重复文件")

    if args.report:
        report = data_manager.generate_report()
        report_path = Path('data_analysis_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"\n📝 分析报告已生成: {report_path}")

    if args.clean:
        data_manager.clean_temp_files()

    if args.archive:
        data_manager.archive_old_files(args.archive, dry_run=not args.execute)

    if args.unify_patent_kg:
        sources = []
        if args.kg_dirs and len(args.kg_dirs) > 0:
            for d in args.kg_dirs:
                sources.append(Path(d))
        else:
            sources.append(data_manager.default_neo4j_import)
        out_dir = (
            Path(args.kg_output)
            if args.kg_output
            else (
                data_manager.data_root
                / 'knowledge_graph_neo4j'
                / 'processed_data'
                / 'unified_patent_kg'
            )
        )
        stats = data_manager.unify_patent_kg(sources, out_dir)
        cypher_path = data_manager.generate_patent_kg_import_cypher(out_dir)
        logger.info(f"✅ 统一CSV已生成: {out_dir}")
        logger.info(f"  专利: {stats['patents']:,}")
        logger.info(f"  关系: {stats['relations']:,}")
        logger.info(f"  Cypher导入脚本: {cypher_path}")

    if args.import_unified_to_neo4j:
        out_dir = (
            Path(args.kg_output)
            if args.kg_output
            else (
                data_manager.data_root
                / 'knowledge_graph_neo4j'
                / 'processed_data'
                / 'unified_patent_kg'
            )
        )
        stats = data_manager.import_unified_patent_kg_to_neo4j(
            out_dir, args.neo4j_uri, args.neo4j_user, args.neo4j_password
        )
        print(
            f"✅ 已导入到Neo4j: 节点 {stats['patents']:,}, 关系 {stats['relations']:,}"
        )
        if args.delete_raw_json:
            json_dirs = []
            if args.json_dirs and len(args.json_dirs) > 0:
                json_dirs = [Path(d) for d in args.json_dirs]
            else:
                json_dirs = [data_manager.data_root / 'patent_kg_superfast']
            deleted = 0
            for d in json_dirs:
                for f in d.glob('batch_*.json'):
                    try:
                        f.unlink()
                        deleted += 1
                    except OSError:
                        pass
                s = d / 'summary.json'
                if s.exists():
                    try:
                        s.unlink()
                        deleted += 1
                    except OSError:
                        pass
            logger.info(f"✅ 已删除原始批次JSON: {deleted} 个文件")


if __name__ == '__main__':
    main()
