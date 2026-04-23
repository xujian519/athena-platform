#!/usr/bin/env python3
from __future__ import annotations
"""
法律知识图谱构建器
Legal Knowledge Graph Builder

基于Neo4j和Qdrant的持久化数据构建法律知识图谱

特性：
- 导入专利法法条
- 导入典型案例
- 构建推理规则
- 建立关联关系
- 向量化存储到Qdrant
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any

import requests
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


@dataclass
class PatentLaw:
    """专利法法条"""
    article: str
    title: str
    content: str
    keywords: list[str]
    category: str
    effective_date: str
    metadata: dict[str, Any] = None


@dataclass
class CasePrecedent:
    """案例先例"""
    case_id: str
    title: str
    issue: str  # 争议焦点
    outcome: str  # 裁判结果
    reasoning: str  # 裁判理由
    cited_articles: list[str]  # 引用法条
    date: str
    metadata: dict[str, Any] = None


@dataclass
class InferenceRule:
    """推理规则"""
    rule_id: str
    name: str
    conditions: list[str]  # 条件
    conclusion: str  # 结论
    confidence: float
    category: str  # 规则类别
    metadata: dict[str, Any] = None


class LegalKnowledgeGraphBuilder:
    """法律知识图谱构建器"""

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = os.getenv("NEO4J_PASSWORD", "athena_neo4j_2024"),
        qdrant_url: str = "http://localhost:6333",
    ):
        """
        初始化知识图谱构建器

        Args:
            neo4j_uri: Neo4j连接URI
            neo4j_user: Neo4j用户名
            neo4j_password: Neo4j密码
            qdrant_url: Qdrant服务URL
        """
        # Neo4j连接
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.qdrant_url = qdrant_url
        self.collection_name = "legal_knowledge"

        logger.info("✅ 法律知识图谱构建器初始化完成")

    async def check_existing_data(self) -> dict[str, Any]:
        """
        检查Neo4j和Qdrant中的现有数据

        Returns:
            现有数据统计
        """
        logger.info("🔍 检查现有持久化数据...")

        stats = {
            "neo4j": {
                "patent_laws": 0,
                "case_precedents": 0,
                "inference_rules": 0,
                "relationships": 0,
            },
            "qdrant": {"collection_exists": False, "points_count": 0},
        }

        # 检查Neo4j数据
        with self.driver.session() as session:
            # 检查专利法法条
            result = session.run("MATCH (l:PatentLaw) RETURN count(l) as count")
            stats["neo4j"]["patent_laws"] = result.single()["count"]

            # 检查案例先例
            result = session.run("MATCH (c:CasePrecedent) RETURN count(c) as count")
            stats["neo4j"]["case_precedents"] = result.single()["count"]

            # 检查推理规则
            result = session.run("MATCH (r:InferenceRule) RETURN count(r) as count")
            stats["neo4j"]["inference_rules"] = result.single()["count"]

            # 检查关系数量
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            stats["neo4j"]["relationships"] = result.single()["count"]

        # 检查Qdrant集合
        try:
            response = requests.get(f"{self.qdrant_url}/collections/{self.collection_name}")
            if response.status_code == 200:
                data = response.json()
                stats["qdrant"]["collection_exists"] = True
                stats["qdrant"]["points_count"] = data["result"]["points_count"]
        except Exception as e:
            logger.warning(f"Qdrant集合检查失败: {e}")

        logger.info("📊 现有数据统计:")
        logger.info("  Neo4j:")
        logger.info(f"    - 专利法法条: {stats['neo4j']['patent_laws']}")
        logger.info(f"    - 案例先例: {stats['neo4j']['case_precedents']}")
        logger.info(f"    - 推理规则: {stats['neo4j']['inference_rules']}")
        logger.info(f"    - 关系数量: {stats['neo4j']['relationships']}")
        logger.info("  Qdrant:")
        logger.info(f"    - 集合存在: {stats['qdrant']['collection_exists']}")
        logger.info(f"    - 向量数量: {stats['qdrant']['points_count']}")

        return stats

    async def build_patent_law_graph(self, force_rebuild: bool = False):
        """
        构建专利法律知识图谱

        Args:
            force_rebuild: 是否强制重建（清除现有数据）
        """
        logger.info("=" * 60)
        logger.info("🏗️ 开始构建专利法律知识图谱...")
        logger.info("=" * 60)

        # 1. 检查现有数据
        existing_stats = await self.check_existing_data()

        if not force_rebuild and existing_stats["neo4j"]["patent_laws"] > 0:
            logger.info("✅ 发现已有的知识图谱数据，跳过重建")
            logger.info("   使用 --force-rebuild 参数来强制重建")
            return

        # 2. 清除现有数据（如果强制重建）
        if force_rebuild:
            logger.info("🗑️ 清除现有数据...")
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            logger.info("✅ 现有数据已清除")

        # 3. 导入专利法法条
        await self.import_patent_laws()

        # 4. 导入典型案例
        await self.import_case_precedents()

        # 5. 构建推理规则
        await self.build_inference_rules()

        # 6. 建立关联关系
        await self.establish_relationships()

        # 7. 向量化知识
        await self.vectorize_knowledge()

        # 8. 验证构建结果
        final_stats = await self.check_existing_data()

        logger.info("=" * 60)
        logger.info("✅ 专利法律知识图谱构建完成！")
        logger.info("=" * 60)
        logger.info("📊 最终统计:")
        logger.info(f"  - 专利法法条: {final_stats['neo4j']['patent_laws']}")
        logger.info(f"  - 案例先例: {final_stats['neo4j']['case_precedents']}")
        logger.info(f"  - 推理规则: {final_stats['neo4j']['inference_rules']}")
        logger.info(f"  - 关系数量: {final_stats['neo4j']['relationships']}")
        logger.info(f"  - 向量数量: {final_stats['qdrant']['points_count']}")

    async def import_patent_laws(self):
        """导入专利法法条"""
        logger.info("📖 导入专利法法条...")

        # 中国专利法核心法条（扩展版）
        patent_laws = [
            PatentLaw(
                article="A2",
                title="授予专利权的条件",
                content="发明和实用新型应当具备新颖性、创造性和实用性",
                keywords=["新颖性", "创造性", "实用性"],
                category="授予条件",
                effective_date="1985-04-01",
            ),
            PatentLaw(
                article="A22.2",
                title="新颖性",
                content="新颖性是指该发明或者实用新型不属于现有技术",
                keywords=["新颖性", "现有技术", "公开"],
                category="授予条件",
                effective_date="1985-04-01",
            ),
            PatentLaw(
                article="A22.3",
                title="创造性",
                content="创造性是指与现有技术相比，该发明具有突出的实质性特点和显著的进步",
                keywords=["创造性", "现有技术", "实质性特点", "显著进步"],
                category="授予条件",
                effective_date="1985-04-01",
            ),
            PatentLaw(
                article="A22.4",
                title="实用性",
                content="实用性是指该发明或者实用新型能够制造或者使用，并且能够产生积极效果",
                keywords=["实用性", "制造", "使用", "积极效果"],
                category="授予条件",
                effective_date="1985-04-01",
            ),
            PatentLaw(
                article="A25",
                title="不授予专利权的情形",
                content="对下列各项，不授予专利权：科学发现、智力活动的规则和方法、疾病的诊断和治疗方法",
                keywords=["不授予", "科学发现", "智力活动", "诊断治疗"],
                category="排除条款",
                effective_date="1985-04-01",
            ),
            PatentLaw(
                article="A26",
                title="申请日的确定",
                content="专利局收到专利申请文件之日为申请日",
                keywords=["申请日", "专利局", "申请文件"],
                category="申请程序",
                effective_date="1985-04-01",
            ),
            PatentLaw(
                article="A45",
                title="专利权的期限",
                content="发明专利权的期限为二十年，实用新型专利权和外观设计专利权的期限为十年",
                keywords=["专利权期限", "发明专利", "实用新型"],
                category="专利权",
                effective_date="1985-04-01",
            ),
            PatentLaw(
                article="A47",
                title="专利权的无效宣告",
                content="自专利局公告授予专利权之日起，任何单位或者个人认为该专利权的授予不符合本法有关规定的，可以请求专利复审委员会宣告该专利权无效",
                keywords=["无效宣告", "专利复审委员会", "专利权无效"],
                category="专利权",
                effective_date="1985-04-01",
            ),
            # === 审查指南：创造性判断（第二部分第四章） ===
            PatentLaw(
                article="SG_II_4_3.2",
                title="技术启示判断",
                content=(
                    "技术启示的三种来源：(1)参考文献自身给出指向其他技术的启示；"
                    "(2)本领域技术人员所掌握的公知常识和行业惯例；"
                    "(3)技术问题本身提供的技术方向指引。"
                    "技术启示否定情形：现有技术给出反向教导；存在结合障碍；"
                    "各对比文件仅分别公开单个特征且无结合启示。"
                    "判断技术启示必须围绕发明实际解决的技术问题，"
                    "技术手段的作用须与发明中一致，避免碎片化拼凑不同对比文件的特征。"
                ),
                keywords=["技术启示", "公知常识", "结合障碍", "反向教导", "结合启示"],
                category="审查指南-创造性",
                effective_date="2010-02-01",
            ),
            PatentLaw(
                article="SG_II_4_5.1",
                title="解决长期渴望但未能成功的技术难题",
                content=(
                    "审查指南第二部分第四章§5.1：发明解决了人们一直渴望解决但始终未能成功的技术难题，"
                    "作为创造性判断的辅助因素。"
                    "认定要件：该技术问题必须确实长期存在且本领域技术人员持续尝试但始终未能解决。"
                    "典型案例：农场牲畜无痛永久性标记——冷冻'烙印'方法。"
                    "注意：必须是真正'长期渴望且始终未能成功'，而非仅存在改进需求。"
                ),
                keywords=["长期技术难题", "渴望解决", "始终未能成功", "辅助判断因素"],
                category="审查指南-创造性",
                effective_date="2010-02-01",
            ),
            PatentLaw(
                article="SG_II_4_5.2",
                title="克服技术偏见",
                content=(
                    "审查指南第二部分第四章§5.2：发明克服了技术偏见，作为创造性判断的辅助因素。"
                    "认定要件（须同时满足）："
                    "(1)存在具有普遍共识的权威性认识（偏差或错误认识）；"
                    "(2)该认识偏离客观事实；"
                    "(3)该认识阻碍了本领域的研究开发。"
                    "不构成偏见的情形：仅有部分反映、同类中的个别现象不推定为普遍偏见。"
                    "举证要点：需证明偏见的存在（如教科书、技术手册中的权威记载），"
                    "以及发明如何偏离该偏见并取得成功。"
                ),
                keywords=["技术偏见", "克服偏见", "普遍共识", "权威性认识", "阻碍研发"],
                category="审查指南-创造性",
                effective_date="2010-02-01",
            ),
            PatentLaw(
                article="SG_II_4_5.3",
                title="预料不到的技术效果",
                content=(
                    "审查指南第二部分第四章§5.3：发明取得了预料不到的技术效果，"
                    "作为创造性判断的辅助因素。"
                    "技术效果产生'质'的变化（新性能）或'量'的变化（超出预期）。"
                    "判断标准：对所属领域技术人员来说，事先无法预测或推理得出。"
                    "排除情形：(1)常规变化（如浓度的线性变化）；"
                    "(2)新效果与已知效果存在关联（可从已知效果推导）。"
                    "补充实验数据限制：补充实验数据证明的技术效果必须能从原始申请文件公开内容中得到。"
                ),
                keywords=["预料不到", "技术效果", "质的变化", "量的变化", "辅助判断"],
                category="审查指南-创造性",
                effective_date="2010-02-01",
            ),
            PatentLaw(
                article="SG_II_4_6.2",
                title="避免事后诸葛亮",
                content=(
                    "审查指南第二部分第四章§6.2：审查创造性时应当避免'事后诸葛亮'。"
                    "核心原则：(1)时间基准严格以申请日（或优先权日）为界；"
                    "(2)判断主体为虚拟的、不具有创造能力的'本领域技术人员'；"
                    "(3)判断依据为申请日前的现有技术整体。"
                    "易犯错误环节：(1)确定实际解决的技术问题时带入发明内容；"
                    "(2)判断技术启示时利用知晓发明后的后见之明；"
                    "(3)认定公知常识时以当前认知替代申请日时认知。"
                    "反向论证：现有技术长期存在某个问题但无人改进，或给出相反教导时，"
                    "事后认为'容易想到'的推论不成立。"
                ),
                keywords=["事后诸葛亮", "后见之明", "本领域技术人员", "申请日"],
                category="审查指南-创造性",
                effective_date="2010-02-01",
            ),
            # === 审查指南：用途发明创造性（第二部分第十章§5.4） ===
            PatentLaw(
                article="SG_II_10_5.4",
                title="用途发明创造性",
                content=(
                    "审查指南第二部分第十章第5.4节：已知产品的新用途发明，"
                    "其创造性判断的核心在于新用途不能从产品本身的结构、组成、已知性质及现有用途"
                    "显而易见得出，而是利用了新发现的性质并产生预料不到的技术效果。"
                    "判断重点：考察新用途与已知用途之间的关联性，"
                    "以及新用途是否利用了新发现的性质而非已知性质的简单延伸。"
                ),
                keywords=["用途发明", "新用途", "新发现性质", "预料不到效果", "创造性"],
                category="审查指南-用途发明",
                effective_date="2010-02-01",
            ),
            PatentLaw(
                article="SG_II_10_5.4a",
                title="新产品用途发明创造性",
                content="新产品用途发明：用途不能从结构或组成相似的已知产品预见到。",
                keywords=["新产品", "用途发明", "结构相似", "不可预见"],
                category="审查指南-用途发明",
                effective_date="2010-02-01",
            ),
            PatentLaw(
                article="SG_II_10_5.4b",
                title="已知产品用途发明创造性",
                content=(
                    "已知产品用途发明创造性判断：新用途不能从产品本身的结构、组成、已知性质及"
                    "现有用途显而易见得出，而是利用了新发现的性质并产生预料不到的技术效果。"
                    "新旧用途共享同一机制时属于自然扩展，不具备创造性（参照第78285号复审决定）。"
                    "新旧用途在检测原理、检测设备、操作方式上完全不同时，不属于同一机制的自然扩展。"
                ),
                keywords=["已知产品", "新用途", "新发现性质", "预料不到效果", "机制不同"],
                category="审查指南-用途发明",
                effective_date="2010-02-01",
            ),
        ]

        with self.driver.session() as session:
            for law in patent_laws:
                session.run(
                    """
                    MERGE (l:PatentLaw {article: $article})
                    SET l.title = $title,
                        l.content = $content,
                        l.keywords = $keywords,
                        l.category = $category,
                        l.effective_date = $effective_date,
                        l.updated_at = datetime()
                """,
                    article=law.article,
                    title=law.title,
                    content=law.content,
                    keywords=law.keywords,
                    category=law.category,
                    effective_date=law.effective_date,
                )

        logger.info(f"✅ 已导入 {len(patent_laws)} 条专利法法条")

    async def import_case_precedents(self):
        """导入典型案例"""
        logger.info("⚖️ 导入典型案例...")

        # 典型专利案例
        cases = [
            CasePrecedent(
                case_id="CN_INVALID_001",
                title="创造性判断标准案",
                issue="如何判断专利的创造性",
                outcome="维持专利权有效",
                reasoning="与现有技术相比，该专利具有突出的实质性特点和显著进步，符合专利法第22条第3款的规定",
                cited_articles=["A22.3"],
                date="2023-05-15",
            ),
            CasePrecedent(
                case_id="CN_INVALID_002",
                title="新颖性丧失案",
                issue="公开是否导致新颖性丧失",
                outcome="宣告专利权无效",
                reasoning="申请日前已在国内外出版物上公开发表，丧失新颖性",
                cited_articles=["A22.2"],
                date="2023-06-20",
            ),
            CasePrecedent(
                case_id="CN_INFRINGE_001",
                title="专利侵权判定案",
                issue="全面覆盖原则的适用",
                outcome="认定侵权成立",
                reasoning="被控侵权产品包含专利权利要求的全部技术特征，构成侵权",
                cited_articles=["A11", "A59"],
                date="2023-07-10",
            ),
            CasePrecedent(
                case_id="CN_INVALID_003",
                title="实用性要求案",
                issue="无法实施的发明是否具有实用性",
                outcome="宣告专利权无效",
                reasoning="该发明无法在产业上制造或使用，不符合实用性要求",
                cited_articles=["A22.4"],
                date="2023-08-05",
            ),
            # === 最高人民法院判例 ===
            CasePrecedent(
                case_id="CN_SUPREME_001",
                title="(2020)最高法知行终185号——反向教导案",
                issue="现有技术明确排除区别技术特征的应用时，是否构成反向教导",
                outcome="撤销驳回，认定具备创造性",
                reasoning=(
                    "如果权利要求所要保护的技术方案与最接近的现有技术相比存在区别技术特征，"
                    "且该现有技术明确排除该区别技术特征的应用的，则本领域技术人员在面对技术问题时"
                    "缺乏动机对该现有技术进行相应技术改进以获得权利要求所要保护的技术方案，"
                    "即现有技术并未给出将上述区别特征应用到该最接近的现有技术以解决其存在的技术问题"
                    "的启示，因此该权利要求所要保护的技术方案相对于该最接近的现有技术而言具备创造性。"
                    "本案中，证据1的目的在于防止反向插入，其明确排除了双向插入的可能性，"
                    "本领域技术人员无动机将证据1改进为允许双向插入的技术方案。"
                ),
                cited_articles=["A22.3"],
                date="2020-12-28",
                metadata={
                    "court": "最高人民法院知识产权法庭",
                    "case_type": "行政上诉",
                    "key_doctrine": "反向教导",
                    "layer": "司法案例层",
                },
            ),
            CasePrecedent(
                case_id="CN_SUPREME_002",
                title="(2019)最高法行再268号——反向教导整体分析",
                issue="如何判断现有技术是否存在反向教导",
                outcome="认定不构成反向教导（提供判断方法论）",
                reasoning=(
                    "在考虑一项现有技术是否存在相反的技术教导时，应当立足于本领域技术人员的"
                    "知识水平和认知能力，从该现有技术的整体上进行分析和判断。"
                    "反向教导的认定要件：(1)现有技术公开了与区别技术特征相反的技术手段；"
                    "(2)该相反的技术手段被明确指出为缺陷或不适宜。"
                    "本案认定不构成反向教导的原因：证据3-1没有明确指出'AM/FM共享天线'本身是缺陷。"
                    "方法论意义：反向教导需'明确排除'或'明确指为缺陷'，而非仅暗示。"
                ),
                cited_articles=["A22.3"],
                date="2019-12-20",
                metadata={
                    "court": "最高人民法院",
                    "case_type": "行政再审",
                    "key_doctrine": "反向教导判断标准",
                    "layer": "司法案例层",
                },
            ),
            # === 专利复审/无效决定 ===
            CasePrecedent(
                case_id="CN_REEXAM_001",
                title="第78285号复审决定——用途发明机制相同无创造性",
                issue="副干酪乳杆菌用于防治远缘链球菌龋是否具备创造性",
                outcome="不具备创造性",
                reasoning=(
                    "对比文件1公开该菌用于防治变形链球菌引起的龋。对比文件2公开变形链球菌群"
                    "包括远缘链球菌等，其表面蛋白抗原具有高度保守性。新旧适应症的致病机理"
                    "高度关联（同一抗原，同群细菌，蛋白高度保守），技术人员有理由将同样通过"
                    "该抗原特异性结合的副干酪乳杆菌用于防治群内其他致龋菌，属于同一机制的"
                    "自然扩展，不具备创造性。"
                ),
                cited_articles=["A22.3", "SG_II_10_5.4"],
                date="2019-06-28",
                metadata={
                    "authority": "国家知识产权局专利复审委员会",
                    "case_type": "复审决定",
                    "key_doctrine": "用途发明-机制相同-无创造性",
                    "layer": "专利专业层",
                },
            ),
            CasePrecedent(
                case_id="CN_REEXAM_002",
                title="第11647号复审决定——技术术语歧义导致无法实现",
                issue="说明书中技术术语含义不清是否导致公开不充分",
                outcome="维持驳回",
                reasoning="说明书中使用的技术术语存在歧义，且从上下文无法确定其唯一含义，"
                "导致本领域技术人员无法实现该发明，不符合专利法第26条第3款的规定。",
                cited_articles=["A26"],
                date="2015-03-20",
                metadata={
                    "authority": "国家知识产权局专利复审委员会",
                    "case_type": "复审决定",
                    "key_doctrine": "技术术语歧义-公开不充分",
                    "layer": "专利专业层",
                },
            ),
            CasePrecedent(
                case_id="CN_REEXAM_003",
                title="202411856719.5复审案——异硫蓝注射液荧光示踪剂",
                issue="异硫蓝注射液作为荧光示踪剂的用途发明是否具备创造性",
                outcome="复审进行中",
                reasoning=(
                    "核心论证：(1)D2将异硫蓝荧光定性为'precludes use of'其他荧光显像剂的"
                    "干扰因素，构成反向教导而非技术启示；(2)D1第[0013]段记载'与间质蛋白微弱结合'，"
                    "教导不重视蛋白结合效应，构成第二重反向教导；"
                    "(3)本申请利用的是'与血清蛋白结合后产生荧光光谱特性'的新发现性质，"
                    "而非D2所述的笼统'产生荧光'已知性质；"
                    "(4)从'切开皮肤肉眼观察蓝染'到'体表仪器探测荧光'是检测原理的质变，"
                    "属于预料不到的技术效果。"
                    "法援：(2020)最高法知行终185号（反向教导）、(2019)最高法行再268号（整体分析）。"
                ),
                cited_articles=["A22.3", "SG_II_10_5.4", "SG_II_4_5.3", "SG_II_4_5.2", "SG_II_4_6.2"],
                date="2026-04-15",
                metadata={
                    "authority": "国家知识产权局专利复审和无效审理部",
                    "case_type": "复审请求",
                    "applicant": "山东大学齐鲁医院",
                    "inventor": "杨其峰教授",
                    "key_doctrine": "双重反向教导+用途发明新性质+预料不到效果",
                    "layer": "专利专业层",
                    "prior_art_D1": "CN106267240A",
                    "prior_art_D2": "Santa Cruz等, Ann Surg Oncol 32:3062-3064",
                },
            ),
        ]

        with self.driver.session() as session:
            for case in cases:
                session.run(
                    """
                    MERGE (c:CasePrecedent {case_id: $case_id})
                    SET c.title = $title,
                        c.issue = $issue,
                        c.outcome = $outcome,
                        c.reasoning = $reasoning,
                        c.cited_articles = $cited_articles,
                        c.date = $date,
                        c.updated_at = datetime()
                """,
                    case_id=case.case_id,
                    title=case.title,
                    issue=case.issue,
                    outcome=case.outcome,
                    reasoning=case.reasoning,
                    cited_articles=case.cited_articles,
                    date=case.date,
                )

        logger.info(f"✅ 已导入 {len(cases)} 个典型案例")

    async def build_inference_rules(self):
        """构建推理规则"""
        logger.info("🔗 构建推理规则...")

        # 推理规则
        rules = [
            InferenceRule(
                rule_id="RULE_CREATIVITY_001",
                name="创造性判断规则",
                conditions=[
                    "发明具有实质性特点",
                    "与现有技术相比有显著进步",
                    "非显而易见",
                ],
                conclusion="具备创造性",
                confidence=0.9,
                category="专利有效性",
            ),
            InferenceRule(
                rule_id="RULE_NOVELTY_001",
                name="新颖性判断规则",
                conditions=[
                    "申请日前未公开",
                    "不属于现有技术",
                    "无抵触申请",
                ],
                conclusion="具备新颖性",
                confidence=0.95,
                category="专利有效性",
            ),
            InferenceRule(
                rule_id="RULE_INVALIDITY_001",
                name="无效宣告规则",
                conditions=[
                    "不符合授予条件",
                    "违反法律规定",
                    "权利要求不清楚",
                ],
                conclusion="可宣告专利权无效",
                confidence=0.85,
                category="专利无效",
            ),
            InferenceRule(
                rule_id="RULE_INFRINGEMENT_001",
                name="侵权判定规则",
                conditions=[
                    "实施专利技术",
                    "未经专利权人许可",
                    "以生产经营为目的",
                ],
                conclusion="构成专利侵权",
                confidence=0.8,
                category="专利侵权",
            ),
            # === 创造性判断专项规则 ===
            InferenceRule(
                rule_id="RULE_CREATIVITY_002",
                name="反向教导判断规则",
                conditions=[
                    "现有技术明确排除区别技术特征的应用",
                    "本领域技术人员缺乏动机对该现有技术进行改进",
                    "现有技术将区别特征定性为缺陷或干扰因素",
                ],
                conclusion="现有技术构成反向教导，未给出技术启示，技术方案具备创造性",
                confidence=0.92,
                category="创造性判断",
                metadata={
                    "source": "(2020)最高法知行终185号、(2019)最高法行再268号",
                    "guide_ref": "审查指南第二部分第四章§3.2、§6.2",
                    "key_point": "反向教导需从现有技术整体判断，要求'明确排除'或'明确指为缺陷'",
                },
            ),
            InferenceRule(
                rule_id="RULE_CREATIVITY_003",
                name="用途发明创造性判断规则",
                conditions=[
                    "已知产品的新用途",
                    "新用途利用了新发现的性质（非已知性质的延伸）",
                    "新旧用途在技术原理或操作方式上存在根本区别",
                    "产生了预料不到的技术效果",
                ],
                conclusion="该用途发明具备创造性",
                confidence=0.90,
                category="创造性判断",
                metadata={
                    "source": "审查指南第二部分第十章§5.4",
                    "guide_ref": "审查指南第二部分第十章第5.4节",
                    "negative_ref": "第78285号复审决定（机制相同=无创造性）",
                    "key_point": "核心判断：新用途是否利用了新发现的性质，而非已知性质的简单延伸",
                },
            ),
            InferenceRule(
                rule_id="RULE_CREATIVITY_004",
                name="技术启示否定规则",
                conditions=[
                    "现有技术给出反向教导",
                    "或存在结合障碍（对比文件之间存在矛盾）",
                    "或各对比文件仅分别公开单个特征且无结合启示",
                    "或技术手段在现有技术中的作用与发明中不一致",
                ],
                conclusion="现有技术未给出技术启示，区别特征非显而易见",
                confidence=0.88,
                category="创造性判断",
                metadata={
                    "source": "审查指南第二部分第四章§3.2.1",
                    "key_point": "技术启示判断须围绕发明实际解决的技术问题，避免碎片化拼凑",
                },
            ),
            InferenceRule(
                rule_id="RULE_CREATIVITY_005",
                name="预料不到效果认定规则",
                conditions=[
                    "技术效果产生质的变化（新性能）",
                    "或技术效果产生量的变化（超出预期）",
                    "所属领域技术人员事先无法预测或推理",
                    "非常规变化且非已知效果的关联推导",
                ],
                conclusion="发明取得了预料不到的技术效果，支持创造性认定",
                confidence=0.90,
                category="创造性判断",
                metadata={
                    "source": "审查指南第二部分第四章§5.3",
                    "key_point": "质变（新性能）或量变（超预期），须事先不可预测",
                },
            ),
            InferenceRule(
                rule_id="RULE_CREATIVITY_006",
                name="事后诸葛亮排除规则",
                conditions=[
                    "审查员从发明内容反推现有技术中存在启示",
                    "或利用申请日后的知识判断申请日前的显而易见性",
                    "或以当前认知替代申请日时本领域技术人员的认知",
                ],
                conclusion="属于事后诸葛亮，该创造性否定论证不成立",
                confidence=0.92,
                category="创造性判断",
                metadata={
                    "source": "审查指南第二部分第四章§6.2",
                    "key_point": "时间基准为申请日，判断主体为虚拟的本领域技术人员",
                },
            ),
            InferenceRule(
                rule_id="RULE_USE_INVENTION_001",
                name="已知产品新用途创造性综合判断",
                conditions=[
                    "产品为已知产品（已在先公开）",
                    "新用途与已知用途的检测原理或操作方式存在根本区别",
                    "新用途利用了产品的新发现性质（非已知性质延伸）",
                    "现有技术对该新性质给出反向教导或负面定性",
                    "新用途产生了预料不到的技术效果（质变或量变）",
                ],
                conclusion="该已知产品新用途发明具备创造性",
                confidence=0.88,
                category="创造性判断",
                metadata={
                    "source": "审查指南第十章§5.4 + 第四章§5.1-5.3",
                    "typical_case": "202411856719.5异硫蓝荧光示踪剂案",
                    "key_point": "综合运用用途发明规则+反向教导+预料不到效果，多重论证",
                },
            ),
        ]

        with self.driver.session() as session:
            for rule in rules:
                session.run(
                    """
                    MERGE (r:InferenceRule {rule_id: $rule_id})
                    SET r.name = $name,
                        r.conditions = $conditions,
                        r.conclusion = $conclusion,
                        r.confidence = $confidence,
                        r.category = $category,
                        r.updated_at = datetime()
                """,
                    rule_id=rule.rule_id,
                    name=rule.name,
                    conditions=rule.conditions,
                    conclusion=rule.conclusion,
                    confidence=rule.confidence,
                    category=rule.category,
                )

        logger.info(f"✅ 已构建 {len(rules)} 条推理规则")

    async def establish_relationships(self):
        """建立关联关系"""
        logger.info("🔗 建立关联关系...")

        with self.driver.session() as session:
            # 1. 案例-法条关系
            session.run(
                """
                MATCH (c:CasePrecedent), (l:PatentLaw)
                WHERE any(article IN c.cited_articles WHERE article = l.article)
                MERGE (c)-[:REFERENCES]->(l)
                """
            )
            logger.info("  ✅ 建立案例-法条引用关系")

            # 2. 案例-推理规则关系
            session.run(
                """
                MATCH (c:CasePrecedent), (r:InferenceRule)
                WHERE any(condition IN r.conditions WHERE c.reasoning CONTAINS condition)
                MERGE (c)-[:APPLIES]->(r)
                """
            )
            logger.info("  ✅ 建立案例-规则应用关系")

            # 3. 法条-推理规则关系
            session.run(
                """
                MATCH (l:PatentLaw), (r:InferenceRule)
                WHERE any(keyword IN l.keywords WHERE any(condition IN r.conditions WHERE condition CONTAINS keyword))
                MERGE (r)-[:BASED_ON]->(l)
                """
            )
            logger.info("  ✅ 建立法条-规则基础关系")

        logger.info("✅ 关联关系建立完成")

    async def vectorize_knowledge(self):
        """向量化法律知识"""
        logger.info("🔢 向量化法律知识到Qdrant...")

        try:
            # 创建集合（如果不存在）
            collection_config = {
                "vectors": {
                    "size": 1024,  # BGE-M3向量维度（标准1024维）
                    "distance": "Cosine",
                }
            }

            response = requests.put(
                f"{self.qdrant_url}/collections/{self.collection_name}",
                json=collection_config,
            )

            if response.status_code in [200, 201]:
                logger.info(f"  ✅ Qdrant集合 '{self.collection_name}' 已创建/更新")
            else:
                logger.warning(f"  ⚠️  Qdrant集合创建返回: {response.status_code}")

            # 向量化并导入知识点
            points = []

            # 初始化embedding服务
            embedding_service = self._get_embedding_service()

            # 从Neo4j获取所有法条
            with self.driver.session() as session:
                result = session.run("MATCH (l:PatentLaw) RETURN l")
                for record in result:
                    law = dict(record["l"].items())

                    # 使用实际的embedding服务
                    text_to_embed = f"{law.get('title', '')} {law.get('content', '')}"
                    vector = self._get_embedding(text_to_embed, embedding_service)

                    points.append(
                        {
                            "id": law["article"],
                            "vector": vector,
                            "payload": {
                                "type": "patent_law",
                                "article": law["article"],
                                "title": law["title"],
                                "content": law["content"],
                            },
                        }
                    )

            # 批量导入向量
            if points:
                response = requests.put(
                    f"{self.qdrant_url}/collections/{self.collection_name}/points",
                    json={"points": points},
                )

                if response.status_code == 200:
                    logger.info(f"  ✅ 已向量化 {len(points)} 个法条知识点")
                else:
                    logger.warning(f"  ⚠️  向量导入失败: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ 向量化失败: {e}")

    def _get_embedding_service(self):
        """获取embedding服务实例"""
        try:
            from core.nlp.bge_embedding_service import BGEEmbeddingService

            return BGEEmbeddingService()
        except ImportError:
            logger.warning("⚠️ BGEEmbeddingService不可用,尝试备用方案...")
            return None

    def _get_embedding(self, text: str, embedding_service=None) -> list[float]:
        """
        获取文本的向量嵌入

        Args:
            text: 要向量化的文本
            embedding_service: embedding服务实例(可选)

        Returns:
            list[float]: 768维向量
        """
        if embedding_service is None:
            embedding_service = self._get_embedding_service()

        if embedding_service is not None:
            try:
                # 使用BGE-M3生成向量
                vector = embedding_service.embed(text)
                if vector and len(vector) == 768:
                    return vector
            except Exception as e:
                logger.warning(f"⚠️ Embedding生成失败: {e}, 使用占位向量")

        # 降级: 使用简化的占位向量
        # 寏个维度使用文本长度的哈希值来生成伪随机但一致的向量
        import hashlib

        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        # 使用哈希值生成768维向量
        base_value = sum(hash_bytes) / len(hash_bytes)
        vector = [base_value] * 768
        # 归一化
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0e-6:
            vector = [v / norm for v in vector]
        return vector

    def close(self):
        """关闭连接"""
        self.driver.close()
        logger.info("✅ Neo4j连接已关闭")


# 使用示例
if __name__ == "__main__":

    async def main():
        """主函数"""
        builder = LegalKnowledgeGraphBuilder()

        try:
            # 构建知识图谱
            await builder.build_patent_law_graph(force_rebuild=False)

        finally:
            builder.close()

    asyncio.run(main())
