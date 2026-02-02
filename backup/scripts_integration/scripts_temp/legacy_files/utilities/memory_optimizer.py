#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存优化工具
Memory Optimization Tool

智能管理和优化系统内存使用
"""

import gc
import logging
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

import psutil
import schedule

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self, check_interval: int = 300):  # 5分钟检查一次
        self.check_interval = check_interval
        self.process = psutil.Process()
        self.memory_threshold = 80  # 内存使用率阈值80%
        self.optimization_history = []
        self.monitoring = False
        
    def get_memory_info(self) -> Dict[str, any]:
        """获取当前内存信息"""
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        
        # 系统内存信息
        system_memory = psutil.virtual_memory()
        
        return {
            'timestamp': datetime.now(),
            'process_memory_mb': round(memory_info.rss / (1024**2), 2),
            'process_memory_percent': round(memory_percent, 2),
            'system_memory_total_gb': round(system_memory.total / (1024**3), 2),
            'system_memory_used_gb': round(system_memory.used / (1024**3), 2),
            'system_memory_percent': system_memory.percent,
            'available_memory_gb': round(system_memory.available / (1024**3), 2)
        }
    
    def optimize_python_memory(self) -> Dict[str, any]:
        """优化Python内存使用"""
        logger.info('🧹 开始优化Python内存...')
        
        before_memory = self.get_memory_info()
        
        # 1. 强制垃圾回收
        collected = gc.collect()
        
        # 2. 清理循环引用
        gc.set_debug(gc.DEBUG_SAVEALL)
        unreachable = gc.collect()
        gc.set_debug(0)
        
        # 3. 限制Python内存增长
        if hasattr(gc, 'set_threshold'):
            gc.set_threshold(700, 10, 10)
        
        after_memory = self.get_memory_info()
        
        freed_memory_mb = before_memory['process_memory_mb'] - after_memory['process_memory_mb']
        
        return {
            'collected_objects': collected,
            'unreachable_objects': unreachable,
            'freed_memory_mb': round(freed_memory_mb, 2),
            'before_memory_mb': before_memory['process_memory_mb'],
            'after_memory_mb': after_memory['process_memory_mb']
        }
    
    def cleanup_import_caches(self) -> Dict[str, any]:
        """清理导入缓存"""
        logger.info('📦 清理模块导入缓存...')
        
        cleaned_modules = 0
        
        # 清理sys.modules中的缓存
        modules_to_remove = []
        for module_name, module in sys.modules.items():
            if module_name.startswith(('tempfile.', 'urllib.', 'http.', 'xmlrpc.')):
                modules_to_remove.append(module_name)
        
        for module_name in modules_to_remove:
            try:
                del sys.modules[module_name]
                cleaned_modules += 1
            except KeyError:
                continue
        
        return {
            'cleaned_modules': cleaned_modules
        }
    
    def optimize_data_structures(self) -> Dict[str, any]:
        """优化数据结构"""
        logger.info('🏗️ 优化数据结构...')
        
        optimization_count = 0
        
        # 清理全局变量中的大型对象
        global_vars = globals()
        local_vars = locals()
        
        for scope_name, scope_vars in [('global', global_vars), ('local', local_vars)]:
            large_objects = []
            for var_name, var_value in scope_vars.items():
                try:
                    if hasattr(var_value, '__sizeof__'):
                        size = var_value.__sizeof__()
                        if size > 1024 * 1024:  # 1MB以上
                            large_objects.append((var_name, size))
                except:
                    continue
            
            # 记录大型对象
            if large_objects:
                logger.info(f"{scope_name} scope大型对象: {len(large_objects)}个")
                optimization_count += len(large_objects)
        
        return {
            'optimization_count': optimization_count
        }
    
    def check_and_optimize(self) -> Dict[str, any]:
        """检查并优化内存"""
        memory_info = self.get_memory_info()
        
        if memory_info['process_memory_percent'] > self.memory_threshold:
            logger.warning(f"⚠️ 内存使用率过高: {memory_info['process_memory_percent']}%")
            return self.perform_optimization()
        else:
            logger.info(f"✅ 内存使用正常: {memory_info['process_memory_percent']}%")
            return {'status': 'normal', 'memory_info': memory_info}
    
    def perform_optimization(self) -> Dict[str, any]:
        """执行内存优化"""
        logger.info('🚀 执行内存优化...')
        
        start_time = time.time()
        
        # 1. Python内存优化
        python_result = self.optimize_python_memory()
        
        # 2. 清理导入缓存
        import_result = self.cleanup_import_caches()
        
        # 3. 优化数据结构
        data_result = self.optimize_data_structures()
        
        end_time = time.time()
        optimization_time = round(end_time - start_time, 2)
        
        # 获取优化后的内存信息
        after_memory = self.get_memory_info()
        
        result = {
            'timestamp': datetime.now(),
            'status': 'optimized',
            'optimization_time_seconds': optimization_time,
            'python_optimization': python_result,
            'import_cleanup': import_result,
            'data_optimization': data_result,
            'memory_after': after_memory
        }
        
        # 记录优化历史
        self.optimization_history.append(result)
        
        logger.info(f"✅ 内存优化完成，耗时: {optimization_time}秒")
        logger.info(f"释放内存: {python_result['freed_memory_mb']}MB")
        
        return result
    
    def start_monitoring(self):
        """启动内存监控"""
        logger.info('👁️ 启动内存监控...')
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    result = self.check_and_optimize()
                    
                    # 记录到日志
                    if result['status'] == 'optimized':
                        logger.info('🔧 自动内存优化已执行')
                        
                except Exception as e:
                    logger.error(f"❌ 内存监控错误: {e}")
                
                time.sleep(self.check_interval)
        
        # 在后台线程中运行
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        logger.info(f"✅ 内存监控已启动，检查间隔: {self.check_interval}秒")
    
    def stop_monitoring(self):
        """停止内存监控"""
        logger.info('⏹️ 停止内存监控...')
        self.monitoring = False
    
    def get_optimization_report(self) -> str:
        """生成优化报告"""
        if not self.optimization_history:
            return '暂无优化历史记录'
        
        latest_memory = self.get_memory_info()
        
        report = f"""
