#!/usr/bin/env python3
from __future__ import annotations
"""
混合分词器 - jieba + BGE-M3

结合jieba的中文分词能力和BGE-M3的语义理解能力
- jieba分词用于全文搜索(PostgreSQL tsvector)
- BGE-M3 tokenizer用于向量搜索(embedding)
- 专利法律领域词典支持

作者: Athena AI Team
创建时间: 2026-01-19
版本: v1.0.0
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class HybridTokenizationResult:
    """
    混合分词结果

    包含jieba分词和BGE-M3分词两种结果
    """
    # 原始文本
    original: str

    # ========== jieba分词结果 ==========
    # jieba分词列表(用于全文搜索)
    jieba_tokens: list[str] = field(default_factory=list)
    # jieba分词后的文本(用于PostgreSQL tsvector)
    jieba_text: str = ""
    # jieba分词数量
    jieba_count: int = 0

    # ========== BGE-M3分词结果 ==========
    # BGE-M3 token列表(用于向量搜索)
    bge_tokens: list[str] = field(default_factory=list)
    # BGE-M3分词后的文本
    bge_text: str = ""
    # BGE-M3 token数量
    bge_count: int = 0

    # ========== 融合结果 ==========
    # 融合后的token列表(jieba + BGE-M3去重)
    hybrid_tokens: list[str] = field(default_factory=list)
    # 融合后的文本
    hybrid_text: str = ""
    # 总token数量
    total_count: int = 0

    # ========== 语言信息 ==========
    has_chinese: bool = False
    has_english: bool = False

    # ========== 领域术语 ==========
    # 检测到的专利法律术语
    domain_terms: list[str] = field(default_factory=list)


class HybridTokenizer:
    """
    混合分词器

    结合jieba和BGE-M3的优势:
    - jieba: 适合中文分词,用于全文搜索
    - BGE-M3: 适合语义理解,用于向量搜索
    - 专利法律词典: 专业术语识别
    """

    # 专利法律领域核心词典
    PATENT_LEGAL_TERMS = {
        # 专利基本概念
        '专利', '发明', '实用新型', '外观设计', '专利权', '专利申请',
        '专利权人', '申请人', '发明人', '代理人', '审查员',

        # 专利特性
        '新颖性', '创造性', '实用性', '现有技术', '技术水平',
        '显而易见', '突出的实质性特点', '显著的进步',

        # 专利申请流程
        '申请日', '优先权日', '公开日', '授权日', '专利号',
        '申请号', '公开号', '公告号', '国际申请', 'PCT申请',

        # 专利审查
        '初步审查', '实质审查', '复审', '无效宣告', '异议',
        '驳回', '撤回', '放弃', '终止', '失效',

        # 专利权利
        '权利要求', '独立权利要求', '从属权利要求', '说明书',
        '摘要', '附图', '保护范围', '侵权', '等同侵权',

        # 专利法律
        '专利法', '专利实施细则', '审查指南', '知识产权',
        '知识产权法', '专利代理', '专利诉讼', '专利侵权',

        # 国际专利
        '专利合作条约', 'PCT', '世界知识产权组织', 'WIPO',
        '欧洲专利局', 'EPO', '美国专利商标局', 'USPTO',
        '日本专利局', 'JPO', '韩国知识产权局', 'KIPO',

        # 专利分类
        '国际专利分类', 'IPC', '洛迦诺分类', 'CPC', 'FTERM',

        # 专利检索
        '专利检索', '查新检索', '侵权检索', '无效检索',
        '技术方案', '技术领域', '背景技术', '发明内容',

        # 专利价值
        '专利价值', '专利评估', '专利许可', '专利转让',
        '专利池', '专利联盟', '标准必要专利', 'SEP',

        # 期限费用
        '专利期限', '专利年费', '维持费', '滞纳金',
        '期限届满', '恢复权利',
    }

    # BGE-M3特殊token
    BGE_SPECIAL_TOKENS = {
        '[PAD]', '[UNK]', '[CLS]', '[SEP]'
    }
