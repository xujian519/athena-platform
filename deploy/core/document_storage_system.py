#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档存储系统管理器
Document Storage System Manager - 统一管理工作文档和专利文件

提供标准化的目录结构创建、文件分类、索引和检索功能
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)


class DocumentStorageSystem:
    """文档存储系统管理器"""

    def __init__(self, base_path: str = "/Users/xujian/工作"):
        """
        初始化文档存储系统

        Args:
            base_path: 基础工作路径
        """
        self.base_path = Path(base_path)
        self.system_path = Path("/Users/xujian/Athena工作平台/deploy")

        # 标准目录结构
        self.directory_structure = {
            "01_客户管理": {
                "description": "所有客户相关的文件和资料",
                "subdirs": {
                    "01_正式客户": {
                        "description": "已签约并缴费的正式客户",
                        "pattern": "客户姓名 + 项目信息"
                    },
                    "02_临时客户": {
                        "description": "正在洽谈中的潜在客户",
                        "pattern": "客户姓名 + 状态标识"
                    },
                    "03_历史客户": {
                        "description": "项目完成的客户档案",
                        "pattern": "客户姓名 + 完成时间"
                    }
                }
            },
            "02_专利管理": {
                "description": "专利申请和管理的专门文件",
                "subdirs": {
                    "01_在申请": {
                        "description": "正在申请过程中的专利",
                        "subdirs": {
                            "01_准备阶段": "技术交底、检索分析阶段",
                            "02_撰写阶段": "申请文件撰写阶段",
                            "03_提交阶段": "已提交待审查",
                            "04_审查答复": "审查意见答复"
                        }
                    },
                    "02_已授权": {
                        "description": "已获得授权的专利",
                        "subdirs": {
                            "01_年费管理": "年费缴纳和管理",
                            "02_维护管理": "专利维护和变更"
                        }
                    },
                    "03_驳回终止": {
                        "description": "驳回或终止的专利"
                    }
                }
            },
            "03_法律文书": {
                "description": "法律文件和合同文档",
                "subdirs": {
                    "01_合同协议": "各类合同和协议文件",
                    "02_法律意见": "法律意见和分析",
                    "03_官方文件": "官方来函和通知"
                }
            },
            "04_审查意见": {
                "description": "专利审查意见和答复",
                "pattern": "申请号 + 审查轮次 + 日期",
                "subdirs": {
                    "01_待答复": "需要处理的审查意见",
                    "02_已答复": "已处理的审查意见",
                    "03_特殊程序": "复审、无效等特殊程序"
                }
            },
            "05_技术资料": {
                "description": "技术分析和研究报告",
                "subdirs": {
                    "01_检索分析": "专利检索和分析报告",
                    "02_技术分析": "技术方案分析",
                    "03_行业研究": "行业和竞争分析"
                }
            },
            "06_财务档案": {
                "description": "财务和收费相关文件",
                "subdirs": {
                    "01_缴费通知": "客户缴费通知单",
                    "02_收费记录": "收费确认和记录",
                    "03_财务报表": "各类财务报表"
                }
            },
            "07_系统管理": {
                "description": "系统管理文件",
                "subdirs": {
                    "01_客户档案": "系统客户档案JSON",
                    "02_案卷记录": "案卷管理记录",
                    "03_索引文件": "文件索引和映射",
                    "04_备份文件": "重要文件备份"
                }
            },
            "08_模板库": {
                "description": "各类模板和标准文件",
                "subdirs": {
                    "01_申请书模板": "专利申请文件模板",
                    "02_合同模板": "合同协议模板",
                    "03_报告模板": "各类报告模板"
                }
            },
            "09_临时文件": {
                "description": "临时处理和待整理文件",
                "pattern": "按日期分类"
            }
        }

    def create_standard_directory_structure(self) -> bool:
        """创建标准目录结构"""
        try:
            print("🏗️  创建标准目录结构...")

            for main_dir, config in self.directory_structure.items():
                main_path = self.base_path / main_dir

                # 创建主目录
                main_path.mkdir(exist_ok=True)

                # 创建说明文件
                readme_path = main_path / "README.md"
                if not readme_path.exists():
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {main_dir}\n\n")
                        f.write(f"**描述**: {config['description']}\n\n")
                        if 'pattern' in config:
                            f.write(f"**命名规范**: {config['pattern']}\n\n")
                        f.write(f"**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                        f.write("## 目录说明\n\n")

                # 创建子目录
                if 'subdirs' in config:
                    for sub_dir, sub_config in config['subdirs'].items():
                        sub_path = main_path / sub_dir

                        if isinstance(sub_config, str):
                            # 简单字符串描述
                            sub_path.mkdir(exist_ok=True)

                            # 创建子目录说明文件
                            sub_readme = sub_path / "README.md"
                            if not sub_readme.exists():
                                with open(sub_readme, 'w', encoding='utf-8') as f:
                                    f.write(f"# {sub_dir}\n\n")
                                    f.write(f"**描述**: {sub_config}\n\n")
                                    f.write(f"**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                        elif isinstance(sub_config, dict):
                            # 复杂配置对象
                            sub_path.mkdir(exist_ok=True)

                            sub_readme = sub_path / "README.md"
                            if not sub_readme.exists():
                                with open(sub_readme, 'w', encoding='utf-8') as f:
                                    f.write(f"# {sub_dir}\n\n")
                                    f.write(f"**描述**: {sub_config['description']}\n\n")
                                    if 'pattern' in sub_config:
                                        f.write(f"**命名规范**: {sub_config['pattern']}\n\n")
                                    f.write(f"**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                                    if 'subdirs' in sub_config:
                                        f.write("## 子目录\n\n")
                                        for sub_sub_dir, sub_sub_desc in sub_config['subdirs'].items():
                                            f.write(f"- **{sub_sub_dir}**: {sub_sub_desc}\n")
                                        f.write("\n")

                            # 创建二级子目录
                            if 'subdirs' in sub_config:
                                for sub_sub_dir, sub_sub_desc in sub_config['subdirs'].items():
                                    sub_sub_path = sub_path / sub_sub_dir
                                    sub_sub_path.mkdir(exist_ok=True)

                                    sub_sub_readme = sub_sub_path / "README.md"
                                    if not sub_sub_readme.exists():
                                        with open(sub_sub_readme, 'w', encoding='utf-8') as f:
                                            f.write(f"# {sub_sub_dir}\n\n")
                                            f.write(f"**描述**: {sub_sub_desc}\n\n")
                                            f.write(f"**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            print("✅ 标准目录结构创建完成")
            return True

        except Exception as e:
            logger.error(f"创建标准目录结构失败: {str(e)}")
            print(f"❌ 创建失败: {str(e)}")
            return False

    def analyze_existing_files(self) -> Dict[str, Any]:
        """分析现有文件结构"""
        analysis = {
            "total_customers": 0,
            "patent_files": 0,
            "legal_documents": 0,
            "other_files": 0,
            "customer_directories": [],
            "recommendations": []
        }

        try:
            print("📊 分析现有文件结构...")

            for item in self.base_path.iterdir():
                if item.is_dir():
                    # 检查是否为客户目录
                    if self._is_customer_directory(item):
                        customer_info = self._analyze_customer_directory(item)
                        analysis["customer_directories"].append(customer_info)
                        analysis["total_customers"] += 1

                    # 检查是否为审查意见
                    elif "审查意见" in item.name or "审查" in item.name:
                        analysis["legal_documents"] += 1

                    # 检查其他类型
                    else:
                        analysis["other_files"] += 1

                elif item.is_file():
                    file_ext = item.suffix.lower()
                    if file_ext in ['.doc', '.docx', '.pdf']:
                        analysis["patent_files"] += 1

            # 生成建议
            analysis["recommendations"] = self._generate_recommendations(analysis)

            print(f"✅ 分析完成: 发现 {analysis['total_customers']} 个客户目录")
            return analysis

        except Exception as e:
            logger.error(f"分析文件结构失败: {str(e)}")
            print(f"❌ 分析失败: {str(e)}")
            return analysis

    def _is_customer_directory(self, path: Path) -> bool:
        """判断是否为客户目录"""
        customer_indicators = [
            # 直接客户姓名
            r'^[王李张刘陈杨黄赵周吴徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾萧田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤][^/]*',
            # 包含客户关键词
            r'.*客户.*', r'.*客户[0-9]*件.*', r'.*实用新型.*件.*'
        ]

        for pattern in customer_indicators:
            if re.match(pattern, path.name):
                return True

        return False

    def _analyze_customer_directory(self, path: Path) -> Dict[str, Any]:
        """分析客户目录"""
        analysis = {
            "name": path.name,
            "path": str(path),
            "size_mb": 0,
            "file_count": 0,
            "file_types": {},
            "patent_count": 0,
            "estimated_stage": "unknown"
        }

        try:
            total_size = 0
            file_types = {}

            for item in path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
                    analysis["file_count"] += 1

                    # 统计文件类型
                    ext = item.suffix.lower()
                    if ext not in file_types:
                        file_types[ext] = 0
                    file_types[ext] += 1

                    # 检查专利相关文件
                    if any(keyword in item.name.lower() for keyword in ['专利', '申请', '实用新型', '发明', '说明书', '权利要求']):
                        analysis["patent_count"] += 1

            analysis["size_mb"] = round(total_size / (1024 * 1024), 2)
            analysis["file_types"] = file_types

            # 估算阶段
            if analysis["patent_count"] > 0:
                if "申报稿" in str(path) or "提交" in str(path):
                    analysis["estimated_stage"] = "申请阶段"
                elif "审查" in str(path):
                    analysis["estimated_stage"] = "审查阶段"
                else:
                    analysis["estimated_stage"] = "准备阶段"

        except Exception as e:
            logger.error(f"分析客户目录失败 {path}: {str(e)}")

        return analysis

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成整理建议"""
        recommendations = []

        if analysis["total_customers"] > 0:
            recommendations.append(f"发现 {analysis['total_customers']} 个客户目录，建议整理到 '01_客户管理' 目录下")

        if analysis["legal_documents"] > 0:
            recommendations.append(f"发现 {analysis['legal_documents']} 个审查意见文件，建议整理到 '04_审查意见' 目录下")

        if analysis["patent_files"] > 0:
            recommendations.append(f"发现 {analysis['patent_files']} 个专利相关文件，建议建立专利档案")

        # 分析客户目录
        customer_dirs = analysis["customer_directories"]
        large_customer_dirs = [c for c in customer_dirs if c["size_mb"] > 50]

        if large_customer_dirs:
            recommendations.append(f"发现 {len(large_customer_dirs)} 个大型客户目录（>50MB），建议进一步分类整理")

        return recommendations

    def migrate_customer_files(self, customer_name: str, customer_status: str = "正式客户") -> bool:
        """迁移客户文件到标准结构"""
        try:
            print(f"🔄 迁移客户文件: {customer_name}")

            # 查找现有客户目录
            existing_dirs = []
            for item in self.base_path.iterdir():
                if item.is_dir() and customer_name in item.name:
                    existing_dirs.append(item)

            if not existing_dirs:
                print(f"⚠️  未找到客户 '{customer_name}' 的目录")
                return False

            # 目标目录
            if customer_status == "正式客户":
                target_base = self.base_path / "01_客户管理" / "01_正式客户"
            elif customer_status == "临时客户":
                target_base = self.base_path / "01_客户管理" / "02_临时客户"
            else:
                target_base = self.base_path / "01_客户管理" / "03_历史客户"

            target_dir = target_base / f"{customer_name}_{datetime.now().strftime('%Y%m%d')}"

            # 迁移文件
            for source_dir in existing_dirs:
                print(f"  📁 迁移: {source_dir} -> {target_dir}")

                if target_dir.exists():
                    # 如果目标目录存在，合并内容
                    for item in source_dir.iterdir():
                        target_item = target_dir / item.name

                        if item.is_file():
                            if not target_item.exists():
                                shutil.copy2(item, target_item)
                            else:
                                # 文件名冲突，添加时间戳
                                timestamp = datetime.now().strftime('%H%M%S')
                                new_name = f"{item.stem}_{timestamp}{item.suffix}"
                                shutil.copy2(item, target_dir / new_name)

                        elif item.is_dir():
                            if not target_item.exists():
                                shutil.copytree(item, target_item)
                            else:
                                # 递归合并目录
                                for sub_item in item.iterdir():
                                    shutil.copy2(sub_item, target_item / sub_item.name)

                    # 删除原目录（谨慎操作，先移动到临时目录）
                    temp_dir = self.base_path / "09_临时文件" / f"已迁移_{source_dir.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.move(str(source_dir), str(temp_dir))
                else:
                    # 直接移动目录
                    shutil.move(str(source_dir), str(target_dir))

            print(f"✅ 客户文件迁移完成: {customer_name}")
            return True

        except Exception as e:
            logger.error(f"迁移客户文件失败: {str(e)}")
            print(f"❌ 迁移失败: {str(e)}")
            return False

    def create_customer_directory(self, customer_name: str, customer_status: str = "正式客户") -> Path:
        """为客户创建标准目录结构"""
        try:
            if customer_status == "正式客户":
                base_dir = self.base_path / "01_客户管理" / "01_正式客户"
            elif customer_status == "临时客户":
                base_dir = self.base_path / "01_客户管理" / "02_临时客户"
            else:
                base_dir = self.base_path / "01_客户管理" / "03_历史客户"

            customer_dir = base_dir / f"{customer_name}_{datetime.now().strftime('%Y%m%d')}"
            customer_dir.mkdir(parents=True, exist_ok=True)

            # 创建客户目录的标准子结构
            subdirs = [
                "01_基本信息",
                "02_专利申请",
                "03_技术资料",
                "04_沟通记录",
                "05_财务档案",
                "06_审查答复",
                "07_附图图纸",
                "08_合同协议"
            ]

            for subdir in subdirs:
                (customer_dir / subdir).mkdir(exist_ok=True)

                # 创建子目录说明
                readme = customer_dir / subdir / "README.md"
                if not readme.exists():
                    with open(readme, 'w', encoding='utf-8') as f:
                        f.write(f"# {subdir}\n\n")
                        f.write(f"**客户**: {customer_name}\n")
                        f.write(f"**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            print(f"✅ 客户目录创建完成: {customer_dir}")
            return customer_dir

        except Exception as e:
            logger.error(f"创建客户目录失败: {str(e)}")
            print(f"❌ 创建失败: {str(e)}")
            return Path()

    def generate_file_index(self) -> Dict[str, Any]:
        """生成文件索引"""
        index = {
            "created_at": datetime.now().isoformat(),
            "base_path": str(self.base_path),
            "directories": {},
            "files": [],
            "total_size": 0
        }

        try:
            print("📋 生成文件索引...")

            file_count = 0
            total_size = 0

            for root, dirs, files in os.walk(self.base_path):
                # 跳过隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                rel_path = os.path.relpath(root, self.base_path)

                if files:
                    index["directories"][rel_path] = {
                        "file_count": len(files),
                        "files": []
                    }

                    for file in files:
                        if not file.startswith('.'):
                            file_path = Path(root) / file
                            rel_file_path = os.path.relpath(file_path, self.base_path)

                            try:
                                file_size = file_path.stat().st_size
                                file_info = {
                                    "name": file,
                                    "path": rel_file_path,
                                    "size": file_size,
                                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                                }

                                index["directories"][rel_path]["files"].append(file_info)
                                index["files"].append(file_info)

                                total_size += file_size
                                file_count += 1

                            except Exception as e:
                                logger.error(f"索引文件失败 {file_path}: {str(e)}")

            index["total_files"] = file_count
            index["total_size"] = total_size
            index["total_size_mb"] = round(total_size / (1024 * 1024), 2)

            # 保存索引文件
            index_path = self.system_path / "data" / "文件索引_最新.json"
            index_path.parent.mkdir(exist_ok=True)

            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index, f, ensure_ascii=False, indent=2)

            print(f"✅ 文件索引生成完成: {file_count} 个文件, {index['total_size_mb']} MB")
            print(f"📁 索引文件: {index_path}")

            return index

        except Exception as e:
            logger.error(f"生成文件索引失败: {str(e)}")
            print(f"❌ 生成失败: {str(e)}")
            return index

    def search_files(self, pattern: str, file_types: Optional[List[str] = None) -> List[Dict[str, Any]]:
        """搜索文件"""
        results = []

        try:
            print(f"🔍 搜索文件: {pattern}")

            for root, dirs, files in os.walk(self.base_path):
                # 跳过隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for file in files:
                    if not file.startswith('.'):
                        # 检查文件名匹配
                        if pattern.lower() in file.lower():
                            file_path = Path(root) / file

                            # 检查文件类型
                            if file_types is None or file_path.suffix.lower() in file_types:
                                try:
                                    file_info = {
                                        "name": file,
                                        "path": str(file_path),
                                        "relative_path": os.path.relpath(file_path, self.base_path),
                                        "size": file_path.stat().st_size,
                                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                                    }

                                    results.append(file_info)

                                except Exception as e:
                                    logger.error(f"搜索文件失败 {file_path}: {str(e)}")

            print(f"✅ 搜索完成: 找到 {len(results)} 个匹配文件")
            return results

        except Exception as e:
            logger.error(f"搜索文件失败: {str(e)}")
            print(f"❌ 搜索失败: {str(e)}")
            return results