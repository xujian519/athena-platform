#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的JanusGraph批量导入
使用交互式方式逐条导入数据
"""

import subprocess
import time
import logging
import sys
import os

# 设置UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleJanusGraphImporter:
    """简化的JanusGraph导入器"""

    def __init__(self):
        self.docker_name = "janusgraph-kg"
        self.stats = {
            "patents": 0,
            "companies": 0,
            "inventors": 0,
            "relations": 0
        }

    def execute_gremlin(self, query, description="执行查询"):
        """执行Gremlin查询"""
        logger.info(f"🔧 {description}")

        try:
            # 创建临时脚本文件
            script_path = "/tmp/gremlin_script.gremlin"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(query)

            # 执行命令
            cmd = [
                'docker', 'exec', self.docker_name,
                '/opt/janusgraph/bin/gremlin.sh',
                f':load {script_path}'
            ]

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 等待执行完成
            stdout, stderr = process.communicate()

            # 清理临时文件
            os.remove(script_path)

            if process.returncode == 0:
                return True
            else:
                logger.error(f"执行失败: {stderr}")
                return False

        except Exception as e:
            logger.error(f"执行异常: {e}")
            return False

    def import_patents(self, count=50):
        """导入专利数据"""
        logger.info(f"📚 导入专利数据 ({count} 条)...")

        # 创建索引
        self.execute_gremlin("""
mgmt = graph.openManagement()
try {
    if (!mgmt.containsPropertyKey('entity_id')) {
        mgmt.makePropertyKey('entity_id').dataType(String.class).make()
    }
    mgmt.makePropertyKey('title').dataType(String.class).make()
    mgmt.makePropertyKey('patent_number').dataType(String.class).make()
    mgmt.buildIndex('byEntityId', Vertex.class)
        .addKey(mgmt.getPropertyKey('entity_id'))
        .buildCompositeIndex()
    mgmt.commit()
    println('✅ 索引创建完成')
} catch (e) {
    println('⚠️ 索引可能已存在')
}
        """, "创建索引")

        # 分批导入
        batch_size = 5
        for batch_start in range(1, count + 1, batch_size):
            batch_end = min(batch_start + batch_size - 1, count)

            query = f"""
g.tx().commit()
g.tx().open()

"""

            for i in range(batch_start, batch_end + 1):
                query += f"""
g.addV('Patent')
    .property('entity_id', 'patent_{i}')
    .property('patent_number', 'CN{str(i).zfill(9)}A')
    .property('title', '深度学习专利 {i}: 创新的神经网络架构')
    .property('abstract', '本专利涉及深度学习算法优化，提升训练效率。')
    .property('inventors', '发明人{(i%10)+1}')
    .property('assignee', '科技公司{(i%20)+1}')
    .property('application_date', '2023-{str(i%12+1).zfill(2)}-01')
    .property('created_at', new Date())
    .next()
"""

            query += """
g.tx().commit()
println('完成专利 ' + str(batch_end) + ' 条')
"""

            success = self.execute_gremlin(query, f"导入专利 {batch_start}-{batch_end}")
            if success:
                self.stats["patents"] += (batch_end - batch_start + 1)
                logger.info(f"  已完成: {batch_end}/{count}")

        logger.info(f"✅ 专利导入完成: {self.stats['patents']} 条")

    def import_companies(self, count=20):
        """导入公司数据"""
        logger.info(f"🏢 导入公司数据 ({count} 条)...")

        query = """
g.tx().commit()
g.tx().open()

"""

        for i in range(1, count + 1):
            query += f"""
g.addV('Company')
    .property('entity_id', 'company_{i}')
    .property('company_id', 'COMP{str(i).zfill(6)}')
    .property('name', 'AI科技公司{i}')
    .property('industry', '人工智能')
    .property('location', '北京市')
    .property('founded_date', '2010-{str(i%12+1).zfill(2)}-01')
    .property('created_at', new Date())
    .next()
"""

        query += """
g.tx().commit()
"""

        success = self.execute_gremlin(query, "导入公司数据")
        if success:
            self.stats["companies"] = count
            logger.info(f"✅ 公司导入完成: {count} 条")

    def import_inventors(self, count=30):
        """导入发明人数据"""
        logger.info(f"👥 导入发明人数据 ({count} 条)...")

        surnames = ["张", "李", "王", "刘", "陈"]
        names = ["伟", "芳", "娜", "敏", "静"]

        query = """
g.tx().commit()
g.tx().open()

"""

        for i in range(1, count + 1):
            surname = surnames[i % 5]
            name = names[i % 5]

            query += f"""
g.addV('Inventor')
    .property('entity_id', 'inventor_{i}')
    .property('inventor_id', 'INV{str(i).zfill(6)}')
    .property('name', '{surname}{name}')
    .property('organization', '清华大学')
    .property('specialization', '深度学习/计算机视觉')
    .property('patent_count', {(i%10)+1})
    .property('created_at', new Date())
    .next()
"""

        query += """
