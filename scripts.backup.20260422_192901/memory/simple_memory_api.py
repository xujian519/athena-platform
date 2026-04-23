#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena记忆系统API服务
Athena Memory System API Service

智能记忆管理和知识检索系统
"""

import sys
from pathlib import Path
import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.security.auth import ALLOWED_ORIGINS
from pydantic import BaseModel

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入身份管理器
try:
    from core.utils.agent_identity_manager import identity_manager
except ImportError:
    identity_manager = None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI应用
app = FastAPI(
    title="Athena记忆系统API",
    description="智能记忆管理和知识检索系统",
    version="2.0.0"
)

# 记忆系统身份信息
memory_identity = {
    "name": "Athena记忆系统",
    "role": "智能记忆管家",
    "title": "永久记忆与知识守护者",
    "slogan": "记录每一个重要瞬间，守护每一段珍贵记忆，让知识与情感在时光中永恒。",
    "motto": "记忆永恒，智慧传承",
    "color": "🧠"
}

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL连接信息
PSQL_PATH = '/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql'
DB_HOST = 'localhost'
DB_PORT = '5438'
DB_NAME = 'memory_module'

@app.get("/")
async def root():
    """主页 - 展示记忆系统身份信息"""
    return {
        "service": f"{memory_identity['color']} {memory_identity['name']} - {memory_identity['title']}",
        "role": memory_identity["role"],
        "slogan": memory_identity["slogan"],
        "motto": memory_identity["motto"],
        "version": "2.0.0",
        "port": 8003,
        "capabilities": [
            "💾 知识存储",
            "🔍 智能检索",
            "📝 记忆管理",
            "🧠 学习分析",
            "📊 数据统计",
            "🔄 记忆同步"
        ],
        "message": "Athena记忆系统已启动，准备守护您的珍贵记忆！",
        "status": "运行中",
        "timestamp": datetime.now().isoformat()
    }

# 请求模型
class MemoryStoreRequest(BaseModel):
    agent_id: str
    content: str
    memory_type: str
    importance: float = 0.5
    tags: List[str] = []

class MemoryRecallRequest(BaseModel):
    agent_id: str
    query: str
    limit: int = 10

# 健康检查
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "memory_system",
        "version": "1.0.0"
    }

# 存储记忆
@app.post("/api/memory/store")
async def store_memory(request: MemoryStoreRequest):
    """存储记忆到PostgreSQL"""
    try:
        # 构建JSON元数据
        import json
        from datetime import datetime

        metadata = {
            "source": "api",
            "timestamp": datetime.now().isoformat()
        }
        metadata_str = json.dumps(metadata).replace('"', '\\"')

        # 构建SQL
        sql = f"""
        INSERT INTO memory_items (
            agent_id, agent_type, content, memory_type, memory_tier,
            importance, tags, metadata, created_at, updated_at
        ) VALUES (
            '{request.agent_id}',
            'athena',
            '{request.content.replace("'", "''")}',
            '{request.memory_type}',
            CASE WHEN {request.importance} >= 0.9 THEN 'eternal'
                 WHEN {request.importance} >= 0.7 THEN 'hot'
                 WHEN {request.importance} >= 0.5 THEN 'warm'
                 ELSE 'cold' END,
            {request.importance},
            ARRAY[{', '.join([f"'{tag}'" for tag in request.tags])}],
            '{metadata_str}',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        );
        """

        # 执行SQL
        cmd = [
            PSQL_PATH,
            '-h', DB_HOST,
            '-p', DB_PORT,
            '-d', DB_NAME,
            '-c', sql
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"成功存储记忆: agent_id={request.agent_id}")
            return {"status": "success", "message": "记忆存储成功"}
        else:
            logger.error(f"存储记忆失败: {result.stderr}")
            raise HTTPException(status_code=500, detail="记忆存储失败")

    except Exception as e:
        logger.error(f"存储记忆错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 检索记忆
@app.post("/api/memory/recall")
async def recall_memory(request: MemoryRecallRequest):
    """从PostgreSQL检索记忆"""
    try:
        # 构建查询SQL
        sql = f"""
        SELECT content, memory_type, importance, created_at
        FROM memory_items
        WHERE agent_id = '{request.agent_id}'
        AND (content ILIKE '%{request.query}%'
             OR '{request.query}' = ANY(tags))
        ORDER BY importance DESC, created_at DESC
        LIMIT {request.limit};
        """

        # 执行查询
        cmd = [
            PSQL_PATH,
            '-h', DB_HOST,
            '-p', DB_PORT,
            '-d', DB_NAME,
            '-c', sql
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            # 解析结果
            lines = result.stdout.strip().split('\n')
            memories = []

            # 跳过头部，每3行是一个记录
            for i in range(2, len(lines), 3):
                if i + 2 < len(lines):
                    memories.append({
                        "content": lines[i].strip(),
                        "memory_type": lines[i+1].strip() if i+1 < len(lines) else "",
                        "importance": float(lines[i+2].strip()) if i+2 < len(lines) else 0.0
                    })

            return {
                "status": "success",
                "count": len(memories),
                "memories": memories
            }
        else:
            logger.error(f"检索记忆失败: {result.stderr}")
            return {"status": "success", "count": 0, "memories": []}

    except Exception as e:
        logger.error(f"检索记忆错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取记忆统计
@app.get("/api/memory/stats")
async def get_memory_stats():
    """获取记忆系统统计"""
    try:
        # 获取总记忆数
        total_sql = "SELECT COUNT(*) FROM memory_items;"
        cmd = [PSQL_PATH, '-h', DB_HOST, '-p', DB_PORT, '-d', DB_NAME, '-c', total_sql]
        result = subprocess.run(cmd, capture_output=True, text=True)

        total_count = 0
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 3:
                try:
                    total_count = int(lines[2].strip())
                except:
                    pass

        # 按类型统计
        type_sql = "SELECT memory_type, COUNT(*) FROM memory_items GROUP BY memory_type;"
        cmd = [PSQL_PATH, '-h', DB_HOST, '-p', DB_PORT, '-d', DB_NAME, '-c', type_sql]
        result = subprocess.run(cmd, capture_output=True, text=True)

        type_stats = {}
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[2:-1]
            for line in lines:
                if ' | ' in line:
                    type_, count = line.split(' | ')
                    type_stats[type_.strip()] = int(count.strip())

        return {
            "status": "success",
            "total_memories": total_count,
            "by_type": type_stats
        }

    except Exception as e:
        logger.error(f"获取统计错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("启动记忆系统API服务...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )