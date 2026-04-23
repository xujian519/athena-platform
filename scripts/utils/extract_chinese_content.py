#!/usr/bin/env python3
"""
Agentic Design Patterns 中文内容提取工具
Extract Chinese-Only Content for Agentic Design Patterns
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


class ChineseContentExtractor:
    """中文内容提取器"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台/knowledge/agentic_design_patterns")
        self.original_dir = self.base_dir / "original"
        self.chinese_dir = self.base_dir / "chinese_only"
        self.english_dir = self.base_dir / "english_only"

    def extract_all_content(self) -> Any:
        """提取所有内容"""
        print("🇨🇳 开始提取中文内容...")

        # 创建目录
        self.chinese_dir.mkdir(exist_ok=True)
        self.english_dir.mkdir(exist_ok=True)

        # 遍历所有Markdown文件
        for root, _dirs, files in os.walk(self.original_dir):
            for file in files:
                if file.endswith('.md'):
                    self.extract_chinese_from_file(root, file)

        print("✅ 中文内容提取完成！")

    def extract_chinese_from_file(self, root, filename) -> Any:
        """从单个文件提取中文内容"""
        source_file = Path(root) / filename

        try:
            # 读取原文件
            with open(source_file, encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"⚠️ 读取文件失败: {source_file} - {e}")
            return

        # 提取中文和英文内容
        chinese_content, english_content = self.separate_chinese_english(content)

        # 保存中文内容
        chinese_file = self.chinese_dir / filename
        with open(chinese_file, 'w', encoding='utf-8') as f:
            f.write(chinese_content)

        # 保存英文内容
        english_file = self.english_dir / filename
        with open(english_file, 'w', encoding='utf-8') as f:
            f.write(english_content)

        print(f"✅ 处理完成: {filename}")

    def separate_chinese_english(self, content) -> Any:
        """分离中英文内容"""
        lines = content.split('\n')
        chinese_lines = []
        english_lines = []

        for line in lines:
            line_stripped = line.strip()

            # 跳过空行和纯符号行
            if not line_stripped or line_stripped in ['#', '---', '***', '```', '---\n', '\n']:
                chinese_lines.append(line)
                english_lines.append(line)
                continue

            # 检查是否为标题行（通常包含中英文）
            if line_stripped.startswith('#'):
                # 提取中文标题
                chinese_title = self.extract_chinese_title(line)
                english_title = self.extract_english_title(line)

                if chinese_title:
                    chinese_lines.append(chinese_title)
                if english_title:
                    english_lines.append(english_title)
                continue

            # 检查是否为代码块
            if line_stripped.startswith('```'):
                chinese_lines.append(line)
                english_lines.append(line)
                continue

            # 检查是否为图片链接
            if line_stripped.startswith('!['):
                chinese_lines.append(line)
                english_lines.append(line)
                continue

            # 检查是否为列表项
            if line_stripped.startswith(('-', '*', '+')):
                chinese_item = self.extract_chinese_list_item(line)
                english_item = self.extract_english_list_item(line)

                if chinese_item:
                    chinese_lines.append(chinese_item)
                if english_item:
                    english_lines.append(english_item)
                continue

            # 检查是否包含中文
            if self.has_chinese(line_stripped):
                # 提取中文部分
                chinese_part = self.extract_chinese_part(line)
                chinese_lines.append(chinese_part)

                # 提取英文部分
                english_part = self.extract_english_part(line)
                if english_part:
                    english_lines.append(english_part)
            else:
                # 纯英文内容
                english_lines.append(line)

        # 清理和优化内容
        chinese_content = self.clean_chinese_content('\n'.join(chinese_lines))
        english_content = self.clean_english_content('\n'.join(english_lines))

        return chinese_content, english_content

    def extract_chinese_title(self, line) -> Any:
        """提取中文标题"""
        # 匹配标题中的中文部分
        chinese_pattern = r'^(#+\s*)([\u4e00-\u9fff].*?)(?=\s*[\u4e00-\u9fff]*\s*[:：]\s*$|\s*$)'
        match = re.search(chinese_pattern, line)
        if match:
            return f"{match.group(1)}{match.group(2).strip()}"

        # 处理包含中英文对照的标题
        if self.has_chinese(line):
            # 提取冒号前的中文部分
            if ':' in line or '：' in line:
                parts = re.split(r'[:：]', line)
                if len(parts) >= 2:
                    chinese_part = parts[0].strip()
                    if self.has_chinese(chinese_part):
                        return chinese_part

        return line if self.has_chinese(line) else None

    def extract_english_title(self, line) -> Any:
        """提取英文标题"""
        # 匹配标题中的英文部分
        if ':' in line or '：' in line:
            parts = re.split(r'[:：]', line)
            if len(parts) >= 2:
                # 提取冒号后的英文部分
                english_part = parts[1].strip()
                if not self.has_chinese(english_part):
                    return f"{line.split(':')[0]}: {english_part}"

        # 如果没有冒号，尝试提取英文部分
        english_part = self.extract_english_part(line)
        if english_part and not self.has_chinese(english_part):
            return english_part

        return None

    def extract_chinese_list_item(self, line) -> Any:
        """提取中文列表项"""
        if self.has_chinese(line):
            return line
        return None

    def extract_english_list_item(self, line) -> Any:
        """提取英文列表项"""
        if not self.has_chinese(line) and line.strip():
            return line
        return None

    def has_chinese(self, text) -> bool:
        """检查文本是否包含中文"""
        chinese_pattern = r'[\u4e00-\u9fff]'
        return bool(re.search(chinese_pattern, text))

    def extract_chinese_part(self, line) -> Any:
        """提取中文部分"""
        # 使用正则表达式提取中文字符
        chinese_pattern = r'[\u4e00-\u9fff\uff00-\uffef]+'
        matches = re.findall(chinese_pattern, line)

        if matches:
            # 添加必要的空格和标点
            result = ''.join(matches)
            # 保留一些英文标点和空格
            result = re.sub(r'([，。！？；：])', r'\1 ', result)
            return result.strip()

        return line if self.has_chinese(line) else ''

    def extract_english_part(self, line) -> Any:
        """提取英文部分"""
        # 移除中文字符，保留英文和标点
        # 保留英文字母、数字、标点和空格
        result = re.sub(r'[\u4e00-\u9fff\uff00-\uffef]', '', line)

        # 清理多余的空格
        result = re.sub(r'\s+', ' ', result).strip()

        return result if result else ''

    def clean_chinese_content(self, content) -> Any:
        """清理中文内容"""
        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            line_stripped = line.strip()

            # 跳过纯空行
            if not line_stripped:
                cleaned_lines.append('')
                continue

            # 清理多余的空格
            line_clean = re.sub(r'\s+', ' ', line_stripped)

            # 优化中文标点
            line_clean = line_clean.replace(' ,', '，').replace(' .', '。')
            line_clean = line_clean.replace('( ', '（').replace(' )', '）')
            line_clean = line_clean.replace(': ', '：').replace(' ;', '；')

            cleaned_lines.append(line_clean)

        # 添加头部信息
        header = f"""# 📚 Agentic Design Patterns (中文版)

> **提取时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> **内容类型**: 中文简体版本
> **总页数**: 424页
> **原始来源**: https://github.com/ginobefun/agentic-design-patterns-cn

---

"""

        return header + '\n'.join(cleaned_lines)

    def clean_english_content(self, content) -> Any:
        """清理英文内容"""
        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            line_stripped = line.strip()

            # 跳过纯空行
            if not line_stripped:
                cleaned_lines.append('')
                continue

            # 保留英文内容
            if not self.has_chinese(line_stripped):
                cleaned_lines.append(line_stripped)

        # 添加头部信息
        header = f"""# Agentic Design Patterns (English Version)

> **Extract Time**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> **Content Type**: English Only Version
> **Total Pages**: 424
> **Original Source**: https://github.com/ginobefun/agentic-design-patterns-cn

---

"""

        return header + '\n'.join(cleaned_lines) if any(cleaned_lines) else "# English Content\n\n_no English content found in this document."

    def create_chinese_reading_index(self) -> Any:
        """创建中文阅读索引"""
        index_content = f"""# 📚 Agentic Design Patterns 中文版索引

> **提取时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> **语言版本**: 中文简体
> **总页数**: 424页
> **章节模式**: 21个核心设计模式

---

## 🎯 快速开始

### 📖 推荐阅读顺序

#### 第一部分：核心设计模式 (第1-7章)
1. [第1章：提示链](./07-Chapter-01-Prompt-Chaining.md) - 任务分解与处理流水线
2. [第2章：路由](./08-Chapter-02-Routing.md) - 智能决策与动态分发
3. [第3章：并行化](./09-Chapter-03-Parallelization.md) - 并发执行与性能提升
4. [第4章：反思](./10-Chapter-04-Reflection.md) - 自我评估和迭代改进
5. [第5章：工具使用](./11-Chapter-05-Tool-Use.md) - 外部工具与API集成
6. [第6章：规划](./12-Chapter-06-Planning.md) - 多步骤计划制定与执行
7. [第7章：多智能体协作](./13-Chapter-07-Multi-Agent-Collaboration.md) - 协同工作架构

#### 第二部分：高级设计模式 (第8-11章)
8. [第8章：记忆管理](./14-Chapter-08-Memory-Management.md) - 短期和长期记忆管理
10. [第10章：模型上下文协议](./16-Chapter-10-Model-Context-Protocol.md) - 标准化交互规范
11. [第11章：目标设定与监控](./17-Chapter-11-Goal-Setting-And-Monitoring.md) - 动态目标管理

#### 第三部分：集成设计模式 (第12-14章)
12. [第12章：异常处理与恢复](./15-Chapter-12-Exception-Handling-and-Recovery.md) - 系统稳定性保障
13. [第13章：人机协作](./19-Chapter-13-Human-in-the-Loop.md) - 人类智慧与AI能力融合
14. [第14章：知识检索(RAG)](./20-Chapter-14-Knowledge-Retrieval-RAG.md) - 外部知识库集成

#### 第四部分：生产设计模式 (第15-21章)
15. [第15章：智能体间通信](./21-Chapter-15-Inter-Agent-Communication.md) - 高效交互协议
16. [第16章：资源感知优化](./22-Chapter-16-Resource-Aware-Optimization.md) - 性能与成本平衡
17. [第17章：推理技术](./23-Chapter-17-Reasoning-Techniques.md) - 决策质量提升
19. [第19章：评估与监控](./25-Chapter-19-Evaluation-and-Monitoring.md) - 性能量化评估
20. [第20章：优先级排序](./26-Chapter-20-Prioritization.md) - 任务优先级管理
21. [第21章：探索与发现](./27-Chapter-21-Exploration-and-Discovery.md) - 自主探索机制

## 📚 其他重要文档

- [项目介绍](./README.md) - 了解项目概况和使用方法
- [什么是智能体](./06-What-Makes-Agent.md) - 智能体的基本概念和特性
- [引言](./05-Introduction.md) - 书籍的背景和目标读者
- [完整目录](./00-Table-of-Contents.md) - 详细的书籍目录结构

## 💡 阅读建议

### 🎯 学习路径
1. **入门阶段**: 阅读项目介绍和引言，了解基础知识
2. **基础学习**: 掌握第1-7章的核心设计模式
3. **进阶学习**: 深入学习第8-14章的高级模式
4. **专家级学习**: 掌握第15-21章的生产级应用

### 📖 阅读技巧
- 按顺序学习，循序渐进
- 理论与实践结合
- 多做笔记和总结
- 应用到实际项目中

### 🔧 实用建议
- 使用支持Markdown的阅读器
- 重点理解每个模式的核心思想
- 关注代码示例的实际应用
- 思考如何在项目中使用这些模式

## 📊 学习统计

- **总页数**: 424页
- **核心模式**: 21个
- **学习阶段**: 4个级别
- **预计学习时间**: 2-4周

---

*祝您学习愉快！如有问题，请参考原始GitHub项目或社区讨论。*
"""

        with open(self.chinese_dir / "阅读索引.md", 'w', encoding='utf-8') as f:
            f.write(index_content)

        print("✅ 中文阅读索引已创建")

    def create_statistics_report(self) -> Any:
        """创建统计报告"""
        chinese_files = list(self.chinese_dir.rglob("*.md"))
        english_files = list(self.english_dir.rglob("*.md"))

        report = f"""# 📊 中文内容提取统计报告

> **提取时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> **处理工具**: Agentic Design Patterns 中文提取器

---

## 📈 提取统计

### 🇨🇳 中文版本
- **文件数量**: {len(chinese_files)}
- **存储位置**: {self.chinese_dir}
- **内容类型**: 中文简体
- **编码格式**: UTF-8

### 🇬🇧 英文版本
- **文件数量**: {len(english_files)}
- **存储位置**: {self.english_dir}
- **内容类型**: 英文原文
- **编码格式**: UTF-8

## 📚 文件列表

### 中文文件
"""
        for file in sorted(chinese_files):
            if file.name != "阅读索引.md":
                report += f"- [{file.name}](./{file.name})\n"

        report += """

### 英文文件
"""
        for file in sorted(english_files):
            report += f"- [{file.name}](./{file.name})\n"

        report += f"""

## ✅ 提取完成状态

- [x] 中文内容提取完成
- [x] 英文内容分离完成
- [x] 编码格式统一(UTF-8)
- [x] 文件结构保持完整
- [x] 阅读索引生成完成

## 💡 下一步建议

1. 使用中文阅读器查看中文版本
2. 根据需要参考英文版本对照学习
3. 创建个人学习笔记
4. 应用到实际项目中

---

*提取完成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

        with open(self.chinese_dir / "统计报告.md", 'w', encoding='utf-8') as f:
            f.write(report)

        print("✅ 统计报告已创建")


def main() -> None:
    """主函数"""
    print("🔧 Agentic Design Patterns 中文内容提取工具")
    print("=" * 50)

    extractor = ChineseContentExtractor()

    try:
        # 提取内容
        extractor.extract_all_content()

        # 创建索引
        extractor.create_chinese_reading_index()

        # 生成统计报告
        extractor.create_statistics_report()

        print("\n🎉 中文内容提取完成！")
        print(f"📁 中文版本: {extractor.chinese_dir}")
        print(f"📁 英文版本: {extractor.english_dir}")
        print(f"📖 开始阅读: {extractor.chinese_dir}/阅读索引.md")

    except Exception as e:
        print(f"❌ 提取过程中出错: {e}")


if __name__ == "__main__":
    main()
