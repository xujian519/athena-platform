#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化中文Markdown格式阅读体验
Optimize Chinese Markdown Reading Experience
"""

import os
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import re
import shutil
from pathlib import Path
from datetime import datetime

class ChineseMarkdownOptimizer:
    """中文Markdown优化器"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台/knowledge/agentic_design_patterns")
        self.chinese_dir = self.base_dir / "chinese_only"
        self.original_images_dir = self.base_dir / "original/images"
        self.chinese_images_dir = self.chinese_dir / "images"

    def optimize_all_markdown_files(self) -> Any:
        """优化所有Markdown文件"""
        print("🔧 开始优化中文Markdown格式...")

        # 创建images目录
        self.chinese_images_dir.mkdir(exist_ok=True)

        # 复制图片到中文目录
        self.copy_images()

        # 优化所有Markdown文件
        markdown_files = list(self.chinese_dir.rglob("*.md"))
        for md_file in markdown_files:
            if md_file.name not in ["阅读索引.md", "统计报告.md"]:
                self.optimize_single_markdown_file(md_file)

        print("✅ 所有Markdown文件优化完成！")

    def copy_images(self) -> Any:
        """复制图片到中文目录"""
        print("🖼️ 复制图片资源...")

        if self.original_images_dir.exists():
            # 复制整个images目录
            if self.chinese_images_dir.exists():
                shutil.rmtree(self.chinese_images_dir)
            shutil.copytree(self.original_images_dir, self.chinese_images_dir)
            print(f"✅ 已复制图片到: {self.chinese_images_dir}")

            # 列出复制的图片
            copied_images = list(self.chinese_images_dir.rglob("*"))
            print(f"📊 复制了 {len([f for f in copied_images if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.svg']])} 个图片文件")
        else:
            print("⚠️ 原始图片目录不存在，将创建空的images目录")

    def optimize_single_markdown_file(self, md_file) -> Any:
        """优化单个Markdown文件"""
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"⚠️ 读取文件失败: {md_file} - {e}")
            return

        # 优化内容
        optimized_content = self.optimize_markdown_content(content, md_file)

        # 写回文件
        try:
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(optimized_content)
            print(f"✅ 优化完成: {md_file.name}")
        except Exception as e:
            print(f"⚠️ 写入文件失败: {md_file} - {e}")

    def optimize_markdown_content(self, content, md_file) -> Any:
        """优化Markdown内容"""
        lines = content.split('\n')
        optimized_lines = []

        for line in lines:
            optimized_line = self.optimize_single_line(line)
            optimized_lines.append(optimized_line)

        # 清理和优化整体结构
        optimized_content = '\n'.join(optimized_lines)
        optimized_content = self.clean_markdown_structure(optimized_content, md_file)

        return optimized_content

    def optimize_single_line(self, line) -> Any:
        """优化单行内容"""
        # 修复图片链接
        line = self.fix_image_links(line)

        # 优化中文格式
        line = self.optimize_chinese_formatting(line)

        # 优化代码块
        line = self.optimize_code_blocks(line)

        # 优化表格
        line = self.optimize_tables(line)

        return line

    def fix_image_links(self, line) -> Any:
        """修复图片链接"""
        # 匹配Markdown图片链接
        image_pattern = r'!\[(.*?)\]\(([^)]+)\)'

        def replace_image_link(match) -> Any:
            alt_text = match.group(1)
            image_path = match.group(2).strip()

            # 如果是绝对路径(/images/开头)，转换为相对路径
            if image_path.startswith('/images/'):
                image_path = image_path[1:]  # 移除开头的 /

            # 确保图片路径正确
            if not image_path.startswith('images/'):
                image_path = f'images/{image_path.split("/")[-1]}'

            return f'![{alt_text}]({image_path})'

        return re.sub(image_pattern, replace_image_link, line)

    def optimize_chinese_formatting(self, line) -> Any:
        """优化中文格式"""
        # 添加中文和英文之间的空格
        line = re.sub(r'([\u4e00-\u9fff])([a-z_a-Z0-9])', r'\1 \2', line)
        line = re.sub(r'([a-z_a-Z0-9])([\u4e00-\u9fff])', r'\1 \2', line)

        # 优化中文标点
        line = line.replace(' ,', '，').replace(' .', '。')
        line = line.replace('( ', '（').replace(' )', '）')
        line = line.replace(': ', '：').replace(' ;', '；')
        line = line.replace(' !', '！').replace(' ?', '？')

        # 移除多余的空格
        line = re.sub(r'\s+', ' ', line)

        return line

    def optimize_code_blocks(self, line) -> Any:
        """优化代码块"""
        # 确保代码块前后有空行
        if line.strip().startswith('```'):
            return line.strip()
        return line

    def optimize_tables(self, line) -> Any:
        """优化表格格式"""
        if '|' in line and '-' in line:
            # 可能是表格行，保持原样
            return line
        return line

    def clean_markdown_structure(self, content, md_file) -> Any:
        """清理Markdown结构"""
        lines = content.split('\n')
        cleaned_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # 清理空行
            if line.strip() == '':
                cleaned_lines.append('')
            else:
                # 确保标题前有空行
                if line.startswith('#') and i > 0 and lines[i-1].strip() != '':
                    cleaned_lines.append('')
                    cleaned_lines.append(line)
                else:
                    cleaned_lines.append(line)
            i += 1

        # 移除连续的多个空行
        result_lines = []
        prev_empty = False
        for line in cleaned_lines:
            if line.strip() == '':
                if not prev_empty:
                    result_lines.append('')
                prev_empty = True
            else:
                result_lines.append(line)
                prev_empty = False

        return '\n'.join(result_lines)

    def create_toc_file(self) -> Any:
        """创建目录文件"""
        print("📋 创建目录文件...")

        markdown_files = list(self.chinese_dir.rglob("*.md"))
        markdown_files = [f for f in markdown_files if f.name not in ["阅读索引.md", "统计报告.md", "index.html"]]

        toc_content = f"""# 📚 智能体设计模式 - 目录索引

> **更新时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> **语言版本**: 中文简体
> **格式**: Markdown优化版

---

## 📖 阅读顺序建议

### 🌟 基础入门（第1-7章）

"""

        # 添加基础章节
        basic_chapters = [1, 2, 3, 4, 5, 6, 7]
        for num in basic_chapters:
            file_found = None
            for f in markdown_files:
                if f"Chapter-{num:02d}" in f.name or f"Chapter{num}" in f.name:
                    file_found = f
                    break

            if file_found:
                chapter_title = self.get_chapter_title(file_found)
                toc_content += f"- [第{num}章：{chapter_title}]({file_found.name})\n"

        toc_content += """

### 🚀 进阶学习（第8-14章）

"""

        # 添加进阶章节
        advanced_chapters = [8, 10, 11, 12, 13, 14]
        for num in advanced_chapters:
            file_found = None
            for f in markdown_files:
                if f"Chapter-{num:02d}" in f.name or f"Chapter{num}" in f.name:
                    file_found = f
                    break

            if file_found:
                chapter_title = self.get_chapter_title(file_found)
                toc_content += f"- [第{num}章：{chapter_title}]({file_found.name})\n"

        toc_content += """

### 🏭 专家实践（第15-21章）

"""

        # 添加专家章节
        expert_chapters = [15, 16, 17, 19, 20, 21]
        for num in expert_chapters:
            file_found = None
            for f in markdown_files:
                if f"Chapter-{num:02d}" in f.name or f"Chapter{num}" in f.name:
                    file_found = f
                    break

            if file_found:
                chapter_title = self.get_chapter_title(file_found)
                toc_content += f"- [第{num}章：{chapter_title}]({file_found.name})\n"

        toc_content += """

## 📚 其他文档

- [项目介绍](README.md) - 了解项目概况
- [什么是智能体](06-What-Makes-Agent.md) - 智能体概念
- [引言](05-Introduction.md) - 书籍介绍
- [完整目录](00-Table-of-Contents.md) - 详细目录

## 💡 阅读建议

1. **按顺序学习**：建议按照章节顺序从基础到高级
2. **理论结合实践**：阅读时结合实际项目思考应用
3. **做好笔记**：记录重要概念和实现方法
4. **多次回顾**：关键内容需要反复学习

## 🖼️ 图片说明

本书中的所有图片都已优化并存储在 `images/` 目录中：
- 支持Markdown阅读器正常显示
- 图片路径已修正为相对路径
- 保持了原有的高清晰度

---

*使用Typora、Mark Text等专业Markdown阅读器可获得最佳阅读效果*
"""

        with open(self.chinese_dir / "目录.md", 'w', encoding='utf-8') as f:
            f.write(toc_content)

        print("✅ 目录文件已创建")

    def get_chapter_title(self, file_path) -> Any | None:
        """从文件中提取章节标题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找第一个章节标题
            lines = content.split('\n')
            for line in lines:
                if line.strip().startswith('# Chapter') or line.strip().startswith('# 第'):
                    # 提取中文标题
                    chinese_match = re.search(r'第[\d]+章[：:]?\s*(.*)', line)
                    if chinese_match:
                        title = chinese_match.group(1).strip()
                        # 清理HTML标签
                        title = re.sub(r'<[^>]+>', '', title)
                        return title

            return f"Chapter {file_path.stem}"
        except:
            return file_path.stem

    def create_reading_recommendations(self) -> Any:
        """创建阅读建议文件"""
        recommendations = f"""# 📖 Markdown阅读器推荐与设置指南

