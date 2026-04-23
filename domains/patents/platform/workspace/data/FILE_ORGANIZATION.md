# 专利工作区文件组织规范

## 📁 目录结构

```
patent-platform/workspace/
├── data/                           # 数据存储区
│   ├── raw/                       # 👉 原始文件存放位置
│   │   ├── disclosures/           # 技术交底书
│   │   │   ├── 202412001_智能机器人.md
│   │   │   ├── 202412002_医疗设备.docx
│   │   │   └── 202412003_软件算法.pdf
│   │   ├── drawings/              # 技术图纸
│   │   │   ├── 202412001_fig1.png
│   │   │   └── 202412001_fig2.jpg
│   │   └── references/            # 参考文档
│   │       ├── prior_art_001.pdf
│   │       └── technical_report.docx
│   │
│   ├── cases/                     # 示例案例和模板
│   │   ├── sample_disclosure.md   # 技术交底书模板
│   │   ├── sample_novelty.json    # 新颖性分析示例
│   │   └── templates/             # 各类模板
│   │       ├── invention_disclosure_template.md
│   │       └── technical_specification_template.docx
│   │
│   └── models/                    # AI模型文件
│       ├── novelty_model.pkl
│       ├── feature_extractor.pt
│       └── vector_index/
│
├── tasks/                          # 任务工作区
│   ├── PAT_20241205_001/          # 具体专利任务
│   │   ├── raw/                   # 原始文件副本
│   │   │   ├── disclosure.md      # 技术交底书
│   │   │   ├── drawings/          # 图纸文件
│   │   │   └── references/        # 参考资料
│   │   ├── novelty/               # 切片1：新颖性分析
│   │   │   ├── analysis_result.json
│   │   │   ├── prior_arts/        # 对比文件
│   │   │   └── feature_extraction.json
│   │   ├── creative/              # 切片2：创造性分析
│   │   ├── writing/               # 切片3：专利撰写
│   │   ├── check/                 # 切片4：形式审查
│   │   └── response/              # 切片5：答复审查意见
│   │
│   └── PAT_20241205_002/          # 另一个专利任务
│
├── src/                           # 源代码
│   ├── cli/                       # CLI工具
│   ├── models/                    # 分析模型
│   ├── api/                       # API服务
│   └── utils/                     # 工具函数
│
└── tests/                         # 测试用例
    ├── novelty/                   # 新颖性分析测试
    ├── creative/                  # 创造性分析测试
    └── cases/                     # 真实案例测试
```

## 📝 文件命名规范

### 1. 技术交底书命名
```
格式：{日期}_{序号}_{专利主题}.{扩展名}
示例：20241205_001_智能机器人控制系统.md
```

### 2. 图纸文件命名
```
格式：{日期}_{序号}_fig{编号}.{扩展名}
示例：20241205_001_fig1.png, 20241205_001_fig2.jpg
```

### 3. 任务ID命名
```
格式：PAT_{日期}_{时间}
示例：PAT_20241205_143022
```

## 🚀 快速开始指南

### 1. 准备原始文件
```bash
# 将技术交底书放入指定目录
cp your_disclosure.md patent-platform/workspace/data/raw/disclosures/

# 如果有图纸，放入图纸目录
cp drawing1.png patent-platform/workspace/data/raw/drawings/
```

### 2. 创建新任务
```bash
cd patent-platform/workspace
python3 src/cli/patent_cli.py init "专利标题" -d "专利描述"
```

### 3. 文件自动复制
系统会自动：
- 将技术交底书复制到 `tasks/TASK_ID/raw/disclosure.md`
- 创建对应的图纸目录
- 初始化各阶段的工作目录

### 4. 执行分析
```bash
# 执行新颖性分析
python3 src/cli/patent_cli.py novelty TASK_ID

# 查看结果
cat tasks/TASK_ID/novelty/analysis_result.json
```

## 💡 最佳实践

1. **原始文件管理**：
   - 原始文件统一放在 `data/raw/` 下
   - 使用日期和序号进行版本管理
   - 支持多种格式：.md, .docx, .pdf, .png, .jpg

2. **任务隔离**：
   - 每个专利任务独立目录
   - 原始文件自动复制到任务目录
   - 分析结果按阶段分类存储

3. **备份策略**：
   - `data/raw/` 作为原始文件备份
   - `tasks/` 作为工作副本
   - 定期备份重要的分析结果

4. **协作支持**：
   - 支持多用户同时处理不同任务
   - 清晰的文件锁定机制
   - 版本控制和变更追踪