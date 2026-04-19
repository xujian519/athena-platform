#!/usr/bin/env python3
"""
NebulaGraph专利全文空间设置 - 简化版
使用本地存储配置
"""

from __future__ import annotations
import logging
import subprocess

logger = logging.getLogger(__name__)


def run_cypher_shell(query, description=""):
    """使用cypher-shell执行查询（兼容NebulaGraph）"""
    # 检查NebulaGraph的cypher-shell
    try:
        # 尝试通过docker执行
        cmd = [
            'infrastructure/infrastructure/docker', 'exec', 'athena_nebula_graph_min',
            '/bin/sh', '-c',
            f'echo "{query}" | nc 127.0.0.1 9669'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {description or '查询成功'}")
            return True
        else:
            print(f"⚠️ {description}: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        return False


# 检查是否有现有的NebulaGraph连接工具
def check_tools():
    """检查可用工具"""
    # 1. 检查本地cypher-shell
    try:
        result = subprocess.run(['which', 'cypher-shell'], capture_output=True)
        if result.returncode == 0:
            return 'local_cypher'
    except Exception as e:
        logger.debug(f"空except块已触发: {e}")
        pass

    # 2. 检查docker
    try:
        result = subprocess.run(['infrastructure/infrastructure/docker', 'ps'], capture_output=True)
        if 'nebula' in result.stdout.decode().lower():
            return 'local_docker'
    except Exception as e:
        logger.debug(f"Docker检查失败: {e}")
        pass

    return None


def create_via_http():
    """通过HTTP API创建NebulaGraph空间"""

    # NebulaGraph使用二进制协议，这里简化为记录手动步骤
    print("=" * 70)
    print("🚀 NebulaGraph专利全文知识图谱初始化")
    print("=" * 70)
    print("")
    print("⚠️ NebulaGraph需要手动创建空间")
    print("")
    print("📋 请使用以下方法之一:")
    print("")
    print("方法1: 使用Python脚本")
    print("  pip install nebula3-python")
    print("  python3 -c \"")
    print("    from nebula3.gclient.net import ConnectionPool")
    print("    from nebula3.Config import Config")
    print("    pool = ConnectionPool()")
    print("    pool.init([('127.0.0.1', 9669)], Config())")
    print("    session = pool.get_session('root', 'xiaonuo@Athena')")
    print('    session.execute(\"CREATE SPACE IF NOT EXISTS patent_full_text(partition_num=10, replica_factor=1, vid_type=FIXED_STRING(64));\")')
    print("  \"")
    print("")
    print("方法2: 安装nebula-console")
    print("  wget https://github.com/vesoft-inc/nebula-console/releases/download/v3.6.0/nebula-console-linux-amd64-v3.6.0")
    print("  chmod +x nebula-console-linux-amd64-v3.6.0")
    print("  ./nebula-console-linux-amd64-v3.6.0 -addr 127.0.0.1 -port 9669 -u root -p 'xiaonuo@Athena'")
    print("  > CREATE SPACE IF NOT EXISTS patent_full_text(partition_num=10, replica_factor=1, vid_type=FIXED_STRING(64));")
    print("")
    print("方法3: 使用现有的其他NebulaGraph客户端")
    print("")
    print("📋 创建空间后，还需执行:")
    print("  USE patent_full_text;")
    print("")
    print("  -- 创建TAG")
    print("  CREATE TAG IF NOT EXISTS patent(id string, application_number string, publication_number string, title string, patent_type string, ipc_main_class string, applicant string, inventor string, pdf_path string, vector_id string, source string);")
    print("  CREATE TAG IF NOT EXISTS claim(id string, patent_id string, claim_number int, claim_type string, claim_text string);")
    print("  CREATE TAG IF NOT EXISTS applicant(id string, name string, country string, type string);")
    print("  CREATE TAG IF NOT EXISTS ipc_class(id string, code string, description string);")
    print("")
    print("  -- 创建EDGE")
    print("  CREATE EDGE IF NOT EXISTS HAS_CLAIM(sequence int);")
    print("  CREATE EDGE IF NOT EXISTS HAS_APPLICANT();")
    print("  CREATE EDGE IF NOT EXISTS CITES(citation_type string);")
    print("  CREATE EDGE IF NOT EXISTS FAMILY(family_id string);")
    print("")

    return False


def main():
    """主函数"""
    tool = check_tools()

    if tool:
        print(f"✅ 检测到工具: {tool}")
        print("📋 请手动使用nebula3-python库创建空间:")
        print("")
        print("from nebula3.gclient.net import ConnectionPool")
        print("from nebula3.Config import Config")
        print("")
        print("pool = ConnectionPool()")
        print("pool.init([('127.0.0.1', 9669)], Config())")
        print("session = pool.get_session('root', 'xiaonuo@Athena')")
        print("")
        print("# 创建空间")
        print('session.execute("CREATE SPACE IF NOT EXISTS patent_full_text(partition_num=10, replica_factor=1, vid_type=FIXED_STRING(64));")')
        print("time.sleep(15)  # 等待空间创建完成")
        print("")
        print("# 使用空间")
        print('session.execute("USE patent_full_text;")')
        print("")
        print("# 创建TAG")
        print('session.execute("CREATE TAG IF NOT EXISTS patent(id string, application_number string, publication_number string, title string, patent_type string, ipc_main_class string, applicant string, inventor string, pdf_path string, vector_id string, source string);")')
        print('session.execute("CREATE TAG IF NOT EXISTS claim(id string, patent_id string, claim_number int, claim_type string, claim_text string);")')
        print('session.execute("CREATE TAG IF NOT EXISTS applicant(id string, name string, country string, type string);")')
        print('session.execute("CREATE TAG IF NOT EXISTS ipc_class(id string, code string, description string);")')
        print("")
        print("# 创建EDGE")
        print('session.execute("CREATE EDGE IF NOT EXISTS HAS_CLAIM(sequence int);")')
        print('session.execute("CREATE EDGE IF NOT EXISTS HAS_APPLICANT();")')
        print('session.execute("CREATE EDGE IF NOT EXISTS CITES(citation_type string);")')
        print('session.execute("CREATE EDGE IF NOT EXISTS FAMILY(family_id string);")')
        print("")
        return True
    else:
        return create_via_http()


if __name__ == "__main__":
    main()
