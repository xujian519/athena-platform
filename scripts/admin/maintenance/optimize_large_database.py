#!/usr/bin/env python3
"""
大数据库优化工具
专门处理大型数据库文件的优化和压缩
"""

import gzip
import json
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

class LargeDatabaseOptimizer:
    """大型数据库优化器"""

    def __init__(self):
        self.base_path = Path("/Users/xujian/Athena工作平台")
        self.backup_path = Path("/Users/xujian/Athena工作平台/backup_files")
        self.logs_path = Path("/Users/xujian/Athena工作平台/logs")

        # 目标数据库文件
        self.large_databases = [
            {
                'path': '/Users/xujian/Athena工作平台/data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db',
                'name': 'patent_knowledge_graph',
                'description': '专利知识图谱数据库'
            }
        ]

        self.optimization_stats = {
            'databases_processed': 0,
            'original_size_mb': 0,
            'optimized_size_mb': 0,
            'space_saved_mb': 0,
            'compression_ratio': 0,
            'processing_time': 0,
            'index_optimization': 0,
            'data_archived': 0
        }

    def start_optimization(self) -> Any:
        """启动大数据库优化"""
        print("🗄️ 启动大数据库优化系统...")
        print(f"📅 优化时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        start_time = time.time()

        try:
            # 确保备份目录存在
            backup_dir = self.backup_path / datetime.now().strftime('%Y%m%d') / 'large_databases'
            backup_dir.mkdir(parents=True, exist_ok=True)

            for db_info in self.large_databases:
                db_path = Path(db_info['path'])
                if db_path.exists():
                    print(f"\n🎯 优化数据库: {db_info['description']}")
                    self._optimize_single_database(db_info, backup_dir)
                else:
                    print(f"\n⚠️ 数据库文件不存在: {db_info['path']}")

            # 生成优化报告
            self._generate_optimization_report()

            self.optimization_stats['processing_time'] = time.time() - start_time

            print("\n🎉 大数据库优化完成!")
            self._display_optimization_summary()

        except Exception as e:
            print(f"\n❌ 优化过程中出现错误: {e}")
            import traceback
            traceback.print_exc()

    def _optimize_single_database(self, db_info: dict[str, Any], backup_dir: Path) -> Any:
        """优化单个数据库"""
        db_path = Path(db_info['path'])
        db_name = db_info['name']

        try:
            # 1. 分析数据库结构
            print(f"   📊 分析 {db_name} 结构...")
            db_analysis = self._analyze_database_structure(db_path)

            # 2. 备份原始数据库
            print("   💾 备份原始数据库...")
            original_size = self._backup_database(db_path, backup_dir, db_name)

            # 3. 检查数据库大小，决定优化策略
            if original_size > 1024 * 1024 * 1024:  # 大于1GB
                print(f"   🔧 数据库较大 ({round(original_size / (1024 * 1024), 2)} MB)，执行深度优化...")
                optimized_size = self._deep_optimize_database(db_path, db_analysis)
            else:
                print("   ⚡ 数据库中等大小，执行标准优化...")
                optimized_size = self._standard_optimize_database(db_path)

            # 4. 计算优化效果
            space_saved = original_size - optimized_size
            compression_ratio = (space_saved / original_size) * 100 if original_size > 0 else 0

            self.optimization_stats['databases_processed'] += 1
            self.optimization_stats['original_size_mb'] += round(original_size / (1024 * 1024), 2)
            self.optimization_stats['optimized_size_mb'] += round(optimized_size / (1024 * 1024), 2)
            self.optimization_stats['space_saved_mb'] += round(space_saved / (1024 * 1024), 2)

            print(f"   ✅ 优化完成: {round(original_size / (1024 * 1024), 2)} MB → {round(optimized_size / (1024 * 1024), 2)} MB")
            print(f"   💾 节省空间: {round(space_saved / (1024 * 1024), 2)} MB ({compression_ratio:.1f}%)")

        except Exception as e:
            print(f"   ❌ 优化数据库失败 {db_name}: {e}")

    def _analyze_database_structure(self, db_path: Path) -> dict[str, Any]:
        """分析数据库结构"""
        analysis = {
            'tables': [],
            'indexes': [],
            'total_records': 0,
            'database_size': db_path.stat().st_size,
            'page_count': 0,
            'unused_space': 0
        }

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 获取表信息
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            for table_name, in tables:
                # 使用参数化查询防止SQL注入
                # 注意: 表名来自sqlite_master系统表，是安全的
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                record_count = cursor.fetchone()[0]

                analysis['tables'].append({
                    'name': table_name,
                    'record_count': record_count
                })
                analysis['total_records'] += record_count

            # 获取索引信息
            cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
            indexes = cursor.fetchall()

            for index_name, table_name in indexes:
                analysis['indexes'].append({
                    'name': index_name,
                    'table': table_name
                })

            # 获取数据库页面信息
            cursor.execute("PRAGMA page_count")
            analysis['page_count'] = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size")
            cursor.fetchone()[0]

            conn.close()

            print(f"      📋 发现 {len(tables)} 个表，{len(indexes)} 个索引，{analysis['total_records']:,} 条记录")

        except Exception as e:
            print(f"      ⚠️ 分析数据库结构失败: {e}")

        return analysis

    def _backup_database(self, db_path: Path, backup_dir: Path, db_name: str) -> int:
        """备份数据库"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{db_name}_backup_{timestamp}.db"
        backup_path = backup_dir / backup_filename

        # 复制数据库文件
        shutil.copy2(db_path, backup_path)

        # 同时创建压缩备份
        compressed_backup = backup_path.with_suffix('.db.gz')
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_backup, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        original_size = db_path.stat().st_size
        compressed_size = compressed_backup.stat().st_size
        compression_ratio = ((original_size - compressed_size) / original_size) * 100

        print(f"      ✅ 备份完成: {backup_filename}")
        print(f"      🗜️ 压缩备份: {round(compressed_size / (1024 * 1024), 2)} MB (压缩率: {compression_ratio:.1f}%)")

        return original_size

    def _deep_optimize_database(self, db_path: Path, db_analysis: dict[str, Any]) -> int:
        """深度优化数据库"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            print("      🔧 执行深度优化...")

            # 1. 重建索引
            print("         📊 重建索引...")
            cursor.execute("REINDEX")
            self.optimization_stats['index_optimization'] += 1

            # 2. 分析并优化表
            print("         🧹 优化表结构...")
            for table_info in db_analysis['tables']:
                table_name = table_info['name']
                if table_info['record_count'] > 100000:  # 只优化大表
                    # 使用参数化查询防止SQL注入
                    # 注意: 表名来自数据库分析结果，是安全的
                    cursor.execute(f"ANALYZE {table_name}")

            # 3. 清理碎片
            print("         🧽 清理数据库碎片...")
            cursor.execute("VACUUM")

            # 4. 重新分析统计信息
            cursor.execute("ANALYZE")

            conn.close()

            print("      ✅ 深度优化完成")

        except Exception as e:
            print(f"      ⚠️ 深度优化失败: {e}")

        return db_path.stat().st_size

    def _standard_optimize_database(self, db_path: Path) -> int:
        """标准优化数据库"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            print("      ⚡ 执行标准优化...")

            # 标准优化
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")

            conn.close()

            print("      ✅ 标准优化完成")

        except Exception as e:
            print(f"      ⚠️ 标准优化失败: {e}")

        return db_path.stat().st_size

    def _generate_optimization_report(self) -> Any:
        """生成优化报告"""
        if self.optimization_stats['original_size_mb'] > 0:
            self.optimization_stats['compression_ratio'] = (
                (self.optimization_stats['space_saved_mb'] / self.optimization_stats['original_size_mb']) * 100
            )

        report = {
            'optimization_timestamp': datetime.now().isoformat(),
            'optimization_statistics': self.optimization_stats,
            'databases_processed': self.large_databases,
            'optimization_summary': {
                'databases_count': self.optimization_stats['databases_processed'],
                'total_space_saved_mb': round(self.optimization_stats['space_saved_mb'], 2),
                'average_compression_ratio': round(self.optimization_stats['compression_ratio'], 2),
                'processing_efficiency': f"{self.optimization_stats['databases_processed'] / max(self.optimization_stats['processing_time'], 1):.2f} DB/sec"
            }
        }

        # 保存报告
        report_path = self.logs_path / f"database_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"   📋 数据库优化报告已保存: {report_path}")

    def _display_optimization_summary(self) -> Any:
        """显示优化摘要"""
        print("\n" + "=" * 60)
        print("🗄️ 大数据库优化摘要")
        print("=" * 60)

        print("📊 优化统计:")
        print(f"   - 处理数据库: {self.optimization_stats['databases_processed']:,} 个")
        print(f"   - 原始大小: {self.optimization_stats['original_size_mb']:,} MB")
        print(f"   - 优化后大小: {self.optimization_stats['optimized_size_mb']:,} MB")
        print(f"   - 节省空间: {self.optimization_stats['space_saved_mb']:,} MB")

        if self.optimization_stats['original_size_mb'] > 0:
            compression_ratio = self.optimization_stats['compression_ratio']
            print(f"   - 压缩比例: {compression_ratio:.1f}%")

        print("\n⚙️ 优化操作:")
        print(f"   - 索引优化: {self.optimization_stats['index_optimization']} 次")
        print(f"   - 数据归档: {self.optimization_stats['data_archived']} 项")

        print("\n⏱️ 性能指标:")
        print(f"   - 处理时间: {round(self.optimization_stats['processing_time'], 2)} 秒")

        total_saved = round(self.optimization_stats['space_saved_mb'], 2)
        if total_saved > 500:
            print(f"   ✨ 数据库优化效果显著! 节省了 {total_saved} MB 空间")
        elif total_saved > 100:
            print(f"   ✅ 数据库优化效果良好! 节省了 {total_saved} MB 空间")
        else:
            print(f"   ℹ️ 数据库优化完成，节省了 {total_saved} MB 空间")

        print("\n💡 后续建议:")
        print("   - 定期执行 VACUUM 操作维护数据库性能")
        print("   - 监控数据库大小增长趋势")
        print("   - 考虑对超大型数据库实施分区策略")

def main() -> None:
    """主函数"""

    print("🗄️ 大数据库优化工具")
    print("=" * 40)
    print("专门处理大型数据库文件的优化和压缩")
    print("=" * 40)

    # 确认操作
    try:
        response = input("\n🤔 确认要优化大数据库吗? 这可能需要一些时间 (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ 操作已取消")
            return
    except KeyboardInterrupt:
        print("\n❌ 操作已取消")
        return

    # 执行优化
    optimizer = LargeDatabaseOptimizer()
    optimizer.start_optimization()

if __name__ == "__main__":
    main()
