"""
理科科目分类器
自动识别问题属于哪个理科科目和主题
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ScienceSubject(Enum):
    """理科科目"""

    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    MATH = "math"
    GENERAL_SCIENCE = "general_science"


@dataclass
class ClassificationResult:
    """分类结果"""

    subject: ScienceSubject
    topic: str
    confidence: float
    keywords: list[str]


class ScienceClassifier:
    """理科科目分类器"""

    def __init__(self):
        # 物理关键词库
        self.physics_keywords = {
            # 力学
            "mechanics": [
                "力学",
                "牛顿",
                "运动",
                "速度",
                "加速度",
                "力",
                "质量",
                "重力",
                "摩擦力",
                "弹力",
                "动量",
                "冲量",
                "功",
                "功率",
                "动能",
                "势能",
                "能量守恒",
                "圆周运动",
                "万有引力",
                "简谐运动",
                "单摆",
                "弹簧",
            ],
            # 电磁学
            "electromagnetism": [
                "电场",
                "磁场",
                "电流",
                "电压",
                "电阻",
                "电容",
                "电感",
                "欧姆",
                "电功",
                "电功率",
                "电磁感应",
                "楞次",
                "法拉第",
                "带电粒子",
                "洛伦兹力",
                "安培力",
                "电路",
                "串联",
                "并联",
            ],
            # 光学
            "optics": [
                "光",
                "反射",
                "折射",
                "全反射",
                "干涉",
                "衍射",
                "偏振",
                "透镜",
                "凸透镜",
                "凹透镜",
                "焦距",
                "像距",
                "物距",
                "显微镜",
                "望远镜",
            ],
            # 热学
            "thermodynamics": [
                "热",
                "温度",
                "压强",
                "体积",
                "理想气体",
                "内能",
                "热力学",
                "熵",
                "焓",
                "比热容",
                "熔化",
                "汽化",
                "液化",
            ],
            # 原子物理
            "modern": [
                "原子",
                "原子核",
                "电子",
                "质子",
                "中子",
                "量子",
                "光电效应",
                "波粒二象性",
                "能级",
                "衰变",
                "核反应",
                "半衰期",
                "质能方程",
            ],
        }

        # 化学关键词库
        self.chemistry_keywords = {
            # 化学反应
            "reaction": [
                "化学方程式",
                "反应",
                "氧化",
                "还原",
                "置换",
                "分解",
                "化合",
                "复分解",
                "离子反应",
                "氧化还原",
                "配平",
            ],
            # 化学平衡
            "equilibrium": [
                "化学平衡",
                "平衡常数",
                "转化率",
                "勒夏特列",
                "可逆反应",
                "平衡移动",
                "Kc",
                "Kp",
            ],
            # 有机化学
            "organic": [
                "有机",
                "烷烃",
                "烯烃",
                "炔烃",
                "苯",
                "醇",
                "酚",
                "醛",
                "酮",
                "羧酸",
                "酯",
                "同分异构",
                "取代反应",
                "加成反应",
                "聚合反应",
            ],
            # 电化学
            "electrochemistry": [
                "原电池",
                "电解池",
                "电极",
                "阳极",
                "阴极",
                "电解",
                "电镀",
                "腐蚀",
                "电动势",
            ],
            # 化学计算
            "calculation": [
                "物质的量",
                "摩尔",
                "摩尔质量",
                "气体摩尔体积",
                "物质的量浓度",
                "溶解度",
                "p_h",
                "溶度积",
            ],
        }

        # 生物关键词库
        self.biology_keywords = {
            # 遗传
            "genetics": [
                "遗传",
                "基因",
                "显性",
                "隐性",
                "基因型",
                "表现型",
                "杂交",
                "自交",
                "测交",
                "伴性遗传",
                "孟德尔",
                "分离定律",
                "自由组合定律",
                "连锁互换",
                "DNA",
                "RNA",
                "转录",
                "翻译",
            ],
            # 生理
            "physiology": [
                "光合作用",
                "呼吸作用",
                "新陈代谢",
                "酶",
                "ATP",
                "激素",
                "神经调节",
                "体液调节",
                "免疫",
                "血液循环",
                "消化",
                "吸收",
                "排泄",
                "渗透",
                "蒸腾",
            ],
            # 生态
            "ecology": [
                "生态",
                "生态系统",
                "食物链",
                "食物网",
                "能量流动",
                "物质循环",
                "生产者",
                "消费者",
                "分解者",
                "生物圈",
                "种群",
                "群落",
                "环境保护",
            ],
            # 分子生物
            "molecular": [
                "蛋白质",
                "核酸",
                "糖类",
                "脂质",
                "细胞",
                "细胞膜",
                "细胞核",
                "细胞质",
                "染色体",
                "基因工程",
                "克隆",
                "PCR",
                "中心法则",
            ],
            # 进化
            "evolution": [
                "进化",
                "自然选择",
                "适者生存",
                "变异",
                "隔离",
                "物种起源",
                "协同进化",
                "生物多样性",
            ],
        }

        # 数学关键词库
        self.math_keywords = {
            "reasoning": ["求", "计算", "化简", "证明", "解方程", "不等式"],
            "sequence": ["数列", "递推", "通项", "等差", "等比", "归纳"],
            "proof": ["证明", "求证", "因为", "所以", "充要条件"],
        }

        logger.info("✅ 理科分类器初始化完成")

    def classify(self, text: str) -> ClassificationResult:
        """
        分类理科问题

        Args:
            text: 问题文本

        Returns:
            ClassificationResult: 分类结果
        """
        text_lower = text.lower()

        # 统计各科目的关键词匹配数
        scores = {
            ScienceSubject.PHYSICS: self._count_matches(text_lower, self.physics_keywords),
            ScienceSubject.CHEMISTRY: self._count_matches(text_lower, self.chemistry_keywords),
            ScienceSubject.BIOLOGY: self._count_matches(text_lower, self.biology_keywords),
            ScienceSubject.MATH: self._count_matches(text_lower, self.math_keywords),
        }

        # 找出得分最高的科目
        max_score = max(scores.values())

        # 如果没有匹配,返回综合理科
        if max_score == 0:
            return ClassificationResult(
                subject=ScienceSubject.GENERAL_SCIENCE,
                topic="science_reasoning",
                confidence=0.5,
                keywords=[],
            )

        # 找出得分最高的科目(可能有多个)
        top_subjects = [subj for subj, score in scores.items() if score == max_score]

        # 如果有多个科目得分相同,优先级:数学 > 物理 > 化学 > 生物
        priority_order = [
            ScienceSubject.MATH,
            ScienceSubject.PHYSICS,
            ScienceSubject.CHEMISTRY,
            ScienceSubject.BIOLOGY,
        ]

        for subject in priority_order:
            if subject in top_subjects:
                # 找出匹配的关键词
                matched_keywords = self._get_matched_keywords(
                    text_lower, self._get_keywords_dict(subject)
                )

                # 确定具体主题
                topic = self._determine_topic(subject, matched_keywords)

                # 计算置信度
                confidence = min(max_score / 5.0, 1.0)  # 假设5个关键词就非常确定了

                logger.debug(f"分类结果: {subject.value} - {topic} (置信度: {confidence:.2f})")
                logger.debug(f"匹配关键词: {matched_keywords}")

                return ClassificationResult(
                    subject=subject, topic=topic, confidence=confidence, keywords=matched_keywords
                )

        # 默认返回
        return ClassificationResult(
            subject=ScienceSubject.GENERAL_SCIENCE,
            topic="science_reasoning",
            confidence=0.5,
            keywords=[],
        )

    def _count_matches(self, text: str, keywords_dict: dict[str, list[str]]) -> int:
        """计算关键词匹配数"""
        count = 0
        for category_keywords in keywords_dict.values():
            for keyword in category_keywords:
                if keyword in text:
                    count += 1
        return count

    def _get_matched_keywords(self, text: str, keywords_dict: dict[str, list[str]]) -> list[str]:
        """获取匹配的关键词"""
        matched = []
        for category, keywords in keywords_dict.items():
            for keyword in keywords:
                if keyword in text:
                    matched.append(f"{category}:{keyword}")
        return matched

    def _get_keywords_dict(self, subject: ScienceSubject) -> dict[str, list[str]]:
        """获取科目的关键词字典"""
        if subject == ScienceSubject.PHYSICS:
            return self.physics_keywords
        elif subject == ScienceSubject.CHEMISTRY:
            return self.chemistry_keywords
        elif subject == ScienceSubject.BIOLOGY:
            return self.biology_keywords
        elif subject == ScienceSubject.MATH:
            return self.math_keywords
        else:
            return {}

    def _determine_topic(self, subject: ScienceSubject, keywords: list[str]) -> str:
        """确定具体主题"""
        if not keywords:
            return f"{subject.value}_reasoning"

        # 从关键词中提取主题(格式:category:keyword)
        categories = [kw.split(":")[0] for kw in keywords]
        most_common = max(set(categories), key=categories.count)

        return f"{subject.value}_{most_common}"


# 单例
_science_classifier: ScienceClassifier | None = None


def get_science_classifier() -> ScienceClassifier:
    """获取理科分类器单例"""
    global _science_classifier
    if _science_classifier is None:
        _science_classifier = ScienceClassifier()
    return _science_classifier


# 使用示例
if __name__ == "__main__":
    classifier = get_science_classifier()

    # 测试物理问题
    physics_problem = "一个质量为2kg的物体从高度10m自由落下,求落地时的速度。"
    result = classifier.classify(physics_problem)
    print(f"物理问题分类: {result.subject.value} - {result.topic}")
    print(f"置信度: {result.confidence:.2f}")
    print(f"匹配关键词: {result.keywords}")

    print("\n" + "=" * 60 + "\n")

    # 测试化学问题
    chemistry_problem = "配平化学方程式:KMnO4 + HCl → KCl + MnCl2 + H2O + Cl2"
    result = classifier.classify(chemistry_problem)
    print(f"化学问题分类: {result.subject.value} - {result.topic}")
    print(f"置信度: {result.confidence:.2f}")
    print(f"匹配关键词: {result.keywords}")

    print("\n" + "=" * 60 + "\n")

    # 测试生物问题
    biology_problem = "一对表现型正常的夫妇生了一个色盲儿子,问这对夫妇的基因型是什么?"
    result = classifier.classify(biology_problem)
    print(f"生物问题分类: {result.subject.value} - {result.topic}")
    print(f"置信度: {result.confidence:.2f}")
    print(f"匹配关键词: {result.keywords}")