> **更新时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> **适用版本**: 中文优化版Markdown

---

## 🏆 推荐的Markdown阅读器

### 1. Typora（强烈推荐）
- **优势**: 最专业的Markdown编辑器
- **特色**: 实时预览、主题丰富、图片管理优秀
- **中文支持**: 完美支持中文显示和编辑
- **价格**: 付费软件（$15），值得投资

### 2. Mark Text
- **优势**: 开源免费、界面简洁
- **特色**: 所见即所得、插件支持
- **中文支持**: 良好的中文支持
- **价格**: 免费

### 3. VS Code + Markdown Preview
- **优势**: 强大的编辑功能、插件丰富
- **特色**: 代码高亮、Git集成
- **中文支持**: 需要安装中文字体包
- **价格**: 免费

### 4. Obsidian
- **优势**: 知识管理、双向链接
- **特色**: 笔记管理、图表支持
- **中文支持**: 良好
- **价格**: 个人使用免费

## ⚙️ 最佳设置建议

### Typora设置
1. **字体设置**：
   - 中文：微软雅黑或苹方
   - 英文：Consolas或Monaco
   - 字号：16-18px

2. **主题设置**：
   - 推荐主题：Picnic、Material、Newsprint
   - 启用夜间模式保护眼睛

3. **图片设置**：
   - 图片根目录：`./images`
   - 自动上传：关闭（使用本地图片）

