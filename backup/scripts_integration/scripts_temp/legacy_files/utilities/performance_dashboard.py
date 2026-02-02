#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统性能监控仪表板
System Performance Dashboard

实时监控系统性能指标
"""

import curses
import json
import logging
import os
import sys
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import psutil

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceDashboard:
    """性能监控仪表板"""
    
    def __init__(self, history_size: int = 60):  # 保存60秒历史
        self.history_size = history_size
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.disk_history = deque(maxlen=history_size)
        self.start_time = datetime.now()
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 内存信息
        memory = psutil.virtual_memory()
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        
        # 网络信息
        network = psutil.net_io_counters()
        
        # 进程信息
        process_count = len(psutil.pids())
        
        return {
            'timestamp': datetime.now(),
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count,
                'load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            },
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'percent': memory.percent
            },
            'disk': {
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'percent': round((disk.used / disk.total) * 100, 2)
            },
            'network': {
                'bytes_sent_mb': round(network.bytes_sent / (1024**2), 2),
                'bytes_recv_mb': round(network.bytes_recv / (1024**2), 2),
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            },
            'process': {
                'count': process_count,
                'active': sum(1 for p in psutil.process_iter() if p.status() == psutil.STATUS_RUNNING)
            }
        }
    
    def update_history(self, metrics: Dict[str, Any]):
        """更新历史数据"""
        self.cpu_history.append(metrics['cpu']['percent'])
        self.memory_history.append(metrics['memory']['percent'])
        self.disk_history.append(metrics['disk']['percent'])
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """获取性能分析"""
        if len(self.cpu_history) < 10:
            return {'status': 'insufficient_data'}
        
        cpu_avg = sum(self.cpu_history) / len(self.cpu_history)
        memory_avg = sum(self.memory_history) / len(self.memory_history)
        disk_avg = sum(self.disk_history) / len(self.disk_history)
        
        cpu_max = max(self.cpu_history)
        memory_max = max(self.memory_history)
        disk_max = max(self.disk_history)
        
        # 性能评分 (0-100)
        cpu_score = max(0, 100 - cpu_avg)
        memory_score = max(0, 100 - memory_avg)
        disk_score = max(0, 100 - disk_avg)
        
        overall_score = (cpu_score + memory_score + disk_score) / 3
        
        # 状态判断
        if overall_score >= 80:
            status = '优秀'
            color = 'green'
        elif overall_score >= 60:
            status = '良好'
            color = 'yellow'
        elif overall_score >= 40:
            status = '一般'
            color = 'orange'
        else:
            status = '较差'
            color = 'red'
        
        return {
            'status': status,
            'color': color,
            'overall_score': round(overall_score, 1),
            'cpu': {'avg': round(cpu_avg, 1), 'max': cpu_max, 'score': round(cpu_score, 1)},
            'memory': {'avg': round(memory_avg, 1), 'max': memory_max, 'score': round(memory_score, 1)},
            'disk': {'avg': round(disk_avg, 1), 'max': disk_max, 'score': round(disk_score, 1)},
            'uptime': str(datetime.now() - self.start_time).split('.')[0]
        }
    
    def generate_text_dashboard(self) -> str:
        """生成文本仪表板"""
        metrics = self.get_system_metrics()
        self.update_history(metrics)
        analysis = self.get_performance_analysis()
        
        dashboard = f"""
{'='*60}
🖥️  Athena系统性能监控仪表板
{'='*60}