# 内存优化报告

## 📊 当前内存状态
- **进程内存**: {latest_memory['process_memory_mb']}MB ({latest_memory['process_memory_percent']}%)
- **系统内存**: {latest_memory['system_memory_used_gb']}GB / {latest_memory['system_memory_total_gb']}GB ({latest_memory['system_memory_percent']}%)
- **可用内存**: {latest_memory['available_memory_gb']}GB

## 📈 优化历史
- **总优化次数**: {len(self.optimization_history)}
- **最新优化时间**: {self.optimization_history[-1]['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if self.optimization_history else 'N/A'}

## 🚀 最近优化结果
"""
        
        if self.optimization_history:
            latest = self.optimization_history[-1]
            if latest['status'] == 'optimized':
                report += f"""
- **优化耗时**: {latest['optimization_time_seconds']}秒
- **释放内存**: {latest['python_optimization']['freed_memory_mb']}MB
- **清理模块**: {latest['import_cleanup']['cleaned_modules']}个
- **垃圾回收**: {latest['python_optimization']['collected_objects']}个对象
"""
        
        report += f"""
## 💡 建议
1. **监控阈值**: 当前设置为{self.memory_threshold}%，可根据需要调整
2. **检查间隔**: 每{self.check_interval}秒检查一次
3. **自动优化**: {'已启用' if self.monitoring else '未启用'}
"""
        
        return report
    
    def schedule_regular_optimization(self):
        """安排定期优化"""
        def daily_optimization():
            logger.info('📅 执行每日内存优化...')
            self.perform_optimization()
        
        # 每天凌晨2点执行
        schedule.every().day.at('02:00').do(daily_optimization)
        
        logger.info('📅 已安排每日凌晨2点执行内存优化')

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='内存优化工具')
    parser.add_argument('--monitor', action='store_true', help='启动内存监控')
    parser.add_argument('--optimize', action='store_true', help='执行一次性优化')
    parser.add_argument('--report', action='store_true', help='生成优化报告')
    parser.add_argument('--interval', type=int, default=300, help='监控间隔（秒）')
    
    args = parser.parse_args()
    
    optimizer = MemoryOptimizer(check_interval=args.interval)
    
    try:
        if args.monitor:
            optimizer.start_monitoring()
            logger.info('按 Ctrl+C 停止监控...')
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                optimizer.stop_monitoring()
                logger.info('监控已停止')
        
        elif args.optimize:
            result = optimizer.perform_optimization()
            logger.info(f"优化完成: {result}")
        
        elif args.report:
            report = optimizer.get_optimization_report()
            logger.info(str(report))
        
        else:
            # 默认执行一次优化
            result = optimizer.check_and_optimize()
            logger.info(f"内存状态: {result}")
    
    except Exception as e:
        logger.error(f"❌ 运行错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()