### VS Code设置
```json
// settings.json
{{
    "markdown.preview.font_size": 16,
    "markdown.preview.font_family": "'Microsoft YaHei', 'PingFang SC', sans-serif",
    "markdown.line_height": 1.8,
    "markdown.preview.breaks": true
}}
```

## 🖼️ 图片显示问题解决

### 问题诊断
如果图片不显示，请检查：

1. **图片路径**：
   - 确保图片在 `images/` 目录下
   - 检查相对路径是否正确

2. **文件权限**：
   - 确保图片文件可读
   - 检查目录权限

3. **阅读器设置**：
   - Typora：偏好设置 → 图像
   - VS Code：设置中的markdown相关选项

### 手动修复
如果某个文件中的图片仍不显示：

1. 检查图片链接格式：`![描述](images/图片名.png)`
2. 确认图片文件存在
3. 尝试使用绝对路径测试

## 📚 阅读技巧

### 高效阅读方法
1. **使用目录导航**：快速跳转到需要的章节
2. **书签功能**：标记重要内容位置
3. **搜索功能**：查找特定概念
4. **分屏阅读**：一边看理论一边看代码

### 笔记建议
- 使用Markdown语法做笔记
- 保留重要代码片段
- 记录实践心得
- 建立知识链接

## 🔧 故障排除

### 常见问题
1. **中文乱码**：
   - 确保文件编码为UTF-8
   - 检查编辑器字体设置

2. **图片不显示**：
   - 检查图片路径
   - 确认图片格式支持
   - 尝试其他阅读器

3. **格式错乱**：
   - 重新生成优化文件
   - 检查Markdown语法

### 获取帮助
如果遇到问题：
1. 查看本指南的故障排除部分
2. 尝试其他推荐阅读器
3. 检查文件完整性

---

**祝你阅读愉快！如有问题，请参考上述解决方案。**
"""

        with open(self.chinese_dir / "阅读器设置指南.md", 'w', encoding='utf-8') as f:
            f.write(recommendations)

        print("✅ 阅读器设置指南已创建")


def main() -> None:
    """主函数"""
    print("🔧 中文Markdown格式优化工具")
    print("=" * 50)

    optimizer = ChineseMarkdownOptimizer()

    try:
        # 优化Markdown文件
        optimizer.optimize_all_markdown_files()

        # 创建目录文件
        optimizer.create_toc_file()

        # 创建阅读器设置指南
        optimizer.create_reading_recommendations()

        print("\n🎉 优化完成！")
        print(f"📁 优化位置: {optimizer.chinese_dir}")
        print(f"🖼️ 图片目录: {optimizer.chinese_images_dir}")
        print(f"📋 目录文件: {optimizer.chinese_dir}/目录.md")
        print(f"📖 设置指南: {optimizer.chinese_dir}/阅读器设置指南.md")

        print("\n💡 建议使用Typora、Mark Text等专业Markdown阅读器")
        print("🔍 图片显示问题请查看'阅读器设置指南.md'")

    except Exception as e:
        print(f"❌ 优化过程中出错: {e}")


if __name__ == "__main__":
    main()