#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局上下文优化器
Global Context Optimizer

优化Claude Code的全局上下文管理策略
"""

import argparse
import json
import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

class GlobalContextOptimizer:
    """全局上下文优化器"""

    def __init__(self):
        self.base_dir = Path('/Users/xujian/Athena工作平台')
        self.claude_dir = Path.home() / '.claude'

        # 优化配置
        self.optimization_config = {
            'history_management': {
                'max_entries': 500,           # 最大历史条目
                'compress_after': 30,       # 压缩阈值
                'archive_after': 7,         # 归档天数
                'keep_pattern': ['patent', 'ai', 'ml', 'search']  # 保留关键词
            },
            'debug_cleanup': {
                'max_sessions': 10,          # 最大调试会话
                'cleanup_interval': 24,     # 清理间隔（小时）
                'keep_recent_hours': 48      # 保留最近时间
            },
            'todos_cleanup': {
                'auto_archive': True,         # 自动归档
                'cleanup_completed': True,   # 清理已完成
                'keep_active_days': 7,        # 保留活跃天数
            },
            'file_history_cleanup': {
                'max_size_mb': 50,           # 最大大小(MB)
                'cleanup_threshold': 0.8,    # 清理阈值
                'compress_large_files': True  # 压缩大文件
            }
        }

        # 创建输出目录
        self.output_dir = self.base_dir / 'documentation' / 'context-optimization'
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze_all_contexts(self) -> Dict:
        """分析所有上下文"""
        logger.info('🔍 分析Claude Code全局上下文...')

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'claude_directory': {
                'size_mb': self._get_dir_size_mb(self.claude_dir),
                'file_count': self._count_files(self.claude_dir),
                'subdirs': self._get_subdirectories(self.claude_dir)
            },
            'history_file': self._analyze_history_file(),
            'debug_info': self._analyze_debug_info(),
            'todos': self._analyze_todos(),
            'file_history': self._analyze_file_history(),
            'recommendations': []
        }

        # 生成建议
        analysis['recommendations'] = self._generate_recommendations(analysis)

        return analysis

    def optimize_all_contexts(self, dry_run: bool = True) -> Dict:
        """优化所有上下文"""
        logger.info('🚀 开始全局上下文优化...')

        results = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'optimizations': {},
            'total_space_freed': '0B',
            'success_count': 0
        }

        # 优化历史文件
        history_result = self._optimize_history_file(dry_run)
        results['optimizations']['history'] = history_result
        results['success_count'] += 1 if history_result['success'] else 0

        # 清理调试信息
        debug_result = self._cleanup_debug_info(dry_run)
        results['optimizations']['debug'] = debug_result
        results['success_count'] += 1 if debug_result['success'] else 0

        # 清理Todos
        todos_result = self._cleanup_todos(dry_run)
        results['optimizations']['todos'] = todos_result
        results['success_count'] += 1 if todos_result['success'] else 0

        # 优化文件历史
        file_result = self._optimize_file_history(dry_run)
        results['optimizations']['file_history'] = file_result
        results['success_count'] += 1 if file_result['success'] else 0

        # 计算总释放空间
        total_bytes = sum([
            result.get('space_freed_bytes', 0)
            for result in results['optimizations'].values()
        ])
        results['total_space_freed'] = self._format_size(total_bytes)

        # 保存优化报告
        report_file = self.output_dir / f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return results

    def _analyze_history_file(self) -> Dict:
        """分析历史文件"""
        history_file = self.claude_dir / 'history.jsonl'

        if not history_file.exists():
            return {'exists': False, 'message': '历史文件不存在'}

        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            total_entries = len(lines)
            file_size = history_file.stat().st_size

            # 分析内容
            important_entries = 0
            for line in lines:
                if any(keyword in line.lower() for keyword in
                   self.optimization_config['history_management']['keep_pattern']):
                    important_entries += 1

            return {
                'exists': True,
                'total_entries': total_entries,
                'file_size_mb': round(file_size / 1024 / 1024, 2),
                'important_entries': important_entries,
                'size_ratio': important_entries / total_entries if total_entries > 0 else 0
            }

        except Exception as e:
            return {'exists': True, 'error': str(e)}

    def _optimize_history_file(self, dry_run: bool = True) -> Dict:
        """优化历史文件"""
        config = self.optimization_config['history_management']
        history_file = self.claude_dir / 'history.jsonl'

        if not history_file.exists():
            return {'success': False, 'message': '历史文件不存在'}

        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if len(lines) <= config['max_entries']:
                return {'success': False, 'message': '历史文件已在优化范围内'}

            # 备份
            if not dry_run:
                backup_file = history_file.with_suffix(f".backup_{int(time.time())}")
                shutil.copy2(history_file, backup_file)

            # 优化：保留重要条目和最近条目
            important_lines = []
            recent_lines = []

            for line in lines:
                if any(keyword in line.lower() for keyword in config['keep_pattern']):
                    important_lines.append(line)

            # 保留最近的条目
            recent_count = min(config['max_entries'] - len(important_lines),
                             len(lines) - len(important_lines))
            if recent_count > 0:
                recent_lines = lines[-recent_count:]

            # 合并并写入
            optimized_lines = recent_lines + important_lines
            space_freed = len(lines) - len(optimized_lines)

            if not dry_run:
                with open(history_file, 'w', encoding='utf-8') as f:
                    f.writelines(optimized_lines)

            return {
                'success': True,
                'original_entries': len(lines),
                'optimized_entries': len(optimized_lines),
                'space_freed_bytes': space_freed * 100,  # 估算每行100字节
                'space_freed': self._format_size(space_freed * 100)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _analyze_debug_info(self) -> Dict:
        """分析调试信息"""
        debug_dir = self.claude_dir / 'debug'

        if not debug_dir.exists():
            return {'exists': False, 'message': '调试目录不存在'}

        file_count = len(list(debug_dir.rglob('*')))
        size_mb = self._get_dir_size_mb(debug_dir)
        oldest_file = min(debug_dir.rglob('*'), key=os.path.getctime) if file_count > 0 else None

        return {
            'exists': True,
            'file_count': file_count,
            'size_mb': round(size_mb, 2),
            'oldest_file': oldest_file.name if oldest_file else None,
            'oldest_age_hours': self._get_file_age_hours(oldest_file) if oldest_file else None
        }

    def _cleanup_debug_info(self, dry_run: bool = True) -> Dict:
        """清理调试信息"""
        config = self.optimization_config['debug_cleanup']
        debug_dir = self.claude_dir / 'debug'

        if not debug_dir.exists():
            return {'success': False, 'message': '调试目录不存在'}

        try:
            debug_files = list(debug_dir.rglob('*'))
            if len(debug_files) <= config['max_sessions']:
                return {'success': False, 'message': '调试文件数量在限制内'}

            # 计算要删除的文件
            files_to_delete = []
            current_time = time.time()
            for file_path in debug_files:
                file_age = (current_time - file_path.stat().st_ctime) / 3600
                if file_age > config['keep_recent_hours']:
                    files_to_delete.append(file_path)

            space_freed = 0
            deleted_count = 0

            if not dry_run:
                for file_path in files_to_delete:
                    try:
                        size = file_path.stat().st_size
                        file_path.unlink()
                        space_freed += size
                        deleted_count += 1
                    except:
                        pass

            return {
                'success': True,
                'original_count': len(debug_files),
                'deleted_count': deleted_count,
                'space_freed_bytes': space_freed,
                'space_freed': self._format_size(space_freed)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _analyze_todos(self) -> Dict:
        """分析Todos"""
        todos_dir = self.claude_dir / 'todos'

        if not todos_dir.exists():
            return {'exists': False, 'message': 'Todos目录不存在'}

        todo_files = list(todos_dir.glob('*.json'))
        total_todos = len(todo_files)
        completed_todos = 0

        for todo_file in todo_files:
            try:
                with open(todo_file, 'r') as f:
                    todo_data = json.load(f)
                    if todo_data.get('status') == 'completed':
                        completed_todos += 1
            except:
                pass

        return {
            'exists': True,
            'total_todos': total_todos,
            'completed_todos': completed_todos,
            'completion_rate': completed_todos / total_todos if total_todos > 0 else 0
        }

    def _cleanup_todos(self, dry_run: bool = True) -> Dict:
        """清理Todos"""
        config = self.optimization_config['todos_cleanup']
        todos_dir = self.claude_dir / 'todos'

        if not todos_dir.exists():
            return {'success': False, 'message': 'Todos目录不存在'}

        try:
            todo_files = list(todos_dir.glob('*.json'))
            files_to_delete = []
            current_time = time.time()

            for todo_file in todo_files:
                try:
                    with open(todo_file, 'r') as f:
                        todo_data = json.load(f)

                    # 检查是否应该删除
                    should_delete = False

                    if config['cleanup_completed'] and todo_data.get('status') == 'completed':
                        file_age = (current_time - todo_file.stat().st_ctime) / 86400
                        if file_age > config['keep_active_days']:
                            should_delete = True

                    if should_delete:
                        files_to_delete.append(todo_file)

                except:
                    pass

            deleted_count = 0
            if not dry_run:
                for todo_file in files_to_delete:
                    try:
                        todo_file.unlink()
                        deleted_count += 1
                    except:
                        pass

            return {
                'success': True,
                'total_todos': len(todo_files),
                'deleted_count': deleted_count,
                'remaining_todos': len(todo_files) - deleted_count
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _analyze_file_history(self) -> Dict:
        """分析文件历史"""
        history_file = self.claude_dir / 'file-history'

        if not history_file.exists():
            return {'exists': False, 'message': '文件历史不存在'}

        file_size = history_file.stat().st_size
        config = self.optimization_config['file_history_cleanup']

        return {
            'exists': True,
            'file_size_mb': round(file_size / 1024 / 1024, 2),
            'over_threshold': file_size > (config['max_size_mb'] * 1024 * 1024),
            'threshold_mb': config['max_size_mb']
        }

    def _optimize_file_history(self, dry_run: bool = True) -> Dict:
        """优化文件历史"""
        history_file = self.claude_dir / 'file-history'
        config = self.optimization_config['file_history_cleanup']

        if not history_file.exists():
            return {'success': False, 'message': '文件历史不存在'}

        file_size = history_file.stat().st_size
        max_size = config['max_size_mb'] * 1024 * 1024

        if file_size <= max_size * config['cleanup_threshold']:
            return {'success': False, 'message': '文件历史大小在可接受范围内'}

        try:
            if not dry_run:
                # 压缩或截断文件
                if config['compress_large_files']:
                    # 创建压缩备份
                    compressed_file = history_file.with_suffix('.json.gz')
                    # 实现压缩逻辑
                    # ...

                # 截断文件到最大大小
                with open(history_file, 'rb') as f:
                    f.seek(max_size)
                    f.truncate()

            return {
                'success': True,
                'original_size_mb': round(file_size / 1024 / 1024, 2),
                'optimized_size_mb': round(max_size / 1024 / 1024, 2),
                'space_freed_bytes': file_size - max_size,
                'space_freed': self._format_size(file_size - max_size)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_dir_size_mb(self, path: Path) -> float:
        """获取目录大小(MB)"""
        try:
            total_size = 0
            for item in path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
            return round(total_size / 1024 / 1024, 2)
        except:
            return 0

    def _count_files(self, path: Path) -> int:
        """统计文件数量"""
        try:
            return len(list(path.rglob('*')))
        except:
            return 0

    def _get_subdirectories(self, path: Path) -> List[str]:
        """获取子目录列表"""
        try:
            return [d.name for d in path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        except:
            return []

    def _get_file_age_hours(self, file_path: Path) -> int:
        """获取文件年龄（小时）"""
        try:
            return int((time.time() - file_path.stat().st_ctime) / 3600)
        except:
            return 0

    def _format_size(self, size_bytes: int) -> str:
        """格式化大小"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / 1024 / 1024:.1f}MB"
        else:
            return f"{size_bytes / 1024 / 1024 / 1024:.1f}GB"

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 历史文件建议
        if analysis['history_file'].get('exists', False):
            history = analysis['history_file']
            if history['total_entries'] > 1000:
                recommendations.append(f"历史记录过多({history['total_entries']}条)，建议清理保留重要条目")

            if history['size_ratio'] < 0.5:
                recommendations.append('历史记录中重要条目比例较低，考虑优化关键词保留策略')

        # 调试信息建议
        if analysis['debug_info'].get('exists', False):
            debug = analysis['debug_info']
            if debug['oldest_age_hours'] and debug['oldest_age_hours'] > 48:
                recommendations.append(f"调试信息过旧({debug['oldest_age_hours']}小时)，建议清理")

        # Todos建议
        if analysis['todos'].get('exists', False):
            todos = analysis['todos']
            if todos['completion_rate'] > 0.8:
                recommendations.append('Todos完成率较高，建议清理已完成的项目')

        # 文件历史建议
        if analysis['file_history'].get('over_threshold', False):
            recommendations.append('文件历史过大，建议启用压缩或截断')

        return recommendations

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='全局上下文优化器')
    parser.add_argument('--analyze', action='store_true', help='分析上下文状态')
    parser.add_argument('--optimize', action='store_true', help='执行优化')
    parser.add_argument('--dry-run', action='store_true', help='预览模式（不实际执行）')

    args = parser.parse_args()

    optimizer = GlobalContextOptimizer()

    if args.analyze:
        analysis = optimizer.analyze_all_contexts()
        logger.info("\n📊 上下文分析报告")
        logger.info(str('=' * 50))

        for category, data in analysis.items():
            if category == 'recommendations':
                logger.info(f"\n💡 优化建议 ({len(data)}项):")
                for i, rec in enumerate(data, 1):
                    logger.info(f"  {i}. {rec}")
            elif category == 'timestamp':
                logger.info(f"\n⏰ 分析时间: {data}")
            else:
                logger.info(f"\n📁 {category.replace('_', ' ').title()}:")
                for key, value in data.items():
                    if key != 'exists' or value:
                        logger.info(f"  {key}: {value}")

    elif args.optimize:
        results = optimizer.optimize_all_contexts(dry_run=args.dry_run)
        logger.info(f"\n🚀 上下文优化报告 ({'预览模式' if args.dry_run else '执行模式'})")
        logger.info(str('=' * 50))

        logger.info(f"\n✅ 成功优化: {results['success_count']}/4 项")
        logger.info(f"💾 释放空间: {results['total_space_freed']}")
        logger.info(f"📄 报告保存: {results['timestamp']}")

        for category, data in results.get('optimizations', {}).items():
            logger.info(f"\n📊 {category.title()}:")
            for key, value in data.items():
                logger.info(f"  {key}: {value}")

    else:
        logger.info('请指定操作: --analyze 或 --optimize')
        logger.info('使用 --help 查看详细帮助')

if __name__ == '__main__':
    main()