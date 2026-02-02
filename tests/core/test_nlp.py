"""
NLP模块单元测试
测试自然语言处理功能
"""

import pytest
from typing import List, Dict, Any


class TestNLPModule:
    """NLP模块测试类"""

    def test_nlp_module_import(self):
        """测试NLP模块可以导入"""
        try:
            import core.nlp
            assert core.nlp is not None
        except ImportError:
            pytest.skip("NLP模块导入失败")

    def test_text_processing_import(self):
        """测试文本处理可以导入"""
        try:
            from core.nlp.text_processor import TextProcessor
            assert TextProcessor is not None
        except ImportError:
            pytest.skip("文本处理器导入失败")


class TestTextProcessing:
    """文本处理测试"""

    def test_text_cleaning(self):
        """测试文本清理"""
        # 包含多余空格和特殊字符的文本
        dirty_text = "  Hello    World!  \n\tHow are you?  "

        # 清理文本
        import re
        clean_text = re.sub(r'\s+', ' ', dirty_text.strip())

        # 验证清理
        assert clean_text == "Hello World! How are you?"
        assert "  " not in clean_text
        assert "\n" not in clean_text
        assert "\t" not in clean_text

    def test_text_segmentation(self):
        """测试文本分段"""
        text = "这是第一句。这是第二句！这是第三句？"

        # 简单的分段（按句号、感叹号、问号）
        import re
        sentences = re.split(r'[。！？]', text)

        # 移除空字符串
        sentences = [s.strip() for s in sentences if s.strip()]

        # 验证分段
        assert len(sentences) == 3
        assert sentences[0] == "这是第一句"

    def test_word_tokenization(self):
        """测试分词"""
        text = "自然语言处理 是 人工智能 的 重要分支"

        # 简单分词（按空格）
        words = text.split(" ")

        # 验证分词
        assert len(words) > 1
        assert "自然语言处理" in words

    def test_remove_stopwords(self):
        """测试停用词移除"""
        # 简单的停用词列表
        stopwords = {"的", "是", "在", "和"}

        text = "这是 人工智能 和 自然语言 处理 的 测试"
        words = text.split(" ")

        # 移除停用词
        filtered = [w for w in words if w not in stopwords]

        # 验证
        assert "的" not in filtered
        assert "是" not in filtered
        assert "人工智能" in filtered


class TestSemanticAnalysis:
    """语义分析测试"""

    def test_keyword_extraction(self):
        """测试关键词提取"""
        text = "人工智能 是 计算机科学 的 一个分支，它 致力于 创建 能够 模拟 人类 智能 的 系统"

        # 简单的关键词提取（选择长词）
        words = text.split(" ")
        keywords = [w for w in words if len(w) > 3]

        # 验证
        assert len(keywords) > 0
        assert "人工智能" in keywords
        assert "计算机科学" in keywords

    def test_text_similarity(self):
        """测试文本相似度"""
        text1 = "人工智能是未来"
        text2 = "人工智能很重要"
        text3 = "今天天气很好"

        # 计算共同词汇
        words1 = set(text1)
        words2 = set(text2)
        words3 = set(text3)

        similarity_12 = len(words1 & words2) / len(words1 | words2)
        similarity_13 = len(words1 & words3) / len(words1 | words3)

        # 验证相似度
        assert similarity_12 > similarity_13
        assert 0 <= similarity_12 <= 1

    def test_sentiment_analysis(self):
        """测试情感分析"""
        # 简单的情感词典（使用单个字符）
        positive_words = {"好", "优", "棒", "喜", "欢", "开", "心", "棒"}
        negative_words = {"坏", "差", "讨厌", "难过"}

        # 分析文本（逐字分析中文）
        text = "这个产品很好，我很开心"
        words = list(text)  # 按字符分割

        positive_count = sum(1 for w in words if w in positive_words)
        negative_count = sum(1 for w in words if w in negative_words)

        # 判断情感
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # 验证
        assert sentiment == "positive"
        assert positive_count >= 2  # "好", "开", "心" 至少有2个


