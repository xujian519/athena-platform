#!/usr/bin/env python3
"""
创建优化的Elasticsearch索引映射
Create Optimized Elasticsearch Index Mapping

为专利数据创建高性能的Elasticsearch索引
"""

import json
import logging

import elasticsearch
from elasticsearch import Elasticsearch

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Elasticsearch配置
ES_CONFIG = {
    'hosts': ['http://localhost:9200'],
    'timeout': 30
}

def create_patent_index():
    """创建优化的专利索引"""
    logger.info('🔧 创建优化的专利索引映射...')

    try:
        es = Elasticsearch(**ES_CONFIG)

        # 检查连接
        if not es.ping():
            logger.error('❌ Elasticsearch连接失败')
            return False

        # 删除现有索引
        if es.indices.exists(index='patents_enhanced'):
            es.indices.delete(index='patents_enhanced')
            logger.info('🗑️ 删除现有索引')

        # 定义优化的索引映射
        mapping = {
            'settings': {
                'number_of_shards': 3,
                'number_of_replicas': 0,
                'analysis': {
                    'analyzer': {
                        'chinese_analyzer': {
                            'type': 'custom',
                            'tokenizer': 'ik_max_word',
                            'filter': ['lowercase']
                        },
                        'search_analyzer': {
                            'type': 'custom',
                            'tokenizer': 'ik_smart',
                            'filter': ['lowercase']
                        }
                    }
                }
            },
            'mappings': {
                'properties': {
                    'id': {'type': 'long'},
                    'application_number': {
                        'type': 'keyword',
                        'fields': {
                            'text': {
                                'type': 'text',
                                'analyzer': 'chinese_analyzer'
                            },
                            'suggest': {
                                'type': 'completion'
                            }
                        }
                    },
                    'patent_name': {
                        'type': 'text',
                        'analyzer': 'chinese_analyzer',
                        'fields': {
                            'keyword': {'type': 'keyword'},
                            'suggest': {
                                'type': 'completion'
                            }
                        }
                    },
                    'abstract': {
                        'type': 'text',
                        'analyzer': 'chinese_analyzer',
                        'fields': {
                            'keyword': {'type': 'keyword'}
                        }
                    },
                    'applicant': {
                        'type': 'text',
                        'analyzer': 'chinese_analyzer',
                        'fields': {
                            'keyword': {'type': 'keyword'},
                            'suggest': {
                                'type': 'completion'
                            }
                        }
                    },
                    'patent_type': {'type': 'keyword'},
                    'source_year': {'type': 'integer'},
                    'ipc_main_class': {
                        'type': 'keyword',
                        'fields': {
                            'text': {
                                'type': 'text',
                                'analyzer': 'chinese_analyzer'
                            }
                        }
                    },
                    'claims_content': {
                        'type': 'text',
                        'analyzer': 'chinese_analyzer'
                    },
                    'current_assignee': {
                        'type': 'text',
                        'analyzer': 'chinese_analyzer',
                        'fields': {
                            'keyword': {'type': 'keyword'}
                        }
                    },
                    'applicant_region': {'type': 'keyword'},
                    'citation_count': {'type': 'integer'},
                    'full_text': {
                        'type': 'text',
                        'analyzer': 'chinese_analyzer'
                    },
                    'data_quality_score': {
                        'type': 'float'
                    },
                    'sync_timestamp': {
                        'type': 'date',
                        'format': 'yyyy-MM-dd HH:mm:ss'
                    },
                    'tags': {
                        'type': 'keyword'
                    }
                }
            }
        }

        # 创建索引
        es.indices.create(
            index='patents_enhanced',
            body=mapping
        )

        logger.info('✅ 创建优化索引成功')

        # 输出索引信息
        index_info = es.indices.get(index='patents_enhanced')
        logger.info(f"📊 索引信息: {json.dumps(index_info, indent=2, ensure_ascii=False)}")

        return True

    except Exception as e:
        logger.error(f"❌ 创建索引失败: {e}")
        return False

def test_index_search():
    """测试索引搜索功能"""
    logger.info('🧪 测试索引搜索功能...')

    try:
        es = Elasticsearch(**ES_CONFIG)

        # 测试查询
        test_query = {
            'query': {
                'multi_match': {
                    'query': '人工智能',
                    'fields': ['patent_name^3', 'abstract^2', 'full_text'],
                    'type': 'best_fields'
                }
            },
            'size': 3,
            'sort': [{'_score': {'order': 'desc'}}]
        }

        response = es.search(
            index='patents_enhanced',
            body=test_query
        )

        logger.info('✅ 搜索测试成功')
        logger.info(f"📊 命中结果数: {len(response['hits']['hits'])}")

        return True

    except Exception as e:
        logger.error(f"❌ 搜索测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info('🔧 创建优化的Elasticsearch索引')
    logger.info(str('=' * 40))

    success = True

    # 创建索引
    if not create_patent_index():
        success = False

    # 测试搜索
    if success and not test_index_search():
        success = False

    if success:
        logger.info('✅ 索引创建完成！')
        logger.info("\n🚀 下一步:")
        logger.info('1. 同步专利数据到Elasticsearch')
        logger.info('2. 实现混合搜索服务')
        logger.info('3. 性能测试和优化')
    else:
        logger.info('❌ 索引创建失败')

    return success

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)