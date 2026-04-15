#!/usr/bin/env python3
"""
法律实体抽取器
Legal Entity Extractor

混合抽取策略:
1. 规则抽取:基于正则和关键词(免费、快速)
2. 轻量LLM:使用本地小模型(如Qwen2.5-7B/Gemma-2-9B)
3. 云端LLM:选择性使用,仅用于高价值条款(成本可控)

成本优化策略:
- 规则抽取覆盖80%基础实体
- 本地LLM处理15%中等复杂度
- 云端LLM仅处理5%高难度复杂条款
"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """提取的实体"""

    entity_type: str  # Subject/Object/Action/Right/Obligation/Liability
    entity_name: str
    entity_text: str
    confidence: float
    extraction_method: str  # rule/local_llm/cloud_llm
    span_start: int = 0
    span_end: int = 0


@dataclass
class ExtractedRelation:
    """提取的关系"""

    from_entity: str
    to_entity: str
    relation_type: str
    confidence: float
    extraction_method: str
    source_text: str = ""


class RuleBasedExtractor:
    """基于规则的实体抽取器(免费、快速)"""

    # 法律主体模式
    SUBJECT_PATTERNS = [
        r"(自然人|公民|法人|其他组织)",
        r"(国家机关|行政机关|司法机关|立法机关|监察机关)",
        r"(国务院|[\u4e00-\u9fa5]{2,6}人民政府)",
        r"(企业|公司|个体工商户|农村承包经营户)",
        r"(用人单位|劳动者|农民工|消费者|经营者)",
        r"(所有人|使用权人|管理人|担保权人|抵押权人)",
        r"(原告|被告|第三人|申请人|被申请人)",
        r"(专利权人|发明人|设计人)",
    ]

    # 法律行为模式
    ACTION_PATTERNS = [
        r"(签订|订立|变更|解除|撤销)合同",
        r"(申请|登记|注册|审批|许可|备案|核准)",
        r"(处罚|罚款|没收|责令停产停业)",
        r"(征收|征用|划拨|出让|转让)",
        r"(起诉|上诉|申诉|仲裁|调解)",
        r"(侵权|假冒|冒充|销售|进口|出口)",
        r"(生产|制造|使用|许诺销售)",
    ]

    # 法律权利模式
    RIGHT_PATTERNS = [
        r"(享有|具有|拥有)…(权利|权)",
        r"(可以|有权)\s*(\w{2,10}权)",
        r"(取得|获得|享有)…权",
        r"(保护|保障)…权",
    ]

    # 法律义务模式
    OBLIGATION_PATTERNS = [
        r"(应当|必须|有义务)\s*(\w{2,20})",
        r"(不得|禁止|严禁)\s*(\w{2,20})",
        r"(负责|承担)…(义务|责任)",
        r"(履行|执行)…(义务|责任)",
    ]

    # 法律责任模式
    LIABILITY_PATTERNS = [
        r"(罚款|罚金)\s*([一二三四五六七八九十百千万零\d]+)(元|万元以上)",
        r"(拘留|逮捕|监视居住|取保候审)",
        r"(有期徒刑|无期徒刑|死刑)",
        r"(吊销|注销|撤销)\s*(许可证|执照|资格)",
        r"(赔偿|补偿)\s*([\d\w二三四五六七八九十百千万]+)(元|倍)",
        r"(承担|负)…(责任|民事责任|行政责任|刑事责任)",
    ]

    def extract_from_clause(
        self, clause_text: str, clause_id: str
    ) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
        """从条款中提取实体和关系"""
        entities = []
        relations = []

        # 提取法律主体
        for pattern in self.SUBJECT_PATTERNS:
            matches = re.finditer(pattern, clause_text)
            for match in matches:
                entity_text = match.group(0)
                entities.append(
                    ExtractedEntity(
                        entity_type="Subject",
                        entity_name=entity_text,
                        entity_text=entity_text,
                        confidence=0.9,
                        extraction_method="rule",
                        span_start=match.start(),
                        span_end=match.end(),
                    )
                )

        # 提取法律行为
        for pattern in self.ACTION_PATTERNS:
            matches = re.finditer(pattern, clause_text)
            for match in matches:
                entity_text = match.group(0)
                entities.append(
                    ExtractedEntity(
                        entity_type="Action",
                        entity_name=entity_text,
                        entity_text=entity_text,
                        confidence=0.85,
                        extraction_method="rule",
                    )
                )

        # 提取权利
        for pattern in self.RIGHT_PATTERNS:
            matches = re.finditer(pattern, clause_text)
            for match in matches:
                entity_text = match.group(0)
                entities.append(
                    ExtractedEntity(
                        entity_type="Right",
                        entity_name=entity_text[:20],
                        entity_text=entity_text,
                        confidence=0.8,
                        extraction_method="rule",
                    )
                )

        # 提取义务
        for pattern in self.OBLIGATION_PATTERNS:
            matches = re.finditer(pattern, clause_text)
            for match in matches:
                entity_text = match.group(0)
                entities.append(
                    ExtractedEntity(
                        entity_type="Obligation",
                        entity_name=entity_text[:20],
                        entity_text=entity_text,
                        confidence=0.85,
                        extraction_method="rule",
                    )
                )

        # 提取责任
        for pattern in self.LIABILITY_PATTERNS:
            matches = re.finditer(pattern, clause_text)
            for match in matches:
                entity_text = match.group(0)
                entities.append(
                    ExtractedEntity(
                        entity_type="Liability",
                        entity_name=entity_text[:20],
                        entity_text=entity_text,
                        confidence=0.9,
                        extraction_method="rule",
                    )
                )

        return entities, relations


class HybridLegalExtractor:
    """混合法律实体抽取器"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化抽取器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 抽取策略配置
        self.rule_threshold = 0.8  # 规则抽取置信度阈值
        self.use_local_llm = self.config.get("use_local_llm", False)
        self.use_cloud_llm = self.config.get("use_cloud_llm", False)
        self.cloud_llm_ratio = self.config.get("cloud_llm_ratio", 0.05)  # 仅5%使用云端

        # 初始化抽取器
        self.rule_extractor = RuleBasedExtractor()
        self.local_llm = None
        self.cloud_llm_client = None

        # 统计信息
        self.stats = {
            "total_clauses": 0,
            "rule_extracted": 0,
            "local_llm_extracted": 0,
            "cloud_llm_extracted": 0,
            "rule_entities": 0,
            "local_llm_entities": 0,
            "cloud_llm_entities": 0,
        }

    def init_local_llm(self) -> bool:
        """
        初始化本地LLM(推荐轻量级模型)

        推荐模型选择(按成本/效果排序):
        1. Qwen2.5-7B-Instruct (4-5GB) - 平衡性能和成本
        2. Gemma-2-9B-IT (4-5GB) - Google优质模型
        3. GLM-4-9B-Chat (4-5GB) - 智谱本地版
        4. BGE-LLM (3-4GB) - 专门用于抽取
        """
        if not self.use_local_llm:
            return False

        try:
            # 使用llama-cpp-python加载本地模型
            from llama_cpp import Llama

            model_path = self.config.get("local_llm_path")
            if not model_path or not Path(model_path).exists():
                logger.warning("⚠️  本地LLM模型不存在,跳过本地LLM抽取")
                return False

            logger.info(f"🔄 加载本地LLM模型: {model_path}")

            self.local_llm = Llama(
                model_path=model_path,
                n_ctx=4096,  # 上下文长度
                n_gpu_layers=-1,  # 全部GPU加速
                n_threads=8,
                verbose=False,
            )

            logger.info("✅ 本地LLM加载成功")
            return True

        except Exception as e:
            logger.warning(f"⚠️  本地LLM加载失败: {e}")
            return False

    def init_cloud_llm(self) -> bool:
        """初始化云端LLM(智谱GLM)"""
        if not self.use_cloud_llm:
            return False

        try:
            from zhipuai import ZhipuAI

            api_key = self.config.get("zhipu_api_key")
            if not api_key:
                logger.warning("⚠️  未配置智谱API Key")
                return False

            self.cloud_llm_client = ZhipuAI(api_key=api_key)
            logger.info("✅ 云端LLM(智谱GLM)连接成功")
            return True

        except Exception as e:
            logger.warning(f"⚠️  云端LLM连接失败: {e}")
            return False

    def extract_from_clause(
        self, clause_text: str, clause_id: str, importance_score: float = 0.5
    ) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
        """
        从条款中抽取实体和关系

        Args:
            clause_text: 条款文本
            clause_id: 条款ID
            importance_score: 重要性分数(0-1),决定使用哪种抽取策略

        Returns:
            (实体列表, 关系列表)
        """
        self.stats["total_clauses"] += 1

        # 策略1: 规则抽取(免费、快速)
        entities, relations = self.rule_extractor.extract_from_clause(clause_text, clause_id)
        self.stats["rule_extracted"] += 1
        self.stats["rule_entities"] += len(entities)

        # 策略2: 本地LLM抽取(中等成本,用于重要条款)
        if self.use_local_llm and self.local_llm and importance_score > 0.6 and len(entities) < 3:

            try:
                llm_entities = self._extract_with_local_llm(clause_text, clause_id)
                if llm_entities:
                    entities.extend(llm_entities)
                    self.stats["local_llm_extracted"] += 1
                    self.stats["local_llm_entities"] += len(llm_entities)
            except Exception as e:
                logger.warning(f"⚠️  本地LLM抽取失败: {e}")

        # 策略3: 云端LLM抽取(高成本,仅用于极重要条款,<5%)
        if (
            self.use_cloud_llm
            and self.cloud_llm_client
            and importance_score > 0.9
            and len(entities) < 3
        ):

            import random

            if random.random() < self.cloud_llm_ratio:  # 5%概率
                try:
                    llm_entities = self._extract_with_cloud_llm(clause_text, clause_id)
                    if llm_entities:
                        entities.extend(llm_entities)
                        self.stats["cloud_llm_extracted"] += 1
                        self.stats["cloud_llm_entities"] += len(llm_entities)
                except Exception as e:
                    logger.warning(f"⚠️  云端LLM抽取失败: {e}")

        return entities, relations

    def _extract_with_local_llm(self, clause_text: str, clause_id: str) -> list[ExtractedEntity]:
        """使用本地LLM抽取实体"""
        if not self.local_llm:
            return []

        prompt = f"""请从以下法律条款中提取实体(JSON格式):

条款:{clause_text}

请提取以下类型的实体:
1. Subject(法律主体):自然人、法人、行政机关等
2. Action(法律行为):签订、申请、处罚等
3. Right(权利):享有的权利
4. Obligation(义务):应当履行的义务
5. Liability(责任):违法后果

返回JSON格式:
{{"entities": [{{"type": "Subject", "name": "自然人", "text": "自然人", "confidence": 0.9}}]}}

只返回JSON,不要其他内容。"""

        try:
            response = self.local_llm(prompt, max_tokens=500, temperature=0.1, stop=["\n\n"])

            # 解析响应
            import json

            response_text = response["choices"][0]["text"].strip()

            # 提取JSON部分
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                entities = []
                for entity_data in result.get("entities", []):
                    entities.append(
                        ExtractedEntity(
                            entity_type=entity_data["type"],
                            entity_name=entity_data["name"],
                            entity_text=entity_data.get("text", entity_data["name"]),
                            confidence=entity_data.get("confidence", 0.7),
                            extraction_method="local_llm",
                        )
                    )
                return entities

        except Exception as e:
            logger.warning(f"本地LLM解析失败: {e}")

        return []

    def _extract_with_cloud_llm(self, clause_text: str, clause_id: str) -> list[ExtractedEntity]:
        """使用云端GLM抽取实体"""
        if not self.cloud_llm_client:
            return []

        prompt = f"""你是专业的法律实体抽取专家。请从以下法律条款中提取实体。

条款:{clause_text}

请提取以下类型的实体,按重要性排序:
1. Subject(法律主体):自然人、法人、行政机关等
2. Action(法律行为):签订、申请、处罚等
3. Right(权利):享有的权利
4. Obligation(义务):应当履行的义务
5. Liability(责任):违法后果

返回JSON格式,confidence为0-1之间的置信度。
"""

        try:
            response = self.cloud_llm_client.chat.completions.create(
                model="glm-4-flash",  # 使用快速版本降低成本
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800,
            )

            import json

            response_text = response.choices[0].message.content.strip()

            # 提取JSON
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                entities = []
                for entity_data in result.get("entities", []):
                    entities.append(
                        ExtractedEntity(
                            entity_type=entity_data["type"],
                            entity_name=entity_data["name"],
                            entity_text=entity_data.get("text", entity_data["name"]),
                            confidence=entity_data.get("confidence", 0.85),
                            extraction_method="cloud_llm",
                        )
                    )
                return entities

        except Exception as e:
            logger.warning(f"云端LLM抽取失败: {e}")

        return []

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_clauses": self.stats["total_clauses"],
            "extraction_distribution": {
                "rule": self.stats["rule_extracted"],
                "local_llm": self.stats["local_llm_extracted"],
                "cloud_llm": self.stats["cloud_llm_extracted"],
            },
            "entity_counts": {
                "rule": self.stats["rule_entities"],
                "local_llm": self.stats["local_llm_entities"],
                "cloud_llm": self.stats["cloud_llm_entities"],
            },
            "cost_estimate": {
                "rule_cost": 0,
                "local_llm_cost": 0,
                "cloud_llm_cost": self.stats["cloud_llm_extracted"] * 0.0001,  # 假设每次0.0001元
            },
        }

    def print_stats(self) -> Any:
        """打印统计信息"""
        stats = self.get_stats()
        logger.info("\n" + "=" * 60)
        logger.info("📊 实体抽取统计")
        logger.info("=" * 60)
        logger.info(f"总条款数: {stats['total_clauses']}")
        logger.info("\n抽取分布:")
        logger.info(f"  规则抽取: {stats['extraction_distribution']['rule']}条款")
        logger.info(f"  本地LLM: {stats['extraction_distribution']['local_llm']}条款")
        logger.info(f"  云端LLM: {stats['extraction_distribution']['cloud_llm']}条款")
        logger.info("\n实体数量:")
        logger.info(f"  规则: {stats['entity_counts']['rule']}个")
        logger.info(f"  本地LLM: {stats['entity_counts']['local_llm']}个")
        logger.info(f"  云端LLM: {stats['entity_counts']['cloud_llm']}个")
        logger.info(f"\n成本估算: ¥{stats['cost_estimate']['cloud_llm_cost']:.4f}")
        logger.info("=" * 60 + "\n")


# 便捷函数
def create_hybrid_extractor(
    use_local_llm: bool = False,
    use_cloud_llm: bool = False,
    local_llm_path: str | None = None,
    zhipu_api_key: str | None = None,
) -> HybridLegalExtractor:
    """
    创建混合抽取器

    Args:
        use_local_llm: 是否使用本地LLM
        use_cloud_llm: 是否使用云端LLM
        local_llm_path: 本地LLM路径
        zhipu_api_key: 智谱API Key

    Returns:
        混合抽取器实例
    """
    config = {
        "use_local_llm": use_local_llm,
        "use_cloud_llm": use_cloud_llm,
        "local_llm_path": local_llm_path,
        "zhipu_api_key": zhipu_api_key,
    }

    extractor = HybridLegalExtractor(config)

    # 初始化LLM
    if use_local_llm:
        extractor.init_local_llm()
    if use_cloud_llm:
        extractor.init_cloud_llm()

    return extractor
