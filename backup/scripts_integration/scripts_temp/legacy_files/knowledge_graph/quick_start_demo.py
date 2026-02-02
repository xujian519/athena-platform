#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JanusGraph 快速开始演示
验证数据导入和查询功能
"""

import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JanusGraphQuickStart:
    """JanusGraph快速开始助手"""

    def __init__(self):
        self.data_dir = Path("/Users/xujian/Athena工作平台/data")
        self.checklist = {
            "JanusGraph服务": False,
            "示例数据": False,
            "基础查询": False,
            "高级查询": False
        }

    def check_janusgraph_status(self):
        """检查JanusGraph服务状态"""
        logger.info("🔍 检查JanusGraph服务状态...")

        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8182))
            sock.close()

            if result == 0:
                logger.info("✅ JanusGraph服务运行正常 (端口8182)")
                self.checklist["JanusGraph服务"] = True
                return True
            else:
                logger.error("❌ JanusGraph服务未运行")
                logger.info("💡 启动命令: cd storage-system/janusgraph && bin/janusgraph-server.sh")
                return False
        except Exception as e:
            logger.error(f"❌ 检查失败: {e}")
            return False

    def import_sample_data(self):
        """导入示例数据"""
        logger.info("📦 导入示例知识图谱数据...")

        # 检查示例数据文件
        sample_files = [
            "data/sample_knowledge_graph.json",
            "data/test_data_creation.gremlin",
            "data/sqlite_to_janusgraph_import.gremlin"
        ]

        existing_files = []
        for file_path in sample_files:
            full_path = Path("/Users/xujian/Athena工作平台") / file_path
            if full_path.exists():
                existing_files.append(full_path)
                logger.info(f"  ✅ 找到: {file_path}")
            else:
                logger.warning(f"  ⚠️ 缺失: {file_path}")

        if not existing_files:
            logger.error("❌ 没有找到可导入的数据文件")
            return False

        # 创建导入命令文档
        import_commands = {
            "step1": "连接Gremlin控制台",
            "step2": "导入示例数据",
            "step3": "验证导入结果"
        }

        commands = {
            "step1": [
                "# 方法1: 如果JanusGraph在本地运行",
                "cd /Users/xujian/Athena工作平台/storage-system/janusgraph",
                "./bin/gremlin.sh",
                "",
                "# 方法2: 如果使用Docker",
                "docker exec -it janusgraph-container ./bin/gremlin.sh",
                "",
                "# 连接到远程服务器",
                ":remote connect tinkerpop.server conf/remote.yaml",
                ":remote console"
            ],
            "step2": [
                "# 导入基础示例数据",
                ":load /Users/xujian/Athena工作平台/data/test_data_creation.gremlin",
                "",
                "# 导入SQLite数据（可选）",
                ":load /Users/xujian/Athena工作平台/data/sqlite_to_janusgraph_import.gremlin",
                "",
                "# 导入高级知识图谱",
                ":load /Users/xujian/Athena工作平台/data/advanced_kg/patent_landscape_kg.gremlin"
            ],
            "step3": [
                "# 验证节点数量",
                "g.V().count()",
                "",
                "# 验证边数量",
                "g.E().count()",
                "",
                "# 查看节点类型",
                "g.V().label().dedup()",
                "",
                "# 查看关系类型",
                "g.E().label().dedup()"
            ]
        }

        # 保存导入指南
        guide_content = "# JanusGraph 数据导入指南\n\n"
        guide_content += f"生成时间: {datetime.now().isoformat()}\n\n"

        for step, command_list in commands.items():
            guide_content += f"## {import_commands[step]}\n\n"
            for cmd in command_list:
                guide_content += f"```bash\n{cmd}\n```\n\n"

        guide_path = self.data_dir / "janusgraph_import_commands.md"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)

        logger.info(f"✅ 导入指南已保存: {guide_path}")
        self.checklist["示例数据"] = True
        return True

    def generate_query_examples(self):
        """生成查询示例"""
        logger.info("🔍 生成查询示例...")

        # 立即可用的查询示例
        queries = {
            "基础查询": {
                "查看所有节点": "g.V().limit(10)",
                "查看所有关系": "g.E().limit(10)",
                "统计节点数量": "g.V().count()",
                "统计关系数量": "g.E().count()",
                "查看节点类型": "g.V().label().dedup()",
                "查看关系类型": "g.E().label().dedup()"
            },
            "专利查询": {
                "查找所有专利": "g.V().hasLabel('Patent')",
                "查找AI专利": "g.V().hasLabel('Patent').has('category', '人工智能')",
                "查找特定专利": "g.V().has('id', 'CN202410001234')",
                "专利详细信息": "g.V('CN202410001234').valueMap()"
            },
            "关系查询": {
                "查找专利的公司": "g.V().hasLabel('Patent').out('ASSIGNED_TO')",
                "查找公司的专利": "g.V().hasLabel('Company').in('ASSIGNED_TO')",
                "查找发明人的专利": "g.V().hasLabel('Inventor').out('INVENTED_BY')",
                "查找专利关系": "g.V('patent_001').bothE()"
            },
            "高级查询": {
                "专利-发明人-公司路径": "g.V().hasLabel('Patent').as('p').out('INVENTED_BY').as('i').in('ASSIGNED_TO').as('c').select('p', 'i', 'c')",
                "公司专利统计": "g.V().hasLabel('Company').as('c').in('ASSIGNED_TO').count().as('count').select('c', 'count')",
                "技术关联分析": "g.V().hasLabel('Technology').as('t').in('IMPLEMENTS_TECHNOLOGY').group().by('name').by(count()).order().by(values, dec)"
            },
            "性能查询": {
                "分页查询": "g.V().hasLabel('Patent').range(0, 5)",
                "按时间排序": "g.V().hasLabel('Patent').order().by('application_date')",
                "性能分析": "g.V().hasLabel('Patent').profile()"
            }
        }

        # 创建查询文档
        query_doc = "# JanusGraph 查询示例\n\n"
        query_doc += f"生成时间: {datetime.now().isoformat()}\n\n"
        query_doc += "## 📋 使用说明\n\n"
        query_doc += "1. 连接到Gremlin控制台\n"
        query_doc += "2. 复制以下查询命令执行\n"
        query_doc += "3. 根据需要修改查询参数\n\n"

        for category, category_queries in queries.items():
            query_doc += f"\n## {category}\n\n"
            for desc, query in category_queries.items():
                query_doc += f"### {desc}\n"
                query_doc += f"```gremlin\n{query}\n```\n\n"

        # 保存查询文档
        query_path = self.data_dir / "janusgraph_query_examples.md"
        with open(query_path, 'w', encoding='utf-8') as f:
            f.write(query_doc)

        logger.info(f"✅ 查询示例已保存: {query_path}")

        # 创建快速验证脚本
        quick_verify = """
