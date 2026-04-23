#!/usr/bin/env python3
"""
深度技术分析脚本 - 基于GLM-4-Plus云端模型
对169个已OCR处理的专利进行深度技术特征提取与分析

Author: Athena平台团队
Date: 2026-04-22
Model: GLM-4-Plus (https://open.bigmodel.cn/api/coding/paas/v4)
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime
import httpx

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GLMPatentAnalyzer:
    """专利技术深度分析器 - 使用GLM-4-Plus云端模型"""

    def __init__(
        self,
        ocr_output_dir: str,
        analysis_output_dir: str,
        api_key: str = None
    ):
        """
        初始化分析器

        Args:
            ocr_output_dir: OCR输出目录
            analysis_output_dir: 分析结果输出目录
            api_key: GLM API密钥
        """
        self.ocr_output_dir = Path(ocr_output_dir)
        self.analysis_output_dir = Path(analysis_output_dir)

        # GLM API配置（固定端点）
        self.api_key = api_key or "2b4ab444ad814c5b9ae4a13be4beb887.coYRf2PKuIjkc1bn"
        self.base_url = "https://open.bigmodel.cn/api/coding/paas/v4"
        self.model = "glm-4-plus"
        self.timeout = 120  # 2分钟超时（云端模型很快）

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
            "total_cost": 0.0
        }

    async def initialize(self):
        """初始化GLM客户端"""
        try:
            # 测试连接
            test_url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    test_url,
                    headers=headers,
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "测试连接"}],
                        "max_tokens": 10
                    }
                )

                if response.status_code == 200:
                    logger.info(f"✅ GLM-4-Plus连接成功: {self.base_url}")
                    return True
                else:
                    logger.error(f"❌ GLM连接失败: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}", exc_info=True)
            return False

    def find_text_files(self) -> List[Path]:
        """查找所有OCR生成的TXT文件"""
        logger.info(f"🔍 扫描OCR输出目录: {self.ocr_output_dir}")

        txt_files = list(self.ocr_output_dir.rglob("*.txt"))

        # 过滤掉报告文件
        txt_files = [f for f in txt_files if "批量处理报告" not in f.name]

        logger.info(f"✅ 找到 {len(txt_files)} 个TXT文件")

        return sorted(txt_files)

    async def analyze_single_patent(self, txt_path: Path) -> Dict[str, Any]:
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

            # 读取OCR文本（限制前3000字符，约1000 tokens）
            patent_text = txt_path.read_text(encoding="utf-8")[:3000]

            # 提取专利号（从文件名）
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

            # 调用GLM API
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2500
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                logger.error(f"  ❌ GLM API错误: {response.status_code}")
                return {
                    "patent_number": patent_number,
                    "source_file": str(txt_path),
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "analysis_time": asyncio.get_event_loop().time() - file_start_time
                }

            # 解析响应
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})

            # 更新统计
            self.stats["total_tokens"] += usage.get("total_tokens", 0)
            # GLM-4-Plus定价：输入¥0.005/1K tokens，输出¥0.005/1K tokens
            input_cost = usage.get("prompt_tokens", 0) * 0.005 / 1000
            output_cost = usage.get("completion_tokens", 0) * 0.005 / 1000
            self.stats["total_cost"] += (input_cost + output_cost)

            # 解析JSON响应
            try:
                # 提取JSON部分（可能包含markdown代码块）
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
                analysis_result["tokens_used"] = usage.get("total_tokens", 0)
                analysis_result["cost"] = input_cost + output_cost

                logger.info(f"  ✅ 分析完成: {patent_number} (证据价值: {analysis_result.get('evidence_value', 'N/A')}, 耗时: {analysis_result['analysis_time']:.1f}秒)")

                return analysis_result

            except json.JSONDecodeError as e:
                logger.error(f"  ❌ JSON解析失败: {patent_number} - {e}")

                # 返回原始响应
                return {
                    "patent_number": patent_number,
                    "source_file": str(txt_path),
                    "success": False,
                    "error": "JSON解析失败",
                    "raw_response": content[:500],  # 保存前500字符
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

    async def analyze_batch(self, txt_files: List[Path]) -> Dict[str, Any]:
        """
        批量分析专利文件（顺序执行）

        Args:
            txt_files: TXT文件列表

        Returns:
            批量分析结果
        """
        self.stats["start_time"] = asyncio.get_event_loop().time()
        self.stats["total_files"] = len(txt_files)

        logger.info("=" * 80)
        logger.info(f"🚀 开始深度技术分析: {len(txt_files)} 个专利")
        logger.info(f"   OCR输出目录: {self.ocr_output_dir}")
        logger.info(f"   分析输出目录: {self.analysis_output_dir}")
        logger.info(f"   使用模型: {self.model}")
        logger.info(f"   API端点: {self.base_url}")
        logger.info("=" * 80)

        # 顺序分析（GLM云端模型很快，不需要并发）
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

    def save_intermediate_results(self, results: List[Dict[str, Any]]):
        """保存中间结果"""
        output_file = self.analysis_output_dir / f"中间结果_GLM_{len(results)}个文件.json"
        output_file.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def save_final_results(self, batch_result: Dict[str, Any]):
        """保存最终结果"""
        # 保存JSON结果
        output_json = self.analysis_output_dir / "深度技术分析完整结果_GLM.json"
        output_json.write_text(
            json.dumps(batch_result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # 生成汇总报告
        self.generate_summary_report(batch_result)

    def generate_summary_report(self, batch_result: Dict[str, Any]):
        """生成汇总报告"""

        results = batch_result["results"]
        stats = self.stats

        # 统计证据价值分布
        high_value = [r for r in results if r.get("success") and r.get("evidence_value") == "高"]
        medium_value = [r for r in results if r.get("success") and r.get("evidence_value") == "中"]
        low_value = [r for r in results if r.get("success") and r.get("evidence_value") == "低"]

        # 计算耗时
        elapsed_time = stats["end_time"] - stats["start_time"]

        # 生成Markdown报告
        md_content = f"""# 深度技术分析汇总报告（GLM-4-Plus）

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**使用模型**: {self.model}
**API端点**: {self.base_url}
**分析人**: Athena深度技术分析器 (GLM版本)

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

        for result in high_value[:20]:  # 显示前20个
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

