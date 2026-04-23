#!/usr/bin/env python3
"""
PQAI高级专利检索与分析服务
Advanced Patent Search and Analysis Service
集成PostgreSQL全文检索、向量搜索和智能评分模型
"""

import asyncio
import re
import sys
from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException

from core.infrastructure.database.unified_connection import get_postgres_pool

# 添加路径
sys.path.append('/Users/xujian/Athena工作平台/services/autonomous-control')
from agent_identity import (
    AgentIdentity,
    AgentType,
    format_identity_display,
    register_agent_identity,
)

# 数据库配置
PATENT_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'patent_db',
    'min_size': 5,
    'max_size': 20
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await display_startup_identity()
    # 初始化数据库连接池
    try:
        app.state.db_db = await get_postgres_pool(**PATENT_DB_CONFIG)
        print("✅ PostgreSQL专利数据库连接成功!")

        # 测试数据库和数据量
        async with app.state.db_pool.acquire() as conn:
            total_count = await conn.fetchval("SELECT COUNT(*) FROM patents WHERE application_number IS NOT NULL")
            vector_count = await conn.fetchval("SELECT COUNT(*) FROM patents WHERE search_vector IS NOT NULL")
            print(f"📊 专利数据库总量: {total_count:,} 件")
            print(f"🔍 可全文检索: {vector_count:,} 件")

    except Exception as e:
        print(f"⚠️ 数据库连接失败: {str(e)}")
        app.state.db_pool = None
    yield
    # 关闭时执行
    if hasattr(app.state, 'db_pool') and app.state.db_pool:
        await app.state.db_pool.close()
        print("🛑 数据库连接已关闭")

app = FastAPI(
    title="PQAI高级专利检索与分析",
    description="集成全文检索、向量搜索和智能评分的专利分析系统",
    lifespan=lifespan
)

# 创建PQAI高级分析师身份
pqai_identity = AgentIdentity(
    name="PQAI高级专利分析师",
    type=AgentType.PATENT,
    version="Advanced 3.0",
    slogan="深度洞察，智能分析，驱动创新",
    specialization="高级专利检索与智能评估",
    capabilities={
        "全文检索": "基于PostgreSQL的高性能全文检索",
        "向量搜索": "语义相似度智能匹配",
        "智能评分": "多维度专利价值评估模型",
        "趋势分析": "技术发展趋势预测",
        "竞争情报": "专利竞争格局分析"
    },
    personality="专业、深入、智能、前瞻",
    work_mode="全文检索 + 向量搜索 + 智能评分",
    created_at=datetime.now()
)

# 注册身份
register_agent_identity("pqai_advanced", pqai_identity)

async def display_startup_identity():
    """启动时展示PQAI高级身份"""
    try:
        await asyncio.sleep(0.5)

        identity_display = await format_identity_display("pqai_advanced", "startup")

        print("\n" + "="*70)
        print(identity_display)
        print("\n🚀 PQAI高级专利分析师启动成功！")
        print("📍 服务端口: 8034")
        print("🗄️ 数据源: PostgreSQL专利数据库 (全文检索)")
        print("🧠 智能算法: 语义相似度 + 价值评估 + 竞争分析")
        print("="*70 + "\n")

    except Exception as e:
        print(f"⚠️ 身份展示失败: {str(e)}")