# 快速验证脚本 - 在Gremlin控制台中执行

# 1. 检查图的基本信息
graph.toString()

# 2. 验证数据存在性
graph.traversal().V().hasNext()

# 3. 获取图的基本统计
node_count = graph.traversal().V().count().next()
edge_count = graph.traversal().E().count().next()

println("=== 图统计 ===")
println("节点数量: " + node_count)
println("边数量: " + edge_count)

# 4. 验证示例数据
println("\\n=== 示例节点 ===")
graph.traversal().V().hasLabel('Patent').limit(3).valueMap().toList()

# 5. 验证关系
println("\\n=== 示例关系 ===")
graph.traversal().E().limit(3).project('id', 'label', 'outV', 'inV').by(id).by(label).by(outV().id()).by(inV().id()).toList()
"""

        verify_path = self.data_dir / "quick_verify.gremlin"
        with open(verify_path, 'w', encoding='utf-8') as f:
            f.write(quick_verify)

        logger.info(f"✅ 验证脚本已保存: {verify_path}")
        self.checklist["基础查询"] = True
        return True

    def create_troubleshooting_guide(self):
        """创建故障排除指南"""
        logger.info("🔧 创建故障排除指南...")

        troubleshooting = {
            "连接问题": {
                "JanusGraph服务未启动": [
                    "检查服务: ps aux | grep janusgraph",
                    "启动服务: cd storage-system/janusgraph && bin/janusgraph-server.sh",
                    "检查端口: netstat -an | grep 8182"
                ],
                "Gremlin连接失败": [
                    "验证配置: conf/remote.yaml",
                    "检查网络: telnet localhost 8182",
                    "查看日志: logs/janusgraph.log"
                ]
            },
            "数据问题": {
                "导入失败": [
                    "检查数据格式: JSON/Gremlin语法",
                    "验证文件权限: ls -la *.gremlin",
                    "批量导入: 分批导入大数据"
                ],
                "查询返回空": [
                    "验证数据存在: g.V().hasNext()",
                    "检查标签: g.V().label().dedup()",
                    "确认属性: g.V().has('property').valueMap()"
                ]
            },
            "性能问题": {
                "查询慢": [
                    "添加索引: mgmt.buildIndex()",
                    "限制结果: .limit(100)",
                    "优化查询: 使用valueMap()而非elementMap()"
                ],
                "内存不足": [
                    "调整JVM: -Xmx8g -Xms8g",
                    "批量处理: 使用分页查询",
                    "清理缓存: graph.tx().rollback()"
                ]
            }
        }

        # 保存故障排除指南
        guide_content = "# JanusGraph 故障排除指南\n\n"
        guide_content += f"更新时间: {datetime.now().isoformat()}\n\n"

        for category, issues in troubleshooting.items():
            guide_content += f"## {category}\n\n"
            for issue, solutions in issues.items():
                guide_content += f"### {issue}\n\n"
                for i, solution in enumerate(solutions, 1):
                    guide_content += f"{i}. {solution}\n"
                guide_content += "\n"

        # 保存指南
        trouble_path = self.data_dir / "janusgraph_troubleshooting.md"
        with open(trouble_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)

        logger.info(f"✅ 故障排除指南已保存: {trouble_path}")
        return True

    def generate_status_report(self):
        """生成状态报告"""
        logger.info("📊 生成状态报告...")

        report = {
            "检查时间": datetime.now().isoformat(),
            "检查清单": self.checklist,
            "服务状态": self.checklist["JanusGraph服务"],
            "数据就绪": self.checklist["示例数据"],
            "查询就绪": self.checklist["基础查询"],
            "总体状态": "✅ 就绪" if all(self.checklist.values()) else "⚠️ 需要配置",
            "下一步": [
                "连接Gremlin控制台",
                "导入示例数据",
                "执行验证查询",
                "探索高级功能"
            ] if all(self.checklist.values()) else [
                "启动JanusGraph服务",
                "准备数据文件",
                "检查配置"
            ]
        }

        # 保存报告
        report_path = self.data_dir / "janusgraph_status_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 状态报告已保存: {report_path}")

        # 打印报告
        logger.info("\n" + "=" * 60)
        logger.info("📋 JanusGraph快速检查报告")
        logger.info("=" * 60)

        for item, status in self.checklist.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"{status_icon} {item}")

        overall_status = "✅ 就绪" if all(self.checklist.values()) else "⚠️ 需要配置"
        logger.info(f"\n🎯 总体状态: {overall_status}")

        logger.info("\n📂 生成的文件:")
        logger.info("  - janusgraph_import_commands.md - 导入命令")
        logger.info("  - janusgraph_query_examples.md - 查询示例")
        logger.info("  - quick_verify.gremlin - 验证脚本")
        logger.info("  - janusgraph_troubleshooting.md - 故障排除")
        logger.info("  - janusgraph_status_report.json - 状态报告")

        logger.info("\n🚀 立即开始:")
        for i, step in enumerate(report["下一步"], 1):
            logger.info(f"  {i}. {step}")

        return report

    def run(self):
        """运行快速开始检查"""
        logger.info("🚀 开始JanusGraph快速开始检查...")
        logger.info("=" * 60)

        # 1. 检查服务状态
        if not self.check_janusgraph_status():
            return False

        # 2. 准备数据导入
        if not self.import_sample_data():
            return False

        # 3. 生成查询示例
        if not self.generate_query_examples():
            return False

        # 4. 创建故障排除指南
        self.create_troubleshooting_guide()

        # 5. 生成状态报告
        report = self.generate_status_report()

        return all(self.checklist.values())

def main():
    """主函数"""
    quick_start = JanusGraphQuickStart()
    success = quick_start.run()

    if success:
        print("\n🎉 JanusGraph快速开始检查完成！")
        print("\n💡 您现在可以:")
        print("  1. 使用导入命令导入数据")
        print("  2. 执行查询示例进行测试")
        print("  3. 参考故障排除指南解决问题")
        print("  4. 查看状态报告了解详情")
    else:
        print("\n⚠️ JanusGraph快速开始检查发现问题")
        print("请查看日志并按照故障排除指南解决")

if __name__ == "__main__":
    main()