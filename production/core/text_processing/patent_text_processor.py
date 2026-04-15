#!/usr/bin/env python3
"""
专利文本预处理器
Patent Text Preprocessor

专门处理专利领域的中文分词、文本清洗和特征提取
"""

from __future__ import annotations
import logging
import re
from collections import Counter
from typing import Any

import jieba
import jieba.posseg as pseg

# 配置日志
logger = logging.getLogger(__name__)


class PatentTextProcessor:
    """专利文本预处理器"""

    def __init__(self):
        """初始化文本处理器"""
        logger.info("初始化专利文本预处理器...")

        # 加载专利领域词典
        self._load_patent_dict()

        # 初始化jieba分词
        jieba.initialize()

        # 加载用户词典
        for word in self.patent_terms:
            jieba.add_word(word, freq=1000, tag="PATENT")

        # 停用词列表
        self.stop_words = self._load_stop_words()

        # 专利领域特殊符号
        self.special_chars = {
            "〔",
            "〕",
            "①",
            "②",
            "③",
            "④",
            "⑤",
            "Fig",
            "FIG",
            "fig",
            "图",
            "附图",
            "CN",
            "US",
            "EP",
            "WO",
            "JP",
            "KR",
            "A",
            "B",
            "U",
            "S",  # 专利文献类型标识
        }

        logger.info("专利文本预处理器初始化完成")

    def _load_patent_dict(self) -> dict[str, Any]:
        """加载专利领域词典"""
        # 专利常用技术术语
        self.patent_terms = {
            # 技术领域
            "深度学习",
            "机器学习",
            "人工智能",
            "神经网络",
            "卷积神经网络",
            "循环神经网络",
            "长短期记忆网络",
            "注意力机制",
            "自注意力",
            "Transformer",
            "BERT",
            "GPT",
            "自然语言处理",
            "计算机视觉",
            "图像识别",
            "语音识别",
            "语音合成",
            "区块链",
            "分布式账本",
            "智能合约",
            "共识机制",
            "物联网",
            "云计算",
            "边缘计算",
            "雾计算",
            "大数据",
            "数据挖掘",
            "知识图谱",
            "图神经网络",
            # 专利术语
            "权利要求",
            "独立权利要求",
            "从属权利要求",
            "说明书",
            "摘要",
            "发明内容",
            "具体实施方式",
            "技术方案",
            "现有技术",
            "背景技术",
            "技术领域",
            "发明目的",
            "有益效果",
            "技术效果",
            "技术问题",
            "优先权",
            "申请日",
            "公开日",
            "授权公告日",
            "新颖性",
            "创造性",
            "实用性",
            "专利性",
            "侵权",
            "等同",
            "全面覆盖原则",
            # 化学和材料
            "聚合物",
            "复合材料",
            "纳米材料",
            "石墨烯",
            "碳纳米管",
            "有机发光",
            "半导体",
            "晶体管",
            "集成电路",
            "芯片",
            "处理器",
            "存储器",
            # 机械和制造
            "传动装置",
            "传动机构",
            "执行机构",
            "控制系统",
            "数控机床",
            "3D打印",
            "增材制造",
            "减材制造",
            "机器人",
            "机械臂",
            "自动化",
            "智能制造",
            # 医疗和生物
            "基因编辑",
            "CRISPR",
            "m_rna",
            "抗体",
            "疫苗",
            "精准医疗",
            "远程医疗",
            "医疗设备",
            "诊断试剂",
            # 通信和网络
            "5G",
            "6G",
            "毫米波",
            "波束赋形",
            "大规模MIMO",
            "OFDM",
            "正交频分复用",
            "载波聚合",
            "网络切片",
            "边缘服务器",
            "内容分发网络",
            "软件定义网络",
            # 汽车和交通
            "自动驾驶",
            "智能网联汽车",
            "新能源汽车",
            "电动汽车",
            "混合动力",
            "燃料电池",
            "激光雷达",
            "毫米波雷达",
            "高级驾驶辅助系统",
        }

        # IPC/CPC分类前缀
        self.ipc_prefixes = {"A", "B", "C", "D", "E", "F", "G", "H"}

    def _load_stop_words(self) -> set[str]:
        """加载停用词"""
        # 基础停用词
        basic_stop = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "你",
            "会",
            "着",
            "没有",
            "看",
            "好",
            "自己",
            "这",
            "那",
            "里",
            "就是",
            "他",
            "时候",
            "可以",
            "下",
            "对",
            "来",
            "用",
            "以",
            "为",
            "能",
            "她",
            "它",
            "这个",
            "那个",
            "什么",
            "怎么",
            "这样",
            "那样",
            "因为",
            "所以",
            "但是",
            "如果",
            "虽然",
            "然而",
            "因此",
            "然后",
            "或者",
            "而且",
            "以及",
            "等等",
            "以下",
            "上述",
            "各种",
            "多个",
            "若干",
            "其他",
            "有关",
            "无关",
        }

        # 专利文档常见停用词
        patent_stop = {
            "本发明",
            "所述",
            "一种",
            "包括",
            "其特征在于",
            "其中",
            "该",
            "上述",
            "上述的",
            "如图",
            "如图所示",
            "参见图",
            "具体",
            "进一步",
            "优选",
            "优选地",
            "第一",
            "第二",
            "第三",
            "第四",
            "第五",
            "第六",
            "第七",
            "第八",
            "第九",
            "第十",
            "这里",
            "此处",
            "本实施例",
            "实施例",
            "本申请",
            "本申请提供",
            "本实用新型",
            "本外观设计",
            "本公开",
            "本公开提供",
        }

        return basic_stop.union(patent_stop)

    def clean_text(self, text: str) -> str:
        """
        清洗专利文本

        Args:
            text: 原始文本

        Returns:
            清洗后的文本
        """
        if not text:
            return ""

        # 统一为简体中文
        text = self._to_simplified_chinese(text)

        # 移除特殊字符和数字编号
        text = self._remove_special_patterns(text)

        # 标准化空白字符
        text = re.sub(r"\s+", " ", text)

        # 移除前后空格
        text = text.strip()

        return text

    def _to_simplified_chinese(self, text: str) -> str:
        """转换为简体中文"""
        # 这里应该使用专业的繁简转换库
        # 简化处理,实际应使用opencc等库
        return text

    def _remove_special_patterns(self, text: str) -> str:
        """移除特殊模式"""
        # 移除专利引用格式
        text = re.sub(r"CN\d+[A-Z]\d+", " ", text)
        text = re.sub(r"US\d+[A-Z]\d+", " ", text)
        text = re.sub(r"EP\d+[A-Z]\d+", " ", text)
        text = re.sub(r"WO\d+[A-Z]\d+", " ", text)

        # 移除数字序列(保留可能的专利号中的数字)
        text = re.sub(r"\b\d{4,}\b", " ", text)

        # 移除特殊字符
        for char in self.special_chars:
            text = text.replace(char, " ")

        return text

    def tokenize(self, text: str, mode: str = "accurate", keep_pos: bool = False) -> list[str]:
        """
        中文分词

        Args:
            text: 待分词文本
            mode: 分词模式 ('accurate', 'fast', 'search')
            keep_pos: 是否保留词性

        Returns:
            分词结果列表
        """
        if not text:
            return []

        # 预处理
        text = self.clean_text(text)

        if mode == "search":
            # 搜索模式:生成更多候选词
            words = self._tokenize_for_search(text)
        elif mode == "fast":
            # 快速模式:使用基础分词
            words = list(jieba.cut(text, cut_all=False))
        else:
            # 精确模式:使用词性标注
            if keep_pos:
                words_with_pos = pseg.cut(text)
                words = [f"{word}/{flag}" for word, flag in words_with_pos if word.strip()]
            else:
                words = list(jieba.cut(text, cut_all=False))

        # 过滤停用词和短词
        filtered_words = []
        for word in words:
            word = word.strip()
            if keep_pos:
                # 保留词性的格式,需要特殊处理
                word_part = word.split("/")[0]
                if (
                    len(word_part) > 1
                    and word_part not in self.stop_words
                    and not word_part.isdigit()
                ):
                    filtered_words.append(word)
            else:
                if len(word) > 1 and word not in self.stop_words and not word.isdigit():
                    filtered_words.append(word)

        return filtered_words

    def _tokenize_for_search(self, text: str) -> list[str]:
        """为搜索优化的分词"""
        # 使用全模式获取所有可能的词
        all_words = list(jieba.cut(text, cut_all=True))

        # 使用精确模式获取准确分词
        accurate_words = list(jieba.cut(text, cut_all=False))

        # 合并并去重
        words = list(set(all_words + accurate_words))

        # 过滤
        filtered_words = []
        for word in words:
            word = word.strip()
            if len(word) > 1 and word not in self.stop_words and not word.isdigit():
                filtered_words.append(word)

        return filtered_words

    def extract_keywords(
        self, text: str, top_k: int = 10, min_freq: int = 2
    ) -> list[dict[str, Any]]:
        """
        提取关键词

        Args:
            text: 输入文本
            top_k: 返回前K个关键词
            min_freq: 最小词频

        Returns:
            关键词列表,每个元素包含词和权重
        """
        words = self.tokenize(text)

        # 统计词频
        word_freq = Counter(words)

        # 计算TF-IDF权重(简化版)
        keywords = []
        total_words = len(words)

        for word, freq in word_freq.items():
            if freq >= min_freq:
                # 计算词频(TF)
                tf = freq / total_words

                # 简化的IDF计算(实际应有文档集合)
                idf = 1.0  # 简化处理

                # 综合权重
                weight = tf * idf

                keywords.append(
                    {
                        "word": word,
                        "frequency": freq,
                        "weight": weight,
                        "is_patent_term": word in self.patent_terms,
                    }
                )

        # 按权重排序
        keywords.sort(key=lambda x: x["weight"], reverse=True)

        return keywords[:top_k]

    def extract_entities(self, text: str) -> dict[str, list[str]]:
        """
        提取专利实体

        Args:
            text: 输入文本

        Returns:
            实体字典
        """
        entities = {
            "technologies": [],  # 技术术语
            "ipc_codes": [],  # IPC分类号
            "patent_numbers": [],  # 专利号
            "companies": [],  # 公司名称
            "numbers": [],  # 数值
        }

        # 提取技术术语
        words = self.tokenize(text)
        for word in words:
            if word in self.patent_terms:
                entities["technologies"].append(word)

        # 提取IPC分类号
        ipc_pattern = r"\b[ABCDEFGH]\d{2}[A-Z]\d{1,4}[A-Z]?\b"
        entities["ipc_codes"] = re.findall(ipc_pattern, text)

        # 提取专利号
        patent_patterns = [
            r"\b_cn\d{9}[A-Z]\b",
            r"\b_us\d{7,8}[A-Z]\b",
            r"\b_ep\d{8}[A-Z]\b",
            r"\b_wo\d{8}[A-Z]\b",
        ]
        for pattern in patent_patterns:
            entities["patent_numbers"].extend(re.findall(pattern, text))

        # 提取数值(包括百分比、温度、角度等)
        number_pattern = r"\b\d+(?:\.\d+)?(?:%|℃|°|mm|cm|m|km|g|kg|t|k_w|MW|GHz|MHz|k_hz|V|A)\b"
        entities["numbers"] = re.findall(number_pattern, text)

        # 去重
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def normalize_text(self, text: str) -> str:
        """
        文本标准化

        Args:
            text: 原始文本

        Returns:
            标准化后的文本
        """
        # 清洗文本
        text = self.clean_text(text)

        # 分词
        words = self.tokenize(text, mode="accurate")

        # 重新组合(可选:保留原始词序或按重要性排序)
        normalized_text = " ".join(words)

        return normalized_text

    def get_text_features(self, text: str) -> dict[str, Any]:
        """
        提取文本特征

        Args:
            text: 输入文本

        Returns:
            特征字典
        """
        features = {}

        # 基础统计
        words = self.tokenize(text)
        features["word_count"] = len(words)
        features["unique_word_count"] = len(set(words))
        features["avg_word_length"] = sum(len(w) for w in words) / len(words) if words else 0

        # 关键词
        features["keywords"] = self.extract_keywords(text, top_k=5)
        features["patent_terms_count"] = sum(1 for w in words if w in self.patent_terms)

        # 实体
        entities = self.extract_entities(text)
        features["entities"] = entities
        features["entity_count"] = sum(len(v) for v in entities.values())

        # 文本类型判断
        features["text_type"] = self._detect_text_type(text)

        return features

    def _detect_text_type(self, text: str) -> str:
        """检测文本类型"""
        # 检查是否包含权利要求特征
        if re.search(r"权利要求|其特征在于|一种.*方法|一种.*系统", text):
            if r"所述" in text and re.search(r"包括.*步骤", text):
                return "claims"
            elif re.search(r"包括.*模块|包括.*单元", text):
                return "claims_device"
            else:
                return "claims_general"

        # 检查是否为摘要
        elif re.search(r"摘要|本发明公开", text):
            return "abstract"

        # 检查是否为说明书
        elif re.search(r"技术领域|背景技术|发明内容|具体实施方式", text):
            return "description"

        # 检查是否为查询
        elif len(text) < 100 and re.search(r"检索|查找|搜索", text):
            return "query"

        else:
            return "general"

    def batch_process(self, texts: list[str], processes: int = 4) -> list[dict[str, Any]]:
        """
        批量处理文本

        Args:
            texts: 文本列表
            processes: 进程数

        Returns:
            处理结果列表
        """
        from multiprocessing import Pool

        with Pool(processes) as pool:
            results = pool.map(self.process_text, texts)

        return results

    def process_text(self, text: str) -> dict[str, Any]:
        """
        处理单个文本(用于并行处理)

        Args:
            text: 输入文本

        Returns:
            处理结果
        """
        return {
            "original": text,
            "cleaned": self.clean_text(text),
            "tokens": self.tokenize(text),
            "keywords": self.extract_keywords(text),
            "entities": self.extract_entities(text),
            "features": self.get_text_features(text),
        }


# 全局实例
_text_processor = None


def get_patent_text_processor() -> PatentTextProcessor:
    """获取专利文本处理器单例"""
    global _text_processor
    if _text_processor is None:
        _text_processor = PatentTextProcessor()
    return _text_processor
