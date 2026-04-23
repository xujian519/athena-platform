#!/usr/bin/env python3
"""
分析工具模块
Analysis Tools Module

提供文本分析、统计分析、机器学习分析等功能
Provides text analysis, statistical analysis, machine learning analysis and other functions

作者: Athena AI系统
创建时间: 2025-12-06
版本: 1.0.0
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入分析工具依赖
try:
    import numpy as np
    import pandas as pd
    PANDAS_AVAILABLE = True
    NUMPY_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    NUMPY_AVAILABLE = False

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import sent_tokenize, word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

__all__ = [
    'TextAnalyzer',
    'StatisticalAnalyzer',
    'MLAnalyzer'
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'Athena AI系统'

class TextAnalyzer:
    """文本分析器"""

    def __init__(self):
        self.nltk_available = NLTK_AVAILABLE
        self.textblob_available = TEXTBLOB_AVAILABLE

    def sentiment_analysis(self, text):
        """情感分析"""
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                return {
                    'polarity': blob.sentiment.polarity,
                    'subjectivity': blob.sentiment.subjectivity
                }
            except Exception as e:
                return {'error': f'Sentiment analysis failed: {str(e)}'}
        else:
            return {'error': 'TextBlob not available'}

    def text_statistics(self, text):
        """文本统计"""
        try:
            words = text.split()
            sentences = text.split('.')

            return {
                'char_count': len(text),
                'word_count': len(words),
                'sentence_count': len(sentences),
                'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0
            }
        except Exception as e:
            return {'error': f'Text statistics failed: {str(e)}'}

    def keyword_extraction(self, text, top_n=10):
        """关键词提取"""
        if SKLEARN_AVAILABLE:
            try:
                vectorizer = TfidfVectorizer(max_features=top_n, stop_words='english')
                tfidf_matrix = vectorizer.fit_transform([text])
                feature_names = vectorizer.get_feature_names_out()
                tfidf_scores = tfidf_matrix.toarray()[0]

                # 获取top关键词
                top_indices = tfidf_scores.argsort()[-top_n:][::-1]
                keywords = [(feature_names[i], tfidf_scores[i]) for i in top_indices]

                return keywords
            except Exception as e:
                return {'error': f'Keyword extraction failed: {str(e)}'}
        else:
            return {'error': 'Scikit-learn not available'}

class StatisticalAnalyzer:
    """统计分析器"""

    def __init__(self):
        self.pandas_available = PANDAS_AVAILABLE
        self.numpy_available = NUMPY_AVAILABLE

    def descriptive_statistics(self, data):
        """描述性统计"""
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            try:
                return data.describe()
            except Exception as e:
                return {'error': f'Descriptive statistics failed: {str(e)}'}
        elif NUMPY_AVAILABLE and isinstance(data, (list, np.ndarray)):
            try:
                arr = np.array(data)
                return {
                    'mean': np.mean(arr),
                    'median': np.median(arr),
                    'std': np.std(arr),
                    'min': np.min(arr),
                    'max': np.max(arr),
                    'count': len(arr)
                }
            except Exception as e:
                return {'error': f'Descriptive statistics failed: {str(e)}'}
        else:
            return {'error': 'Invalid data format or missing dependencies'}

    def correlation_analysis(self, data):
        """相关性分析"""
        if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
            try:
                return data.corr()
            except Exception as e:
                return {'error': f'Correlation analysis failed: {str(e)}'}
        else:
            return {'error': 'Pandas not available or invalid data format'}

class MLAnalyzer:
    """机器学习分析器"""

    def __init__(self):
        self.sklearn_available = SKLEARN_AVAILABLE
        self.pandas_available = PANDAS_AVAILABLE
        self.numpy_available = NUMPY_AVAILABLE

    def text_clustering(self, texts, n_clusters=5):
        """文本聚类"""
        if not SKLEARN_AVAILABLE:
            return {'error': 'Scikit-learn not available'}

        try:
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            X = vectorizer.fit_transform(texts)

            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(X)

            return {
                'clusters': clusters.tolist(),
                'cluster_centers': kmeans.cluster_centers_.tolist(),
                'inertia': kmeans.inertia_
            }
        except Exception as e:
            return {'error': f'Text clustering failed: {str(e)}'}

    def dimensionality_reduction(self, data, n_components=2):
        """降维分析"""
        if not SKLEARN_AVAILABLE:
            return {'error': 'Scikit-learn not available'}

        try:
            pca = PCA(n_components=n_components)
            reduced_data = pca.fit_transform(data)

            return {
                'reduced_data': reduced_data.tolist(),
                'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
                'total_variance_explained': sum(pca.explained_variance_ratio_)
            }
        except Exception as e:
            return {'error': f'Dimensionality reduction failed: {str(e)}'}

# 工具可用性状态
TOOL_STATUS = {
    'text_analyzer': NLTK_AVAILABLE or TEXTBLOB_AVAILABLE,
    'statistical_analyzer': PANDAS_AVAILABLE or NUMPY_AVAILABLE,
    'ml_analyzer': SKLEARN_AVAILABLE,
    'nltk_features': NLTK_AVAILABLE,
    'sklearn_features': SKLEARN_AVAILABLE,
    'textblob_features': TEXTBLOB_AVAILABLE
}

def get_available_tools():
    """获取可用的工具列表"""
    return [tool for tool, available in TOOL_STATUS.items() if available]

def get_tool_status():
    """获取工具状态信息"""
    return TOOL_STATUS.copy()

def check_dependencies():
    """检查依赖库状态"""
    deps = {
        'pandas': PANDAS_AVAILABLE,
        'numpy': NUMPY_AVAILABLE,
        'nltk': NLTK_AVAILABLE,
        'sklearn': SKLEARN_AVAILABLE,
        'textblob': TEXTBLOB_AVAILABLE
    }
    return deps

if __name__ == '__main__':
    logger.info('🔧 分析工具模块状态')
    logger.info(f"版本: {__version__}")
    logger.info(f"作者: {__author__}")
    logger.info(f"\n可用工具: {get_available_tools()}")
    logger.info(f"依赖检查: {check_dependencies()}")

    # 简单功能测试
    try:
        analyzer = TextAnalyzer()
        logger.info("✅ TextAnalyzer 初始化成功")

        # 测试文本统计
        test_text = 'This is a test sentence for analysis.'
        stats = analyzer.text_statistics(test_text)
        logger.info(f"✅ 文本统计测试: {stats}")

    except Exception as e:
        logger.info(f"❌ TextAnalyzer 测试失败: {e}")
