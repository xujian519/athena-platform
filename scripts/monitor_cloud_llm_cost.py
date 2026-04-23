#!/usr/bin/env python3
"""
云端LLM成本监控脚本
实时跟踪API调用量和成本
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict
from collections import defaultdict


class CostTracker:
    """成本跟踪器"""

    # 价格表 (元/百万tokens)
    PRICING = {
        "deepseek": {"input": 1.0, "output": 1.0},
        "qwen": {"input": 0.8, "output": 0.8},
        "zhipu": {"input": 0.5, "output": 0.5},
        "claude": {"input": 3.0, "output": 15.0},
    }

    def __init__(self, log_file: str = "data/cloud_llm_usage.json"):
        """初始化成本跟踪器"""
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.usage_data = self._load_usage_data()

    def _load_usage_data(self) -> Dict:
        """加载使用数据"""
        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"calls": []}

    def _save_usage_data(self):
        """保存使用数据"""
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(self.usage_data, f, indent=2, ensure_ascii=False)

    def log_call(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        prompt_preview: str = ""
    ):
        """记录一次API调用"""
        pricing = self.PRICING.get(provider, {"input": 1.0, "output": 1.0})

        cost = (
            input_tokens * pricing["input"] / 1_000_000 +
            output_tokens * pricing["output"] / 1_000_000
        )

        call_record = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": round(cost, 6),
            "prompt_preview": prompt_preview[:100] if prompt_preview else ""
        }

        self.usage_data["calls"].append(call_record)
        self._save_usage_data()

        return call_record

    def get_stats(self, period: str = "today") -> Dict:
        """获取统计数据

        Args:
            period: 时间周期 (today, week, month, all)
        """
        now = datetime.now()
        if period == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start = now - timedelta(days=7)
        elif period == "month":
            start = now - timedelta(days=30)
        else:  # all
            start = datetime.fromtimestamp(0)

        filtered_calls = [
            call for call in self.usage_data["calls"]
            if datetime.fromisoformat(call["timestamp"]) >= start
        ]

        if not filtered_calls:
            return {
                "period": period,
                "calls": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "by_provider": {}
            }

        stats = {
            "period": period,
            "calls": len(filtered_calls),
            "total_tokens": sum(call["total_tokens"] for call in filtered_calls),
            "total_cost": sum(call["cost"] for call in filtered_calls),
            "by_provider": defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0.0})
        }

        for call in filtered_calls:
            provider = call["provider"]
            stats["by_provider"][provider]["calls"] += 1
            stats["by_provider"][provider]["tokens"] += call["total_tokens"]
            stats["by_provider"][provider]["cost"] += call["cost"]

        # 转换为普通dict
        stats["by_provider"] = dict(stats["by_provider"])

        return stats

    def print_report(self, period: str = "today"):
        """打印成本报告"""
        stats = self.get_stats(period)

        print(f"\n{'='*70}")
        print(f"💰 云端LLM成本报告 - {stats['period'].upper()}")
        print(f"{'='*70}")

        if stats["calls"] == 0:
            print("📊 本周期无API调用记录")
            return

        print(f"\n📈 总体统计:")
        print(f"  调用次数: {stats['calls']:,}")
        print(f"  总Token数: {stats['total_tokens']:,}")
        print(f"  总成本: ¥{stats['total_cost']:.4f}")
        print(f"  平均每次: ¥{stats['total_cost']/stats['calls']:.6f}")

        print(f"\n🏢 分服务商统计:")
        for provider, data in sorted(
            stats["by_provider"].items(),
            key=lambda x: x[1]["cost"],
            reverse=True
        ):
            print(f"\n  {provider.upper()}:")
            print(f"    调用次数: {data['calls']:,}")
            print(f"    Token数: {data['tokens']:,}")
            print(f"    成本: ¥{data['cost']:.4f}")

        # 对比本地模型
        local_cost = 3083 / 30  # 本地模型日均成本
        savings = local_cost - stats["total_cost"]
        savings_pct = (savings / local_cost) * 100

        print(f"\n💡 成本对比:")
        print(f"  本地模型日均成本: ¥{local_cost:.2f}")
        print(f"  云端模型实际成本: ¥{stats['total_cost']:.4f}")
        print(f"  节省: ¥{savings:.2f} ({savings_pct:.1f}%)")

        print(f"\n{'='*70}\n")

    def export_report(self, output_file: str = "reports/cost_report.json"):
        """导出成本报告"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "generated_at": datetime.now().isoformat(),
            "stats": {
                "today": self.get_stats("today"),
                "week": self.get_stats("week"),
                "month": self.get_stats("month"),
                "all": self.get_stats("all")
            }
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ 成本报告已导出: {output_path}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="云端LLM成本监控")
    parser.add_argument(
        "--period",
        choices=["today", "week", "month", "all"],
        default="today",
        help="统计周期"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="导出报告到文件"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="生成演示数据"
    )

    args = parser.parse_args()

    tracker = CostTracker()

    # 生成演示数据
    if args.demo:
        print("🎯 生成演示数据...\n")
        providers = ["deepseek", "qwen", "zhipu"]
        for i in range(100):
            provider = providers[i % 3]
            tracker.log_call(
                provider=provider,
                model="chat" if provider == "deepseek" else "turbo",
                input_tokens=1000 + i * 10,
                output_tokens=500 + i * 5,
                prompt_preview=f"测试调用 {i+1}"
            )
        print("✅ 演示数据生成完成\n")

    # 打印报告
    tracker.print_report(args.period)

    # 导出报告
    if args.export:
        tracker.export_report()


if __name__ == "__main__":
    main()
