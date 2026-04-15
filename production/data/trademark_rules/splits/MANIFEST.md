# 商标审查指南切割清单

**生成时间**: 2025-12-26 22:22:03
**生成者**: 小诺·双鱼座 (Athena平台)
**源文件**: 商标审查审理指南.pdf
**切割份数**: 20

---

## 📊 文件信息

- **文件名**: 商标审查审理指南.pdf
- **文件大小**: 80.22 MB
- **切割策略**: 按页数均分
- **切割份数**: 20

---

## 📄 切割文件列表

| 序号 | 文件名 | 页码范围 | 页数 | 文件大小 |
|-----|--------|---------|-----|---------|
| 1 | 商标审查审理指南_part01_of_20.pdf | 第1-21页 | 21 | 1.87 MB |
| 2 | 商标审查审理指南_part02_of_20.pdf | 第22-42页 | 21 | 3.40 MB |
| 3 | 商标审查审理指南_part03_of_20.pdf | 第43-63页 | 21 | 3.27 MB |
| 4 | 商标审查审理指南_part04_of_20.pdf | 第64-84页 | 21 | 1.87 MB |
| 5 | 商标审查审理指南_part05_of_20.pdf | 第85-105页 | 21 | 5.48 MB |
| 6 | 商标审查审理指南_part06_of_20.pdf | 第106-126页 | 21 | 1.86 MB |
| 7 | 商标审查审理指南_part07_of_20.pdf | 第127-147页 | 21 | 1.95 MB |
| 8 | 商标审查审理指南_part08_of_20.pdf | 第148-168页 | 21 | 1.63 MB |
| 9 | 商标审查审理指南_part09_of_20.pdf | 第169-189页 | 21 | 1.61 MB |
| 10 | 商标审查审理指南_part10_of_20.pdf | 第190-210页 | 21 | 4.80 MB |
| 11 | 商标审查审理指南_part11_of_20.pdf | 第211-231页 | 21 | 6.82 MB |
| 12 | 商标审查审理指南_part12_of_20.pdf | 第232-252页 | 21 | 5.12 MB |
| 13 | 商标审查审理指南_part13_of_20.pdf | 第253-273页 | 21 | 7.53 MB |
| 14 | 商标审查审理指南_part14_of_20.pdf | 第274-294页 | 21 | 9.15 MB |
| 15 | 商标审查审理指南_part15_of_20.pdf | 第295-315页 | 21 | 10.35 MB |
| 16 | 商标审查审理指南_part16_of_20.pdf | 第316-336页 | 21 | 5.84 MB |
| 17 | 商标审查审理指南_part17_of_20.pdf | 第337-357页 | 21 | 4.84 MB |
| 18 | 商标审查审理指南_part18_of_20.pdf | 第358-378页 | 21 | 2.73 MB |
| 19 | 商标审查审理指南_part19_of_20.pdf | 第379-399页 | 21 | 2.66 MB |
| 20 | 商标审查审理指南_part20_of_20.pdf | 第400-422页 | 23 | 2.13 MB |

---

## 🚀 使用方法

### 方式1: 单独处理某个文件

```bash
python3 /Users/xujian/Athena工作平台/production/scripts/patent_guideline/full_laws_processor.py \
    --single-file /Users/xujian/Athena工作平台/production/data/trademark_rules/splits/商标审查审理指南_part01_of_20.pdf
```

### 方式2: 批量处理所有文件

```bash
cd /Users/xujian/Athena工作平台/production/data/trademark_rules/splits
bash process_all_splits.sh
```

### 方式3: 并发处理（高级）

```bash
# 使用GNU parallel并发处理
ls /Users/xujian/Athena工作平台/production/data/trademark_rules/splits/*.pdf | parallel -j 4 \
    'python3 /Users/xujian/Athena工作平台/production/scripts/patent_guideline/full_laws_processor.py --single-file {}'
```

---

## 📊 预期结果

处理完成后，您将拥有:

- **Qdrant集合**: trademark_laws
  - 向量数量: 预计10,000-20,000个
  - 向量维度: 1024维 (BGE-large-zh-v1.5)
  - 相似度检索: 支持

- **NebulaGraph空间**: trademark_rules
  - 节点数量: 预计5,000-10,000个
  - 关系数量: 预计3,000-6,000条
  - 节点类型: 6-8种
  - 关系类型: 6-8种

---

## ⚠️ 注意事项

1. **内存管理**
   - 每个文件约4-5MB，可以单独处理
   - 建议逐个处理，避免并发过多导致内存溢出

2. **时间估算**
   - 单个文件处理时间: 约10-20分钟
   - 总处理时间: 约3-6小时
   - 建议使用批量脚本夜间处理

3. **错误处理**
   - 如果某个文件处理失败，可以单独重试
   - 查看日志文件定位问题

4. **质量验证**
   - 处理完成后随机抽查验证
   - 检查向量检索质量
   - 检查图谱查询质量

---

**清单版本**: v1.0
**最后更新**: 2025-12-26 22:22:03
