# 手动迁移专利数据库到移动硬盘指南

## 📋 迁移前准备

### 1. 确认源数据库位置
```bash
# 查找专利数据库位置
find /Users/xujian/Athena工作平台 -name "*patent*" -type d | grep database
```

常见位置：
- `/Users/xujian/Athena工作平台/data/local/databases/patent_db`
- `/Users/xujian/Athena工作平台/postgres/data/patent_db`

### 2. 检查数据库大小
```bash
# 查看目录大小
du -sh /path/to/patent_db
```

### 3. 准备移动硬盘
- 确保移动硬盘已连接
- 确认名称为 "AthenaData"
- 检查可用空间（至少240GB）

## 🔧 手动迁移步骤

### 步骤1：停止专利数据库

```bash
# 方法1：如果使用pg_ctl
pg_ctl -D /path/to/patent_db status
pg_ctl -D /path/to/patent_db stop -m fast

# 方法2：查找并停止PostgreSQL进程
ps aux | grep postgres
sudo kill -15 <PID>
```

### 步骤2：创建目标目录

```bash
# 在移动硬盘创建目录
mkdir -p /Volumes/AthenaData/databases
mkdir -p /Volumes/AthenaData/databases/patent_full
```

### 步骤3：复制数据（推荐rsync）

```bash
# 使用rsync（支持断点续传，显示进度）
rsync -avh --progress \
  /Users/xujian/Athena工作平台/data/local/databases/patent_db/ \
  /Volumes/AthenaData/databases/patent_full/
```

**参数说明：**
- `-a` 归档模式，保留所有属性
- `-v` 显示详细信息
- `-h` 人类可读的格式
- `--progress` 显示进度

### 步骤4：配置外部数据库

1. **创建postgresql.conf**
```bash
# 创建或编辑配置文件
nano /Volumes/AthenaData/databases/patent_full/postgresql.conf
```

添加以下内容：
```ini
# 外部存储配置
port = 5450
max_connections = 100
shared_buffers = 512MB
work_mem = 8MB
maintenance_work_mem = 128MB
effective_cache_size = 2GB
```

### 步骤5：创建启动脚本

```bash
# 创建脚本目录
mkdir -p /Users/xujian/Athena工作平台/dev/scripts/databases

# 创建启动脚本
nano /Users/xujian/Athena工作平台/dev/scripts/databases/patent_full.sh
```

脚本内容：
```bash
#!/bin/bash
DB_PATH="/Volumes/AthenaData/databases/patent_full"
PORT=5450
LOG_FILE="$DB_PATH/logfile"

case "$1" in
    start)
        echo "启动外部专利数据库..."
        if [ ! -d "/Volumes/AthenaData" ]; then
            echo "❌ 移动硬盘未挂载"
            exit 1
        fi
        pg_ctl -D "$DB_PATH" -l "$LOG_FILE" start -o "-p $PORT"
        echo "✅ 启动成功 (端口: $PORT)"
        ;;
    stop)
        echo "停止外部专利数据库..."
        pg_ctl -D "$DB_PATH" -m fast stop
        echo "✅ 停止成功"
        ;;
    status)
        pg_ctl -D "$DB_PATH" status
        ;;
    *)
        echo "用法: $0 {start|stop|status}"
        exit 1
        ;;
esac
```

添加执行权限：
```bash
chmod +x /Users/xujian/Athena工作平台/dev/scripts/databases/patent_full.sh
```

### 步骤6：测试启动

```bash
# 启动外部数据库
/Users/xujian/Athena工作平台/dev/scripts/databases/patent_full.sh start

# 检查状态
/Users/xujian/Athena工作平台/dev/scripts/databases/patent_full.sh status
```

### 步骤7：验证数据

```bash
# 连接数据库测试
psql -h localhost -p 5450 -U postgres -d patent_db

# 检查数据
SELECT count(*) FROM patents;  -- 或其他表
\q
```

## 🧹 清理本地数据（可选）

### 选项1：保留备份
```bash
# 重命名原目录
mv /path/to/patent_db /path/to/patent_db_backup
```

### 选项2：压缩备份
```bash
# 创建压缩包
cd /path/to/
tar -czf patent_db_backup.tar.gz patent_db
# 然后删除原目录
rm -rf patent_db
```

### 选项3：直接删除
```bash
# 确保已备份后再执行
rm -rf /path/to/patent_db
```

## 📊 更新应用配置

### 1. 更新数据库连接配置
```python
# 在您的应用配置文件中更新连接信息
PATENT_FULL_DB_CONFIG = {
    "host": "localhost",
    "port": 5450,  # 新端口
    "infrastructure/infrastructure/database": "patent_db",
    "user": "postgres",
    "password": "your_password"
}
```

### 2. 更新路由配置
确保路由器知道如何访问端口5450。

## ⚠️ 注意事项

1. **数据安全**
   - 迁移前先完整备份
   - 确保移动硬盘质量可靠
   - 考虑定期备份数据

2. **性能考虑**
   - USB 3.0或Thunderbolt连接
   - 避免频繁的外部硬盘操作
   - 考虑SSD移动硬盘

3. **自动化提示**
   - 可以创建一个挂载检查脚本
   - 考虑设置自动备份

## 🔄 自动化脚本（可选）

如果需要，可以创建一个简单的挂载检查脚本：

```bash
#!/bin/bash
# check_external_storage.sh
if [ -d "/Volumes/AthenaData" ]; then
    echo "✅ 移动硬盘已挂载"
    # 可以在这里添加自动启动命令
else
    echo "❌ 移动硬盘未挂载"
    # 发送通知或邮件
fi
```

## 📞 故障排除

### 问题1：无法启动数据库
```bash
# 检查日志
cat /Volumes/AthenaData/databases/patent_full/logfile

# 检查权限
ls -la /Volumes/AthenaData/databases/patent_full/
```

### 问题2：连接失败
```bash
# 检查端口
netstat -an | grep 5450

# 检查PostgreSQL进程
ps aux | grep postgres
```

### 问题3：权限错误
```bash
# 修复权限
sudo chown -R postgres:postgres /Volumes/AthenaData/databases/patent_full
```

## 🎉 迁移完成后的好处

1. **释放空间**：约200GB本地空间
2. **性能提升**：本地资源竞争减少
3. **灵活性**：可以单独管理大型数据库
4. **扩展性**：未来可以添加更多外部数据库

## 📝 记录

建议记录迁移信息：
- 迁移日期
- 数据库版本
- 移动硬盘序列号
- 任何特殊配置

这样便于后续维护和故障排查。