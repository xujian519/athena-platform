# 专利PDF下载指南

## 方法一：使用专业专利下载工具

### 1. 专利家（Patent）
- 官网: https://www.patentguan.com/
- 支持批量下载中国专利PDF
- 需要注册账号（部分功能免费）

### 2. SooPAT
- 官网: https://www.soopat.com/
- 支持PDF下载
- 需要登录

### 3. 专利汇
- 官网: https://www.patentguic.com/
- 提供专利PDF下载服务

## 方法二：中国专利局官方渠道

### 1. 中国专利公布公告查询
- 网址: https://pss-system.cponline.cnipa.gov.cn/conventionalSearch
- 查询步骤：
  1. 输入专利号
  2. 查看专利详情
  3. 点击"全文下载"获取PDF

### 2. 中国专利电子申请网站
- 网址: https://www.cponline.cnipa.gov.cn/
- 需要注册账号

## 方法三：使用浏览器插件

推荐插件：
1. **PatentPDF** - Chrome/Edge浏览器插件
2. **专利下载助手** - 下载中国专利PDF
3. **PatentSnap** - 专利分析及下载

## 方法四：使用命令行工具

### 1. 专利号列表批量下载脚本

```bash
# 进入目标目录
cd "/Users/xujian/Nutstore Files/02无效诉讼/济南力邦/201921401279.9/专利无效/检索结果/下载专利PDF"

# 执行下载脚本
bash download_commands.sh
```

### 2. 使用curl命令单独下载

```bash
# 单个专利下载示例
curl -o "CN210149632U.pdf" "https://pss-system.cponline.cnipa.gov.cn/beforePub/CN210149632U/pdf"
```

## 方法五：使用专业API服务

### 1. 优译翻译API
- 提供专利PDF下载服务
- 支持批量下载

### 2. 其他商业API
- PatentAPI
- PatentsView
- Innography

## 推荐方案

对于您的106个专利，推荐使用以下方案：

### 方案A：半自动下载
1. 使用专利家或SooPAT批量下载
2. 将下载的PDF文件保存到指定目录

### 方案B：手动下载高价值专利
1. 优先下载与目标专利最相关的专利
2. 基于关键词筛选后手动下载

### 方案C：委托专业服务
1. 联系专利数据库服务商
2. 购买批量下载服务

## 当前状态

- ✅ 专利号列表已读取：106个
- ✅ 下载脚本已生成：download_commands.sh
- ⚠️ 测试下载失败（Google Patents链接不可用）

## 下一步建议

1. **尝试其他下载源**
   - 使用中国专利局官网
   - 使用专利家等专业工具

2. **选择性下载**
   - 优先下载高相关性专利
   - 根据需要选择性下载

3. **使用已有数据**
   - 检索结果目录中已有markdown格式的专利文档
   - 可直接使用这些文档进行对比分析
