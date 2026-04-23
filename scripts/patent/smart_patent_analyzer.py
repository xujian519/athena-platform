#!/usr/bin/env python3
"""
深度技术分析脚本 - 支持所有GLM模型
智能选择最适合的模型进行专利分析

Author: Athena平台团队
Date: 2026-04-22
Models: glm-4-plus, glm-4-0520, glm-4-air, glm-4-flash
"""

import asyncio
import json
import logging
import sys
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ai.llm.glm_model_selector import PerformancePreference, TaskType
from core.ai.llm.unified_glm_client import UnifiedGLMClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SmartPatentAnalyzer:
    """智能专利分析器 - 支持所有GLM模型"""

    def __init__(
        self,
        ocr_output_dir: str,
        analysis_output_dir: str,
        model: str | None = None,
        preference: str = "quality",
        api_key: str | None = None
    ):
        """
        初始化分析器

        Args:
            ocr_output_dir: OCR输出目录
            analysis_output_dir: 分析结果输出目录
            model: 指定模型（可选：glm-4-plus, glm-4-air, glm-4-flash等）
            preference: 性能偏好（quality/balanced/speed/cost）
            api_key: GLM API密钥
        """
        self.ocr_output_dir = Path(ocr_output_dir)
        self.analysis_output_dir = Path(analysis_output_dir)

        # 性能偏好映射
        preference_map = {
            "quality": PerformancePreference.QUALITY,
            "balanced": PerformancePreference.BALANCED,
            "speed": PerformancePreference.SPEED,
            "cost": PerformancePreference.COST
        }

        pref = preference_map.get(preference, PerformancePreference.BALANCED)

        # 创建统一GLM客户端
        if model:
            # 使用指定模型
            self.client = UnifiedGLMClient(api_key=api_key, model=model)
            logger.info(f"✅ 使用指定模型: {model}")
        else:
            # 自动选择模型
            self.client = UnifiedGLMClient(
                api_key=api_key,
                task_type=TaskType.PATENT_DEEP_ANALYSIS,
                preference=pref
            )
            logger.info(f"✅ 自动选择模型: {self.client.model} (偏好: {preference})")

        # 创建输出目录
        self.analysis_output_dir.mkdir(parents=True, exist_ok=True)

        # 目标专利信息
        self.target_patent = {
            "patent_number": "201921401279.9",
            "title": "包装机物品传送装置的物料限位板自动调节机构",
            "application_date": "2019-03-26",
            "grant_date": "2020-01-17",
            "type": "实用新型"
        }

        # 目标专利权利要求1的核心技术特征
        self.target_claim1_features = [
            "机架",
            "两块可滑动地安装在机架上的物料限位板",
            "物料传送带安装空间",
            "物料限位板斜向间距调节机构",
            "驱动单元",
            "纵向调节单元",
            "斜向调节单元",
            "两个安装架",
            "两条斜向滑轨",
            "两个滑动座",
            "两条斜向滑轨的间距从左往右逐渐缩短"  # 核心创新点
        ]

        # 统计信息
        self.stats = {
            "total_files": 0,
            "analyzed": 0,
            "failed": 0,
            "start_time": None,
            "end_time": None,
            "total_tokens": 0,
            "total_cost": 0.0,
            "model_used": self.client.model
        }

    def find_text_files(self) -> list[Path]:
        """查找所有OCR生成的TXT文件"""
        logger.info(f"🔍 扫描OCR输出目录: {self.ocr_output_dir}")

        txt_files = list(self.ocr_output_dir.rglob("*.txt"))

        # 过滤掉报告文件
        txt_files = [f for f in txt_files if "批量处理报告" not in f.name]

        logger.info(f"✅ 找到 {len(txt_files)} 个TXT文件")

        return sorted(txt_files)

    async def analyze_single_patent(self, txt_path: Path) -> dict[str, Any]:
        """
        分析单个专利文件

        Args:
            txt_path: TXT文件路径

        Returns:
            分析结果
        """
        file_start_time = asyncio.get_event_loop().time()

        try:
            logger.info(f"🔄 分析: {txt_path.name}")

            # 读取OCR文本（限制前3000字符）
            patent_text = txt_path.read_text(encoding="utf-8")[:3000]

            # 提取专利号
            patent_number = txt_path.stem

            # 构建分析提示词
            system_prompt = """你是一位资深的专利技术专家，专门从事专利无效宣告分析工作。

你的任务是从对比文件（现有技术）中提取关键技术特征，并与目标专利进行对比分析。

分析要求：
1. 准确识别对比文件的技术领域、发明主题、技术问题
2. 提取对比文件的所有技术特征（特别是结构、组件、连接关系）
3. 识别与目标专利权利要求1的相同/相似/不同特征
4. 评估该对比文件作为无效证据的价值

输出格式：JSON"""

            user_prompt = f"""请对以下对比文件进行深度技术分析。

## 目标专利信息

专利号：{self.target_patent['patent_number']}
专利名称：{self.target_patent['title']}
专利类型：{self.target_patent['type']}

## 目标专利权利要求1的核心技术特征

{json.dumps(self.target_claim1_features, ensure_ascii=False, indent=2)}

## 对比文件内容

专利号：{patent_number}

全文内容：

{patent_text}

---

请以JSON格式输出分析结果，包含以下字段：

{{
  "patent_number": "对比文件专利号",
  "technical_field": "技术领域",
  "invention_title": "发明主题",
  "technical_problem": "要解决的技术问题",
  "key_features": [
    "关键特征1",
    "关键特征2",
    ...
  ],
  "claim1_comparison": {{
    "same_features": ["与目标专利相同的特征"],
    "similar_features": ["与目标专利相似的特征"],
    "different_features": ["与目标专利不同的特征"]
  }},
  "evidence_value": "证据价值评估（高/中/低）",
  "evidence_reason": "证据价值评估理由",
  "invalidation_grounds": ["可作为的无效理由（novelty/creativity）"],
  "confidence": "评估置信度（0-100）"
}}

请严格按照JSON格式输出，不要包含任何其他内容。"""

            # 调用GLM API（包含使用统计）
            result = await self.client.generate_with_usage(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=2500
            )

            # 更新统计
            self.stats["total_tokens"] += result['usage']['total_tokens']
            self.stats["total_cost"] += result['cost']['total']

            # 解析JSON响应
            try:
                content = result['content']

                # 提取JSON部分
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content.strip()

                analysis_result = json.loads(json_str)
                analysis_result["source_file"] = str(txt_path)
                analysis_result["analysis_time"] = asyncio.get_event_loop().time() - file_start_time
                analysis_result["success"] = True
                analysis_result["tokens_used"] = result['usage']['total_tokens']
                analysis_result["cost"] = result['cost']['total']

                logger.info(f"  ✅ 分析完成: {patent_number} (证据价值: {analysis_result.get('evidence_value', 'N/A')}, 耗时: {analysis_result['analysis_time']:.1f}秒, 成本: ¥{analysis_result['cost']:.4f})")

                return analysis_result

            except json.JSONDecodeError as e:
                logger.error(f"  ❌ JSON解析失败: {patent_number} - {e}")

                # 返回原始响应
                return {
                    "patent_number": patent_number,
                    "source_file": str(txt_path),
                    "success": False,
                    "error": "JSON解析失败",
                    "raw_response": result['content'][:500],
                    "analysis_time": asyncio.get_event_loop().time() - file_start_time
                }

        except Exception as e:
            logger.error(f"  ❌ 分析失败: {txt_path.name} - {e}")

            return {
                "patent_number": txt_path.stem,
                "source_file": str(txt_path),
                "success": False,
                "error": str(e),
                "analysis_time": asyncio.get_event_loop().time() - file_start_time
            }

    async def analyze_batch(self, txt_files: list[Path]) -> dict[str, Any]:
        """批量分析专利文件"""
        self.stats["start_time"] = asyncio.get_event_loop().time()
        self.stats["total_files"] = len(txt_files)

        model_info = self.client.get_model_info()

        logger.info("=" * 80)
        logger.info(f"🚀 开始深度技术分析: {len(txt_files)} 个专利")
        logger.info(f"   OCR输出目录: {self.ocr_output_dir}")
        logger.info(f"   分析输出目录: {self.analysis_output_dir}")
        logger.info(f"   使用模型: {self.client.model} ({model_info.get('name', 'Unknown')})")
        logger.info(f"   模型质量: {model_info.get('quality', 'Unknown')}")
        logger.info(f"   模型速度: {model_info.get('speed', 'Unknown')}")
        logger.info("=" * 80)

        # 顺序分析
        results = []

        for idx, txt_file in enumerate(txt_files, 1):
            logger.info(f"📊 进度: {idx}/{len(txt_files)} ({idx/len(txt_files)*100:.1f}%)")

            result = await self.analyze_single_patent(txt_file)
            results.append(result)

            if result["success"]:
                self.stats["analyzed"] += 1
            else:
                self.stats["failed"] += 1

            # 每分析10个保存一次中间结果
            if idx % 10 == 0:
                self.save_intermediate_results(results)
                logger.info(f"💾 已保存中间结果: {idx}个文件")

        self.stats["end_time"] = asyncio.get_event_loop().time()

        return {
            "results": results,
            "stats": self.stats
        }

    def save_intermediate_results(self, results: list[dict[str, Any]):
        """保存中间结果"""
        output_file = self.analysis_output_dir / f"中间结果_{self.client.model}_{len(results)}个文件.json"
        output_file.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def save_final_results(self, batch_result: dict[str, Any]):
        """保存最终结果"""
        # 保存JSON结果
        output_json = self.analysis_output_dir / f"深度技术分析完整结果_{self.client.model}.json"
        output_json.write_text(
            json.dumps(batch_result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # 生成汇总报告
        self.generate_summary_report(batch_result)

    def generate_summary_report(self, batch_result: dict[str, Any]):
        """生成汇总报告"""

        results = batch_result["results"]
        stats = self.stats

        # 统计证据价值分布
        high_value = [r for r in results if r.get("success") and r.get("evidence_value") == "高"]
        medium_value = [r for r in results if r.get("success") and r.get("evidence_value") == "中"]
        low_value = [r for r in results if r.get("success") and r.get("evidence_value") == "低"]

        # 计算耗时
        elapsed_time = stats["end_time"] - stats["start_time"]

        # 获取模型信息
        model_info = self.client.get_model_info()

        # 生成Markdown报告
        md_content = f"""# 深度技术分析汇总报告（{model_info.get('name', 'GLM')}）

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**使用模型**: {self.client.model} ({model_info.get('name', 'Unknown')})
**模型质量**: {model_info.get('quality', 'Unknown')}
**模型速度**: {model_info.get('speed', 'Unknown')}
**API端点**: https://open.bigmodel.cn/api/coding/paas/v4
**分析人**: Athena智能专利分析器

---

## 📊 分析统计

| 项目 | 数量 | 占比 |
|------|------|------|
| **总文件数** | {stats['total_files']} | 100% |
| **成功分析** | {stats['analyzed']} | {stats['analyzed']/max(stats['total_files'],1)*100:.1f}% |
| **分析失败** | {stats['failed']} | {stats['failed']/max(stats['total_files'],1)*100:.1f}% |
| **总耗时** | {elapsed_time/60:.1f} 分钟 | - |
| **平均速度** | {elapsed_time/max(stats['total_files'],1):.1f} 秒/文件 | - |
| **总Token使用** | {stats['total_tokens']:,} | - |
| **总成本** | ¥{stats['total_cost']:.2f} | - |

---

## 🎯 证据价值分布

| 证据价值 | 数量 | 占比 |
|---------|------|------|
| **高价值** | {len(high_value)} | {len(high_value)/max(len(results),1)*100:.1f}% |
| **中价值** | {len(medium_value)} | {len(medium_value)/max(len(results),1)*100:.1f}% |
| **低价值** | {len(low_value)} | {len(low_value)/max(len(results),1)*100:.1f}% |

---

## ⭐ 高价值证据清单

"""

        for result in high_value[:20]:
            md_content += f"""
### {result['patent_number']}

- **技术领域**: {result.get('technical_field', 'N/A')}
- **发明主题**: {result.get('invention_title', 'N/A')}
- **证据价值**: ⭐⭐⭐ **高**
- **评估理由**: {result.get('evidence_reason', 'N/A')}
- **无效理由**: {', '.join(result.get('invalidation_grounds', []))}
- **置信度**: {result.get('confidence', 0)}%

---

"""

        md_content += f"""
## 📈 详细分析结果

完整的分析结果已保存至: `{self.analysis_output_dir}/深度技术分析完整结果_{self.client.model}.json`

---

## 💡 下一步建议

1. **重点分析高价值证据**: 对{len(high_value)}个高价值证据进行逐项对比
2. **证据组合策略**: 选择3-5个最强证据形成证据链
3. **补充理由撰写**: 基于分析结果撰写正式补充理由

---

## ⚡ 模型性能总结

| 指标 | 数值 |
|------|------|
| 使用模型 | {model_info.get('name', 'Unknown')} |
| 模型质量 | {model_info.get('quality', 'Unknown')} |
| 处理速度 | {elapsed_time/max(stats['total_files'],1):.1f} 秒/文件 |
| 总耗时 | {elapsed_time/60:.1f} 分钟 |
| 总成本 | ¥{stats['total_cost']:.2f} |
| 平均每文件成本 | ¥{stats['total_cost']/max(stats['total_files'],1):.4f} |

---

**报告生成**: Athena智能专利分析器 🚀
"""

        # 保存Markdown报告
        report_path = self.analysis_output_dir / f"深度技术分析汇总报告_{self.client.model}.md"
        report_path.write_text(md_content, encoding="utf-8")

        logger.info(f"📝 汇总报告已生成: {report_path}")


def main():
    """主函数"""
    parser = ArgumentParser(description="智能专利深度分析工具 - 支持所有GLM模型")

    parser.add_argument(
        "ocr_output_dir",
        help="OCR输出目录"
    )

    parser.add_argument(
        "analysis_output_dir",
        help="分析结果输出目录"
    )

    parser.add_argument(
        "--model", "-m",
        choices=["glm-4-plus", "glm-4-0520", "glm-4-air", "glm-4-flash", "glm-4"],
        help="指定模型（不指定则自动选择）",
        default=None
    )

    parser.add_argument(
        "--preference", "-p",
        choices=["quality", "balanced", "speed", "cost"],
        help="性能偏好（仅在不指定模型时生效）",
        default="quality"
    )

    parser.add_argument(
        "--api-key", "-k",
        help="GLM API密钥（不指定则从环境变量读取）",
        default=None
    )

    args = parser.parse_args()

    async def run():
        # 创建分析器
        analyzer = SmartPatentAnalyzer(
            ocr_output_dir=args.ocr_output_dir,
            analysis_output_dir=args.analysis_output_dir,
            model=args.model,
            preference=args.preference,
            api_key=args.api_key
        )

        # 查找TXT文件
        txt_files = analyzer.find_text_files()

        if not txt_files:
            logger.warning(f"⚠️ 未找到TXT文件: {args.ocr_output_dir}")
            sys.exit(0)

        # 批量分析
        batch_result = await analyzer.analyze_batch(txt_files)

        # 保存最终结果
        analyzer.save_final_results(batch_result)

        # 输出最终统计
        stats = analyzer.stats
        elapsed_time = stats["end_time"] - stats["start_time"]
        model_info = analyzer.client.get_model_info()

        logger.info("=" * 80)
        logger.info("✅ 深度技术分析完成！")
        logger.info(f"   模型: {analyzer.client.model} ({model_info.get('name', 'Unknown')})")
        logger.info(f"   总文件数: {stats['total_files']}")
        logger.info(f"   成功分析: {stats['analyzed']}")
        logger.info(f"   分析失败: {stats['failed']}")
        logger.info(f"   总耗时: {elapsed_time/60:.1f} 分钟")
        logger.info(f"   平均速度: {elapsed_time/stats['total_files']:.1f} 秒/文件")
        logger.info(f"   总Token使用: {stats['total_tokens']:,}")
        logger.info(f"   总成本: ¥{stats['total_cost']:.2f}")
        logger.info(f"   输出目录: {analyzer.analysis_output_dir}")
        logger.info("=" * 80)

    asyncio.run(run())


if __name__ == "__main__":
    main()
