#!/usr/bin/env python3
from __future__ import annotations
"""
PostgreSQL中国专利数据库迭代式搜索系统
Iterative Patent Search System for PostgreSQL Chinese Patent Database

通过迭代式搜索在专利名称、主权项和摘要中获取专利信息,
包括提取Google专利meta标签中的数据
"""

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "patent_db",
    "user": "postgres",
    "password": "postgres",
    "options": "-c client_encoding=UTF8",
}


@dataclass
class GooglePatentMeta:
    """Google专利Meta标签数据结构"""

    title: str
    abstract: str
    inventors: list[str]
    assignee: str
    publication_date: str
    application_date: str
    family_id: str
    priority_date: str
    citations_count: int
    cited_by_count: int
    ipc_codes: list[str]
    uspc_codes: list[str]
    cpc_codes: list[str]
    legal_events: list[dict]
    description: str
    claims: list[str]


@dataclass
class PatentInfo:
    """专利信息数据结构"""

    id: str
    patent_name: str
    abstract: str
    claims_content: str
    claims: list[str]
    applicant: str
    inventor: str
    application_number: str
    application_date: datetime
    publication_number: str
    publication_date: datetime
    authorization_number: str
    authorization_date: datetime
    ipc_code: str
    ipc_main_class: str
    ipc_classification: str
    citation_count: int
    cited_count: int
    google_meta: GooglePatentMeta | None = None
    relevance_score: float = 0.0


