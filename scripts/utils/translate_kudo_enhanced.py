#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译 Kudo 2013 磺酸离子液体催化剂论文为中文 Markdown 格式（增强版）
Translate Kudo 2013 Sulfonate Ionic Liquid Catalyst Paper to Chinese Markdown (Enhanced)
"""

import re
import sys
from datetime import datetime

# 输入输出路径
INPUT_FILE = "/tmp/kudo_paper.txt"
OUTPUT_FILE = "/Users/xujian/工作/04_审查意见/03_特殊程序/淄博千汇驳回复审/Kudo_2013_Sulfonate_Ionic_Liquid_Catalyst_LVS_中文翻译.md"


# 完整术语翻译表
TRANSLATION_DICT = {
    # 通用术语
    "Catalysts": "催化剂",
    "Ionic Liquids": "离子液体",
    "Ionic Liquid": "离子液体",
    "Levoglucosenone": "左旋葡聚糖酮",
    "Catalytic Pyrolysis": "催化热解",
    "pyrolysis": "热解",
    "Saccharides": "糖类",
    "saccharides": "糖类",
    "Cellulose": "纤维素",
    "cellulose": "纤维素",
    "Sulfonate": "磺酸基",
    "sulfonate": "磺酸基",
    "anion": "阴离子",
    "Anion": "阴离子",
    "cations": "阳离子",
    "cations": "阳离子",
    "Thermogravimetric Analysis": "热重分析",
    "thermogravimetric analysis": "热重分析",
    "Abstract": "摘要",
    "Introduction": "引言",
    "Results and Discussion": "结果与讨论",
    "Conclusion": "结论",
    "Conclusions": "结论",
    "References": "参考文献",
    "Keywords": "关键词",
    "Experimental": "实验部分",
    "Materials and Methods": "材料与方法",
    "Scheme": "方案",
    "Figure": "图",
    "Table": "表",
    "yield": "产率",
    "yields": "产率",
    "conversion": "转化",
    "recovery": "回收",
    "recoveries": "回收率",
    "reutilization": "再利用",
    "thermal stability": "热稳定性",
    "volatile products": "挥发性产物",
    "volatiles": "挥发性产物",
    "lignocellulosic": "木质纤维素",
    "lignocellulosic biomass": "木质纤维素生物质",
    "biomass": "生物质",
    "depolymerized": "解聚",
    "dehydrated": "脱水",
    "dehydration": "脱水",
    "hydrolysis": "水解",
    "regenerated": "再生",
    "regeneration": "再生",
    "amorphous": "无定形",
    "enzymatic hydrolysis": "酶水解",
    "fractionation": "分馏",
    "intrinsic": "内在",
    "intrinsic activity": "内在活性",
    "Brønsted acidity": "布朗斯特酸性",
    "Lewis acidic": "路易斯酸性",
    "chiral synthon": "手性合成子",
    "functionalized": "功能化",
    "recyclable": "可回收",
    "reusable": "可重复使用",
    "reuse": "重复使用",
    "homogeneous phase": "均相",
    "heterogeneous phase": "多相",
    "dissolution": "溶解",
    "solvent": "溶剂",
    "catalyst": "催化剂",
    "catalytic": "催化",
    "catalysts": "催化剂",
    "catalysis": "催化",
    "reaction": "反应",
    "reacting": "反应",
    "substances": "物质",
    "substance": "物质",
    "products": "产物",
    "product": "产物",
    "compound": "化合物",
    "compounds": "化合物",
    "synthesis": "合成",
    "synthesize": "合成",
    "applications": "应用",
    "application": "应用",
    "properties": "性质",
    "property": "性质",
    "process": "过程",
    "processes": "过程",
    "temperature": "温度",
    "pressure": "压力",
    "ambient pressure": "常压",
    "heating": "加热",
    "heating rate": "升温速率",
    "weight loss": "失重",
    "weight": "重量",
    "mass": "质量",
    "molecules": "分子",
    "molecule": "分子",
    "glucose": "葡萄糖",
    "fructose": "果糖",
    "reducing sugars": "还原糖",
    "water": "水",
    "acid": "酸",
    "acidity": "酸性",
    "base": "碱",
    "basicity": "碱性",
    "salt": "盐",
    "lignin": "木质素",
    "organic": "有机",
    "inorganic": "无机",
    "conventional": "常规",
    "conventionally": "常规地",
    "efficient": "高效",
    "efficiently": "高效地",
    "efficiency": "效率",
    "enhanced": "增强",
    "improved": "改善",
    "improve": "改善",
    "studies": "研究",
    "study": "研究",
    "research": "研究",
    "researchers": "研究人员",
    "examination": "检查",
    "examined": "检查",
    "demonstrate": "证明",
    "demonstrated": "证明",
    "reveal": "揭示",
    "revealed": "揭示",
    "indicate": "表明",
    "indicated": "表明",
    "suggest": "建议",
    "suggested": "建议",
    "propose": "提出",
    "proposed": "提出",
    "provide": "提供",
    "provided": "提供",
    "focus": "聚焦",
    "focused": "聚焦",
    "attention": "注意",
    "little attention": "很少关注",
    "significant": "显著",
    "significantly": "显著地",
    "essential": "本质",
    "essentially": "本质地",
    "excellent": "优秀",
    "excellent": "卓越地",
    "valuable": "有价值",
    "versatile": "多功能",
    "novel": "新颖",
    "attractive": "有吸引力",
    "highly": "高度",
    "widely": "广泛",
    "commonly": "通常",
    "generally": "通常",
    "typically": "典型地",
    "recently": "最近",
    "currently": "目前",
    "present": "当前",
    "present work": "本工作",
    "previous": "先前",
    "earlier": "较早",
    "further": "进一步",
    "additional": "额外",
    "various": "各种",
    "diverse": "多样",
    "different": "不同",
    "similar": "相似",
    "identical": "相同",
    "respectively": "分别",
    "separately": "分别",
    "individually": "单独",
    "together": "一起",
    "combined": "组合",
    "mixed": "混合",
    "associated": "相关",
    "correlated": "相关",
    "leading": "导致",
    "resulting": "导致",
    "resulted": "导致",
    "obtained": "获得",
    "achieved": "实现",
    "performed": "执行",
    "carried out": "进行",
    "conducted": "进行",
    "investigated": "调查",
    "evaluated": "评估",
    "analyzed": "分析",
    "measured": "测量",
    "determined": "确定",
    "calculated": "计算",
    "estimated": "估计",
    "observed": "观察",
    "found": "发现",
    "reported": "报告",
    "published": "发表",
    "reviewed": "综述",
    "discussed": "讨论",
    "considered": "考虑",
    "concluded": "总结",
    "mentioned": "提到",
    "noted": "注意",
    "shown": "显示",
    "displayed": "显示",
    "presented": "呈现",
    "described": "描述",
    "explained": "解释",
    "illustrated": "说明",
    "summarized": "总结",
    "outlined": "概述",
    "highlighted": "强调",
    "emphasized": "强调",
    "confirmed": "确认",
    "verified": "验证",
    "validated": "验证",
    "tested": "测试",
    "compared": "比较",
    "selected": "选择",
    "chosen": "选择",
    "prepared": "制备",
    "synthesized": "合成",
    "produced": "生产",
    "generated": "产生",
    "formed": "形成",
    "created": "创建",
    "developed": "开发",
    "designed": "设计",
    "optimized": "优化",
    "modified": "修改",
    "improved": "改善",
    "enhanced": "增强",
    "increased": "增加",
    "decreased": "减少",
    "reduced": "减少",
    "controlled": "控制",
    "maintained": "保持",
    "preserved": "保存",
    "stored": "储存",
    "stability": "稳定性",
    "stable": "稳定",
    "stabilized": "稳定化",
    "activity": "活性",
    "active": "活性",
    "selectivity": "选择性",
    "selective": "选择性",
    "conversion": "转化",
    "transform": "转化",
    "formation": "形成",
    "decomposition": "分解",
    "separation": "分离",
    "separated": "分离",
    "purification": "纯化",
    "purified": "纯化",
    "recovery": "回收",
    "yield": "产率",
    "performance": "性能",
    "behavior": "行为",
    "characteristics": "特性",
    "features": "特征",
    "advantages": "优势",
    "disadvantages": "劣势",
    "benefits": "益处",
    "drawbacks": "缺点",
    "limitations": "限制",
    "challenges": "挑战",
    "opportunities": "机会",
    "potential": "潜在",
    "promising": "有前景",
    "feasible": "可行",
    "practical": "实用",
    "economical": "经济",
    "effective": "有效",
    "efficient": "高效",
    "suitable": "适合",
    "appropriate": "适当",
    "proper": "正确",
    "correct": "正确",
    "accurate": "准确",
    "precise": "精确",
    "reliable": "可靠",
    "reproducible": "可重复",
    "consistent": "一致",
    "robust": "稳健",
    "flexible": "灵活",
    "versatile": "多功能",
    "scalable": "可扩展",
    "sustainable": "可持续",
    "environmentally friendly": "环境友好",
    "green": "绿色",
    "clean": "清洁",
    "renewable": "可再生",
    "alternative": "替代",
    "conventional": "传统",
    "traditional": "传统",
    "industrial": "工业",
    "commercial": "商业",
    "laboratory": "实验室",
    "pilot": "中试",
    "demonstration": "示范",
    "implementation": "实施",
    "application": "应用",
    "utilization": "利用",
    "employment": "使用",
    "usage": "用途",
    "method": "方法",
    "technique": "技术",
    "approach": "方法",
    "strategy": "策略",
    "procedure": "程序",
    "protocol": "方案",
    "workflow": "工作流程",
    "process": "过程",
    "system": "系统",
    "equipment": "设备",
    "apparatus": "装置",
    "instrument": "仪器",
    "device": "设备",
    "machine": "机器",
    "tool": "工具",
    "material": "材料",
    "chemical": "化学品",
    "reagent": "试剂",
    "solvent": "溶剂",
    "solution": "溶液",
    "mixture": "混合物",
    "compound": "化合物",
    "substance": "物质",
    "element": "元素",
    "atom": "原子",
    "molecule": "分子",
    "particle": "粒子",
    "structure": "结构",
    "morphology": "形貌",
    "surface": "表面",
    "interface": "界面",
    "bulk": "体相",
    "phase": "相",
    "state": "状态",
    "condition": "条件",
    "environment": "环境",
    "atmosphere": "气氛",
    "medium": "介质",
    "matrix": "基质",
    "support": "载体",
    "substrate": "底物",
    "precursor": "前驱体",
    "intermediate": "中间体",
    "product": "产物",
    "by-product": "副产物",
    "waste": "废物",
    "emission": "排放",
    "pollution": "污染",
    "contamination": "污染",
    "toxicity": "毒性",
    "safety": "安全",
    "hazard": "危害",
    "risk": "风险",
    "benefit": "益处",
    "advantage": "优势",
    "drawback": "缺点",
    "problem": "问题",
    "issue": "问题",
    "challenge": "挑战",
    "solution": "解决方案",
    "answer": "答案",
    "result": "结果",
    "outcome": "结果",
    "conclusion": "结论",
    "summary": "总结",
    "overview": "概述",
    "introduction": "引言",
    "background": "背景",
    "objective": "目标",
    "purpose": "目的",
    "goal": "目标",
    "aim": "目标",
    "scope": "范围",
    "focus": "焦点",
    "emphasis": "重点",
    "highlight": "重点",
    "key": "关键",
    "main": "主要",
    "major": "主要",
    "minor": "次要",
    "primary": "主要",
    "secondary": "次要",
    "important": "重要",
    "significant": "重要",
    "critical": "关键",
    "essential": "本质",
    "fundamental": "基本",
    "basic": "基本",
    "preliminary": "初步",
    "initial": "初始",
    "final": "最终",
    "ultimate": "最终",
    "overall": "整体",
    "total": "总计",
    "complete": "完整",
    "partial": "部分",
    "full": "完全",
    "empty": "空",
    "blank": "空白",
    "control": "控制",
    "experiment": "实验",
    "investigation": "调查",
    "analysis": "分析",
    "evaluation": "评估",
    "characterization": "表征",
    "measurement": "测量",
    "determination": "确定",
    "calculation": "计算",
    "estimation": "估计",
    "prediction": "预测",
    "simulation": "模拟",
    "modeling": "建模",
    "optimization": "优化",
    "improvement": "改进",
    "development": "开发",
    "design": "设计",
    "synthesis": "合成",
    "preparation": "制备",
    "production": "生产",
    "manufacturing": "制造",
    "fabrication": "制备",
    "processing": "处理",
    "treatment": "处理",
    "modification": "改性",
    "functionalization": "功能化",
    "activation": "活化",
    "stabilization": "稳定化",
    "passivation": "钝化",
    "regeneration": "再生",
    "recycling": "回收",
    "recovery": "回收",
    "separation": "分离",
    "purification": "纯化",
    "isolation": "分离",
    "extraction": "提取",
    "concentration": "浓缩",
    "dilution": "稀释",
    "drying": "干燥",
    "heating": "加热",
    "cooling": "冷却",
    "annealing": "退火",
    "calcination": "煅烧",
    "sintering": "烧结",
    "crystallization": "结晶",
    "precipitation": "沉淀",
    "filtration": "过滤",
    "centrifugation": "离心",
    "evaporation": "蒸发",
    "distillation": "蒸馏",
    "chromatography": "色谱",
    "spectroscopy": "光谱",
    "microscopy": "显微镜",
    "diffraction": "衍射",
    "scattering": "散射",
    "absorption": "吸收",
    "adsorption": "吸附",
    "desorption": "脱附",
    "reaction": "反应",
    "transformation": "转化",
    "conversion": "转化",
    "decomposition": "分解",
    "oxidation": "氧化",
    "reduction": "还原",
    "hydrogenation": "加氢",
    "dehydrogenation": "脱氢",
    "hydrolysis": "水解",
    "dehydration": "脱水",
    "condensation": "缩合",
    "polymerization": "聚合",
    "depolymerization": "解聚",
    "isomerization": "异构化",
    "rearrangement": "重排",
    "substitution": "取代",
    "addition": "加成",
    "elimination": "消除",
    "coupling": "偶联",
    "cyclization": "环化",
    "ring-opening": "开环",
    "functional group": "官能团",
    "mechanism": "机理",
    "kinetics": "动力学",
    "thermodynamics": "热力学",
    "equilibrium": "平衡",
    "rate": "速率",
    "speed": "速度",
    "velocity": "速度",
    "acceleration": "加速",
    "deceleration": "减速",
    "energy": "能量",
    "enthalpy": "焓",
    "entropy": "熵",
    "Gibbs free energy": "吉布斯自由能",
    "activation energy": "活化能",
    "heat": "热",
    "work": "功",
    "power": "功率",
    "force": "力",
    "pressure": "压力",
    "volume": "体积",
    "density": "密度",
    "concentration": "浓度",
    "molarity": "摩尔浓度",
    "molality": "质量摩尔浓度",
    "mole fraction": "摩尔分数",
    "mass fraction": "质量分数",
    "volume fraction": "体积分数",
    "percentage": "百分比",
    "ratio": "比例",
    "proportion": "比例",
    "amount": "量",
    "quantity": "数量",
    "number": "数",
    "count": "计数",
    "value": "值",
    "level": "水平",
    "degree": "度",
    "extent": "程度",
    "magnitude": "大小",
    "intensity": "强度",
    "severity": "严重性",
    "purity": "纯度",
    "quality": "质量",
    "performance": "性能",
    "efficiency": "效率",
    "selectivity": "选择性",
    "sensitivity": "灵敏度",
    "specificity": "特异性",
    "accuracy": "准确度",
    "precision": "精密度",
    "reproducibility": "重现性",
    "reliability": "可靠性",
    "stability": "稳定性",
    "durability": "耐久性",
    "lifetime": "寿命",
    "shelf life": "保质期",
    "storage life": "储存寿命",
    "operating life": "运行寿命",
    "service life": "使用寿命",
    "time": "时间",
    "duration": "持续时间",
    "period": "周期",
    "interval": "间隔",
    "frequency": "频率",
    "rate": "速率",
    "speed": "速度",
    "velocity": "速度",
    "acceleration": "加速度",
    "flow rate": "流速",
    "flux": "通量",
    "current": "电流",
    "voltage": "电压",
    "resistance": "电阻",
    "conductivity": "电导率",
    "resistivity": "电阻率",
    "capacitance": "电容",
    "inductance": "电感",
    "impedance": "阻抗",
    "charge": "电荷",
    "electric field": "电场",
    "magnetic field": "磁场",
    "electromagnetic": "电磁",
    "optical": "光学",
    "thermal": "热",
    "mechanical": "机械",
    "electrical": "电",
    "chemical": "化学",
    "physical": "物理",
    "biological": "生物",
    "environmental": "环境",
    "economical": "经济",
    "social": "社会",
    "political": "政治",
    "legal": "法律",
    "regulatory": "监管",
    "standard": "标准",
    "specification": "规格",
    "requirement": "要求",
    "criteria": "标准",
    "guideline": "指南",
    "protocol": "方案",
    "procedure": "程序",
    "method": "方法",
    "technique": "技术",
    "technology": "技术",
    "innovation": "创新",
    "invention": "发明",
    "discovery": "发现",
    "breakthrough": "突破",
    "advancement": "进步",
    "progress": "进展",
    "development": "发展",
    "improvement": "改进",
    "achievement": "成就",
    "success": "成功",
    "failure": "失败",
    "error": "错误",
    "mistake": "错误",
    "problem": "问题",
    "difficulty": "困难",
    "challenge": "挑战",
    "obstacle": "障碍",
    "barrier": "障碍",
    "limitation": "限制",
    "constraint": "约束",
    "restriction": "限制",
    "condition": "条件",
    "requirement": "要求",
    "prerequisite": "前提",
    "assumption": "假设",
    "hypothesis": "假说",
    "theory": "理论",
    "model": "模型",
    "concept": "概念",
    "idea": "想法",
    "principle": "原理",
    "law": "定律",
    "rule": "规则",
    "equation": "方程",
    "formula": "公式",
    "expression": "表达式",
    "calculation": "计算",
    "computation": "计算",
    "simulation": "模拟",
    "analysis": "分析",
    "evaluation": "评估",
    "assessment": "评估",
    "investigation": "调查",
    "examination": "检查",
    "inspection": "检查",
    "observation": "观察",
    "measurement": "测量",
    "determination": "确定",
    "quantification": "定量",
    "qualification": "定性",
    "characterization": "表征",
    "identification": "识别",
    "detection": "检测",
    "recognition": "识别",
    "classification": "分类",
    "categorization": "归类",
    "organization": "组织",
    "arrangement": "排列",
    "structure": "结构",
    "configuration": "构型",
    "composition": "组成",
    "constitution": "构成",
    "formulation": "配方",
    "preparation": "制备",
    "synthesis": "合成",
    "fabrication": "制备",
    "manufacturing": "制造",
    "processing": "处理",
    "treatment": "处理",
    "modification": "改性",
    "alteration": "改变",
    "change": "变化",
    "variation": "变化",
    "transformation": "转化",
    "conversion": "转化",
    "transition": "转变",
    "shift": "位移",
    "movement": "运动",
    "motion": "运动",
    "flow": "流动",
    "diffusion": "扩散",
    "migration": "迁移",
    "transport": "传输",
    "transfer": "传递",
    "transmission": "传输",
    "conduction": "传导",
    "convection": "对流",
    "radiation": "辐射",
    "emission": "发射",
    "absorption": "吸收",
    "reflection": "反射",
    "refraction": "折射",
    "scattering": "散射",
    "diffraction": "衍射",
    "interference": "干涉",
    "polarization": "极化",
    "magnetization": "磁化",
    "electrification": "电气化",
    "ionization": "电离",
    "excitation": "激发",
    "relaxation": "弛豫",
    "vibration": "振动",
    "rotation": "旋转",
    "translation": "平移",
    "oscillation": "振荡",
    "fluctuation": "波动",
    "variation": "变化",
    "deviation": "偏差",
    "error": "误差",
    "uncertainty": "不确定性",
    "precision": "精密度",
    "accuracy": "准确度",
    "resolution": "分辨率",
    "sensitivity": "灵敏度",
    "detection limit": "检测限",
    "quantification limit": "定量限",
    "linear range": "线性范围",
    "dynamic range": "动态范围",
    "working range": "工作范围",
    "operating range": "操作范围",
    "optimum": "最优",
    "optimal": "最优",
    "maximum": "最大",
    "minimum": "最小",
    "average": "平均",
    "mean": "平均",
    "median": "中位数",
    "mode": "众数",
    "standard deviation": "标准偏差",
    "variance": "方差",
    "range": "范围",
    "spread": "分布",
    "distribution": "分布",
    "trend": "趋势",
    "pattern": "模式",
    "relationship": "关系",
    "correlation": "相关性",
    "association": "关联",
    "dependence": "依赖",
    "independence": "独立",
    "interaction": "相互作用",
    "interplay": "相互作用",
    "interference": "干涉",
    "competition": "竞争",
    "cooperation": "合作",
    "synergy": "协同",
    "antagonism": "拮抗",
    "additivity": "加和性",
    "linearity": "线性",
    "non-linearity": "非线性",
    "saturation": "饱和",
    "inhibition": "抑制",
    "activation": "活化",
    "promotion": "促进",
    "enhancement": "增强",
    "reduction": "减少",
    "decrease": "降低",
    "increase": "增加",
    "elevation": "升高",
    "rise": "上升",
    "decline": "下降",
    "drop": "下降",
    "fall": "下降",
    "improvement": "改善",
    "deterioration": "恶化",
    "degradation": "降解",
    "decomposition": "分解",
    "stabilization": "稳定",
    "destabilization": "不稳定",
    "optimization": "优化",
    "maximization": "最大化",
    "minimization": "最小化",
    "normalization": "归一化",
    "standardization": "标准化",
    "calibration": "校准",
    "validation": "验证",
    "verification": "核实",
    "confirmation": "确认",
    "demonstration": "证明",
    "illustration": "说明",
    "explanation": "解释",
    "interpretation": "解释",
    "discussion": "讨论",
    "comment": "评论",
    "remark": "评论",
    "note": "注释",
    "observation": "观察",
    "finding": "发现",
    "result": "结果",
    "conclusion": "结论",
    "summary": "总结",
    "abstract": "摘要",
    "introduction": "引言",
    "background": "背景",
    "literature review": "文献综述",
    "methodology": "方法论",
    "experimental": "实验",
    "theoretical": "理论",
    "numerical": "数值",
    "computational": "计算",
    "simulation": "模拟",
    "modeling": "建模",
    "analysis": "分析",
    "discussion": "讨论",
    "conclusion": "结论",
    "future work": "未来工作",
    "acknowledgment": "致谢",
    "reference": "参考文献",
    "appendix": "附录",
    "supplementary material": "补充材料",
    "supporting information": "支持信息",
}


def translate_text(text, preserve_chemicals=True):
    """翻译英文文本为中文，保留化学式和数字"""
    # 保存需要保护的化学式和数字
    protected = []
    protected_counter = 0

    if preserve_chemicals:
        # 保护化学式和特定格式
        patterns = [
            (r'\[?[A-Z][a-z]?\d*(?:\([^)]+\))?\]?[+-]?', 'chemical'),
            (r'\d+\.?\d*\s*(?:°C|K|°F|bar|atm|MPa|kPa|Pa|mmHg|psi|g|kg|mg|μg|ng|pg|L|mL|μL|mol|mmol|μmol|nmol|pmol|M|mM|μM|nM|pM|%|wt%|vol%|mol%)', 'unit'),
            (r'\d+\.?\d*\s*(?:hours?|hrs?|minutes?|mins?|seconds?|secs?|days?|weeks?|months?|years?)', 'time'),
            (r'\{[^}]+\}', 'formula'),
        ]

        for pattern, ptype in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                placeholder = f"__PROTECTED_{protected_counter}__"
                protected.append((placeholder, match.group(), ptype))
                text = text[:match.start()] + placeholder + text[match.end():]
                protected_counter += 1

    # 按长度降序排序翻译字典，优先匹配长词组
    sorted_dict = sorted(TRANSLATION_DICT.items(), key=lambda x: len(x[0].split()), reverse=True)

    # 应用翻译（区分大小写）
    for eng, chi in sorted_dict:
        # 首字母大写的词
        if eng[0].isupper():
            pattern = r'\b' + eng + r'\b'
            text = re.sub(pattern, chi, text)
        # 全部小写的词
        pattern_lower = r'\b' + eng.lower() + r'\b'
        text = re.sub(pattern_lower, chi.lower() if chi else chi, text)

    # 恢复保护的内容
    for placeholder, original, ptype in protected:
        text = text.replace(placeholder, original)

    return text


def parse_paper_to_markdown(content):
    """将论文内容解析为Markdown格式"""
    lines = content.split('\n')

    md_lines = []
    md_lines.append("---")
    md_lines.append("title: 磺酸基离子液体作为稳定高效催化剂用于糖类催化热解制备左旋葡聚糖酮")
    md_lines.append("original_title: Sulfonate Ionic Liquid as a Stable and Active Catalyst for Levoglucosenone Production from Saccharides via Catalytic Pyrolysis")
    md_lines.append(f"translation_date: {datetime.now().strftime('%Y-%m-%d')}")
    md_lines.append("translator: AI Translation System")
    md_lines.append("journal: Catalysts 2013, 3(4), 757-773")
    md_lines.append("doi: 10.3390/catal3040757")
    md_lines.append("---")
    md_lines.append("")

    current_section = "header"
    skip_empty = True
    buffer = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            if buffer and current_section != "references":
                md_lines.append("")  # 保留段落间距
            continue

        # 跳过页码和页眉
        if re.match(r'^\d+$', line):
            continue
        if line in ["Catalysts 2013, 3", "758", "759", "760", "761", "762", "763", "764", "765", "766", "767", "768", "769", "770", "771", "772", "773"]:
            continue

        # 检测章节标题
        if line == "Abstract":
            if buffer:
                md_lines.extend([translate_text(l) for l in buffer])
                buffer = []
            md_lines.append("\n## 摘要\n")
            current_section = "abstract"
            continue
        elif line == "Keywords:":
            md_lines.append("\n**关键词：**")
            current_section = "keywords"
            continue
        elif line == "1. Introduction":
            if buffer:
                md_lines.extend([translate_text(l) for l in buffer])
                buffer = []
            md_lines.append("\n## 1. 引言\n")
            current_section = "introduction"
            continue
        elif re.match(r'^2\.\s+Results and Discussion', line):
            if buffer:
                md_lines.extend([translate_text(l) for l in buffer])
                buffer = []
            md_lines.append(f"\n## {translate_text(line)}\n")
            current_section = "results"
            continue
        elif re.match(r'^2\.\d+\.', line) or re.match(r'^3\.\d+\.', line):
            # 子章节
            if buffer:
                md_lines.extend([translate_text(l) for l in buffer])
                buffer = []
            md_lines.append(f"\n### {translate_text(line)}\n")
            continue
        elif line.startswith("Figure") and len(line) > 10:
            if buffer:
                md_lines.extend([translate_text(l) for l in buffer])
                buffer = []
            md_lines.append(f"\n### {line}\n")
            continue
        elif line.startswith("Table") and len(line) > 10:
            if buffer:
                md_lines.extend([translate_text(l) for l in buffer])
                buffer = []
            md_lines.append(f"\n### {line}\n")
            continue
        elif line == "References":
            if buffer:
                md_lines.extend([translate_text(l) for l in buffer])
                buffer = []
            md_lines.append("\n## 参考文献\n")
            current_section = "references"
            continue

        # 处理关键词
        if current_section == "keywords":
            keywords = [kw.strip() for kw in line.split(';')]
            translated_kw = []
            for kw in keywords:
                for eng, chi in TRANSLATION_DICT.items():
                    kw = re.sub(r'\b' + eng + r'\b', chi, kw, flags=re.IGNORECASE)
                translated_kw.append(kw)
            md_lines.append("; ".join(translated_kw))
            current_section = "body"
            continue

        # 收集正文段落
        if current_section == "header":
            # 处理标题头部信息
            if "Catalysts" in line and "2013" in line:
                continue  # 跳过期刊信息
            elif "OPEN ACCESS" in line:
                continue
            elif line == "Article":
                continue
            elif "Sulfonate Ionic Liquid" in line and "Catalyst" in line:
                md_lines.append(f"# {translate_text(line)}\n")
            elif re.match(r'^\w+\s+\w+,\s+\*\s*,', line):  # 作者行
                md_lines.append(f"\n**作者：** {line}\n")
            elif "Institute" in line or "University" in line or "Graduate School" in line:
                md_lines.append(f"{line}  \n")
            elif "Received:" in line or "Published:" in line:
                md_lines.append(f"{translate_text(line)}\n")
            else:
                buffer.append(line)
        else:
            # 正文段落
            buffer.append(line)

    # 处理剩余buffer
    if buffer:
        if current_section == "references":
            for ref in buffer:
                md_lines.append(f"{ref}\n")
        else:
            translated_paragraphs = []
            current_para = []
            for l in buffer:
                if l and not l[0].isdigit():
                    current_para.append(l)
                else:
                    if current_para:
                        translated_paragraphs.append(" ".join(current_para))
                    current_para = []
            if current_para:
                translated_paragraphs.append(" ".join(current_para))

            for para in translated_paragraphs:
                md_lines.append(translate_text(para))
                md_lines.append("")

    return "\n".join(md_lines)


def main():
    print("="*80)
    print("📄 翻译 Kudo 2013 论文为中文 Markdown")
    print("="*80)

    # 读取提取的文本
    print("\n1️⃣ 读取原始文本...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"   ✓ 读取了 {len(content.split(chr(10)))} 行文本")

    # 解析并生成Markdown
    print("\n2️⃣ 解析并翻译论文结构...")
    markdown_content = parse_paper_to_markdown(content)
    print(f"   ✓ 翻译完成，生成 {len(markdown_content.split(chr(10)))} 行 Markdown")

    # 保存文件
    print("\n3️⃣ 保存翻译文件...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"   ✓ 翻译文件已保存至：")
    print(f"   {OUTPUT_FILE}")

    print("\n" + "="*80)
    print("✅ 翻译完成！")
    print("="*80)


if __name__ == "__main__":
    main()
