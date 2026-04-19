#!/usr/bin/env python3
from __future__ import annotations
"""
快速部署ArangoDB - 使用Docker
"""

import os
import subprocess
import time


def run_command(cmd, check=True):
    """运行命令"""
    print(f"执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"错误: {result.stderr}")
        return False
    return True

def main():
    print("🚀 快速部署ArangoDB...")

    # 检查Docker
    if not run_command("docker --version", check=False):
        print("❌ Docker未安装，请先安装Docker")
        return

    # 清理旧容器
    run_command("docker stop athena-arangodb 2>/dev/null || true", check=False)
    run_command("docker rm athena-arangodb 2>/dev/null || true", check=False)

    # 创建数据目录
    data_dir = os.path.expanduser("~/arangodb_data")
    os.makedirs(data_dir, exist_ok=True)
    print(f"✅ 数据目录: {data_dir}")

    # 启动ArangoDB
    docker_cmd = f"""
    docker run -d \
        --name athena-arangodb \
        -p 8529:8529 \
        -e ARANGO_ROOT_PASSWORD="" \
        -e ARANGO_NO_AUTH=1 \
        -v {data_dir}:/var/lib/arangodb3 \
        --restart unless-stopped \
        arangodb/arangodb:3.11
    """

    if run_command(docker_cmd):
        print("✅ ArangoDB容器启动中...")

        # 等待启动
        for i in range(30):
            print(f"等待启动... ({i+1}/30)")
            time.sleep(2)

            # 检查容器状态
            result = subprocess.run(
                "docker ps | grep athena-arangodb",
                shell=True,
                capture_output=True
            )

            if "athena-arangodb" in result.stdout.decode():
                print("✅ ArangoDB启动成功！")
                print("\n📊 访问地址:")
                print("  Web UI: http://localhost:8528")
                print("  API: http://localhost:8529/_db/athena_kg/_admin/aardvark/index.html")

                # 安装Python依赖
                print("\n📦 安装Python依赖...")
                run_command("pip3 install python-arango")

                # 创建数据库
                print("\n🗄️ 创建数据库...")
                create_db_script = '''
from arango import ArangoClient
try:
    client = ArangoClient('http://localhost:8529')
    sys_db = client.db('_system', username='root', password='')
    if not sys_db.has_database('athena_kg'):
        sys_db.create_database('athena_kg')
        print("✅ 数据库创建成功")
    else:
        print("ℹ️  数据库已存在")
    print("🎉 ArangoDB部署完成！")
except Exception as e:
    print(f"❌ 错误: {e}")
'''

                with open('/tmp/create_db.py', 'w') as f:
                    f.write(create_db_script)

                run_command("python3 /tmp/create_db.py")
                break
        else:
            print("❌ 启动超时，请检查Docker日志")
            run_command("docker logs athena-arangodb")

if __name__ == "__main__":
    main()
