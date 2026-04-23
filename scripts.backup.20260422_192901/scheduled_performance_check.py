#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定期性能优化检查系统
自动执行存储系统性能检查和优化建议
"""

import asyncio
import json
import sys
import os
import schedule
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

class ScheduledPerformanceChecker:
    """定期性能检查器"""

    def __init__(self):
        self.logs_path = Path("/Users/xujian/Athena工作平台/logs")
        self.config_path = Path("/Users/xujian/Athena工作平台/config/storage_optimization.json")
        self.health_check_history = []

    def run_health_check(self) -> Any:
        """运行健康检查"""
        print("🔍 执行存储系统健康检查...")

        health_status = {
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }

        # 1. 检查配置文件完整性
        health_status['checks']['config_file'] = self._check_config_file()

        # 2. 检查系统性能指标
        health_status['checks']['performance_metrics'] = self._check_performance_metrics()

        # 3. 检查存储组件状态
        health_status['checks']['storage_components'] = self._check_storage_components()

        # 4. 检查系统资源使用
        health_status['checks']['system_resources'] = self._check_system_resources()

        # 5. 检查日志文件大小
        health_status['checks']['log_files'] = self._check_log_files()

        # 计算总体健康评分
        health_score = self._calculate_health_score(health_status['checks'])
        health_status['overall_health_score'] = health_score
        health_status['health_grade'] = self._get_health_grade(health_score)

        # 保存健康检查结果
        self._save_health_check(health_status)

        # 如果健康评分低于阈值，触发自动优化
        if health_score < 80:
            print(f"⚠️ 健康评分较低 ({health_score}%)，触发自动优化...")
            self._trigger_auto_optimization(health_status)
        else:
            print(f"✅ 系统健康状况良好 ({health_score}%)")

        return health_status

    def _check_config_file(self) -> Dict[str, Any]:
        """检查配置文件"""
        result = {
            'status': 'unknown',
            'issues': [],
            'recommendations': []
        }

        try:
            if not self.config_path.exists():
                result['status'] = 'error'
                result['issues'].append('配置文件不存在')
                return result

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 检查必要的配置项
            required_keys = [
                'storage_optimization.max_parallel_workers',
                'storage_optimization.cache_size_mb',
                'router_config.cache_priority_weight'
            ]

            for key in required_keys:
                if '.' in key:
                    section, param = key.split('.', 1)
                    if section not in config or param not in config[section]:
                        result['issues'].append(f'缺少配置项: {key}')
                        result['recommendations'].append(f'添加配置项 {key}')

            if not result['issues']:
                result['status'] = 'healthy'
                # 检查配置合理性
                workers = config.get('storage_optimization', {}).get('max_parallel_workers', 0)
                if workers < 4:
                    result['recommendations'].append('建议增加并行工作线程数到至少4个')

        except Exception as e:
            result['status'] = 'error'
            result['issues'].append(f'配置文件读取失败: {e}')

        return result

    def _check_performance_metrics(self) -> Dict[str, Any]:
        """检查性能指标"""
        result = {
            'status': 'unknown',
            'issues': [],
            'recommendations': []
        }

        try:
            # 查找最新的性能监控报告
            monitoring_reports = list(self.logs_path.glob("*storage_performance_monitoring_report.json"))
            if not monitoring_reports:
                result['status'] = 'warning'
                result['issues'].append('没有性能监控报告')
                result['recommendations'].append('运行性能监控系统')
                return result

            # 获取最新的报告
            latest_report = max(monitoring_reports, key=lambda x: x.stat().st_mtime)
            with open(latest_report, 'r', encoding='utf-8') as f:
                report = json.load(f)

            # 分析性能指标
            perf_stats = report.get('performance_statistics', {})
            execution_time = perf_stats.get('execution', {}).get('average_time', 0)
            reliability = perf_stats.get('reliability', {}).get('average_success_rate', 0)

            if execution_time > 0.15:
                result['issues'].append(f'平均执行时间过长: {execution_time:.3f}s')
                result['recommendations'].append('考虑增加并行工作线程或优化查询')

            if reliability < 0.95:
                result['issues'].append(f'成功率偏低: {reliability:.1%}')
                result['recommendations'].append('检查存储系统稳定性')

            # 检查路由多样性
            storage_usage = report.get('storage_usage_distribution', {})
            if len(storage_usage) <= 1:
                result['issues'].append('路由决策缺乏多样性')
                result['recommendations'].append('调整路由权重配置')

            if not result['issues']:
                result['status'] = 'healthy'

        except Exception as e:
            result['status'] = 'error'
            result['issues'].append(f'性能指标检查失败: {e}')

        return result

    def _check_storage_components(self) -> Dict[str, Any]:
        """检查存储组件状态"""
        result = {
            'status': 'unknown',
            'components': {},
            'issues': [],
            'recommendations': []
        }

        components = {
            'smart_storage_router': '/Users/xujian/Athena工作平台/storage-system/smart_storage_router.py',
            'parallel_storage_executor': '/Users/xujian/Athena工作平台/storage-system/parallel_storage_executor.py',
            'storage_performance_monitor': '/Users/xujian/Athena工作平台/storage-system/storage_performance_monitor.py'
        }

        for component_name, file_path in components.items():
            component_status = {
                'file_exists': False,
                'file_size': 0,
                'last_modified': None
            }

            try:
                if Path(file_path).exists():
                    component_status['file_exists'] = True
                    stat = Path(file_path).stat()
                    component_status['file_size'] = stat.st_size
                    component_status['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                else:
                    result['issues'].append(f'组件文件缺失: {component_name}')
                    result['recommendations'].append(f'重新创建组件: {component_name}')

            except Exception as e:
                result['issues'].append(f'组件检查失败 {component_name}: {e}')

            result['components'][component_name] = component_status

        if not result['issues']:
            result['status'] = 'healthy'

        return result

    def _check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源"""
        result = {
            'status': 'unknown',
            'issues': [],
            'recommendations': []
        }

        try:
            import psutil

            # 检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                result['issues'].append(f'CPU使用率过高: {cpu_percent:.1f}%')
                result['recommendations'].append('优化计算密集型任务或增加计算资源')

            # 检查内存使用率
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                result['issues'].append(f'内存使用率过高: {memory.percent:.1f}%')
                result['recommendations'].append('清理缓存或增加内存大小')

            # 检查磁盘空间
            disk = psutil.disk_usage('/Users/xujian/Athena工作平台')
            disk_usage_percent = (disk.used / disk.total) * 100
            if disk_usage_percent > 90:
                result['issues'].append(f'磁盘空间不足: {disk_usage_percent:.1f}%')
                result['recommendations'].append('清理日志文件或扩展存储空间')

            result['system_info'] = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_usage_percent': disk_usage_percent,
                'available_disk_gb': disk.free / (1024**3)
            }

            if not result['issues']:
                result['status'] = 'healthy'

        except ImportError:
            result['status'] = 'warning'
            result['issues'].append('psutil模块未安装，无法检查系统资源')
            result['recommendations'].append('安装psutil: pip install psutil')

        except Exception as e:
            result['status'] = 'error'
            result['issues'].append(f'系统资源检查失败: {e}')

        return result

    def _check_log_files(self) -> Dict[str, Any]:
        """检查日志文件"""
        result = {
            'status': 'unknown',
            'log_files': {},
            'issues': [],
            'recommendations': []
        }

        try:
            if not self.logs_path.exists():
                result['status'] = 'warning'
                result['issues'].append('日志目录不存在')
                return result

            # 检查主要日志文件
            log_patterns = [
                'storage_performance_monitoring_report.json',
                'storage_optimization_report.json',
                'storage_parameter_tuning_report.md'
            ]

            total_size = 0
            for pattern in log_patterns:
                log_files = list(self.logs_path.glob(pattern))
                for log_file in log_files:
                    size = log_file.stat().st_size / (1024 * 1024)  # MB
                    total_size += size
                    result['log_files'][log_file.name] = {
                        'size_mb': round(size, 2),
                        'last_modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                    }

            # 检查总体日志大小
            result['total_log_size_mb'] = round(total_size, 2)
            if total_size > 100:  # 超过100MB
                result['issues'].append(f'日志文件总大小过大: {total_size:.1f}MB')
                result['recommendations'].append('定期清理或压缩旧的日志文件')

            if not result['issues']:
                result['status'] = 'healthy'

        except Exception as e:
            result['status'] = 'error'
            result['issues'].append(f'日志文件检查失败: {e}')

        return result

    def _calculate_health_score(self, checks: Dict[str, Any]) -> int:
        """计算健康评分"""
        scores = {
            'healthy': 100,
            'warning': 70,
            'error': 30,
            'unknown': 50
        }

        total_score = 0
        check_count = len(checks)

        for check_name, check_result in checks.items():
            status = check_result.get('status', 'unknown')
            total_score += scores.get(status, 50)

            # 如果有严重问题，额外扣分
            issues = check_result.get('issues', [])
            if issues:
                total_score -= len(issues) * 5

        return max(0, min(100, int(total_score / check_count)))

    def _get_health_grade(self, score: int) -> str:
        """获取健康等级"""
        if score >= 90:
            return 'A (优秀)'
        elif score >= 80:
            return 'B (良好)'
        elif score >= 70:
            return 'C (一般)'
        elif score >= 60:
            return 'D (较差)'
        else:
            return 'F (需要立即关注)'

    def _save_health_check(self, health_status: Dict[str, Any]) -> Any:
        """保存健康检查结果"""
        self.health_check_history.append(health_status)

        # 保存到文件
        health_file = self.logs_path / f"storage_health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        health_file.parent.mkdir(exist_ok=True)

        with open(health_file, 'w', encoding='utf-8') as f:
            json.dump(health_status, f, indent=2, ensure_ascii=False, default=str)

        print(f"💾 健康检查结果已保存: {health_file}")

        # 只保留最近10次检查记录
        if len(self.health_check_history) > 10:
            self.health_check_history = self.health_check_history[-10:]

    def _trigger_auto_optimization(self, health_status: Dict[str, Any]) -> Any:
        """触发自动优化"""
        print("🔧 触发自动优化流程...")

        # 检查配置问题
        if health_status['checks'].get('config_file', {}).get('status') != 'healthy':
            print("  - 修复配置文件问题...")
            # 这里可以调用配置修复逻辑

        # 检查性能问题
        if health_status['checks'].get('performance_metrics', {}).get('status') != 'healthy':
            print("  - 优化性能参数...")
            # 这里可以调用参数调优逻辑
            try:
                from tune_storage_parameters import StorageParameterTuner
                tuner = StorageParameterTuner()
                tuner.run_parameter_tuning()
            except Exception as e:
                print(f"  - 自动调优失败: {e}")

        # 检查日志大小问题
        if health_status['checks'].get('log_files', {}).get('issues'):
            print("  - 清理日志文件...")
            self._cleanup_old_logs()

    def _cleanup_old_logs(self) -> Any:
        """清理旧的日志文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=7)  # 7天前的文件
            old_logs = []

            for log_file in self.logs_path.glob("*.json"):
                if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                    old_logs.append(log_file)

            for old_log in old_logs[:5]:  # 最多删除5个旧文件
                old_log.unlink()
                print(f"  - 删除旧日志: {old_log.name}")

        except Exception as e:
            print(f"  - 日志清理失败: {e}")

    def setup_schedule(self) -> Any:
        """设置定期检查计划"""
        print("📅 设置定期性能检查计划...")
        print("  - 每小时执行健康检查")
        print("  - 每天凌晨2点执行深度优化")
        print("  - 每周一执行完整参数调优")

        # 每小时健康检查
        schedule.every().hour.do(self.run_health_check)

        # 每天深度优化
        schedule.every().day.at("02:00").do(self._daily_deep_optimization)

        # 每周参数调优
        schedule.every().monday.at("03:00").do(self._weekly_parameter_tuning)

    def _daily_deep_optimization(self) -> Any:
        """每日深度优化"""
        print("🔧 执行每日深度优化...")
        # 这里可以实现更深入的优化逻辑

    def _weekly_parameter_tuning(self) -> Any:
        """每周参数调优"""
        print("🔧 执行每周参数调优...")
        try:
            from tune_storage_parameters import StorageParameterTuner
            tuner = StorageParameterTuner()
            tuner.run_parameter_tuning()
        except Exception as e:
            print(f"每周调优失败: {e}")

    def run_scheduler(self) -> Any:
        """运行调度器"""
        print("⏰ 启动定期性能检查调度器...")
        print("按 Ctrl+C 停止调度器")

        # 立即执行一次检查
        self.run_health_check()

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            print("\n🛑 调度器已停止")

def main() -> None:
    """主函数"""
    print("🔍 存储系统定期性能检查工具")
    print("=" * 50)

    checker = ScheduledPerformanceChecker()

    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        # 只执行一次检查
        checker.run_health_check()
    else:
        # 启动定期调度器
        checker.setup_schedule()
        checker.run_scheduler()

if __name__ == "__main__":
    main()