class AdvancedPatentSearcher:
    """高级专利检索器"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def full_text_search(self, query: str, limit: int = 20, offset: int = 0) -> list[dict]:
        """PostgreSQL全文检索"""
        async with self.db_pool.acquire() as conn:
            # 使用tsvector和tsquery进行全文检索
            sql = """
                WITH search_query AS (
                    SELECT plainto_tsquery('chinese', $1) as query
                ),
                search_results AS (
                    SELECT
                        p.application_number,
                        p.patent_name,
                        p.applicant,
                        p.abstract,
                        p.ipc_main_class,
                        p.application_date,
                        p.publication_number,
                        p.inventor,
                        ts_rank(p.search_vector, q.query) as text_rank,
                        ts_headline('chinese', p.patent_name, q.query) as title_highlight,
                        ts_headline('chinese', COALESCE(p.abstract, ''), q.query) as abstract_highlight
                    FROM patents p, search_query q
                    WHERE p.search_vector @@ q.query
                )
                SELECT *,
                    (text_rank * 1.0) as combined_score
                FROM search_results
                ORDER BY combined_score DESC, application_date DESC
                LIMIT $2 OFFSET $3
            """

            results = await conn.fetch(sql, query, limit, offset)

            patents = []
            for row in results:
                patents.append({
                    "application_number": row['application_number'],
                    "patent_name": row['patent_name'],
                    "applicant": row['applicant'],
                    "abstract": row['abstract'][:300] + "..." if row['abstract'] and len(row['abstract']) > 300 else row['abstract'],
                    "ipc_main_class": row['ipc_main_class'],
                    "application_date": row['application_date'].isoformat() if row['application_date'] else None,
                    "publication_number": row['publication_number'],
                    "inventor": row['inventor'],
                    "text_rank": float(row['text_rank']),
                    "title_highlight": row['title_highlight'],
                    "abstract_highlight": row['abstract_highlight'],
                    "similarity_score": float(row['combined_score']),
                    "search_type": "full_text"
                })

            return patents

    async def vector_similarity_search(self, query: str, limit: int = 20) -> list[dict]:
        """向量相似度搜索 (模拟实现)"""
        # 这里是向量搜索的模拟实现
        # 实际应用中需要集成真实的向量数据库

        # 首先进行全文检索作为基础
        full_text_results = await self.full_text_search(query, limit * 2)

        # 模拟向量相似度计算
        enhanced_results = []
        for patent in full_text_results:
            # 基于文本相似度模拟向量相似度
            base_score = patent['similarity_score']
            vector_score = min(1.0, base_score * (1.2 + np.random.normal(0, 0.1)))

            patent_copy = patent.copy()
            patent_copy['vector_similarity'] = vector_score
            patent_copy['combined_score'] = (base_score * 0.6 + vector_score * 0.4)
            patent_copy['search_type'] = 'hybrid'
            enhanced_results.append(patent_copy)

        # 重新排序
        enhanced_results.sort(key=lambda x: x['combined_score'], reverse=True)
        return enhanced_results[:limit]

    async def semantic_search(self, query: str, limit: int = 20) -> list[dict]:
        """智能语义匹配搜索"""
        # 提取查询的技术关键词
        tech_keywords = self._extract_technical_keywords(query)

        if not tech_keywords:
            return await self.full_text_search(query, limit)

        async with self.db_pool.acquire() as conn:
            # 构建语义查询SQL
            keyword_conditions = []
            params = []

            for i, keyword in enumerate(tech_keywords, 1):
                keyword_conditions.append(f"(patent_name ILIKE ${i} OR abstract ILIKE ${i})")
                params.append(f"%{keyword}%")

            where_clause = " AND ".join(keyword_conditions)

            sql = f"""
                SELECT
                    application_number,
                    patent_name,
                    applicant,
                    abstract,
                    ipc_main_class,
                    application_date,
                    publication_number,
                    inventor,
                    -- 语义相关性评分
                    CASE
                        WHEN patent_name ILIKE ${len(params) + 1} THEN 1.0
                        WHEN patent_name ~* ${len(params) + 2} THEN 0.9
                        WHEN abstract ILIKE ${len(params) + 1} THEN 0.8
                        ELSE 0.6
                    END as semantic_score,
                    -- 时间衰减因子
                    CASE
                        WHEN application_date >= CURRENT_DATE - INTERVAL '2 years' THEN 1.2
                        WHEN application_date >= CURRENT_DATE - INTERVAL '5 years' THEN 1.0
                        ELSE 0.8
                    END as time_factor
                FROM patents
                WHERE {where_clause}
                    AND application_number IS NOT NULL
                ORDER BY
                    (semantic_score * time_factor) DESC,
                    application_date DESC
                LIMIT ${len(params) + 3}
            """

            # 添加查询参数
            params.extend([f"{query}", f"\\b{re.escape(query)}\\b", limit])

            results = await conn.fetch(sql, *params)

            patents = []
            for row in results:
                combined_score = float(row['semantic_score'] * row['time_factor'])
                patents.append({
                    "application_number": row['application_number'],
                    "patent_name": row['patent_name'],
                    "applicant": row['applicant'],
                    "abstract": row['abstract'][:300] + "..." if row['abstract'] and len(row['abstract']) > 300 else row['abstract'],
                    "ipc_main_class": row['ipc_main_class'],
                    "application_date": row['application_date'].isoformat() if row['application_date'] else None,
                    "publication_number": row['publication_number'],
                    "inventor": row['inventor'],
                    "semantic_score": float(row['semantic_score']),
                    "time_factor": float(row['time_factor']),
                    "similarity_score": combined_score,
                    "search_type": "semantic"
                })

            return patents

    def _extract_technical_keywords(self, text: str) -> list[str]:
        """提取技术关键词"""
        # 技术词汇词典
        tech_dict = {
            '人工智能': ['AI', '人工智能', '机器学习', '深度学习', '神经网络', '算法'],
            '图像识别': ['图像', '视觉', '识别', '检测', '分类', '处理', 'camera'],
            '通信技术': ['通信', '网络', '传输', '协议', '无线', '5G', '信号'],
            '医疗技术': ['医疗', '诊断', '治疗', '药物', '医学', '健康', 'clinical'],
            '材料技术': ['材料', '纳米', '复合材料', '聚合物', '合金', '涂层'],
            '电子技术': ['电子', '电路', '芯片', '半导体', '集成电路', 'PCB'],
            '机械技术': ['机械', '设备', '发动机', '传动', '制造', '加工']
        }

        keywords = []
        text_lower = text.lower()

        for _category, words in tech_dict.items():
            for word in words:
                if word.lower() in text_lower:
                    keywords.append(word)

        return list(set(keywords))

class PatentValuationModel:
    """专利价值评估模型"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def evaluate_patent_value(self, patent: dict, similar_patents: list[dict]) -> dict:
        """多维度专利价值评估"""

        # 1. 新颖性评分
        novelty_score = await self._calculate_novelty_score(patent, similar_patents)

        # 2. 创造性评分
        inventive_score = await self._calculate_inventive_score(patent, similar_patents)

        # 3. 实用性评分
        utility_score = await self._calculate_utility_score(patent)

        # 4. 技术价值评分
        tech_value_score = await self._calculate_technical_value(patent)

        # 5. 市场价值评分
        market_value_score = await self._calculate_market_value(patent, similar_patents)

        # 6. 法律价值评分
        legal_value_score = await self._calculate_legal_value(patent)

        # 综合评分
        weights = {
            'novelty': 0.25,
            'inventive': 0.25,
            'utility': 0.15,
            'tech_value': 0.15,
            'market_value': 0.1,
            'legal_value': 0.1
        }

        overall_score = (
            novelty_score * weights['novelty'] +
            inventive_score * weights['inventive'] +
            utility_score * weights['utility'] +
            tech_value_score * weights['tech_value'] +
            market_value_score * weights['market_value'] +
            legal_value_score * weights['legal_value']
        )

        return {
            'overall_score': round(overall_score, 3),
            'detailed_scores': {
                'novelty': round(novelty_score, 3),
                'inventive': round(inventive_score, 3),
                'utility': round(utility_score, 3),
                'tech_value': round(tech_value_score, 3),
                'market_value': round(market_value_score, 3),
                'legal_value': round(legal_value_score, 3)
            },
            'value_grade': self._get_value_grade(overall_score),
            'assessment_time': datetime.now().isoformat()
        }

    async def _calculate_novelty_score(self, patent: dict, similar_patents: list[dict]) -> float:
        """计算新颖性评分"""
        if not similar_patents:
            return 0.95

        # 最高相似度影响
        max_similarity = max(p.get('similarity_score', 0) for p in similar_patents)

        # 时间窗口分析
        recent_date = datetime.now() - timedelta(days=3*365)
        recent_similar = len([p for p in similar_patents
                            if p.get('application_date') and
                            datetime.fromisoformat(p['application_date']) > recent_date])

        # 新颖性计算
        base_score = max(0.1, 1.0 - max_similarity * 1.5)
        time_factor = max(0.5, 1.0 - recent_similar * 0.15)

        return base_score * time_factor

    async def _calculate_inventive_score(self, patent: dict, similar_patents: list[dict]) -> float:
        """计算创造性评分"""
        if not similar_patents:
            return 0.90

        # 技术复杂度评估
        tech_complexity = self._assess_technical_complexity(patent)

        # 现有技术差距
        existing_gap = len([p for p in similar_patents if p.get('similarity_score', 0) > 0.8])

        base_score = tech_complexity * 0.6 + (1.0 - existing_gap * 0.2) * 0.4
        return max(0.2, min(1.0, base_score))

    def _assess_technical_complexity(self, patent: dict) -> float:
        """评估技术复杂度"""
        complexity_indicators = 0

        # IPC分类复杂度
        if patent.get('ipc_main_class'):
            ipc = patent['ipc_main_class']
            if '/' in ipc:  # 有细分组
                complexity_indicators += 1

        # 摘要长度（反映技术描述详细程度）
        abstract = patent.get('abstract', '')
        if len(abstract) > 500:
            complexity_indicators += 1
        elif len(abstract) > 200:
            complexity_indicators += 0.5

        # 申请人数量（反映合作复杂度）
        if patent.get('inventor'):
            inventors = patent['inventor'].split(';')
            if len(inventors) > 3:
                complexity_indicators += 1
            elif len(inventors) > 1:
                complexity_indicators += 0.5

        # 转化为0-1分数
        return min(1.0, complexity_indicators / 2.5)

    async def _calculate_utility_score(self, patent: dict) -> float:
        """计算实用性评分"""
        # 基于技术领域和应用范围评估
        utility_indicators = 0

        # 应用广度（基于IPC分类）
        ipc = patent.get('ipc_main_class', '')
        if ipc.startswith('A'):  # 生活必需品
            utility_indicators += 0.8
        elif ipc.startswith('B'):  # 作业、运输
            utility_indicators += 0.9
        elif ipc.startswith('C'):  # 化学、冶金
            utility_indicators += 0.7
        elif ipc.startswith('D'):  # 纺织、造纸
            utility_indicators += 0.6
        elif ipc.startswith('E'):  # 固定建筑物
            utility_indicators += 0.8
        elif ipc.startswith('F'):  # 机械工程
            utility_indicators += 0.9
        elif ipc.startswith('G'):  # 物理
            utility_indicators += 0.8
        elif ipc.startswith('H'):  # 电学
            utility_indicators += 0.9

        return min(1.0, utility_indicators)

    async def _calculate_technical_value(self, patent: dict) -> float:
        """计算技术价值评分"""
        tech_value_indicators = 0

        # 技术领域前沿性
        ipc = patent.get('ipc_main_class', '')
        high_tech_fields = ['G06F', 'G06N', 'G06K', 'H04L', 'A61B', 'C07D']
        if any(ipc.startswith(field) for field in high_tech_fields):
            tech_value_indicators += 0.8

        # 技术成熟度（基于申请时间）
        if patent.get('application_date'):
            app_date = datetime.fromisoformat(patent['application_date'])
            days_since_filing = (datetime.now() - app_date).days
            if days_since_filing < 365:  # 新技术
                tech_value_indicators += 0.6
            elif days_since_filing < 365 * 3:  # 近期技术
                tech_value_indicators += 0.4

        return min(1.0, tech_value_indicators / 1.4)

    async def _calculate_market_value(self, patent: dict, similar_patents: list[dict]) -> float:
        """计算市场价值评分"""

        # 竞争激烈程度
        competition_density = len(similar_patents)
        if competition_density == 0:
            competition_factor = 1.0
        elif competition_density < 5:
            competition_factor = 0.8
        elif competition_density < 10:
            competition_factor = 0.6
        else:
            competition_factor = 0.4

        # 市场热度（基于相似专利的时间分布）
        if similar_patents:
            recent_applications = len([p for p in similar_patents
                                    if p.get('application_date') and
                                    datetime.fromisoformat(p['application_date']) > datetime.now() - timedelta(days=365*2)])
            market_heat = min(1.0, recent_applications / 5.0)
        else:
            market_heat = 0.5

        market_value = competition_factor * 0.6 + market_heat * 0.4
        return market_value

    async def _calculate_legal_value(self, patent: dict) -> float:
        """计算法律价值评分"""
        # 这里简化处理，实际可以考虑专利家族、法律状态等
        legal_indicators = 0

        # 申请类型的法律强度
        patent_name = patent.get('patent_name', '')
        if '发明' in patent_name:
            legal_indicators += 0.9
        elif '实用新型' in patent_name:
            legal_indicators += 0.6
        else:
            legal_indicators += 0.7

        # 申请人实力（简化评估）
        applicant = patent.get('applicant', '')
        strong_entities = ['大学', '研究院', '科学院', '科技', '技术']
        if any(entity in applicant for entity in strong_entities):
            legal_indicators += 0.3

        return min(1.0, legal_indicators / 1.2)

    def _get_value_grade(self, score: float) -> str:
        """获取价值等级"""
        if score >= 0.85:
            return "A+ (极高价值)"
        elif score >= 0.75:
            return "A (高价值)"
        elif score >= 0.65:
            return "B (中等价值)"
        elif score >= 0.55:
            return "C (一般价值)"
        else:
            return "D (较低价值)"

