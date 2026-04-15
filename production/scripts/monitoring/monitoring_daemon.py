#!/usr/bin/env python3
"""
Athena工作平台监控守护进程
"""

from __future__ import annotations
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

sys.path.append(str(Path(__file__).parent.parent.parent))

from comprehensive_health_check import AthenaHealthChecker


class MonitoringDaemon:
    def __init__(self):
        self.health_checker = AthenaHealthChecker()
        self.running = False
        self.check_interval = 300  # 5分钟
        self.alert_config = self.load_alert_config()

    def load_alert_config(self) -> Any | None:
        """加载告警配置"""
        try:
            config_file = Path("/Users/xujian/Athena工作平台/production/config/infrastructure/infrastructure/monitoring/alert_config.json")
            with open(config_file, encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
            return {"alert_rules": {}, "notification_channels": {}}

    def check_alert_conditions(self, health_report) -> None:
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

    def send_alert(self, alert) -> None:
        """发送告警"""
        # 记录到日志
        log_file = Path("/Users/xujian/Athena工作平台/production/logs/alerts/alerts.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{alert['timestamp']}] [{alert['severity'].upper()}] {alert['component']}: {alert['message']}\n")

        # 这里可以添加更多通知方式，如邮件、Webhook等

    def monitoring_loop(self) -> Any:
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
                print("\n🛑 监控守护进程已停止")
                break
            except Exception as e:
                print(f"❌ 监控异常: {e}")
                time.sleep(60)  # 出错时等待1分钟再重试

    def start(self) -> None:
        """启动监控"""
        print("🚀 启动Athena监控守护进程")
        self.running = True
        self.monitoring_loop()

    def stop(self) -> None:
        """停止监控"""
        self.running = False

def main() -> None:
    """主函数"""
    print("🌸🐟 Athena工作平台监控守护进程")
    print("=" * 50)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("检查间隔: 5分钟")
    print("按 Ctrl+C 停止监控")
    print()

    daemon = MonitoringDaemon()
    daemon.start()

if __name__ == "__main__":
    main()
