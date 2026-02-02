#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱数据完整性监控系统
作者：小娜
日期：2025-12-07
"""

import json
from core.async_main import async_main
import logging
from core.logging_config import setup_logging
import smtplib
import threading
import time
from datetime import datetime, timedelta
from email.mime.multipart import MimeMultipart
from email.mime.text import MimeText
from pathlib import Path
from typing import Any, Dict, List

import requests
import schedule

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation/logs/knowledge_graph_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = setup_logging()

class KnowledgeGraphMonitor:
    """知识图谱监控器"""

    def __init__(self, neo4j_uri: str = 'http://localhost:7474',
                 neo4j_user: str = 'neo4j', neo4j_password: str = 'password'):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.session = requests.Session()
        self.session.auth = (neo4j_user, neo4j_password)
        self.headers = {'Content-Type': 'application/json'}
        self.alerts = []
        self.reports_dir = Path('data/monitoring_reports')
        self.reports_dir.mkdir(exist_ok=True)

    def execute_query(self, query: str, parameters: Dict = None) -> Dict:
        """执行Cypher查询"""
        try:
            data = {'statements': [{'statement': query, 'parameters': parameters or {}}]}
            response = self.session.post(
                f"{self.neo4j_uri}/db/neo4j/tx/commit",
                headers=self.headers,
                json=data
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"查询执行失败: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"查询执行异常: {e}")
            return {}

    def check_database_health(self) -> Dict:
        """检查数据库健康状况"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'checks': {}
        }

        # 检查数据库连接
        try:
            result = self.execute_query('RETURN 1 as test')
            if result and result.get('results'):
                health['checks']['connection'] = 'OK'
            else:
                health['checks']['connection'] = 'FAILED'
                health['status'] = 'unhealthy'
        except Exception as e:
            health['checks']['connection'] = f"ERROR: {str(e)}"
            health['status'] = 'unhealthy'

        # 检查节点数量
        try:
            result = self.execute_query('MATCH (n) RETURN count(n) as count')
            if result and result.get('results'):
                node_count = result['results'][0]['data'][0]['row'][0]
                health['checks']['node_count'] = f"{node_count:,} nodes"
                health['total_nodes'] = node_count
            else:
                health['checks']['node_count'] = 'FAILED'
                health['status'] = 'warning'
        except Exception as e:
            health['checks']['node_count'] = f"ERROR: {str(e)}"
            health['status'] = 'warning'

        # 检查关系数量
        try:
            result = self.execute_query('MATCH ()-[r]->() RETURN count(r) as count')
            if result and result.get('results'):
                rel_count = result['results'][0]['data'][0]['row'][0]
                health['checks']['relationship_count'] = f"{rel_count:,} relationships"
                health['total_relationships'] = rel_count
            else:
                health['checks']['relationship_count'] = 'FAILED'
                health['status'] = 'warning'
        except Exception as e:
            health['checks']['relationship_count'] = f"ERROR: {str(e)}"
            health['status'] = 'warning'

        return health

    def check_data_integrity(self) -> Dict:
        """检查数据完整性"""
        integrity = {
            'timestamp': datetime.now().isoformat(),
            'issues': [],
            'metrics': {}
        }

        # 检查孤立节点
        try:
            result = self.execute_query("""
            MATCH (n)
            WHERE NOT (n)--()
            RETURN count(n) as count
            """)
            if result and result.get('results'):
                orphan_count = result['results'][0]['data'][0]['row'][0]
                integrity['metrics']['orphaned_nodes'] = orphan_count
                if orphan_count > 1000:  # 阈值可配置
                    integrity['issues'].append(f"孤立节点过多: {orphan_count}")
        except Exception as e:
            logger.error(f"检查孤立节点失败: {e}")

        # 检查重复节点
        try:
            result = self.execute_query("""
            MATCH (n:MemoryEntity)
            WITH n.name as name, collect(n) as nodes
            WHERE size(nodes) > 1
            RETURN count(*) as duplicate_groups, sum(size(nodes)) as total_duplicates
            """)
            if result and result.get('results'):
                data = result['results'][0]['data'][0]['row']
                integrity['metrics']['duplicate_groups'] = data[0]
                integrity['metrics']['total_duplicates'] = data[1]
                if data[0] > 0:
                    integrity['issues'].append(f"发现重复节点组: {data[0]}")
        except Exception as e:
            logger.error(f"检查重复节点失败: {e}")

        # 检查悬挂关系
        try:
            result = self.execute_query("""
            MATCH ()-[r]->()
            WHERE NOT exists(start_node(r)) OR NOT exists(end_node(r))
            RETURN count(r) as count
            """)
            if result and result.get('results'):
                dangling_count = result['results'][0]['data'][0]['row'][0]
                integrity['metrics']['dangling_relationships'] = dangling_count
                if dangling_count > 0:
                    integrity['issues'].append(f"发现悬挂关系: {dangling_count}")
        except Exception as e:
            logger.error(f"检查悬挂关系失败: {e}")

        # 检查空属性
        try:
            result = self.execute_query("""
            MATCH (n:MemoryEntity)
            WHERE n.name IS NULL OR n.name = ''
            RETURN count(n) as count
            """)
            if result and result.get('results'):
                empty_name_count = result['results'][0]['data'][0]['row'][0]
                integrity['metrics']['entities_without_name'] = empty_name_count
                if empty_name_count > 0:
                    integrity['issues'].append(f"记忆实体缺少名称: {empty_name_count}")
        except Exception as e:
            logger.error(f"检查空属性失败: {e}")

        return integrity

    def check_performance_metrics(self) -> Dict:
        """检查性能指标"""
        performance = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {}
        }

        # 检查查询性能
        start_time = time.time()
        try:
            self.execute_query('MATCH (n) RETURN count(n) LIMIT 100')
            query_time = time.time() - start_time
            performance['metrics']['avg_query_time'] = f"{query_time:.3f}s"
            if query_time > 1.0:
                performance['warning'] = '查询响应时间较慢'
        except Exception as e:
            performance['metrics']['avg_query_time'] = f"ERROR: {str(e)}"
            performance['warning'] = '查询性能检查失败'

        # 检查索引使用情况
        try:
            result = self.execute_query('SHOW INDEXES')
            if result and result.get('results'):
                indexes = result['results'][0].get('data', [])
                performance['metrics']['index_count'] = len(indexes)
                if len(indexes) < 5:
                    performance['suggestion'] = '建议添加更多索引以提升查询性能'
        except Exception as e:
            logger.error(f"检查索引失败: {e}")

        return performance

    def generate_report(self) -> Dict:
        """生成监控报告"""
        logger.info('生成监控报告...')

        report = {
            'report_id': f"monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'health': self.check_database_health(),
            'integrity': self.check_data_integrity(),
            'performance': self.check_performance_metrics()
        }

        # 汇总状态
        if report['health']['status'] != 'healthy' or report['integrity']['issues']:
            report['overall_status'] = 'alert'
        elif report['performance'].get('warning'):
            report['overall_status'] = 'warning'
        else:
            report['overall_status'] = 'ok'

        # 保存报告
        report_file = self.reports_dir / f"{report['report_id']}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"监控报告已保存: {report_file}")
        return report

    def send_alert(self, report: Dict) -> Any:
        """发送告警通知"""
        if report['overall_status'] in ['alert', 'warning']:
            alert_message = f"""
            知识图谱监控告警

            时间: {report['timestamp']}
            状态: {report['overall_status']}

            健康状态: {report['health']['status']}
            数据问题: {len(report['integrity']['issues'])}

            详细问题:
            {chr(10).join(report['integrity']['issues'])}

            请及时处理！
            """

            # 这里可以配置邮件、微信、钉钉等通知方式
            logger.warning(alert_message)
            self.alerts.append({
                'timestamp': datetime.now().isoformat(),
                'level': report['overall_status'],
                'message': alert_message
            })

    def run_monitoring(self) -> Any:
        """运行监控"""
        logger.info('开始运行知识图谱监控...')

        # 生成报告
        report = self.generate_report()

        # 发送告警
        self.send_alert(report)

        # 记录摘要
        logger.info(f"监控完成 - 状态: {report['overall_status']}")
        logger.info(f"节点数: {report['health'].get('total_nodes', 'N/A')}")
        logger.info(f"关系数: {report['health'].get('total_relationships', 'N/A')}")
        logger.info(f"问题数: {len(report['integrity']['issues'])}")

    def start_scheduler(self) -> Any:
        """启动定时监控"""
        # 每10分钟检查一次
        schedule.every(10).minutes.do(self.run_monitoring)

        # 每天生成详细报告
        schedule.every().day.at('09:00').do(self.generate_report)

        logger.info('监控调度器已启动')

        while True:
            schedule.run_pending()
            time.sleep(60)

def main() -> None:
    """主函数"""
    logger.info('启动知识图谱监控系统...')

    monitor = KnowledgeGraphMonitor()

    # 立即运行一次监控
    monitor.run_monitoring()

    # 启动定时监控
    try:
        monitor.start_scheduler()
    except KeyboardInterrupt:
        logger.info('监控系统已停止')

if __name__ == '__main__':
    main()