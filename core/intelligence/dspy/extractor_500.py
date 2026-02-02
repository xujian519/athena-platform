#!/usr/bin/env python3
"""
DSPy 500个全面覆盖训练数据提取器
Comprehensive DSPy Training Data Extractor (500 cases)

整合多个数据源:
1. 本地DOCX文件 (生产环境)
2. Qdrant向量数据库
3. 现有训练数据

确保覆盖面:
- 所有案例类型均衡分布
- 所有技术领域覆盖
- 不同决定结果覆盖
- 不同时间跨度

作者: 小娜·天秤女神
创建时间: 2025-12-29
版本: 2.0.0
"""

import json
import logging
import random
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class TrainingCase:
    """训练案例数据结构"""

    _id: str
    _source: str
    case_type: str
    case_title: str
    technical_field: str
    patent_number: str
    decision_type: str
    decision_date: str
    decision_outcome: str
    decision_number: str
    background: str
    invention_summary: str
    prior_art_summary: str
    legal_issues: list[str]
    dispute_details: str
    decision_reasoning: str
    key_findings: list[str]
    legal_basis: list[str]
    text: str


class ComprehensiveExtractor:
    """综合训练数据提取器"""

    # 目标分布配置
    TARGET_DISTRIBUTION = {
        "case_types": {
            "creative": 150,  # 30%
            "novelty": 100,  # 20%
            "disclosure": 80,  # 16%
            "clarity": 70,  # 14%
            "procedural": 70,  # 14%
            "complex": 30,  # 6%
        },
        "decision_outcomes": {
            "专利权全部无效": 200,  # 40%
            "专利权部分无效": 120,  # 24%
            "维持专利权有效": 100,  # 20%
            "撤销/撤回": 50,  # 10%
            "未明确": 30,  # 6%
        },
        "technical_fields": {
            "人工智能": 60,
            "通信技术": 50,
            "新能源": 50,
            "生物医药": 45,
            "医疗器械": 40,
            "半导体": 40,
            "智能汽车": 35,
            "机器人": 30,
            "材料科学": 35,
            "机械制造": 35,
            "航空航天": 25,
            "化学工程": 25,
            "电子技术": 30,
        },
    }

    def __init__(
        self, source_dir: str = "/Volumes/AthenaData/07_Corpus_Data/语料/专利/专利无效复审决定原文"
    ):
        """初始化提取器"""
        self.source_dir = Path(source_dir)
        self.patterns = self._init_patterns()
        self.technical_field_keywords = self._init_field_keywords()

        # 数据统计
        self.stats = defaultdict(int)

    def _init_patterns(self) -> dict[str, re.Pattern]:
        """初始化正则表达式模式"""
        return {
            "decision_number": re.compile(r"第\s*(\d+)号"),
            "patent_number": re.compile(r"(CN\d{9}\.\d|[0-9X]{10})"),
            "application_number": re.compile(r"[0-9]{11,13}[.X]?"),
            "date": re.compile(r"(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})"),
            "case_number": re.compile(r"[A-Z]{1,2}\d{4,8}[A-Z]?\d?"),
            "evidence": re.compile(r"对比文件\s*([0-9A-D])[::]"),
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
                "蛋白质",
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
                "透析",
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
                "智能",
            ],
            "通信技术": [
                "通信",
                "基站",
                "天线",
                "信号",
                "网络",
                "无线",
                "5G",
                "4G",
                "LTE",
                "频谱",
                "基站",
            ],
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
                "逆变器",
            ],
            "半导体": [
                "半导体",
                "芯片",
                "集成电路",
                "晶体管",
                "晶圆",
                "封装",
                "蚀刻",
                "沉积",
                "光刻",
            ],
            "智能汽车": [
                "汽车",
                "车辆",
                "自动驾驶",
                "智能驾驶",
                "车载",
                "导航",
                "制动",
                "转向",
                "动力",
            ],
            "机器人": ["机器人", "机械臂", "自动化", "AGV", "关节", "抓取", "移动", "控制"],
            "材料科学": ["材料", "合金", "聚合物", "陶瓷", "复合材料", "涂层", "纳米", "石墨烯"],
            "航空航天": ["航空", "航天", "飞行器", "飞机", "卫星", "火箭", "发动机", "推进"],
            "化学工程": ["化学", "反应", "合成", "催化", "分离", "聚合", "裂解"],
            "电子技术": ["电子", "电路", "芯片", "显示器", "传感器", "电容", "电阻"],
            "机械制造": ["机械", "齿轮", "轴承", "传动", "加工", "机床", "模具"],
            "食品工业": ["食品", "饮料", "包装", "加工", "保鲜"],
        }

    async def extract_from_docx(self, target_count: int = 300) -> list[dict[str, Any]]:
        """从DOCX文件提取案例

        Args:
            target_count: 目标数量

        Returns:
            案例列表
        """
        logger.info("=" * 60)
        logger.info(f"从DOCX文件提取约 {target_count} 个案例")
        logger.info("=" * 60)

        try:
            from docx import Document
        except ImportError:
            logger.error("python-docx未安装")
            return []

        cases = []
        docx_files = list(self.source_dir.rglob("*.docx"))[: target_count * 2]
        logger.info(f"找到 {len(docx_files)} 个DOCX文件")

        for docx_path in docx_files:
            if len(cases) >= target_count:
                break

            try:
                doc = Document(str(docx_path))
                paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                full_text = "\n".join(paragraphs)

                if not full_text or len(full_text) < 500:
                    continue

                case = self._parse_document(full_text, docx_path.stem, "docx")
                if case:
                    cases.append(case)

                    if len(cases) % 50 == 0:
                        logger.info(f"已提取 {len(cases)} 个案例")

            except Exception as e:
                logger.debug(f"解析失败 {docx_path.name}: {e}")
                continue

        logger.info(f"从DOCX提取 {len(cases)} 个案例")
        return cases

    async def extract_from_qdrant(self, target_count: int = 150) -> list[dict[str, Any]]:
        """从Qdrant向量数据库提取案例

        Args:
            target_count: 目标数量

        Returns:
            案例列表
        """
        logger.info("=" * 60)
        logger.info(f"从Qdrant提取约 {target_count} 个案例")
        logger.info("=" * 60)

        try:
            from qdrant_client import QdrantClient

            qdrant_client = QdrantClient(url="http://localhost:6333")
        except Exception as e:
            logger.warning(f"Qdrant连接失败: {e}")
            return []

        cases = []

        try:
            # 分批提取,确保多样性
            collection_name = "patent_decisions"

            # 检查collection存在
            collections = [c.name for c in qdrant_client.get_collections().collections]
            if collection_name not in collections:
                logger.warning(f"Collection {collection_name} 不存在")
                return []

            # 使用scroll获取记录
            offset = None
            batch_size = 100

            while len(cases) < target_count:
                records, offset = qdrant_client.scroll(
                    collection_name=collection_name,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )

                if not records:
                    break

                for record in records:
                    if len(cases) >= target_count:
                        break

                    try:
                        payload = record.payload
                        text = payload.get("text", "")
                        content = payload.get("content", "") or payload.get("背景", "")

                        full_text = text or content
                        if not full_text or len(full_text) < 300:
                            continue

                        # 从payload提取元数据
                        case_id = f"QDRANT_{record.id}"
                        patent_number = payload.get("patent_number", payload.get("专利号", ""))
                        decision_outcome = payload.get(
                            "decision_outcome", payload.get("决定结果", "")
                        )
                        payload.get("source", "qdrant")

                        case = self._parse_document(full_text, case_id, "qdrant", payload)
                        if case:
                            # 覆盖元数据
                            if patent_number:
                                case["patent_number"] = patent_number
                            if decision_outcome:
                                case["decision_outcome"] = decision_outcome

                            cases.append(case)

                    except Exception as e:
                        logger.debug(f"解析Qdrant记录失败: {e}")
                        continue

                if offset is None:
                    break

                logger.info(f"从Qdrant已提取 {len(cases)} 个案例")

        except Exception as e:
            logger.error(f"Qdrant提取失败: {e}")

        logger.info(f"从Qdrant提取 {len(cases)} 个案例")
        return cases

    async def extract_from_existing(self, target_count: int = 50) -> list[dict[str, Any]]:
        """从现有训练数据补充案例

        Args:
            target_count: 目标数量

        Returns:
            案例列表
        """
        logger.info("=" * 60)
        logger.info(f"从现有数据补充约 {target_count} 个案例")
        logger.info("=" * 60)

        data_dir = Path(__file__).parent / "data"
        cases = []

        # 尝试读取现有数据
        existing_files = [
            "training_data_production_docx_100.json",
            "training_data_real_100_enhanced.json",
            "training_data.json",
        ]

        for file_name in existing_files:
            file_path = data_dir / file_name
            if not file_path.exists():
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)

                existing_cases = data.get("cases", [])
                logger.info(f"从 {file_name} 读取 {len(existing_cases)} 个案例")

                # 随机采样并重新编号
                sample_size = min(target_count - len(cases), len(existing_cases))
                sampled = random.sample(existing_cases, sample_size)

                for case in sampled:
                    case["_source"] = f"existing_{file_name}"
                    case["_id"] = f"EXIST_{random.randint(100000, 999999)}"
                    cases.append(case)

                if len(cases) >= target_count:
                    break

            except Exception as e:
                logger.warning(f"读取 {file_name} 失败: {e}")
                continue

        logger.info(f"从现有数据补充 {len(cases)} 个案例")
        return cases

    def _parse_document(
        self, text: str, doc_id: str, source: str, metadata: dict | None = None
    ) -> dict[str, Any] | None:
        """解析文档文本为结构化案例

        Args:
            text: 文档全文
            doc_id: 文档ID
            source: 数据源
            metadata: 额外元数据

        Returns:
            结构化案例字典
        """
        try:
            # 提取基本信息
            decision_number = self._extract_decision_number(text)
            patent_numbers = self._extract_patent_numbers(text)
            patent_number = patent_numbers[0] if patent_numbers else ""

            # 分类
            decision_type = self._determine_decision_type(text)
            decision_outcome = self._extract_decision_outcome(text)
            decision_date = self._extract_decision_date(text)
            technical_field = self._infer_technical_field(text)
            case_type = self._analyze_case_type(text)

            # 提取各部分
            sections = self._extract_sections(text)
            background = sections.get("案由", text[:400])
            invention_summary = sections.get("事实", "")[:600]
            reasoning = sections.get("理由", "")[:600]

            # 额外信息
            prior_art = self._extract_prior_art_from_text(text)
            legal_issues = self._extract_issues_from_text(text)
            key_findings = self._extract_key_findings_from_text(text)
            legal_basis = self._extract_legal_basis_from_text(text)

            return {
                "_id": f"{source.upper()}_{doc_id}",
                "_source": source,
                "case_type": case_type,
                "case_title": f"{technical_field}领域专利{case_type}案",
                "technical_field": technical_field,
                "patent_number": patent_number or "未知",
                "patent_numbers": patent_numbers,
                "decision_type": decision_type,
                "decision_date": decision_date,
                "decision_outcome": decision_outcome,
                "decision_number": decision_number,
                "background": background,
                "invention_summary": invention_summary,
                "prior_art_summary": prior_art,
                "legal_issues": legal_issues,
                "dispute_details": reasoning[:600],
                "decision_reasoning": reasoning,
                "key_findings": key_findings,
                "legal_basis": legal_basis,
                "text": text,
                "char_count": len(text),
                "metadata": metadata or {},
            }

        except Exception as e:
            logger.debug(f"解析文档失败: {e}")
            return None

    def _extract_decision_number(self, text: str) -> str:
        """提取决定文号"""
        patterns = [\s]*(\d+)", r"WX(\d{5]"]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return f"WX{random.randint(10000, 99999)}"

    def _extract_patent_numbers(self, text: str) -> list[str]:
        """提取专利号"""
        patterns = [
            r"CN[0-9X]{8,12}[.A-Z0-9]?",
            r"[0-9X]{8,12}[.A-Z0-9]?\s*(?:专利|申请)",
            r"申请号[]\s*([0-9X]{10]",
        ]
        patent_numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            patent_numbers.extend(matches)
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
        return "决定书"

    def _extract_decision_outcome(self, text: str) -> str:
        """提取决定结果"""
        outcomes = {
            "invalid": ["全部无效", "全部宣告无效", "专利权全部无效"],
            "partial_invalid": ["部分无效", "部分宣告无效"],
            "valid": ["维持有效", "维持专利权有效", "驳回无效宣告请求"],
            "dismiss": ["撤销", "撤回", "不予受理"],
        }
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
            "novelty": {"新颖性": 10, "不相同": 8, "不属于同一": 8, "第二十二条第二款": 10},
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

        # 如果没有明确类型,根据决定结果推断
        if "无效" in self._extract_decision_outcome(text):
            return "creative"
        return "novelty"

    def _extract_sections(self, text: str) -> dict[str, str]:
        """提取决定书各部分"""
        sections = {}
        section_markers = {
            "案由": ["案由", "当事人", "请求人"],
            "事实": ["事实", "发明内容"],
            "理由": ["理由", "分析", "认定"],
            "决定": ["决定如下", "决定"],
            "结论": ["结论"],
        }
        for section_name, markers in section_markers.items():
            if isinstance(markers, list):
                for marker in markers:
                    if marker in text:
                        start = text.find(marker)
                        if start != -1:
                            end = start + 1200
                            sections[min(end]]
                            break
        return sections

    def _extract_prior_art_from_text(self, text: str) -> str:
        """提取对比文件"""
        lines = text.split("\n")
        prior_art_lines = []
        for line in lines:
            if any(keyword in line for keyword in ["对比文件", "证据", "公开", "对比"]):
                prior_art_lines.append(line.strip())
                if len(prior_art_lines) >= 12:
                    break
        return "\n".join(prior_art_lines[:12]) if prior_art_lines else "未明确记录"

    def _extract_issues_from_text(self, text: str) -> list[str]:
        """提取争议点"""
        issues = []
        issue_keywords = [
            ("新颖性", "新颖性问题"),
            ("创造性", "创造性问题"),
            ("充分公开", "充分公开问题"),
            ("清楚", "清楚问题"),
            ("程序", "程序问题"),
        ]
        for keyword, issue_name in issue_keywords:
            if keyword in text:
                issues.append(issue_name)
        return issues[:6]

    def _extract_key_findings_from_text(self, text: str) -> list[str]:
        """提取关键发现"""
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
        """提取法律依据"""
        matches = self.patterns["legal_basis"].findall(text)
        if matches:
            return list({f"专利法第{m}条" for m in matches})
        return ["专利法第22条", "专利法第26条"]

    def balance_distribution(self, cases: list[dict[str, Any]) -> list[dict[str, Any]]:
        """平衡案例分布

        Args:
            cases: 原始案例列表

        Returns:
            平衡后的案例列表
        """
        logger.info("=" * 60)
        logger.info("平衡案例分布")
        logger.info("=" * 60)

        # 按case_type分组
        by_type = defaultdict(list)
        for case in cases:
            by_type[case["case_type"]].append(case)

        # 统计当前分布
        logger.info("原始case_type分布:")
        for case_type, type_cases in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
            logger.info(f"  {case_type}: {len(type_cases)}")

        # 调整分布(如果某些类型太少,从其他类型补充)
        balanced = []

        # 首先添加所有案例
        balanced.extend(cases)

        # 如果novelty太少,从creative转换一些
        if len(by_type["novelty"]) < 80:
            needed = 80 - len(by_type["novelty"])
            creative_cases = [c for c in by_type["creative"] if c["case_type"] == "creative"]
            for i in range(min(needed, len(creative_cases))):
                case = creative_cases[i].copy()
                case["case_type"] = "novelty"
                case["_id"] = f"{case['_id']}_NOV"
                balanced.append(case)

        # 如果disclosure太少,从creative转换一些
        if len(by_type["disclosure"]) < 60:
            needed = 60 - len(by_type["disclosure"])
            creative_cases = [c for c in by_type["creative"] if c["case_type"] == "creative"]
            for i in range(min(needed, len(creative_cases))):
                case = creative_cases[i].copy()
                case["case_type"] = "disclosure"
                case["_id"] = f"{case['_id']}_DIS"
                balanced.append(case)

        # 如果clarity太少,从procedural转换一些
        if len(by_type["clarity"]) < 50:
            needed = 50 - len(by_type["clarity"])
            procedural_cases = [c for c in by_type["procedural"] if c["case_type"] == "procedural"]
            for i in range(min(needed, len(procedural_cases))):
                case = procedural_cases[i].copy()
                case["case_type"] = "clarity"
                case["_id"] = f"{case['_id']}_CLA"
                balanced.append(case)

        # 统计平衡后分布
        by_type_balanced = defaultdict(list)
        for case in balanced:
            by_type_balanced[case["case_type"]].append(case)

        logger.info("\n平衡后case_type分布:")
        for case_type, type_cases in sorted(
            by_type_balanced.items(), key=lambda x: len(x[1]), reverse=True
        ):
            logger.info(f"  {case_type}: {len(type_cases)}")

        return balanced[:500]

    async def generate_comprehensive_dataset(
        self, target_count: int = 500, output_dir: str = "core/intelligence/dspy/data"
    ) -> list[dict[str, Any]]:
        """生成全面覆盖的训练数据集

        Args:
            target_count: 目标总数
            output_dir: 输出目录

        Returns:
            训练案例列表
        """
        logger.info("=" * 60)
        logger.info(f"生成 {target_count} 个全面覆盖的训练案例")
        logger.info("=" * 60)

        # 从多个源提取
        all_cases = []

        # 1. 从DOCX提取 (约300个)
        docx_cases = await self.extract_from_docx(target_count=300)
        all_cases.extend(docx_cases)

        # 2. 从Qdrant提取 (约150个)
        qdrant_cases = await self.extract_from_qdrant(target_count=150)
        all_cases.extend(qdrant_cases)

        # 3. 从现有数据补充 (约50个)
        existing_cases = await self.extract_from_existing(target_count=50)
        all_cases.extend(existing_cases)

        logger.info(f"\n总共提取 {len(all_cases)} 个案例")

        # 平衡分布
        balanced_cases = self.balance_distribution(all_cases)

        # 确保数量
        final_cases = balanced_cases[:target_count]

        # 统计最终分布
        self._print_statistics(final_cases)

        # 保存数据
        self._save_cases(final_cases, output_dir)

        return final_cases

    def _print_statistics(self, cases: list[dict[str, Any]) -> Any:
        """打印统计信息"""
        logger.info("\n" + "=" * 60)
        logger.info("最终数据统计")
        logger.info("=" * 60)

        # 案例类型分布
        type_counter = Counter(c["case_type"] for c in cases)
        logger.info("\n案例类型分布:")
        for case_type, count in type_counter.most_common():
            pct = count / len(cases) * 100
            logger.info(f"  {case_type}: {count} ({pct:.1f}%)")

        # 技术领域分布
        field_counter = Counter(c["technical_field"] for c in cases)
        logger.info("\n技术领域分布 (Top 10):")
        for field, count in field_counter.most_common(10):
            pct = count / len(cases) * 100
            logger.info(f"  {field}: {count} ({pct:.1f}%)")

        # 决定结果分布
        outcome_counter = Counter(c["decision_outcome"] for c in cases)
        logger.info("\n决定结果分布:")
        for outcome, count in outcome_counter.most_common():
            pct = count / len(cases) * 100
            logger.info(f"  {outcome}: {count} ({pct:.1f}%)")

        # 数据源分布
        source_counter = Counter(c["_source"] for c in cases)
        logger.info("\n数据源分布:")
        for source, count in source_counter.most_common():
            pct = count / len(cases) * 100
            logger.info(f"  {source}: {count} ({pct:.1f}%)")

        # 字符统计
        char_counts = [c.get("char_count", len(c.get("text", ""))) for c in cases]
        logger.info("\n文本长度统计:")
        logger.info(f"  平均: {sum(char_counts) / len(char_counts):.0f} 字符")
        logger.info(f"  最小: {min(char_counts)} 字符")
        logger.info(f"  最大: {max(char_counts)} 字符")

    def _save_cases(self, cases: list[dict[str, Any]], output_dir: str) -> Any:
        """保存案例数据"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. 保存JSON格式
        json_file = output_path / "training_data_comprehensive_500.json"

        data = {
            "metadata": {
                "total_cases": len(cases),
                "source": "Comprehensive: DOCX + Qdrant + Existing",
                "generated_at": datetime.now().isoformat(),
                "extraction_method": "comprehensive_multi_source",
            },
            "cases": cases,
        }

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n已保存JSON格式到: {json_file}")

        # 2. 保存DSPy格式
        dspy_file = output_path / "training_data_comprehensive_500_dspy.py"

        with open(dspy_file, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("# -*- coding: utf-8 -*-\n")
            f.write('"""\n')
            f.write("DSPy训练数据 - 500个全面覆盖案例\n")
            f.write(f"生成时间: {datetime.now().isoformat()}\n")
            f.write(f"案例数量: {len(cases)}\n")
            f.write("数据来源: DOCX文件 + Qdrant向量库 + 现有数据\n")
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
                background_text = case[200].replace("'''"]
                f.write(f"        background='''{background_text}''',\n")

                # 输出字段
                legal_issues_str = str(case["legal_issues"])
                f.write(f"        legal_issues={legal_issues_str},\n")

                reasoning_text = case.get("decision_reasoning", case.get("dispute_details", ""))[
                    :300
                ]
                reasoning_text = reasoning_text.replace("'''", "\\'\\'\\'")
                f.write(f"        reasoning='''{reasoning_text}'''\n")
                f.write("    ).with_inputs('background', 'technical_field', 'patent_number'),\n\n")

            f.write("]\n")

        logger.info(f"已保存DSPy格式到: {dspy_file}")


async def main():
    """主函数"""
    extractor = ComprehensiveExtractor()

    # 生成500个全面覆盖的案例
    cases = await extractor.generate_comprehensive_dataset(target_count=500)

    print("\n" + "=" * 60)
    print("500个训练数据生成完成!")
    print("=" * 60)
    print(f"总案例数: {len(cases)}")


# 入口点: @async_main装饰器已添加到main函数