完整的分析结果已保存至: `{self.analysis_output_dir}/深度技术分析完整结果_GLM.json`

---

## 💡 下一步建议

1. **重点分析高价值证据**: 对{len(high_value)}个高价值证据进行逐项对比
2. **证据组合策略**: 选择3-5个最强证据形成证据链
3. **补充理由撰写**: 基于分析结果撰写正式补充理由

---

## ⚡ 性能对比（GLM vs 本地Qwen）

| 指标 | 本地Qwen3.5-27B | GLM-4-Plus | 提升 |
|------|----------------|-----------|------|
| 平均速度 | ~300秒/文件 | {elapsed_time/max(stats['total_files'],1):.1f}秒/文件 | {300/max(elapsed_time/max(stats['total_files'],1),1):.1f}倍 |
| 总耗时 | ~17-28小时 | {elapsed_time/60:.1f}分钟 | - |
| 成本 | 免费（电费） | ¥{stats['total_cost']:.2f} | - |

---

**报告生成**: Athena深度技术分析器 (GLM-4-Plus) 🚀
"""

        # 保存Markdown报告
        report_path = self.analysis_output_dir / "深度技术分析汇总报告_GLM.md"
        report_path.write_text(md_content, encoding="utf-8")

        logger.info(f"📝 汇总报告已生成: {report_path}")


async def main():
    """主函数"""

    # 检查命令行参数
    if len(sys.argv) < 3:
        print("使用方法: python deep_technical_analysis_glm.py <OCR输出目录> <分析输出目录>")
        print("")
        print("参数说明:")
        print("  OCR输出目录: RapidOCR生成的TXT文件目录")
        print("  分析输出目录: 保存分析结果的目录")
        print("")
        print("示例:")
        print("  python deep_technical_analysis_glm.py \\")
        print("    '/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9无效材料/RapidOCR批量输出' \\")
        print("    '/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9无效材料/深度技术分析输出'")
        sys.exit(1)

    ocr_output_dir = sys.argv[1]
    analysis_output_dir = sys.argv[2]

    # 创建分析器
    analyzer = GLMPatentAnalyzer(
        ocr_output_dir=ocr_output_dir,
        analysis_output_dir=analysis_output_dir
    )

    # 初始化
    logger.info("🔧 初始化GLM-4-Plus深度技术分析器...")
    if not await analyzer.initialize():
        logger.error("❌ 初始化失败，请检查API密钥和网络连接")
        sys.exit(1)

    # 查找TXT文件
    txt_files = analyzer.find_text_files()

    if not txt_files:
        logger.warning(f"⚠️ 未找到TXT文件: {ocr_output_dir}")
        sys.exit(0)

    # 批量分析
    batch_result = await analyzer.analyze_batch(txt_files)

    # 保存最终结果
    analyzer.save_final_results(batch_result)

    # 输出最终统计
    stats = analyzer.stats
    elapsed_time = stats["end_time"] - stats["start_time"]
    logger.info("=" * 80)
    logger.info("✅ 深度技术分析完成！")
    logger.info(f"   总文件数: {stats['total_files']}")
    logger.info(f"   成功分析: {stats['analyzed']}")
    logger.info(f"   分析失败: {stats['failed']}")
    logger.info(f"   总耗时: {elapsed_time/60:.1f} 分钟")
    logger.info(f"   平均速度: {elapsed_time/stats['total_files']:.1f} 秒/文件")
    logger.info(f"   总Token使用: {stats['total_tokens']:,}")
    logger.info(f"   总成本: ¥{stats['total_cost']:.2f}")
    logger.info(f"   输出目录: {analyzer.analysis_output_dir}")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
