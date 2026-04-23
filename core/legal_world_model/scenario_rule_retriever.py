#!/usr/bin/env python3
from __future__ import annotations
"""
场景规则检索器 - 从Neo4j检索场景规则
Scenario Rule Retriever - Retrieve scenario rules from Neo4j

版本: 1.0.0
创建时间: 2026-01-23
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ScenarioRule:
    """
    场景规则数据类

    包含场景的所有规则信息:提示词模板、处理规则、工作流等
    """

    rule_id: str
    domain: str
    task_type: str
    phase: str

    # 提示词模板
    system_prompt_template: str
    user_prompt_template: str

    # 处理规则和工作流
    processing_rules: list[str] = field(default_factory=list)
    workflow_steps: list[dict[str, Any]] = field(default_factory=list)

    # 变量定义
    variables: dict[str, str] = field(default_factory=dict)

    # 法律依据和参考案例
    legal_basis: list[str] = field(default_factory=list)
    reference_cases: list[dict[str, str]] = field(default_factory=list)

    # 能力调用配置(用于动态提示词系统调用RAG等能力)
    capability_invocations: list[dict[str, Any]] = field(default_factory=list)

    # 专家配置
    expert_config: dict[str, Any] = field(default_factory=dict)

    # 系统配置
    agent_level: str = "L2"
    lyra_optimization: bool = True
    lyra_focus: list[str] = field(default_factory=list)

    def substitute_variables(self, variables: dict[str, Any]) -> tuple[str, str]:
        """
        替换提示词模板中的变量

        Args:
            variables: 变量值字典

        Returns:
            (system_prompt, user_prompt): 替换后的提示词
        """
        system_prompt = self.system_prompt_template
        user_prompt = self.user_prompt_template

        # 替换所有变量占位符
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            system_prompt = system_prompt.replace(placeholder, str(value))
            user_prompt = user_prompt.replace(placeholder, str(value))

        return system_prompt, user_prompt

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "rule_id": self.rule_id,
            "domain": self.domain,
            "task_type": self.task_type,
            "phase": self.phase,
            "system_prompt_template": self.system_prompt_template,
            "user_prompt_template": self.user_prompt_template,
            "processing_rules": self.processing_rules,
            "workflow_steps": self.workflow_steps,
            "variables": self.variables,
            "legal_basis": self.legal_basis,
            "reference_cases": self.reference_cases,
            "capability_invocations": self.capability_invocations,
            "expert_config": self.expert_config,
            "agent_level": self.agent_level,
            "lyra_optimization": self.lyra_optimization,
            "lyra_focus": self.lyra_focus,
        }


class ScenarioRuleRetriever:
    """
    场景规则检索器

    从Neo4j知识图谱中检索场景规则、法律依据和参考案例
    """

    def __init__(self, db_manager):
        """
        初始化规则检索器

        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager

    def retrieve_rule(
        self, domain: str, task_type: str, phase: Optional[str] = None
    ) -> ScenarioRule | None:
        """
        从Neo4j检索场景规则

        Args:
            domain: 领域 (patent/trademark/legal)
            task_type: 任务类型 (creativity_analysis/novelty_analysis/etc.)
            phase: 阶段 (application/examination/litigation),可选

        Returns:
            ScenarioRule: 场景规则对象,如果未找到则返回None
        """
        logger.info(f"🔍 检索场景规则: {domain}/{task_type}/{phase or 'any'}")

        with self.db_manager.neo4j_session() as session:
            # 构建查询
            phase_filter = ""
            params = {"domain": domain, "task_type": task_type}

            if phase:
                phase_filter = "AND sr.phase = $phase"
                params["phase"] = phase

            cypher = f"""
                MATCH (sr:ScenarioRule)
                WHERE sr.domain = $domain
                  AND sr.task_type = $task_type
                  AND sr.is_active = true
                  {phase_filter}
                RETURN sr
                ORDER BY sr.version DESC
                LIMIT 1
            """

            result = session.run(cypher, **params)
            record = result.single()

            if not record:
                logger.warning(f"⚠️ 未找到场景规则: {domain}/{task_type}/{phase or 'any'}")
                return None

            sr_node = record["sr"]

            # 解析JSON字段
            try:
                processing_rules = json.loads(sr_node.get("processing_rules", "[]"))
                workflow_steps = json.loads(sr_node.get("workflow_steps", "[]"))
                variables = json.loads(sr_node.get("variables", "{}"))
                legal_basis = json.loads(sr_node.get("legal_basis", "[]"))
                reference_cases = json.loads(sr_node.get("reference_cases", "[]"))
                capability_invocations = json.loads(sr_node.get("capability_invocations", "[]"))
                expert_config = json.loads(sr_node.get("expert_config", "{}"))
                lyra_focus = json.loads(sr_node.get("lyra_focus", "[]"))
            except json.JSONDecodeError as e:
                logger.error(f"❌ 解析规则JSON失败: {e}")
                return None

            rule = ScenarioRule(
                rule_id=sr_node.get("rule_id", ""),
                domain=sr_node.get("domain", ""),
                task_type=sr_node.get("task_type", ""),
                phase=sr_node.get("phase", ""),
                system_prompt_template=sr_node.get("system_prompt_template", ""),
                user_prompt_template=sr_node.get("user_prompt_template", ""),
                processing_rules=processing_rules,
                workflow_steps=workflow_steps,
                variables=variables,
                legal_basis=legal_basis,
                reference_cases=reference_cases,
                capability_invocations=capability_invocations,
                expert_config=expert_config,
                agent_level=sr_node.get("agent_level", "L2"),
                lyra_optimization=sr_node.get("lyra_optimization", True),
                lyra_focus=lyra_focus,
            )

            logger.info(f"✅ 找到场景规则: {rule.rule_id}")

            return rule

    def retrieve_all_rules_for_domain(self, domain: str) -> list[ScenarioRule]:
        """
        检索指定领域的所有规则

        Args:
            domain: 领域

        Returns:
            list[ScenarioRule]: 规则列表
        """
        logger.info(f"🔍 检索领域所有规则: {domain}")

        with self.db_manager.neo4j_session() as session:
            cypher = """
                MATCH (sr:ScenarioRule)
                WHERE sr.domain = $domain
                  AND sr.is_active = true
                RETURN sr
                ORDER BY sr.task_type, sr.phase, sr.version DESC
            """

            result = session.run(cypher, domain=domain)

            rules = []
            for record in result:
                sr_node = record["sr"]

                try:
                    rule = ScenarioRule(
                        rule_id=sr_node.get("rule_id", ""),
                        domain=sr_node.get("domain", ""),
                        task_type=sr_node.get("task_type", ""),
                        phase=sr_node.get("phase", ""),
                        system_prompt_template=sr_node.get("system_prompt_template", ""),
                        user_prompt_template=sr_node.get("user_prompt_template", ""),
                        processing_rules=json.loads(sr_node.get("processing_rules", "[]")),
                        workflow_steps=json.loads(sr_node.get("workflow_steps", "[]")),
                        variables=json.loads(sr_node.get("variables", "{}")),
                        legal_basis=json.loads(sr_node.get("legal_basis", "[]")),
                        reference_cases=json.loads(sr_node.get("reference_cases", "[]")),
                        capability_invocations=json.loads(
                            sr_node.get("capability_invocations", "[]")
                        ),
                        expert_config=json.loads(sr_node.get("expert_config", "{}")),
                        agent_level=sr_node.get("agent_level", "L2"),
                        lyra_optimization=sr_node.get("lyra_optimization", True),
                        lyra_focus=json.loads(sr_node.get("lyra_focus", "[]")),
                    )

                    rules.append(rule)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ 解析规则JSON失败: {e}")
                    continue

            logger.info(f"✅ 找到 {len(rules)} 条规则")

            return rules

    def retrieve_legal_basis_for_rule(self, rule_id: str) -> list[dict[str, Any]]:
        """
        检索规则关联的法律依据

        Args:
            rule_id: 规则ID

        Returns:
            list[Dict]: 法律依据列表
        """
        logger.info(f"🔍 检索法律依据: {rule_id}")

        with self.db_manager.neo4j_session() as session:
            cypher = """
                MATCH (sr:ScenarioRule {rule_id: $rule_id})-[:HAS_LEGAL_BASIS]->(law)
                RETURN law.title AS title,
                       law.content AS content,
                       labels(law)[0] AS law_type,
                       law.node_id AS law_id
                ORDER BY law_type, title
            """

            result = session.run(cypher, rule_id=rule_id)

            legal_basis = []
            for record in result:
                legal_basis.append(
                    {
                        "title": record["title"],
                        "content": record.get("content", "")[:500],
                        "law_type": record["law_type"],
                        "law_id": record.get("law_id", ""),
                    }
                )

            logger.info(f"✅ 找到 {len(legal_basis)} 条法律依据")

            return legal_basis

    def retrieve_reference_cases_for_rule(self, rule_id: str) -> list[dict[str, Any]]:
        """
        检索规则关联的参考案例

        Args:
            rule_id: 规则ID

        Returns:
            list[Dict]: 参考案例列表
        """
        logger.info(f"🔍 检索参考案例: {rule_id}")

        with self.db_manager.neo4j_session() as session:
            cypher = """
                MATCH (sr:ScenarioRule {rule_id: $rule_id})-[:HAS_REFERENCE_CASE]->(case)
                RETURN case.case_number AS case_number,
                       case.title AS title,
                       case.court_name AS court,
                       substring(case.judgment_result, 0, 500) AS result
                LIMIT 10
            """

            result = session.run(cypher, rule_id=rule_id)

            cases = []
            for record in result:
                cases.append(
                    {
                        "case_number": record["case_number"],
                        "title": record["title"],
                        "court": record.get("court", ""),
                        "result": record.get("result", ""),
                    }
                )

            logger.info(f"✅ 找到 {len(cases)} 个参考案例")

            return cases

    def retrieve_rule_with_relations(
        self, domain: str, task_type: str, phase: Optional[str] = None
    ) -> ScenarioRule | None:
        """
        检索规则及其关联的法律依据和参考案例

        Args:
            domain: 领域
            task_type: 任务类型
            phase: 阶段

        Returns:
            ScenarioRule: 包含法律依据和参考案例的规则对象
        """
        # 1. 检索规则
        rule = self.retrieve_rule(domain, task_type, phase)
        if not rule:
            return None

        # 2. 检索法律依据
        legal_basis = self.retrieve_legal_basis_for_rule(rule.rule_id)
        rule.legal_basis = legal_basis

        # 3. 检索参考案例
        reference_cases = self.retrieve_reference_cases_for_rule(rule.rule_id)
        rule.reference_cases = reference_cases

        return rule

    def list_available_scenarios(self, domain: Optional[str] = None) -> list[dict[str, str]]:
        """
        列出可用的场景

        Args:
            domain: 可选,过滤特定领域

        Returns:
            list[Dict]: 场景列表,每个场景包含domain, task_type, phase等信息
        """
        logger.info(f"🔍 列出可用场景: {domain or 'all'}")

        with self.db_manager.neo4j_session() as session:
            if domain:
                cypher = """
                    MATCH (sr:ScenarioRule)
                    WHERE sr.domain = $domain
                      AND sr.is_active = true
                    RETURN DISTINCT
                        sr.domain AS domain,
                        sr.task_type AS task_type,
                        sr.phase AS phase,
                        sr.name AS name,
                        count(sr) AS rule_count
                    ORDER BY domain, task_type, phase
                """
                result = session.run(cypher, domain=domain)
            else:
                cypher = """
                    MATCH (sr:ScenarioRule)
                    WHERE sr.is_active = true
                    RETURN DISTINCT
                        sr.domain AS domain,
                        sr.task_type AS task_type,
                        sr.phase AS phase,
                        sr.name AS name,
                        count(sr) AS rule_count
                    ORDER BY domain, task_type, phase
                """
                result = session.run(cypher)

            scenarios = []
            for record in result:
                scenarios.append(
                    {
                        "domain": record["domain"],
                        "task_type": record["task_type"],
                        "phase": record["phase"],
                        "name": record["name"],
                        "rule_count": record["rule_count"],
                    }
                )

            logger.info(f"✅ 找到 {len(scenarios)} 个场景")

            return scenarios

    def create_rule(self, rule: ScenarioRule) -> bool:
        """
        创建新规则

        Args:
            rule: 规则对象

        Returns:
            bool: 是否创建成功
        """
        logger.info(f"📝 创建新规则: {rule.rule_id}")

        try:
            with self.db_manager.neo4j_session() as session:
                cypher = """
                    CREATE (sr:ScenarioRule {
                        rule_id: $rule_id,
                        domain: $domain,
                        task_type: $task_type,
                        phase: $phase,

                        system_prompt_template: $system_prompt_template,
                        user_prompt_template: $user_prompt_template,

                        processing_rules: $processing_rules,
                        workflow_steps: $workflow_steps,
                        variables: $variables,

                        legal_basis: $legal_basis,
                        reference_cases: $reference_cases,
                        capability_invocations: $capability_invocations,

                        expert_config: $expert_config,

                        agent_level: $agent_level,
                        lyra_optimization: $lyra_optimization,
                        lyra_focus: $lyra_focus,

                        name: $name,
                        description: $description,
                        version: $version,
                        created_at: datetime(),
                        updated_at: datetime(),
                        is_active: true
                    })
                """

                session.run(
                    cypher,
                    rule_id=rule.rule_id,
                    domain=rule.domain,
                    task_type=rule.task_type,
                    phase=rule.phase,
                    system_prompt_template=rule.system_prompt_template,
                    user_prompt_template=rule.user_prompt_template,
                    processing_rules=json.dumps(rule.processing_rules, ensure_ascii=False),
                    workflow_steps=json.dumps(rule.workflow_steps, ensure_ascii=False),
                    variables=json.dumps(rule.variables, ensure_ascii=False),
                    legal_basis=json.dumps(rule.legal_basis, ensure_ascii=False),
                    reference_cases=json.dumps(rule.reference_cases, ensure_ascii=False),
                    capability_invocations=json.dumps(
                        rule.capability_invocations, ensure_ascii=False
                    ),
                    expert_config=json.dumps(rule.expert_config, ensure_ascii=False),
                    agent_level=rule.agent_level,
                    lyra_optimization=rule.lyra_optimization,
                    lyra_focus=json.dumps(rule.lyra_focus, ensure_ascii=False),
                    name=rule.rule_id,  # 简化处理
                    description=f"{rule.domain} - {rule.task_type}",
                    version="1.0.0",
                )

            logger.info(f"✅ 规则创建成功: {rule.rule_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 规则创建失败: {e}")
            return False


# 便捷函数
def retrieve_scenario_rule(
    db_manager: Any | None = None, domain: Optional[str] = None, task_type: Optional[str] = None, phase: Optional[str] = None
) -> ScenarioRule | None:
    """
    便捷函数:检索场景规则

    Args:
        db_manager: 数据库管理器
        domain: 领域
        task_type: 任务类型
        phase: 阶段

    Returns:
        ScenarioRule: 规则对象或None
    """
    retriever = ScenarioRuleRetriever(db_manager)
    return retriever.retrieve_rule_with_relations(domain, task_type, phase)
