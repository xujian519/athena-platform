#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的定期性能检查系统
不依赖外部包，专注于核心性能检查
"""

import json
import sys
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

class SimplePerformanceChecker:
    """简化的性能检查器"""

    def __init__(self):
        self.logs_path = Path("/Users/xujian/Athena工作平台/logs")
        self.config_path = Path("/Users/xujian/Athena工作平台/config/storage_optimization.json")

    def run_comprehensive_check(self) -> Any:
        """运行综合性能检查"""
        print("🔍 执行存储系统综合性能检查...")
        print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        check_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'checks': {},
            'recommendations': [],
            'performance_score': 0
        }

        # 1. 配置文件检查
        config_check = self._check_configuration()
        check_results['checks']['configuration'] = config_check

        # 2. 组件文件检查
        components_check = self._check_storage_components()
        check_results['checks']['components'] = components_check

        # 3. 日志文件分析
        logs_check = self._analyze_log_files()
        check_results['checks']['logs'] = logs_check

        # 4. 性能趋势分析
        performance_trend = self._analyze_performance_trend()
        check_results['checks']['performance_trend'] = performance_trend

        # 5. 优化效果评估
        optimization_effectiveness = self._evaluate_optimization_effectiveness()
        check_results['checks']['optimization'] = optimization_effectiveness

        # 计算总体评分
        check_results['performance_score'] = self._calculate_overall_score(check_results['checks'])
        check_results['overall_status'] = self._get_overall_status(check_results['performance_score'])

        # 生成建议
        check_results['recommendations'] = self._generate_recommendations(check_results['checks'])

        # 显示结果
        self._display_results(check_results)

        # 保存检查结果
        self._save_check_results(check_results)

        return check_results

    def _check_configuration(self) -> Dict[str, Any]:
        """检查配置文件状态"""
        result = {
            'status': 'unknown',
            'details': {},
            'issues': []
        }

        try:
            if not self.config_path.exists():
                result['status'] = 'critical'
                result['issues'].append('配置文件不存在')
                return result

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 检查关键配置参数
            storage_config = config.get('storage_optimization', {})
            router_config = config.get('router_config', {})
            monitor_config = config.get('monitoring_config', {})

            result['details'] = {
                'max_workers': storage_config.get('max_parallel_workers', 'not_set'),
                'cache_size_mb': storage_config.get('cache_size_mb', 'not_set'),
                'connection_pool': storage_config.get('connection_pool_size', 'not_set'),
                'router_cache_weight': router_config.get('cache_priority_weight', 'not_set'),
                'monitoring_interval': monitor_config.get('reflection_interval_seconds', 'not_set')
            }

            # 验证配置合理性
            workers = storage_config.get('max_parallel_workers', 0)
            if workers < 4:
                result['issues'].append(f'工作线程数过低 ({workers})，建议至少4个')

            cache_size = storage_config.get('cache_size_mb', 0)
            if cache_size < 512:
                result['issues'].append(f'缓存大小偏小 ({cache_size}MB)，建议至少512MB')

            if not result['issues']:
                result['status'] = 'excellent'
            elif len(result['issues']) == 1:
                result['status'] = 'good'
            else:
                result['status'] = 'warning'

        except Exception as e:
            result['status'] = 'critical'
            result['issues'].append(f'配置文件读取错误: {e}')

        return result

    def _check_storage_components(self) -> Dict[str, Any]:
        """检查存储组件文件"""
        result = {
            'status': 'unknown',
            'components': {},
            'issues': []
        }

        components = {
            'smart_storage_router': '/Users/xujian/Athena工作平台/storage-system/smart_storage_router.py',
            'parallel_storage_executor': '/Users/xujian/Athena工作平台/storage-system/parallel_storage_executor.py',
            'storage_performance_monitor': '/Users/xujian/Athena工作平台/storage-system/storage_performance_monitor.py'
        }

        total_size = 0
        for name, path in components.items():
            component_info = {'exists': False, 'size_kb': 0, 'modified': None}

            try:
                if Path(path).exists():
                    component_info['exists'] = True
                    stat = Path(path).stat()
                    component_info['size_kb'] = round(stat.st_size / 1024, 2)
                    component_info['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    total_size += stat.st_size
                else:
                    result['issues'].append(f'组件缺失: {name}')

            except Exception as e:
                result['issues'].append(f'组件检查失败 {name}: {e}')

            result['components'][name] = component_info

        result['total_code_size_kb'] = round(total_size / 1024, 2)

        if not result['issues']:
            result['status'] = 'excellent'
        elif len(result['issues']) == 1:
            result['status'] = 'warning'
        else:
            result['status'] = 'critical'

        return result

    def _analyze_log_files(self) -> Dict[str, Any]:
        """分析日志文件"""
        result = {
            'status': 'unknown',
            'log_files': {},
            'analysis': {},
            'issues': []
        }

        try:
            if not self.logs_path.exists():
                result['status'] = 'warning'
                result['issues'].append('日志目录不存在')
                return result

            # 查找相关日志文件
            log_patterns = [
                '*storage_performance*.json',
                '*storage_optimization*.json',
                '*storage_parameter*.md'
            ]

            total_size = 0
            file_count = 0
            latest_log = None

            for pattern in log_patterns:
                for log_file in self.logs_path.glob(pattern):
                    size = log_file.stat().st_size
                    modified = datetime.fromtimestamp(log_file.stat().st_mtime)

                    total_size += size
                    file_count += 1

                    result['log_files'][log_file.name] = {
                        'size_mb': round(size / (1024 * 1024), 2),
                        'modified': modified.isoformat()
                    }

                    if latest_log is None or modified > datetime.fromisoformat(latest_log['modified']):
                        latest_log = {
                            'name': log_file.name,
                            'size_mb': round(size / (1024 * 1024), 2),
                            'modified': modified.isoformat()
                        }

            result['analysis'] = {
                'total_files': file_count,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'latest_log': latest_log
            }

            # 检查日志文件是否过大
            if result['analysis']['total_size_mb'] > 50:
                result['issues'].append(f'日志文件总大小过大: {result["analysis"]["total_size_mb"]}MB')

            # 检查最近是否有日志记录
            if latest_log:
                last_modified = datetime.fromisoformat(latest_log['modified'])
                if (datetime.now() - last_modified).days > 7:
                    result['issues'].append('超过7天没有新的日志记录')
            else:
                result['issues'].append('没有找到日志文件')

            if not result['issues']:
                result['status'] = 'excellent'
            elif len(result['issues']) == 1:
                result['status'] = 'good'
            else:
                result['status'] = 'warning'

        except Exception as e:
            result['status'] = 'error'
            result['issues'].append(f'日志分析失败: {e}')

        return result

    def _analyze_performance_trend(self) -> Dict[str, Any]:
        """分析性能趋势"""
        result = {
            'status': 'unknown',
            'trend_data': {},
            'issues': []
        }

        try:
            # 查找性能监控报告
            perf_reports = list(self.logs_path.glob("*storage_performance_monitoring_report.json"))

            if len(perf_reports) < 2:
                result['status'] = 'insufficient_data'
                result['issues'].append('需要至少2个性能报告进行趋势分析')
                return result

            # 分析最近的两个报告
            perf_reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            recent_report = perf_reports[0]
            previous_report = perf_reports[1]

            with open(recent_report, 'r', encoding='utf-8') as f:
                recent_data = json.load(f)
            with open(previous_report, 'r', encoding='utf-8') as f:
                previous_data = json.load(f)

            # 比较性能指标
            recent_avg_time = recent_data.get('performance_statistics', {}).get('execution', {}).get('average_time', 0)
            previous_avg_time = previous_data.get('performance_statistics', {}).get('execution', {}).get('average_time', 0)

            recent_success_rate = recent_data.get('performance_statistics', {}).get('reliability', {}).get('average_success_rate', 0)
            previous_success_rate = previous_data.get('performance_statistics', {}).get('reliability', {}).get('average_success_rate', 0)

            # 计算趋势
            if previous_avg_time > 0:
                time_trend = ((recent_avg_time - previous_avg_time) / previous_avg_time) * 100
            else:
                time_trend = 0

            if previous_success_rate > 0:
                reliability_trend = (recent_success_rate - previous_success_rate) * 100
            else:
                reliability_trend = 0

            result['trend_data'] = {
                'response_time_trend_percent': round(time_trend, 2),
                'reliability_trend_percent': round(reliability_trend, 2),
                'recent_avg_time': round(recent_avg_time, 4),
                'recent_success_rate': round(recent_success_rate, 4)
            }

            # 分析趋势
            if time_trend > 10:
                result['issues'].append(f'响应时间恶化 {time_trend:.1f}%')
            elif time_trend < -5:
                result['trend_data']['improvement'] = f'响应时间改善 {abs(time_trend):.1f}%'

            if reliability_trend < -2:
                result['issues'].append(f'成功率下降 {abs(reliability_trend):.1f}%')

            if not result['issues']:
                result['status'] = 'excellent'
            elif len(result['issues']) == 1:
                result['status'] = 'warning'
            else:
                result['status'] = 'critical'

        except Exception as e:
            result['status'] = 'error'
            result['issues'].append(f'性能趋势分析失败: {e}')

        return result

    def _evaluate_optimization_effectiveness(self) -> Dict[str, Any]:
        """评估优化效果"""
        result = {
            'status': 'unknown',
            'effectiveness': {},
            'issues': []
        }

        try:
            # 查找优化报告
            optimization_reports = list(self.logs_path.glob("*storage_optimization_report.json"))

            if not optimization_reports:
                result['status'] = 'no_optimization_data'
                result['issues'].append('没有找到优化报告')
                return result

            # 读取最新的优化报告
            latest_report = max(optimization_reports, key=lambda x: x.stat().st_mtime)
            with open(latest_report, 'r', encoding='utf-8') as f:
                opt_data = json.load(f)

            # 分析优化效果
            test_results = opt_data.get('test_results', {})
            response_time_improvement = test_results.get('response_time', {}).get('improvement', '0%')
            concurrent_improvement = test_results.get('concurrent_capacity', {}).get('improvement', '0%')

            result['effectiveness'] = {
                'response_time_improvement': response_time_improvement,
                'concurrent_improvement': concurrent_improvement,
                'optimization_date': opt_data.get('optimization_summary', {}).get('timestamp', 'unknown'),
                'implemented_patterns': len(opt_data.get('implemented_patterns', []))
            }

            # 评估效果
            if '54.4%' in response_time_improvement or '75.0%' in concurrent_improvement:
                result['status'] = 'excellent'
                result['effectiveness']['rating'] = '优化效果显著'
            elif '%' in response_time_improvement:
                result['status'] = 'good'
                result['effectiveness']['rating'] = '优化效果良好'
            else:
                result['status'] = 'warning'
                result['issues'].append('优化效果不明显')

        except Exception as e:
            result['status'] = 'error'
            result['issues'].append(f'优化效果评估失败: {e}')

        return result

    def _calculate_overall_score(self, checks: Dict[str, Any]) -> int:
        """计算总体性能评分"""
        scores = {
            'excellent': 100,
            'good': 80,
            'warning': 60,
            'critical': 30,
            'error': 20,
            'insufficient_data': 50,
            'no_optimization_data': 40,
            'unknown': 50
        }

        total_score = 0
        check_count = 0

        for check_name, check_result in checks.items():
            status = check_result.get('status', 'unknown')
            total_score += scores.get(status, 50)
            check_count += 1

            # 如果有严重问题，额外扣分
            issues = check_result.get('issues', [])
            if issues:
                total_score -= len(issues) * 3

        if check_count == 0:
            return 50

        final_score = max(0, min(100, int(total_score / check_count)))
        return final_score

    def _get_overall_status(self, score: int) -> str:
        """获取总体状态"""
        if score >= 90:
            return 'excellent'
        elif score >= 80:
            return 'good'
        elif score >= 70:
            return 'acceptable'
        elif score >= 60:
            return 'needs_attention'
        else:
            return 'critical'

    def _generate_recommendations(self, checks: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 基于各个检查结果生成建议
        for check_name, check_result in checks.items():
            issues = check_result.get('issues', [])

            for issue in issues:
                if '配置' in issue:
                    recommendations.append("🔧 运行参数调优脚本: python3 scripts/tune_storage_parameters.py")
                elif '组件缺失' in issue:
                    recommendations.append("🔧 重新创建存储组件文件")
                elif '日志文件过大' in issue:
                    recommendations.append("🧹 清理旧的日志文件")
                elif '响应时间恶化' in issue:
                    recommendations.append("🚀 考虑增加并行工作线程数")
                elif '成功率下降' in issue:
                    recommendations.append("🔧 检查存储系统连接稳定性")
                elif '优化效果不明显' in issue:
                    recommendations.append("📊 重新运行性能监控和优化")

        # 添加通用建议
        if not recommendations:
            recommendations.append("✅ 系统运行良好，继续保持当前配置")
        else:
            recommendations.append("📈 建议定期运行性能检查: python3 scripts/simple_performance_check.py")

        return recommendations

    def _display_results(self, results: Dict[str, Any]) -> Any:
        """显示检查结果"""
        print(f"\n📊 存储系统性能检查结果")
        print(f"📅 检查时间: {results['timestamp']}")
        print(f"🎯 总体评分: {results['performance_score']}/100")
        print(f"📋 系统状态: {results['overall_status'].upper()}")
        print("=" * 60)

        # 显示各项检查结果
        for check_name, check_result in results['checks'].items():
            status_icon = {
                'excellent': '✅',
                'good': '🟢',
                'warning': '⚠️',
                'critical': '❌',
                'error': '💥',
                'insufficient_data': '❓',
                'no_optimization_data': '📊'
            }.get(check_result['status'], '❓')

            print(f"\n{status_icon} {check_name.upper().replace('_', ' ')}: {check_result['status'].upper()}")

            # 显示关键信息
            if check_name == 'configuration':
                details = check_result.get('details', {})
                print(f"   工作线程: {details.get('max_workers', 'N/A')}")
                print(f"   缓存大小: {details.get('cache_size_mb', 'N/A')}MB")
                print(f"   监控间隔: {details.get('monitoring_interval', 'N/A')}秒")

            elif check_name == 'components':
                print(f"   组件总数: {len(check_result.get('components', {}))}")
                print(f"   代码总大小: {check_result.get('total_code_size_kb', 'N/A')}KB")

            elif check_name == 'logs':
                analysis = check_result.get('analysis', {})
                if analysis:
                    print(f"   日志文件: {analysis.get('total_files', 0)}个")
                    print(f"   总大小: {analysis.get('total_size_mb', 0)}MB")

            elif check_name == 'performance_trend':
                trend_data = check_result.get('trend_data', {})
                if trend_data:
                    print(f"   响应时间趋势: {trend_data.get('response_time_trend_percent', 0)}%")
                    print(f"   可靠性趋势: {trend_data.get('reliability_trend_percent', 0)}%")

            elif check_name == 'optimization':
                effectiveness = check_result.get('effectiveness', {})
                if effectiveness:
                    print(f"   响应时间优化: {effectiveness.get('response_time_improvement', 'N/A')}")
                    print(f"   并发能力优化: {effectiveness.get('concurrent_improvement', 'N/A')}")

            # 显示问题
            issues = check_result.get('issues', [])
            for issue in issues:
                print(f"   ⚠️ {issue}")

        # 显示建议
        print(f"\n💡 优化建议:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"   {i}. {rec}")

    def _save_check_results(self, results: Dict[str, Any]) -> Any:
        """保存检查结果"""
        try:
            check_file = self.logs_path / f"storage_performance_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            check_file.parent.mkdir(exist_ok=True)

            with open(check_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n💾 检查结果已保存: {check_file}")
        except Exception as e:
            print(f"❌ 保存检查结果失败: {e}")

def main() -> None:
    """主函数"""
    print("🔍 存储系统简化性能检查工具")
    print("=" * 50)

    checker = SimplePerformanceChecker()
    results = checker.run_comprehensive_check()

    # 根据评分设置退出码
    if results['performance_score'] >= 80:
        exit_code = 0  # 正常
    elif results['performance_score'] >= 60:
        exit_code = 1  # 警告
    else:
        exit_code = 2  # 严重问题

    sys.exit(exit_code)

if __name__ == "__main__":
    main()