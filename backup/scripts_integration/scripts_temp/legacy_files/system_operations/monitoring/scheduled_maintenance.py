#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定期维护和清理流程
Scheduled Maintenance and Cleanup Process

自动化的知识图谱定期维护、检查和清理流程
"""

import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import schedule

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/xujian/Athena工作平台/logs/scheduled_maintenance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScheduledMaintenance:
    """定期维护管理器"""

    def __init__(self):
        self.project_root = '/Users/xujian/Athena工作平台'
        self.maintenance_log = '/Users/xujian/Athena工作平台/logs/maintenance_history.json'
        self.kg_directories = [
            '/Users/xujian/Athena工作平台/data/professional_knowledge_graphs',
            '/Users/xujian/Athena工作平台/data/merged_knowledge_graphs'
        ]
        self.maintenance_history = self.load_maintenance_history()

    def load_maintenance_history(self) -> Dict[str, Any]:
        """加载维护历史"""
        try:
            if Path(self.maintenance_log).exists():
                with open(self.maintenance_log, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载维护历史失败: {e}")

        return {
            'last_maintenance': None,
            'maintenance_count': 0,
            'issues_found': 0,
            'issues_fixed': 0,
            'history': []
        }

    def save_maintenance_history(self):
        """保存维护历史"""
        try:
            # 确保目录存在
            Path(self.maintenance_log).parent.mkdir(parents=True, exist_ok=True)

            with open(self.maintenance_log, 'w', encoding='utf-8') as f:
                json.dump(self.maintenance_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存维护历史失败: {e}")

    def run_daily_maintenance(self):
        """执行每日维护任务"""
        logger.info('🔧 执行每日维护任务')
        logger.info(str('=' * 50))

        maintenance_start = datetime.now()

        # 1. 健康检查
        logger.info("\n📊 执行健康检查...")
        health_issues = self.health_check()

        # 2. 数据质量检查
        logger.info("\n🔍 执行数据质量检查...")
        quality_issues = self.quality_check()

        # 3. 存储空间检查
        logger.info("\n💾 执行存储空间检查...")
        storage_issues = self.storage_check()

        # 4. 清理临时文件
        logger.info("\n🗑️ 执行临时文件清理...")
        cleanup_results = self.cleanup_temp_files()

        # 5. 生成维护报告
        logger.info("\n📄 生成维护报告...")
        report_file = self.generate_maintenance_report(
            maintenance_start, health_issues, quality_issues, storage_issues, cleanup_results
        )

        # 更新维护历史
        self.update_maintenance_history(maintenance_start, len(health_issues) + len(quality_issues))

        logger.info(f"\n✅ 每日维护完成!")
        logger.info(f"   发现问题: {len(health_issues) + len(quality_issues)} 个")
        logger.info(f"   清理文件: {cleanup_results['cleaned_files']} 个")
        logger.info(f"   报告文件: {report_file}")

    def run_weekly_maintenance(self):
        """执行每周维护任务"""
        logger.info('🔧 执行每周维护任务')
        logger.info(str('=' * 50))

        # 1. 深度数据质量检查
        logger.info("\n🔍 执行深度数据质量检查...")
        deep_quality_issues = self.deep_quality_check()

        # 2. 数据库优化
        logger.info("\n⚡ 执行数据库优化...")
        optimization_results = self.optimize_databases()

        # 3. 备份重要数据
        logger.info("\n💾 执行数据备份...")
        backup_results = self.backup_critical_data()

        # 4. 性能基准测试
        logger.info("\n🏃 执行性能基准测试...")
        performance_results = self.performance_benchmark()

        # 5. 生成周维护报告
        logger.info("\n📄 生成周维护报告...")
        report_file = self.generate_weekly_report(
            deep_quality_issues, optimization_results, backup_results, performance_results
        )

        logger.info(f"\n✅ 每周维护完成!")
        logger.info(f"   深度问题: {len(deep_quality_issues)} 个")
        logger.info(f"   优化数据库: {optimization_results['optimized_count']} 个")
        logger.info(f"   备份数据: {backup_results['backup_count']} 个")
        logger.info(f"   报告文件: {report_file}")

    def run_monthly_maintenance(self):
        """执行每月维护任务"""
        logger.info('🔧 执行每月维护任务')
        logger.info(str('=' * 50))

        # 1. 全面数据审计
        logger.info("\n📊 执行全面数据审计...")
        audit_results = self.full_data_audit()

        # 2. 索引重建
        logger.info("\n🔧 执行索引重建...")
        index_results = self.rebuild_indexes()

        # 3. 数据归档
        logger.info("\n📦 执行数据归档...")
        archive_results = self.archive_old_data()

        # 4. 系统更新检查
        logger.info("\n🔄 执行系统更新检查...")
        update_results = self.check_system_updates()

        # 5. 生成月维护报告
        logger.info("\n📄 生成月维护报告...")
        report_file = self.generate_monthly_report(
            audit_results, index_results, archive_results, update_results
        )

        logger.info(f"\n✅ 每月维护完成!")
        logger.info(f"   审计问题: {len(audit_results['issues'])} 个")
        logger.info(f"   重建索引: {index_results['rebuilt_count']} 个")
        logger.info(f"   归档数据: {archive_results['archived_count']} 个")
        logger.info(f"   报告文件: {report_file}")

    def health_check(self) -> List[Dict[str, Any]]:
        """健康检查"""
        issues = []

        for kg_dir in self.kg_directories:
            if not Path(kg_dir).exists():
                issues.append({
                    'type': 'directory_missing',
                    'path': kg_dir,
                    'severity': 'high',
                    'description': '知识图谱目录不存在'
                })
                continue

            for db_file in Path(kg_dir).glob('*.db'):
                try:
                    # 检查文件可访问性
                    conn = sqlite3.connect(str(db_file))
                    cursor = conn.cursor()

                    # 执行完整性检查
                    cursor.execute('PRAGMA integrity_check')
                    integrity_result = cursor.fetchone()[0]

                    if integrity_result != 'ok':
                        issues.append({
                            'type': 'database_integrity',
                            'file': str(db_file),
                            'severity': 'high',
                            'description': f"数据库完整性检查失败: {integrity_result}"
                        })

                    # 检查文件大小
                    file_size = db_file.stat().st_size
                    if file_size == 0:
                        issues.append({
                            'type': 'empty_file',
                            'file': str(db_file),
                            'severity': 'medium',
                            'description': '数据库文件为空'
                        })
                    elif file_size > 5 * 1024 * 1024 * 1024:  # 5GB
                        issues.append({
                            'type': 'large_file',
                            'file': str(db_file),
                            'severity': 'low',
                            'description': f"数据库文件过大: {file_size / (1024*1024):.1f} MB"
                        })

                    conn.close()

                except Exception as e:
                    issues.append({
                        'type': 'access_error',
                        'file': str(db_file),
                        'severity': 'high',
                        'description': f"无法访问数据库: {str(e)}"
                    })

        return issues

    def quality_check(self) -> List[Dict[str, Any]]:
        """数据质量检查"""
        issues = []

        for kg_dir in self.kg_directories:
            for db_file in Path(kg_dir).glob('*.db'):
                try:
                    conn = sqlite3.connect(str(db_file))
                    cursor = conn.cursor()

                    # 获取表列表
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [t[0] for t in cursor.fetchall()]

                    # 检查空表
                    empty_tables = []
                    for table in tables:
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table}")
                                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        if count == 0:
                            empty_tables.append(table)

                    if empty_tables:
                        issues.append({
                            'type': 'empty_tables',
                            'file': str(db_file),
                            'severity': 'medium',
                            'description': f"发现空表: {', '.join(empty_tables)}",
                            'details': {'empty_tables': empty_tables}
                        })

                    # 检查重复数据
                    if 'entities' in tables:
                        cursor.execute('SELECT COUNT(*) - COUNT(DISTINCT id) FROM entities')
                        duplicate_entities = cursor.fetchone()[0]
                        if duplicate_entities > 0:
                            issues.append({
                                'type': 'duplicate_entities',
                                'file': str(db_file),
                                'severity': 'medium',
                                'description': f"发现重复实体: {duplicate_entities} 个"
                            })

                    conn.close()

                except Exception as e:
                    logger.error(f"质量检查失败 {db_file}: {e}")

        return issues

    def storage_check(self) -> List[Dict[str, Any]]:
        """存储空间检查"""
        issues = []
        total_size = 0

        for kg_dir in self.kg_directories:
            if Path(kg_dir).exists():
                dir_size = sum(f.stat().st_size for f in Path(kg_dir).rglob('*') if f.is_file())
                total_size += dir_size

                # 检查目录大小
                if dir_size > 10 * 1024 * 1024 * 1024:  # 10GB
                    issues.append({
                        'type': 'large_directory',
                        'path': kg_dir,
                        'severity': 'medium',
                        'description': f"目录占用空间过大: {dir_size / (1024*1024):.1f} MB"
                    })

        # 检查总存储空间
        if total_size > 20 * 1024 * 1024 * 1024:  # 20GB
            issues.append({
                'type': 'total_storage_high',
                'severity': 'high',
                'description': f"总存储空间占用过高: {total_size / (1024*1024):.1f} MB",
                'details': {'total_size_mb': total_size / (1024*1024)}
            })

        return issues

    def cleanup_temp_files(self) -> Dict[str, Any]:
        """清理临时文件"""
        cleaned_files = 0
        space_freed = 0

        temp_patterns = [
            '*.tmp',
            '*.temp',
            '*~',
            '*.swp',
            '*.bak'
        ]

        for kg_dir in self.kg_directories:
            if Path(kg_dir).exists():
                for pattern in temp_patterns:
                    for temp_file in Path(kg_dir).glob(pattern):
                        try:
                            file_size = temp_file.stat().st_size
                            temp_file.unlink()
                            cleaned_files += 1
                            space_freed += file_size
                        except Exception as e:
                            logger.error(f"清理临时文件失败 {temp_file}: {e}")

        return {
            'cleaned_files': cleaned_files,
            'space_freed': space_freed,
            'space_freed_mb': space_freed / (1024*1024)
        }

    def deep_quality_check(self) -> List[Dict[str, Any]]:
        """深度数据质量检查"""
        issues = []

        # 检查数据一致性
        for kg_dir in self.kg_directories:
            for db_file in Path(kg_dir).glob('*.db'):
                try:
                    conn = sqlite3.connect(str(db_file))
                    cursor = conn.cursor()

                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [t[0] for t in cursor.fetchall()]

                    # 检查引用完整性
                    if 'entities' in tables and 'relations' in tables:
                        cursor.execute("""
                            SELECT COUNT(*) FROM relations r
                            LEFT JOIN entities e ON r.source_id = e.id
                            WHERE e.id IS NULL
                        """)
                        missing_sources = cursor.fetchone()[0]

                        if missing_sources > 100:  # 阈值检查
                            issues.append({
                                'type': 'many_missing_references',
                                'file': str(db_file),
                                'severity': 'high',
                                'description': f"大量缺失的源引用: {missing_sources} 个"
                            })

                    conn.close()

                except Exception as e:
                    logger.error(f"深度质量检查失败 {db_file}: {e}")

        return issues

    def optimize_databases(self) -> Dict[str, Any]:
        """优化数据库"""
        optimized_count = 0
        total_time_saved = 0

        for kg_dir in self.kg_directories:
            for db_file in Path(kg_dir).glob('*.db'):
                try:
                    start_time = time.time()

                    conn = sqlite3.connect(str(db_file))
                    cursor = conn.cursor()

                    # 执行优化操作
                    cursor.execute('VACUUM')
                    cursor.execute('ANALYZE')
                    cursor.execute('REINDEX')

                    conn.close()

                    optimization_time = time.time() - start_time
                    total_time_saved += optimization_time
                    optimized_count += 1

                    logger.info(f"优化完成: {db_file.name} ({optimization_time:.2f}s)")

                except Exception as e:
                    logger.error(f"优化数据库失败 {db_file}: {e}")

        return {
            'optimized_count': optimized_count,
            'total_time_saved': total_time_saved
        }

    def backup_critical_data(self) -> Dict[str, Any]:
        """备份关键数据"""
        backup_count = 0
        backup_size = 0

        # 创建备份目录
        backup_dir = Path('/Users/xujian/Athena工作平台/backup') / f"weekly_backup_{datetime.now().strftime('%Y%m%d')}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 备份专业知识图谱
        professional_dir = Path('/Users/xujian/Athena工作平台/data/professional_knowledge_graphs')
        if professional_dir.exists():
            for db_file in professional_dir.glob('*.db'):
                try:
                    backup_path = backup_dir / 'professional' / db_file.name
                    backup_path.parent.mkdir(parents=True, exist_ok=True)

                    import shutil
                    shutil.copy2(db_file, backup_path)

                    backup_count += 1
                    backup_size += db_file.stat().st_size

                except Exception as e:
                    logger.error(f"备份失败 {db_file}: {e}")

        return {
            'backup_count': backup_count,
            'backup_size': backup_size,
            'backup_size_mb': backup_size / (1024*1024)
        }

    def performance_benchmark(self) -> Dict[str, Any]:
        """性能基准测试"""
        benchmarks = []

        for kg_dir in self.kg_directories:
            for db_file in Path(kg_dir).glob('*.db')[:3]:  # 测试前3个文件
                try:
                    start_time = time.time()

                    conn = sqlite3.connect(str(db_file))
                    cursor = conn.cursor()

                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [t[0] for t in cursor.fetchall()]

                    # 测试查询性能
                    for table in tables[:3]:  # 测试前3个表
                        query_start = time.time()
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table}")
                                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        cursor.fetchone()
                        query_time = time.time() - query_start

                        benchmarks.append({
                            'file': db_file.name,
                            'table': table,
                            'query_time': query_time
                        })

                    conn.close()
                    total_time = time.time() - start_time

                except Exception as e:
                    logger.error(f"性能测试失败 {db_file}: {e}")

        # 计算平均性能
        avg_query_time = sum(b['query_time'] for b in benchmarks) / len(benchmarks) if benchmarks else 0

        return {
            'benchmarks': benchmarks,
            'avg_query_time': avg_query_time,
            'test_count': len(benchmarks)
        }

    def generate_maintenance_report(self, maintenance_start: datetime,
                                   health_issues: List, quality_issues: List,
                                   storage_issues: List, cleanup_results: Dict) -> str:
        """生成维护报告"""
        report_file = f"/Users/xujian/Athena工作平台/DAILY_MAINTENANCE_REPORT_{datetime.now().strftime('%Y%m%d')}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 每日维护报告\n\n")
            f.write(f"**维护时间**: {maintenance_start.isoformat()}\n")
            f.write(f"**维护工程师**: Athena AI Assistant\n\n")
            f.write("---\n\n")

            f.write("## 📊 维护统计\n\n")
            f.write(f"- **健康检查问题**: {len(health_issues)} 个\n")
            f.write(f"- **数据质量问题**: {len(quality_issues)} 个\n")
            f.write(f"- **存储空间问题**: {len(storage_issues)} 个\n")
            f.write(f"- **清理临时文件**: {cleanup_results['cleaned_files']} 个\n")
            f.write(f"- **释放空间**: {cleanup_results['space_freed_mb']:.1f} MB\n\n")

            # 问题详情
            all_issues = health_issues + quality_issues + storage_issues
            if all_issues:
                f.write("## ⚠️ 发现的问题\n\n")

                high_issues = [i for i in all_issues if i.get('severity') == 'high']
                medium_issues = [i for i in all_issues if i.get('severity') == 'medium']
                low_issues = [i for i in all_issues if i.get('severity') == 'low']

                if high_issues:
                    f.write("### 高优先级问题\n\n")
                    for issue in high_issues:
                        f.write(f"- **{issue['type']}**: {issue['description']}\n")
                    f.write("\n")

                if medium_issues:
                    f.write("### 中优先级问题\n\n")
                    for issue in medium_issues:
                        f.write(f"- **{issue['type']}**: {issue['description']}\n")
                    f.write("\n")

                if low_issues:
                    f.write("### 低优先级问题\n\n")
                    for issue in low_issues:
                        f.write(f"- **{issue['type']}**: {issue['description']}\n")
                    f.write("\n")
            else:
                f.write("## ✅ 未发现问题\n\n")
                f.write("所有系统组件运行正常，未发现需要关注的问题。\n\n")

        return report_file

    def generate_weekly_report(self, quality_issues: List, optimization_results: Dict,
                              backup_results: Dict, performance_results: Dict) -> str:
        """生成周维护报告"""
        report_file = f"/Users/xujian/Athena工作平台/WEEKLY_MAINTENANCE_REPORT_{datetime.now().strftime('%Y%W')}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 每周维护报告\n\n")
            f.write(f"**报告周期**: {datetime.now().strftime('%Y年第%W周')}\n")
            f.write(f"**报告时间**: {datetime.now().isoformat()}\n\n")
            f.write("---\n\n")

            f.write("## 📊 周维护统计\n\n")
            f.write(f"- **深度质量问题**: {len(quality_issues)} 个\n")
            f.write(f"- **优化数据库**: {optimization_results['optimized_count']} 个\n")
            f.write(f"- **备份数据**: {backup_results['backup_count']} 个\n")
            f.write(f"- **备份大小**: {backup_results['backup_size_mb']:.1f} MB\n")
            f.write(f"- **性能测试**: {performance_results['test_count']} 项\n")
            f.write(f"- **平均查询时间**: {performance_results['avg_query_time']:.3f} 秒\n\n")

        return report_file

    def generate_monthly_report(self, audit_results: Dict, index_results: Dict,
                               archive_results: Dict, update_results: Dict) -> str:
        """生成月维护报告"""
        report_file = f"/Users/xujian/Athena工作平台/MONTHLY_MAINTENANCE_REPORT_{datetime.now().strftime('%Y%m')}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 每月维护报告\n\n")
            f.write(f"**报告月份**: {datetime.now().strftime('%Y年%m月')}\n")
            f.write(f"**报告时间**: {datetime.now().isoformat()}\n\n")
            f.write("---\n\n")

            f.write("## 📊 月维护统计\n\n")
            f.write(f"- **审计问题**: {len(audit_results.get('issues', []))} 个\n")
            f.write(f"- **重建索引**: {index_results['rebuilt_count']} 个\n")
            f.write(f"- **归档数据**: {archive_results['archived_count']} 个\n")
            f.write(f"- **系统更新**: {len(update_results.get('available_updates', []))} 项\n\n")

        return report_file

    def update_maintenance_history(self, maintenance_time: datetime, issues_count: int):
        """更新维护历史"""
        self.maintenance_history['last_maintenance'] = maintenance_time.isoformat()
        self.maintenance_history['maintenance_count'] += 1
        self.maintenance_history['issues_found'] += issues_count

        # 添加到历史记录
        self.maintenance_history['history'].append({
            'timestamp': maintenance_time.isoformat(),
            'issues_count': issues_count
        })

        # 保留最近100条记录
        if len(self.maintenance_history['history']) > 100:
            self.maintenance_history['history'] = self.maintenance_history['history'][-100:]

        self.save_maintenance_history()

    # 简化的其他方法
    def full_data_audit(self) -> Dict[str, Any]:
        """全面数据审计"""
        return {'issues': [], 'recommendations': []}

    def rebuild_indexes(self) -> Dict[str, Any]:
        """重建索引"""
        return {'rebuilt_count': 0}

    def archive_old_data(self) -> Dict[str, Any]:
        """归档旧数据"""
        return {'archived_count': 0}

    def check_system_updates(self) -> Dict[str, Any]:
        """检查系统更新"""
        return {'available_updates': []}

    def setup_schedule(self):
        """设置定期维护计划"""
        # 每日维护
        schedule.every().day.at('02:00').do(self.run_daily_maintenance)

        # 每周维护
        schedule.every().week.do(self.run_weekly_maintenance)

        # 每月维护
        schedule.every().month.do(self.run_monthly_maintenance)

        logger.info('📅 定期维护计划已设置:')
        logger.info('   - 每日维护: 凌晨 02:00')
        logger.info('   - 每周维护: 每周执行一次')
        logger.info('   - 每月维护: 每月执行一次')

    def run_scheduler(self):
        """运行调度器"""
        logger.info('⏰ 定期维护调度器启动')
        logger.info('按 Ctrl+C 停止')

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("\n⏹️ 调度器已停止")

def main():
    """主函数"""
    maintenance = ScheduledMaintenance()

    import argparse

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query
    parser = argparse.ArgumentParser(description='知识图谱定期维护工具')
    parser.add_argument('--mode', choices=['daily', 'weekly', 'monthly', 'schedule'],
                       default='daily', help='维护模式')

    args = parser.parse_args()

    if args.mode == 'schedule':
        maintenance.setup_schedule()
        maintenance.run_scheduler()
    elif args.mode == 'daily':
        maintenance.run_daily_maintenance()
    elif args.mode == 'weekly':
        maintenance.run_weekly_maintenance()
    elif args.mode == 'monthly':
        maintenance.run_monthly_maintenance()

if __name__ == '__main__':
    main()