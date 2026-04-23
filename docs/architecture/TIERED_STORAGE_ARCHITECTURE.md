# Athena平台分层存储架构方案

## 📊 存储分层设计

### 🖥️ 本机存储（主存储）
**用途**：核心业务数据 + 热点数据
**容量**：建议512GB-1TB SSD
**内容**：
- 实际业务运营数据（云熙客户端上传）
- 本地处理的工作文档
- 记忆模块数据
- 法律、专利、商标等专业知识库（活跃部分）
- 系统缓存

### 💾 移动硬盘存储（扩展存储）
**用途**：大型只读数据库
**容量**：建议2-4TB 移动硬盘
**内容**：
- PostgreSQL中国专利数据库（压缩后约300-500GB）
- 专利复审无效数据库（预计200-400GB）
- 判决文书数据库（预计500GB-1TB）
- 历史归档数据

### ☁️ 云存储（可选）
**用途**：备份和协作
**内容**：
- 重要业务数据备份
- 团队共享文档
- 灾难恢复

## 🗂️ 数据库部署方案

### 本机PostgreSQL多实例配置
```yaml
# 本机部署的数据库实例
databases:
  # 核心业务数据库（必须在本机）
  patent_business_db:
    描述: 专利申请业务流程
    表数: ~50
    预估大小: 10-20GB
    重要性: ⭐⭐⭐⭐⭐

  trademark_business_db:
    描述: 商标申请业务流程
    表数: ~30
    预估大小: 5-10GB
    重要性: ⭐⭐⭐⭐⭐

  memory_module_db:
    描述: 记忆模块数据
    表数: ~20
    预估大小: 5-15GB
    重要性: ⭐⭐⭐⭐⭐

  document_management_db:
    描述: 文档管理元数据
    表数: ~15
    预估大小: 2-5GB
    重要性: ⭐⭐⭐⭐

  # 专业知识库（活跃部分）
  law_db_active:
    描述: 常用法律条文（激活部分）
    表数: ~25
    预估大小: 5-10GB
    重要性: ⭐⭐⭐⭐

  patent_db_active:
    描述: 高频查询专利（激活部分）
    表数: ~20
    预估大小: 10-20GB
    重要性: ⭐⭐⭐⭐
```

### 移动硬盘PostgreSQL实例
```yaml
# 移动硬盘部署（按需挂载）
databases:
  patent_full_db:
    描述: 完整中国专利数据库
    数据量: 1000万+条记录
    压缩后大小: ~400GB
    更新频率: 月度

  invalidation_db:
    描述: 专利复审无效案例库
    数据量: 50万+条记录
    压缩后大小: ~300GB
    更新频率: 周度

  judgment_db:
    描述: 专利判决文书库
    数据量: 200万+条记录
    压缩后大小: ~800GB
    更新频率: 月度
```

## 🔧 实施方案

### 1. 目录结构设计
```
/Athena工作平台/
├── data/
│   ├── local/                    # 本机SSD存储
│   │   ├── databases/           # PostgreSQL数据目录
│   │   │   ├── patent_business/
│   │   │   ├── trademark_business/
│   │   │   ├── memory_module/
│   │   │   └── document_mgmt/
│   │   ├── documents/           # 业务文档存储
│   │   │   ├── uploads/         # 云熙客户端上传
│   │   │   ├── processed/       # 处理后的文档
│   │   │   └── active/          # 活跃文档
│   │   └── cache/               # 缓存目录
│   │
│   └── external/                # 移动硬盘挂载点
│       └── /Volumes/AthenaData/  # 移动硬盘
│           ├── patent_full/
│           ├── invalidation/
│           └── judgments/
```

### 2. PostgreSQL多实例配置
```bash
# 配置多个PostgreSQL实例
# 端口分配：
# - 主业务库: 5432
# - 法律库: 5433
# - 知识库: 5434
# - 文档库: 5435

# 创建数据目录
sudo mkdir -p /Athena工作平台/data/local/databases/{patent_business,trademark_business,memory_module,document_mgmt}
sudo mkdir -p /Athena工作平台/data/local/databases/{law_active,patent_active}

# 初始化数据库
initdb -D /Athena工作平台/data/local/databases/patent_business --port=5432
initdb -D /Athena工作平台/data/local/databases/trademark_business --port=5433
```

