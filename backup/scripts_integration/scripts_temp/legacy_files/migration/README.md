# 数据迁移脚本目录

## 📋 说明

本目录包含所有数据迁移相关的脚本，用于数据结构升级、数据迁移等操作。

## 📁 文件列表

### 批量迁移脚本
| 文件名 | 功能描述 | 使用方法 |
|--------|---------|----------|
| `batch_import_years.py` | 批量导入年度数据 | `python3 batch_import_years.py --year 2023` |
| `batch_migrate_patents.py` | 批量迁移专利数据 | `python3 batch_migrate_patents.py` |

### SQLite到Neo4j迁移
| 文件名 | 功能描述 | 使用方法 |
|--------|---------|----------|
| `migrate_sqlite_to_neo4j.py` | SQLite迁移到Neo4j | `python3 migrate_sqlite_to_neo4j.py` |
| `migrate_sqlite_to_neo4j_fixed.py` | 修复版SQLite迁移 | `python3 migrate_sqlite_to_neo4j_fixed.py` |

### 版本迁移脚本
| 文件名 | 功能描述 | 使用方法 |
|--------|---------|----------|
| `migrate_2015_batch.py` | 2015年数据批量迁移 | `python3 migrate_2015_batch.py` |
| `migrate_2015_to_2025.py` | 2015到2025升级迁移 | `python3 migrate_2015_to_2025.py` |

## 🚀 使用指南

### 执行迁移前检查
```bash
# 1. 备份数据
python3 ../database/patent_db_backup.sh

# 2. 检查源数据
ls -la /path/to/source/data
```

### 执行迁移
```bash
# 单个迁移
python3 batch_import_years.py --year 2023 --source /data/2023/

# 批量迁移
python3 batch_migrate_patents.py --all
```

## ⚠️ 注意事项

1. **备份重要性**: 执行迁移前务必备份数据
2. **测试环境**: 先在测试环境验证迁移脚本
3. **监控进度**: 大数据量迁移需要监控进度
4. **回滚计划**: 准备回滚方案以防万一

## 📊 迁移状态

- [ ] 待迁移
- [x] 已迁移
- [!] 需要注意

---
*最后更新: 2025-12-11*