#!/usr/bin/env python3
"""
专利决定书文件去重工具
解决复审决定和无效宣告两个目录中的重复文件问题
"""

from __future__ import annotations
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# 使用安全哈希函数替代不安全的MD5/SHA1

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """文件信息"""
    path: str
    name: str
    size: int
    category: str  # 'review' 或 'invalid'
    md5_hash: str = ""


@dataclass
class DuplicateGroup:
    """重复文件组"""
    canonical_file: str  # 优先使用的文件
    duplicates: list[str]  # 重复文件列表
    name: str
    size: int
    content_match: bool = False


class PatentDecisionDeduplicator:
    """专利决定书去重器"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.review_dir = Path("/Volumes/AthenaData/语料/专利/专利复审决定原文")
        self.invalid_dir = Path("/Volumes/AthenaData/语料/专利/专利无效宣告原文")
        self.dedup_report_path = self.base_dir / "production/data/patent_decisions/dedup_report.json"

        # 文件索引
        self.files_by_name: dict[str, list[FileInfo]] = {}
        self.files_by_hash: dict[str, list[FileInfo]] = {}
        self.duplicate_groups: list[DuplicateGroup] = []

    def scan_directories(self) -> dict[str, any]:
        """扫描两个目录，建立索引"""
        logger.info("="*70)
        logger.info("🔍 扫描目录，建立文件索引")
        logger.info("="*70)

        stats = {
            'review_total': 0,
            'review_docx': 0,
            'review_doc': 0,
            'invalid_total': 0,
            'invalid_docx': 0,
            'invalid_doc': 0,
            'common_names': 0,
            'unique_to_review': 0,
            'unique_to_invalid': 0,
        }

        # 扫描复审决定
        logger.info(f"扫描复审决定目录: {self.review_dir}")
        for ext in ['*.docx', '*.doc']:
            for file_path in self.review_dir.glob(ext):
                file_info = FileInfo(
                    path=str(file_path),
                    name=file_path.name,
                    size=file_path.stat().st_size,
                    category='review'
                )
                self._index_file(file_info)
                stats['review_total'] += 1
                if ext == '*.docx':
                    stats['review_docx'] += 1
                else:
                    stats['review_doc'] += 1

        # 扫描无效宣告
        logger.info(f"扫描无效宣告目录: {self.invalid_dir}")
        for ext in ['*.docx', '*.doc']:
            for file_path in self.invalid_dir.glob(ext):
                file_info = FileInfo(
                    path=str(file_path),
                    name=file_path.name,
                    size=file_path.stat().st_size,
                    category='invalid'
                )
                self._index_file(file_info)
                stats['invalid_total'] += 1
                if ext == '*.docx':
                    stats['invalid_docx'] += 1
                else:
                    stats['invalid_doc'] += 1

        # 分析重复情况
        logger.info("分析文件重复情况...")

        # 按文件名分组
        name_groups = {name: files for name, files in self.files_by_name.items() if len(files) > 1}
        stats['common_names'] = len(name_groups)
        stats['unique_to_review'] = sum(1 for files in self.files_by_name.values() if files[0].category == 'review' and len(files) == 1)
        stats['unique_to_invalid'] = sum(1 for files in self.files_by_name.values() if files[0].category == 'invalid' and len(files) == 1)

        logger.info(f"总文件数: {stats['review_total'] + stats['invalid_total']:,}")
        logger.info(f"共同文件名: {stats['common_names']:,}")
        logger.info(f"复审独有: {stats['unique_to_review']:,}")
        logger.info(f"无效独有: {stats['unique_to_invalid']:,}")

        return stats

    def _index_file(self, file_info: FileInfo) -> Any:
        """索引文件"""
        name_key = file_info.name.lower()

        # 按文件名索引
        if name_key not in self.files_by_name:
            self.files_by_name[name_key] = []
        self.files_by_name[name_key].append(file_info)

    def compute_content_hashes(self, sample_size: int = 100) -> int:
        """计算文件内容哈希（用于验证内容是否相同）"""
        logger.info("="*70)
        logger.info("🔐 计算文件内容哈希（验证重复）")
        logger.info("="*70)

        # 只对有重复文件名的计算哈希
        duplicate_names = [name for name, files in self.files_by_name.items() if len(files) > 1]

        logger.info(f"需要验证的重复文件名: {len(duplicate_names):,}")

        processed = 0
        for name in duplicate_names:
            files = self.files_by_name[name]

            for file_info in files:
                # 计算MD5
                try:
                    md5_hash = self._compute_file_hash(file_info.path)
                    file_info.md5_hash = md5_hash

                    # 按哈希索引
                    if md5_hash not in self.files_by_hash:
                        self.files_by_hash[md5_hash] = []
                    self.files_by_hash[md5_hash].append(file_info)

                except Exception as e:
                    logger.warning(f"计算哈希失败 {file_info.name}: {e}")

            processed += 1
            if processed % 100 == 0:
                logger.info(f"进度: {processed}/{len(duplicate_names)}")

        logger.info(f"✅ 完成哈希计算，发现 {len(self.files_by_hash)} 个唯一内容")

        return len(self.files_by_hash)

    def _compute_file_hash(self, file_path: str, chunk_size: int = 8192) -> str:
        """计算文件MD5哈希"""
        md5 = hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(chunk_size), b''):
                    if not chunk:
                        break
                    md5.update(chunk)
        except Exception as e:
            logger.warning(f"读取文件失败 {file_path}: {e}")
            # 如果无法读取，使用文件名和大小作为哈希
            path_obj = Path(file_path)
            md5.update(f"{path_obj.name}_{path_obj.stat().st_size}".encode())

        return md5.hexdigest()

    def analyze_duplicates(self) -> list[DuplicateGroup]:
        """分析重复文件"""
        logger.info("="*70)
        logger.info("📊 分析重复文件")
        logger.info("="*70)

        # 按文件名分组的重复文件
        duplicate_groups = []

        for name, files in self.files_by_name.items():
            if len(files) > 1:
                # 检查是否有两个目录的文件
                review_files = [f for f in files if f.category == 'review']
                invalid_files = [f for f in files if f.category == 'invalid']

                if review_files and invalid_files:
                    # 检查内容是否相同（通过大小和哈希）
                    review_file = review_files[0]
                    invalid_file = invalid_files[0]

                    content_match = (
                        review_file.size == invalid_file.size and
                        (not review_file.md5_hash or not invalid_file.md5_hash or
                         review_file.md5_hash == invalid_file.md5_hash)
                    )

                    # 决定规范文件（优先级：复审 > 无效）
                    # 优先复审决定，因为复审决定通常在先
                    canonical = review_file.path if review_file.size > 0 else invalid_file.path

                    group = DuplicateGroup(
                        canonical_file=canonical,
                        duplicates=[f.path for f in files if f.path != canonical],
                        name=name,
                        size=review_file.size,
                        content_match=content_match
                    )
                    duplicate_groups.append(group)

        self.duplicate_groups = duplicate_groups

        # 统计
        total_duplicates = sum(len(g.duplicates) for g in duplicate_groups)
        content_matches = sum(1 for g in duplicate_groups if g.content_match)

        logger.info(f"发现重复组: {len(duplicate_groups):,}")
        logger.info(f"重复文件总数: {total_duplicates:,}")
        logger.info(f"内容完全相同: {content_matches:,} ({content_matches/len(duplicate_groups)*100:.1f}%)")

        return duplicate_groups

    def generate_dedup_strategy(self) -> dict[str, any]:
        """生成去重策略"""
        logger.info("="*70)
        logger.info("🎯 生成去重策略")
        logger.info("="*70)

        strategy = {
            'approach': '优先复审决定',
            'reason': '复审决定通常在无效宣告决定之前，复审决定文件更规范完整',
            'rules': []
        }

        content_match_count = 0
        size_mismatch_count = 0

        for group in self.duplicate_groups:
            if group.content_match:
                # 内容相同，优先复审决定
                rule = {
                    'name': group.name,
                    'action': 'use_review',
                    'canonical': group.canonical_file,
                    'skip': group.duplicates,
                    'reason': '内容相同，优先使用复审决定'
                }
                strategy['rules'].append(rule)
                content_match_count += 1
            else:
                # 内容不同，可能需要都处理
                rule = {
                    'name': group.name,
                    'action': 'process_both',
                    'files': [group.canonical_file] + group.duplicates,
                    'reason': '内容不同（大小不同），都需要处理'
                }
                strategy['rules'].append(rule)
                size_mismatch_count += 1

        logger.info(f"内容相同（跳过重复）: {content_match_count:,}")
        logger.info(f"内容不同（都处理）: {size_mismatch_count:,}")

        return strategy

    def create_skip_list(self) -> set[str]:
        """创建跳过列表（需要跳过的文件路径）"""
        skip_list = set()

        for group in self.duplicate_groups:
            if group.content_match:
                # 内容相同的重复文件，跳过
                for dup_path in group.duplicates:
                    skip_list.add(dup_path)

        logger.info(f"跳过列表包含 {len(skip_list):,} 个文件")
        return skip_list

    def save_report(self, stats: dict, strategy: dict) -> None:
        """保存去重报告"""
        self.dedup_report_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': stats,
            'strategy': strategy,
            'duplicate_groups': [
                {
                    'name': g.name,
                    'canonical': g.canonical_file,
                    'duplicates': g.duplicates,
                    'size': g.size,
                    'content_match': g.content_match
                }
                for g in self.duplicate_groups[:100]  # 保存前100个作为示例
            ],
            'total_duplicate_groups': len(self.duplicate_groups)
        }

        with open(self.dedup_report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 报告已保存: {self.dedup_report_path}")

    def run_analysis(self) -> tuple[set[str], dict]:
        """运行完整分析"""
        logger.info("🚀 开始去重分析...")

        # 1. 扫描目录
        stats = self.scan_directories()

        # 2. 计算内容哈希（抽样）
        self.compute_content_hashes(sample_size=500)

        # 3. 分析重复
        self.analyze_duplicates()

        # 4. 生成策略
        strategy = self.generate_dedup_strategy()

        # 5. 创建跳过列表
        skip_list = self.create_skip_list()

        # 6. 保存报告
        self.save_report(stats, strategy)

        logger.info("="*70)
        logger.info("✅ 去重分析完成")
        logger.info("="*70)

        return skip_list, strategy


def main() -> None:
    """主函数"""
    dedup = PatentDecisionDeduplicator()
    skip_list, strategy = dedup.run_analysis()

    print()
    print("="*70)
    print("📊 去重分析总结")
    print("="*70)
    print(f"跳过列表文件数: {len(skip_list):,}")
    print(f"去重策略: {strategy['approach']}")
    print()
    print("建议:")
    print("  1. 使用skip_list过滤重复文件")
    print("  2. 优先处理复审决定目录的文件")
    print("  3. 对于内容不同的文件，分别处理并标记来源")
    print("="*70)


if __name__ == "__main__":
    main()
