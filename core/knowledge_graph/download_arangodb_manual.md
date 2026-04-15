# ArangoDB 手动安装指南 (macOS M4)

## 方法一：直接下载安装包（推荐）

1. **访问官方下载页面**
   - 网址：https://www.arangodb.com/download-major/
   - 选择：macOS ARM64 (Apple Silicon) 版本

2. **下载步骤**
   ```bash
   # 创建下载目录
   mkdir -p ~/Downloads/arangodb
   cd ~/Downloads/arangodb

   # 使用curl下载（替换为最新版本号）
   curl -L -o arangodb-macos-arm64.tar.gz \
     "https://download.arangodb.com/arangodb311/Community/macos/arangodb3-macos-arm64-3.11.0.tar.gz"
   ```

3. **解压安装**
   ```bash
   # 解压
   tar -xzf arangodb-macos-arm64.tar.gz

   # 移动到应用目录
   sudo mv arangodb3 /opt/

   # 创建符号链接
   sudo ln -sf /opt/arangodb3/bin/arangod /usr/local/bin/arangod
   sudo ln -sf /opt/arangodb3/bin/arangosh /usr/local/bin/arangosh
   ```

## 方法二：使用Docker（备用方案）

如果直接下载有问题，可以使用Docker：

```bash
# 拉取镜像
docker pull arangodb/arangodb:3.11.0

# 创建数据目录
mkdir -p ~/arangodb_data

# 运行容器
docker run -d \
  --name athena-arangodb \
  -p 8529:8529 \
  -e ARANGO_ROOT_PASSWORD="" \
  -e ARANGO_NO_AUTH=1 \
  -v ~/arangodb_data:/var/lib/arangodb3 \
  arangodb/arangodb:3.11.0
```

## 验证安装

```bash
# 检查版本
arangod --version

# 或使用Docker检查
docker ps | grep athena-arangodb
```

## 创建数据库

安装成功后运行：
```python
python3 -c "
from arango import ArangoClient

# 连接
client = ArangoClient('http://localhost:8529')

# 创建系统数据库连接
sys_db = client.db('_system', username='root', password='')

# 创建athena_kg数据库
try:
    sys_db.create_database('athena_kg')
    print('✅ 数据库创建成功')
except Exception as e:
    print(f'ℹ️ 可能已存在: {e}')

# 测试连接
db = client.db('athena_kg', username='root', password='')
print('✅ 连接成功！')
"
```

## Web界面

- 访问地址：http://localhost:8528
- 用户名：root
- 密码：空