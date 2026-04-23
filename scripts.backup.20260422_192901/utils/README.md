# 工具脚本目录

## 📋 说明

本目录包含各种工具类脚本，提供系统维护、配置、分析等辅助功能。

## 📁 文件列表

### 配置管理
| 文件名 | 功能描述 | 使用方法 |
|--------|---------|----------|
| `configure_api_keys.py` | 配置API密钥 | `python3 configure_api_keys.py` |
| `quick_config_check.sh` | 快速配置检查 | `bash quick_config_check.sh` |
| `quick_status_check.sh` | 快速状态检查 | `bash quick_status_check.sh` |

### 数据库工具
| 文件名 | 功能描述 | 使用方法 |
|--------|---------|----------|
| `create_legal_kg_sqlite.py` | 创建法律知识图谱SQLite | `python3 create_legal_kg_sqlite.py` |
| `networkx_sqlite_import.py` | NetworkX数据导入SQLite | `python3 networkx_sqlite_import.py` |
| `sqlite_knowledge_graph_manager.py` | SQLite知识图谱管理器 | `python3 sqlite_knowledge_graph_manager.py` |

### 文件组织
| 文件名 | 功能描述 | 使用方法 |
|--------|---------|----------|
| `organize_data_by_techstack.py` | 按技术栈组织数据 | `python3 organize_data_by_techstack.py` |
| `organize_root_directory.py` | 组织根目录 | `python3 organize_root_directory.py` |
| `organize_scripts.py` | 组织脚本文件 | `python3 organize_scripts.py` |
| `maintain_project_structure.py` | 维护项目结构 | `python3 maintain_project_structure.py` |
| `xiaonuo_file_organizer.py` | 小诺文件整理器 | `python3 xiaonuo_file_organizer.py` |

### 文档工具
| 文件名 | 功能描述 | 使用方法 |
|--------|---------|----------|
| `documentation_standardizer.py` | 文档标准化工具 | `python3 documentation_standardizer.py` |

### 查看工具
| 文件名 | 功能描述 | 使用方法 |
|--------|---------|----------|
| `tool_finder.py` | 工具查找器 | `python3 tool_finder.py` |
| `view_knowledge_graphs.py` | 查看知识图谱 | `python3 view_knowledge_graphs.py` |

### 系统工具
| 文件名 | 功能描述 | 使用方法 |
|--------|---------|----------|
| `cli.py` | 命令行工具 | `python3 cli.py` |
| `initialize.sh` | 初始化脚本 | `bash initialize.sh` |
| `quick_backup.sh` | 快速备份 | `bash quick_backup.sh` |

### 统计文件
| 文件名 | 功能描述 | 格式 |
|--------|---------|------|
| `scripts_stats.json` | 脚本统计信息 | JSON |

## 🚀 使用指南

### 常用工具快速访问
```bash
# 配置API
python3 configure_api_keys.py

# 检查系统状态
bash quick_status_check.sh

# 查找工具
python3 tool_finder.py --keyword "导入"

# 整理项目
python3 maintain_project_structure.py
```

### 开发工具使用
```bash
# 标准化文档
python3 documentation_standardizer.py --path ./docs

# 知识图谱管理
python3 sqlite_knowledge_graph_manager.py --action backup
```

## 📝 注意事项

1. 部分脚本需要管理员权限运行
2. 使用备份工具前确保有足够的存储空间
3. 文档工具会修改文件，请先备份
4. CLI工具支持 `--help` 查看详细使用说明

---
*最后更新: 2025-12-11*