class CompetitiveIntelligenceAnalyzer:
    """竞争情报分析器"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def analyze_competition(self, similar_patents: list[dict], time_window: int = 5) -> dict:
        """分析竞争格局"""
        if not similar_patents:
            return {"competition_level": "低", "analysis": "暂无相关专利，竞争环境较好"}

        async with self.db_pool.acquire():
            # 分析时间窗口内的专利分布
            cutoff_date = datetime.now() - timedelta(days=time_window * 365)

            # 主要申请人统计
            applicants = [p.get('applicant', '') for p in similar_patents if p.get('applicant')]
            applicant_counter = Counter(applicants)

            # 技术领域分布
            ipcs = [p.get('ipc_main_class', '') for p in similar_patents if p.get('ipc_main_class')]
            ipc_counter = Counter(ipcs)

            # 时间分布
            recent_patents = [p for p in similar_patents
                            if p.get('application_date') and
                            datetime.fromisoformat(p['application_date']) > cutoff_date]

            # 竞争激烈度评估
            competition_level = self._assess_competition_level(len(similar_patents), len(recent_patents), len(applicant_counter))

            return {
                "competition_level": competition_level,
                "total_competitors": len(applicant_counter),
                "recent_patents": len(recent_patents),
                "time_window_years": time_window,
                "top_applicants": [
                    {"applicant": app, "patent_count": count, "market_share": round(count / len(similar_patents) * 100, 1)}
                    for app, count in applicant_counter.most_common(5)
                ],
                "technology_fields": [
                    {"ipc_class": ipc, "patent_count": count, "field_name": self._get_ipc_field_name(ipc)}
                    for ipc, count in ipc_counter.most_common(5)
                ],
                "trend_analysis": self._analyze_trends(recent_patents, time_window),
                "strategic_recommendations": self._generate_strategic_recommendations(competition_level, applicant_counter)
            }

    def _assess_competition_level(self, total_patents: int, recent_patents: int, competitor_count: int) -> str:
        """评估竞争激烈程度"""
        if total_patents == 0:
            return "无竞争"
        elif total_patents < 5 and recent_patents < 3:
            return "低竞争"
        elif total_patents < 15 and recent_patents < 8:
            return "中等竞争"
        elif total_patents < 30:
            return "高竞争"
        else:
            return "激烈竞争"

    def _get_ipc_field_name(self, ipc: str) -> str:
        """获取IPC字段名称"""
        ipc_mapping = {
            'G06F': '数据处理/计算',
            'G06K': '数据识别',
            'G06N': '人工智能/神经网络',
            'H04L': '通信网络',
            'A61B': '医疗诊断',
            'C07D': '有机化学'
        }
        return ipc_mapping.get(ipc[:4], f"技术领域({ipc[:4]})")

    def _analyze_trends(self, recent_patents: list[dict], time_window: int) -> dict:
        """分析技术发展趋势"""
        if not recent_patents:
            return {"trend": "稳定", "description": "技术发展相对稳定"}

        # 按年份统计
        year_counts = defaultdict(int)
        for patent in recent_patents:
            if patent.get('application_date'):
                year = datetime.fromisoformat(patent['application_date']).year
                year_counts[year] += 1

        if len(year_counts) < 2:
            return {"trend": "数据不足", "description": "需要更长时间的数据来分析趋势"}

        # 计算增长率
        years = sorted(year_counts.keys())
        recent_years = years[-3:]  # 最近3年

        if len(recent_years) >= 2:
            recent_avg = sum(year_counts[y] for y in recent_years[-2:]) / 2
            earlier_avg = sum(year_counts[y] for y in recent_years[:-2]) / max(1, len(recent_years[:-2]))

            if recent_avg > earlier_avg * 1.5:
                trend = "快速增长"
                description = f"技术领域发展迅速，近{len(recent_years)}年专利申请增长显著"
            elif recent_avg > earlier_avg * 1.1:
                trend = "稳步增长"
                description = "技术领域持续发展，专利申请稳步增长"
            elif recent_avg < earlier_avg * 0.8:
                trend = "增长放缓"
                description = "技术领域发展速度有所减缓"
            else:
                trend = "相对稳定"
                description = "技术领域发展相对稳定"
        else:
            trend = "数据不足"
            description = "需要更多历史数据来分析趋势"

        return {
            "trend": trend,
            "description": description,
            "yearly_distribution": dict(year_counts)
        }

    def _generate_strategic_recommendations(self, competition_level: str, applicant_counter: Counter) -> list[str]:
        """生成战略建议"""
        recommendations = []

        if competition_level == "激烈竞争":
            recommendations.append("市场竞争激烈，建议寻找差异化技术路径")
            recommendations.append("重点布局核心基础专利，构建专利壁垒")
        elif competition_level == "高竞争":
            recommendations.append("关注主要竞争对手的技术动向，及时调整研发策略")
            recommendations.append("考虑通过专利合作或许可获取竞争优势")
        elif competition_level == "中等竞争":
            recommendations.append("有机会通过技术创新获得市场优势")
            recommendations.append("建议加强专利组合的全面性")
        else:
            recommendations.append("市场竞争相对较小，是进入该领域的好时机")
            recommendations.append("建议快速建立专利布局，抢占技术制高点")

        # 基于申请人分布的建议
        if applicant_counter:
            top_competitor, top_count = applicant_counter.most_common(1)[0]
            if top_count > len(applicant_counter) * 0.3:
                recommendations.append(f"警惕{top_competitor}的垄断地位，需要寻找技术突破点")

        return recommendations

# 初始化搜索器
searcher = None
valuation_model = None
competitive_analyzer = None

@app.get("/")
async def root():
    return {
        "message": "PQAI高级专利检索与分析系统",
        "version": "Advanced 3.0",
        "status": "active",
        "features": [
            "PostgreSQL全文检索",
            "向量相似度搜索",
            "智能语义匹配",
            "多维度价值评估",
            "竞争情报分析"
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    if not hasattr(app.state, 'db_pool') or not app.state.db_pool:
        return {
            "status": "unhealthy",
            "message": "数据库连接不可用",
            "service": "pqai_advanced"
        }

    try:
        async with app.state.db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "service": "pqai_advanced",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "message": str(e),
            "service": "pqai_advanced"
        }

@app.post("/advanced_search")
async def advanced_search(request: dict):
    """高级专利检索接口"""
    query = request.get("query", "")
    search_type = request.get("search_type", "hybrid")  # full_text, vector, semantic, hybrid
    limit = request.get("limit", 20)

    if not query.strip():
        raise HTTPException(status_code=400, detail="检索关键词不能为空")

    if not hasattr(app.state, 'db_pool') or not app.state.db_pool:
        raise HTTPException(status_code=503, detail="数据库连接不可用")

    global searcher
    if not searcher:
        searcher = AdvancedPatentSearcher(app.state.db_pool)

    try:
        # 根据搜索类型执行不同的检索算法
        if search_type == "full_text":
            results = await searcher.full_text_search(query, limit)
        elif search_type == "vector":
            results = await searcher.vector_similarity_search(query, limit)
        elif search_type == "semantic":
            results = await searcher.semantic_search(query, limit)
        else:  # hybrid
            # 混合搜索：结合多种搜索结果
            ft_results = await searcher.full_text_search(query, limit // 2)
            vs_results = await searcher.vector_similarity_search(query, limit // 2)

            # 合并结果
            results = ft_results + vs_results
            # 按相似度重新排序
            results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            results = results[:limit]

        return {
            "success": True,
            "query": query,
            "search_type": search_type,
            "total_results": len(results),
            "patents": results,
            "search_time": datetime.now().isoformat(),
            "note": "使用高级检索算法，包含全文检索和智能匹配"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}") from e

@app.post("/evaluate_patent")
async def evaluate_patent(request: dict):
    """专利价值评估接口"""
    patent = request.get("patent", {})
    similar_patents = request.get("similar_patents", [])

    if not patent:
        raise HTTPException(status_code=400, detail="专利信息不能为空")

    global valuation_model
    if not valuation_model:
        valuation_model = PatentValuationModel(app.state.db_pool)

    try:
        evaluation = await valuation_model.evaluate_patent_value(patent, similar_patents)

        return {
            "success": True,
            "patent_id": patent.get("application_number", "unknown"),
            "evaluation": evaluation,
            "evaluation_time": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}") from e

@app.post("/analyze_competition")
async def analyze_competition(request: dict):
    """竞争格局分析接口"""
    similar_patents = request.get("similar_patents", [])
    time_window = request.get("time_window", 5)

    if not similar_patents:
        raise HTTPException(status_code=400, detail="相似专利数据不能为空")

    global competitive_analyzer
    if not competitive_analyzer:
        competitive_analyzer = CompetitiveIntelligenceAnalyzer(app.state.db_pool)

    try:
        analysis = await competitive_analyzer.analyze_competition(similar_patents, time_window)

        return {
            "success": True,
            "competition_analysis": analysis,
            "analysis_time": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}") from e

@app.post("/comprehensive_analysis")
async def comprehensive_analysis(request: dict):
    """综合分析接口 - 整合所有高级功能"""
    query = request.get("query", "")
    search_limit = request.get("search_limit", 15)
    include_competition = request.get("include_competition", True)
    time_window = request.get("time_window", 5)

    if not query.strip():
        raise HTTPException(status_code=400, detail="分析关键词不能为空")

    if not hasattr(app.state, 'db_pool') or not app.state.db_pool:
        raise HTTPException(status_code=503, detail="数据库连接不可用")

    try:
        # 初始化分析器
        global searcher, valuation_model, competitive_analyzer
        if not searcher:
            searcher = AdvancedPatentSearcher(app.state.db_pool)
        if not valuation_model:
            valuation_model = PatentValuationModel(app.state.db_pool)
        if not competitive_analyzer:
            competitive_analyzer = CompetitiveIntelligenceAnalyzer(app.state.db_pool)

        # 1. 执行混合检索
        ft_results = await searcher.full_text_search(query, search_limit)
        vs_results = await searcher.vector_similarity_search(query, search_limit)

        # 合并并排序结果
        all_patents = ft_results + vs_results
        all_patents.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        top_patents = all_patents[:search_limit]

        # 2. 专利价值评估
        patent_evaluations = []
        for patent in top_patents[:5]:  # 只评估前5个
            evaluation = await valuation_model.evaluate_patent_value(patent, top_patents)
            patent_evaluations.append({
                "patent": {
                    "application_number": patent.get("application_number"),
                    "patent_name": patent.get("patent_name"),
                    "applicant": patent.get("applicant")
                },
                "evaluation": evaluation
            })

        # 3. 竞争格局分析
        competition_analysis = None
        if include_competition and top_patents:
            competition_analysis = await competitive_analyzer.analyze_competition(top_patents, time_window)

        # 4. 生成综合建议
        recommendations = _generate_comprehensive_recommendations(
            top_patents, patent_evaluations, competition_analysis
        )

        return {
            "success": True,
            "query": query,
            "analysis_summary": {
                "total_retrieved": len(all_patents),
                "top_patents": len(top_patents),
                "highest_similarity": top_patents[0]['similarity_score'] if top_patents else 0,
                "search_methods_used": ["full_text", "vector_similarity"]
            },
            "patent_evaluations": patent_evaluations,
            "competition_analysis": competition_analysis,
            "recommendations": recommendations,
            "analysis_time": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"综合分析失败: {str(e)}") from e

def _generate_comprehensive_recommendations(patents: list[dict], evaluations: list[dict], competition: dict) -> list[str]:
    """生成综合建议"""
    recommendations = []

    # 基于检索结果的建议
    if not patents:
        recommendations.append("未发现相关专利，技术领域相对空白，具有较好的专利申请前景")
    else:
        max_similarity = patents[0]['similarity_score'] if patents else 0

        if max_similarity > 0.8:
            recommendations.append("发现高度相似专利，建议仔细分析技术差异，寻找创新突破点")
        elif max_similarity > 0.6:
            recommendations.append("存在一定相似专利，建议重点突出技术创新点")
        else:
            recommendations.append("相关专利较少，技术新颖性较高，建议积极推进专利申请")

    # 基于价值评估的建议
    if evaluations:
        high_value_patents = [e for e in evaluations if e['evaluation']['overall_score'] > 0.75]
        if high_value_patents:
            recommendations.append(f"发现{len(high_value_patents)}项高价值专利，建议深入学习其技术方案")

    # 基于竞争分析的建议
    if competition:
        competition_level = competition.get('competition_level', '')
        if '激烈' in competition_level or '高' in competition_level:
            recommendations.append("技术领域竞争激烈，建议构建专利组合，形成技术壁垒")
        elif '中等' in competition_level:
            recommendations.append("市场竞争适中，是进入该领域的好时机")

    # 综合建议
    recommendations.append("建议结合市场需求和技术发展趋势，制定长期的专利战略")

    return recommendations

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8034)  # 内网通信，通过Gateway访问
