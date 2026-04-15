#!/usr/bin/env python3
"""
Athena工作平台健康监控系统设置
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class MonitoringSystemSetup:
    """健康监控系统设置器"""

    def __init__(self):
        self.base_path = Path("/Users/xujian/Athena工作平台/production")
        self.logs_dir = self.base_path / "logs"
        self.config_dir = self.base_path / "config" / "infrastructure/infrastructure/monitoring"

    def print_pink(self, message: str) -> Any:
        """打印粉色消息"""
        print(f"💖 {message}")

    def print_success(self, message: str) -> Any:
        """打印成功消息"""
        print(f"✅ {message}")

    def print_info(self, message: str) -> Any:
        """打印信息消息"""
        print(f"ℹ️ {message}")

    def setup_monitoring_directories(self) -> Any:
        """设置监控目录"""
        self.print_info("📁 创建监控目录结构...")

        monitoring_dirs = [
            self.config_dir,
            self.base_path / "dev/scripts" / "infrastructure/infrastructure/monitoring",
            self.logs_dir / "infrastructure/infrastructure/monitoring",
            self.logs_dir / "alerts",
            self.logs_dir / "metrics"
        ]

        for dir_path in monitoring_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

        self.print_success(f"✅ 监控目录已创建 ({len(monitoring_dirs)} 个)")

    def create_health_check_scripts(self) -> Any:
        """创建健康检查脚本"""
        self.print_info("🔍 创建健康检查脚本...")

        # 综合健康检查脚本
        health_check_script = self.base_path / "dev/scripts" / "infrastructure/infrastructure/monitoring" / "comprehensive_health_check.py"
        health_check_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台综合健康检查
"""

import json
import time
import subprocess
import requests
from datetime import datetime
from pathlib import Path

class AthenaHealthChecker:
    def __init__(self):
        self.check_results = {}
        self.start_time = datetime.now()

    def check_databases(self):
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

    def check_containers(self):
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

    def check_memory_system(self):
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

    def check_disk_space(self):
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

    def generate_health_report(self):
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
        for component_name, component_data in health_report['components'].items():
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
        print(f"\\n📊 健康检查摘要:")
        print(f"   整体状态: {health_report['overall_status'].upper()}")
        print(f"   组件总数: {health_report['summary']['total_components']}")
        print(f"   健康: {health_report['summary']['healthy']}")
        print(f"   警告: {health_report['summary']['warning']}")
        print(f"   异常: {health_report['summary']['unhealthy']}")
        print(f"   错误: {health_report['summary']['error']}")
        print(f"\\n📄 报告已保存: {report_file.name}")

        return health_report

def main():
    """主函数"""
    print("🌸🐟 Athena工作平台健康监控系统")
    print("=" * 50)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    checker = AthenaHealthChecker()
    report = checker.generate_health_report()

    print("\\n" + "=" * 50)
    if report['overall_status'] == 'healthy':
        print("✅ 系统状态健康！")
    elif report['overall_status'] == 'warning':
        print("⚠️ 系统状态一般，需要关注")
    else:
        print("❌ 系统状态异常，需要处理！")

if __name__ == "__main__":
    main()
