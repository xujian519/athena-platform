#!/bin/bash
# =============================================================================
# Athena法律世界模型数据备份到移动硬盘
# Backup Legal World Model Data to External Drive
#
# 备份内容：
# - Neo4j知识图谱数据
# - Qdrant向量数据库数据
# - PostgreSQL法律知识库数据
#
# 目标：/Volumes/AthenaData/Athena_Backups/
# =============================================================================

set -e  # 遇到错误立即退出

# 全局变量
EXTERNAL_DRIVE="/Volumes/AthenaData"
BACKUP_DIR=""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 分隔线
print_section() {
    echo ""
    echo "============================================================================"
    echo "$1"
    echo "============================================================================"
}

# 检查移动硬盘
check_external_drive() {
    print_section "检查移动硬盘"

    if [ ! -d "$EXTERNAL_DRIVE" ]; then
        log_error "移动硬盘未找到: $EXTERNAL_DRIVE"
        log_info "请连接移动硬盘后重试"
        exit 1
    fi

    # 检查可用空间
    available_space=$(df -h "$EXTERNAL_DRIVE" | tail -1 | awk '{print $4}' | sed 's/Gi//')
    log_success "移动硬盘已挂载: $EXTERNAL_DRIVE"
    log_info "可用空间: $available_space"

    # 创建备份目录
    BACKUP_DIR="$EXTERNAL_DRIVE/Athena_Backups/legal_world_model_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    log_success "备份目录创建成功: $BACKUP_DIR"

    # 不再echo输出，直接使用全局变量
}

# 备份Neo4j数据
backup_neo4j() {
    print_section "备份Neo4j知识图谱数据"

    log_info "数据卷: athena-neo4j-data"

    local backup_file="$BACKUP_DIR/neo4j_knowledge_graph.tar.gz"
    local backup_path_in_container="/backup${BACKUP_DIR#$EXTERNAL_DRIVE}"

    log_info "开始备份Neo4j数据..."

    # 使用临时容器备份数据
    docker run --rm \
        -v athena-neo4j-data:/data:ro \
        -v "$EXTERNAL_DRIVE:/backup" \
        alpine tar czf "$backup_path_in_container/neo4j_knowledge_graph.tar.gz" -C /data .

    if [ $? -eq 0 ]; then
        # 检查备份文件大小
        backup_size=$(du -h "$backup_file" | cut -f1)
        log_success "Neo4j备份完成: $backup_file"
        log_info "备份大小: $backup_size"
    else
        log_error "Neo4j备份失败"
        return 1
    fi
}

# 备份Qdrant数据
backup_qdrant() {
    print_section "备份Qdrant向量数据库数据"

    log_info "数据卷: athena-qdrant-data"

    local backup_file="$BACKUP_DIR/qdrant_vector_db.tar.gz"
    local backup_path_in_container="/backup${BACKUP_DIR#$EXTERNAL_DRIVE}"

    log_info "开始备份Qdrant数据..."

    # 使用临时容器备份数据
    docker run --rm \
        -v athena-qdrant-data:/data:ro \
        -v "$EXTERNAL_DRIVE:/backup" \
        alpine tar czf "$backup_path_in_container/qdrant_vector_db.tar.gz" -C /data .

    if [ $? -eq 0 ]; then
        backup_size=$(du -h "$backup_file" | cut -f1)
        log_success "Qdrant备份完成: $backup_file"
        log_info "备份大小: $backup_size"
    else
        log_error "Qdrant备份失败"
        return 1
    fi
}

# 备份PostgreSQL数据（可选）
backup_postgres() {
    print_section "备份PostgreSQL法律知识库数据（可选）"

    log_warning "PostgreSQL数据量较大（~8GB），备份需要较长时间"
    read -p "是否备份PostgreSQL数据？(y/N): " -n 2 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "跳过PostgreSQL备份"
        return 0
    fi

    log_info "数据卷: athena-postgres-data-prod"

    local backup_file="$BACKUP_DIR/postgresql_legal_knowledge.tar.gz"
    local backup_path_in_container="/backup${BACKUP_DIR#$EXTERNAL_DRIVE}"

    log_info "开始备份PostgreSQL数据..."

    # 使用临时容器备份数据
    docker run --rm \
        -v athena-postgres-data-prod:/data:ro \
        -v "$EXTERNAL_DRIVE:/backup" \
        alpine tar czf "$backup_path_in_container/postgresql_legal_knowledge.tar.gz" -C /data .

    if [ $? -eq 0 ]; then
        backup_size=$(du -h "$backup_file" | cut -f1)
        log_success "PostgreSQL备份完成: $backup_file"
        log_info "备份大小: $backup_size"
    else
        log_error "PostgreSQL备份失败"
        return 1
    fi
}

