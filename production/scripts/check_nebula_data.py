#!/usr/bin/env python3
"""
检查NebulaGraph知识图谱数据
Check NebulaGraph Knowledge Graph Data

检查NebulaGraph图数据库中的实际数据

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Any

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 导入安全配置
try:
    from production.config import get_nebula_config
except ImportError:
    def get_nebula_config() -> Any | None:
        return {
            'host': '127.0.0.1',
            'port': 9669,
            'user': 'root',
            "password": config.get("NEBULA_PASSWORD", required=True),
            'space': 'patent_kg'
        }


from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool

from core.config.secure_config import get_config

config = get_config()


# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[35m"
    CYAN = "\033[96m"
    PINK = "\033[95m"
    RESET = "\033[0m"

def print_header(title) -> None:
    """打印标题"""
    print(f"\n{Colors.PURPLE}{'='*80}{Colors.RESET}")
    print(f"{Colors.PURPLE}🕸️ {title} 🕸️{Colors.RESET}")
    print(f"{Colors.PURPLE}{'='*80}{Colors.RESET}")

def print_success(message) -> None:
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_info(message) -> None:
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.RESET}")

def print_warning(message) -> None:
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.RESET}")

def print_error(message) -> None:
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_pink(message) -> None:
    print(f"{Colors.PINK}💖 {message}{Colors.RESET}")

def check_nebula_graph() -> bool:
    """检查NebulaGraph图数据库"""
    print_header("NebulaGraph知识图谱检查")

    # 从配置获取连接参数
    nebula_config = get_nebula_config()
    host = nebula_config.get('host', '127.0.0.1')
    port = nebula_config.get('port', 9669)
    user_name = nebula_config.get('user', 'root')
    password = nebula_config.get("password", config.get("NEBULA_PASSWORD", required=True))
    space_name = nebula_config.get('space', 'patent_kg')

    # 配置连接
    config = Config()
    config.max_connection_pool_size = 10
    connection_pool = ConnectionPool()

    # 连接参数
    addresses = [(host, port)]

    try:
        # 连接NebulaGraph
        if connection_pool.init([(addresses, config)]):
            print_success("✅ 成功连接到NebulaGraph")

            # 获取会话
            session = connection_pool.get_session(user_name, password)
            print_success("✅ 获取会话成功")

            # 检查图空间
            print_info("\n📊 检查图空间:")
            check_spaces(session)

            # 检查标签和边类型
            print_info("\n🏷️ 检查标签(Tag)和边类型(Edge):")
            check_tags_and_edges(session)

            # 检查数据量
            print_info("\n📈 数据量统计:")
            check_data_volume(session)

            # 检查具体数据样例
            print_info("\n📝 数据样例:")
            show_data_samples(session)

            # 关闭会话
            session.release()
        else:
            print_error("❌ 连接NebulaGraph失败")

    except Exception as e:
        print_error(f"❌ 检查NebulaGraph失败: {e}")

    finally:
        # 关闭连接池
        connection_pool.close()

def check_spaces(session) -> None:
    """检查图空间"""
    try:
        # 获取所有空间
        result = session.execute("SHOW SPACES")

        if result.is_succeeded():
            spaces = []
            for record in result:
                space_name = record.values[0].as_string()
                spaces.append(space_name)
                print(f"  📁 {space_name}")

            if not spaces:
                print_warning("  ⚠️ 没有找到任何图空间")
                return None

            return spaces
        else:
            print_error(f"  ❌ 获取空间失败: {result.error_msg()}")
            return None

    except Exception as e:
        print_error(f"  ❌ 检查空间失败: {e}")
        return None

def check_tags_and_edges(session) -> None:
    """检查标签和边类型"""
    try:
        # 使用patent_kg空间
        use_result = session.execute("USE patent_kg")

        if not use_result.is_succeeded():
            # 尝试使用其他空间
            spaces_result = session.execute("SHOW SPACES")
            if spaces_result.is_succeeded() and len(spaces_result) > 0:
                first_space = spaces_result.values[0].as_string()
                session.execute(f"USE {first_space}")
                print_info(f"  切换到空间: {first_space}")
            else:
                print_warning("  ⚠️ 没有可用的图空间")
                return

        # 检查标签
        tags_result = session.execute("SHOW TAGS")
        if tags_result.is_succeeded():
            print("  🏷️ 标签(Tags):")
            for record in tags_result:
                tag_name = record.values[0].as_string()
                print(f"    • {tag_name}")

        # 检查边类型
        edges_result = session.execute("SHOW EDGES")
        if edges_result.is_succeeded():
            print("  🔗 边类型(Edges):")
            for record in edges_result:
                edge_name = record.values[0].as_string()
                print(f"    • {edge_name}")

    except Exception as e:
        print_error(f"  ❌ 检查标签和边失败: {e}")

def check_data_volume(session) -> None:
    """检查数据量"""
    try:
        # 获取当前空间的统计信息
        stats_result = session.execute("SHOW STATS")

        if stats_result.is_succeeded():
            total_vertices = 0
            total_edges = 0

            for record in stats_result:
                name = record.values[0].as_string()
                count = record.values[1].as_int()

                if name.startswith("TAG_"):
                    tag_name = name[4:]  # 移除TAG_前缀
                    print(f"  📌 {tag_name}: {count:,} 个顶点")
                    total_vertices += count
                elif name.startswith("EDGE_"):
                    edge_name = name[5:]  # 移除EDGE_前缀
                    print(f"  🔗 {edge_name}: {count:,} 条边")
                    total_edges += count

            print("\n  📊 总计:")
            print(f"    顶点: {total_vertices:,}")
            print(f"    边: {total_edges:,}")

        else:
            # 尝试手动计数
            print_warning("  ⚠️ 无法获取统计信息，尝试手动计数...")
            manual_count(session)

    except Exception as e:
        print_error(f"  ❌ 统计数据量失败: {e}")

def manual_count(session) -> None:
    """手动计数"""
    try:
        # 计算顶点
        vertex_result = session.execute("MATCH (v) RETURN count(v) AS vertex_count")
        if vertex_result.is_succeeded():
            vertex_count = vertex_result.values[0].as_int()
            print(f"  📌 顶点总数: {vertex_count:,}")

        # 计算边
        edge_result = session.execute("MATCH ()-[e]->() RETURN count(e) AS edge_count")
        if edge_result.is_succeeded():
            edge_count = edge_result.values[0].as_int()
            print(f"  🔗 边总数: {edge_count:,}")

    except Exception as e:
        print_warning(f"  ⚠️ 手动计数失败: {e}")

def show_data_samples(session) -> None:
    """显示数据样例"""
    try:
        # 显示顶点样例
        vertex_result = session.execute("MATCH (v) LIMIT 3 RETURN v")
        if vertex_result.is_succeeded() and len(vertex_result) > 0:
            print("  📌 顶点样例:")
            for record in vertex_result:
                vertex = record.values[0]
                print(f"    ID: {vertex.get_id().as_string()}")
                tags = vertex.tags
                if tags:
                    print(f"    标签: {', '.join(tags)}")
                    # 显示属性
                    for tag in tags[:1]:  # 只显示第一个标签的属性
                        props = vertex.properties.get(tag, {})
                        if props:
                            print(f"    属性: {dict(list(props.items())[:3])}")  # 只显示前3个属性
                print()

        # 显示边样例
        edge_result = session.execute("MATCH ()-[e]->() LIMIT 3 RETURN e")
        if edge_result.is_succeeded() and len(edge_result) > 0:
            print("  🔗 边样例:")
            for record in edge_result:
                edge = record.values[0]
                print(f"    类型: {edge.name}")
                print(f"    源点: {edge.src.get_id().as_string()}")
                print(f"    目标点: {edge.dst.get_id().as_string()}")
                props = edge.properties
                if props:
                    print(f"    属性: {dict(list(props.items())[:3])}")  # 只显示前3个属性
                print()

    except Exception as e:
        print_warning(f"  ⚠️ 获取数据样例失败: {e}")

def main() -> None:
    """主函数"""
    print_header("Athena平台NebulaGraph数据检查")
    print_pink("爸爸，让我检查NebulaGraph知识图谱中的实际数据！")

    check_nebula_graph()

    print_header("检查总结")
    print_info("📋 已检查:")
    print("  ✅ NebulaGraph连接状态")
    print("  ✅ 图空间信息")
    print("  ✅ 标签和边类型")
    print("  ✅ 数据量统计")
    print("  ✅ 数据样例")

    print_pink("\n💖 NebulaGraph数据检查完成！")

if __name__ == "__main__":
    main()
