#!/usr/bin/env python3
"""
Athena工作平台综合健康检查
"""

from __future__ import annotations
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


class AthenaHealthChecker:
    def __init__(self):
        self.check_results = {}
        self.start_time = datetime.now()

    def check_databases(self) -> bool:
        """检查数据库状态"""
        print("🔍 检查数据库状态...")

        results = {}

        # PostgreSQL
        try:
            result = subprocess.run(['pg_isready'], capture_output=True, text=True)
            results['postgresql'] = {
                'status': 'healthy' if result.returncode == 0 else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'details': 'PostgreSQL service is running' if result.returncode == 0 else 'PostgreSQL service is down'
            }
        except Exception as e:
            results['postgresql'] = {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'details': f'Error checking PostgreSQL: {e}'
            }

        # Redis
        try:
            result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
            results['redis'] = {
                'status': 'healthy' if 'PONG' in result.stdout else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'details': 'Redis service is responsive' if 'PONG' in result.stdout else 'Redis service is down'
            }
        except Exception as e:
            results['redis'] = {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'details': f'Error checking Redis: {e}'
            }

        # Elasticsearch
        try:
            response = requests.get('http://localhost:9200/_cluster/health', timeout=10)
            if response.status_code == 200:
                health = response.json()
                results['elasticsearch'] = {
                    'status': 'healthy' if health['status'] in ['green', 'yellow'] else 'unhealthy',
                    'timestamp': datetime.now().isoformat(),
                    'details': f"Elasticsearch cluster status: {health['status']}"
                }
            else:
                results['elasticsearch'] = {
                    'status': 'unhealthy',
                    'timestamp': datetime.now().isoformat(),
                    'details': f"Elasticsearch HTTP status: {response.status_code}"
                }
        except Exception as e:
            results['elasticsearch'] = {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'details': f'Error checking Elasticsearch: {e}'
            }

        # Qdrant
        try:
            response = requests.get('http://localhost:6333/collections', timeout=10)
            if response.status_code == 200:
                collections = response.json()
                results['qdrant'] = {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'details': f"Qdrant service running with {len(collections.get('result', {}).get('collections', []))} collections"
                }
            else:
                results['qdrant'] = {
                    'status': 'unhealthy',
                    'timestamp': datetime.now().isoformat(),
                    'details': f"Qdrant HTTP status: {response.status_code}"
                }
        except Exception as e:
            results['qdrant'] = {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'details': f'Error checking Qdrant: {e}'
            }

        return results

    def check_containers(self) -> bool:
        """检查Docker容器状态"""
        print("🐳 检查容器状态...")

        results = {}
        essential_containers = [
            'athena_qdrant_main',
            'storage-system-redis-1',
            'athena_elasticsearch',
            'athena_postgres_legal'
        ]

        for container in essential_containers:
            try:
                result = subprocess.run(
                    ['infrastructure/infrastructure/docker', 'ps', '--filter', f'name={container}', '--format', '{{.Status}}'],
                    capture_output=True, text=True
                )

                if result.stdout.strip():
                    status_info = result.stdout.strip()
                    if 'Up' in status_info and 'healthy' in status_info:
                        results[container] = {
                            'status': 'healthy',
                            'timestamp': datetime.now().isoformat(),
                            'details': status_info
                        }
                    elif 'Up' in status_info:
                        results[container] = {
                            'status': 'warning',
                            'timestamp': datetime.now().isoformat(),
                            'details': status_info
                        }
                    else:
                        results[container] = {
                            'status': 'unhealthy',
                            'timestamp': datetime.now().isoformat(),
                            'details': 'Container is stopped'
                        }
                else:
                    results[container] = {
                        'status': 'unhealthy',
                        'timestamp': datetime.now().isoformat(),
                        'details': 'Container not found'
                    }
            except Exception as e:
                results[container] = {
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'details': f'Error checking container: {e}'
                }

        return results

    def check_memory_system(self) -> bool:
        """检查记忆系统"""
        print("🧠 检查记忆系统...")

        memory_path = Path("/Users/xujian/Athena工作平台/core/modules/memory/memory")
        layers = ["hot_memories", "warm_memories", "cold_memories", "eternal_memories"]

        results = {
            'total_layers': len(layers),
            'healthy_layers': 0,
            'total_files': 0,
            'details': {}
        }

        for layer in layers:
            layer_path = memory_path / layer
            if layer_path.exists():
                files = list(layer_path.glob("*.json"))
                results['total_files'] += len(files)

                if files:
                    results['healthy_layers'] += 1
                    results['details'][layer] = {
                        'files': len(files),
                        'size_mb': sum(f.stat().st_size for f in files) / 1024 / 1024,
                        'latest_file': max(files, key=lambda f: f.stat().st_mtime).name if files else None
                    }
                else:
                    results['details'][layer] = {
                        'files': 0,
                        'size_mb': 0,
                        'latest_file': None
                    }
            else:
                results['details'][layer] = {
                    'files': 0,
                    'size_mb': 0,
                    'latest_file': None
                }

        # 计算整体健康状态
        health_percentage = (results['healthy_layers'] / results['total_layers']) * 100

        results['status'] = 'healthy' if health_percentage >= 75 else 'warning' if health_percentage >= 50 else 'unhealthy'
        results['health_percentage'] = health_percentage
        results['timestamp'] = datetime.now().isoformat()

        return results

    def check_disk_space(self) -> bool:
        """检查磁盘空间"""
        print("💿 检查磁盘空间...")

        try:
            import psutil

            disk = psutil.disk_usage('/')
            free_gb = disk.free / 1024 / 1024 / 1024
            total_gb = disk.total / 1024 / 1024 / 1024
            used_percent = (disk.used / disk.total) * 100

            results = {
                'status': 'healthy' if used_percent < 90 else 'warning' if used_percent < 95 else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'details': {
                    'total_gb': round(total_gb, 1),
                    'used_gb': round(disk.used / 1024 / 1024 / 1024, 1),
                    'free_gb': round(free_gb, 1),
                    'usage_percent': round(used_percent, 1)
                }
            }

        except ImportError:
            results = {
                'status': 'unknown',
                'timestamp': datetime.now().isoformat(),
                'details': 'psutil not available for disk space check'
            }
        except Exception as e:
            results = {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'details': f'Error checking disk space: {e}'
            }

        return results

    def generate_health_report(self) -> Any:
        """生成健康报告"""
        print("📊 生成健康报告...")

        health_report = {
            'check_time': datetime.now().isoformat(),
            'check_duration': (datetime.now() - self.start_time).total_seconds(),
            'overall_status': 'unknown',
            'components': {},
            'summary': {
                'total_components': 0,
                'healthy': 0,
                'warning': 0,
                'unhealthy': 0,
                'error': 0
            }
        }

        # 执行各项检查
        health_report['components']['databases'] = self.check_databases()
        health_report['components']['containers'] = self.check_containers()
        health_report['components']['memory_system'] = self.check_memory_system()
        health_report['components']['disk_space'] = self.check_disk_space()

        # 统计结果
        for _component_name, component_data in health_report['components'].items():
            if isinstance(component_data, dict):
                status = component_data.get('status', 'unknown')
                health_report['summary']['total_components'] += 1
                health_report['summary'][status] = health_report['summary'].get(status, 0) + 1

        # 确定整体状态
        healthy_count = health_report['summary']['healthy']
        total_count = health_report['summary']['total_components']

        if total_count == 0:
            health_report['overall_status'] = 'unknown'
        elif healthy_count == total_count:
            health_report['overall_status'] = 'healthy'
        elif healthy_count >= total_count * 0.75:
            health_report['overall_status'] = 'warning'
        else:
            health_report['overall_status'] = 'unhealthy'

        # 保存报告
        reports_dir = Path("/Users/xujian/Athena工作平台/production/logs/infrastructure/monitoring")
        reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = reports_dir / f"health_report_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(health_report, f, indent=2, ensure_ascii=False, default=str)

        # 显示摘要
        print("\n📊 健康检查摘要:")
        print(f"   整体状态: {health_report['overall_status'].upper()}")
        print(f"   组件总数: {health_report['summary']['total_components']}")
        print(f"   健康: {health_report['summary']['healthy']}")
        print(f"   警告: {health_report['summary']['warning']}")
        print(f"   异常: {health_report['summary']['unhealthy']}")
        print(f"   错误: {health_report['summary']['error']}")
        print(f"\n📄 报告已保存: {report_file.name}")

        return health_report

def main() -> None:
    """主函数"""
    print("🌸🐟 Athena工作平台健康监控系统")
    print("=" * 50)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    checker = AthenaHealthChecker()
    report = checker.generate_health_report()

    print("\n" + "=" * 50)
    if report['overall_status'] == 'healthy':
        print("✅ 系统状态健康！")
    elif report['overall_status'] == 'warning':
        print("⚠️ 系统状态一般，需要关注")
    else:
        print("❌ 系统状态异常，需要处理！")

if __name__ == "__main__":
    main()
