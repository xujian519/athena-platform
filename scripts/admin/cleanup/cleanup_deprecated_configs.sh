#!/bin/bash
# 清理废弃配置文件脚本

set -e

DEPRECATED_DIR="config/deprecated_configs/20260421_stage2"
mkdir -p "$DEPRECATED_DIR"

echo "🧹 开始清理废弃配置文件..."

# 移动废弃的JSON配置文件
DEPRECATED_JSON=(
  "config/local_search_engine.json"
  "config/local_model_registry.json"
  "config/system_config.json"
  "config/optimized.json"
  "config/cache_optimized.json"
  "config/multi_agent_integration.json"
  "config/xiaonuo_model_priority_config.json"
  "config/legal_clauses_sharding.json"
  "config/memory_system_config.json"
  "config/integration_test_report.json"
  "config/hybrid_crawler_config.json"
  "config/task_management.json"
  "config/model_pointers.json"
  "config/dimension_standardization.json"
  "config/multimodal_config.json"
  "config/vector_database_optimized.json"
  "config/api_gateway_crawler_config.json"
  "config/platform_crawler_config.json"
  "config/bge_m3_modelscope.json"
  "config/performance.json"
  "config/intelligence_system_update.json"
  "config/deployment/optimized_cache_config.json"
  "config/database_locations.json"
  "config/athena_mcp_config.json"
  "config/qdrant_optimized.json"
  "config/perception/enhanced_patent_config.json"
  "config/multimodal_config_original.json"
  "config/identity_integration.json"
  "config/storage_optimization.json"
  "config/qwen_config.json"
  "config/kg_visualization.json"
  "config/scraping_config.json"
)

for file in "${DEPRECATED_JSON[@]}"; do
  if [ -f "$file" ]; then
    mv "$file" "$DEPRECATED_DIR/"
    echo "✅ 已移动: $file"
  fi
done

# 移动废弃的Python配置文件
DEPRECATED_PY=(
  "config/configure_gemini_llm.py"
  "config/vector_config.py"
  "config/bge_m3_mps_optimized.py"
  "config/configure_zhipu_llm.py"
  "config/config_manager.py"
  "config/domestic_llm_integration.py"
  "config/bge_model_config.py"
  "config/update_local_neo4j.py"
)

for file in "${DEPRECATED_PY[@]}"; do
  if [ -f "$file" ]; then
    mv "$file" "$DEPRECATED_DIR/"
    echo "✅ 已移动: $file"
  fi
done

echo "🎉 废弃配置清理完成！"
echo "📊 统计："
echo "   - 移动到: $DEPRECATED_DIR"
echo "   - 移动的文件数: $(ls -1 "$DEPRECATED_DIR" | wc -l)"
