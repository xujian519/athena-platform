#!/usr/bin/env python3
"""
学习模块性能监控脚本

实时监控学习模块守护进程的性能指标:
- 进程状态
- 内存使用
- CPU使用
- 运行时间
- 日志分析

作者: Athena平台团队
创建时间: 2026-01-28
版本: v1.0.0
"""

import json
import time
from datetime import datetime
from pathlib import Path

import psutil


class LearningModuleMonitor:
    """学习模块监控器"""

    def __init__(self, pid_file: str = "logs/learning_module.pid"):
        """初始化监控器"""
        self.pid_file = Path(pid_file)
        self.pid = self._read_pid()
        self.metrics_history = []

    def _read_pid(self) -> int | None:
        """读取PID文件"""
        if self.pid_file.exists():
            try:
                return int(self.pid_file.read_text().strip())
            except (OSError, ValueError):
                return None
        return None

    def get_process_info(self) -> dict | None:
        """获取进程信息"""
        if not self.pid:
            return None

        try:
            p = psutil.Process(self.pid)
            mem_info = p.memory_info()
            cpu_percent = p.cpu_percent(interval=0.1)

            return {
                "pid": self.pid,
                "status": p.status(),
                "cpu_percent": cpu_percent,
                "memory_rss_mb": mem_info.rss / 1024 / 1024,
                "memory_vms_mb": mem_info.vms / 1024 / 1024,
                "memory_percent": p.memory_percent(),
                "num_threads": p.num_threads(),
                "create_time": p.create_time(),
                "running_time_seconds": time.time() - p.create_time(),
            }
        except psutil.NoSuchProcess:
            return None
        except Exception as e:
            print(f"⚠️ 获取进程信息失败: {e}")
            return None

    def analyze_logs(self, log_file: str = "logs/learning_module.log", lines: int = 100) -> dict:
        """分析日志文件"""
        log_path = Path(log_file)
        if not log_path.exists():
            return {"error": "日志文件不存在"}

        try:
            # 读取最后N行
            with open(log_path, encoding='utf-8') as f:
                log_lines = f.readlines()[-lines:]

            # 统计日志级别
            stats = {
                "total_lines": len(log_lines),
                "info": sum(1 for line in log_lines if "INFO" in line),
                "warning": sum(1 for line in log_lines if "WARNING" in line),
                "error": sum(1 for line in log_lines if "ERROR" in line),
                "last_errors": [],
            }

            # 提取最近的错误
            for line in log_lines:
                if "ERROR" in line:
                    stats["last_errors"].append(line.strip()[:100])

            return stats
        except Exception as e:
            return {"error": str(e)}

    def evaluate_performance(self, info: dict) -> dict:
        """评估性能状态"""
        evaluation = {
            "overall": "unknown",
            "checks": [],
        }

        if not info:
            evaluation["overall"] = "error"
            evaluation["checks"].append({
                "name": "进程状态",
                "status": "❌",
                "message": "进程不存在"
            })
            return evaluation

        score = 0

        # 检查内存使用
        if info["memory_percent"] < 1:
            evaluation["checks"].append({
                "name": "内存使用",
                "status": "✅",
                "message": f"优秀 ({info['memory_percent']:.2f}%)",
                "value": info["memory_percent"]
            })
            score += 3
        elif info["memory_percent"] < 5:
            evaluation["checks"].append({
                "name": "内存使用",
                "status": "✅",
                "message": f"良好 ({info['memory_percent']:.2f}%)",
                "value": info["memory_percent"]
            })
            score += 2
        else:
            evaluation["checks"].append({
                "name": "内存使用",
                "status": "⚠️",
                "message": f"需要关注 ({info['memory_percent']:.2f}%)",
                "value": info["memory_percent"]
            })
            score += 1

        # 检查CPU使用
        if info["cpu_percent"] < 5:
            evaluation["checks"].append({
                "name": "CPU使用",
                "status": "✅",
                "message": f"正常 ({info['cpu_percent']:.1f}%)",
                "value": info["cpu_percent"]
            })
            score += 3
        else:
            evaluation["checks"].append({
                "name": "CPU使用",
                "status": "⚠️",
                "message": f"较高 ({info['cpu_percent']:.1f}%)",
                "value": info["cpu_percent"]
            })
            score += 1

        # 检查运行时间
        running_hours = info["running_time_seconds"] / 3600
        if running_hours > 1:
            evaluation["checks"].append({
                "name": "运行时间",
                "status": "✅",
                "message": f"稳定运行 {running_hours:.1f} 小时",
                "value": running_hours
            })
            score += 2
        else:
            evaluation["checks"].append({
                "name": "运行时间",
                "status": "ℹ️",
                "message": f"运行 {running_hours:.1f} 小时",
                "value": running_hours
            })
            score += 1

        # 总体评估
        if score >= 8:
            evaluation["overall"] = "优秀"
        elif score >= 6:
            evaluation["overall"] = "良好"
        elif score >= 4:
            evaluation["overall"] = "一般"
        else:
            evaluation["overall"] = "需要关注"

        return evaluation

    def print_report(self):
        """打印监控报告"""
        print("=" * 70)
        print("📊 学习模块性能监控报告")
        print("=" * 70)
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"PID文件: {self.pid_file}")
        print(f"PID: {self.pid or '未知'}")
        print()

        # 获取进程信息
        info = self.get_process_info()

        if info:
            print("📈 进程信息:")
            print(f"  状态:     {info['status']}")
            print(f"  运行时间: {info['running_time_seconds'] / 3600:.2f} 小时")
            print(f"  线程数:   {info['num_threads']}")
            print()

            print("💾 内存使用:")
            print(f"  物理内存: {info['memory_rss_mb']:.2f} MB")
            print(f"  虚拟内存: {info['memory_vms_mb']:.2f} MB")
            print(f"  内存占比: {info['memory_percent']:.2f}%")
            print()

            print("⚡ CPU使用:")
            print(f"  CPU占比:  {info['cpu_percent']:.1f}%")
            print()

            # 性能评估
            evaluation = self.evaluate_performance(info)
            print("🎯 性能评估:")
            print(f"  总体评级: {evaluation['overall']}")
            for check in evaluation["checks"]:
                print(f"  {check['status']} {check['name']}: {check['message']}")
        else:
            print("❌ 进程未运行")

        print()

        # 日志分析
        log_stats = self.analyze_logs()
        if "error" not in log_stats:
            print("📋 日志统计 (最近100行):")
            print(f"  INFO:    {log_stats['info']}")
            print(f"  WARNING: {log_stats['warning']}")
            print(f"  ERROR:   {log_stats['error']}")

            if log_stats["last_errors"]:
                print()
                print("⚠️ 最近的错误:")
                for error in log_stats["last_errors"][:3]:
                    print(f"  - {error}")

        print()
        print("=" * 70)

    def save_metrics(self, output_file: str = "logs/learning_metrics.json"):
        """保存指标到JSON文件"""
        info = self.get_process_info()
        log_stats = self.analyze_logs()
        evaluation = self.evaluate_performance(info) if info else None

        data = {
            "timestamp": datetime.now().isoformat(),
            "process_info": info,
            "log_stats": log_stats,
            "evaluation": evaluation,
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)

        # 读取历史数据
        history = []
        if output_path.exists():
            try:
                with open(output_path, encoding='utf-8') as f:
                    history = json.load(f)
            except (OSError, json.JSONDecodeError):
                pass

        # 添加新数据
        history.append(data)

        # 只保留最近100条记录
        history = history[-100:]

        # 保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="学习模块性能监控")
    parser.add_argument("--pid-file", default="logs/learning_module.pid", help="PID文件路径")
    parser.add_argument("--save", action="store_true", help="保存指标到JSON")
    parser.add_argument("--watch", action="store_true", help="持续监控模式")

    args = parser.parse_args()

    monitor = LearningModuleMonitor(args.pid_file)

    if args.watch:
        print("🔄 持续监控模式 (按Ctrl+C退出)")
        try:
            while True:
                monitor.print_report()
                monitor.save_metrics()
                time.sleep(60)  # 每分钟更新
        except KeyboardInterrupt:
            print("\n✅ 监控已停止")
    else:
        monitor.print_report()
        if args.save:
            monitor.save_metrics()
            print("💾 指标已保存到 logs/learning_metrics.json")


if __name__ == "__main__":
    main()
