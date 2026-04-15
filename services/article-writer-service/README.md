# Athena文章撰写服务

> **统一文章撰写模块** - 整合平台所有文章撰写能力，实现与OpenClaw的内容交接

---

## 📋 概述

Athena文章撰写服务是一个统一的文章撰写模块，整合了平台现有的所有文章撰写相关功能，并提供与OpenClaw自媒体运营系统的无缝内容交接。

### 核心特性

- ✅ 统一的文章撰写API
- ✅ 整合现有写作素材库
- ✅ 支持多种文章类型和风格
- ✅ Markdown + 配图的内容交接
- ✅ 直接对接OpenClaw自媒体运营文件夹

---

## 🏗️ 模块整合

### 整合的现有模块

| 原模块 | 路径 | 核心功能 | 整合方式 |
|--------|------|----------|----------|
| WritingMaterialsManager | `core/llm/writing_materials_manager.py` | 法律写作素材库管理 | 直接导入 |
| LawArticleParser | `core/nlp/law_article_parser.py` | 法律条文解析 | 直接导入 |
| ArticleGenerator | `core/judgment_vector_db/generation/article_generator.py` | 文章生成引擎 | 功能整合 |
| ContentCreator | `services/self-media-agent/.../content_creator.py` | 内容创作模块 | 迁移并增强 |
| EnhancedContentStyles | `services/self-media-agent/.../enhanced_content_styles.py` | 风格系统 | 直接导入 |

### 新增模块

| 模块 | 功能 |
|------|------|
| `ArticleWritingEngine` | 统一的文章撰写引擎 |
| `OpenClawHandover` | OpenClaw内容交接接口 |
| `ImageGenerator` | 配图生成协调器 |
| `QualityChecker` | 文章质量检查 |

---

## 📂 目录结构

```
services/article-writer-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI服务入口
│   ├── config.py               # 配置文件
│   │
│   ├── core/                   # 核心模块
│   │   ├── __init__.py
│   │   ├── writing_engine.py   # 统一文章撰写引擎
│   │   ├── materials_manager.py # 素材库管理（整合）
│   │   ├── style_manager.py    # 风格管理（整合）
│   │   └── quality_checker.py  # 质量检查
│   │
│   ├── openclaw/               # OpenClaw集成
│   │   ├── __init__.py
│   │   ├── handover.py         # 内容交接
│   │   └── config.py           # OpenClaw配置
│   │
│   ├── generators/             # 文章生成器
│   │   ├── __init__.py
│   │   ├── legal_article.py    # 法律文章生成器
│   │   ├── ip_article.py       # IP科普文章生成器
│   │   ├── industry_insight.py # 行业洞察生成器
│   │   └── casual_blog.py      # 轻松博客生成器
│   │
│   ├── api/                    # API路由
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── markdown.py         # Markdown处理
│       └── logger.py           # 日志工具
│
├── tests/
│   └── test_article_writer.py
│
└── README.md
```

---

## 🔄 OpenClaw内容交接

### 交接格式

```yaml
内容包结构:
  文章草稿/:
    微信公众号/:
      YYYY-MM-DD-文章标题.md
    小红书/:
      YYYY-MM-DD-文章标题.md
    知乎/:
      YYYY-MM-DD-文章标题.md

  配图素材/:
    专业风格/:
      文章标题-01.png
      文章标题-02.png
```

### 交接接口

```python
class OpenClawHandover:
    """OpenClaw内容交接"""

    async def handover_article(
        self,
        article: Article,
        platforms: List[str],
        images: List[Path] = None
    ) -> HandoverResult:
        """
        交接文章到OpenClaw

        Args:
            article: 文章对象
            platforms: 目标平台列表
            images: 配图列表

        Returns:
            交接结果
        """
```

---

## 🚀 快速开始

### 安装依赖

```bash
cd services/article-writer-service
pip install -r requirements.txt
```

### 启动服务

```bash
python -m app.main
```

### API示例

```bash
# 撰写IP科普文章
curl -X POST http://localhost:8031/api/v1/articles/write \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "专利申请流程",
    "article_type": "ip_education",
    "style": "shandong_humor",
    "platforms": ["微信公众号", "小红书"],
    "generate_images": true,
    "handover_to_openclaw": true
  }'
```

---

## 📝 文章类型支持

| 文章类型 | 说明 | 适用场景 |
|---------|------|----------|
| `ip_education` | IP知识科普 | 公众号、知乎 |
| `legal_analysis` | 法律案例分析 | 公众号、专业平台 |
| `industry_insight` | 行业洞察分析 | 公众号、知乎 |
| `patent_guide` | 专利实务指南 | 公众号、专业平台 |
| `casual_blog` | 轻松博客 | 小红书、微博 |

---

## 🎨 风格支持

| 风格 | 说明 | 特征 |
|------|------|------|
| `shandong_humor` | 山东幽默 | 幽默风趣、山东元素 |
| `professional` | 专业严谨 | 专业深度、逻辑清晰 |
| `cultural` | 文化传承 | 历史典故、文化引用 |
| `practical` | 实在实用 | 干货满满、解决问题 |

---

## 📊 配图支持

### 配图风格

- 专业风格：商务、科技感
- 法律风格：法槌、天平等
- 生活风格：温馨、亲和
- 科技风格：现代、前沿

### 配图生成

支持通过以下方式生成配图：
1. AI生成（集成AI图像生成）
2. 素材库匹配
3. 用户上传

---

## 🔧 配置

### OpenClaw路径配置

```python
# app/openclaw/config.py
OPENCLAW_MEDIA_PATH = Path("/Users/xujian/Documents/自媒体运营")

OPENCLAW_PATHS = {
    "articles": OPENCLAW_MEDIA_PATH / "文章草稿",
    "images": OPENCLAW_MEDIA_PATH / "配图素材",
    "templates": OPENCLAW_MEDIA_PATH / "模板库",
    "materials": OPENCLAW_MEDIA_PATH / "素材库"
}
```

---

## 🧪 测试

```bash
# 运行测试
pytest tests/ -v

# 测试覆盖率
pytest tests/ --cov=app --cov-report=html
```

---

## 📈 路线图

### Phase 1: 核心功能（当前）
- [x] 整合现有模块
- [ ] 实现统一撰写引擎
- [ ] 实现OpenClaw交接
- [ ] 基础API接口

### Phase 2: 增强功能
- [ ] AI配图生成
- [ ] SEO优化
- [ ] 批量生成
- [ ] 定时发布对接

### Phase 3: 高级功能
- [ ] 智能选题
- [ ] 热点追踪
- [ ] 数据分析对接
- [ ] A/B测试

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**版本**: v1.0.0
**最后更新**: 2026-02-03
**维护者**: 徐健 (xujian519@gmail.com)
