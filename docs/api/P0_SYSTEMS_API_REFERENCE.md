# P0系统API参考文档

**版本**: 1.0.0
**更新日期**: 2026-04-21
**适用对象**: 开发者

---

## 📚 目录

1. [Skills系统API](#skills系统api)
2. [Plugins系统API](#plugins系统api)
3. [会话记忆系统API](#会话记忆系统api)

---

## Skills系统API

### 核心类

#### SkillDefinition

```python
@dataclass
class SkillDefinition:
    """技能定义"""
    
    id: str                          # 技能唯一标识
    name: str                        # 技能名称
    category: SkillCategory          # 技能类别
    description: str                 # 技能描述
    tools: list[str]                 # 关联的工具列表
    metadata: SkillMetadata | None   # 元数据
    content: str                     # 技能内容（Markdown）
    source: str                      # 来源
    path: str | None                 # 文件路径
    
    def has_tool(self, tool_id: str) -> bool:
        """检查技能是否包含指定工具"""
        
    def is_enabled(self) -> bool:
        """检查技能是否启用"""
```

#### SkillRegistry

```python
class SkillRegistry:
    """技能注册表"""
    
    def __init__(self):
        """初始化注册表"""
    
    def register(self, skill: SkillDefinition) -> None:
        """注册技能
        
        Args:
            skill: 技能定义
            
        Raises:
            ValueError: 技能ID已存在
        """
    
    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        """获取技能
        
        Args:
            skill_id: 技能ID
            
        Returns:
            SkillDefinition | None: 技能定义
        """
    
    def unregister(self, skill_id: str) -> bool:
        """注销技能
        
        Args:
            skill_id: 技能ID
            
        Returns:
            bool: 是否成功注销
        """
    
    def list_skills(
        self,
        category: Optional[SkillCategory] = None,
        enabled_only: bool = False,
    ) -> List[SkillDefinition]:
        """列出技能
        
        Args:
            category: 技能类别
            enabled_only: 是否只返回启用的技能
            
        Returns:
            list[SkillDefinition]: 技能列表
        """
    
    def find_skills(
        self,
        name_pattern: str = "*",
        category: Optional[SkillCategory] = None,
    ) -> List[SkillDefinition]:
        """按模式查找技能
        
        Args:
            name_pattern: 名称模式（支持通配符*）
            category: 技能类别
            
        Returns:
            list[SkillDefinition]: 匹配的技能列表
        """
    
    def get_skills_by_tool(self, tool_id: str) -> List[SkillDefinition]:
        """获取使用指定工具的所有技能
        
        Args:
            tool_id: 工具ID
            
        Returns:
            list[SkillDefinition]: 技能列表
        """
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            dict: 统计信息（total_skills, by_category）
        """
```

#### SkillLoader

```python
class SkillLoader:
    """技能加载器"""
    
    def __init__(self, registry: Optional[SkillRegistry] = None):
        """初始化加载器
        
        Args:
            registry: 技能注册表
        """
    
    def load_from_file(self, file_path: str | Path) -> Optional[SkillDefinition]:
        """从文件加载技能
        
        Args:
            file_path: 文件路径（.yaml或.yml）
            
        Returns:
            SkillDefinition | None: 技能定义
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误
        """
    
    def load_from_directory(
        self,
        directory: str | Path,
        recursive: bool = False,
        register: bool = True,
    ) -> List[SkillDefinition]:
        """从目录加载技能
        
        Args:
            directory: 目录路径
            recursive: 是否递归加载子目录
            register: 是否自动注册到注册表
            
        Returns:
            list[SkillDefinition]: 加载的技能列表
        """
```

#### SkillToolMapper

```python
class SkillToolMapper:
    """技能-工具映射器"""
    
    def __init__(self, registry: SkillRegistry):
        """初始化映射器
        
        Args:
            registry: 技能注册表
        """
    
    def map_tools_to_skills(self) -> Dict[str, List[str]]:
        """映射工具到技能
        
        Returns:
            dict: {tool_id: [skill_id1, skill_id2, ...]}
        """
    
    def get_tools_for_skill(self, skill_id: str) -> List[str]:
        """获取技能所需的工具
        
        Args:
            skill_id: 技能ID
            
        Returns:
            list[str]: 工具ID列表
        """
    
    def get_skills_for_tool(self, tool_id: str) -> List[SkillDefinition]:
        """获取使用某工具的所有技能
        
        Args:
            tool_id: 工具ID
            
        Returns:
            list[SkillDefinition]: 技能列表
        """
    
    def detect_tool_conflicts(self) -> List[Dict[str, Any]]:
        """检测工具冲突
        
        Returns:
            list[dict]: 冲突列表
        """
    
    def detect_tool_dependencies(self) -> Dict[str, List[str]]:
        """检测工具依赖
        
        Returns:
            dict: {skill_id: [dependent_skill_id, ...]}
        """
    
    def get_tool_usage_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取工具使用统计
        
        Returns:
            dict: {tool_id: {count: int, skill_ids: list}}
        """
    
    def find_unused_tools(self, all_tools: List[str]) -> List[str]:
        """查找未使用的工具
        
        Args:
            all_tools: 所有可用工具ID列表
            
        Returns:
            list[str]: 未使用的工具ID列表
        """
```

### 使用示例

```python
from core.skills.loader import SkillLoader
from core.skills.registry import SkillRegistry
from core.skills.tool_mapper import SkillToolMapper

# 1. 创建注册表和加载器
registry = SkillRegistry()
loader = SkillLoader(registry)

# 2. 加载技能
skills = loader.load_from_directory("core/skills/bundled")

# 3. 查询技能
patent_skill = registry.get_skill("patent_analysis")
print(f"技能: {patent_skill.name}")
print(f"工具: {patent_skill.tools}")

# 4. 工具映射分析
mapper = SkillToolMapper(registry)
conflicts = mapper.detect_tool_conflicts()
stats = mapper.get_tool_usage_stats()
```

---

## Plugins系统API

### 核心类

#### PluginDefinition

```python
@dataclass
class PluginDefinition:
    """插件定义"""
    
    id: str                          # 插件唯一标识
    name: str                        # 插件名称
    type: PluginType                 # 插件类型
    status: PluginStatus             # 插件状态
    metadata: PluginMetadata | None   # 元数据
    entry_point: str                 # 入口点
    config: dict[str, Any]           # 配置
    enabled: bool                    # 是否启用
    skills: list[str]                # 提供的技能列表
    path: str | None                 # 插件路径
    
    def is_active(self) -> bool:
        """检查插件是否激活"""
        
    def is_enabled(self) -> bool:
        """检查插件是否启用"""
        
    def can_load(self) -> bool:
        """检查插件是否可加载"""
```

#### PluginRegistry

```python
class PluginRegistry:
    """插件注册表"""
    
    def __init__(self):
        """初始化注册表"""
    
    def register(self, plugin: PluginDefinition) -> None:
        """注册插件"""
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginDefinition]:
        """获取插件"""
    
    def unregister(self, plugin_id: str) -> bool:
        """注销插件"""
    
    def activate(self, plugin_id: str) -> bool:
        """激活插件
        
        Returns:
            bool: 是否成功激活
        """
    
    def deactivate(self, plugin_id: str) -> bool:
        """停用插件
        
        Returns:
            bool: 是否成功停用
        """
    
    def list_plugins(
        self,
        plugin_type: Optional[PluginType] = None,
        status: Optional[PluginStatus] = None,
        enabled_only: bool = False,
    ) -> List[PluginDefinition]:
        """列出插件"""
    
    def find_plugins(
        self,
        name_pattern: str = "*",
        plugin_type: Optional[PluginType] = None,
    ) -> List[PluginDefinition]:
        """按模式查找插件"""
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
```

#### PluginLoader

```python
class PluginLoader:
    """插件加载器"""
    
    def __init__(self, registry: Optional[PluginRegistry] = None):
        """初始化加载器"""
    
    def load_from_file(self, file_path: str | Path) -> Optional[PluginDefinition]:
        """从文件加载插件"""
    
    def load_from_directory(
        self,
        directory: str | Path,
        recursive: bool = False,
        register: bool = True,
    ) -> List[PluginDefinition]:
        """从目录加载插件"""
    
    def load_plugin_module(self, plugin: PluginDefinition) -> Any:
        """加载插件模块
        
        Args:
            plugin: 插件定义
            
        Returns:
            Any: 插件模块实例
            
        Raises:
            ImportError: 模块加载失败
            AttributeError: 入口点不存在
        """
```

### 使用示例

```python
from core.plugins.loader import PluginLoader
from core.plugins.registry import PluginRegistry

# 1. 创建注册表和加载器
registry = PluginRegistry()
loader = PluginLoader(registry)

# 2. 加载插件
plugins = loader.load_from_directory("core/plugins/bundled")

# 3. 激活插件
registry.activate("patent_analyzer_plugin")

# 4. 加载插件模块
plugin = registry.get_plugin("patent_analyzer_plugin")
module = loader.load_plugin_module(plugin)
result = module.analyze(patent_id="CN123456789A")
```

---

## 会话记忆系统API

### 核心类

#### SessionMessage

```python
@dataclass
class SessionMessage:
    """会话消息"""
    
    role: MessageRole               # 消息角色
    content: str                    # 消息内容
    timestamp: datetime             # 时间戳
    metadata: dict[str, Any]        # 元数据
    token_count: int                # token数量
    message_id: str                 # 消息ID
```

#### SessionContext

```python
@dataclass
class SessionContext:
    """会话上下文"""
    
    session_id: str                 # 会话ID
    user_id: str                    # 用户ID
    agent_id: str                   # Agent ID
    start_time: datetime            # 开始时间
    last_activity: datetime         # 最后活动时间
    status: SessionStatus           # 会话状态
    metadata: dict[str, Any]        # 元数据
    total_tokens: int               # 总token数
    message_count: int              # 消息数量
    
    def update_activity(self) -> None:
        """更新活动时间"""
    
    def is_expired(self, timeout_seconds: int = 3600) -> bool:
        """检查会话是否过期"""
```

#### SessionMemory

```python
@dataclass
class SessionMemory:
    """会话记忆"""
    
    context: SessionContext         # 会话上下文
    messages: list[SessionMessage]  # 消息列表
    summary: SessionSummary | None   # 会话摘要
    embeddings: dict                # 嵌入向量
    
    def add_message(self, message: SessionMessage) -> None:
        """添加消息"""
    
    def get_recent_messages(
        self,
        count: int = 10,
        role: Optional[MessageRole] = None,
    ) -> List[SessionMessage]:
        """获取最近的消息"""
    
    def calculate_tokens(self) -> int:
        """计算总token数"""
```

#### SessionManager

```python
class SessionManager:
    """会话管理器"""
    
    def __init__(
        self,
        storage: Optional[SessionStorage] = None,
        session_timeout: int = 3600,
    ):
        """初始化会话管理器
        
        Args:
            storage: 会话存储
            session_timeout: 会话超时时间（秒）
        """
    
    def create_session(
        self,
        session_id: str,
        user_id: str,
        agent_id: str,
        metadata: Optional[dict] = None,
    ) -> SessionMemory:
        """创建新会话"""
    
    def get_session(self, session_id: str) -> Optional[SessionMemory]:
        """获取会话"""
    
    def close_session(self, session_id: str) -> bool:
        """关闭会话"""
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
    
    def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        token_count: int = 0,
        metadata: Optional[dict] = None,
    ) -> Optional[SessionMessage]:
        """添加消息到会话"""
    
    def get_session_messages(
        self,
        session_id: str,
        count: Optional[int] = None,
        role: Optional[MessageRole] = None,
    ) -> List[SessionMessage]:
        """获取会话消息"""
    
    def get_active_sessions(
        self,
        user_id: Optional[str] = None,
    ) -> List[SessionMemory]:
        """获取活跃会话"""
    
    def cleanup_expired_sessions(self) -> int:
        """清理过期会话
        
        Returns:
            int: 清理的会话数量
        """
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
    
    def generate_session_summary(
        self,
        session_id: str,
        title: str,
        summary: str,
        key_points: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
    ) -> Optional[SessionSummary]:
        """生成会话摘要"""
```

#### SessionStorage

```python
class SessionStorage:
    """会话存储基类"""
    
    def save(self, memory: SessionMemory) -> bool:
        """保存会话"""
    
    def load(self, session_id: str) -> Optional[SessionMemory]:
        """加载会话"""
    
    def delete(self, session_id: str) -> bool:
        """删除会话"""
    
    def exists(self, session_id: str) -> bool:
        """检查会话是否存在"""

class FileSessionStorage(SessionStorage):
    """文件会话存储"""
    
    def __init__(self, storage_dir: str = "data/sessions"):
        """初始化文件存储"""
```

### 使用示例

```python
from core.memory.sessions.manager import SessionManager
from core.memory.sessions.storage import FileSessionStorage
from core.memory.sessions.types import MessageRole

# 1. 创建带存储的管理器
storage = FileSessionStorage(storage_dir="data/sessions")
manager = SessionManager(storage=storage)

# 2. 创建会话
memory = manager.create_session(
    session_id="session_001",
    user_id="user123",
    agent_id="xiaona"
)

# 3. 添加消息
manager.add_message(
    session_id="session_001",
    role=MessageRole.USER,
    content="帮我分析专利CN123456789A",
    token_count=15
)

manager.add_message(
    session_id="session_001",
    role=MessageRole.ASSISTANT,
    content="好的，我来分析这个专利...",
    token_count=20
)

# 4. 获取消息
messages = manager.get_session_messages("session_001")
print(f"会话有 {len(messages)} 条消息")

# 5. 生成摘要
summary = manager.generate_session_summary(
    session_id="session_001",
    title="专利分析讨论",
    summary="用户咨询了专利CN123456789A的创造性",
    key_points=["专利权利要求分析", "创造性评估"],
    tags=["专利", "分析"]
)

# 6. 关闭会话（自动保存）
manager.close_session("session_001")
```

---

## 枚举类型

### SkillCategory

```python
class SkillCategory(Enum):
    ANALYSIS = "analysis"       # 分析类技能
    WRITING = "writing"         # 写作类技能
    SEARCH = "search"           # 检索类技能
    COORDINATION = "coordination"  # 协调类技能
    AUTOMATION = "automation"   # 自动化技能
```

### PluginType

```python
class PluginType(Enum):
    AGENT = "agent"             # Agent插件
    TOOL = "tool"               # 工具插件
    MIDDLEWARE = "middleware"   # 中间件插件
    OBSERVER = "observer"       # 观察者插件
    EXECUTOR = "executor"       # 执行器插件
```

### PluginStatus

```python
class PluginStatus(Enum):
    LOADED = "loaded"           # 已加载
    ACTIVE = "active"           # 激活中
    INACTIVE = "inactive"       # 未激活
    ERROR = "error"             # 错误状态
    UNLOADED = "unloaded"       # 已卸载
```

### SessionStatus

```python
class SessionStatus(Enum):
    ACTIVE = "active"           # 活跃
    SUSPENDED = "suspended"     # 暂停
    CLOSED = "closed"           # 关闭
    ARCHIVED = "archived"       # 已归档
```

### MessageRole

```python
class MessageRole(Enum):
    USER = "user"               # 用户
    ASSISTANT = "assistant"     # 助手
    SYSTEM = "system"           # 系统
    TOOL = "tool"               # 工具
```

---

**作者**: Athena平台团队
**最后更新**: 2026-04-21
**版本**: 1.0.0