⏰ 时间: {metrics['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
⏱️ 运行时间: {analysis.get('uptime', 'N/A')}

📊 整体性能状态: {analysis.get('status', 'N/A')} ({analysis.get('overall_score', 'N/A')}/100)

{'─'*60}
💻 CPU使用率: {metrics['cpu']['percent']}%
   - 核心数: {metrics['cpu']['count']}
   - 平均负载: {', '.join([f'{x:.2f}' for x in metrics['cpu']['load_avg']])}

🧠 内存使用率: {metrics['memory']['percent']}%
   - 已用: {metrics['memory']['used_gb']}GB / {metrics['memory']['total_gb']}GB
   - 可用: {metrics['memory']['available_gb']}GB

💾 磁盘使用率: {metrics['disk']['percent']}%
   - 已用: {metrics['disk']['used_gb']}GB / {metrics['disk']['total_gb']}GB
   - 空闲: {metrics['disk']['free_gb']}GB

🌐 网络流量:
   - 发送: {metrics['network']['bytes_sent_mb']}MB ({metrics['network']['packets_sent']}包)
   - 接收: {metrics['network']['bytes_recv_mb']}MB ({metrics['network']['packets_recv']}包)

🔌 进程统计:
   - 总数: {metrics['process']['count']}
   - 运行中: {metrics['process']['active']}

{'─'*60}
📈 最近{len(self.cpu_history)}秒平均值:
   - CPU: {analysis.get('cpu', {}).get('avg', 'N/A')}%
   - 内存: {analysis.get('memory', {}).get('avg', 'N/A')}%
   - 磁盘: {analysis.get('disk', {}).get('avg', 'N/A')}%

💡 性能建议:
"""
        
        # 添加性能建议
        if metrics['cpu']['percent'] > 80:
            dashboard += "   - CPU使用率过高，建议检查高CPU占用进程\n"
        
        if metrics['memory']['percent'] > 85:
            dashboard += "   - 内存使用率过高，建议释放内存或增加内存\n"
        
        if metrics['disk']['percent'] > 90:
            dashboard += "   - 磁盘空间不足，建议清理不必要文件\n"
        
        if len(self.cpu_history) >= 10 and all(cpu < 20 for cpu in list(self.cpu_history)[-10:]):
            dashboard += "   - 系统负载较低，运行正常\n"
        
        dashboard += f"\n{'='*60}\n"
        
        return dashboard
    
    def save_metrics_to_file(self, metrics: Dict[str, Any], filename: str = None):
        """保存指标到文件"""
        if filename is None:
            filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 转换datetime为字符串
        metrics_copy = metrics.copy()
        metrics_copy['timestamp'] = metrics['timestamp'].isoformat()
        
        metrics_dir = Path('metrics')
        metrics_dir.mkdir(exist_ok=True)
        
        filepath = metrics_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics_copy, f, ensure_ascii=False, indent=2)
        
        return filepath

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='系统性能监控仪表板')
    parser.add_argument('--watch', action='store_true', help='持续监控模式')
    parser.add_argument('--interval', type=int, default=5, help='监控间隔（秒）')
    parser.add_argument('--save', action='store_true', help='保存指标到文件')
    
    args = parser.parse_args()
    
    dashboard = PerformanceDashboard()
    
    try:
        if args.watch:
            logger.info('🚀 启动系统性能监控...')
            logger.info('按 Ctrl+C 退出监控')
            print()
            
            try:
                while True:
                    # 清屏
                    os.system('clear' if os.name == 'posix' else 'cls')
                    
                    # 显示仪表板
                    text_dashboard = dashboard.generate_text_dashboard()
                    logger.info(str(text_dashboard))
                    
                    # 保存指标
                    if args.save:
                        metrics = dashboard.get_system_metrics()
                        filepath = dashboard.save_metrics_to_file(metrics)
                        logger.info(f"指标已保存到: {filepath}")
                    
                    time.sleep(args.interval)
                    
            except KeyboardInterrupt:
                logger.info("\n监控已停止")
        
        else:
            # 显示一次性仪表板
            text_dashboard = dashboard.generate_text_dashboard()
            logger.info(str(text_dashboard))
            
            if args.save:
                metrics = dashboard.get_system_metrics()
                filepath = dashboard.save_metrics_to_file(metrics)
                logger.info(f"\n📁 指标已保存到: {filepath}")
    
    except Exception as e:
        logger.error(f"❌ 运行错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()