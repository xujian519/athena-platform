#!/usr/bin/env python3
"""
技术发展趋势分析器
Technology Trend Analyzer
深度分析专利数据中的技术发展趋势、热点领域和未来方向
"""

import asyncio
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

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

class TrendDirection(Enum):
    """趋势方向枚举"""
    RISING = "上升"
    STABLE = "稳定"
    DECLINING = "下降"
    VOLATILE = "波动"

@dataclass
class TechnologyTrend:
    """技术趋势数据结构"""
    technology: str
    trend_direction: TrendDirection
    growth_rate: float
    confidence: float
    time_span: int
    key_indicators: dict[str, Any]
    prediction: dict[str, Any]

@dataclass
class HotspotAnalysis:
    """技术热点分析"""
    hotspot_field: str
    heat_index: float
    growth_potential: float
    market_size: str
    key_players: list[str]
    emerging_keywords: list[str]

@dataclass
class TrendForecast:
    """趋势预测"""
    time_horizon: int  # 预测时间范围（年）
    expected_development: str
    risk_factors: list[str]
    opportunities: list[str]
    confidence_level: float

class TechnologyTrendAnalyzer:
    """技术发展趋势分析器"""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.technology_keywords = self._init_technology_keywords()
        self.ipc_tech_mapping = self._init_ipc_mapping()

    def _init_technology_keywords(self) -> dict[str, list[str]:
        """初始化技术关键词词典"""
        return {
            "人工智能": [
                "人工智能", "AI", "机器学习", "深度学习", "神经网络", "卷积神经网络",
                "循环神经网络", "强化学习", "自然语言处理", "计算机视觉", "智能算法",
                "模式识别", "数据挖掘", "预测模型", "分类算法", "聚类算法"
            ],
            "物联网": [
                "物联网", "IoT", "智能设备", "传感器网络", "无线传感器", "智能家居",
                "智能城市", "工业物联网", "IIoT", "边缘计算", "M2M", "远程监控",
                "设备互联", "数据采集", "实时传输", "嵌入式系统"
            ],
            "区块链": [
                "区块链", "分布式账本", "加密货币", "智能合约", "去中心化", "共识机制",
                "加密算法", "数字货币", "比特币", "以太坊", "链上数据", "P2P网络",
                "挖矿", "节点", "哈希", " Merkle树"
            ],
            "5G通信": [
                "5G", "第五代移动通信", "毫米波", "大规模MIMO", "网络切片", "边缘计算",
                "低延迟通信", "高速传输", "移动通信", "基站", "频谱", "波束成形",
                "载波聚合", "网络覆盖", "无线接入"
            ],
            "新能源": [
                "新能源", "太阳能", "光伏", "风能", "电池", "储能", "充电桩", "电动汽车",
                "燃料电池", "清洁能源", "可再生能源", "能源管理", "智能电网",
                "光伏发电", "风力发电", "能源转换", "电池技术"
            ],
            "生物技术": [
                "生物技术", "基因工程", "基因编辑", "CRISPR", "基因测序", "蛋白质工程",
                "细胞培养", "生物制药", "疫苗", "抗体", "诊断试剂", "生物材料",
                "合成生物学", "干细胞", "基因治疗"
            ],
            "量子计算": [
                "量子计算", "量子比特", "量子纠缠", "量子门", "量子算法", "量子通信",
                "量子密码", "量子传感", "退火", "量子优势", "相干性",
                "叠加态", "量子处理器"
            ],
            "自动驾驶": [
                "自动驾驶", "无人驾驶", "智能汽车", "ADAS", "激光雷达", "毫米波雷达",
                "车载系统", "路径规划", "环境感知", "决策系统", "车联网",
                "V2X", "交通智能化", "安全驾驶"
            ],
            "机器人": [
                "机器人", "工业机器人", "服务机器人", "协作机器人", "机械臂", "自动化",
                "运动控制", "传感器融合", "人机交互", "智能机器人", "机器人控制系统",
                "机器人视觉", "机器人导航"
            ],
            "云计算": [
                "云计算", "云服务", "分布式计算", "虚拟化", "容器技术", "微服务",
                "云存储", "云安全", "边缘计算", "无服务器计算", "SaaS", "PaaS", "IaaS"
            ],
            "大数据": [
                "大数据", "数据分析", "数据仓库", "数据湖", "流处理", "批处理",
                "数据可视化", "商业智能", "数据治理", "隐私保护", "数据安全",
                "实时分析", "预测分析"
            ],
            "虚拟现实": [
                "虚拟现实", "VR", "增强现实", "AR", "混合现实", "MR", "360度视频",
                "3D显示", "头戴式设备", "触觉反馈", "沉浸式体验", "虚拟仿真"
            ]
        }

    def _init_ipc_mapping(self) -> dict[str, str]:
        """初始化IPC到技术领域的映射"""
        return {
            "G06F": "计算机技术/软件",
            "G06N": "人工智能/机器学习",
            "G06K": "数据识别/图像处理",
            "H04L": "通信网络/数据传输",
            "H04W": "无线通信/移动网络",
            "H04M": "电话通信",
            "H04N": "图像通信/视频处理",
            "G01N": "测量/测试",
            "A61B": "医疗诊断/设备",
            "A61K": "医学/制药",
            "C07D": "有机化学/医药",
            "H01M": "电池技术",
            "H02J": "电力供应/配电",
            "H02H": "紧急保护电路",
            "B60L": "电动汽车动力",
            "B60W": "车辆控制系统",
            "G05B": "控制系统/自动化",
            "G16C": "计算化学/材料科学",
            "C40B": "复合材料",
            "Y02": "可持续技术"
        }

    async def analyze_technology_trend(self, technology: str, years: int = 10) -> TechnologyTrend:
        """分析特定技术的发展趋势"""

        # 获取技术相关的专利数据
        patent_data = await self._get_technology_patents(technology, years)

        if not patent_data:
            return TechnologyTrend(
                technology=technology,
                trend_direction=TrendDirection.STABLE,
                growth_rate=0.0,
                confidence=0.0,
                time_span=years,
                key_indicators={},
                prediction={}
            )

        # 计算年度趋势
        yearly_stats = self._calculate_yearly_statistics(patent_data)

        # 分析趋势方向
        trend_direction, growth_rate, confidence = self._determine_trend_direction(yearly_stats)

        # 生成关键指标
        key_indicators = await self._calculate_key_indicators(patent_data, yearly_stats)

        # 预测未来趋势
        prediction = await self._predict_future_trend(technology, yearly_stats, key_indicators)

        return TechnologyTrend(
            technology=technology,
            trend_direction=trend_direction,
            growth_rate=growth_rate,
            confidence=confidence,
            time_span=years,
            key_indicators=key_indicators,
            prediction=prediction
        )

    async def _get_technology_patents(self, technology: str, years: int) -> list[dict]:
        """获取技术相关的专利数据"""
        async with self.db_pool.acquire() as conn:
            # 获取关键词
            keywords = self.technology_keywords.get(technology, [technology])

            # 构建查询条件
            where_conditions = []
            params = []

            for i, keyword in enumerate(keywords, 1):
                where_conditions.append(f"(patent_name ILIKE ${i} OR abstract ILIKE ${i})")
                params.append(f"%{keyword}%")

            # 添加时间条件
            cutoff_date = datetime.now() - timedelta(days=years * 365)
            where_conditions.append(f"application_date >= ${len(params) + 1}")
            params.append(cutoff_date)

            where_clause = " AND ".join(where_conditions)

            sql = f"""
                SELECT
                    application_number,
                    patent_name,
                    applicant,
                    abstract,
                    ipc_main_class,
                    application_date,
                    publication_date,
                    inventor
                FROM patents
                WHERE {where_clause}
                    AND application_number IS NOT NULL
                ORDER BY application_date DESC
            """

            results = await conn.fetch(sql, *params)

            patents = []
            for row in results:
                patents.append({
                    "application_number": row['application_number'],
                    "patent_name": row['patent_name'],
                    "applicant": row['applicant'],
                    "abstract": row['abstract'],
                    "ipc_main_class": row['ipc_main_class'],
                    "application_date": row['application_date'].isoformat() if row['application_date'] else None,
                    "publication_date": row['publication_date'].isoformat() if row['publication_date'] else None,
                    "inventor": row['inventor']
                })

            return patents

    def _calculate_yearly_statistics(self, patent_data: list[dict]) -> dict[int, dict]:
        """计算年度统计信息"""
        yearly_stats = defaultdict(lambda: {
            'count': 0,
            'applicants': set(),
            'ipc_classes': set(),
            'total_abstract_length': 0
        })

        for patent in patent_data:
            if patent.get('application_date'):
                date = datetime.fromisoformat(patent['application_date'])
                year = date.year

                yearly_stats[year]['count'] += 1
                yearly_stats[year]['applicants'].add(patent.get('applicant', ''))
                yearly_stats[year]['ipc_classes'].add(patent.get('ipc_main_class', ''))

                if patent.get('abstract'):
                    yearly_stats[year]['total_abstract_length'] += len(patent['abstract'])

        # 转换集合并计算衍生指标
        for year in yearly_stats:
            stats = yearly_stats[year]
            stats['applicant_count'] = len(stats['applicants'])
            stats['ipc_diversity'] = len(stats['ipc_classes'])
            stats['avg_abstract_length'] = stats['total_abstract_length'] / max(1, stats['count'])

            # 清理set对象以便JSON序列化
            del stats['applicants']
            del stats['ipc_classes']
            del stats['total_abstract_length']

        return dict(yearly_stats)

    def _determine_trend_direction(self, yearly_stats: dict[int, dict]) -> tuple[TrendDirection, float, float]:
        """确定趋势方向和增长率"""
        if len(yearly_stats) < 3:
            return TrendDirection.STABLE, 0.0, 0.0

        years = sorted(yearly_stats.keys())
        counts = [yearly_stats[year]['count'] for year in years]

        # 计算线性趋势
        n = len(years)
        sum_x = sum(range(n))
        sum_y = sum(counts)
        sum_xy = sum(i * counts[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))

        if n * sum_x2 - sum_x * sum_x == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        # 计算增长率（相对平均值）
        avg_count = sum_y / n
        growth_rate = slope / max(avg_count, 1) if avg_count > 0 else 0

        # 计算R²决定系数（置信度）
        y_mean = avg_count
        ss_tot = sum((count - y_mean) ** 2 for count in counts)
        ss_res = sum((counts[i] - (slope * i + (sum_y - slope * sum_x) / n)) ** 2 for i in range(n))

        confidence = 1 - (ss_res / max(ss_tot, 1)) if ss_tot > 0 else 0

        # 确定趋势方向
        if growth_rate > 0.1:
            trend_direction = TrendDirection.RISING
        elif growth_rate < -0.1:
            trend_direction = TrendDirection.DECLINING
        elif confidence < 0.3:
            trend_direction = TrendDirection.VOLATILE
        else:
            trend_direction = TrendDirection.STABLE

        return trend_direction, growth_rate, min(confidence, 1.0)

    async def _calculate_key_indicators(self, patent_data: list[dict], yearly_stats: dict[int, dict]) -> dict[str, Any]:
        """计算关键指标"""
        if not patent_data:
            return {}

        # 计算总体指标
        total_patents = len(patent_data)

        # 申请人统计
        applicant_counts = Counter(p.get('applicant', '') for p in patent_data)
        top_applicant = applicant_counts.most_common(1)[0] if applicant_counts else None

        # IPC分布
        ipc_counts = Counter(p.get('ipc_main_class', '') for p in patent_data if p.get('ipc_main_class'))

        # 技术成熟度（基于申请人多样性）
        herfindahl_index = sum((count / total_patents) ** 2 for count in applicant_counts.values())
        maturity_score = 1 - herfindahl_index  # 多样性越高，越成熟

        # 技术活跃度（基于近期专利比例）
        recent_date = datetime.now() - timedelta(days=3 * 365)
        recent_patents = len([p for p in patent_data
                            if p.get('application_date') and
                            datetime.fromisoformat(p['application_date']) > recent_date])
        activity_score = recent_patents / max(total_patents, 1)

        # 国际化程度
        international_patents = len([p for p in patent_data
                                   if p.get('applicant') and
                                   any(char in p['applicant'] for char in ['US', 'EP', 'WO', 'JP'])])
        internationalization_score = international_patents / max(total_patents, 1)

        return {
            "total_patents": total_patents,
            "top_applicant": {
                "name": top_applicant[0] if top_applicant else "",
                "patent_count": top_applicant[1] if top_applicant else 0,
                "market_share": round(top_applicant[1] / total_patents * 100, 1) if top_applicant else 0
            },
            "applicant_diversity": len(applicant_counts),
            "ipc_diversity": len(ipc_counts),
            "top_ipc_fields": [
                {"field": ipc, "count": count, "description": self.ipc_tech_mapping.get(ipc[:4], f"技术领域({ipc[:4]})")}
                for ipc, count in ipc_counts.most_common(5)
            ],
            "maturity_score": round(maturity_score, 3),
            "activity_score": round(activity_score, 3),
            "internationalization_score": round(internationalization_score, 3),
            "yearly_growth": {
                str(year): stats['count']
                for year, stats in sorted(yearly_stats.items())
            }
        }

    async def _predict_future_trend(self, technology: str, yearly_stats: dict[int, dict],
                                   key_indicators: dict) -> dict[str, Any]:
        """预测未来趋势"""
        years = sorted(yearly_stats.keys())
        if len(years) < 3:
            return {
                "prediction": "数据不足",
                "confidence": 0.0,
                "factors": []
            }

        counts = [yearly_stats[year]['count'] for year in years]

        # 简单的线性预测
        n = len(years)
        if n >= 3:
            # 使用最后3年数据进行预测
            recent_counts = counts[-3:]
            if len(recent_counts) == 3:
                # 计算二阶差分
                first_diff = [recent_counts[i+1] - recent_counts[i] for i in range(2)]
                second_diff = first_diff[1] - first_diff[0]

                # 预测未来2年
                next_year_count = recent_counts[-1] + first_diff[-1] + second_diff / 2
                year_after_next_count = next_year_count + first_diff[-1] + second_diff

                # 预测描述
                if second_diff > 0:
                    trend_desc = "加速增长"
                elif second_diff < -1:
                    trend_desc = "增长放缓"
                else:
                    trend_desc = "稳定增长"

                return {
                    "short_term_prediction": f"预计未来1-2年将{trend_desc}",
                    "next_year_estimate": max(0, int(next_year_count)),
                    "year_after_next_estimate": max(0, int(year_after_next_count)),
                    "growth_acceleration": round(second_diff, 2),
                    "confidence": 0.7 if abs(second_diff) > 5 else 0.5,
                    "key_factors": [
                        f"当前活跃度: {key_indicators.get('activity_score', 0):.2f}",
                        f"技术成熟度: {key_indicators.get('maturity_score', 0):.2f}",
                        f"申请人多样性: {key_indicators.get('applicant_diversity', 0)}"
                    ]
                }

        return {
            "prediction": "趋势稳定",
            "confidence": 0.5,
            "factors": ["历史数据有限，预测精度较低"]
        }

    async def identify_technology_hotspots(self, years: int = 5) -> list[HotspotAnalysis]:
        """识别技术热点"""
        hotspots = []

        # 获取最近几年的专利数据
        async with self.db_pool.acquire() as conn:
            cutoff_date = datetime.now() - timedelta(days=years * 365)

            # 分析各技术领域的专利数量
            tech_field_stats = defaultdict(int)
            tech_field_patents = defaultdict(list)

            for tech_name, keywords in self.technology_keywords.items():
                for keyword in keywords[:5]:  # 限制查询关键词数量
                    sql = """
                        SELECT application_number, patent_name, applicant, ipc_main_class, application_date
                        FROM patents
                        WHERE (patent_name ILIKE $1 OR abstract ILIKE $1)
                            AND application_date >= $2
                            AND application_number IS NOT NULL
                        LIMIT 500
                    """
                    results = await conn.fetch(sql, f"%{keyword}%", cutoff_date)

                    for row in results:
                        tech_field_stats[tech_name] += 1
                        tech_field_patents[tech_name].append({
                            "application_number": row['application_number'],
                            "patent_name": row['patent_name'],
                            "applicant": row['applicant'],
                            "ipc_main_class": row['ipc_main_class'],
                            "application_date": row['application_date'].isoformat() if row['application_date'] else None
                        })

            # 为每个技术领域计算热度指数
            for tech_name, patent_count in tech_field_stats.items():
                if patent_count < 10:  # 过滤专利数量过少的领域
                    continue

                patents = tech_field_patents[tech_name]

                # 计算热度指标
                heat_index = await self._calculate_heat_index(patents, years)
                growth_potential = await self._calculate_growth_potential(patents)
                market_size = self._estimate_market_size(tech_name, patent_count)

                # 获取主要参与者
                key_players = list(Counter(p['applicant'] for p in patents).most_common(5))

                # 提取新兴关键词
                emerging_keywords = self._extract_emerging_keywords(patents)

                hotspot = HotspotAnalysis(
                    hotspot_field=tech_name,
                    heat_index=heat_index,
                    growth_potential=growth_potential,
                    market_size=market_size,
                    key_players=key_players,
                    emerging_keywords=emerging_keywords
                )

                hotspots.append(hotspot)

        # 按热度指数排序
        hotspots.sort(key=lambda x: x.heat_index, reverse=True)
        return hotspots[:10]  # 返回前10个热点

    async def _calculate_heat_index(self, patents: list[dict], years: int) -> float:
        """计算技术热度指数"""
        if not patents:
            return 0.0

        # 基础分数：专利数量
        base_score = min(len(patents) / 100.0, 1.0)  # 标准化到0-1

        # 增长分数：近期专利比例
        recent_date = datetime.now() - timedelta(days=2 * 365)
        recent_count = len([p for p in patents
                           if p.get('application_date') and
                           datetime.fromisoformat(p['application_date']) > recent_date])
        growth_score = recent_count / max(len(patents), 1)

        # 多样性分数：申请人多样性
        applicant_diversity = len({p.get('applicant', '') for p in patents})
        diversity_score = min(applicant_diversity / 50.0, 1.0)

        # 综合热度指数
        heat_index = (base_score * 0.4 + growth_score * 0.4 + diversity_score * 0.2)
        return round(heat_index, 3)

    async def _calculate_growth_potential(self, patents: list[dict]) -> float:
        """计算增长潜力"""
        if len(patents) < 5:
            return 0.5  # 默认中等潜力

        # 按年份统计
        yearly_counts = defaultdict(int)
        for patent in patents:
            if patent.get('application_date'):
                year = datetime.fromisoformat(patent['application_date']).year
                yearly_counts[year] += 1

        if len(yearly_counts) < 2:
            return 0.5

        years = sorted(yearly_counts.keys())
        counts = [yearly_counts[year] for year in years]

        # 计算增长率
        if len(counts) >= 2:
            recent_growth = (counts[-1] - counts[0]) / max(counts[0], 1)
            growth_potential = min(max(recent_growth, 0), 1.0)
            return round(growth_potential, 3)

        return 0.5

    def _estimate_market_size(self, tech_name: str, patent_count: int) -> str:
        """估算市场规模"""
        if patent_count > 1000:
            return "大型市场"
        elif patent_count > 500:
            return "中大型市场"
        elif patent_count > 100:
            return "中型市场"
        elif patent_count > 50:
            return "中小型市场"
        else:
            return "新兴市场"

    def _extract_emerging_keywords(self, patents: list[dict]) -> list[str]:
        """提取新兴关键词"""
        # 简单的关键词提取（实际应用中可使用更复杂的NLP方法）
        all_text = []
        for patent in patents[:20]:  # 分析前20个专利
            if patent.get('patent_name'):
                all_text.append(patent['patent_name'])
            if patent.get('abstract'):
                all_text.append(patent['abstract'][:200])  # 取前200字符

        combined_text = ' '.join(all_text).lower()

        # 常见技术词汇过滤
        common_words = {'方法', '系统', '装置', '基于', '一种', '实现', '包括', '用于', '通过', '可以'}

        # 简单的关键词频率统计
        word_freq = Counter()
        for word in re.findall(r'[\u4e00-\u9fff]+|[a-z_a-Z]+', combined_text):
            if len(word) >= 2 and word not in common_words:
                word_freq[word] += 1

        # 返回最常见的新兴关键词
        emerging_keywords = [word for word, count in word_freq.most_common(10)
                           if count >= 3 and len(word) >= 2]

        return emerging_keywords

    async def generate_trend_report(self, technology: str = None, years: int = 5) -> dict[str, Any]:
        """生成技术趋势报告"""
        if technology:
            # 分析特定技术
            trend = await self.analyze_technology_trend(technology, years)

            return {
                "report_type": "单技术趋势分析",
                "technology": technology,
                "analysis_period": f"最近{years}年",
                "trend_analysis": {
                    "direction": trend.trend_direction.value,
                    "growth_rate": trend.growth_rate,
                    "confidence": trend.confidence
                },
                "key_indicators": trend.key_indicators,
                "future_prediction": trend.prediction,
                "recommendations": self._generate_recommendations(trend),
                "generated_at": datetime.now().isoformat()
            }
        else:
            # 识别技术热点
            hotspots = await self.identify_technology_hotspots(years)

            return {
                "report_type": "技术热点分析",
                "analysis_period": f"最近{years}年",
                "hotspot_count": len(hotspots),
                "top_hotspots": [
                    {
                        "technology": h.hotspot_field,
                        "heat_index": h.heat_index,
                        "growth_potential": h.growth_potential,
                        "market_size": h.market_size,
                        "key_players": [p[0] for p in h.key_players[:3],
                        "emerging_keywords": h.emerging_keywords[:5]
                    }
                    for h in hotspots[:5]
                ],
                "market_overview": {
                    "total_technologies": len(hotspots),
                    "high_heat_techs": len([h for h in hotspots if h.heat_index > 0.7]),
                    "high_growth_techs": len([h for h in hotspots if h.growth_potential > 0.7])
                },
                "strategic_insights": self._generate_strategic_insights(hotspots),
                "generated_at": datetime.now().isoformat()
            }

    def _generate_recommendations(self, trend: TechnologyTrend) -> list[str]:
        """生成建议"""
        recommendations = []

        if trend.trend_direction == TrendDirection.RISING:
            recommendations.append("技术呈上升趋势，建议加大研发投入")
            recommendations.append(f"增长率{trend.growth_rate:.1%}，市场前景良好")
        elif trend.trend_direction == TrendDirection.DECLINING:
            recommendations.append("技术呈下降趋势，建议谨慎投资")
            recommendations.append("考虑技术转型或寻找新的应用领域")
        elif trend.trend_direction == TrendDirection.VOLATILE:
            recommendations.append("技术发展波动较大，建议深入分析市场驱动因素")
        else:
            recommendations.append("技术发展相对稳定，适合长期布局")

        # 基于关键指标的建议
        if trend.key_indicators.get('maturity_score', 0) > 0.7:
            recommendations.append("技术较为成熟，建议关注应用创新")
        elif trend.key_indicators.get('maturity_score', 0) < 0.3:
            recommendations.append("技术处于早期阶段，存在较大创新空间")

        if trend.key_indicators.get('internationalization_score', 0) > 0.3:
            recommendations.append("国际化程度较高，建议关注全球市场动态")

        return recommendations

    def _generate_strategic_insights(self, hotspots: list[HotspotAnalysis]) -> list[str]:
        """生成战略洞察"""
        insights = []

        if not hotspots:
            return ["暂无足够数据进行战略分析"]

        # 市场集中度分析
        top_technology = hotspots[0]
        if top_technology.heat_index > 0.8:
            insights.append(f"{top_technology.hotspot_field}是最热门的技术领域，竞争激烈")

        # 增长潜力分析
        high_growth_techs = [h for h in hotspots if h.growth_potential > 0.7]
        if high_growth_techs:
            insights.append(f"发现{len(high_growth_techs)}个高增长潜力技术领域值得关注")

        # 市场规模分析
        large_markets = [h for h in hotspots if h.market_size in ["大型市场", "中大型市场"]
        if large_markets:
            insights.append(f"大型市场技术领域：{', '.join([h.hotspot_field for h in large_markets[:3])}")

        # 技术融合机会
        ipc_overlaps = self._find_technology_overlaps(hotspots)
        if ipc_overlaps:
            insights.append("发现技术融合机会，建议关注交叉领域创新")

        return insights

    def _find_technology_overlaps(self, hotspots: list[HotspotAnalysis]) -> list[str]:
        """发现技术重叠领域"""
        # 简化的重叠检测
        overlaps = []
        if len(hotspots) >= 2:
            overlaps.append("人工智能与物联网的融合应用")
        if len(hotspots) >= 3:
            overlaps.append("大数据驱动的智能制造")
        return overlaps

# FastAPI应用部分
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await display_startup_identity()
    # 初始化数据库连接池
    try:
        app.state.db_db = await get_postgres_pool(**PATENT_DB_CONFIG)
        print("✅ PostgreSQL专利数据库连接成功!")
    except Exception as e:
        print(f"⚠️ 数据库连接失败: {str(e)}")
        app.state.db_pool = None
    yield
    # 关闭时执行
    if hasattr(app.state, 'db_pool') and app.state.db_pool:
        await app.state.db_pool.close()
        print("🛑 数据库连接已关闭")

app = FastAPI(
    title="技术发展趋势分析器",
    description="深度分析专利数据中的技术发展趋势、热点领域和未来方向",
    lifespan=lifespan
)

# 创建分析专家身份
trend_analyzer_identity = AgentIdentity(
    name="技术趋势分析师",
    type=AgentType.PATENT,
    version="Trend Analysis 1.0",
    slogan="洞察技术趋势，预测未来方向",
    specialization="技术发展趋势分析与预测",
    capabilities={
        "趋势分析": "深度分析特定技术的发展趋势",
        "热点识别": "识别当前技术热点和新兴领域",
        "市场预测": "预测技术市场发展前景",
        "战略建议": "提供技术投资和研发战略建议"
    },
    personality="前瞻、深入、客观、专业",
    work_mode="数据驱动 + 算法分析 + 战略洞察",
    created_at=datetime.now()
)

# 注册身份
register_agent_identity("trend_analyzer", trend_analyzer_identity)

async def display_startup_identity():
    """启动时展示身份"""
    try:
        await asyncio.sleep(0.5)

        identity_display = await format_identity_display("trend_analyzer", "startup")

        print("\n" + "="*70)
        print(identity_display)
        print("\n📈 技术趋势分析师启动成功！")
        print("📍 服务端口: 8035")
        print("🗄️ 数据源: PostgreSQL专利数据库")
        print("🔍 分析能力: 趋势分析 + 热点识别 + 战略预测")
        print("="*70 + "\n")

    except Exception as e:
        print(f"⚠️ 身份展示失败: {str(e)}")

# 全局分析器实例
trend_analyzer = None

@app.get("/")
async def root():
    return {
        "message": "技术发展趋势分析器",
        "version": "Trend Analysis 1.0",
        "status": "active",
        "capabilities": [
            "单技术趋势分析",
            "技术热点识别",
            "市场预测",
            "战略建议生成"
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    if not hasattr(app.state, 'db_pool') or not app.state.db_pool:
        return {
            "status": "unhealthy",
            "message": "数据库连接不可用",
            "service": "trend_analyzer"
        }

    try:
        async with app.state.db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "service": "trend_analyzer",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "message": str(e),
            "service": "trend_analyzer"
        }

@app.post("/analyze_technology_trend")
async def analyze_technology_trend(request: dict):
    """分析特定技术的发展趋势"""
    technology = request.get("technology", "")
    years = request.get("years", 10)

    if not technology:
        raise HTTPException(status_code=400, detail="技术名称不能为空")

    if not hasattr(app.state, 'db_pool') or not app.state.db_pool:
        raise HTTPException(status_code=503, detail="数据库连接不可用")

    global trend_analyzer
    if not trend_analyzer:
        trend_analyzer = TechnologyTrendAnalyzer(app.state.db_pool)

    try:
        # 检查是否为已知技术领域
        known_technologies = list(trend_analyzer.technology_keywords.keys())
        if technology not in known_technologies:
            # 尝试找到最相似的技术领域
            best_match = None
            max_match = 0
            for tech in known_technologies:
                if tech in technology or technology in tech:
                    best_match = tech
                    max_match = len(tech)

            if best_match and max_match >= 2:
                technology = best_match
            else:
                raise HTTPException(status_code=400, detail=f"未知技术领域。已知领域: {', '.join(known_technologies)}")

        # 执行趋势分析
        trend = await trend_analyzer.analyze_technology_trend(technology, years)

        return {
            "success": True,
            "technology": technology,
            "trend_analysis": {
                "direction": trend.trend_direction.value,
                "growth_rate": round(trend.growth_rate * 100, 2),  # 转换为百分比
                "confidence": round(trend.confidence * 100, 2),  # 转换为百分比
                "time_span_years": trend.time_span
            },
            "key_indicators": trend.key_indicators,
            "future_prediction": trend.prediction,
            "recommendations": trend_analyzer._generate_recommendations(trend),
            "analysis_time": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"趋势分析失败: {str(e)}") from e

@app.post("/identify_hotspots")
async def identify_hotspots(request: dict):
    """识别技术热点"""
    years = request.get("years", 5)
    limit = request.get("limit", 10)

    if not hasattr(app.state, 'db_pool') or not app.state.db_pool:
        raise HTTPException(status_code=503, detail="数据库连接不可用")

    global trend_analyzer
    if not trend_analyzer:
        trend_analyzer = TechnologyTrendAnalyzer(app.state.db_pool)

    try:
        hotspots = await trend_analyzer.identify_technology_hotspots(years)
        hotspots = hotspots[:limit]

        # 格式化热点数据
        formatted_hotspots = []
        for hotspot in hotspots:
            formatted_hotspots.append({
                "technology": hotspot.hotspot_field,
                "heat_index": round(hotspot.heat_index * 100, 1),
                "growth_potential": round(hotspot.growth_potential * 100, 1),
                "market_size": hotspot.market_size,
                "key_players": [player[0] for player in hotspot.key_players[:3],
                "emerging_keywords": hotspot.emerging_keywords[:5]
            })

        return {
            "success": True,
            "analysis_period": f"最近{years}年",
            "hotspot_count": len(formatted_hotspots),
            "hotspots": formatted_hotspots,
            "market_overview": {
                "high_heat_technologies": len([h for h in hotspots if h.heat_index > 0.7]),
                "high_growth_technologies": len([h for h in hotspots if h.growth_potential > 0.7]),
                "large_market_technologies": len([h for h in hotspots if h.market_size in ["大型市场", "中大型市场"])
            },
            "analysis_time": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"热点识别失败: {str(e)}") from e

@app.post("/generate_trend_report")
async def generate_trend_report(request: dict):
    """生成技术趋势报告"""
    technology = request.get("technology", None)  # None表示分析所有热点
    years = request.get("years", 5)

    if not hasattr(app.state, 'db_pool') or not app.state.db_pool:
        raise HTTPException(status_code=503, detail="数据库连接不可用")

    global trend_analyzer
    if not trend_analyzer:
        trend_analyzer = TechnologyTrendAnalyzer(app.state.db_pool)

    try:
        report = await trend_analyzer.generate_trend_report(technology, years)
        return {
            "success": True,
            "report": report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}") from e

@app.get("/available_technologies")
async def get_available_technologies():
    """获取可分析的技术领域列表"""
    global trend_analyzer
    if not trend_analyzer:
        return {"available_technologies": []}

    return {
        "available_technologies": list(trend_analyzer.technology_keywords.keys()),
        "total_count": len(trend_analyzer.technology_keywords)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8035)  # 内网通信，通过Gateway访问
