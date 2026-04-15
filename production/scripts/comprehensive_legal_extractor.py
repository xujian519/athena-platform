#!/usr/bin/env python3
"""
综合法律实体关系提取器
Comprehensive Legal Entity and Relation Extractor

深度提取法律法规中的实体和关系

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LegalEntity:
    """法律实体"""
    entity_id: str
    entity_type: str  # 机构、人物、地点、时间、金额、法律文件等
    entity_name: str
    normalized_name: str  # 标准化名称
    attributes: dict  # 额外属性
    context: str  # 上下文
    article_id: str
    confidence: float  # 置信度

@dataclass
class LegalRelation:
    """法律关系"""
    relation_id: str
    relation_type: str
    source_entity: str
    target_entity: str
    source_article: str
    target_article: str
    description: str
    strength: float  # 关系强度
    direction: str  # directed/undirected

class ComprehensiveLegalExtractor:
    """综合法律实体关系提取器"""

    def __init__(self):
        # 增强的实体识别模式
        self.entity_patterns = {
            "机构": {
                "中央机关": [
                    r'(国务院|全国人民代表大会|全国人大常委会|最高人民法院|最高人民检察院)',
                    r'(公安部|外交部|国防部|国家发展和改革委员会|教育部|科技部)',
                    r'(工业和信息化部|司法部|财政部|人力资源和社会保障部|自然资源部)',
                    r'(生态环境部|住房和城乡建设部|交通运输部|水利部|农业农村部)',
                    r'(商务部|文化和旅游部|国家卫生健康委员会|中国人民银行|审计署)'
                ],
                "地方机关": [
                    r'([省市区县]+人民政府)',
                    r'([省市区县]+[部委厅局])',
                    r'([省市]+人民代表大会)',
                    r'([省市]+高级|中级人民法院)',
                    r'([市区县]+人民法院)'
                ],
                "特殊机构": [
                    r'(国家监察委员会|国家市场监督管理总局|国家广播电视总局|国家体育总局)',
                    r'(国家统计局|国家国际发展合作署|国家医疗保障局|国家机关事务管理局)',
                    r'(国家粮食和物资储备局|国家能源局|国家烟草专卖局|国家移民管理局)'
                ]
            },
            "人物": {
                "职务角色": [
                    r'(国家主席|副主席|总理|副总理|国务委员|部长|副部长|省长|副省长)',
                    r'(市长|副市长|厅长|副厅长|局长|副局长|县长|副县长)',
                    r'(院长|副院长|检察长|副检察长|审判长|审判员|检察员)',
                    r'(书记|副书记|主任|副主任|委员|代表)',
                    r'(法人|法定代表人|负责人|经办人|当事人|申请人|被申请人)'
                ]
            },
            "地点": {
                "行政区划": [
                    r'(中华人民共和国|中国)',
                    r'([一二三四五六七八九十]个[省市区县自治州旗])',
                    r'([京津沪渝][市]|河北|山西|辽宁|吉林|黑龙江|江苏|浙江|安徽|福建|江西|山东|河南|湖北|湖南|广东|海南|四川|贵州|云南|陕西|甘肃|青海|台湾|内蒙古|广西|西藏|宁夏|新疆|香港|澳门)',
                    r'([特别行政区|自治区|自治州|自治县|旗])'
                ],
                "特殊区域": [
                    r'(经济特区|经济技术开发区|高新技术产业开发区|自由贸易试验区)',
                    r'(边境经济合作区|跨境经济合作区|综合保税区|出口加工区)',
                    r'(沿海开放城市|沿边开放城市|内陆开放城市)'
                ]
            },
            "时间": {
                "具体日期": [
                    r'(\d{4}年\d{1,2}月\d{1,2}日)',
                    r'([一二三四五六七八九十]+年[一二三四五六七八九十]+月[一二三四五六七八九十]+日)',
                    r'(\d{4}/\d{1,2}/\d{1,2})'
                ],
                "相对时间": [
                    r'(自本条例施行之日起|自发布之日起|施行之日起|生效之日起)',
                    r'([一二三四五六七八九十]+日内|[一二三四五六七八九十]+日内|[一二三四五六七八九十]+个月内)',
                    r'(工作日|节假日|法定节假日|休息日)',
                    r'(时效期间|诉讼时效|申请期限)'
                ]
            },
            "金额": {
                "货币金额": [
                    r'(\d+元|\d+万元|\d+亿元)',
                    r'([一二三四五六七八九十百千万亿]+元)',
                    r'(人民币\d+|美元\d+|欧元\d+)',
                    r'罚款\d+|处罚\d+|赔偿\d+|补偿\d+'
                ],
                "比例金额": [
                    r'(\d+%|\d+成|[一二三四五六七八九十]+成)',
                    r'(倍以上|以下|以内|超过)'
                ]
            },
            "法律文件": {
                "法律": [
                    r'(《[^》]*法》)',
                    r'(《[^》]*法案》)',
                    r'(《[^》]*公约》)'
                ],
                "法规": [
                    r'(《[^》]*条例》)',
                    r'(《[^》]*规定》)',
                    r'(《[^》]*办法》)',
                    r'(《[^》]*细则》)'
                ],
                "其他文件": [
                    r'(《[^》]*解释》)',
                    r'(《[^》]*决定》)',
                    r'(《[^》]*通知》)',
                    r'(《[^》]*意见》)'
                ]
            }
        }

        # 增强的关系识别模式
        self.relation_patterns = {
            "引用": {
                "直接引用": [
                    r'根据([《][^》]+[》])第([一二三四五六七八九十百千万\d]+)条',
                    r'按照([《][^》]+[》])第([一二三四五六七八九十百千万\d]+)条',
                    r'依据([《][^》]+[》])第([一二三四五六七八九十百千万\d]+)条'
                ],
                "概括引用": [
                    r'根据([《][^》]+[》])的有关规定',
                    r'按照([《][^》]+[》])的相关条款',
                    r'依据([《][^》]+[》])的要求'
                ]
            },
            "修改": {
                "直接修改": [
                    r'修改([《][^》]+[》])第([一二三四五六七八九十百千万\d]+)条',
                    r'修订([《][^》]+[》])第([一二三四五六七八九十百千万\d]+)条',
                    r'将([《][^》]+[》])第([一二三四五六七八九十百千万\d]+)条修改为'
                ]
            },
            "废止": {
                "直接废止": [
                    r'废止([《][^》]+[》])',
                    r'取消([《][^》]+[》])',
                    r'不再适用([《][^》]+[》])',
                    r'([《][^》]+[》])同时废止'
                ]
            },
            "解释": {
                "司法解释": [
                    r'对([《][^》]+[》])的解释',
                    r'([《][^》]+[》])的释义',
                    r'([《][^》]+[》])的理解与适用'
                ]
            },
            "执行": {
                "执法机关": [
                    r'由([\u4e00-\u9fff]+部|\u4e00-\u9fff]+委员会|\u4e00-\u9fff]+局)负责执行',
                    r'([\u4e00-\u9fff]+人民政府)组织实施',
                    r'([\u4e00-\u9fff]+机关)监督管理'
                ]
            }
        }

        # 实体标准化映射
        self.entity_normalization = {
            "机构": {
                "国务院": "中华人民共和国国务院",
                "全国人大": "全国人民代表大会",
                "全国人大常委会": "全国人民代表大会常务委员会",
                "最高法": "最高人民法院",
                "最高检": "最高人民检察院"
            },
            "法律文件": {
                "刑法": "中华人民共和国刑法",
                "民法典": "中华人民共和国民法典",
                "宪法": "中华人民共和国宪法"
            }
        }

    def extract_entities_from_text(self, text: str, article_id: str) -> list[LegalEntity]:
        """从文本中提取实体"""
        entities = []
        entity_counter = 0

        for entity_type, categories in self.entity_patterns.items():
            for category, patterns in categories.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        entity_name = match.group()

                        # 标准化实体名称
                        normalized_name = self.normalize_entity_name(entity_name, entity_type)

                        # 计算置信度
                        confidence = self.calculate_confidence(match, text, entity_type)

                        # 避免重复
                        if not any(e.entity_name == entity_name and e.context == match.context
                                for e in entities):
                            entity = LegalEntity(
                                entity_id=f"{entity_type}_{entity_counter:04d}",
                                entity_type=entity_type,
                                entity_name=entity_name,
                                normalized_name=normalized_name,
                                attributes={
                                    "category": category,
                                    "position": match.start(),
                                    "length": len(entity_name)
                                },
                                context=text[max(0, match.start()-30):match.end()+30],
                                article_id=article_id,
                                confidence=confidence
                            )
                            entities.append(entity)
                            entity_counter += 1

        return entities

    def normalize_entity_name(self, name: str, entity_type: str) -> str:
        """标准化实体名称"""
        # 去除冗余信息
        normalized = re.sub(r'[的的了是在]', '', name)

        # 使用映射表
        if entity_type in self.entity_normalization:
            for alias, standard in self.entity_normalization[entity_type].items():
                if alias in normalized:
                    normalized = normalized.replace(alias, standard)

        return normalized

    def calculate_confidence(self, match, text: str, entity_type: str) -> float:
        """计算实体识别置信度"""
        base_confidence = 0.8

        # 根据上下文调整
        context_before = text[:match.start()]
        context_after = text[match.end():match.end()+20]

        # 关键词增强
        if entity_type == "机构":
            if any(word in context_before for word in ["由", "经", "通过", "向"]):
                base_confidence += 0.1
            if any(word in context_after for word in ["负责", "组织", "实施", "监督"]):
                base_confidence += 0.1
        elif entity_type == "时间":
            if any(word in context_before for word in ["自", "从", "于", "在"]):
                base_confidence += 0.1
        elif entity_type == "金额":
            if any(word in context_before for word in ["罚款", "处罚", "赔偿", "补偿"]):
                base_confidence += 0.1

        return min(base_confidence, 1.0)

    def extract_relations_from_text(self, text: str, article_id: str, entities: list[LegalEntity]) -> list[LegalRelation]:
        """从文本中提取关系"""
        relations = []
        relation_counter = 0

        # 构建实体索引
        entity_index = {e.entity_name: e for e in entities}

        for relation_type, categories in self.relation_patterns.items():
            for category, patterns in categories.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        relation = self.parse_relation_match(
                            match, relation_type, category, article_id, entity_index, text
                        )
                        if relation:
                            relation.relation_id = f"{relation_type}_{relation_counter:04d}"
                            relations.append(relation)
                            relation_counter += 1

        return relations

    def parse_relation_match(self, match, relation_type: str, category: str,
                            article_id: str, entity_index: dict, text: str) -> LegalRelation | None:
        """解析关系匹配"""
        try:
            if relation_type == "引用" and "第" in match.group(0):
                # 引用关系
                law_name = match.group(1) if match.groups() else ""
                article_num = match.group(2) if len(match.groups()) > 1 else ""

                return LegalRelation(
                    relation_id="",
                    relation_type=f"{relation_type}_{category}",
                    source_entity=article_id,
                    target_entity=f"{law_name}_{article_num}" if law_name else "",
                    source_article=article_id,
                    target_article=f"{law_name}_{article_num}" if law_name else "",
                    description=f"引用{law_name}第{article_num}条" if law_name else "引用相关条款",
                    strength=0.9,
                    direction="directed"
                )

            elif relation_type == "执行":
                # 执行关系
                executor = match.group(1) if match.groups() else ""

                return LegalRelation(
                    relation_id="",
                    relation_type=f"{relation_type}_{category}",
                    source_entity=executor,
                    target_entity=article_id,
                    source_article="",
                    target_article=article_id,
                    description=f"{executor}负责执行本条款",
                    strength=0.8,
                    direction="directed"
                )

            else:
                # 其他关系类型
                target = match.group(1) if match.groups() else ""

                return LegalRelation(
                    relation_id="",
                    relation_type=f"{relation_type}_{category}",
                    source_entity=article_id,
                    target_entity=target,
                    source_article=article_id,
                    target_article="",
                    description=f"本条款{relation_type}了{target}",
                    strength=0.7,
                    direction="directed"
                )

        except Exception as e:
            logger.warning(f"解析关系失败: {e}")
            return None

    def process_legal_documents(self, data_dir: Path, limit: int = 50) -> dict:
        """批量处理法律文档"""
        logger.info(f"\n🔍 开始处理法律文档，限制: {limit}个")

        md_files = list(data_dir.rglob("*.md"))
        logger.info(f"找到 {len(md_files)} 个法律文件")

        results = {
            "timestamp": datetime.now().isoformat(),
            "processed_files": min(len(md_files), limit),
            "entities": [],
            "relations": [],
            "statistics": {
                "total_entities": 0,
                "total_relations": 0,
                "entity_types": {},
                "relation_types": {}
            }
        }

        entity_counter = 0
        relation_counter = 0

        for i, file_path in enumerate(md_files[:limit]):
            logger.info(f"\n处理 {i+1}/{limit}: {file_path.name}")

            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()

                # 提取标题
                title_match = re.search(r'^#\s*(.+)', content, re.MULTILINE)
                title = title_match.group(1) if title_match else file_path.stem

                # 识别条款（简化版）
                article_pattern = r'第([一二三四五六七八九十百千万\d]+)条[：:\s]*([^\n]*?)(?=第|$)'
                articles = re.finditer(article_pattern, content, re.MULTILINE | re.DOTALL)

                for article_match in articles:
                    article_num = article_match.group(1)
                    article_title = article_match.group(2).strip()
                    article_start = article_match.start()
                    article_end = article_match.end()

                    # 提取条款内容（到下一个条款或文件结束）
                    next_match = re.search(article_pattern, content[article_end:])
                    if next_match:
                        article_content = content[article_end:article_end + next_match.start()]
                    else:
                        article_content = content[article_end:]

                    article_content = article_content.strip()[:1000]  # 限制长度
                    article_text = f"{article_title} {article_content}"

                    # 生成条款ID
                    article_id = f"{title}_{article_num}"

                    # 提取实体
                    entities = self.extract_entities_from_text(article_text, article_id)

                    # 提取关系
                    relations = self.extract_relations_from_text(article_text, article_id, entities)

                    # 更新ID计数器
                    for entity in entities:
                        entity.entity_id = f"ent_{entity_counter:04d}"
                        entity_counter += 1
                        results["entities"].append(asdict(entity))

                    for relation in relations:
                        relation.relation_id = f"rel_{relation_counter:04d}"
                        relation_counter += 1
                        results["relations"].append(asdict(relation))

                    logger.info(f"  条款{article_num}: {len(entities)}个实体, {len(relations)}个关系")

            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")

        # 统计
        results["statistics"]["total_entities"] = len(results["entities"])
        results["statistics"]["total_relations"] = len(results["relations"])

        for entity in results["entities"]:
            etype = entity["entity_type"]
            results["statistics"]["entity_types"][etype] = results["statistics"]["entity_types"].get(etype, 0) + 1

        for relation in results["relations"]:
            rtype = relation["relation_type"]
            results["statistics"]["relation_types"][rtype] = results["statistics"]["relation_types"].get(rtype, 0) + 1

        logger.info("\n📊 提取完成:")
        logger.info(f"  处理文件: {results['processed_files']}")
        logger.info(f"  总实体数: {results['statistics']['total_entities']}")
        logger.info(f"  总关系数: {results['statistics']['total_relations']}")

        return results

    def save_results(self, results: dict) -> None:
        """保存提取结果"""
        # 保存实体
        entities_file = Path("/Users/xujian/Athena工作平台/production/data/knowledge_graph") / \
                       f"legal_entities_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        entities_file.parent.mkdir(parents=True, exist_ok=True)

        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(results["entities"], f, ensure_ascii=False, indent=2)

        # 保存关系
        relations_file = Path("/Users/xujian/Athena工作平台/production/data/knowledge_graph") / \
                        f"legal_relations_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(relations_file, 'w', encoding='utf-8') as f:
            json.dump(results["relations"], f, ensure_ascii=False, indent=2)

        # 保存完整报告
        report_file = Path("/Users/xujian/Athena工作平台/production/data/metadata") / \
                     f"entity_relation_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info("\n💾 结果已保存:")
        logger.info(f"  实体文件: {entities_file}")
        logger.info(f"  关系文件: {relations_file}")
        logger.info(f"  报告文件: {report_file}")

def main() -> None:
    """主函数"""
    print("="*100)
    print("🔍 综合法律实体关系提取器 🔍")
    print("="*100)

    extractor = ComprehensiveLegalExtractor()

    # 处理法律文档
    data_dir = Path("/Users/xujian/Athena工作平台/dev/tools/Laws-1.0.0")
    results = extractor.process_legal_documents(data_dir, limit=100)

    # 保存结果
    extractor.save_results(results)

    # 显示统计
    print("\n📈 提取统计:")
    print("  实体类型分布:")
    for etype, count in results["statistics"]["entity_types"].items():
        print(f"    {etype}: {count}")

    print("\n  关系类型分布:")
    for rtype, count in results["statistics"]["relation_types"].items():
        print(f"    {rtype}: {count}")

if __name__ == "__main__":
    main()