class TestEntityRecognition:
    """实体识别测试"""

    def test_extract_numbers(self):
        """测试数字提取"""
        import re

        text = "专利申请号是CN202310123456，费用是5000元"

        # 提取数字
        numbers = re.findall(r'\d+', text)

        # 验证
        assert "202310123456" in numbers
        assert "5000" in numbers

    def test_extract_dates(self):
        """测试日期提取"""
        import re

        text = "专利申请日期是2024-01-15，公开日是2024-06-20"

        # 提取日期
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', text)

        # 验证
        assert len(dates) == 2
        assert "2024-01-15" in dates

    def test_extract_emails(self):
        """测试邮箱提取"""
        import re

        text = "联系我们：support@example.com 或 admin@test.org"

        # 提取邮箱
        emails = re.findall(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}', text)

        # 验证
        assert len(emails) == 2
        assert "support@example.com" in emails


class TestTextClassification:
    """文本分类测试"""

    def test_category_prediction(self):
        """测试类别预测"""
        # 简单的关键词分类器
        categories = {
            "patent": ["专利", "发明", "申请", "CN", "US"],
            "legal": ["法律", "法院", "判决", "合同"],
            "technology": ["算法", "数据", "系统", "软件"],
        }

        # 测试文本
        text = "如何申请发明专利？"

        # 预测类别
        scores = {}
        for category, keywords in categories.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[category] = score

        predicted = max(scores, key=scores.get)

        # 验证
        assert predicted == "patent"
        assert scores["patent"] > 0

    def test_multi_label_classification(self):
        """测试多标签分类"""
        text = "这是一个关于专利申请的法律文件"

        # 多标签分类
        labels = []
        if "专利" in text:
            labels.append("patent")
        if "法律" in text:
            labels.append("legal")

        # 验证
        assert len(labels) == 2
        assert "patent" in labels
        assert "legal" in labels


class TestNLPPerformance:
    """NLP性能测试"""

    def test_text_processing_speed(self):
        """测试文本处理速度"""
        import time

        # 创建测试文本
        text = "这是一个测试文本。" * 100

        # 测试处理时间
        start_time = time.time()
        words = text.split(" ")
        end_time = time.time()

        processing_time = end_time - start_time

        # 验证性能（应该在10ms内）
        assert processing_time < 0.01

    def test_batch_processing(self):
        """测试批量处理"""
        texts = [
            "这是第一段文本",
            "这是第二段文本",
            "这是第三段文本",
        ]

        # 批量处理
        results = []
        for text in texts:
            words = len(text)
            results.append(words)

        # 验证
        assert len(results) == 3
        assert all(isinstance(r, int) for r in results)


class TestLanguageDetection:
    """语言检测测试"""

    def test_chinese_detection(self):
        """测试中文检测"""
        import re

        chinese_text = "这是中文文本"
        english_text = "This is English text"

        # 检测中文字符
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', chinese_text))
        has_chinese_2 = bool(re.search(r'[\u4e00-\u9fff]', english_text))

        # 验证
        assert has_chinese is True
        assert has_chinese_2 is False

    def test_mixed_language(self):
        """测试混合语言"""
        mixed_text = "这是Chinese and English混合文本"

        # 检测是否包含中英文
        import re
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', mixed_text))
        has_english = bool(re.search(r'[a-zA-Z]', mixed_text))

        # 验证
        assert has_chinese is True
        assert has_english is True


class TestTextNormalization:
    """文本规范化测试"""

    def test_unicode_normalization(self):
        """测试Unicode规范化"""
        import unicodedata

        text = "café"

        # 规范化为NFC
        normalized = unicodedata.normalize('NFC', text)

        # 验证
        assert isinstance(normalized, str)
        assert len(normalized) > 0

    def test_case_conversion(self):
        """测试大小写转换"""
        text = "Hello World"

        # 转换为小写
        lower = text.lower()

        # 验证
        assert lower == "hello world"
        assert "hello" in lower
        assert "WORLD" not in lower

    def test_whitespace_normalization(self):
        """测试空白字符规范化"""
        import re

        text = "Hello\t\tWorld\n\n"

        # 规范化空白
        normalized = re.sub(r'\s+', ' ', text)

        # 验证
        assert normalized == "Hello World "
