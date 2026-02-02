#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扩展专利规则向量库
将法律法规向量合并到专利规则向量库
"""

import json
import logging
from datetime import datetime

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PatentRulesLegalExtender:
    """专利规则向量库法律法规扩展器"""

    def __init__(self):
        self.client = QdrantClient(host='localhost', port=6333)
        self.collection_name = 'patent_rules_1024'
        self.vector_dimension = 1024

        # BGE模型
        self.model_path = '/Users/xujian/Athena工作平台/models/pretrained/bge-large-zh-v1.5'
        self.model = None

        # 法律法规向量文件
        self.legal_vectors_file = '/Users/xujian/Athena工作平台/data/legal_patent_vectors/patent_legal_vectors_20251207_124420.json'

    def load_bge_model(self):
        """加载BGE模型"""
        try:
            logger.info('🔄 加载BGE Large ZH v1.5模型...')
            self.model = SentenceTransformer(self.model_path)
            logger.info('✅ BGE模型加载成功')
            return True
        except Exception as e:
            logger.error(f"❌ BGE模型加载失败: {e}")
            return False

    def create_extended_patent_rules(self):
        """创建扩展的专利规则"""
        logger.info('📚 创建扩展的专利规则...')

        extended_rules = {
            # 专利法核心条款
            'PAT_LAW_001': {
                'rule_type': 'patent_law',
                'priority': 5,
                'title': '专利法保护对象',
                'description': '专利法保护发明、实用新型和外观设计',
                'content': '专利法所称发明，是指对产品、方法或者其改进所提出的新的技术方案。专利法所称实用新型，是指对产品的形状、构造或者其结合所提出的适于实用的新的技术方案。专利法所称外观设计，是指对产品的整体或者局部的形状、图案或者其结合以及色彩与形状、图案的结合所作出的富有美感并适于工业应用的新设计。',
                'conditions': ['技术方案具有新颖性', '技术方案具有创造性', '技术方案具有实用性'],
                'actions': ['申请发明专利', '申请实用新型专利', '申请外观设计专利'],
                'confidence': 1.0,
                'source': '专利法第二条',
                'last_updated': datetime.now().isoformat()
            },
            'PAT_LAW_002': {
                'rule_type': 'patent_law',
                'priority': 5,
                'title': '专利授权条件',
                'description': '授予专利权的发明和实用新型应当具备新颖性、创造性和实用性',
                'content': '授予专利权的发明和实用新型，应当具备新颖性、创造性和实用性。新颖性，是指该发明或者实用新型不属于现有技术；也没有任何单位或者个人就同样的发明或者实用新型在申请日以前向国务院专利行政部门提出过申请，并记载在申请日以后公布的专利申请文件或者公告的专利文件中。创造性，是指与现有技术相比，该发明具有突出的实质性特点和显著的进步，该实用新型具有实质性特点和进步。实用性，是指该发明或者实用新型能够制造或者使用，并且能够产生积极效果。',
                'conditions': ['不属于现有技术', '具有创造性', '能够制造或使用', '产生积极效果'],
                'actions': ['评估新颖性', '评估创造性', '评估实用性', '提交专利申请'],
                'confidence': 0.95,
                'source': '专利法第二十二条',
                'last_updated': datetime.now().isoformat()
            },
            'PAT_LAW_003': {
                'rule_type': 'patent_law',
                'priority': 5,
                'title': '不授予专利权的情形',
                'description': '对违反法律、社会公德或者妨害公共利益的发明创造，不授予专利权',
                'content': '对违反法律、社会公德或者妨害公共利益的发明创造，不授予专利权。对违反法律、行政法规的规定获取或者利用遗传资源，并依赖该遗传资源完成的发明创造，不授予专利权。科学发现、智力活动的规则和方法、疾病的诊断和治疗方法、动物和植物品种、用原子核变换方法获得的物质等不授予专利权。',
                'conditions': ['违反法律', '违反社会公德', '妨害公共利益', '属于不授权情形'],
                'actions': ['判断是否属于不授权情形', '调整技术方案', '寻求其他保护方式'],
                'exceptions': ['产品发明的方法', '材料本身的发明'],
                'confidence': 0.98,
                'source': '专利法第五条、第二十五条',
                'last_updated': datetime.now().isoformat()
            },

            # 实施细则相关规则
            'IMPL_RULE_001': {
                'rule_type': 'implementation',
                'priority': 4,
                'title': '专利申请文件要求',
                'description': '申请发明或者实用新型专利的，应当提交请求书、说明书及其摘要和权利要求书等文件',
                'content': '申请发明或者实用新型专利的，应当提交请求书、说明书及其摘要和权利要求书等文件。请求书应当写明发明或者实用新型的名称，发明人的姓名，申请人姓名或者名称、地址，以及其他事项。说明书应当对发明或者实用新型作出清楚、完整的说明，以所属技术领域的技术人员能够实现为准；必要的时候，应当有附图。',
                'conditions': ['准备专利申请文件', '符合格式要求', '内容清楚完整'],
                'actions': ['编写请求书', '撰写说明书', '撰写权利要求书', '准备附图'],
                'confidence': 0.95,
                'source': '专利法实施细则第十六条',
                'last_updated': datetime.now().isoformat()
            },
            'IMPL_RULE_002': {
                'rule_type': 'implementation',
                'priority': 4,
                'title': '权利要求书撰写要求',
                'description': '权利要求书应当有独立权利要求，也可以有从属权利要求',
                'content': '权利要求书应当有独立权利要求，也可以有从属权利要求。独立权利要求应当从整体上反映发明或者实用新型的技术方案，记载解决技术问题的必要技术特征。从属权利要求应当用附加的技术特征，对引用的权利要求作进一步的限定。',
                'conditions': ['包含独立权利要求', '技术特征完整', '限定清楚'],
                'actions': ['确定独立权利要求', '撰写从属权利要求', '检查权利要求层次'],
                'confidence': 0.92,
                'source': '专利法实施细则第二十条',
                'last_updated': datetime.now().isoformat()
            },

            # 审查指南相关规则
            'GUIDE_001': {
                'rule_type': 'examination_guide',
                'priority': 4,
                'title': '专利审查基本原则',
                'description': '专利审查应当遵循请求原则、书面原则、程序节约原则和听证原则',
                'content': '专利审查应当遵循请求原则、书面原则、程序节约原则和听证原则。请求原则指除法律另有规定外，专利局不得主动审查专利申请。书面原则指专利申请和办理其他手续应当以书面形式提出。程序节约原则指在保证专利申请合法公正的前提下，尽量简化程序，节约资源。听证原则指在作出对申请人不利的决定前，应当给予申请人陈述意见的机会。',
                'conditions': ['遵循基本原则', '保障程序公正', '节约审查资源'],
                'actions': ['按请求原则审查', '以书面形式办理', '简化审查程序', '给予陈述机会'],
                'confidence': 0.90,
                'source': '专利审查指南',
                'last_updated': datetime.now().isoformat()
            },
            'GUIDE_002': {
                'rule_type': 'examination_guide',
                'priority': 5,
                'title': '新颖性审查标准',
                'description': '新颖性是指发明或者实用新型不属于现有技术',
                'content': '现有技术是指申请日以前在国内外为公众所知的技术。现有技术包括在申请日（有优先权的，指优先权日）以前在国内外出版物上公开发表、在国内外公开使用或者以其他方式为公众所知的技术。专利法第二十二条第三款所称的现有技术，是指申请日以前在国内外为公众所知的技术。',
                'conditions': ['不属于现有技术', '无提前公开', '满足时间要求'],
                'actions': ['检索现有技术', '对比技术方案', '判断新颖性'],
                'confidence': 0.95,
                'source': '专利审查指南',
                'last_updated': datetime.now().isoformat()
            },

            # 司法解释相关规则
            'JUDICIAL_001': {
                'rule_type': 'judicial_interpretation',
                'priority': 4,
                'title': '专利权保护范围确定',
                'description': '发明或者实用新型专利权的保护范围以其权利要求的内容为准',
                'content': '发明或者实用新型专利权的保护范围以其权利要求的内容为准，说明书及附图可以用于解释权利要求的内容。人民法院应当根据权利要求的记载，结合本领域普通技术人员阅读说明书及附图后对权利要求的理解，确定专利权的保护范围。',
                'conditions': ['权利要求明确', '说明书支持', '技术特征清楚'],
                'actions': ['解释权利要求', '参考说明书', '确定保护范围'],
                'confidence': 0.93,
                'source': '最高人民法院关于审理侵犯专利权纠纷案件应用法律若干问题的解释',
                'last_updated': datetime.now().isoformat()
            },
            'JUDICIAL_002': {
                'rule_type': 'judicial_interpretation',
                'priority': 4,
                'title': '专利侵权判定原则',
                'description': '全面覆盖原则是专利侵权判定的基本原则',
                'content': '专利法第五十九条第一款规定的发明或者实用新型专利权的保护范围以其权利要求的内容为准，说明书及附图可以用于解释权利要求的内容。人民法院判定被诉侵权技术方案是否落入专利权的保护范围，应当审查权利人主张的权利要求所记载的全部技术特征。被诉侵权技术方案包含与权利要求记载的全部技术特征相同或者等同的技术特征的，人民法院应当认定其落入专利权的保护范围；被诉侵权技术方案的技术特征与权利要求记载的全部技术特征相比，缺少权利要求记载的一个以上的技术特征，或者有一个以上技术特征不相同也不等同的，人民法院应当认定其没有落入专利权的保护范围。',
                'conditions': ['技术特征相同', '技术特征等同', '满足全面覆盖'],
                'actions': ['对比技术特征', '判断是否等同', '适用全面覆盖原则'],
                'confidence': 0.95,
                'source': '最高人民法院关于审理侵犯专利权纠纷案件应用法律若干问题的解释',
                'last_updated': datetime.now().isoformat()
            },

            # 代理相关规则
            'AGENT_001': {
                'rule_type': 'agent_regulation',
                'priority': 3,
                'title': '专利代理师执业要求',
                'description': '专利代理师应当遵守职业道德和执业纪律',
                'content': '专利代理师应当遵守职业道德和执业纪律，依法执业，勤勉尽责，诚实守信，为委托人提供规范、高效的专利代理服务，维护委托人的合法权益。专利代理师不得同时在两个以上专利代理机构从事专利代理业务，不得以自己的名义申请专利。',
                'conditions': ['取得执业资格', '遵守职业道德', '诚实守信'],
                'actions': ['办理执业证', '加入代理机构', '规范执业行为'],
                'confidence': 0.90,
                'source': '专利代理条例',
                'last_updated': datetime.now().isoformat()
            }
        }

        logger.info(f"✅ 创建了{len(extended_rules)}条扩展专利规则")
        return extended_rules

    def generate_rules_vectors(self, rules):
        """生成规则向量"""
        if not self.model:
            return []

        logger.info(f"🔄 生成{len(rules)}条扩展专利规则的向量...")

        texts = []
        for rule_id, rule_data in rules.items():
            # 构建完整文本
            text_parts = [
                f"规则ID: {rule_id}",
                f"标题: {rule_data.get('title', '')}",
                f"描述: {rule_data.get('description', '')}",
                f"内容: {rule_data.get('content', '')}",
                f"规则类型: {rule_data.get('rule_type', '')}",
                f"条件: {'; '.join(rule_data.get('conditions', []))}",
                f"行动: {'; '.join(rule_data.get('actions', []))}",
                f"例外: {'; '.join(rule_data.get('exceptions', []))}",
                f"来源: {rule_data.get('source', '')}"
            ]
            text = ' '.join(text_parts)
            texts.append(text)

        try:
            vectors = self.model.encode(
                texts,
                batch_size=8,
                normalize_embeddings=True,
                show_progress_bar=True
            )

            logger.info(f"✅ 成功生成{len(vectors)}个扩展规则向量")
            return vectors.tolist()
        except Exception as e:
            logger.error(f"❌ 向量生成失败: {e}")
            return []

    def load_legal_vectors(self):
        """加载法律法规向量"""
        try:
            with open(self.legal_vectors_file, 'r', encoding='utf-8') as f:
                legal_data = json.load(f)

            logger.info(f"✅ 加载了{len(legal_data)}个法律法规向量")
            return legal_data
        except Exception as e:
            logger.error(f"❌ 加载法律法规向量失败: {e}")
            return []

    def clear_and_recreate_collection(self):
        """清空并重新创建集合"""
        try:
            # 删除现有集合
            self.client.delete_collection(self.collection_name)
            logger.info('✅ 已删除现有集合')

            # 创建新集合
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    'size': self.vector_dimension,
                    'distance': 'Cosine'
                }
            )
            logger.info('✅ 已创建新集合')
            return True
        except Exception as e:
            logger.error(f"❌ 重建集合失败: {e}")
            return False

    def upload_all_vectors(self, rules, rule_vectors, legal_vectors):
        """上传所有向量"""
        logger.info('📤 开始上传所有向量...')

        points = []
        next_id = 0

        # 上传扩展规则
        rule_items = list(rules.items())
        for i, (rule_id, rule_data) in enumerate(rule_items):
            if i < len(rule_vectors):
                point = PointStruct(
                    id=next_id,
                    vector=rule_vectors[i],
                    payload={
                        'id': f"rule_{rule_id}",
                        'content': rule_data.get('content', ''),
                        'title': rule_data.get('title', ''),
                        'description': rule_data.get('description', ''),
                        'rule_type': rule_data.get('rule_type', ''),
                        'priority': rule_data.get('priority', 0),
                        'conditions': rule_data.get('conditions', []),
                        'actions': rule_data.get('actions', []),
                        'exceptions': rule_data.get('exceptions', []),
                        'source': rule_data.get('source', ''),
                        'confidence': rule_data.get('confidence', 0.0),
                        'vector_type': 'extended_rule',
                        'last_updated': rule_data.get('last_updated', '')
                    }
                )
                points.append(point)
                next_id += 1

        # 上传法律法规向量
        for legal_data in legal_vectors:
            chunk_info = legal_data.get('chunk_info', {})
            point = PointStruct(
                id=next_id,
                vector=legal_data['vector'],
                payload={
                    'id': f"legal_{chunk_info.get('doc_name', '')}",
                    'content': chunk_info.get('content', ''),
                    'doc_name': chunk_info.get('doc_name', ''),
                    'doc_type': chunk_info.get('doc_type', ''),
                    'file_path': chunk_info.get('file_path', ''),
                    'chunk_id': chunk_info.get('chunk_id', 0),
                    'vector_type': 'legal_document',
                    'source': '专利法律法规',
                    'created_time': legal_data.get('vectorization_time', '')
                }
            )
            points.append(point)
            next_id += 1

        # 批量上传
        try:
            batch_size = 10
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                logger.info(f"✅ 上传批次 {i//batch_size + 1}: {len(batch)} 个向量")

            logger.info(f"✅ 成功上传{len(points)}个向量")
            return True
        except Exception as e:
            logger.error(f"❌ 上传失败: {e}")
            return False

    def verify_extended_collection(self):
        """验证扩展后的集合"""
        try:
            collection_info = self.client.get_collection(self.collection_name)

            logger.info('📊 扩展后集合状态:')
            logger.info(f"   - 向量总数: {collection_info.points_count}")
            logger.info(f"   - 向量维度: {collection_info.config.params.vectors.size}")
            logger.info(f"   - 距离度量: {collection_info.config.params.vectors.distance}")

            # 统计向量类型
            all_points = self.client.scroll(
                collection_name=self.collection_name,
                limit=collection_info.points_count
            )[0]

            vector_types = {}
            for point in all_points:
                vector_type = point.payload.get('vector_type', 'unknown')
                vector_types[vector_type] = vector_types.get(vector_type, 0) + 1

            logger.info('   - 向量类型分布:')
            for vector_type, count in vector_types.items():
                logger.info(f"     * {vector_type}: {count}条")

            return True
        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            return False

    def run(self):
        """执行完整扩展流程"""
        logger.info('🚀 开始扩展专利规则向量库...')

        # 加载BGE模型
        if not self.load_bge_model():
            return False

        # 创建扩展规则
        rules = self.create_extended_patent_rules()
        if not rules:
            logger.error('❌ 创建扩展规则失败')
            return False

        # 生成规则向量
        rule_vectors = self.generate_rules_vectors(rules)
        if not rule_vectors:
            logger.error('❌ 生成规则向量失败')
            return False

        # 加载法律法规向量
        legal_vectors = self.load_legal_vectors()

        # 重建集合
        if not self.clear_and_recreate_collection():
            return False

        # 上传所有向量
        if not self.upload_all_vectors(rules, rule_vectors, legal_vectors):
            return False

        # 验证结果
        if not self.verify_extended_collection():
            return False

        logger.info('🎉 专利规则向量库扩展完成!')
        logger.info(f"📍 访问地址: http://localhost:6333/collections/{self.collection_name}")
        return True

def main():
    """主函数"""
    extender = PatentRulesLegalExtender()
    extender.run()

if __name__ == '__main__':
    main()