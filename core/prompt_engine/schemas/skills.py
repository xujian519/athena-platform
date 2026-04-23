"""
Domain: skills
Generated schemas for 8 prompt(s).
"""

from core.prompt_engine.schema import PromptSchema, VariableSpec, VariableType

# --- skills/SKILL_TEMPLATE (staging) ---
SKILLS_SKILL_TEMPLATE_SCHEMA = PromptSchema(
    rule_id="skills/SKILL_TEMPLATE",
    template_version="0.9.0",
    variables=[
    ],
)

# --- skills/legal-world-model/INSTALL (staging) ---
SKILLS_LEGAL_WORLD_MODEL_INSTALL_SCHEMA = PromptSchema(
    rule_id="skills/legal-world-model/INSTALL",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="layer2",
            source="system",
        ),
        VariableSpec(
            name="layer3",
            source="system",
        ),
        VariableSpec(
            name="legal_world_model",
            source="system",
        ),
        VariableSpec(
            name="patent_retrieval",
            source="system",
        ),
        VariableSpec(
            name="scenario_planner",
            source="system",
        ),
    ],
)

# --- skills/legal-world-model/README (staging) ---
SKILLS_LEGAL_WORLD_MODEL_README_SCHEMA = PromptSchema(
    rule_id="skills/legal-world-model/README",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="Patent_Retrieval",
            source="system",
        ),
        VariableSpec(
            name="Prompt_System",
            source="system",
        ),
        VariableSpec(
            name="Scenario_Planner",
            source="system",
        ),
        VariableSpec(
            name="layer2",
            source="system",
        ),
        VariableSpec(
            name="layer3",
            source="system",
        ),
    ],
)

# --- skills/legal-world-model/SKILL (staging) ---
SKILLS_LEGAL_WORLD_MODEL_SKILL_SCHEMA = PromptSchema(
    rule_id="skills/legal-world-model/SKILL",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="answer",
            source="system",
        ),
        VariableSpec(
            name="conclusion",
            source="system",
        ),
        VariableSpec(
            name="confidence",
            source="system",
        ),
        VariableSpec(
            name="layer1",
            source="system",
        ),
        VariableSpec(
            name="layer2",
            source="system",
        ),
        VariableSpec(
            name="layer3",
            source="system",
        ),
    ],
)

# --- skills/patent-retrieval/README (staging) ---
SKILLS_PATENT_RETRIEVAL_README_SCHEMA = PromptSchema(
    rule_id="skills/patent-retrieval/README",
    template_version="0.9.0",
    variables=[
        VariableSpec(
            name="SKILL_md",
            source="system",
        ),
        VariableSpec(
            name="docs_reports_patent_retrieval_final_report_md",
            type=VariableType.LIST,
            source="system",
        ),
        VariableSpec(
            name="references_database_schema_md",
            source="system",
        ),
    ],
)

# --- skills/patent-retrieval/SKILL (staging) ---
SKILLS_PATENT_RETRIEVAL_SKILL_SCHEMA = PromptSchema(
    rule_id="skills/patent-retrieval/SKILL",
    template_version="0.9.0",
    variables=[
    ],
)

# --- skills/patent-retrieval/references/database-schema (staging) ---
SKILLS_PATENT_RETRIEVAL_REFERENCES_DATABASE_SCHEMA_SCHEMA = PromptSchema(
    rule_id="skills/patent-retrieval/references/database-schema",
    template_version="0.9.0",
    variables=[
    ],
)

# --- skills/public/hello-world/SKILL (staging) ---
SKILLS_PUBLIC_HELLO_WORLD_SKILL_SCHEMA = PromptSchema(
    rule_id="skills/public/hello-world/SKILL",
    template_version="0.9.0",
    variables=[
    ],
)
