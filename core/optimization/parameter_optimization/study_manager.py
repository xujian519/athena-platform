#!/usr/bin/env python3
from __future__ import annotations
"""
Study管理器
Study Manager

管理Optuna Study的生命周期:
- 创建/加载/删除Study
- Study列表和查询
- 结果导出和可视化

作者: Athena平台团队
创建时间: 2025-01-04
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import optuna
import pandas as pd

logger = logging.getLogger(__name__)


class StudyManager:
    """
    Optuna Study管理器

    功能:
    1. 管理多个Study
    2. 查询Study状态
    3. 导出优化结果
    4. 生成可视化报告
    """

    def __init__(self, storage_url: str = "sqlite:///data/optimization/optuna_studies.db"):
        """
        初始化Study管理器

        Args:
            storage_url: Optuna存储URL
        """
        self.storage_url = storage_url
        self.storage_dir = Path("data/optimization")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"📊 初始化Study管理器: {storage_url}")

    def list_studies(self, pattern: Optional[str] = None) -> list[dict[str, Any]]:
        """
        列出所有Study

        Args:
            pattern: 名称过滤模式(可选)

        Returns:
            Study信息列表
        """
        studies = optuna.get_all_study_summaries(storage=self.storage_url)

        result = []
        for study in studies:
            if pattern is None or pattern in study.study_name:
                result.append(
                    {
                        "study_name": study.study_name,
                        "direction": study.direction.name,
                        "n_trials": study.n_trials,
                        "best_value": study.best_value,
                        "datetime_start": study.datetime_start,
                    }
                )

        return result

    def get_study(self, study_name: str) -> optuna.Study:
        """
        获取指定Study

        Args:
            study_name: Study名称

        Returns:
            Study对象
        """
        try:
            study = optuna.load_study(study_name=study_name, storage=self.storage_url)
            logger.info(f"✅ 加载Study: {study_name}")
            return study
        except Exception as e:
            logger.error(f"加载Study失败: {e}")
            raise

    def delete_study(self, study_name: str) -> bool:
        """
        删除指定Study

        Args:
            study_name: Study名称

        Returns:
            是否成功
        """
        try:
            optuna.delete_study(study_name=study_name, storage=self.storage_url)
            logger.info(f"🗑️ 删除Study: {study_name}")
            return True
        except Exception as e:
            logger.error(f"删除Study失败: {e}")
            return False

    def export_study(
        self, study_name: str, format: str = "json", output_path: Path | None = None
    ) -> Path:
        """
        导出Study结果

        Args:
            study_name: Study名称
            format: 导出格式 ('json', 'csv', 'excel')
            output_path: 输出路径(可选)

        Returns:
            导出文件路径
        """
        study = self.get_study(study_name)

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.storage_dir / f"{study_name}_export_{timestamp}.{format}"

        # 准备数据
        trials_data = []
        for trial in study.trials:
            trial_data = {
                "number": trial.number,
                "value": trial.value,
                "state": trial.state.name,
                "datetime_start": trial.datetime_start,
                "datetime_complete": trial.datetime_complete,
                **trial.params,
            }
            trials_data.append(trial_data)

        # 导出
        if format == "json":
            import json

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(trials_data, f, indent=2, ensure_ascii=False, default=str)

        elif format in ["csv", "excel"]:

            df = pd.DataFrame(trials_data)

            if format == "csv":
                df.to_csv(output_path, index=False, encoding="utf-8")
            else:
                df.to_excel(output_path, index=False, engine="openpyxl")

        logger.info(f"📤 导出Study: {output_path}")
        return output_path

    def generate_report(self, study_name: str, output_path: Path | None = None) -> Path:
        """
        生成优化报告(HTML)

        Args:
            study_name: Study名称
            output_path: 输出路径(可选)

        Returns:
            报告文件路径
        """
        study = self.get_study(study_name)

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.storage_dir / f"{study_name}_report_{timestamp}.html"

        # 生成HTML报告
        html_content = self._generate_html_report(study)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"📊 生成报告: {output_path}")
        return output_path

    def _generate_html_report(self, study: optuna.Study) -> str:
        """生成HTML报告内容"""

        # 基础信息
        best_trial = study.best_trial
        best_params = best_trial.params

        # 优化历史图
        optuna.visualization.plot_optimization_history(study)

        # 参数重要性图
        importance = optuna.importance.get_param_importances(study)

        # 生成HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>优化报告: {study.study_name}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .metrics {{ display: flex; gap: 20px; margin: 20px 0; }}
                .metric {{ flex: 1; background: #f9f9f9; padding: 15px; border-radius: 5px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
                .best-params {{ background: #f9f9f9; padding: 15px; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #2196F3; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 优化报告: {study.study_name}</h1>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="metrics">
                <div class="metric">
                    <div>试验次数</div>
                    <div class="metric-value">{len(study.trials)}</div>
                </div>
                <div class="metric">
                    <div>最佳值</div>
                    <div class="metric-value">{best_trial.value:.4f}</div>
                </div>
                <div class="metric">
                    <div>优化方向</div>
                    <div class="metric-value">{study.direction.name}</div>
                </div>
            </div>

            <h2>📊 优化历史</h2>
            <div id="history-chart"></div>

            <h2>⚙️ 最佳参数</h2>
            <div class="best-params">
                <table>
                    <tr><th>参数</th><th>值</th></tr>
        """

        for param, value in best_params.items():
            html += f"<tr><td>{param}</td><td>{value}</td></tr>"

        html += """
                </table>
            </div>

            <h2>🎯 参数重要性</h2>
            <div class="best-params">
                <table>
                    <tr><th>参数</th><th>重要性</th></tr>
        """

        for param, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
            html += f"<tr><td>{param}</td><td>{imp:.4f}</td></tr>"

        html += """
                </table>
            </div>

            <script>
                // 这里可以添加交互式图表
            </script>
        </body>
        </html>
        """

        return html

    def compare_studies(self, study_names: list[str]) -> dict[str, Any]:
        """
        比较多个Study

        Args:
            study_names: Study名称列表

        Returns:
            比较结果
        """
        studies = []
        for name in study_names:
            try:
                study = self.get_study(name)
                studies.append(
                    {
                        "name": name,
                        "best_value": study.best_value,
                        "n_trials": len(study.trials),
                        "best_params": study.best_params,
                    }
                )
            except Exception as e:
                logger.warning(f"无法加载Study {name}: {e}")

        # 找出最佳Study
        best = max(studies, key=lambda x: x["best_value"]) if studies else None

        return {"studies": studies, "best_study": best}
