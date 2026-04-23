#!/usr/bin/env python3

"""
小娜专利命名系统 - 规则加载器
Xiaona Patent Naming System - Rule Loader

作者: 小娜·天秤女神
创建时间: 2025-12-17
重构时间: 2026-01-27
版本: v2.0.0

负责加载和管理专利命名规则、技术词汇库、命名模板和成功案例。
"""

from typing import Any


class RuleLoader:
    """规则加载器 - 负责加载和管理命名规则数据"""

    @staticmethod
    def load_naming_rules() -> dict[str, Any]:
        """加载专利命名规则"""
        return {
            "invention_patent": {
                "name_length": {"min": 5, "max": 25},
                "structure": "[技术领域] + [核心创新] + [技术手段]",
                "forbidden_words": ["新的", "改进的", "优化的"],
                "required_elements": ["技术创新", "技术特征"],
                "keywords": ["装置", "系统", "方法", "工艺", "设备"],
            },
            "utility_model": {
                "name_length": {"min": 8, "max": 30},
                "structure": "[产品/装置] + [结构/功能特征] + [创新点]",
                "forbidden_words": ["新型", "特殊", "高级"],
                "required_elements": ["形状", "构造", "功能"],
                "keywords": ["装置", "设备", "工具", "机构", "结构"],
            },
            "design_patent": {
                "name_length": {"min": 3, "max": 20},
                "structure": "[产品] + [设计特点]",
                "forbidden_words": ["美观", "实用", "创新"],
                "required_elements": ["外观", "形状"],
                "keywords": ["外观", "造型", "设计", "图案"],
            },
        }

    @staticmethod
    def load_technical_vocabulary() -> dict[str, list[str]]:
        """加载技术词汇库"""
        return {
            "chemical_engineering": [
                "反应器",
                "催化剂",
                "工艺",
                "装置",
                "系统",
                "方法",
                "合成",
                "制备",
                "分离",
                "纯化",
                "回收",
                "利用",
            ],
            "mechanical_engineering": [
                "设备",
                "装置",
                "机构",
                "结构",
                "组件",
                "系统",
                "驱动",
                "传动",
                "控制",
                "检测",
                "调节",
                "保护",
            ],
            "electronic_engineering": [
                "电路",
                "系统",
                "装置",
                "模块",
                "接口",
                "协议",
                "信号",
                "处理",
                "传输",
                "存储",
                "显示",
                "控制",
            ],
            "biotechnology": [
                "菌株",
                "酶",
                "基因",
                "蛋白",
                "细胞",
                "培养",
                "提取",
                "纯化",
                "检测",
                "鉴定",
                "应用",
                "方法",
            ],
            "materials": [
                "材料",
                "复合材料",
                "纳米材料",
                "合金",
                "涂层",
                "薄膜",
                "纤维",
                "颗粒",
                "制备",
                "应用",
                "改性",
            ],
        }

    @staticmethod
    def load_naming_templates() -> dict[str, list[str]]:
        """加载命名模板库"""
        return {
            "invention_patent": [
                "一种{技术领域}的{核心创新}{技术手段}",
                "基于{技术原理}的{核心创新}{技术手段}",
                "{技术领域}{核心创新}的{技术手段}及{应用方法}",
                "一种用于{应用场景}的{核心创新}{技术手段}",
                "集成了{关键技术}的{核心创新}{技术手段}",
            ],
            "utility_model": [
                "一种{产品}的{结构特征}{功能特征}",
                "具有{功能特点}的{产品}{结构特征}",
                "{产品}的{创新点}{结构特征}及{功能特征}",
                "一种{产品}的{结构特征}{结构部件}",
                "改进的{产品}{结构特征}及{功能特征}",
            ],
            "design_patent": [
                "{产品}{设计特点}",
                "具有{外观特征}的{产品}",
                "{产品}的{造型设计}",
                "一种{产品}的{图案}{色彩}设计",
                "{产品}的{整体}{外观设计}",
            ],
        }

    @staticmethod
    def load_success_cases() -> list[dict[str, Any]]:
        """加载成功案例库"""
        return [
            {
                "name": "一种基于深度学习的智能图像识别系统及方法",
                "patent_type": "invention",
                "technical_field": "人工智能",
                "innovation_points": ["深度学习", "智能识别", "系统架构"],
                "success_score": 0.95,
            },
            {
                "name": "一种高效节能的LED驱动电路结构",
                "patent_type": "utility_model",
                "technical_field": "电子工程",
                "innovation_points": ["节能", "驱动电路", "结构优化"],
                "success_score": 0.88,
            },
            {
                "name": "智能手机的曲面屏外观设计",
                "patent_type": "design",
                "technical_field": "产品设计",
                "innovation_points": ["曲面屏", "外观设计", "造型创新"],
                "success_score": 0.92,
            },
        ]

