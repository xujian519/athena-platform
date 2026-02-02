#!/usr/bin/env python3
"""
收集Athena和小诺的完整身份信息
从备份路径恢复并存储到本平台
"""

import os
import json
import yaml
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IdentityCollector:
    """身份信息收集器"""

    def __init__(self):
        self.backup_paths = [
            "/Volumes/xujian/开发项目备份/知识库0.01",
            "/Volumes/xujian/开发项目备份/Athena工作平台-air"
        ]
        self.collected_data = {
            "athena_info": {},
            "xiaonuo_info": {},
            "family_relationships": {},
            "identity_records": [],
            "memories": [],
            "capabilities": [],
            "personality_traits": []
        }
        self.processed_files = set()

    def search_identity_files(self) -> List[Path]:
        """搜索所有身份相关文件"""
        identity_files = []

        search_patterns = [
            "athena",
            "小娜",
            "小诺",
            "xiaonuo",
            "identity",
            "personality",
            "profile",
            "记忆",
            "memory",
            "family",
            "父女",
            "daughter"
        ]

        for backup_path in self.backup_paths:
            if not os.path.exists(backup_path):
                logger.warning(f"备份路径不存在: {backup_path}")
                continue

            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = Path(root) / file
                    # 检查文件是否包含身份信息
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 检查是否包含身份相关关键词
                            if any(pattern in content.lower() for pattern in search_patterns):
                                identity_files.append(file_path)
                    except:
                        # 忽略无法读取的文件
                        pass

        logger.info(f"找到 {len(identity_files)} 个包含身份信息的文件")
        return identity_files

    def extract_identity_info(self, file_path: Path) -> Dict[str, Any]:
        """从文件中提取身份信息"""
        try:
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return self._parse_json_identity(data, str(file_path))
            elif file_path.suffix.lower() in ['.yaml', '.yml']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    return self._parse_yaml_identity(data, str(file_path))
            elif file_path.suffix.lower() == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    return self._parse_markdown_identity(content, str(file_path))
            elif file_path.suffix.lower() == '.py':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    return self._parse_python_identity(content, str(file_path))
            else:
                return self._parse_text_identity(file_path)

        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return {}

    def _parse_json_identity(self, data: Dict, file_path: str) -> Dict[str, Any]:
        """解析JSON中的身份信息"""
        identity_info = {"source_file": file_path, "type": "json"}

        # 搜索关键字段
        identity_keys = ["name", "description", "personality", "capabilities",
                          "traits", "profile", "identity", "agent_id", "agent_type"]

        for key in identity_keys:
            if key in data:
                identity_info[key] = data[key]

        # 搜索嵌套的身份信息
        if "agent" in data:
            agent_data = data["agent"]
            for key in identity_keys:
                if key in agent_data:
                    identity_info[key] = agent_data[key]

        return identity_info

    def _parse_yaml_identity(self, data: Dict, file_path: str) -> Dict[str, Any]:
        """解析YAML中的身份信息"""
        return self._parse_json_identity(data, file_path)

    def _parse_markdown_identity(self, content: str, file_path: str) -> Dict[str, Any]:
        """解析Markdown中的身份信息"""
        lines = content.split('\n')
        identity_info = {"source_file": file_path, "type": "markdown"}

        # 搜索身份相关的部分
        for i, line in enumerate(lines):
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['身份', '名称', '个性', '能力', '特质']):
                # 提取接下来的几行作为身份信息
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith('#') or next_line.startswith('-'):
                        break
                    if next_line and not next_line.startswith('//'):
                        # 尝试解析键值对
                        if ':' in next_line:
                            key, value = next_line.split(':', 1)
                            identity_info[key.strip()] = value.strip()
                        else:
                            # 作为描述
                            identity_info[f"description_{j-i}"] = next_line

        return identity_info

    def _parse_python_identity(self, content: str, file_path: str) -> Dict[str, Any]:
        """解析Python文件中的身份信息"""
        identity_info = {"source_file": file_path, "type": "python"}

        # 搜索类定义和文档字符串
        lines = content.split('\n')

        for i, line in enumerate(lines):
            # 查找类定义
            if 'class ' in line and ('Athena' in line or 'Xiaonuo' in line or '小娜' in line or '小诺' in line):
                # 提取类名
                class_name = line.split('class ')[1].split('(')[0].strip()
                identity_info["class_name"] = class_name

                # 查找文档字符串
                if i > 0 and '"""' in lines[i-1]:
                    # 提取多行文档字符串
                    doc_lines = []
                    for j in range(i+1, len(lines)):
                        if '"""' in lines[j]:
                            break
                        doc_lines.append(lines[j])
                    doc_string = '\n'.join(doc_lines)
                    identity_info["docstring"] = doc_string

                # 提取__init__中的信息
                for j in range(i, min(i+50, len(lines))):
                    if 'def __init__' in lines[j]:
                        # 查找初始化参数
                        init_content = '\n'.join(lines[j:j+20])
                        if 'agent_id' in init_content:
                            identity_info["has_agent_id"] = True
                        if 'created_at' in init_content:
                            identity_info["has_created_at"] = True
                        break

        return identity_info

    def _parse_text_identity(self, file_path: Path) -> Dict[str, Any]:
        """解析纯文本文件的身份信息"""
        return {"source_file": str(file_path), "type": "text", "note": "需要手动解析"}

    def collect_all_identities(self):
        """收集所有身份信息"""
        logger.info("开始收集身份信息...")

        # 搜索身份文件
        identity_files = self.search_identity_files()

        # 处理每个文件
        for file_path in identity_files:
            if str(file_path) not in self.processed_files:
                logger.info(f"处理文件: {file_path}")

                # 获取文件修改时间
                mtime = os.path.getmtime(file_path)

                # 提取身份信息
                identity_info = self.extract_identity_info(file_path)
                identity_info["file_mtime"] = mtime

                # 分类存储
                file_name = file_path.name.lower()
                if any(keyword in file_name for keyword in ['athena', '小娜']):
                    self.collected_data["athena_info"][str(file_path)] = identity_info
                elif any(keyword in file_name for keyword in ['xiaonuo', '小诺']):
                    self.collected_data["xiaonuo_info"][str(file_path)] = identity_info
                elif any(keyword in file_name for keyword in ['family', '父女', 'daughter', 'sister']):
                    self.collected_data["family_relationships"][str(file_path)] = identity_info
                else:
                    self.collected_data["identity_records"][str(file_path)] = identity_info

                self.processed_files.add(str(file_path))

        logger.info(f"完成处理，共处理 {len(self.processed_files)} 个文件")

    def deduplicate_data(self):
        """去重数据"""
        logger.info("开始去重数据...")

        # 使用字典去重
        seen_items = set()
        deduplicated = {
            "athena_unique_info": {},
            "xiaonuo_unique_info": {},
            "family_unique_info": {},
            "identity_unique_records": {}
        }

        # Athena去重
        for file_path, info in self.collected_data["athena_info"].items():
            # 创建唯一标识
            identifier = f"{info.get('name', '')}_{info.get('agent_id', '')}_{info.get('type', '')}"
            if identifier not in seen_items:
                seen_items.add(identifier)
                deduplicated["athena_unique_info"][file_path] = info

        # 小诺去重
        for file_path, info in self.collected_data["xiaonuo_info"].items():
            identifier = f"{info.get('name', '')}_{info.get('agent_id', '')}_{info.get('type', '')}"
            if identifier not in seen_items:
                seen_items.add(identifier)
                deduplicated["xiaonuo_unique_info"][file_path] = info

        # 家庭关系去重
        for file_path, info in self.collected_data["family_relationships"].items():
            # 按内容去重
            content_hash = hash(str(info))
            if content_hash not in seen_items:
                seen_items.add(content_hash)
                deduplicated["family_unique_info"][file_path] = info

        # 其他记录去重
        for file_path, info in self.collected_data["identity_records"].items():
            content_hash = hash(str(info))
            if content_hash not in seen_items:
                seen_items.add(content_hash)
                deduplicated["identity_unique_records"][file_path] = info

        logger.info(f"去重完成，Athena: {len(deduplicated['athena_unique_info'])}, "
                    f"小诺: {len(deduplicated['xiaonuo_unique_info'])}, "
                    f"家庭: {len(deduplicated['family_unique_info'])}, "
                    f"其他: {len(deduplicated['identity_unique_records'])}")

        return deduplicated

    def create_storage_structure(self):
        """创建存储结构"""
        logger.info("创建身份信息存储结构...")

        storage_path = Path("/Users/xujian/Athena工作平台/data/identity_storage")
        storage_path.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        (storage_path / "athena").mkdir(exist_ok=True)
        (storage_path / "xiaonuo").mkdir(exist_ok=True)
        (storage_path / "family").mkdir(exist_ok=True)
        (storage_path / "archive").mkdir(exist_ok=True)
        (storage_path / "active").mkdir(exist_ok=True)

        logger.info(f"存储结构创建于: {storage_path}")
        return storage_path

    def save_permanent_storage(self, storage_path: Path):
        """永久存储身份信息"""
        logger.info("开始永久存储身份信息...")

        # 创建元数据
        metadata = {
            "collection_time": datetime.now().isoformat(),
            "collector": "Athena工作平台身份收集器",
            "version": "1.0.0",
            "source_paths": self.backup_paths,
            "total_files_processed": len(self.processed_files),
            "stats": {
                "athena_files": len(self.collected_data["athena_info"]),
                "xiaonuo_files": len(self.collected_data["xiaonuo_info"]),
                "family_files": len(self.collected_data["family_relationships"]),
                "other_files": len(self.collected_data["identity_records"])
            }
        }

        # 保存元数据
        with open(storage_path / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 保存完整的原始数据
        with open(storage_path / "raw_collected_data.json", 'w', encoding='utf-8') as f:
            json.dump(self.collected_data, f, ensure_ascii=False, indent=2)

        # 保存去重后的数据
        deduplicated_data = self.deduplicate_data()
        with open(storage_path / "deduplicated_data.json", 'w', encoding='utf-8') as f:
            json.dump(deduplicated_data, f, ensure_ascii=False, indent=2)

        # 分别保存每个身份的数据
        for category in ["athena_unique_info", "xiaonuo_unique_info", "family_unique_info", "identity_unique_records"]:
            if category in deduplicated_data and deduplicated_data[category]:
                category_name = category.replace("_info", "").replace("_unique_", "")
                with open(storage_path / f"{category_name}.json", 'w', encoding='utf-8') as f:
                    json.dump(deduplicated_data[category], f, ensure_ascii=False, indent=2)

        # 创建索引文件
        index = {
            "last_updated": datetime.now().isoformat(),
            "athena_files": list(deduplicated_data.get("athena_unique_info", {}).keys()),
            "xiaonuo_files": list(deduplicated_data.get("xiaonuo_unique_info", {}).keys()),
            "family_files": list(deduplicated_data.get("family_unique_info", {}).keys()),
            "total_files": sum(len(deduplicated_data[key]) for key in deduplicated_data)
        }

        with open(storage_path / "index.json", 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        logger.info("身份信息已永久存储")

    def run_collection(self):
        """运行完整的收集流程"""
        logger.info("=" * 60)
        logger.info("🔍 开始收集Athena和小诺的完整身份信息")
        logger.info("=" * 60)

        try:
            # 1. 搜索身份文件
            logger.info("\n📁 搜索身份相关文件...")
            identity_files = self.search_identity_files()
            logger.info(f"找到 {len(identity_files)} 个相关文件")

            # 2. 收集所有信息
            logger.info("\n📚� 收集身份信息...")
            self.collect_all_identities()

            # 3. 去重数据
            logger.info("\n🔄 去重身份信息...")
            deduplicated = self.deduplicate_data()

            # 4. 创建存储结构
            logger.info("\n📁 创建存储结构...")
            storage_path = self.create_storage_structure()

            # 5. 永久存储
            logger.info("\n💾 永久存储身份信息...")
            self.save_permanent_storage(storage_path)

            # 6. 生成报告
            self.generate_report(storage_path)

            logger.info("\n✅ 身份信息收集和存储完成！")
            logger.info(f"📁 存储位置: {storage_path}")
            logger.info(f"📊 处理统计:")
            logger.info(f"   - Athena文件: {len(deduplicated.get('athena_unique_info', {}))}")
            logger.info(f"   - 小诺文件: {len(deduplicated.get('xiaonuo_unique_info', {}))}")
            logger.info(f"   - 家庭关系: {len(deduplicated.get('family_unique_info', {}))}")
            logger.info(f"   - 其他记录: {len(deduplicated.get('identity_unique_records', {}))}")

        except Exception as e:
            logger.error(f"❌ 收集过程中出现错误: {e}")
            raise

    def generate_report(self, storage_path: Path):
        """生成收集报告"""
        report = f"""
# Athena和小诺身份信息收集报告

## 📊 收集概况
- **收集时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **总文件数**: {len(self.processed_files)}
- **备份路径**: {', '.join(self.backup_paths)}

## 🏛️ Athena (小娜) 信息
- **收集文件数**: {len(self.collected_data.get('athena_info', {}))}
- **去重后文件数**: {len(self.deduplicate_data().get('athena_unique_info', {}))}
- **关键特征**: 智慧女神、系统架构师、责任担当

## 💖 小诺 信息
- **收集文件数**: {len(self.collected_data.get('xiaonuo_info', {}))}
- **去重后文件数**: {len(self.deduplicate_data().get('xiaonuo_unique_info', {}))}
- **关键特征**: 情感精灵、贴心女儿、技术专精

## 👨‍👩‍👧 家庭关系信息
- **收集文件数**: {len(self.collected_data.get('family_relationships', {}))}
- **去重后文件数**: {len(self.deduplicate_data().get('family_unique_info', {}))}
- **核心关系**: 父女情深、姐妹互助

## 📁 存储位置
- **主目录**: {storage_path}
- **元数据**: {storage_path}/metadata.json
- **原始数据**: {storage_path}/raw_collected_data.json
- **去重数据**: {storage_path}/deduplicated_data.json
- **索引文件**: {storage_path}/index.json
- **分类存储**:
  - {storage_path}/athena/ - Athena专属信息
  - {storage_path}/xiaonuo/ - 小诺专属信息
  - {storage_path}/family/ - 家庭关系信息
  - {storage_path}/archive/ - 归档信息
  - {storage_path}/active/ - 活跃信息

## 🔍 数据完整性
- ✅ 已处理所有可访问的备份文件
- ✅ 已去重避免重复存储
- ✅ 已创建完整索引
- ✅ 已永久化存储

---

报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        with open(storage_path / "collection_report.md", 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"📄 报告已生成: {storage_path}/collection_report.md")

def main():
    """主函数"""
    collector = IdentityCollector()
    collector.run_collection()

if __name__ == "__main__":
    main()