g.tx().commit()
"""

        success = self.execute_gremlin(query, "导入发明人数据")
        if success:
            self.stats["inventors"] = count
            logger.info(f"✅ 发明人导入完成: {count} 条")

    def import_relations(self):
        """导入关系数据"""
        logger.info("🔗 导入关系数据...")

        # 专利-公司关系
        query = """
g.tx().commit()
g.tx().open()

"""

        for i in range(1, 30):
            patent_id = (i % 50) + 1
            company_id = (i % 20) + 1

            query += f"""
p = g.V().has('entity_id', 'patent_{patent_id}').tryNext()
c = g.V().has('entity_id', 'company_{company_id}').tryNext()

if (p.isPresent() && c.isPresent()) {{
    p.get().addEdge('OWNED_BY', c.get())
        .property('created_at', new Date())
        .next()
}}
"""

        query += """
g.tx().commit()
"""

        success = self.execute_gremlin(query, "导入专利-公司关系")
        if success:
            self.stats["relations"] += 30

        # 专利-发明人关系
        query = """
g.tx().commit()
g.tx().open()

"""

        for i in range(1, 50):
            patent_id = (i % 50) + 1
            inventor_id = (i % 30) + 1

            query += f"""
p = g.V().has('entity_id', 'patent_{patent_id}').tryNext()
inv = g.V().has('entity_id', 'inventor_{inventor_id}').tryNext()

if (p.isPresent() && inv.isPresent()) {{
    p.get().addEdge('INVENTED_BY', inv.get())
        .property('contribution_type', 'main')
        .property('created_at', new Date())
        .next()
}}
"""

        query += """
g.tx().commit()
"""

        success = self.execute_gremlin(query, "导入专利-发明人关系")
        if success:
            self.stats["relations"] += 50

        logger.info(f"✅ 关系导入完成: {self.stats['relations']} 条")

    def validate_import(self):
        """验证导入结果"""
        logger.info("\n🔍 验证导入结果...")
        logger.info("=" * 50)

        # 统计顶点
        self.execute_gremlin("""
vertex_count = g.V().count().next()
println('\\n✅ 顶点总数: ' + vertex_count)

// 按类型统计顶点
vertex_types = g.V().groupCount().by(label).next()
if (vertex_types) {
    println('\\n📋 顶点类型分布:')
    vertex_types.each { label, count ->
        println('  ' + label + ': ' + count)
    }
}
        """, "验证导入结果")

        # 统计边
        self.execute_gremlin("""
edge_count = g.E().count().next()
println('\\n✅ 边总数: ' + edge_count)

// 按类型统计边
edge_types = g.E().groupCount().by(label).next()
if (edge_types) {
    println('\\n📋 边类型分布:')
    edge_types.each { label, count ->
        println('  ' + label + ': ' + count)
    }
}
        """, "验证关系结果")

        # 示例查询
        self.execute_gremlin("""
// 示例查询
patents = g.V().hasLabel('Patent').limit(3).valueMap().next()
if (patents && patents.size() > 0) {
    println('\\n📝 示例专利:')
    patents.eachWithIndex { idx, patent ->
        println('  ' + (idx + 1) + '. ' + patent.get('patent_number', 'N/A'))
    }
}
        """, "查询示例数据")

        return self.stats

    def run_import(self):
        """执行完整导入"""
        logger.info("🚀 开始JanusGraph简化导入...")
        logger.info("=" * 60)

        start_time = time.time()

        try:
            # 1. 导入专利
            self.import_patents(50)

            # 2. 导入公司
            self.import_companies(20)

            # 3. 导入发明人
            self.import_inventors(30)

            # 4. 导入关系
            self.import_relations()

            # 5. 验证结果
            results = self.validate_import()

            end_time = time.time()
            duration = end_time - start_time

            logger.info("\n" + "=" * 60)
            logger.info("✅ 导入完成！")
            logger.info(f"⏱️ 总耗时: {duration:.2f}秒")
            logger.info(f"📊 导入统计:")
            logger.info(f"   专利: {results['patents']} 条")
            logger.info(f"  公司: {results['companies']} 条")
            logger.info(f"  发明人: {results['inventors']} 条")
            logger.info(f"  关系: {results['relations']} 条")

            total = sum(results.values())
            logger.info(f"\n🎉 总计导入: {total} 条实体和关系")

            return True

        except Exception as e:
            logger.error(f"❌ 导入失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    importer = SimpleJanusGraphImporter()
    success = importer.run_import()

    if success:
        print("\n🎉 JanusGraph知识图谱导入成功！")
        print("\n💡 使用方式:")
        print("1. 查看导入数据: docker exec -it janusgraph-kg /opt/janusgraph/bin/gremlin.sh")
        print("2. 图统计查询: g.V().count()")
        print("3. 连接到混合搜索API: http://localhost:8080/docs")
        print("\n📊 导入的实体已存储在JanusGraph中，可以开始使用！")

if __name__ == "__main__":
    main()