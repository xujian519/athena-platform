# 测试脚本目录

## 📋 说明

本目录包含所有测试相关的脚本，用于验证系统各模块的功能。

## 📁 文件列表

| 文件名 | 功能描述 | 使用方法 |
|--------|---------|----------|
| `test_enhanced_perception.py` | 测试增强感知服务 | `python3 test_enhanced_perception.py` |
| `test_knowledge_memory_integration.py` | 测试知识记忆集成 | `python3 test_knowledge_memory_integration.py` |
| `test_perception_service.py` | 测试感知服务 | `python3 test_perception_service.py` |
| `test_vector_dbs.py` | 测试向量数据库 | `python3 test_vector_dbs.py` |

## 🚀 使用指南

### 运行所有测试
```bash
# 运行单个测试
python3 test_enhanced_perception.py

# 批量运行测试
for test in test_*.py; do
    echo "运行 $test..."
    python3 $test
done
```

### 测试环境要求
- Python 3.7+
- 相关依赖已安装
- 数据库服务正常运行

## 📝 注意事项

- 运行测试前请确保相关服务已启动
- 部分测试可能需要测试数据
- 测试结果会输出到控制台

---
*最后更新: 2025-12-11*