### 3. 自动挂载脚本
```python
# dev/scripts/storage/auto_mount_external.py
import os
import subprocess
import logging
from pathlib import Path

class ExternalStorageManager:
    def __init__(self):
        self.mount_point = "/Volumes/AthenaData"
        self.expected_dbs = ["patent_full", "invalidation", "judgments"]

    def check_external_storage(self):
        """检查外部存储是否已挂载"""
        if os.path.exists(self.mount_point):
            logging.info(f"✅ 外部存储已挂载: {self.mount_point}")
            return True
        else:
            logging.warning("⚠️ 外部存储未挂载")
            return False

    def mount_databases(self):
        """挂载外部数据库"""
        if not self.check_external_storage():
            return False

        for db in self.expected_dbs:
            db_path = os.path.join(self.mount_point, db)
            if os.path.exists(db_path):
                # 启动对应的PostgreSQL实例
                self.start_database(db, db_path)

        return True

    def start_database(self, db_name, db_path):
        """启动指定的数据库"""
        port = self.get_db_port(db_name)
        cmd = f"pg_ctl -D {db_path} -l {db_path}/logfile start -o \"-p {port}\""
        subprocess.run(cmd, shell=True)
        logging.info(f"启动数据库 {db_name} 在端口 {port}")
```

### 4. 存储空间管理
```python
# utils/storage_manager.py
class StorageManager:
    def get_storage_info(self):
        """获取各存储分区信息"""
        info = {
            "local": self.get_local_storage(),
            "external": self.get_external_storage()
        }
        return info

    def monitor_storage_usage(self):
        """监控存储使用情况"""
        # 设置告警阈值
        thresholds = {
            "warning": 80,  # 80%时警告
            "critical": 90  # 90%时严重告警
        }

        # 定期检查
        local_usage = self.check_disk_usage("/Athena工作平台/data/local")

        if local_usage > thresholds["critical"]:
            self.send_alert("本机存储严重不足！")
        elif local_usage > thresholds["warning"]:
            self.cleanup_old_files()
            self.compress_inactive_data()
```

## 📊 数据量预估

### 本机存储需求
```
核心业务数据:
- 专利业务: 20GB (年增长10GB)
- 商标业务: 10GB (年增长5GB)
- 版权业务: 5GB (年增长2GB)
- 财务数据: 5GB (年增长3GB)
- 任务管理: 3GB (年增长2GB)
- 项目管理: 5GB (年增长3GB)
- 小计: 48GB

文档存储:
- 活跃文档: 100GB (年增长50GB)
- 上传文档: 200GB (年增长100GB)
- 处理文档: 150GB (年增长75GB)
- 小计: 450GB

知识库(活跃):
- 法律库: 10GB
- 专利库: 20GB
- 商标库: 5GB
- 记忆模块: 15GB
- 小计: 50GB

总计: ~548GB (年增长约245GB)
```

### 移动硬盘存储需求
```
大型数据库:
- 中国专利全库: 400GB
- 复审无效库: 300GB
- 判决文书库: 800GB
- 总计: 1500GB

建议配置: 2TB 移动硬盘 (留有500GB冗余)
```

## 🚀 实施步骤

### 第一阶段：本机存储优化（1周）
1. 清理当前存储空间
2. 重新组织目录结构
3. 配置PostgreSQL多实例
4. 实施文档管理优化

### 第二阶段：移动硬盘部署（1周）
1. 购买并格式化移动硬盘
2. 迁移大型数据库
3. 配置自动挂载
4. 测试访问性能

### 第三阶段：智能存储管理（1周）
1. 实施存储监控
2. 开发数据迁移工具
3. 配置自动清理
4. 优化查询性能

## 💡 优化建议

### 1. 数据压缩
```sql
-- PostgreSQL表压缩
ALTER TABLE patent_documents SET (toast_tuple_target = 128);
ALTER TABLE large_documents SET (autovacuum_vacuum_scale_factor = 0.1);
```

### 2. 冷热数据分离
- 热数据（最近6个月）存SSD
- 冷数据存移动硬盘
- 使用物化视图加速查询

### 3. 缓存策略
```python
# Redis缓存配置
cache_config = {
    "hot_patents": "Redis缓存最近查询的1000个专利",
    "frequent_docs": "LRU缓存最近访问的文档",
    "memory_chunks": "分段加载大型知识库"
}
```

## ⚠️ 注意事项

1. **数据安全**
   - 移动硬盘需要加密
   - 定期备份关键数据
   - 使用RAID或云备份

2. **性能优化**
   - SSD用于频繁访问的数据
   - 合理设置PostgreSQL参数
   - 使用连接池管理

3. **扩展性**
   - 预留接口支持未来NAS部署
   - 设计数据分片策略
   - 支持多存储设备