'''

        with open(health_check_script, 'w', encoding='utf-8') as f:
            f.write(health_check_content)

        health_check_script.chmod(0o755)
        self.print_success("✅ 综合健康检查脚本已创建")

    def create_alert_system(self) -> Any:
        """创建告警系统"""
        self.print_info("🚨 创建告警系统...")

        alert_config = {
            "alert_rules": {
                "database_connection": {
                    "enabled": True,
                    "threshold": 3,
                    "severity": "critical",
                    "message": "数据库连接异常"
                },
                "container_failure": {
                    "enabled": True,
                    "threshold": 1,
                    "severity": "high",
                    "message": "关键容器停止运行"
                },
                "disk_space": {
                    "enabled": True,
                    "threshold": 90,
                    "severity": "warning",
                    "message": "磁盘空间不足"
                },
                "memory_system": {
                    "enabled": True,
                    "threshold": 50,
                    "severity": "medium",
                    "message": "记忆系统异常"
                },
                "response_time": {
                    "enabled": True,
                    "threshold": 5000,  # 5秒
                    "severity": "medium",
                    "message": "系统响应时间过长"
                }
            },
            "notification_channels": {
                "email": {
                    "enabled": False,
                    "recipients": [],
                    "smtp_config": {
                        "server": "smtp.example.com",
                        "port": 587,
                        "username": "",
                        "password": ""
                    }
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {}
                },
                "log": {
                    "enabled": True,
                    "level": "INFO"
                }
            },
            "escalation": {
                "enabled": True,
                "rules": {
                    "critical": {"immediate": True, "retry_interval": 60},
                    "high": {"immediate": False, "retry_interval": 300},
                    "medium": {"immediate": False, "retry_interval": 600},
                    "low": {"immediate": False, "retry_interval": 3600}
                }
            }
        }

        alert_config_file = self.config_dir / "alert_config.json"
        with open(alert_config_file, 'w', encoding='utf-8') as f:
            json.dump(alert_config, f, indent=2, ensure_ascii=False)

        self.print_success("✅ 告警配置已创建")

    def create_monitoring_daemon(self) -> Any:
        """创建监控守护进程"""
        self.print_info("🔄 创建监控守护进程...")

        daemon_script = self.base_path / "dev/scripts" / "infrastructure/infrastructure/monitoring" / "monitoring_daemon.py"
        daemon_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena工作平台监控守护进程
"""

import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from comprehensive_health_check import AthenaHealthChecker

class MonitoringDaemon:
    def __init__(self):
        self.health_checker = AthenaHealthChecker()
        self.running = False
        self.check_interval = 300  # 5分钟
        self.alert_config = self.load_alert_config()

    def load_alert_config(self):
        """加载告警配置"""
        try:
            config_file = Path("/Users/xujian/Athena工作平台/production/config/infrastructure/infrastructure/monitoring/alert_config.json")
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
            return {"alert_rules": {}, "notification_channels": {}}

    def check_alert_conditions(self, health_report):
        """检查告警条件"""
        alerts = []

        for component_name, component_data in health_report.get('components', {}).items():
            if component_name == 'databases':
                for db_name, db_data in component_data.items():
                    if db_data.get('status') == 'unhealthy':
                        alerts.append({
                            'severity': 'critical',
                            'component': f"database.{db_name}",
                            'message': f"{db_name} is unhealthy: {db_data.get('details', 'Unknown')}",
                            'timestamp': datetime.now().isoformat()
                        })
            elif component_name == 'containers':
                for container_name, container_data in component_data.items():
                    if container_data.get('status') in ['unhealthy', 'error']:
                        alerts.append({
                            'severity': 'high',
                            'component': f"container.{container_name}",
                            'message': f"Container {container_name} issue: {container_data.get('details', 'Unknown')}",
                            'timestamp': datetime.now().isoformat()
                        })
            elif component_name == 'disk_space':
                usage_percent = component_data.get('details', {}).get('usage_percent', 0)
                if usage_percent > 90:
                    alerts.append({
                        'severity': 'warning',
                        'component': 'disk_space',
                        'message': f"Disk usage critical: {usage_percent:.1f}%",
                        'timestamp': datetime.now().isoformat()
                    })

        return alerts

    def send_alert(self, alert):
        """发送告警"""
        # 记录到日志
        log_file = Path("/Users/xujian/Athena工作平台/production/logs/alerts/alerts.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{alert['timestamp']}] [{alert['severity'].upper()}] {alert['component']}: {alert['message']}\\n")

        # 这里可以添加更多通知方式，如邮件、Webhook等

    def monitoring_loop(self):
        """监控循环"""
        while self.running:
            try:
                print(f"🔄 执行健康检查 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")

                # 生成健康报告
                health_report = self.health_checker.generate_health_report()

                # 检查告警条件
                alerts = self.check_alert_conditions(health_report)

                # 发送告警
                for alert in alerts:
                    self.send_alert(alert)
                    print(f"🚨 告警: {alert['message']}")

                print(f"✅ 检查完成，状态: {health_report['overall_status']}")
                print(f"   下次检查: {(datetime.now() + timedelta(seconds=self.check_interval)).strftime('%H:%M:%S')}")
                print()

                # 等待下次检查
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                print("\\n🛑 监控守护进程已停止")
                break
            except Exception as e:
                print(f"❌ 监控异常: {e}")
                time.sleep(60)  # 出错时等待1分钟再重试

    def start(self):
        """启动监控"""
        print("🚀 启动Athena监控守护进程")
        self.running = True
        self.monitoring_loop()

    def stop(self):
        """停止监控"""
        self.running = False

def main():
    """主函数"""
    print("🌸🐟 Athena工作平台监控守护进程")
    print("=" * 50)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"检查间隔: 5分钟")
    print("按 Ctrl+C 停止监控")
    print()

    daemon = MonitoringDaemon()
    daemon.start()

if __name__ == "__main__":
    main()
'''

        with open(daemon_script, 'w', encoding='utf-8') as f:
            f.write(daemon_content)

        daemon_script.chmod(0o755)
        self.print_success("✅ 监控守护进程已创建")

    def create_startup_scripts(self) -> Any:
        """创建启动脚本"""
        self.print_info("🚀 创建监控启动脚本...")

        # 启动脚本
        start_script = self.base_path / "dev/scripts" / "start_monitoring.sh"
        start_content = '''#!/bin/bash
# 启动监控系统

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAEMON_SCRIPT="$SCRIPT_DIR/infrastructure/infrastructure/monitoring/monitoring_daemon.py"

echo "🚀 启动Athena监控系统..."

# 创建日志目录
mkdir -p /Users/xujian/Athena工作平台/production/logs/monitoring
mkdir -p /Users/xujian/Athena工作平台/production/logs/alerts

# 启动监控守护进程
nohup python3 "$DAEMON_SCRIPT" > /Users/xujian/Athena工作平台/production/logs/infrastructure/infrastructure/monitoring/daemon.log 2>&1 &
echo $! > /Users/xujian/Athena工作平台/production/logs/infrastructure/infrastructure/monitoring/daemon.pid

echo "✅ 监控系统已启动"
echo "📋 PID文件: /Users/xujian/Athena工作平台/production/logs/infrastructure/infrastructure/monitoring/daemon.pid"
echo "📋 日志文件: /Users/xujian/Athena工作平台/production/logs/infrastructure/infrastructure/monitoring/daemon.log"
echo "📋 告警日志: /Users/xujian/Athena工作平台/production/logs/alerts/alerts.log"
echo ""
echo "🛑 停止监控: ./dev/scripts/stop_monitoring.sh"
echo "📊 健康检查: python3 dev/scripts/infrastructure/infrastructure/monitoring/comprehensive_health_check.py"
'''

        with open(start_script, 'w', encoding='utf-8') as f:
            f.write(start_content)

        # 停止脚本
        stop_script = self.base_path / "dev/scripts" / "stop_monitoring.sh"
        stop_content = '''#!/bin/bash
# 停止监控系统

PID_FILE="/Users/xujian/Athena工作平台/production/logs/infrastructure/infrastructure/monitoring/daemon.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "🛑 停止监控系统 (PID: $PID)"
    kill $PID
    rm "$PID_FILE"
    echo "✅ 监控系统已停止"
else
    echo "❌ 监控系统未运行"
fi
'''

        with open(stop_script, 'w', encoding='utf-8') as f:
            f.write(stop_content)

        # 设置权限
        start_script.chmod(0o755)
        stop_script.chmod(0o755)

        self.print_success("✅ 监控启动脚本已创建")

    def main(self) -> None:
        """主函数"""
        print("🌸🐟 Athena工作平台健康监控系统设置")
        print("=" * 60)
        print(f"设置时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.setup_monitoring_directories()
        self.create_health_check_scripts()
        self.create_alert_system()
        self.create_monitoring_daemon()
        self.create_startup_scripts()

        print("\n" + "=" * 60)
        print("✅ 健康监控系统设置完成！")
        print("💖 小诺已为您建立了完整的监控和告警系统！")
        print("\n📋 使用方法:")
        print("   1. 启动监控系统: ./dev/scripts/start_monitoring.sh")
        print("   2. 手动健康检查: python3 dev/scripts/infrastructure/infrastructure/monitoring/comprehensive_health_check.py")
        print("   3. 停止监控系统: ./dev/scripts/stop_monitoring.sh")
        print("   4. 查看监控日志: tail -f logs/infrastructure/infrastructure/monitoring/daemon.log")
        print("   5. 查看告警日志: tail -f logs/alerts/alerts.log")

if __name__ == "__main__":
    monitoring_setup = MonitoringSystemSetup()
    monitoring_setup.main()
