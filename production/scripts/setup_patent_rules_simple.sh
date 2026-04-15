#!/bin/bash
# patent_rules图空间设置脚本
# 作者: 小诺·双鱼公主 v4.0.0

echo "========================================"
echo "🚀 patent_rules图空间设置"
echo "========================================"
echo ""

# NebulaGraph连接参数
HOST="127.0.0.1"
PORT="9669"
USER="root"
PASSWORD="nebula"

# 临时命令文件
CMD_FILE="/tmp/nebula_setup_commands.txt"

# 创建命令文件
cat > $CMD_FILE << 'EOF'
-- 步骤1: 创建图空间
CREATE SPACE IF NOT EXISTS patent_rules (
    partition_num = 10,
    replica_factor = 1,
    vid_type = FIXED_STRING(256)
);

-- 等待图空间初始化(手动等待)
-- 在实际执行时需要等待20-30秒

-- 步骤2: 使用图空间
USE patent_rules;

-- 步骤3: 创建标签
CREATE TAG IF NOT EXISTS legal_term(
    name string,
    definition string,
    category string,
    source string,
    confidence double,
    created_at string
);

CREATE TAG IF NOT EXISTS document(
    title string,
    doc_type string,
    publish_date string,
    source string,
    confidence double,
    created_at string
);

CREATE TAG IF NOT EXISTS tech_field(
    name string,
    description string,
    level string,
    keywords string,
    confidence double,
    created_at string
);

CREATE TAG IF NOT EXISTS law_article(
    article_id string,
    article_name string,
    content string,
    law_type string,
    level string,
    effective_date string,
    created_at string
);

-- 步骤4: 创建边类型
CREATE EDGE IF NOT EXISTS related_to(
    relation_type string,
    strength double,
    confidence double,
    created_at string
);

CREATE EDGE IF NOT EXISTS refers_to(
    relationship_type string,
    confidence double,
    created_at string
);

CREATE EDGE IF NOT EXISTS cites(
    context string,
    confidence double,
    created_at string
);

CREATE EDGE IF NOT EXISTS applies_to(
    context string,
    relevance double,
    confidence double,
    created_at string
);

-- 步骤5: 插入测试数据
-- 插入法律术语
INSERT VERTEX legal_term(name, definition, category, source, confidence, created_at)
VALUES "专利法第22条": "专利法第22条", "创造性的规定", "法律条文", "patent_law", 1.0, "2025-12-28";

INSERT VERTEX legal_term(name, definition, category, source, confidence, created_at)
VALUES "专利法第26条": "专利法第26条", "充分公开的规定", "法律条文", "patent_law", 1.0, "2025-12-28";

INSERT VERTEX legal_term(name, definition, category, source, confidence, created_at)
VALUES "新颖性": "新颖性", "不属于现有技术", "法律概念", "patent_law", 0.95, "2025-12-28";

INSERT VERTEX legal_term(name, definition, category, source, confidence, created_at)
VALUES "创造性": "创造性", "突出的实质性特点和显著的进步", "法律概念", "patent_law", 0.95, "2025-12-28";

-- 插入法条实体
INSERT VERTEX law_article(article_id, article_name, content, law_type, level, effective_date, created_at)
VALUES "A22.3": "专利法第22条第3款", "授予专利权的发明和实用新型，应当具备新颖性、创造性和实用性。创造性，是指与现有技术相比，该发明具有突出的实质性特点和显著的进步，该实用新型具有实质性特点和进步。", "法律", "法律", "2021-06-01", "2025-12-28";

INSERT VERTEX law_article(article_id, article_name, content, law_type, level, effective_date, created_at)
VALUES "A26.3": "专利法第26条第3款", "说明书应当对发明或者实用新型作出清楚、完整的说明，以所属技术领域的技术人员能够实现为准；必要的时候，应当有附图。摘要应当简要说明发明或者实用新型的技术要点。", "法律", "法律", "2021-06-01", "2025-12-28";

-- 插入关系
INSERT EDGE related_to(relation_type, strength, confidence, created_at)
VALUES "专利法第22条"->"新颖性": "包含", 0.9, 0.95, "2025-12-28";

INSERT EDGE related_to(relation_type, strength, confidence, created_at)
VALUES "专利法第22条"->"创造性": "包含", 0.9, 0.95, "2025-12-28";

INSERT EDGE refers_to(relationship_type, confidence, created_at)
VALUES "A22.3"->"专利法第22条": "条文", 1.0, "2025-12-28";

INSERT EDGE cites(context, confidence, created_at)
VALUES "专利法第22条"->"A22.3": "条文引用", 1.0, "2025-12-28";
EOF

echo "📄 命令文件已创建: $CMD_FILE"
echo ""
echo "📋 下一步操作:"
echo "1. 使用Docker执行命令:"
echo "   docker exec -it patent_nebula_graphd nebula-console -addr 127.0.0.1 -port 9669 -u root -p nebula -f $CMD_FILE"
echo ""
echo "2. 或者手动进入NebulaGraph控制台:"
echo "   docker exec -it patent_nebula_graphd /usr/local/nebula/bin/nebula-console -addr 127.0.0.1 -port 9669"
echo ""
echo "3. 然后手动执行命令文件中的命令"
echo ""
echo "⚠️ 注意: CREATE SPACE后需要等待20-30秒让图空间初始化"
echo ""
echo "========================================"
