# 第2阶段 Week 1 执行计划

> **阶段**: 第2阶段 - 基础重构
> **周次**: Week 1 - 统一配置管理系统
> **时间**: 2026-04-22 (Day 1开始)
> **团队**: phase2-refactor
> **风险**: ★★★☆☆ (中)

---

## 📋 Week 1 目标

建立统一的配置管理系统，使用Pydantic Settings实现类型安全的配置管理。

---

## 🎯 Day 1-2: 设计配置架构

### 任务清单

- [ ] 研究Pydantic Settings最佳实践
- [ ] 设计配置分层结构
  ```
  config/
  ├── base/              # 基础配置（所有环境共享）
  │   ├── database.yml   # 数据库配置
  │   ├── redis.yml      # Redis配置
  │   ├── qdrant.yml     # Qdrant配置
  │   └── llm.yml        # LLM配置
  ├── environments/      # 环境特定配置
  │   ├── development.yml
  │   ├── test.yml
  │   └── production.yml
  ├── services/          # 服务配置
  │   ├── gateway.yml
  │   ├── xiaona.yml
  │   └── xiaonuo.yml
  └── deployments/       # 部署配置
      ├── docker.yml
      └── kubernetes.yml
  ```

- [ ] 设计配置继承机制
  ```python
  # 配置加载顺序
  # 1. base/ (基础配置)
  # 2. environments/{env}.yml (环境配置)
  # 3. services/{service}.yml (服务配置)
  # 4. 环境变量 (覆盖配置文件)
  ```

- [ ] 编写配置架构文档

**验证标准**:
- ✅ 配置架构设计文档已完成
- ✅ 配置分层结构清晰
- ✅ 配置加载逻辑明确

---

## 🔧 Day 3-4: 实现配置管理工具

### 任务清单

- [ ] 创建core/config/settings.py
  ```python
  from pydantic_settings import BaseSettings, SettingsConfigDict
  
  class Settings(BaseSettings):
      """统一配置管理"""
      
      model_config = SettingsConfigDict(
          env_file=".env",
          env_file_encoding="utf-8",
          case_sensitive=False,
      )
      
      # 环境名
      environment: Literal["development", "test", "production"] = "development"
      
      # 数据库配置
      database_host: str = "localhost"
      database_port: int = 5432
      database_user: str = "athena"
      database_password: str = "athena123"
      database_name: str = "athena"
      
      @property
      def database_url(self) -> str:
          return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"
      
      # 全局配置实例
      settings = Settings.get_instance()
  ```

- [ ] 实现环境配置加载器
- [ ] 实现配置验证器
- [ ] 编写单元测试

**验证标准**:
- ✅ Settings类实现完成
- ✅ 环境配置加载器实现完成
- ✅ 配置验证器实现完成
- ✅ 单元测试全部通过

---

## 🔄 Day 5: 迁移核心配置

### 任务清单

- [ ] 迁移config/数据库配置
- [ ] 迁移core/config/代码级配置
- [ ] 迁移services/config/服务配置
- [ ] 使用适配器模式兼容旧配置

**验证标准**:
- ✅ 核心配置已迁移到新格式
- ✅ 旧配置仍可通过适配器访问
- ✅ 测试套件全部通过
- ✅ 系统运行正常

---

## 🧹 Day 6-7: 清理旧配置

### 任务清单

- [ ] 删除重复的配置文件
- [ ] 更新配置文档
- [ ] 验证所有服务正常启动
- [ ] 部署到测试环境
- [ ] 观察48小时

**验证标准**:
- ✅ 重复配置文件已删除
- ✅ 配置文档已更新
- ✅ 所有服务正常启动
- ✅ 测试环境运行48小时无异常

---

## 📊 Week 1 检查点

- [ ] 配置架构设计完成
- [ ] 配置管理工具实现完成
- [ ] 核心配置已迁移
- [ ] 旧配置已清理
- [ ] 测试覆盖率 > 70%

---

## 🚀 开始执行

**执行命令**: 使用OMC团队模式并行执行任务

**团队**: phase2-refactor
**任务**: 4个主要任务
**预计时间**: 7天 (可压缩为1-2天)

---

**计划创建时间**: 2026-04-21
**执行开始时间**: 2026-04-22
**团队模式**: phase2-refactor
