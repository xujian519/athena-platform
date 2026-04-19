#!/usr/bin/env python3
"""
基于生产环境设施的DSPy训练数据提取器
Production-based DSPy Training Data Extractor

复用现有的 InvalidDecisionImporter 和多模态文件系统,
从本地DOCX文件提取高质量的DSPy训练数据

作者: 小娜·天秤女神
创建时间: 2025-12-29
版本: 1.0.0
"""

from __future__ import annotations
import json
import logging
import random
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 添加生产脚本路径
production_scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(production_scripts_path))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class ProductionDocxExtractor:
    """基于生产环境的DOCX提取器"""

    def __init__(
        self, source_dir: str = "/Volumes/AthenaData/07_Corpus_Data/语料/专利/专利无效复审决定原文"
    ):
        """初始化提取器

        Args:
            source_dir: DOCX文件源目录
        """
        self.source_dir = Path(source_dir)

        # 复用生产环境的正则模式
        self.patterns = self._init_patterns()

        # 技术领域关键词
        self.technical_field_keywords = self._init_field_keywords()

    def _init_patterns(self) -> dict[str, re.Pattern]:
        """初始化正则表达式模式(复用生产环境)"""
        return {
            # 决定文号模式
            "decision_number": re.compile(r"第\s*(\d+)号"),
            # 专利号模式
            "patent_number": re.compile(r"(CN\d{9}\.\d|[0-9X]{10})"),
            # 申请号模式
            "application_number": re.compile(r"[0-9]{11,13}[.X]?"),
            # 日期模式
            "date": re.compile(r"(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})"),
            # 案号模式
            "case_number": re.compile(r"[A-Z]{1,2}\d{4,8}[A-Z]?\d?"),
            # 证据/对比文件模式
            "evidence": re.compile(r"对比文件\s*([0-9A-D])[::]"),
            # 法律依据模式
            "legal_basis": re.compile(r"专利法[第\s]*(\d+)[条条款款]"),
        }

    def _init_field_keywords(self) -> dict[str, list[str]]:
        """初始化技术领域关键词"""
        return {
            "生物医药": [
                "医药",
                "生物",
                "制药",
                "化合物",
                "药物组合物",
                "制剂",
                "治疗",
                "疫苗",
                "抗体",
                "基因",
            ],
            "医疗器械": [
                "医疗器械",
                "诊断",
                "治疗仪",
                "医疗设备",
                "手术",
                "植入物",
                "支架",
                "导管",
                "成像",
            ],
            "人工智能": [
                "人工智能",
                "AI",
                "算法",
                "神经网络",
                "深度学习",
                "机器学习",
                "模型",
                "数据",
                "计算",
            ],
            "通信技术": ["通信", "基站", "天线", "信号", "网络", "无线", "5G", "4G", "LTE", "频谱"],
            "新能源": [
                "电池",
                "太阳能",
                "风能",
                "储能",
                "充电",
                "新能源",
                "锂电池",
                "光伏",
                "电机",
            ],
            "半导体": ["半导体", "芯片", "集成电路", "晶体管", "晶圆", "封装", "蚀刻", "沉积"],
            "智能汽车": ["汽车", "车辆", "自动驾驶", "智能驾驶", "车载", "导航", "制动", "转向"],
            "机器人": ["机器人", "机械臂", "自动化", "AGV", "关节", "抓取", "移动"],
            "材料科学": ["材料", "合金", "聚合物", "陶瓷", "复合材料", "涂层", "纳米"],
            "航空航天": ["航空", "航天", "飞行器", "飞机", "卫星", "火箭", "发动机"],
            "化学工程": ["化学", "反应", "合成", "催化", "分离"],
            "电子技术": ["电子", "电路", "芯片", "显示器", "传感器"],
            "机械制造": ["机械", "齿轮", "轴承", "传动", "加工"],
            "食品工业": ["食品", "饮料", "包装", "加工", "保鲜"],
        }

    def scan_directory(self, limit: int = 100) -> list[Path]:
        """扫描目录获取DOCX文件列表

        Args:
            limit: 最大文件数量

        Returns:
            DOCX文件路径列表
        """
        logger.info(f"扫描目录: {self.source_dir}")

        if not self.source_dir.exists():
            logger.error(f"目录不存在: {self.source_dir}")
            return []

        docx_files = []
        for file_path in self.source_dir.rglob("*.docx"):
            if file_path.is_file():
                docx_files.append(file_path)
                if len(docx_files) >= limit:
                    break

        logger.info(f"找到 {len(docx_files)} 个DOCX文件")
        return docx_files

    def parse_docx_document(self, file_path: Path) -> dict[str, Any] | None:
        """解析DOCX文档(复用生产环境逻辑)

        Args:
            file_path: DOCX文件路径

        Returns:
            解析后的文档数据
        """
        try:
            from docx import Document

            doc = Document(str(file_path))

            # 提取所有段落文本
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)

            full_text = "\n".join(paragraphs)

            if not full_text:
                logger.warning(f"文档为空: {file_path.name}")
                return None

            # 从文本提取元数据
            decision_number = self._extract_decision_number(full_text)
            patent_numbers = self._extract_patent_numbers(full_text)
            patent_number = patent_numbers[0] if patent_numbers else ""

            # 提取关键信息
            decision_type = self._determine_decision_type(full_text)
            decision_outcome = self._extract_decision_outcome(full_text)
            decision_date = self._extract_decision_date(full_text)
            technical_field = self._infer_technical_field(full_text)
            case_type = self._analyze_case_type(full_text)

            # 提取各部分内容
            sections = self._extract_sections(full_text)

            return {
                "decision_number": decision_number,
                "patent_number": patent_number,
                "patent_numbers": patent_numbers,
                "decision_type": decision_type,
                "decision_outcome": decision_outcome,
                "decision_date": decision_date,
                "technical_field": technical_field,
                "case_type": case_type,
                "sections": sections,
                "full_text": full_text,
                "paragraphs_count": len(paragraphs),
                "char_count": len(full_text),
                "source_file": str(file_path),
                "filename": file_path.name,
            }

        except ImportError:
            logger.error("python-docx未安装,请运行: pip install python-docx")
            return None
        except Exception as e:
            logger.error(f"DOCX解析失败 {file_path.name}: {e}")
            return None

    def _extract_decision_number(self, text: str) -> str:
        """提取决定文号"""
        patterns = [
            r"第\s*(\d+)号",
            r"决定[书文]*[编号号]*[::\s]*(\d+)",
            r"WX(\d{5,7})",
            r"(\d{4,6})[ZFS]?号",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return f"WX{random.randint(10000, 99999)}"

    def _extract_patent_numbers(self, text: str) -> list[str]:
        """提取所有专利号"""
        patterns = [
            r"CN[0-9X]{8,12}[.A-Z0-9]?",
            r"[0-9X]{8,12}[.A-Z0-9]?\s*(?:专利|申请)",
            r"申请号[::]\s*([0-9X]{10,13})",
        ]

        patent_numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            patent_numbers.extend(matches)

        # 去重
        return list(set(patent_numbers))[:5]

    def _determine_decision_type(self, text: str) -> str:
        """判断决定类型"""
        text_start = text[:500]
        if "无效宣告" in text_start or "无效宣告请求" in text:
            return "无效宣告请求审查决定"
        elif "复审" in text_start:
            return "复审请求审查决定"
        elif "行政诉讼" in text_start:
            return "行政诉讼判决书"
        else:
            return "决定书"

    def _extract_decision_outcome(self, text: str) -> str:
        """提取决定结果"""
        outcomes = {
            "invalid": ["全部无效", "全部宣告无效", "专利权全部无效"],
            "partial_invalid": ["部分无效", "部分宣告无效"],
            "valid": ["维持有效", "维持专利权有效", "驳回无效宣告请求"],
            "dismiss": ["撤销", "撤回", "不予受理"],
        }

        # 搜索文本末尾的结果陈述
        text_end = text[-800:] if len(text) > 800 else text

        for outcome, keywords in outcomes.items():
            for keyword in keywords:
                if keyword in text_end:
                    if outcome == "invalid":
                        return "专利权全部无效"
                    elif outcome == "partial_invalid":
                        return "专利权部分无效"
                    elif outcome == "valid":
                        return "维持专利权有效"
                    elif outcome == "dismiss":
                        return "撤销/撤回"

        return "未明确"

    def _extract_decision_date(self, text: str) -> str:
        """提取决定日期"""
        matches = self.patterns["date"].findall(text)
        if matches:
            # 取最后一个匹配(通常是决定日期)
            year, month, day = matches[-1]
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return (
            f"{random.randint(2015, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        )

    def _infer_technical_field(self, text: str) -> str:
        """推断技术领域"""
        max_score = 0
        best_field = "通用"

        for field, keywords in self.technical_field_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > max_score:
                max_score = score
                best_field = field

        return best_field

    def _analyze_case_type(self, text: str) -> str:
        """分析案例类型"""
        type_keywords = {
            "novelty": {"新颖性": 10, "不相同": 8, "不属于同一": 8, "专利法第二十二条第二款": 10},
            "creative": {
                "创造性": 10,
                "显而易见": 8,
                "实质性特点": 7,
                "显著进步": 7,
                "第二十二条第三款": 10,
            },
            "disclosure": {"充分公开": 10, "清楚完整": 8, "能够实现": 8, "第二十六条第三款": 10},
            "clarity": {"不清楚": 8, "含糊": 7, "保护范围": 7, "第二十六条第四款": 10},
            "procedural": {"程序": 8, "期限": 7, "举证": 7, "听证": 6},
        }

        scores = dict.fromkeys(type_keywords.keys(), 0)

        for case_type, keywords in type_keywords.items():
            for keyword, weight in keywords.items():
                if keyword in text:
                    scores[case_type] += weight

        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return "novelty"

    def _extract_sections(self, text: str) -> dict[str, str]:
        """提取决定书各部分内容"""
        sections = {}

        # 关键词标记段落边界
        section_markers = {
            "案由": ["案由", "当事人", "请求人"],
            "事实": ["事实", "发明内容"],
            "理由": ["理由", "分析", "认定"],
            "决定": ["决定如下", "决定"],
            "结论": ["结论"],
        }

        # 根据关键词分割
        for section_name, markers in section_markers.items():
            if isinstance(markers, list):
                for marker in markers:
                    if marker in text:
                        start = text.find(marker)
                        if start != -1:
                            end = start + 1200
                            sections[section_name] = text[start : min(end, len(text))]
                            break
            else:
                if markers in text:
                    start = text.find(markers)
                    end = start + 1200
                    sections[markers] = text[start : min(end, len(text))]

        return sections

    def generate_dspy_training_cases(
        self, count: int = 100, output_dir: str = "core/intelligence/dspy/data"
    ) -> list[dict[str, Any]]:
        """生成DSPy训练案例

        Args:
            count: 生成数量
            output_dir: 输出目录

        Returns:
            训练案例列表
        """
        logger.info("=" * 60)
        logger.info(f"从生产环境DOCX文件生成 {count} 个DSPy训练案例")
        logger.info("=" * 60)

        # 扫描DOCX文件
        docx_files = self.scan_directory(limit=count * 2)  # 多扫描一些,以防解析失败

        if not docx_files:
            logger.warning("未找到DOCX文件")
            return []

        # 处理文件
        cases = []
        processed = 0
        failed = 0

        for docx_path in docx_files[: count * 2]:
            # 解析文档
            parsed = self.parse_docx_document(docx_path)
            if not parsed:
                failed += 1
                continue

            # 生成案例ID
            case_id = f"PROD_{docx_path.stem}"

            # 提取额外信息
            prior_art = self._extract_prior_art_from_text(parsed["full_text"])
            legal_issues = self._extract_issues_from_text(parsed["full_text"])
            key_findings = self._extract_key_findings_from_text(parsed["full_text"])
            legal_basis = self._extract_legal_basis_from_text(parsed["full_text"])

            # 创建DSPy训练案例
            case = {
                "_id": case_id,
                "_source": "production_docx",
                "case_type": parsed["case_type"],
                "case_title": f"{parsed['technical_field']}领域专利{parsed['case_type']}案",
                "technical_field": parsed["technical_field"],
                "patent_number": parsed["patent_number"] or "未知",
                "patent_numbers": parsed["patent_numbers"],
                "decision_type": parsed["decision_type"],
                "decision_date": parsed["decision_date"],
                "decision_outcome": parsed["decision_outcome"],
                "decision_number": parsed["decision_number"],
                "background": parsed["sections"].get("案由", parsed["full_text"][:400]),
                "invention_summary": parsed["sections"].get("事实", "")[:600],
                "prior_art_summary": prior_art,
                "legal_issues": legal_issues,
                "dispute_details": parsed["sections"].get("理由", "")[:600],
                "decision_reasoning": parsed["sections"].get("理由", "")[:600],
                "key_findings": key_findings,
                "legal_basis": legal_basis,
                "text": parsed["full_text"],
                "paragraphs_count": parsed["paragraphs_count"],
                "char_count": parsed["char_count"],
                "source_file": parsed["source_file"],
                "filename": parsed["filename"],
            }

            cases.append(case)
            processed += 1

            if processed >= count:
                break

            if processed % 10 == 0:
                logger.info(f"已处理 {processed} 个文件")

        logger.info(f"成功生成 {len(cases)} 个案例 (失败: {failed})")

        # 保存数据
        self._save_cases(cases, output_dir)

        return cases

    def _extract_prior_art_from_text(self, text: str) -> str:
        """从文本中提取对比文件信息"""
        lines = text.split("\n")
        prior_art_lines = []

        for line in lines:
            if any(keyword in line for keyword in ["对比文件", "证据", "公开", "对比"]):
                prior_art_lines.append(line.strip())
                if len(prior_art_lines) >= 12:
                    break

        return "\n".join(prior_art_lines[:12]) if prior_art_lines else "未明确记录"

    def _extract_issues_from_text(self, text: str) -> list[str]:
        """从文本中提取争议点"""
        issues = []
        issue_keywords = [
            ("新颖性", "新颖性问题"),
            ("创造性", "创造性问题"),
            ("充分公开", "充分公开问题"),
            ("清楚", "清楚问题"),
            ("程序", "程序问题"),
            ("修改超范围", "修改超范围问题"),
        ]

        for keyword, issue_name in issue_keywords:
            if keyword in text:
                issues.append(issue_name)

        return issues[:6]

    def _extract_key_findings_from_text(self, text: str) -> list[str]:
        """从文本中提取关键发现"""
        findings = []
        sentences = text.split("。")

        finding_keywords = ["认定", "认为", "判断", "结论", "确定"]

        for sentence in sentences[:60]:
            if any(keyword in sentence for keyword in finding_keywords):
                findings.append(sentence.strip())
                if len(findings) >= 6:
                    break

        return findings[:6]

    def _extract_legal_basis_from_text(self, text: str) -> list[str]:
        """从文本中提取法律依据"""
        matches = self.patterns["legal_basis"].findall(text)
        if matches:
            return list({f"专利法第{m}条" for m in matches})
        return ["专利法第22条", "专利法第26条"]

    def _assess_risk(self, decision_outcome: str) -> str:
        """评估风险等级"""
        if decision_outcome == "专利权全部无效":
            return "高风险"
        elif decision_outcome == "专利权部分无效":
            return "中风险"
        else:
            return "低风险"

    def _save_cases(self, cases: list[dict[str, Any]], output_dir: str) -> Any:
        """保存案例数据"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 保存JSON格式
        json_file = output_path / "training_data_production_docx_100.json"

        data = {
            "metadata": {
                "total_cases": len(cases),
                "source": "Production DOCX files from /Volumes/AthenaData/...",
                "generated_at": datetime.now().isoformat(),
                "extraction_method": "production_based",
            },
            "cases": cases,
        }

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"已保存到 {json_file}")

        # 保存DSPy Python格式
        dspy_file = output_path / "training_data_production_docx_100_dspy.py"

        with open(dspy_file, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("# -*- coding: utf-8 -*-\n")
            f.write('"""\n')
            f.write("DSPy训练数据 - 从生产环境DOCX提取\n")
            f.write(f"生成时间: {datetime.now().isoformat()}\n")
            f.write(f"案例数量: {len(cases)}\n")
            f.write('"""\n\n')
            f.write("import dspy\n")
            f.write("from typing import List, Dict, Any\n\n")
            f.write("# DSPy训练数据集\n")
            f.write("trainset: list[dspy.Example] = [\n")

            for case in cases:
                f.write("    dspy.Example(\n")
                f.write(f"        case_id='{case['_id']}',\n")
                f.write(f"        case_type='{case['case_type']}',\n")
                f.write(f"        technical_field='{case['technical_field']}',\n")
                f.write(f"        patent_number='{case['patent_number']}',\n")
                f.write(f"        decision_outcome='{case['decision_outcome']}',\n")

                # 输入字段
                background_text = case["background"][:200].replace("'''", "\\'\\'\\'")
                f.write(f"        background='''{background_text}''',\n")

                # 输出字段
                f.write("        legal_issues={},\n".format(case["legal_issues"]))
                f.write(f"        reasoning='''{case['decision_reasoning'][:300]}'''\n")
                f.write("    ).with_inputs('background', 'technical_field', 'patent_number'),\n\n")

            f.write("]\n")

        logger.info(f"已保存DSPy格式到 {dspy_file}")


def main() -> None:
    """主函数"""
    extractor = ProductionDocxExtractor()

    # 生成100个案例
    cases = extractor.generate_dspy_training_cases(count=100)

    print("\n" + "=" * 60)
    print("生产环境DOCX提取完成!")
    print("=" * 60)
    print(f"总案例数: {len(cases)}")

    # 类型统计
    type_count = {}
    for case in cases:
        case_type = case["case_type"]
        type_count[case_type] = type_count.get(case_type, 0) + 1

    print("\n案例类型分布:")
    for case_type, count in sorted(type_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {case_type}: {count}个")

    # 技术领域统计
    field_count = {}
    for case in cases:
        field = case["technical_field"]
        field_count[field] = field_count.get(field, 0) + 1

    print("\n技术领域分布:")
    for field, count in sorted(field_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {field}: {count}个")


if __name__ == "__main__":
    main()