# 生成备份清单
generate_manifest() {
    print_section "生成备份清单"

    MANIFEST_FILE="$BACKUP_DIR/backup_manifest.txt"

    log_info "生成备份清单..."

    cat > "$MANIFEST_FILE" <<EOF
==============================================================================
Athena法律世界模型数据备份清单
Legal World Model Data Backup Manifest
==============================================================================

备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份主机: $(hostname)
备份目录: $BACKUP_DIR

==============================================================================
1. Neo4j知识图谱数据 (Neo4j Knowledge Graph)
==============================================================================
数据内容:
  - 节点数: 40,034个 (OpenClawNode)
  - 关系数: 407,744条
  - 数据类型: 图谱数据
  - 数据卷: athena-neo4j-data
  - 备份文件: neo4j_knowledge_graph.tar.gz

==============================================================================
2. Qdrant向量数据库 (Qdrant Vector Database)
==============================================================================
数据内容:
  - 集合数: 19个
  - 向量总数: 553,670条
  - 主要集合:
    * legal_articles_v2: 295,810条 (1024维)
    * patent_invalid_embeddings: 119,660条 (1024维)
    * judgment_embeddings: 20,478条 (1024维)
    * patent_judgment_vectors: 17,388条 (1024维)
  - 数据类型: 向量嵌入数据
  - 数据卷: athena-qdrant-data
  - 备份文件: qdrant_vector_db.tar.gz

==============================================================================
3. PostgreSQL法律知识库 (PostgreSQL Legal Knowledge)
==============================================================================
$(if [ -f "$BACKUP_DIR/postgresql_legal_knowledge.tar.gz" ]; then
数据内容:
  - 数据库: legal_world_model
  - 总记录数: 4,154,519条
  - 主要表:
    * patent_invalid_entities: 2,363,891条
    * judgment_entities: 891,659条
    * legal_articles_v2: 295,733条
    * legal_articles_v2_embeddings: 295,810条
    * patent_invalid_embeddings: 119,660条
  - 数据卷: athena-postgres-data-prod
  - 备份文件: postgresql_legal_knowledge.tar.gz
else
状态: 未备份
fi

==============================================================================
恢复说明 (Recovery Instructions)
==============================================================================

1. Neo4j数据恢复:
   docker volume create athena-neo4j-data-restored
   docker run --rm -v athena-neo4j-data-restored:/data -v /path/to/backup:/backup \
     alpine tar xzf /backup/neo4j_knowledge_graph.tar.gz -C /data
   # 更新docker-compose.yml中的卷引用

2. Qdrant数据恢复:
   docker volume create athena-qdrant-data-restored
   docker run --rm -v athena-qdrant-data-restored:/data -v /path/to/backup:/backup \
     alpine tar xzf /backup/qdrant_vector_db.tar.gz -C /data
   # 更新docker-compose.yml中的卷引用

3. PostgreSQL数据恢复:
   docker volume create athena-postgres-data-restored
   docker run --rm -v athena-postgres-data-restored:/data -v /path/to/backup:/backup \
     alpine tar xzf /backup/postgresql_legal_knowledge.tar.gz -C /data
   # 更新docker-compose.yml中的卷引用

==============================================================================
数据完整性验证 (Data Integrity Verification)
==============================================================================

备份后请运行以下命令验证数据完整性:

1. 检查备份文件大小:
   ls -lh $BACKUP_DIR/

2. 验证Neo4j备份:
   tar -tzf $BACKUP_DIR/neo4j_knowledge_graph.tar.gz | head -10

3. 验证Qdrant备份:
   tar -tzf $BACKUP_DIR/qdrant_vector_db.tar.gz | head -10

4. 计算校验和:
   md5 $BACKUP_DIR/*.tar.gz > $BACKUP_DIR/checksums.md5

==============================================================================
备份状态: ✅ 完成
Backup Status: Completed

生成时间: $(date '+%Y-%m-%d %H:%M:%S')
==============================================================================
EOF

    log_success "备份清单已生成: $MANIFEST_FILE"
}

# 计算校验和
calculate_checksums() {
    print_section "计算校验和"

    log_info "计算MD5校验和..."

    md5 "$BACKUP_DIR"/*.tar.gz > "$BACKUP_DIR/checksums.md5" 2>/dev/null || true

    log_success "校验和文件已生成: $BACKUP_DIR/checksums.md5"
}

# 显示备份摘要
show_summary() {
    print_section "备份完成摘要"

    echo ""
    echo "备份位置: $BACKUP_DIR"
    echo ""

    # 列出备份文件
    echo "备份文件列表:"
    ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | awk '{print "  " $9 " - " $5 " (" $4 ")"}' || echo "  (无文件)"

    echo ""
    log_success "所有数据备份完成！"
    echo ""
    echo "📁 备份目录: $BACKUP_DIR"
    echo "📄 清单文件: $MANIFEST_FILE"
    echo ""
    echo "💡 提示:"
    echo "  - 备份文件已压缩存储"
    echo "  - 请妥善保管移动硬盘"
    echo "  - 恢复步骤请查看: $MANIFEST_FILE"
    echo ""
}

# 主函数
main() {
    print_section "Athena法律世界模型数据备份"
    log_info "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # 检查移动硬盘并创建备份目录（会设置全局变量BACKUP_DIR）
    check_external_drive

    # 导出变量供子函数使用
    export BACKUP_DIR

    # 备份Neo4j
    backup_neo4j

    # 备份Qdrant
    backup_qdrant

    # 备份PostgreSQL（可选）
    backup_postgres

    # 生成清单
    generate_manifest

    # 计算校验和
    calculate_checksums

    # 显示摘要
    show_summary

    log_success "备份流程全部完成！"
    echo ""
    echo "============================================================================"
}

# 执行备份
main "$@"