class IterativePatentSearcher:
    """迭代式专利搜索器"""

    def __init__(self):
        """初始化搜索器"""
        self.conn = None
        self.search_history = []
        self.max_iterations = 5
        self.relevance_threshold = 0.3
        self.batch_size = 100

        # 同义词词典(技术术语扩展)
        self.synonym_dict = {
            "人工智能": ["AI", "机器学习", "深度学习", "神经网络", "智能系统"],
            "机器学习": ["ML", "统计学习", "模式识别", "预测建模"],
            "深度学习": ["DL", "神经网络", "深度神经网络", "CNN", "RNN"],
            "神经网络": ["NN", "人工神经网络", "ANN", "感知器"],
            "算法": ["方法", "过程", "技术", "方案", "计算方法"],
            "系统": ["装置", "设备", "机制", "架构", "平台"],
            "方法": ["工艺", "流程", "技术", "方案", "算法"],
            "通信": ["传输", "通信技术", "数据传输", "信息传输"],
            "控制": ["管理", "调控", "监控", "优化"],
            "处理": ["加工", "分析", "计算", "操作"],
            "数据": ["信息", "信号", "数据集", "数字内容"],
            "网络": ["通信网络", "数据网络", "连接", "互联"],
        }

        # 搜索权重配置
        self.field_weights = {
            "patent_name": 0.4,  # 专利名称权重最高
            "claims_content": 0.3,  # 主权项权重次之
            "abstract": 0.2,  # 摘要权重
            "ipc_main_class": 0.1,  # IPC分类权重
        }

        logger.info("🔍 迭代式专利搜索器初始化完成")

    def connect(self) -> Any:
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
            logger.info("✅ 成功连接到PostgreSQL专利数据库")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e!s}")
            raise

    def disconnect(self) -> Any:
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("📌 数据库连接已关闭")

    def _normalize_text(self, text: str) -> str:
        """文本标准化处理"""
        if not text:
            return ""
        # 转换为小写
        text = text.lower()
        # 移除特殊字符,保留中英文和数字
        text = re.sub(r"[^\u4e00-\u9fa5a-z_a-Z0-9\s]", " ", text)
        # 合并多个空格
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _expand_keywords(self, query: str) -> list[str]:
        """扩展查询关键词"""
        expanded = [query]
        normalized_query = self._normalize_text(query)

        for keyword, synonyms in self.synonym_dict.items():
            if keyword in normalized_query:
                expanded.extend(synonyms)
            for syn in synonyms:
                if syn.lower() in normalized_query:
                    expanded.append(keyword)

        # 去重
        return list(set(expanded))

    def _build_search_query(self, keywords: list[str], iteration: int = 1) -> str:
        """构建搜索查询SQL"""
        conditions = []
        params = []

        for _i, keyword in enumerate(keywords):
            # 专利名称搜索(最高权重)
            conditions.append("LOWER(patent_name) LIKE %s")
            params.append(f"%{keyword.lower()}%")

            # 主权项搜索
            conditions.append("LOWER(claims_content) LIKE %s")
            params.append(f"%{keyword.lower()}%")

            # 摘要搜索
            conditions.append("LOWER(abstract) LIKE %s")
            params.append(f"%{keyword.lower()}%")

            # IPC分类搜索
            conditions.append("LOWER(ipc_main_class) LIKE %s")
            params.append(f"%{keyword.lower()}%")

        # 使用OR连接所有条件,匹配任一关键词
        base_query = f"""
        SELECT *,
               -- 计算相关性分数
               (
                   CASE WHEN LOWER(patent_name) LIKE %s THEN 1 ELSE 0 END * 0.4 +
                   CASE WHEN LOWER(claims_content) LIKE %s THEN 1 ELSE 0 END * 0.3 +
                   CASE WHEN LOWER(abstract) LIKE %s THEN 1 ELSE 0 END * 0.2 +
                   CASE WHEN LOWER(ipc_main_class) LIKE %s THEN 1 ELSE 0 END * 0.1
               ) as relevance_score
        FROM patents
        WHERE ({' OR '.join(conditions)})
        AND (patent_name IS NOT NULL OR abstract IS NOT NULL OR claims_content IS NOT NULL)
        ORDER BY relevance_score DESC, citation_count DESC
        LIMIT %s
        """

        # 添加原始查询的全文匹配参数
        main_keyword = keywords[0].lower()
        all_params = (
            [
                f"%{main_keyword}%",  # patent_name
                f"%{main_keyword}%",  # claims_content
                f"%{main_keyword}%",  # abstract
                f"%{main_keyword}%",  # ipc_main_class
            ]
            + params
            + [self.batch_size]
        )

        return base_query, all_params

    def _extract_google_meta_data(self, patent_data: dict) -> GooglePatentMeta:
        """从专利数据中提取Google专利meta标签信息"""
        # 这里模拟从专利数据提取meta信息
        # 实际应用中可能需要调用Google Patents API或爬取数据

        return GooglePatentMeta(
            title=patent_data.get("patent_name", ""),
            abstract=patent_data.get("abstract", ""),
            inventors=self._parse_inventors(patent_data.get("inventor", "")),
            assignee=patent_data.get("current_assignee", patent_data.get("applicant", "")),
            publication_date=str(patent_data.get("publication_date", "")),
            application_date=str(patent_data.get("application_date", "")),
            family_id=patent_data.get("application_number", ""),
            priority_date=str(patent_data.get("application_date", "")),
            citations_count=patent_data.get("citation_count", 0),
            cited_by_count=patent_data.get("cited_count", 0),
            ipc_codes=self._parse_ipc_codes(patent_data.get("ipc_classification", "")),
            uspc_codes=[],
            cpc_codes=self._parse_cpc_codes(patent_data.get("ipc_classification", "")),
            legal_events=[],
            description=patent_data.get("abstract", ""),
            claims=self._parse_claims(patent_data.get("claims_content", "")),
        )

    def _parse_inventors(self, inventor_str: str) -> list[str]:
        """解析发明人列表"""
        if not inventor_str:
            return []
        # 分割发明人,常见分隔符:;;、,
        inventors = re.split(r"[;;,,、]", inventor_str)
        return [inv.strip() for inv in inventors if inv.strip()]

    def _parse_ipc_codes(self, ipc_str: str) -> list[str]:
        """解析IPC分类号"""
        if not ipc_str:
            return []
        # 提取IPC分类号格式(如G06F 17/00)
        ipc_pattern = r"[A-H]\d{2}[A-Z]\s*\d{1,4}/\d{2,4}"
        matches = re.findall(ipc_pattern, ipc_str)
        return matches

    def _parse_cpc_codes(self, ipc_str: str) -> list[str]:
        """解析CPC分类号(基于IPC数据转换)"""
        return self._parse_ipc_codes(ipc_str)  # 简化处理

    def _parse_claims(self, claims_str: str) -> list[str]:
        """解析权利要求"""
        if not claims_str:
            return []
        # 按权利要求编号分割
        claims = re.split(r"\n\s*\d+\.\s*", claims_str.strip())
        return [claim.strip() for claim in claims if claim.strip()]

    def _calculate_completeness_score(self, patent: dict) -> float:
        """计算专利信息完整度分数"""
        fields = [
            "patent_name",
            "abstract",
            "claims_content",
            "applicant",
            "inventor",
            "application_number",
            "publication_number",
            "ipc_code",
            "application_date",
            "publication_date",
        ]

        filled_fields = sum(1 for field in fields if patent.get(field))
        return filled_fields / len(fields)

    async def search(self, query: str, max_results: int = 50) -> list[PatentInfo]:
        """执行迭代式搜索"""
        logger.info(f"🔍 开始迭代式搜索: {query}")

        all_results = []
        searched_ids = set()
        keywords = self._expand_keywords(query)

        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"📝 执行第{iteration}轮搜索...")

            # 构建查询
            search_query, params = self._build_search_query(keywords, iteration)

            try:
                with self.conn.cursor() as cursor:
                    cursor.execute(search_query, params)
                    results = cursor.fetchall()

                    if not results:
                        logger.info(f"第{iteration}轮搜索未找到结果")
                        break

                    # 处理搜索结果
                    iteration_results = []
                    for row in results:
                        patent_id = str(row["id"])

                        # 跳过已搜索的专利
                        if patent_id in searched_ids:
                            continue

                        searched_ids.add(patent_id)

                        # 提取Google专利meta数据
                        google_meta = self._extract_google_meta_data(dict(row))

                        # 创建专利信息对象
                        patent_info = PatentInfo(
                            id=patent_id,
                            patent_name=row.get("patent_name", ""),
                            abstract=row.get("abstract", ""),
                            claims_content=row.get("claims_content", ""),
                            claims=self._parse_claims(row.get("claims_content", "")),
                            applicant=row.get("applicant", ""),
                            inventor=row.get("inventor", ""),
                            application_number=row.get("application_number", ""),
                            application_date=row.get("application_date"),
                            publication_number=row.get("publication_number", ""),
                            publication_date=row.get("publication_date"),
                            authorization_number=row.get("authorization_number", ""),
                            authorization_date=row.get("authorization_date"),
                            ipc_code=row.get("ipc_code", ""),
                            ipc_main_class=row.get("ipc_main_class", ""),
                            ipc_classification=row.get("ipc_classification", ""),
                            citation_count=row.get("citation_count", 0) or 0,
                            cited_count=row.get("cited_count", 0) or 0,
                            google_meta=google_meta,
                            relevance_score=float(row.get("relevance_score", 0)),
                        )

                        # 计算完整度分数
                        completeness = self._calculate_completeness_score(dict(row))
                        patent_info.relevance_score = (
                            patent_info.relevance_score * 0.7 + completeness * 0.3
                        )

                        # 过滤低相关性结果
                        if patent_info.relevance_score >= self.relevance_threshold:
                            iteration_results.append(patent_info)

                    all_results.extend(iteration_results)
                    logger.info(f"第{iteration}轮搜索找到{len(iteration_results)}个新结果")

                    # 如果没有找到新结果,提前结束
                    if len(iteration_results) == 0:
                        break

                    # 如果已达到最大结果数,结束搜索
                    if len(all_results) >= max_results:
                        break

                    # 基于当前结果优化关键词
                    if iteration < self.max_iterations and iteration_results:
                        self._optimize_keywords(keywords, iteration_results)

            except Exception as e:
                logger.error(f"第{iteration}轮搜索出错: {e!s}")
                continue

        # 排序并返回结果
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        final_results = all_results[:max_results]

        # 记录搜索历史
        self.search_history.append(
            {
                "query": query,
                "timestamp": datetime.now(),
                "results_count": len(final_results),
                "iterations": iteration,
            }
        )

        logger.info(f"✅ 搜索完成,共找到{len(final_results)}个专利")
        return final_results

    def _optimize_keywords(self, keywords: list[str], results: list[PatentInfo]) -> Any:
        """基于搜索结果优化关键词"""
        # 从高相关性结果中提取新的关键词
        new_keywords = []

        for patent in results[:5]:  # 取前5个最相关的结果
            # 从IPC分类中提取
            if patent.ipc_main_class and len(patent.ipc_main_class) > 3:
                new_keywords.append(patent.ipc_main_class[:3])

            # 从申请人中提取(如果是知名公司)
            applicant = patent.applicant
            if applicant and any(keyword in applicant for keyword in ["有限公司", "科技", "大学"]):
                # 提取公司名的关键部分
                key_parts = re.findall(
                    r"([^\uff0c\u3001()()]+)(科技|大学|研究院|公司)", applicant
                )
                if key_parts:
                    new_keywords.append(key_parts[0][0])

        # 添加新关键词
        keywords.extend([kw for kw in new_keywords if kw not in keywords])
        keywords = list(set(keywords))  # 去重

        logger.info(f"🔄 优化后的关键词: {keywords}")

    def export_results(
        self, results: list[PatentInfo], output_file: str, format: str = "json"
    ) -> Any:
        """导出搜索结果"""
        try:
            if format.lower() == "json":
                data = {
                    "search_time": datetime.now().isoformat(),
                    "total_results": len(results),
                    "patents": [],
                }

                for patent in results:
                    patent_dict = asdict(patent)
                    if patent.google_meta:
                        patent_dict["google_meta"] = asdict(patent.google_meta)
                    data["patents"].append(patent_dict)

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            elif format.lower() == "csv":
                import csv

                fields = [
                    "id",
                    "patent_name",
                    "abstract",
                    "applicant",
                    "inventor",
                    "application_number",
                    "publication_number",
                    "ipc_main_class",
                    "citation_count",
                    "cited_count",
                    "relevance_score",
                ]

                with open(output_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()

                    for patent in results:
                        row = {field: getattr(patent, field, "") for field in fields}
                        writer.writerow(row)

            logger.info(f"✅ 结果已导出到: {output_file}")

        except Exception as e:
            logger.error(f"❌ 导出失败: {e!s}")
            raise


# 使用示例
async def main():
    """主函数示例"""
    searcher = IterativePatentSearcher()

    try:
        # 连接数据库
        searcher.connect()

        # 执行搜索
        query = "深度学习 图像识别"
        results = await searcher.search(query, max_results=20)

        # 打印结果
        logger.info(f"\n🎯 搜索结果: {len(results)}个专利")
        logger.info(str("-" * 100))

        for i, patent in enumerate(results[:5], 1):
            logger.info(f"\n{i}. {patent.patent_name}")
            logger.info(f"   申请号: {patent.application_number}")
            logger.info(f"   申请人: {patent.applicant}")
            logger.info(f"   摘要: {patent.abstract[:100]}...")
            logger.info(f"   相关性评分: {patent.relevance_score:.2f}")

            if patent.google_meta:
                meta = patent.google_meta
                logger.info(f"   Google Meta - 发明人: {', '.join(meta.inventors[:2])}")
                logger.info(f"   Google Meta - 引用数: {meta.citations_count}")

        # 导出结果
        searcher.export_results(results, "patent_search_results.json")

    finally:
        # 断开连接
        searcher.disconnect()


# 入口点: @async_main装饰器已添加到main函数
