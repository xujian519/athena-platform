#!/usr/bin/env python3
"""
Athena工作平台生产环境存储系统验证器
Production Environment Storage System Validator
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)

import numpy as np
import psycopg2
import redis
import requests
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

# 设置路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent))

class StorageSystemValidator:
    """存储系统验证器"""

    def __init__(self):
        self.session_id = f"storage_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_results = {
            "postgresql": {"status": "unknown", "details": {}, "dev/tests": []},
            "redis": {"status": "unknown", "details": {}, "dev/tests": []},
            "elasticsearch": {"status": "unknown", "details": {}, "dev/tests": []},
            "qdrant": {"status": "unknown", "details": {}, "dev/tests": []},
            "memory_system": {"status": "unknown", "details": {}, "dev/tests": []},
            "file_system": {"status": "unknown", "details": {}, "dev/tests": []}
        }

        # 配置信息
        self.db_config = {
            "postgresql": {
                "host": "localhost",
                "port": 5432,
                "infrastructure/infrastructure/database": "athena",
                "user": "postgres",
                "password": ""
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0
            },
            "elasticsearch": {
                "host": "localhost",
                "port": 9200
            },
            "qdrant": {
                "host": "localhost",
                "port": 6333
            }
        }

        # 测试数据
        self.test_data = {
            "test_id": f"test_{int(time.time())}",
            "test_vector": np.random.random(768).tolist(),
            "test_metadata": {
                "title": "测试专利",
                "description": "这是一个用于验证存储系统的测试专利",
                "category": "test",
                "timestamp": datetime.now().isoformat()
            }
        }

    def print_pink(self, message: str):
        """打印粉色消息"""
        print(f"💖 {message}")

    def print_success(self, message: str):
        """打印成功消息"""
        print(f"✅ {message}")

    def print_info(self, message: str):
        """打印信息消息"""
        print(f"ℹ️ {message}")

    def print_warning(self, message: str):
        """打印警告消息"""
        print(f"⚠️  {message}")

    def print_error(self, message: str):
        """打印错误消息"""
        print(f"❌ {message}")

    async def validate_postgresql(self) -> dict[str, Any]:
        """验证PostgreSQL数据库"""
        self.print_info("🔍 验证PostgreSQL数据库...")
        result = {"status": "unknown", "details": {}, "dev/tests": []}

        try:
            # 测试连接
            conn = psycopg2.connect(**self.db_config["postgresql"])
            cursor = conn.cursor()

            # 测试1: 基本连接
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            result["dev/tests"].append({
                "name": "数据库连接",
                "status": "success",
                "details": f"PostgreSQL {version.split()[1]}"
            })
            self.print_success("✅ PostgreSQL连接成功")

            # 测试2: 检查数据库结构
            cursor.execute("""
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            result["dev/tests"].append({
                "name": "数据库结构",
                "status": "success",
                "details": f"发现 {len(tables)} 个表"
            })
            self.print_info(f"📊 发现 {len(tables)} 个数据表")

            # 测试3: 数据写入测试
            test_table = "storage_validation_test"
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {test_table} (
                    id SERIAL PRIMARY KEY,
                    test_id VARCHAR(100),
                    data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute(f"""
                INSERT INTO {test_table} (test_id, data)
                VALUES (%s, %s);
            """, (self.test_data["test_id"], json.dumps(self.test_data["test_metadata"])))

            # 测试4: 数据读取测试
            cursor.execute(f"SELECT * FROM {test_table} WHERE test_id = %s;", (self.test_data["test_id"],))
            inserted_data = cursor.fetchone()
            if inserted_data:
                result["dev/tests"].append({
                    "name": "数据读写",
                    "status": "success",
                    "details": "写入和读取测试通过"
                })
                self.print_success("✅ 数据读写测试通过")

            # 清理测试数据
            cursor.execute(f"DROP TABLE IF EXISTS {test_table};")
            conn.commit()

            # 获取数据库统计
            cursor.execute("""
                SELECT
                    pg_size_pretty(pg_database_size(current_database())) as db_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections;
            """)
            stats = cursor.fetchone()
            result["details"] = {
                "database_size": stats[0],
                "active_connections": stats[1],
                "tables_count": len(tables)
            }

            cursor.close()
            conn.close()

            result["status"] = "healthy"

        except Exception as e:
            result["status"] = "error"
            result["dev/tests"].append({
                "name": "数据库连接",
                "status": "failed",
                "details": str(e)
            })
            self.print_error(f"❌ PostgreSQL验证失败: {e}")

        return result

    async def validate_redis(self) -> dict[str, Any]:
        """验证Redis缓存"""
        self.print_info("🔍 验证Redis缓存...")
        result = {"status": "unknown", "details": {}, "dev/tests": []}

        try:
            # 测试连接
            r = redis.Redis(**self.db_config["redis"])

            # 测试1: 基本连接
            pong = r.ping()
            if pong:
                result["dev/tests"].append({
                    "name": "Redis连接",
                    "status": "success",
                    "details": "PONG响应正常"
                })
                self.print_success("✅ Redis连接成功")

            # 测试2: 数据写入
            test_key = f"test:{self.test_data['test_id']}"
            r.set(test_key, json.dumps(self.test_data["test_metadata"]))

            # 测试3: 数据读取
            stored_data = r.get(test_key)
            if stored_data:
                result["dev/tests"].append({
                    "name": "缓存读写",
                    "status": "success",
                    "details": "缓存读写测试通过"
                })
                self.print_success("✅ 缓存读写测试通过")

            # 测试4: 过期时间
            r.setex(f"expire_test:{self.test_data['test_id']}", 60, "expire_test")
            ttl = r.ttl(f"expire_test:{self.test_data['test_id']}")
            result["dev/tests"].append({
                "name": "过期时间",
                "status": "success",
                "details": f"TTL设置正常: {ttl}秒"
            })

            # 获取Redis信息
            info = r.info()
            result["details"] = {
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses")
            }

            # 清理测试数据
            r.delete(test_key)
            r.delete(f"expire_test:{self.test_data['test_id']}")

            result["status"] = "healthy"

        except Exception as e:
            result["status"] = "error"
            result["dev/tests"].append({
                "name": "Redis连接",
                "status": "failed",
                "details": str(e)
            })
            self.print_error(f"❌ Redis验证失败: {e}")

        return result

    async def validate_elasticsearch(self) -> dict[str, Any]:
        """验证Elasticsearch"""
        self.print_info("🔍 验证Elasticsearch...")
        result = {"status": "unknown", "details": {}, "dev/tests": []}

        try:
            # 测试连接
            es_url = f"http://{self.db_config['elasticsearch']['host']}:{self.db_config['elasticsearch']['port']}"

            # 测试1: 集群健康
            response = requests.get(f"{es_url}/_cluster/health", timeout=10)
            if response.status_code == 200:
                health = response.json()
                result["dev/tests"].append({
                    "name": "集群健康",
                    "status": "success",
                    "details": f"状态: {health['status']}, 节点数: {health['number_of_nodes']}"
                })
                self.print_success("✅ Elasticsearch集群健康")

            # 测试2: 索引操作
            test_index = f"storage_validation_{self.test_data['test_id']}"

            # 创建测试索引
            index_mapping = {
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "description": {"type": "text"},
                        "category": {"type": "keyword"},
                        "timestamp": {"type": "date"}
                    }
                }
            }

            response = requests.put(f"{es_url}/{test_index}", json=index_mapping, timeout=10)
            if response.status_code in [200, 201]:
                result["dev/tests"].append({
                    "name": "索引创建",
                    "status": "success",
                    "details": "测试索引创建成功"
                })

            # 测试3: 文档写入
            doc_response = requests.post(
                f"{es_url}/{test_index}/_doc/1",
                json=self.test_data["test_metadata"],
                timeout=10
            )
            if doc_response.status_code in [200, 201]:
                result["dev/tests"].append({
                    "name": "文档写入",
                    "status": "success",
                    "details": "文档写入成功"
                })
                self.print_success("✅ 文档写入测试通过")

            # 测试4: 文档搜索
            search_response = requests.get(
                f"{es_url}/{test_index}/_search",
                json={"query": {"match": {"title": "测试"}}},
                timeout=10
            )
            if search_response.status_code == 200:
                search_results = search_response.json()
                hits = search_results.get("hits", {}).get("total", {}).get("value", 0)
                result["dev/tests"].append({
                    "name": "文档搜索",
                    "status": "success",
                    "details": f"搜索到 {hits} 个结果"
                })

            # 获取集群信息
            response = requests.get(f"{es_url}/_cluster/stats", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                result["details"] = {
                    "cluster_name": stats.get("cluster_name"),
                    "nodes_count": stats.get("nodes", {}).get("count", {}).get("total"),
                    "indices_count": stats.get("indices", {}).get("count"),
                    "store_size": stats.get("indices", {}).get("store", {}).get("size_in_bytes")
                }

            # 清理测试数据
            requests.delete(f"{es_url}/{test_index}", timeout=10)

            result["status"] = "healthy"

        except Exception as e:
            result["status"] = "error"
            result["dev/tests"].append({
                "name": "Elasticsearch连接",
                "status": "failed",
                "details": str(e)
            })
            self.print_error(f"❌ Elasticsearch验证失败: {e}")

        return result

    async def validate_qdrant(self) -> dict[str, Any]:
        """验证Qdrant向量数据库"""
        self.print_info("🔍 验证Qdrant向量数据库...")
        result = {"status": "unknown", "details": {}, "dev/tests": []}

        try:
            # 测试连接
            client = QdrantClient(
                host=self.db_config["qdrant"]["host"],
                port=self.db_config["qdrant"]["port"]
            )

            # 测试1: 基本连接
            collections = client.get_collections()
            result["dev/tests"].append({
                "name": "Qdrant连接",
                "status": "success",
                "details": f"连接成功，当前有 {len(collections.collections)} 个集合"
            })
            self.print_success("✅ Qdrant连接成功")

            # 测试2: 创建集合
            collection_name = f"storage_validation_{self.test_data['test_id']}"

            try:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
                result["dev/tests"].append({
                    "name": "集合创建",
                    "status": "success",
                    "details": f"创建集合 {collection_name} 成功"
                })
                self.print_success("✅ 向量集合创建成功")

            except Exception as e:
                if "already exists" not in str(e):
                    raise e

            # 测试3: 向量写入
            point = PointStruct(
                id=1,
                vector=self.test_data["test_vector"],
                payload=self.test_data["test_metadata"]
            )

            client.upsert(
                collection_name=collection_name,
                points=[point]
            )

            result["dev/tests"].append({
                "name": "向量写入",
                "status": "success",
                "details": "向量数据写入成功"
            })
            self.print_success("✅ 向量写入测试通过")

            # 测试4: 向量搜索
            search_result = client.search(
                collection_name=collection_name,
                query_vector=self.test_data["test_vector"],
                limit=1
            )

            if search_result:
                result["dev/tests"].append({
                    "name": "向量搜索",
                    "status": "success",
                    "details": f"搜索到 {len(search_result)} 个结果，相似度: {search_result[0].score:.4f}"
                })
                self.print_success("✅ 向量搜索测试通过")

            # 获取集合信息
            collection_info = client.get_collection(collection_name)
            result["details"] = {
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status
            }

            # 清理测试数据
            client.delete_collection(collection_name)

            result["status"] = "healthy"

        except Exception as e:
            result["status"] = "error"
            result["dev/tests"].append({
                "name": "Qdrant连接",
                "status": "failed",
                "details": str(e)
            })
            self.print_error(f"❌ Qdrant验证失败: {e}")

        return result

    async def validate_memory_system(self) -> dict[str, Any]:
        """验证四层记忆系统"""
        self.print_info("🔍 验证四层记忆系统...")
        result = {"status": "unknown", "details": {}, "dev/tests": []}

        try:
            memory_base = project_root / "core" / "modules/modules/memory/modules/memory/modules/memory/memory"

            # 测试1: 检查记忆层级目录
            required_layers = ["hot_memories", "warm_memories", "cold_memories", "eternal_memories"]
            existing_layers = []

            for layer in required_layers:
                layer_path = memory_base / layer
                if layer_path.exists():
                    memory_files = list(layer_path.glob("*.json"))
                    if memory_files:
                        existing_layers.append({
                            "layer": layer,
                            "files_count": len(memory_files),
                            "size_mb": sum(f.stat().st_size for f in memory_files) / 1024 / 1024
                        })
                        result["dev/tests"].append({
                            "name": f"{layer}检查",
                            "status": "success",
                            "details": f"{len(memory_files)} 个记忆文件"
                        })
                        self.print_success(f"✅ {layer} - {len(memory_files)} 个记忆文件")
                    else:
                        result["dev/tests"].append({
                            "name": f"{layer}检查",
                            "status": "warning",
                            "details": "目录存在但无记忆文件"
                        })
                        self.print_warning(f"⚠️  {layer} - 目录存在但无记忆文件")
                else:
                    result["dev/tests"].append({
                        "name": f"{layer}检查",
                        "status": "failed",
                        "details": "目录不存在"
                    })
                    self.print_error(f"❌ {layer} - 目录不存在")

            # 测试2: 检查记忆连接网络
            memory_network_file = memory_base / "memory_network.json"
            if memory_network_file.exists():
                with open(memory_network_file, encoding='utf-8') as f:
                    network_data = json.load(f)

                result["dev/tests"].append({
                    "name": "记忆连接网络",
                    "status": "success",
                    "details": f"网络包含 {len(network_data)} 个连接"
                })
                self.print_success("✅ 记忆连接网络已建立")

                # 测试3: 验证记忆文件格式
                sample_files = []
                for layer_info in existing_layers:
                    layer_path = memory_base / layer_info["layer"]
                    files = list(layer_path.glob("*.json"))
                    if files:
                        sample_files.append(files[0])

                valid_files = 0
                for file_path in sample_files[:3]:  # 检查前3个文件
                    try:
                        with open(file_path, encoding='utf-8') as f:
                            memory_data = json.load(f)

                        required_fields = ["id", "content", "timestamp"]
                        if all(field in memory_data for field in required_fields):
                            valid_files += 1
                    except Exception as e:
                        logger.debug(f"空except块已触发: {e}")
                        pass

                result["dev/tests"].append({
                    "name": "记忆文件格式",
                    "status": "success",
                    "details": f"{valid_files}/{len(sample_files)} 文件格式正确"
                })

            # 计算记忆系统健康度
            memory_health = (len(existing_layers) / len(required_layers)) * 100
            result["details"] = {
                "total_layers": len(required_layers),
                "existing_layers": len(existing_layers),
                "health_percentage": memory_health,
                "total_files": sum(layer["files_count"] for layer in existing_layers),
                "total_size_mb": round(sum(layer["size_mb"] for layer in existing_layers), 2)
            }

            if memory_health >= 75:
                result["status"] = "healthy"
            elif memory_health >= 50:
                result["status"] = "warning"
            else:
                result["status"] = "error"

        except Exception as e:
            result["status"] = "error"
            result["dev/tests"].append({
                "name": "记忆系统检查",
                "status": "failed",
                "details": str(e)
            })
            self.print_error(f"❌ 记忆系统验证失败: {e}")

        return result

    async def validate_file_system(self) -> dict[str, Any]:
        """验证文件系统"""
        self.print_info("🔍 验证文件系统...")
        result = {"status": "unknown", "details": {}, "dev/tests": []}

        try:
            production_path = project_root / "production"

            # 测试1: 检查关键目录
            critical_dirs = [
                "logs",
                "cache",
                "data",
                "config",
                "dev/scripts",
                "backups"
            ]

            for dir_name in critical_dirs:
                dir_path = production_path / dir_name
                if dir_path.exists() and dir_path.is_dir():
                    result["dev/tests"].append({
                        "name": f"{dir_name}目录",
                        "status": "success",
                        "details": "目录存在且可访问"
                    })
                else:
                    result["dev/tests"].append({
                        "name": f"{dir_name}目录",
                        "status": "warning",
                        "details": "目录不存在"
                    })

            # 测试2: 检查磁盘空间
            if psutil is None:
                result["dev/tests"].append({
                    "name": "磁盘空间",
                    "status": "warning",
                    "details": "psutil未安装，无法检查磁盘空间"
                })
            else:
                disk_usage = psutil.disk_usage(str(project_root))
                free_space_gb = disk_usage.free / 1024 / 1024 / 1024
                total_space_gb = disk_usage.total / 1024 / 1024 / 1024
                usage_percent = (disk_usage.used / disk_usage.total) * 100

                result["dev/tests"].append({
                    "name": "磁盘空间",
                    "status": "success" if usage_percent < 90 else "warning",
                    "details": f"使用率 {usage_percent:.1f}%, 剩余 {free_space_gb:.1f}GB"
                })

            # 测试3: 检查文件权限
            test_file = production_path / "permission_test.tmp"
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                result["dev/tests"].append({
                    "name": "文件权限",
                    "status": "success",
                    "details": "读写权限正常"
                })
            except Exception as e:
                result["dev/tests"].append({
                    "name": "文件权限",
                    "status": "failed",
                    "details": str(e)
                })

            # 计算目录大小
            total_size = 0
            for root, _dirs, files in os.walk(production_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except Exception as e:
                        logger.debug(f"跳过不可访问文件: {e}")
                        pass

            result["details"] = {
                "total_size_gb": round(total_size / 1024 / 1024 / 1024, 2),
                "disk_usage_percent": round(usage_percent, 1),
                "free_space_gb": round(free_space_gb, 1),
                "total_space_gb": round(total_space_gb, 1)
            }

            result["status"] = "healthy"

        except Exception as e:
            result["status"] = "error"
            result["dev/tests"].append({
                "name": "文件系统检查",
                "status": "failed",
                "details": str(e)
            })
            self.print_error(f"❌ 文件系统验证失败: {e}")

        return result

    async def run_comprehensive_validation(self):
        """运行综合验证"""
        print("🌸🐟 Athena工作平台生产环境存储系统验证器")
        print("=" * 60)
        print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"会话ID: {self.session_id}")
        print("")

        # 依次验证各个存储系统
        validation_tasks = [
            ("PostgreSQL数据库", self.validate_postgresql),
            ("Redis缓存", self.validate_redis),
            ("Elasticsearch", self.validate_elasticsearch),
            ("Qdrant向量数据库", self.validate_qdrant),
            ("四层记忆系统", self.validate_memory_system),
            ("文件系统", self.validate_file_system)
        ]

        for system_name, validator_func in validation_tasks:
            print(f"\n🔍 验证 {system_name}...")
            try:
                result = await validator_func()
                self.test_results[result.__class__.__name__ if 'result' in locals() else system_name.lower().replace(' ', '_')] = result
            except Exception as e:
                self.print_error(f"❌ {system_name} 验证异常: {e}")
                self.test_results[system_name.lower().replace(' ', '_')] = {
                    "status": "error",
                    "details": {"error": str(e)},
                    "dev/tests": []
                }

        # 生成验证报告
        await self.generate_validation_report()

    async def generate_validation_report(self):
        """生成验证报告"""
        print("\n" + "=" * 60)
        print("📊 存储系统验证结果摘要")
        print("=" * 60)

        # 统计结果
        total_systems = len(self.test_results)
        healthy_systems = sum(1 for result in self.test_results.values() if result["status"] == "healthy")
        warning_systems = sum(1 for result in self.test_results.values() if result["status"] == "warning")
        error_systems = sum(1 for result in self.test_results.values() if result["status"] == "error")

        overall_score = (healthy_systems / total_systems) * 100

        print(f"🎯 总体评分: {overall_score:.1f}%")
        print(f"✅ 健康系统: {healthy_systems}/{total_systems}")
        print(f"⚠️  警告系统: {warning_systems}/{total_systems}")
        print(f"❌ 错误系统: {error_systems}/{total_systems}")

        # 详细结果
        print("\n📋 详细验证结果:")
        for system_name, result in self.test_results.items():
            status_icon = {
                "healthy": "✅",
                "warning": "⚠️ ",
                "error": "❌",
                "unknown": "❓"
            }.get(result["status"], "❓")

            print(f"   {status_icon} {system_name}: {result['status'].upper()}")

            if result["dev/tests"]:
                passed_tests = sum(1 for test in result["dev/tests"] if test["status"] == "success")
                total_tests = len(result["dev/tests"])
                print(f"      测试通过: {passed_tests}/{total_tests}")

        # 保存报告
        report = {
            "validation_metadata": {
                "session_id": self.session_id,
                "validation_time": datetime.now().isoformat(),
                "overall_score": overall_score,
                "total_systems": total_systems,
                "healthy_systems": healthy_systems,
                "warning_systems": warning_systems,
                "error_systems": error_systems
            },
            "detailed_results": self.test_results,
            "recommendations": self.generate_recommendations()
        }

        # 保存JSON报告
        logs_dir = project_root / "production" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        report_file = logs_dir / f"storage_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n📄 验证报告已保存: {report_file.name}")

        # 最终评估
        if overall_score >= 90:
            self.print_pink("🎉 存储系统验证优秀！系统完全可用！")
        elif overall_score >= 75:
            self.print_success("👍 存储系统验证良好！基本可用！")
        elif overall_score >= 50:
            self.print_warning("⚠️  存储系统验证一般，需要注意！")
        else:
            self.print_error("❌ 存储系统验证失败，需要修复！")

    def generate_recommendations(self) -> list[str]:
        """生成优化建议"""
        recommendations = []

        for system_name, result in self.test_results.items():
            if result["status"] == "error":
                recommendations.append(f"紧急修复 {system_name} - 系统不可用")
            elif result["status"] == "warning":
                recommendations.append(f"关注 {system_name} - 存在潜在问题")

        if not recommendations:
            recommendations.append("存储系统运行良好，建议定期检查和维护")

        return recommendations

async def main():
    """主函数"""
    validator = StorageSystemValidator()
    await validator.run_comprehensive_validation()

if __name__ == "__main__":
    asyncio.run(main())
