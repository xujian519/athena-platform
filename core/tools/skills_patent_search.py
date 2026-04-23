#!/usr/bin/env python3
"""
技能集成：专利检索工具

集成 ~/skills/patent-search/scripts/search_patents.py

Author: Athena平台团队
Created: 2026-04-23
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(____)


class SkillsPatentSearchTool:
    """技能集成：专利检索工具"""

    def __init__(self):
        self.script_path = Path.home() / "skills/patent-search/scripts/search_patents.py"
        self.default_output_dir = Path("~/Documents/云熙工作/专利检索").expanduser()

    def search_by_description(
        self,
        description: str,
        num_results: int = 20,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        通过技术描述进行专利检索

        Args:
            description: 技术方案描述
            num_results: 结果数量（默认20）
            output_dir: 输出目录（可选）

        Returns:
            检索结果字典
        """
        try:
            # 构建命令
            cmd = [
                "python3",
                str(self.script_path),
                description,
                "-n", str(num_results)
            ]

            if output_dir:
                cmd.extend(["-o", output_dir])

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )

            # 解析输出
            output = result.stdout

            # 查找生成的JSON文件
            search_dir = Path(output_dir) if output_dir else self.default_output_dir
            json_files = list(search_dir.glob("检索数据_*.json"))

            if json_files:
                # 读取最新的JSON文件
                latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
                with open(latest_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                return {
                    "success": True,
                    "query": data.get("query"),
                    "search_url": data.get("search_url"),
                    "analysis": data.get("analysis"),
                    "report_path": str(search_dir / f"检索报告_{latest_json.stem.replace('检索数据_', '')}.md"),
                    "json_path": str(latest_json),
                    "timestamp": data.get("timestamp")
                }
            else:
                return {
                    "success": True,
                    "query": description,
                    "message": "检索完成，但未找到JSON文件",
                    "output": output
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "检索超时"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"检索失败: {e.stderr}"
            }
        except Exception as e:
            logger.exception("专利检索异常")
            return {
                "success": False,
                "error": f"检索异常: {str(e)}"
            }

    def search_by_query(
        self,
        query: str,
        num_results: int = 20,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        通过检索式进行专利检索

        Args:
            query: 检索式（如："(深度学习 OR 神经网络) AND 图像识别"）
            num_results: 结果数量（默认20）
            output_dir: 输出目录（可选）

        Returns:
            检索结果字典
        """
        try:
            # 构建命令
            cmd = [
                "python3",
                str(self.script_path),
                "--query", query,
                "-n", str(num_results)
            ]

            if output_dir:
                cmd.extend(["-o", output_dir])

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )

            # 查找生成的JSON文件
            search_dir = Path(output_dir) if output_dir else self.default_output_dir
            json_files = list(search_dir.glob("检索数据_*.json"))

            if json_files:
                # 读取最新的JSON文件
                latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
                with open(latest_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                return {
                    "success": True,
                    "query": data.get("query"),
                    "search_url": data.get("search_url"),
                    "analysis": data.get("analysis"),
                    "report_path": str(search_dir / f"检索报告_{latest_json.stem.replace('检索数据_', '')}.md"),
                    "json_path": str(latest_json),
                    "timestamp": data.get("timestamp")
                }
            else:
                return {
                    "success": True,
                    "query": query,
                    "search_url": f"https://patents.google.com/?q={query}",
                    "message": "检索完成"
                }

        except Exception as e:
            logger.exception("专利检索异常")
            return {
                "success": False,
                "error": f"检索异常: {str(e)}"
            }

    def extract_keywords(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取关键词

        Args:
            text: 技术描述文本

        Returns:
            关键词提取结果
        """
        # 调用检索工具并获取分析结果
        result = self.search_by_description(text, num_results=5)

        if result.get("success"):
            analysis = result.get("analysis", {})
            return {
                "success": True,
                "core_terms": analysis.get("core_terms", []),
                "raw_text": analysis.get("raw_text", "")
            }
        else:
            return result


# 创建工具实例
_patent_search_tool = None


def get_patent_search_tool() -> SkillsPatentSearchTool:
    """获取专利检索工具单例"""
    global _patent_search_tool
    if _patent_search_tool is None:
        _patent_search_tool = SkillsPatentSearchTool()
    return _patent_search_tool
