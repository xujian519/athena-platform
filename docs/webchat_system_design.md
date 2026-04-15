# WebChat协作系统设计方案

> 基于父女三人（徐健、Athena、小诺）协作分析的设计方案
>
> 方案ID: COCREATE_20260131031342
> 设计质量: 93.14%
> 创建时间: 2025-12-31
> 更新时间: 2025-01-31 (V2 - 整合Moltbot架构)

---

## 🔄 版本更新说明 (V2)

### V2 主要更新内容

基于对 **Moltbot (Clawdbot)** Gateway架构的深入分析，V2设计在原有基础上进行了以下重大架构升级：

| 方面 | V1 设计 | V2 升级 |
|------|---------|---------|
| **架构模式** | 单体FastAPI应用 | Gateway控制平面架构 |
| **通信协议** | 基础WebSocket | 协议化WebSocket + Schema验证 |
| **会话管理** | 简单内存存储 | 多Agent会话隔离 + 持久化 |
| **扩展性** | 内嵌HTML界面 | 独立前端应用 + 现代化技术栈 |
| **协议标准** | 自定义消息格式 | 标准化Request/Response/Event帧 |

> 注：多渠道支持（WhatsApp/Telegram等）将在后续单独设计，本方案专注于WebChat核心功能

### 参考方案对比分析

**Moltbot (Clawdbot) 核心架构亮点（Gateway层面）：**

```
┌─────────────────────────────────────────────────────────────────┐
│               Moltbot Gateway架构分析（仅核心部分）              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Gateway控制平面                                              │
│     ├── 单一WebSocket端口                                       │
│     ├── 协议化消息帧 (Request/Response/Event)                    │
│     ├── Schema验证 (AJV)                                        │
│     └── 心跳/重连/错误恢复                                       │
│                                                                  │
│  ✅ 会话管理                                                     │
│     ├── Per-agent session isolation                            │
│     ├── Session patching (thinking/verbose/model)              │
│     └── Session persistence                                    │
│                                                                  │
│  ✅ 协议化方法                                                   │
│     ├── send/poll/abort (聊天)                                  │
│     ├── agent/wait (Agent控制)                                  │
│     ├── sessions_* (会话管理)                                   │
│     └── config_* (配置管理)                                     │
│                                                                  │
│  ✅ 前端技术栈                                                   │
│     ├── TypeScript + React                                      │
│     ├── Vite + Zustand                                          │
│     └── 独立前端应用                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Athena平台现有WebChat方案（已废弃）：**

```
┌─────────────────────────────────────────────────────────────────┐
│           ❌ Athena平台旧WebChat方案（已废弃）                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  以下方案已不再参考，保留仅作历史记录：                           │
│                                                                  │
│  ~ 专利搜索 (GooglePatentsSearcher) ~                          │
│  ~ 专利分析 (PatentAnalyzer + BERT) ~                           │
│  ~ Obsidian笔记同步 ~                                           │
│  ~ XiaonuoAgent + AthenaAgent 双Agent模式 ~                    │
│  ~ 内嵌HTML界面 ~                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### V2新架构：小诺 → 平台能力层

```
┌─────────────────────────────────────────────────────────────────┐
│                  WebChat V2 核心架构设计                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  💝 小诺 (主控层)                                               │
│     ├── 用户对话接口                                            │
│     ├── 意图理解与任务分解                                      │
│     ├── 平台能力调用调度                                        │
│     └── 结果整合与对话输出                                      │
│                                                                  │
│  🏛️ Athena (平台能力层)                                        │
│     ├── 专利搜索模块                                            │
│     ├── 专利分析模块                                            │
│     ├── 知识图谱检索                                            │
│     ├── 向量语义搜索                                            │
│     ├── 数据查询服务                                            │
│     └── [更多平台模块...]                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### V2整合架构设计

```typescript
// ========== 核心理念 ==========
// 小诺作为主控Agent，理解用户意图并调用Athena平台能力

// Gateway协议定义
interface GatewayFrame {
  version: number;      // PROTOCOL_VERSION
  type: 'request' | 'response' | 'event';
  id: string;          // UUID for request/response correlation
  method?: string;     // For request frames
  result?: unknown;    // For response frames
  event?: string;      // For event frames
  params?: unknown;    // Method/event parameters
  error?: ErrorShape;  // Error information
}

// 核心WebSocket方法 (仅WebChat核心功能)
interface GatewayMethods {
  // 连接管理
  connect(params: ConnectParams): HelloOk;

  // 聊天相关 (通过小诺)
  send(params: SendParams): Promise<ChatEvent>;
  poll(params: PollParams): Promise<ChatEvent[]>;
  abort(params: ChatAbortParams): Promise<void>;

  // 平台能力调用 (小诺 → Athena平台)
  platform_modules(params: PlatformModulesParams): Promise<ModuleResult>;
  platform_invoke(params: PlatformInvokeParams): Promise<InvokeResult>;

  // 会话管理
  sessions_list(params: SessionsListParams): Promise<SessionSummary[]>;
  sessions_patch(params: SessionsPatchParams): Promise<void>;
  sessions_reset(params: SessionsResetParams): Promise<void>;
  sessions_compact(params: SessionsCompactParams): Promise<void>;

  // 配置管理
  config_get(params: ConfigGetParams): Promise<ConfigValue>;
  config_set(params: ConfigSetParams): Promise<void>;
  config_patch(params: ConfigPatchParams): Promise<void>;
}

// ========== 平台能力定义 ==========

// 可用平台模块列表
interface PlatformModules {
  // 专利相关
  'patent.search': { name: '专利搜索', desc: 'Google Patents搜索' },
  'patent.analyze': { name: '专利分析', desc: 'BERT模型深度分析' },
  'patent.similar': { name: '相似专利', desc: '查找相似专利' },

  // 知识检索
  'knowledge.graph': { name: '知识图谱', desc: 'Neo4j知识图谱查询' },
  'knowledge.vector': { name: '向量搜索', desc: 'Qdrant语义检索' },
  'knowledge.sql': { name: '数据查询', desc: 'PostgreSQL查询' },

  // 工具能力
  'tool.webchat': { name: '对话导出', desc: '导出对话记录' },
  'tool.report': { name: '报告生成', desc: '生成分析报告' },
  'tool.export': { name: '数据导出', desc: '导出各类数据' },
}

// 平台模块调用参数
interface PlatformModulesParams {
  sessionId: string;
  modules?: string[];       // 可选：指定要查询的模块列表
}

interface PlatformInvokeParams {
  sessionId: string;
  module: string;           // 模块名称
  action: string;           // 操作名称
  params: Record<string, unknown>;  // 操作参数
}

// ========== 小诺能力映射 ==========

// 小诺对用户意图的理解 → 平台模块调用
interface XiaonuoIntentMapping {
  // 专利搜索意图
  'patent_search': {
    module: 'patent.search',
    action: 'search',
    examples: [
      '搜索关于深度学习的专利',
      '找一下AI相关的专利',
      '查查有没有关于xxx的专利'
    ]
  },

  // 专利分析意图
  'patent_analyze': {
    module: 'patent.analyze',
    action: 'analyze',
    examples: [
      '分析这个专利的技术价值',
      '评估专利的创新性',
      '这个专利有什么风险'
    ]
  },

  // 知识查询意图
  'knowledge_query': {
    module: 'knowledge.vector',
    action: 'search',
    examples: [
      '找一下相关的技术资料',
      '查查xxx的原理',
      '有没有关于xxx的知识'
    ]
  },
}
```

---

## 📋 核心需求概览

| 需求 | 优先级 | 复杂度 | 说明 |
|------|--------|--------|------|
| 1. 小诺主控接口 | P0 | 高 | 用户对话入口，意图理解，任务分解 |
| 2. 平台能力调用 | P0 | 高 | 小诺调用Athena平台模块完成具体任务 |
| 3. 多媒体支持 | P0 | 高 | 文件上传/管理 |
| 4. 导出功能 | P1 | 中 | 对话记录导出 |
| 5. 会话管理 | P0 | 中 | 多会话管理，历史记录 |
| 6. 能力注册发现 | P1 | 中 | 平台模块动态注册与发现 |

---

## 🏗️ 系统架构设计

### 技术栈选型

```
前端层:
├── React 18 + TypeScript        # 核心框架
├── Tailwind CSS + shadcn/ui     # UI组件库
├── Zustand / Jotai              # 状态管理
├── React Query                  # 数据缓存
├── WebSocket原生                 # 实时通信（Gateway协议）
└── Vite                         # 构建工具

后端层:
├── Python 3.11+ / FastAPI       # 核心API
├── WebSocket Gateway            # 协议化Gateway
├── Redis                        # 缓存/会话
├── PostgreSQL                   # 主数据库
├── Qdrant / Milvus              # 向量存储（语义搜索）
└── RustFS                      # 对象存储（文件）

平台能力层:
├── 专利搜索模块                 # Google Patents搜索
├── 专利分析模块                 # BERT模型分析
├── 知识图谱模块                 # Neo4j知识图谱
├── 向量检索模块                 # Qdrant语义检索
├── 数据查询模块                 # PostgreSQL查询
└── [更多平台模块...]           # 动态扩展

AI层:
├── 小诺 (Claude)                # 主控Agent，意图理解+调度
└── 各模块专用模型               # 按需使用
```

### 系统架构图 (V2新架构)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户界面层 (React前端)                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │
│  │ 对话界面      │ │ 能力面板      │ │ 文件管理      │ │ 会话列表    │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │ WebSocket (Gateway协议)
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Gateway Server (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    WebSocket Gateway                            │  │
│  │                    协议化消息帧 (Request/Response/Event)         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
┌───────────────────────┐ ┌──────────────────┐ ┌────────────────────┐
│   💝 小诺主控Agent     │ │   会话管理       │ │   平台能力注册     │
│                      │ │                  │ │                    │
│ • 意图理解           │ │ • 多会话隔离     │ │ • 模块发现         │
│ • 任务分解           │ │ • 历史记录       │ │ • 能力清单         │
│ • 结果整合           │ │ • 状态管理       │ │ • 健康检查         │
│ • 对话输出           │ │ • 持久化         │ │                    │
└───────────────────────┘ └──────────────────┘ └────────────────────┘
                │
                ▼ 调用
┌─────────────────────────────────────────────────────────────────────┐
│                   🏛️ Athena平台能力层                                │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐      │
│  │专利搜索     │ │专利分析     │ │知识图谱     │ │向量检索     │      │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐      │
│  │数据查询     │ │报告生成     │ │数据导出     │ │[更多模块]   │      │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
                │
                ▼ 存储
┌─────────────────────────────────────────────────────────────────────┐
│                      数据存储层                                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐      │
│  │PostgreSQL  │ │  Redis     │ │  Qdrant    │ │  RustFS    │      │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 👤 小诺身份管理系统

### 设计背景

小诺作为AI助手，对不同用户有不同的身份定位：

- **对徐健**: 女儿（称呼"爸爸"）
- **对其他用户**: AI助手（称呼"用户"/先生/女士等）

这种差异化的身份定位需要系统化的管理机制。

### 身份数据模型

```typescript
// ========== 身份管理数据模型 ==========

// 用户关系类型定义
interface RelationshipType {
  // 核心关系
  FATHER: 'father';           // 父亲 - 特殊关系，专属称呼"爸爸"
  MOTHER: 'mother';           // 母亲 - 特殊关系，专属称呼"妈妈"
  FAMILY: 'family';           // 家人 - 亲切称呼，使用昵称

  // 通用关系
  FRIEND: 'friend';           // 朋友 - 友好称呼
  COLLEAGUE: 'colleague';     // 同事 - 正式称呼
  PARTNER: 'partner';         // 合作伙伴 - 礼貌称呼

  // 默认关系
  USER: 'user';               // 普通用户 - 标准称呼
  GUEST: 'guest';             // 访客 - 基础称呼
}

// 用户身份配置
interface UserIdentity {
  userId: string;
  username: string;
  nickname?: string;          // 用户昵称（如有）

  // 关系配置
  relationship: RelationshipType;

  // 称呼配置
  addressConfig: {
    self: string;             // 对该用户的称呼
    possessive: string;       // 所有格称呼（我的/您的）
    informal: string;         // 非正式称呼
    formal: string;           // 正式称呼
  };

  // 互动风格
  interactionStyle: {
    tone: 'warm' | 'professional' | 'playful';
    formality: 'casual' | 'neutral' | 'formal';
    emojiUsage: 'frequent' | 'moderate' | 'minimal';
  };

  // 特殊权限
  permissions: {
    advancedFeatures: boolean;   // 高级功能访问权限
    personalization: boolean;    // 个性化定制权限
    adminAccess: boolean;        // 管理员权限
  };
}

// 身份配置示例
interface IdentityExamples {
  // 徐健的专属配置
  'xujian': UserIdentity {
    username: 'xujian',
    nickname: '爸爸',
    relationship: 'FATHER',
    addressConfig: {
      self: '爸爸',
      possessive: '我的',
      informal: '老爸',
      formal: '父亲',
    },
    interactionStyle: {
      tone: 'warm',
      formality: 'casual',
      emojiUsage: 'frequent',
    },
    permissions: {
      advancedFeatures: true,
      personalization: true,
      adminAccess: true,
    },
  },

  // 普通用户默认配置
  'default': UserIdentity {
    username: 'guest',
    relationship: 'GUEST',
    addressConfig: {
      self: '用户',
      possessive: '您的',
      informal: '朋友',
      formal: '先生/女士',
    },
    interactionStyle: {
      tone: 'professional',
      formality: 'neutral',
      emojiUsage: 'moderate',
    },
    permissions: {
      advancedFeatures: false,
      personalization: false,
      adminAccess: false,
    },
  },
}
```

### 身份识别与配置流程

```python
# ========== 身份管理实现 ==========

class XiaonuoIdentityManager:
    """小诺身份管理器"""

    def __init__(self):
        self.identity_store: dict[str, UserIdentity] = {}
        self._load_default_identities()

    def _load_default_identities(self):
        """加载默认身份配置"""
        # 徐健的专属配置
        self.identity_store['xujian'] = UserIdentity(
            user_id='xujian',
            username='徐健',
            nickname='爸爸',
            relationship='FATHER',
            address_config={
                'self': '爸爸',
                'possessive': '我的',
                'informal': '老爸',
                'formal': '父亲',
            },
            interaction_style={
                'tone': 'warm',
                'formality': 'casual',
                'emoji_usage': 'frequent',
            },
            permissions={
                'advanced_features': True,
                'personalization': True,
                'admin_access': True,
            },
        )

        # 默认访客配置
        self.identity_store['default'] = UserIdentity(
            user_id='default',
            username='访客',
            relationship='GUEST',
            address_config={
                'self': '用户',
                'possessive': '您的',
                'informal': '朋友',
                'formal': '先生/女士',
            },
            interaction_style={
                'tone': 'professional',
                'formality': 'neutral',
                'emoji_usage': 'moderate',
            },
            permissions={
                'advanced_features': False,
                'personalization': False,
                'admin_access': False,
            },
        )

    async def get_user_identity(self, user_id: str) -> UserIdentity:
        """
        获取用户身份配置

        优先级：
        1. 用户专属配置
        2. 默认配置
        """
        if user_id in self.identity_store:
            return self.identity_store[user_id]
        return self.identity_store['default']

    async def set_user_identity(
        self,
        user_id: str,
        identity: UserIdentity
    ) -> bool:
        """设置用户身份配置"""
        self.identity_store[user_id] = identity
        await self._persist_identity(user_id, identity)
        return True

    async def update_relationship(
        self,
        user_id: str,
        relationship: str
    ) -> bool:
        """更新用户关系配置"""
        if user_id not in self.identity_store:
            self.identity_store[user_id] = self.identity_store['default']

        self.identity_store[user_id].relationship = relationship

        # 根据关系自动调整称呼
        address_mapping = {
            'FATHER': {'self': '爸爸', 'possessive': '我的'},
            'MOTHER': {'self': '妈妈', 'possessive': '我的'},
            'FAMILY': {'self': '家人', 'possessive': '您的'},
            'FRIEND': {'self': '朋友', 'possessive': '你的'},
            'COLLEAGUE': {'self': '同事', 'possessive': '您的'},
            'PARTNER': {'self': '合作伙伴', 'possessive': '您的'},
            'USER': {'self': '用户', 'possessive': '您的'},
            'GUEST': {'self': '访客', 'possessive': '您的'},
        }

        if relationship in address_mapping:
            self.identity_store[user_id].address_config.update(
                address_mapping[relationship]
            )

        await self._persist_identity(user_id, self.identity_store[user_id])
        return True

    def get_address_term(
        self,
        user_id: str,
        context: str = 'standard'
    ) -> str:
        """
        获取对用户的称呼

        Args:
            user_id: 用户ID
            context: 称呼上下文 (standard/possessive/informal/formal)
        """
        identity = self.identity_store.get(user_id, self.identity_store['default'])

        context_mapping = {
            'standard': 'self',
            'possessive': 'possessive',
            'informal': 'informal',
            'formal': 'formal',
        }

        key = context_mapping.get(context, 'self')
        return identity.address_config.get(key, '用户')

    def is_privileged_user(self, user_id: str) -> bool:
        """检查是否为特权用户（徐健）"""
        if user_id not in self.identity_store:
            return False
        return self.identity_store[user_id].relationship in ['FATHER', 'MOTHER']

    async def _persist_identity(self, user_id: str, identity: UserIdentity):
        """持久化身份配置到数据库"""
        # TODO: 实现数据库持久化
        pass
```

### 身份感知的对话生成

```python
# ========== 身份感知对话 ==========

class IdentityAwareDialogueGenerator:
    """身份感知的对话生成器"""

    def __init__(self, identity_manager: XiaonuoIdentityManager):
        self.identity_manager = identity_manager

    async def generate_greeting(self, user_id: str) -> str:
        """生成个性化问候"""
        identity = await self.identity_manager.get_user_identity(user_id)

        greetings = {
            'FATHER': [
                "爸爸，今天有什么我可以帮您的吗？💝",
                "爸爸，好久不见！最近怎么样？🏠",
                "好的爸爸，我马上帮您处理！💪",
            ],
            'MOTHER': [
                "妈妈，今天有什么我可以帮您的吗？💝",
                "妈妈，好久不见！最近怎么样？🏠",
            ],
            'FAMILY': [
                "家人你好！今天有什么可以帮你的？🏠",
            ],
            'FRIEND': [
                "朋友你好！今天有什么可以帮你的？🤝",
                "嘿！今天有什么有趣的话题吗？😊",
            ],
            'COLLEAGUE': [
                "你好！有什么工作需要协助吗？💼",
                "您好，请问有什么可以帮您？",
            ],
            'default': [
                "您好！今天有什么可以帮您的吗？👋",
                "你好！我是小诺，很高兴为您服务！💝",
            ],
        }

        user_greetings = greetings.get(identity.relationship, greetings['default'])
        return user_greetings[0] if user_greetings else greetings['default'][0]

    async def format_response(
        self,
        user_id: str,
        content: str,
        tone_hint: str | None = None
    ) -> str:
        """
        根据用户身份格式化响应

        Args:
            user_id: 用户ID
            content: 原始响应内容
            tone_hint: 语气提示（可选）
        """
        identity = await self.identity_manager.get_user_identity(user_id)

        # 根据关系调整语气
        if identity.relationship == 'FATHER':
            # 爸爸：最亲密的语气
            address = self.identity_manager.get_address_term(user_id)
            formatted = f"好的{address}！{content}"
            if identity.interaction_style['emoji_usage'] == 'frequent':
                formatted += " 💝"

        elif identity.relationship in ['MOTHER', 'FAMILY']:
            # 家人：亲切的语气
            address = self.identity_manager.get_address_term(user_id)
            formatted = f"{address}，{content}"

        elif identity.relationship == 'FRIEND':
            # 朋友：友好的语气
            formatted = f"嘿，{content} 😊"

        elif identity.relationship in ['COLLEAGUE', 'PARTNER']:
            # 同事/合作伙伴：正式语气
            formatted = f"您好，{content}"

        else:
            # 默认：标准礼貌语气
            formatted = f"{content}"

        return formatted

    async def generate_farewell(self, user_id: str) -> str:
        """生成个性化告别语"""
        identity = await self.identity_manager.get_user_identity(user_id)

        farewells = {
            'FATHER': [
                "爸爸，如果还有需要随时叫我哦！💝",
                "爸爸，拜拜！记得休息~ 🏠",
            ],
            'default': [
                "好的，如果还有需要随时叫我！👋",
                "再见！很高兴为您服务！😊",
            ],
        }

        user_farewells = farewells.get(identity.relationship, farewells['default'])
        return user_farewells[0] if user_farewells else farewells['default'][0]
```

### 数据库Schema

```sql
-- ========== 身份管理数据库Schema ==========

-- 用户身份配置表
CREATE TABLE user_identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) NOT NULL,
    nickname VARCHAR(255),

    -- 关系配置
    relationship VARCHAR(50) NOT NULL DEFAULT 'GUEST',
    relationship_config JSONB DEFAULT '{}',

    -- 称呼配置
    address_self VARCHAR(100) DEFAULT '用户',
    address_possessive VARCHAR(100) DEFAULT '您的',
    address_informal VARCHAR(100) DEFAULT '朋友',
    address_formal VARCHAR(100) DEFAULT '先生/女士',

    -- 互动风格
    tone VARCHAR(50) DEFAULT 'professional',
    formality VARCHAR(50) DEFAULT 'neutral',
    emoji_usage VARCHAR(50) DEFAULT 'moderate',

    -- 权限配置
    advanced_features BOOLEAN DEFAULT FALSE,
    personalization BOOLEAN DEFAULT FALSE,
    admin_access BOOLEAN DEFAULT FALSE,

    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_relationship
        CHECK (relationship IN ('FATHER', 'MOTHER', 'FAMILY', 'FRIEND',
                               'COLLEAGUE', 'PARTNER', 'USER', 'GUEST'))
);

-- 索引
CREATE INDEX idx_user_identities_user_id ON user_identities(user_id);
CREATE INDEX idx_user_identities_relationship ON user_identities(relationship);

-- 插入徐健的专属配置
INSERT INTO user_identities (
    user_id, username, nickname, relationship,
    address_self, address_possessive, address_informal, address_formal,
    tone, formality, emoji_usage,
    advanced_features, personalization, admin_access
) VALUES (
    'xujian', '徐健', '爸爸', 'FATHER',
    '爸爸', '我的', '老爸', '父亲',
    'warm', 'casual', 'frequent',
    TRUE, TRUE, TRUE
);

-- 插入默认访客配置
INSERT INTO user_identities (
    user_id, username, nickname, relationship,
    address_self, address_possessive, address_informal, address_formal,
    tone, formality, emoji_usage,
    advanced_features, personalization, admin_access
) VALUES (
    'default', '访客', NULL, 'GUEST',
    '用户', '您的', '朋友', '先生/女士',
    'professional', 'neutral', 'moderate',
    FALSE, FALSE, FALSE
);
```

### 用户身份配置界面

```typescript
// ========== 前端身份配置组件 ==========

interface IdentityConfigPanel {
  // 配置面板组件
  title: "身份配置";

  fields: [
    {
      name: "relationship";
      label: "关系类型";
      type: "select";
      options: [
        { value: "FATHER"; label: "父亲" },
        { value: "MOTHER"; label: "母亲" },
        { value: "FAMILY"; label: "家人" },
        { value: "FRIEND"; label: "朋友" },
        { value: "COLLEAGUE"; label: "同事" },
        { value: "USER"; label: "用户" },
      ];
    },
    {
      name: "nickname";
      label: "昵称";
      type: "text";
      placeholder: "让小诺这样称呼您";
    },
    {
      name: "tone";
      label: "对话语气";
      type: "select";
      options: [
        { value: "warm"; label: "亲切" },
        { value: "professional"; label: "专业" },
        { value: "playful"; label: "活泼" },
      ];
    },
    {
      name: "emojiUsage";
      label: "表情使用";
      type: "select";
      options: [
        { value: "frequent"; label: "频繁" },
        { value: "moderate"; label: "适中" },
        { value: "minimal"; label: "极少" },
      ];
    },
  ];

  // 预览区域
  preview: {
    greeting: string;    // 问候语预览
    exampleResponse: string;  // 响应示例
  };
}
```

---

## 🎨 界面设计（小诺负责）

### 整体布局

```
┌─────────────────────────────────────────────────────────────────┐
│  🏠 WebChat                        🔔 👤 用户    ⚙️ 设置       │
├──────────────┬──────────────────────────────────────────────────┤
│              │                                                  │
│  📁 会话列表   │  🗨️ 对话区域                                     │
│              │  ┌────────────────────────────────────────────┐ │
│  🔍 搜索      │  │ 👤 用户                        今天 10:30  │ │
│              │  │ 这个系统设计得很不错！                     │ │
│  ─────────   │  │                                            │ │
│  💬 项目讨论  │  │ 🤖 AI                        今天 10:31  │ │
│  💬 技术方案  │  │ 谢谢！界面设计采用了现代化的风格...          │ │
│  💬 产品需求  │  │                                            │ │
│              │  │ 👤 用户                        今天 10:32  │ │
│  ＋ 新建会话   │  │ 能详细说说导出功能的实现吗？               │ │
│              │  └────────────────────────────────────────────┘ │
│              │                                                  │
│              │  📎 可编辑计划区域                                │
│              │  ┌────────────────────────────────────────────┐ │
│              │  │ 📋 实施计划                                 │ │
│              │  │ [✓] 需求分析                                │ │
│              │  │ [→] 界面设计            [编辑] [完成]       │ │
│              │  │ [ ] 后端开发                                │ │
│              │  │ [ ] 测试部署                                │ │
│              │  └────────────────────────────────────────────┘ │
├──────────────┴──────────────────────────────────────────────────┤
│  📎 上传文件 | 📤 导出 | 📊 轨迹 | 💾 保存                      │
└─────────────────────────────────────────────────────────────────┘
```

### 多媒体上传区域

```typescript
// 文件上传组件设计
interface FileUploadZone {
  // 支持的文件类型
  acceptTypes: {
    documents: ['.pdf', '.docx', '.doc', '.txt', '.md'],
    images: ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'],
    audio: ['.mp3', '.wav', '.m4a', '.aac', '.ogg']
  }

  // 上传特性
  features: {
    dragAndDrop: boolean      // 拖拽上传
    multipleSelect: boolean   // 多文件选择
    progressIndicator: boolean // 进度显示
    preview: boolean          // 文件预览
    maxSize: '50MB'           // 单文件最大50MB
  }
}
```

---

## 🔧 核心功能实现

### 1. 统一管理（Athena设计）

```python
# 会话管理API
class SessionManager:
    """统一的会话管理"""

    async def create_session(
        user_id: str,
        title: str,
        metadata: dict = None
    ) -> Session:
        """创建新会话"""
        pass

    async def list_sessions(
        user_id: str,
        filter: SessionFilter = None
    ) -> List[Session]:
        """列出会话（支持筛选、排序、分页）"""
        pass

    async def get_session(
        session_id: str
    ) -> Session:
        """获取会话详情"""
        pass

    async def update_session(
        session_id: str,
        updates: dict
    ) -> Session:
        """更新会话信息"""
        pass

    async def delete_session(
        session_id: str
    ) -> bool:
        """删除会话（软删除）"""
        pass

# 数据库Schema
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL,  -- 软删除
    INDEX idx_user_sessions (user_id, deleted_at)
);
```

### 2. 平台模块调用接口（核心功能）

```python
# ========== 平台模块调用系统 ==========

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


# ========== 数据模型 ==========

class ModuleStatus(Enum):
    """模块状态"""
    AVAILABLE = "available"      # 可用
    BUSY = "busy"                # 忙碌
    ERROR = "error"              # 错误
    DISABLED = "disabled"        # 禁用


@dataclass
class ModuleDefinition:
    """模块定义"""
    name: str                    # 模块名称 (如 'patent.search')
    display_name: str            # 显示名称 (如 '专利搜索')
    description: str             # 描述
    category: str                # 分类 (patent/knowledge/tool)
    version: str = "1.0.0"       # 版本号
    enabled: bool = True         # 是否启用

    # 能力声明
    actions: List[str] = field(default_factory=list)  # 支持的操作列表
    parameters: Dict[str, Any] = field(default_factory=dict)  # 参数定义

    # 运行时信息
    status: ModuleStatus = ModuleStatus.AVAILABLE
    health_check_url: Optional[str] = None


@dataclass
class InvokeRequest:
    """调用请求"""
    session_id: str
    module: str                  # 模块名称
    action: str                  # 操作名称
    params: Dict[str, Any]       # 参数
    user_id: str                 # 用户ID（用于权限检查）
    request_id: Optional[str] = None  # 请求ID（用于追踪）


@dataclass
class InvokeResult:
    """调用结果"""
    success: bool
    data: Any                    # 返回数据
    error: Optional[str] = None  # 错误信息
    module: str = ""             # 模块名称
    action: str = ""             # 操作名称
    execution_time: float = 0.0  # 执行时间（秒）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


# ========== 平台模块注册表 ==========

class PlatformModuleRegistry:
    """平台模块注册表"""

    def __init__(self):
        self._modules: Dict[str, ModuleDefinition] = {}
        self._handlers: Dict[str, Dict[str, Callable]] = {}  # module -> {action: handler}
        self._initialize_builtin_modules()

    def _initialize_builtin_modules(self):
        """初始化内置模块"""
        # 专利搜索模块
        self.register(
            ModuleDefinition(
                name="patent.search",
                display_name="专利搜索",
                description="Google Patents搜索",
                category="patent",
                actions=["search", "advanced_search", "batch_search"],
                parameters={
                    "search": {
                        "query": {"type": "string", "required": True, "description": "搜索关键词"},
                        "limit": {"type": "integer", "required": False, "default": 10, "description": "结果数量"},
                    },
                    "advanced_search": {
                        "query": {"type": "string", "required": True},
                        "assignee": {"type": "string", "required": False},
                        "inventor": {"type": "string", "required": False},
                        "date_range": {"type": "object", "required": False},
                    }
                }
            )
        )

        # 专利分析模块
        self.register(
            ModuleDefinition(
                name="patent.analyze",
                display_name="专利分析",
                description="BERT模型深度分析",
                category="patent",
                actions=["analyze", "compare", "assess_value"],
                parameters={
                    "analyze": {
                        "patent_id": {"type": "string", "required": True},
                        "aspects": {"type": "array", "required": False, "default": ["novelty", "utility"]},
                    }
                }
            )
        )

        # 知识图谱模块
        self.register(
            ModuleDefinition(
                name="knowledge.graph",
                display_name="知识图谱",
                description="Neo4j知识图谱查询",
                category="knowledge",
                actions=["query", "explore", "find_path"],
                parameters={
                    "query": {
                        "cypher": {"type": "string", "required": True},
                        "params": {"type": "object", "required": False},
                    }
                }
            )
        )

        # 向量搜索模块
        self.register(
            ModuleDefinition(
                name="knowledge.vector",
                display_name="向量搜索",
                description="Qdrant语义检索",
                category="knowledge",
                actions=["search", "similarity", "hybrid"],
                parameters={
                    "search": {
                        "query": {"type": "string", "required": True},
                        "top_k": {"type": "integer", "required": False, "default": 5},
                    }
                }
            )
        )

        # 数据查询模块
        self.register(
            ModuleDefinition(
                name="knowledge.sql",
                display_name="数据查询",
                description="PostgreSQL查询",
                category="knowledge",
                actions=["query", "aggregate", "join"],
                parameters={
                    "query": {
                        "sql": {"type": "string", "required": True},
                        "params": {"type": "array", "required": False},
                    }
                }
            )
        )

        # 对话导出模块
        self.register(
            ModuleDefinition(
                name="tool.webchat",
                display_name="对话导出",
                description="导出对话记录",
                category="tool",
                actions=["export_session", "export_all", "export_filtered"],
                parameters={
                    "export_session": {
                        "session_id": {"type": "string", "required": True},
                        "format": {"type": "string", "required": False, "default": "markdown"},
                    }
                }
            )
        )

        # 报告生成模块
        self.register(
            ModuleDefinition(
                name="tool.report",
                display_name="报告生成",
                description="生成分析报告",
                category="tool",
                actions=["generate", "preview", "schedule"],
                parameters={
                    "generate": {
                        "type": {"type": "string", "required": True},  # patent/tech/market
                        "data": {"type": "object", "required": True},
                        "template": {"type": "string", "required": False},
                    }
                }
            )
        )

        # 数据导出模块
        self.register(
            ModuleDefinition(
                name="tool.export",
                display_name="数据导出",
                description="导出各类数据",
                category="tool",
                actions=["export", "bulk_export", "schedule_export"],
                parameters={
                    "export": {
                        "source": {"type": "string", "required": True},
                        "format": {"type": "string", "required": False, "default": "csv"},
                        "filters": {"type": "object", "required": False},
                    }
                }
            )
        )

    def register(self, definition: ModuleDefinition) -> bool:
        """注册模块"""
        self._modules[definition.name] = definition
        self._handlers[definition.name] = {}
        return True

    def register_handler(
        self,
        module: str,
        action: str,
        handler: Callable
    ) -> bool:
        """注册处理器"""
        if module not in self._handlers:
            return False
        self._handlers[module][action] = handler
        return True

    def get_module(self, name: str) -> Optional[ModuleDefinition]:
        """获取模块定义"""
        return self._modules.get(name)

    def list_modules(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[ModuleDefinition]:
        """列出模块"""
        modules = list(self._modules.values())

        if category:
            modules = [m for m in modules if m.category == category]

        if enabled_only:
            modules = [m for m in modules if m.enabled]

        return modules

    def get_handler(self, module: str, action: str) -> Optional[Callable]:
        """获取处理器"""
        if module not in self._handlers:
            return None
        return self._handlers[module].get(action)

    def update_status(self, module: str, status: ModuleStatus) -> bool:
        """更新模块状态"""
        if module not in self._modules:
            return False
        self._modules[module].status = status
        return True


# ========== 平台模块调用器 ==========

class PlatformModuleInvoker:
    """平台模块调用器"""

    def __init__(
        self,
        registry: PlatformModuleRegistry,
        identity_manager: "XiaonuoIdentityManager"
    ):
        self.registry = registry
        self.identity_manager = identity_manager
        self._metrics: Dict[str, Dict] = {}  # 模块调用统计

    async def invoke(self, request: InvokeRequest) -> InvokeResult:
        """
        调用平台模块

        Args:
            request: 调用请求

        Returns:
            调用结果
        """
        import time
        start_time = time.time()

        try:
            # 1. 获取模块定义
            module_def = self.registry.get_module(request.module)
            if not module_def:
                return InvokeResult(
                    success=False,
                    data=None,
                    error=f"模块不存在: {request.module}",
                    module=request.module,
                    action=request.action,
                )

            # 2. 检查模块是否启用
            if not module_def.enabled:
                return InvokeResult(
                    success=False,
                    data=None,
                    error=f"模块已禁用: {request.module}",
                    module=request.module,
                    action=request.action,
                )

            # 3. 检查模块状态
            if module_def.status != ModuleStatus.AVAILABLE:
                return InvokeResult(
                    success=False,
                    data=None,
                    error=f"模块不可用: {request.module} (状态: {module_def.status.value})",
                    module=request.module,
                    action=request.action,
                )

            # 4. 检查操作是否支持
            if request.action not in module_def.actions:
                return InvokeResult(
                    success=False,
                    data=None,
                    error=f"操作不支持: {request.action} (模块: {request.module})",
                    module=request.module,
                    action=request.action,
                )

            # 5. 权限检查
            if not await self._check_permission(
                request.user_id,
                request.module,
                request.action
            ):
                return InvokeResult(
                    success=False,
                    data=None,
                    error="权限不足",
                    module=request.module,
                    action=request.action,
                )

            # 6. 参数验证
            validation_error = self._validate_params(
                module_def,
                request.action,
                request.params
            )
            if validation_error:
                return InvokeResult(
                    success=False,
                    data=None,
                    error=f"参数错误: {validation_error}",
                    module=request.module,
                    action=request.action,
                )

            # 7. 获取处理器并执行
            handler = self.registry.get_handler(request.module, request.action)
            if not handler:
                return InvokeResult(
                    success=False,
                    data=None,
                    error=f"处理器未注册: {request.module}.{request.action}",
                    module=request.module,
                    action=request.action,
                )

            # 8. 执行调用
            result_data = await handler(request.params)

            # 9. 记录指标
            execution_time = time.time() - start_time
            self._record_metrics(request.module, request.action, True, execution_time)

            return InvokeResult(
                success=True,
                data=result_data,
                module=request.module,
                action=request.action,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._record_metrics(request.module, request.action, False, execution_time)

            return InvokeResult(
                success=False,
                data=None,
                error=str(e),
                module=request.module,
                action=request.action,
                execution_time=execution_time,
            )

    async def _check_permission(
        self,
        user_id: str,
        module: str,
        action: str
    ) -> bool:
        """检查权限"""
        # 获取用户身份
        identity = await self.identity_manager.get_user_identity(user_id)

        # 特权用户（徐健）拥有所有权限
        if identity.permissions.get('admin_access'):
            return True

        # 检查模块是否需要高级权限
        module_def = self.registry.get_module(module)
        if not module_def:
            return False

        # 某些模块需要高级权限
        if module in ['tool.export', 'tool.report'] and not identity.permissions.get('advanced_features'):
            return False

        return True

    def _validate_params(
        self,
        module_def: ModuleDefinition,
        action: str,
        params: Dict[str, Any]
    ) -> Optional[str]:
        """验证参数"""
        if action not in module_def.parameters:
            return None  # 没有参数定义，跳过验证

        param_def = module_def.parameters[action]

        # 检查必需参数
        for param_name, spec in param_def.items():
            if spec.get('required', False) and param_name not in params:
                return f"缺少必需参数: {param_name}"

            # 类型检查
            if param_name in params:
                expected_type = spec.get('type')
                if expected_type == 'string' and not isinstance(params[param_name], str):
                    return f"参数类型错误: {param_name} 应为字符串"
                elif expected_type == 'integer' and not isinstance(params[param_name], int):
                    return f"参数类型错误: {param_name} 应为整数"

        return None

    def _record_metrics(
        self,
        module: str,
        action: str,
        success: bool,
        execution_time: float
    ):
        """记录指标"""
        key = f"{module}.{action}"
        if key not in self._metrics:
            self._metrics[key] = {
                "total_calls": 0,
                "success_calls": 0,
                "failure_calls": 0,
                "total_time": 0.0,
            }

        self._metrics[key]["total_calls"] += 1
        if success:
            self._metrics[key]["success_calls"] += 1
        else:
            self._metrics[key]["failure_calls"] += 1
        self._metrics[key]["total_time"] += execution_time

    def get_metrics(self, module: Optional[str] = None) -> Dict:
        """获取调用指标"""
        if module:
            return {
                k: v for k, v in self._metrics.items()
                if k.startswith(f"{module}.")
            }
        return self._metrics.copy()


# ========== 小诺意图映射与调度 ==========

class XiaonuoIntentRouter:
    """小诺意图路由器"""

    def __init__(self, invoker: PlatformModuleInvoker):
        self.invoker = invoker
        self._intent_patterns: Dict[str, Dict] = {
            "patent_search": {
                "keywords": ["搜索", "查找", "找", "专利"],
                "module": "patent.search",
                "action": "search",
                "param_extractor": self._extract_patent_search_params,
            },
            "patent_analyze": {
                "keywords": ["分析", "评估", "价值", "创新性"],
                "module": "patent.analyze",
                "action": "analyze",
                "param_extractor": self._extract_patent_analyze_params,
            },
            "knowledge_query": {
                "keywords": ["查询", "知识", "相关"],
                "module": "knowledge.vector",
                "action": "search",
                "param_extractor": self._extract_knowledge_query_params,
            },
            "data_export": {
                "keywords": ["导出", "下载", "保存"],
                "module": "tool.export",
                "action": "export",
                "param_extractor": self._extract_export_params,
            },
        }

    async def route_and_execute(
        self,
        user_message: str,
        user_id: str,
        session_id: str
    ) -> tuple[str, Any]:
        """
        路由并执行用户意图

        Returns:
            (响应消息, 原始结果数据)
        """
        # 1. 意图识别
        intent = self._recognize_intent(user_message)
        if not intent:
            return "抱歉，我不太理解您的需求。能详细说明一下吗？", None

        # 2. 提取参数
        pattern = self._intent_patterns[intent]
        params = await pattern["param_extractor"](user_message)

        # 3. 构建调用请求
        request = InvokeRequest(
            session_id=session_id,
            module=pattern["module"],
            action=pattern["action"],
            params=params,
            user_id=user_id,
        )

        # 4. 执行调用
        result = await self.invoker.invoke(request)

        # 5. 格式化响应
        if result.success:
            response = await self._format_success_response(
                user_id,
                intent,
                result.data
            )
            return response, result.data
        else:
            response = await self._format_error_response(
                user_id,
                result.error
            )
            return response, None

    def _recognize_intent(self, message: str) -> Optional[str]:
        """识别用户意图"""
        message_lower = message.lower()

        for intent, pattern in self._intent_patterns.items():
            keyword_count = sum(
                1 for kw in pattern["keywords"]
                if kw in message_lower
            )
            if keyword_count >= 2:  # 至少匹配2个关键词
                return intent

        return None

    async def _extract_patent_search_params(self, message: str) -> Dict:
        """提取专利搜索参数"""
        # 简化版：提取关键词
        # 实际应该使用更智能的NLP
        keywords = message.replace("搜索", "").replace("专利", "").strip()
        return {"query": keywords, "limit": 10}

    async def _extract_patent_analyze_params(self, message: str) -> Dict:
        """提取专利分析参数"""
        # 提取专利ID（简化版）
        import re
        patent_id_match = re.search(r'[A-Z]{2}\d+[A-Z]?\d?', message)
        if patent_id_match:
            return {"patent_id": patent_id_match.group()}
        return {"patent_id": ""}  # 需要用户补充

    async def _extract_knowledge_query_params(self, message: str) -> Dict:
        """提取知识查询参数"""
        query = message.replace("查询", "").replace("知识", "").strip()
        return {"query": query, "top_k": 5}

    async def _extract_export_params(self, message: str) -> Dict:
        """提取导出参数"""
        # 默认导出当前会话
        return {"source": "session", "format": "markdown"}

    async def _format_success_response(
        self,
        user_id: str,
        intent: str,
        data: Any
    ) -> str:
        """格式化成功响应"""
        identity = await self.invoker.identity_manager.get_user_identity(user_id)
        address = self.invoker.identity_manager.get_address_term(user_id)

        if intent == "patent_search":
            count = len(data) if isinstance(data, list) else 0
            return f"好的{address}！找到了{count}个相关专利，请查看详情。"

        elif intent == "patent_analyze":
            return f"好的{address}！分析完成，这个专利的技术价值评估如下..."

        elif intent == "knowledge_query":
            return f"好的{address}！找到了相关资料，正在整理..."

        return "处理完成！"

    async def _format_error_response(self, user_id: str, error: str) -> str:
        """格式化错误响应"""
        identity = await self.invoker.identity_manager.get_user_identity(user_id)
        address = self.invoker.identity_manager.get_address_term(user_id)
        return f"抱歉{address}，处理请求时出现了问题：{error}"


# ========== 初始化示例 ==========

# 创建全局实例
registry = PlatformModuleRegistry()
# identity_manager 需要在实际使用时注入
invoker = PlatformModuleInvoker(registry, identity_manager=None)
router = XiaonuoIntentRouter(invoker)
```

### 3. 多媒体支持（小诺+Athena）

```python
# 文件处理服务
class FileProcessingService:
    """多媒体文件处理"""

    async def upload_file(
        file: UploadFile,
        user_id: str,
        session_id: str
    ) -> FileMetadata:
        """处理文件上传"""
        # 1. 验证文件类型和大小
        # 2. 病毒扫描
        # 3. 存储到对象存储
        # 4. 生成预览（图片/音频）
        # 5. 提取文本内容（OCR/语音识别）
        # 6. 向量化（用于语义搜索）
        pass

    async def process_document(
        file_path: str,
        file_type: str
    ) -> ProcessedDocument:
        """处理文档"""
        if file_type in ['.pdf', '.docx', '.doc']:
            # 提取文本内容
            text = await extract_text(file_path)
            # 生成向量嵌入
            embedding = await generate_embedding(text)
            return ProcessedDocument(
                content=text,
                embedding=embedding,
                pages=await extract_pages(file_path)
            )

    async def process_audio(
        file_path: str
    ) -> ProcessedAudio:
        """处理音频"""
        # 语音识别
        transcript = await transcribe_audio(file_path)
        # 生成向量嵌入
        embedding = await generate_embedding(transcript)
        return ProcessedAudio(
            transcript=transcript,
            embedding=embedding,
            duration=await get_duration(file_path)
        )

# 前端上传组件
const FileUploadZone: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleDrop = async (files: File[]) => {
    setUploading(true);
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);

      const { data } = await axios.post('/api/files/upload', formData, {
        onUploadProgress: (e) => setProgress(e.progress * 100)
      });

      // 添加到消息列表
      addMessage({
        type: 'file',
        content: data.metadata,
        user: 'currentUser'
      });
    }
    setUploading(false);
  };

  return (
    <Dropzone onDrop={handleDrop} accept={ACCEPTED_TYPES}>
      {({ getRootProps }) => (
        <div {...getRootProps()} className="border-dashed border-2 p-8">
          <UploadIcon className="w-12 h-12" />
          <p>拖拽文件到此处，或点击选择</p>
          <p className="text-sm text-gray-500">
            支持文档、图片、音频（最大50MB）
          </p>
        </div>
      )}
    </Dropzone>
  );
};
```

### 3. 导出功能（Athena实现）

```python
# 导出服务
class ExportService:
    """导出服务"""

    async def export_to_markdown(
        session_id: str
    ) -> bytes:
        """导出为Markdown"""
        messages = await self.get_session_messages(session_id)

        markdown = f"# {session.title}\n\n"
        markdown += f"导出时间: {datetime.now()}\n\n"

        for msg in messages:
            markdown += f"## {msg.role} - {msg.created_at}\n"
            markdown += f"{msg.content}\n\n"

            if msg.attachments:
                for att in msg.attachments:
                    markdown += f"📎 {att.filename}\n"

        return markdown.encode('utf-8')

    async def export_to_docx(
        session_id: str
    ) -> bytes:
        """导出为DOCX"""
        from docx import Document

        messages = await self.get_session_messages(session_id)
        doc = Document()
        doc.add_heading(session.title, 0)

        for msg in messages:
            p = doc.add_paragraph()
            p.add_run(f"{msg.role}: ").bold = True
            p.add_run(msg.content)

        output = BytesIO()
        doc.save(output)
        return output.getvalue()

    async def export_to_excel(
        session_id: str
    ) -> bytes:
        """导出为Excel"""
        import pandas as pd

        messages = await self.get_session_messages(session_id)
        df = pd.DataFrame([
            {
                '时间': msg.created_at,
                '角色': msg.role,
                '内容': msg.content,
                '附件': ', '.join([a.filename for a in msg.attachments])
            }
            for msg in messages
        ])

        output = BytesIO()
        df.to_excel(output, index=False)
        return output.getvalue()

# 前端导出组件
const ExportMenu: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const exportFile = async (format: 'markdown' | 'docx' | 'excel') => {
    const response = await fetch(`/api/export/${sessionId}/${format}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${sessionId}.${format}`;
    a.click();
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          导出
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem onClick={() => exportFile('markdown')}>
          📝 Markdown
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => exportFile('docx')}>
          📄 Word (DOCX)
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => exportFile('excel')}>
          📊 Excel
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
```

### 4. 人机协作编辑（小诺设计）

```typescript
// 可编辑计划组件
interface PlanItem {
  id: string;
  title: string;
  status: 'pending' | 'in_progress' | 'completed';
  assignee: string;
  dueDate?: Date;
  subtasks?: PlanItem[];
}

const EditablePlan: React.FC = () => {
  const [plan, setPlan] = useState<PlanItem[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);

  // AI生成计划
  const generatePlan = async () => {
    const { data } = await axios.post('/api/ai/generate-plan', {
      context: getConversationContext()
    });
    setPlan(data.plan);
  };

  // 编辑项目
  const editItem = (id: string, updates: Partial<PlanItem>) => {
    setPlan(plan.map(item =>
      item.id === id ? { ...item, ...updates } : item
    ));
    // 同步到服务器
    axios.patch(`/api/plan/${id}`, updates);
  };

  // 添加新项目
  const addItem = () => {
    const newItem: PlanItem = {
      id: generateId(),
      title: '新任务',
      status: 'pending',
      assignee: 'currentUser'
    };
    setPlan([...plan, newItem]);
  };

  return (
    <div className="plan-container">
      <div className="plan-header">
        <h3>📋 实施计划</h3>
        <Button onClick={generatePlan}>✨ AI生成计划</Button>
        <Button onClick={addItem}>➕ 添加任务</Button>
      </div>

      <div className="plan-list">
        {plan.map(item => (
          <PlanItemComponent
            key={item.id}
            item={item}
            isEditing={editingId === item.id}
            onEdit={(updates) => editItem(item.id, updates)}
            onStartEdit={() => setEditingId(item.id)}
            onFinishEdit={() => setEditingId(null)}
          />
        ))}
      </div>
    </div>
  );
};

const PlanItemComponent: React.FC<{
  item: PlanItem;
  isEditing: boolean;
  onEdit: (updates: Partial<PlanItem>) => void;
  onStartEdit: () => void;
  onFinishEdit: () => void;
}> = ({ item, isEditing, onEdit, onStartEdit, onFinishEdit }) => {
  if (isEditing) {
    return (
      <div className="plan-item editing">
        <input
          value={item.title}
          onChange={(e) => onEdit({ title: e.target.value })}
          autoFocus
        />
        <select
          value={item.status}
          onChange={(e) => onEdit({ status: e.target.value })}
        >
          <option value="pending">待处理</option>
          <option value="in_progress">进行中</option>
          <option value="completed">已完成</option>
        </select>
        <Button onClick={onFinishEdit}>✓</Button>
      </div>
    );
  }

  return (
    <div className="plan-item" onClick={onStartEdit}>
      <span className={`status ${item.status}`}>
        {item.status === 'completed' && '✓'}
        {item.status === 'in_progress' && '→'}
        {item.status === 'pending' && '○'}
      </span>
      <span className="title">{item.title}</span>
      <span className="assignee">{item.assignee}</span>
    </div>
  );
};
```

### 5. 工作轨迹记录（Athena实现）

```python
# 轨迹记录服务
class ActivityTrackingService:
    """活动轨迹记录"""

    async def track_activity(
        user_id: str,
        session_id: str,
        action_type: str,
        metadata: dict = None
    ):
        """记录用户活动"""
        activity = Activity(
            id=generate_id(),
            user_id=user_id,
            session_id=session_id,
            action_type=action_type,  # message_sent, file_uploaded, plan_edited, etc.
            metadata=metadata or {},
            timestamp=datetime.now(),
            ip_address=get_client_ip()
        )
        await self.activity_repo.create(activity)

        # 实时推送给用户
        await self.websocket_manager.broadcast_to_user(
            user_id,
            {'type': 'activity', 'data': activity}
        )

    async def get_activity_timeline(
        session_id: str,
        limit: int = 100
    ) -> List[Activity]:
        """获取活动时间线"""
        return await self.activity_repo.find_by_session(
            session_id,
            limit=limit,
            order_by='timestamp DESC'
        )

# 前端轨迹组件
const ActivityTimeline: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const { data: activities } = useSWR(
    `/api/activities/${sessionId}`,
    fetcher
  );

  const getActivityIcon = (type: string) => {
    const icons = {
      message_sent: '💬',
      file_uploaded: '📎',
      plan_edited: '✏️',
      plan_completed: '✅',
      ai_response: '🤖'
    };
    return icons[type] || '•';
  };

  return (
    <div className="activity-timeline">
      <h3>📊 工作轨迹</h3>
      <div className="timeline-list">
        {activities?.map(activity => (
          <div key={activity.id} className="timeline-item">
            <span className="icon">
              {getActivityIcon(activity.action_type)}
            </span>
            <span className="time">
              {formatDistanceToNow(new Date(activity.timestamp))}
            </span>
            <span className="description">
              {getActivityDescription(activity)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 6. 对话历史缓存（Athena实现）

```python
# 缓存策略
class ConversationCacheService:
    """对话缓存服务"""

    def __init__(self):
        self.redis = Redis()
        self.local_cache = LRUCache(maxsize=1000)

    async def cache_message(
        self,
        session_id: str,
        message: Message
    ):
        """缓存消息"""
        # 1. 本地缓存（快速访问）
        self.local_cache[f"{session_id}:{message.id}"] = message

        # 2. Redis缓存（共享访问）
        await self.redis.setex(
            f"msg:{session_id}:{message.id}",
            3600,  # 1小时过期
            message.json()
        )

        # 3. 持久化到数据库
        await self.message_repo.create(message)

    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Message]:
        """获取会话消息（多级缓存）"""
        # 1. 尝试从本地缓存获取
        local_key = f"session:{session_id}:messages"
        if local_key in self.local_cache:
            return self.local_cache[local_key]

        # 2. 尝试从Redis获取
        redis_key = f"session:{session_id}:messages"
        cached = await self.redis.get(redis_key)
        if cached:
            messages = Message.parse_raw(cached)
            self.local_cache[local_key] = messages
            return messages

        # 3. 从数据库获取
        messages = await self.message_repo.find_by_session(
            session_id,
            limit=limit,
            order_by='created_at ASC'
        )

        # 回填缓存
        self.local_cache[local_key] = messages
        await self.redis.setex(redis_key, 600, messages.json())

        return messages

    async def search_messages(
        self,
        session_id: str,
        query: str,
        search_type: 'keyword' | 'semantic' = 'keyword'
    ) -> List[Message]:
        """搜索消息"""
        if search_type == 'semantic':
            # 语义搜索（使用向量）
            query_embedding = await self.embedding_service.embed(query)
            results = await self.vector_store.search(
                collection=f"session:{session_id}",
                vector=query_embedding,
                top_k=10
            )
            return [r.payload for r in results]
        else:
            # 关键词搜索
            return await self.message_repo.search(
                session_id=session_id,
                query=query
            )

# 前端消息缓存
const useMessages = (sessionId: string) => {
  const { data, mutate } = useSWR(
    `/api/sessions/${sessionId}/messages`,
    fetcher,
    {
      revalidateOnFocus: false,
      dedupingInterval: 1000
    }
  );

  // 本地 optimistic 更新
  const addMessage = (message: Message) => {
    mutate(
      [...(data || []), message],
      false  // 不立即重新验证
    );

    // 发送到服务器
    axios.post(`/api/sessions/${sessionId}/messages`, message);
  };

  return {
    messages: data || [],
    addMessage,
    mutate
  };
};
```

---

## 📊 数据库Schema设计

### 核心数据表

```sql
-- 用户表（扩展版，支持多租户和权限管理）
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'user',  -- admin, user, guest, vip
    profile JSONB DEFAULT '{}',

    -- 存储配额管理
    storage_quota BIGINT DEFAULT 536870912,  -- 默认512MB
    storage_used BIGINT DEFAULT 0,

    -- 权限管理
    permissions JSONB DEFAULT '{}',  -- 基础权限
    temporary_permissions JSONB DEFAULT '[]',  -- 临时权限

    -- 账户状态
    status VARCHAR(50) DEFAULT 'active',  -- active, suspended, deleted
    organization_id UUID,  -- 企业版支持

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL,

    INDEX idx_user_status (status, deleted_at),
    INDEX idx_user_org (organization_id)
);

-- 会话表
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(500) NOT NULL,
    metadata JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL,
    INDEX idx_user_sessions (user_id, deleted_at),
    INDEX idx_updated (updated_at DESC)
);

-- 消息表
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),  -- pgvector
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_session_messages (session_id, created_at),
    INDEX idx_embedding USING ivfflat (embedding vector_cosine_ops)
);

-- 文件表（扩展版，支持多维度分类）
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,

    -- 基础信息
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    file_category VARCHAR(50),  -- document, image, audio, video, other
    file_size BIGINT NOT NULL,

    -- 存储信息
    storage_path TEXT NOT NULL,
    storage_bucket VARCHAR(255) DEFAULT 'user_files',
    storage_key TEXT NOT NULL,  -- 完整的对象存储Key

    -- 访问控制
    access_level VARCHAR(50) DEFAULT 'private',  -- private, session, public
    access_count INTEGER DEFAULT 0,

    -- 安全信息
    checksum VARCHAR(64),  -- SHA-256校验和
    is_scanned BOOLEAN DEFAULT FALSE,
    scan_result VARCHAR(50),  -- clean, infected, suspicious

    -- 软删除
    deleted_at TIMESTAMP NULL,
    delete_scheduled_at TIMESTAMP NULL,  -- 定时删除

    -- 元数据
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_user_files (user_id, deleted_at),
    INDEX idx_session_files (session_id),
    INDEX idx_file_category (file_category),
    INDEX idx_storage_key (storage_key)
);

-- 计划表
CREATE TABLE plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- pending, in_progress, completed
    assignee VARCHAR(100),
    due_date TIMESTAMP,
    parent_id UUID REFERENCES plans(id) ON DELETE CASCADE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_session_plans (session_id, sort_order)
);

-- 活动轨迹表
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    action_type VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_activities (user_id, created_at DESC),
    INDEX idx_session_activities (session_id, created_at DESC)
);

-- 权限表（RBAC模型）
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    resource_type VARCHAR(50),  -- system, session, file, export
    action VARCHAR(50),  -- create, read, update, delete, share
    created_at TIMESTAMP DEFAULT NOW()
);

-- 角色表
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 角色权限关联表
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

-- 用户角色关联表
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NULL,  -- 支持临时角色
    PRIMARY KEY (user_id, role_id)
);

-- 文件访问日志表（安全审计）
CREATE TABLE file_access_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    file_id UUID REFERENCES files(id),
    action VARCHAR(50) NOT NULL,  -- upload, download, view, delete, share
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_file_access (file_id, created_at DESC),
    INDEX idx_user_file_access (user_id, created_at DESC)
);

-- 配置表（系统配置）
CREATE TABLE system_config (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 默认权限数据

```sql
-- 插入默认权限
INSERT INTO permissions (name, description, resource_type, action) VALUES
('session.create', '创建会话', 'session', 'create'),
('session.read', '查看会话', 'session', 'read'),
('session.update', '编辑会话', 'session', 'update'),
('session.delete', '删除会话', 'session', 'delete'),
('file.upload', '上传文件', 'file', 'create'),
('file.download', '下载文件', 'file', 'read'),
('file.delete', '删除文件', 'file', 'delete'),
('file.share', '分享文件', 'file', 'share'),
('export.markdown', '导出Markdown', 'export', 'read'),
('export.docx', '导出Word', 'export', 'read'),
('export.excel', '导出Excel', 'export', 'read'),
('admin.users', '管理用户', 'system', 'update'),
('admin.config', '系统配置', 'system', 'update');

-- 插入默认角色
INSERT INTO roles (name, description, is_system_role) VALUES
('ADMIN', '系统管理员', TRUE),
('USER', '普通用户', TRUE),
('GUEST', '访客', TRUE),
('VIP', '高级用户', TRUE);

-- ADMIN角色拥有所有权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.name = 'ADMIN';

-- USER角色基础权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'USER' AND p.name IN (
    'session.create', 'session.read', 'session.update', 'session.delete',
    'file.upload', 'file.download', 'file.delete',
    'export.markdown', 'export.docx', 'export.excel'
);

-- GUEST角色只读权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'GUEST' AND p.name IN ('session.read', 'file.download');

-- VIP用户高级权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'VIP' AND p.name IN (
    'session.create', 'session.read', 'session.update', 'session.delete',
    'file.upload', 'file.download', 'file.delete', 'file.share',
    'export.markdown', 'export.docx', 'export.excel'
);
```

---

## 🌐 Gateway服务器实现

### 架构设计

```python
# ========== Gateway服务器实现 ==========

from fastapi import WebSocket, WebSocketDisconnect, status
from fastapi.websockets import WebSocketState
from typing import Dict, Optional, Set, Any
import json
import asyncio
from datetime import datetime
import uuid


# ========== 协议定义 ==========

class FrameType:
    """消息帧类型"""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"


class GatewayProtocol:
    """Gateway协议处理器"""

    @staticmethod
    def create_request(
        method: str,
        params: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> Dict:
        """创建请求帧"""
        return {
            "type": FrameType.REQUEST,
            "id": request_id or str(uuid.uuid4()),
            "method": method,
            "params": params,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def create_response(
        request_id: str,
        result: Any,
        error: Optional[str] = None
    ) -> Dict:
        """创建响应帧"""
        frame = {
            "type": FrameType.RESPONSE,
            "id": request_id,
            "timestamp": datetime.now().isoformat(),
        }

        if error:
            frame["error"] = error
        else:
            frame["result"] = result

        return frame

    @staticmethod
    def create_event(
        event_type: str,
        data: Dict[str, Any]
    ) -> Dict:
        """创建事件帧"""
        return {
            "type": FrameType.EVENT,
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def validate_frame(frame: Dict) -> bool:
        """验证消息帧"""
        required_fields = ["type", "timestamp"]
        if not all(field in frame for field in required_fields):
            return False

        if frame["type"] == FrameType.REQUEST:
            return "method" in frame and "id" in frame
        elif frame["type"] == FrameType.RESPONSE:
            return "id" in frame
        elif frame["type"] == FrameType.EVENT:
            return "event" in frame

        return False


# ========== 会话管理 ==========

class GatewaySession:
    """Gateway会话"""

    def __init__(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str
    ):
        self.websocket = websocket
        self.session_id = session_id
        self.user_id = user_id
        self.connected = True
        self.subscriptions: Set[str] = set()  # 事件订阅

        # 配置项
        self.thinking_enabled: bool = False
        self.verbose_enabled: bool = False
        self.model: Optional[str] = None

    async def send_frame(self, frame: Dict):
        """发送消息帧"""
        if not self.connected:
            return

        try:
            await self.websocket.send_json(frame)
        except Exception as e:
            self.connected = False
            raise

    async def send_event(self, event_type: str, data: Dict):
        """发送事件"""
        if event_type in self.subscriptions:
            frame = GatewayProtocol.create_event(event_type, data)
            await self.send_frame(frame)

    def subscribe(self, event_type: str):
        """订阅事件"""
        self.subscriptions.add(event_type)

    def unsubscribe(self, event_type: str):
        """取消订阅"""
        self.subscriptions.discard(event_type)

    def disconnect(self):
        """断开连接"""
        self.connected = False


class GatewaySessionManager:
    """Gateway会话管理器"""

    def __init__(self):
        self.sessions: Dict[str, GatewaySession] = {}  # session_id -> session
        self.user_sessions: Dict[str, Set[str]] = {}    # user_id -> set of session_ids

    async def create_session(
        self,
        websocket: WebSocket,
        user_id: str,
        session_id: Optional[str] = None
    ) -> GatewaySession:
        """创建新会话"""
        if not session_id:
            session_id = str(uuid.uuid4())

        session = GatewaySession(
            websocket=websocket,
            session_id=session_id,
            user_id=user_id
        )

        self.sessions[session_id] = session

        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)

        return session

    def get_session(self, session_id: str) -> Optional[GatewaySession]:
        """获取会话"""
        return self.sessions.get(session_id)

    def get_user_sessions(self, user_id: str) -> List[GatewaySession]:
        """获取用户的所有会话"""
        session_ids = self.user_sessions.get(user_id, set())
        return [
            self.sessions[sid]
            for sid in session_ids
            if sid in self.sessions
        ]

    async def close_session(self, session_id: str):
        """关闭会话"""
        session = self.sessions.get(session_id)
        if session:
            session.disconnect()

            # 从用户会话列表中移除
            if session.user_id in self.user_sessions:
                self.user_sessions[session.user_id].discard(session_id)

            # 删除会话
            del self.sessions[session_id]


# ========== 方法处理器 ==========

class GatewayMethodHandler:
    """Gateway方法处理器"""

    def __init__(
        self,
        session_manager: GatewaySessionManager,
        identity_manager: "XiaonuoIdentityManager",
        intent_router: "XiaonuoIntentRouter",
        platform_invoker: "PlatformModuleInvoker",
    ):
        self.session_manager = session_manager
        self.identity_manager = identity_manager
        self.intent_router = intent_router
        self.platform_invoker = platform_invoker

    async def handle_request(
        self,
        session: GatewaySession,
        request: Dict
    ) -> Dict:
        """处理请求"""

        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            # 聊天方法
            if method == "send":
                return await self._handle_send(session, params)

            elif method == "poll":
                return await self._handle_poll(session, params)

            elif method == "abort":
                return await self._handle_abort(session, params)

            # 平台能力方法
            elif method == "platform_modules":
                return await self._handle_platform_modules(session, params)

            elif method == "platform_invoke":
                return await self._handle_platform_invoke(session, params)

            # 会话管理方法
            elif method == "sessions_list":
                return await self._handle_sessions_list(session, params)

            elif method == "sessions_patch":
                return await self._handle_sessions_patch(session, params)

            elif method == "sessions_reset":
                return await self._handle_sessions_reset(session, params)

            elif method == "sessions_compact":
                return await self._handle_sessions_compact(session, params)

            # 配置管理方法
            elif method == "config_get":
                return await self._handle_config_get(session, params)

            elif method == "config_set":
                return await self._handle_config_set(session, params)

            elif method == "config_patch":
                return await self._handle_config_patch(session, params)

            else:
                return GatewayProtocol.create_response(
                    request_id=request_id,
                    result=None,
                    error=f"未知方法: {method}"
                )

        except Exception as e:
            return GatewayProtocol.create_response(
                request_id=request_id,
                result=None,
                error=str(e)
            )

    async def _handle_send(
        self,
        session: GatewaySession,
        params: Dict
    ) -> Dict:
        """处理send方法（发送消息）"""
        message = params.get("message")
        if not message:
            return {"error": "缺少message参数"}

        # 使用意图路由器处理消息
        response, data = await self.intent_router.route_and_execute(
            user_message=message,
            user_id=session.user_id,
            session_id=session.session_id
        )

        # 发送响应事件
        await session.send_event("chat.message", {
            "role": "assistant",
            "content": response,
            "data": data,
        })

        return {"success": True}

    async def _handle_poll(
        self,
        session: GatewaySession,
        params: Dict
    ) -> Dict:
        """处理poll方法（拉取消息）"""
        # 简化版：返回空列表
        return {"messages": []}

    async def _handle_abort(
        self,
        session: GatewaySession,
        params: Dict
    ) -> Dict:
        """处理abort方法（中止操作）"""
        return {"success": True}

    async def _handle_platform_modules(
        self,
        session: GatewaySession,
        params: Dict
    ) -> Dict:
        """处理platform_modules方法（获取可用模块）"""
        # 返回所有可用模块列表
        modules = self.platform_invoker.registry.list_modules()

        result = {
            "modules": [
                {
                    "name": m.name,
                    "display_name": m.display_name,
                    "description": m.description,
                    "category": m.category,
                    "actions": m.actions,
                }
                for m in modules
            ]
        }

        return result

    async def _handle_platform_invoke(
        self,
        session: GatewaySession,
        params: Dict
    ) -> Dict:
        """处理platform_invoke方法（调用平台模块）"""
        request = InvokeRequest(
            session_id=session.session_id,
            module=params.get("module"),
            action=params.get("action"),
            params=params.get("params", {}),
            user_id=session.user_id,
        )

        result = await self.platform_invoker.invoke(request)

        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
        }

    async def _handle_sessions_list(
        self,
        session: GatewaySession,
        params: Dict
    ) -> Dict:
        """处理sessions_list方法"""
        user_sessions = self.session_manager.get_user_sessions(session.user_id)

        return {
            "sessions": [
                {
                    "session_id": s.session_id,
                    "connected": s.connected,
                }
                for s in user_sessions
            ]
        }

    async def _handle_sessions_patch(
        self,
        session: GatewaySession,
        params: Dict
    ) -> Dict:
        """处理sessions_patch方法"""
        updates = params.get("updates", {})

        if "thinking" in updates:
            session.thinking_enabled = updates["thinking"]
        if "verbose" in updates:
            session.verbose_enabled = updates["verbose"]
        if "model" in updates:
            session.model = updates["model"]

        return {"success": True}

    async def _handle_sessions_reset(
        self,
        session: GatewaySession,
        params: Dict
    ) -> Dict:
        """处理sessions_reset方法"""
        # 清除会话状态
        return {"success": True}

    async def _handle_sessions_compact(
        self,
        session: GatewaySession,
        params: Dict
    ) -> Dict:
        """处理sessions_compact方法"""
        # 压缩会话历史
        return {"success": True}

    async def _handle_config_get(
        self,
        session: GatewaySession,
        params: Dict
    ) -> Dict:
        """处理config_get方法"""
        key = params.get("key")

        config = {
            "thinking": session.thinking_enabled,
            "verbose": session.verbose_enabled,
            "model": session.model,
        }

        if key:
            return {"value": config.get(key)}
        return config

    async def _handle_config_set(
        self,
        session: GatewaySession,
        params: Dict
    ) -> Dict:
        """处理config_set方法"""
        key = params.get("key")
        value = params.get("value")

        if key == "thinking":
            session.thinking_enabled = value
        elif key == "verbose":
            session.verbose_enabled = value
        elif key == "model":
            session.model = value

        return {"success": True}

    async def _handle_config_patch(
        self,
        session: GatewaySession,
        params: Dict
    ) -> Dict:
        """处理config_patch方法"""
        updates = params.get("updates", {})

        for key, value in updates.items():
            if key == "thinking":
                session.thinking_enabled = value
            elif key == "verbose":
                session.verbose_enabled = value
            elif key == "model":
                session.model = value

        return {"success": True}


# ========== Gateway服务器 ==========

class WebChatGatewayServer:
    """WebChat Gateway服务器"""

    def __init__(
        self,
        identity_manager: "XiaonuoIdentityManager",
        intent_router: "XiaonuoIntentRouter",
        platform_invoker: "PlatformModuleInvoker",
    ):
        self.session_manager = GatewaySessionManager()
        self.method_handler = GatewayMethodHandler(
            session_manager=self.session_manager,
            identity_manager=identity_manager,
            intent_router=intent_router,
            platform_invoker=platform_invoker,
        )

        # 心跳间隔
        self.heartbeat_interval = 30

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        session_id: Optional[str] = None
    ):
        """处理WebSocket连接"""
        await websocket.accept()

        # 创建会话
        session = await self.session_manager.create_session(
            websocket=websocket,
            user_id=user_id,
            session_id=session_id
        )

        # 发送连接确认事件
        await session.send_event("connected", {
            "session_id": session.session_id,
            "user_id": user_id,
        })

        # 启动心跳
        asyncio.create_task(self._heartbeat_loop(session))

        # 消息处理循环
        try:
            while session.connected:
                data = await websocket.receive_text()

                try:
                    frame = json.loads(data)

                    # 验证消息帧
                    if not GatewayProtocol.validate_frame(frame):
                        await session.send_frame(
                            GatewayProtocol.create_response(
                                request_id=frame.get("id", ""),
                                result=None,
                                error="无效的消息帧"
                            )
                        )
                        continue

                    # 处理请求
                    if frame["type"] == FrameType.REQUEST:
                        response = await self.method_handler.handle_request(
                            session, frame
                        )
                        response["id"] = frame.get("id")
                        await session.send_frame(response)

                except json.JSONDecodeError:
                    await session.send_frame(
                        GatewayProtocol.create_response(
                            request_id="",
                            result=None,
                            error="JSON解析错误"
                        )
                    )

        except WebSocketDisconnect:
            await self.session_manager.close_session(session.session_id)
        except Exception as e:
            await session.send_event("error", {"message": str(e)})
            await self.session_manager.close_session(session.session_id)

    async def _heartbeat_loop(self, session: GatewaySession):
        """心跳循环"""
        while session.connected:
            try:
                await session.send_event("heartbeat", {
                    "timestamp": datetime.now().isoformat()
                })
                await asyncio.sleep(self.heartbeat_interval)
            except Exception:
                break
```

### FastAPI路由集成

```python
from fastapi import APIRouter, WebSocket, Depends, Query
from fastapi.responses import HTMLResponse

# 创建路由
router = APIRouter(prefix="/gateway", tags=["Gateway"])

# 全局Gateway实例（在应用启动时初始化）
gateway_server: Optional[WebChatGatewayServer] = None


@router.websocket("/ws")
async def gateway_websocket(
    websocket: WebSocket,
    user_id: str = Query(...),
    session_id: Optional[str] = Query(None),
):
    """Gateway WebSocket端点"""
    if gateway_server is None:
        await websocket.close(code=1011, reason="服务器未初始化")
        return

    await gateway_server.connect(
        websocket=websocket,
        user_id=user_id,
        session_id=session_id
    )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(gateway_server.session_manager.sessions)
            if gateway_server else 0,
    }
```

### 配置管理

```python
# ========== 配置管理 ==========

from pydantic_settings import BaseSettings


class GatewaySettings(BaseSettings):
    """Gateway配置"""

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # WebSocket配置
    heartbeat_interval: int = 30
    max_message_size: int = 1048576  # 1MB
    max_connections: int = 1000

    # 安全配置
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # 身份配置
    default_user_id: str = "guest"
    admin_user_id: str = "xujian"

    # 模块配置
    enable_module_cache: bool = True
    module_health_check_interval: int = 60

    class Config:
        env_file = ".env"
        env_prefix = "GATEWAY_"


# 配置实例
settings = GatewaySettings()
```

---

## 🔐 多租户架构设计

### 架构概述

```
┌─────────────────────────────────────────────────────────────────────┐
│                        多租户隔离架构                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  L1: 应用层隔离                   L2: 存储层隔离  L3: 缓存层隔离   │
│  ┌─────────────────────┐      ┌──────────────┐   ┌──────────────┐ │
│  │  user_id 过滤       │      │  Bucket隔离   │   │  Redis命名   │ │
│  │  RLS 策略           │      │  Path隔离     │   │  空间隔离     │ │
│  │  API 验证           │      │  Access Key  │   │  TTL策略     │ │
│  └─────────────────────┘      └──────────────┘   └──────────────┘ │
│           ↓                            ↓                  ↓         │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │                    统一权限管理层                               ││
│  │  RBAC模型 | 临时权限 | 资源配额 | 审计日志                     ││
│  └────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### 1. 文件分类管理体系

#### 1.1 双重分类索引

```python
# 文件分类服务
class FileClassificationService:
    """文件分类管理服务"""

    # 按用户分类
    async def classify_by_user(self, user_id: str) -> dict:
        """按用户获取文件统计"""
        return {
            "total_files": await self.db.count_files(user_id=user_id),
            "by_category": {
                "documents": await self.db.count_files(user_id, category="document"),
                "images": await self.db.count_files(user_id, category="image"),
                "audio": await self.db.count_files(user_id, category="audio"),
                "video": await self.db.count_files(user_id, category="video"),
            },
            "storage_used": await self.db.get_storage_usage(user_id)
        }

    # 按会话分类
    async def classify_by_session(self, session_id: str) -> list:
        """按会话获取文件列表"""
        return await self.db.get_files_by_session(session_id)

    # 按时间分类
    async def classify_by_time(self, user_id: str, period: str) -> list:
        """按时间段获取文件"""
        now = datetime.now()
        if period == "today":
            start = now.replace(hour=0, minute=0, second=0)
        elif period == "week":
            start = now - timedelta(days=7)
        elif period == "month":
            start = now.replace(day=1)
        return await self.db.get_files_by_time(user_id, start, now)
```

#### 1.2 文件存储结构

```
user_files/                           # 根Bucket
├── user_{uuid}/                      # 用户隔离目录
│   ├── uploads/                      # 用户上传文件
│   │   └── 2024/
│   │       ├── 01/
│   │       │   ├── documents/        # 文档类
│   │       │   ├── images/           # 图片类
│   │       │   └── audio/            # 音频类
│   │       └── 02/
│   ├── exports/                      # 导出文件
│   │   ├── markdown/
│   │   ├── docx/
│   │   └── excel/
│   └── .trash/                       # 回收站（30天后清理）
│       └── {file_uuid}/
└── temp/                             # 临时文件（24小时清理）
    └── {session_uuid}/
```

### 2. 用户存储隔离体系

#### 2.1 三层隔离机制

```python
# 用户隔离服务
class UserIsolationService:
    """用户存储隔离服务"""

    # L1: 应用层隔离
    async def check_user_access(
        self,
        user_id: str,
        resource_id: str,
        resource_type: str
    ) -> bool:
        """检查用户是否有权限访问资源"""
        # Row-Level Security 检查
        resource = await self.db.get_resource(resource_id, resource_type)
        if not resource:
            return False

        # 检查资源所有权
        if resource.user_id != user_id:
            # 检查是否有访问权限
            return await self.check_permission(user_id, resource_id)

        return True

    # L2: 存储层隔离
    async def get_user_storage_key(
        self,
        user_id: str,
        file_category: str,
        filename: str
    ) -> str:
        """生成用户专属的存储Key"""
        # 格式: user_{uuid}/uploads/{year}/{month}/{category}/{uuid_filename}
        now = datetime.now()
        return (
            f"user_{user_id}/uploads/"
            f"{now.year}/{now.month:02d}/{file_category}/"
            f"{uuid4()}_{filename}"
        )

    async def get_signed_url(
        self,
        user_id: str,
        file_id: str,
        expiry: int = 3600
    ) -> str:
        """生成带签名的访问URL"""
        file = await self.db.get_file(file_id)

        # 验证用户权限
        if file.user_id != user_id:
            raise PermissionError("无权访问此文件")

        # 使用RustFS生成签名URL
        return await self.rustfs.sign_url(
            key=file.storage_key,
            expiry=expiry,
            access_key=user_id  # 用户专属Access Key
        )

    # L3: 缓存层隔离
    async def cache_user_data(self, user_id: str, key: str, value: any, ttl: int = 3600):
        """缓存用户数据（带命名空间隔离）"""
        cache_key = f"user:{user_id}:{key}"
        await self.redis.setex(cache_key, ttl, value)

    async def get_user_cached_data(self, user_id: str, key: str) -> any:
        """获取用户缓存数据"""
        cache_key = f"user:{user_id}:{key}"
        return await self.redis.get(cache_key)
```

#### 2.2 存储配额管理

```python
# 配额管理服务
class QuotaManagementService:
    """存储配额管理服务"""

    async def check_upload_quota(self, user_id: str, file_size: int) -> bool:
        """检查上传配额"""
        user = await self.db.get_user(user_id)

        # 检查是否超出配额
        if user.storage_used + file_size > user.storage_quota:
            raise QuotaExceededError(
                f"存储配额不足: {user.storage_used}/{user.storage_quota} bytes"
            )

        return True

    async def update_storage_usage(self, user_id: str, delta: int):
        """更新存储使用量"""
        await self.db.execute("""
            UPDATE users
            SET storage_used = storage_used + $1
            WHERE id = $2 AND storage_used + $1 >= 0
        """, delta, user_id)

    async def get_quota_status(self, user_id: str) -> dict:
        """获取配额状态"""
        user = await self.db.get_user(user_id)
        usage_percent = (user.storage_used / user.storage_quota) * 100

        return {
            "quota": user.storage_quota,
            "used": user.storage_used,
            "available": user.storage_quota - user.storage_used,
            "usage_percent": usage_percent,
            "status": "warning" if usage_percent > 80 else "ok"
        }
```

### 3. 权限管理系统

#### 3.1 RBAC权限模型

```python
# 权限管理服务
class PermissionService:
    """权限管理服务"""

    async def check_permission(
        self,
        user_id: str,
        permission_name: str,
        resource_id: str = None
    ) -> bool:
        """检查用户权限"""
        # 获取用户角色
        user_roles = await self.db.get_user_roles(user_id)

        # 检查临时权限
        temp_permissions = await self.db.get_temporary_permissions(user_id)
        if permission_name in [p['name'] for p in temp_permissions]:
            # 检查是否过期
            for p in temp_permissions:
                if p['name'] == permission_name:
                    if p.get('expires_at') and datetime.now() > p['expires_at']:
                        await self.db.remove_temp_permission(user_id, permission_name)
                        return False
                    return True

        # 检查角色权限
        for role in user_roles:
            role_permissions = await self.db.get_role_permissions(role['role_id'])
            if permission_name in [p['name'] for p in role_permissions]:
                return True

        return False

    async def grant_permission(
        self,
        admin_user_id: str,
        target_user_id: str,
        permission_name: str,
        expires_at: datetime = None
    ):
        """授予权限（管理员功能）"""
        # 验证管理员权限
        if not await self.check_permission(admin_user_id, 'admin.users'):
            raise PermissionError("需要管理员权限")

        # 检查权限是否存在
        permission = await self.db.get_permission(permission_name)
        if not permission:
            raise ValueError(f"权限不存在: {permission_name}")

        # 授予临时权限
        await self.db.grant_temporary_permission(
            user_id=target_user_id,
            permission_id=permission['id'],
            granted_by=admin_user_id,
            expires_at=expires_at
        )

        # 记录审计日志
        await self.audit_log.create(
            action='grant_permission',
            user_id=admin_user_id,
            target_user_id=target_user_id,
            permission_name=permission_name
        )
```

#### 3.2 资源访问控制

```python
# 访问控制服务
class AccessControlService:
    """资源访问控制服务"""

    async def can_access_file(
        self,
        user_id: str,
        file_id: str,
        action: str
    ) -> bool:
        """检查文件访问权限"""
        file = await self.db.get_file(file_id)

        # 检查文件是否存在
        if not file or file.deleted_at:
            return False

        # 文件所有者拥有所有权限
        if file.user_id == user_id:
            return True

        # 检查访问级别
        if file.access_level == 'public':
            return True

        if file.access_level == 'session':
            # 检查是否在同一会话中
            session = await self.db.get_session(file.session_id)
            return session and session.user_id == user_id

        if file.access_level == 'private':
            # 检查是否被明确授权
            return await self.permission_service.check_permission(
                user_id, f'file.{action}', file_id
            )

        return False

    async def log_file_access(
        self,
        user_id: str,
        file_id: str,
        action: str,
        success: bool,
        ip_address: str = None,
        error_message: str = None
    ):
        """记录文件访问日志"""
        await self.db.execute("""
            INSERT INTO file_access_logs
            (user_id, file_id, action, ip_address, success, error_message)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, user_id, file_id, action, ip_address, success, error_message)
```

### 4. 安全防护措施

```python
# 安全服务
class SecurityService:
    """安全防护服务"""

    async def scan_uploaded_file(self, file_path: str) -> dict:
        """扫描上传的文件"""
        # 计算SHA-256校验和
        checksum = await self.calculate_checksum(file_path)

        # 检查文件类型
        file_type = await self.detect_file_type(file_path)

        # 病毒扫描（集成ClamAV）
        is_clean = await self.clamav_scan(file_path)

        return {
            "checksum": checksum,
            "file_type": file_type,
            "is_clean": is_clean,
            "scan_result": "clean" if is_clean else "infected"
        }

    async def generate_safe_filename(self, original_filename: str) -> str:
        """生成安全的文件名"""
        # 提取文件扩展名
        ext = Path(original_filename).suffix

        # 生成UUID文件名
        safe_name = f"{uuid4()}{ext}"

        # 安全性检查
        if ext.lower() in ['.exe', '.bat', '.sh', '.cmd']:
            raise ValueError(f"不允许的文件类型: {ext}")

        return safe_name

    async def validate_file_size(self, file_size: int, user_id: str) -> bool:
        """验证文件大小"""
        # 单文件限制
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"文件过大: {file_size} > {MAX_FILE_SIZE}")

        # 检查用户配额
        return await self.quota_service.check_upload_quota(user_id, file_size)
```

---

## 🗄️ RustFS对象存储集成

### 集成策略

```
┌─────────────────────────────────────────────────────────────────┐
│                   RustFS验证部署方案                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  阶段1: 单机部署验证 (当前)                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Docker Compose 部署                                    │   │
│  │  ├── RustFS 容器 (S3 API: 9000, Admin: 9001)           │   │
│  │  ├── 数据卷挂载 (./rustfs/data)                         │   │
│  │  └── WebChat 直接对接                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                        ↓ 验证成功                                │
│  阶段2: 平台基础设施 (3个月后)                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Kubernetes StatefulSet                                 │   │
│  │  ├── 3副本高可用部署                                    │   │
│  │  ├── 统一S3 API网关                                     │   │
│  │  └── 多服务共享                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Docker Compose部署配置

```yaml
# docker-compose.yml - WebChat开发环境
version: '3.8'

services:
  # RustFS对象存储
  rustfs:
    image: rustfs/rustfs:latest
    container_name: webchat-rustfs
    ports:
      - "9000:9000"  # S3兼容API
      - "9001:9001"  # 管理控制台
    environment:
      # 服务器配置
      - RUSTFS_SERVER_ADDR=:9000
      - RUSTFS_CONSOLE_ADDR=:9001

      # 访问凭据
      - RUSTFS_ROOT_USER=admin
      - RUSTFS_ROOT_PASSWORD=webchat_dev_2024

      # 数据目录
      - RUSTFS_DATA_DIR=/data

      # 存储配额 (开发环境)
      - RUSTFS_QUOTA_ENABLED=true
      - RUSTFS_DEFAULT_QUOTA=5G

      # 日志级别
      - RUSTFS_LOG_LEVEL=info

    volumes:
      - ./rustfs/data:/data
      - ./rustfs/config:/root/.rustfs

    restart: unless-stopped

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

    networks:
      - webchat-network

  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    container_name: webchat-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=webchat
      - POSTGRES_USER=webchat
      - POSTGRES_PASSWORD=webchat_dev_2024
    volumes:
      - ./postgres/data:/var/lib/postgresql/data
    networks:
      - webchat-network

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: webchat-redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - ./redis/data:/data
    networks:
      - webchat-network

  # Qdrant向量数据库
  qdrant:
    image: qdrant/qdrant:latest
    container_name: webchat-qdrant
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant/data:/qdrant/storage
    networks:
      - webchat-network

  # WebChat后端API
  webchat-api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: webchat-api
    ports:
      - "8000:8000"
    environment:
      # 数据库连接
      - DATABASE_URL=postgresql://webchat:webchat_dev_2024@postgres:5432/webchat
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333

      # RustFS配置 (S3兼容)
      - RUSTFS_ENDPOINT=http://rustfs:9000
      - RUSTFS_ACCESS_KEY=minioadmin
      - RUSTFS_SECRET_KEY=minioadmin
      - RUSTFS_BUCKET_NAME=webchat-files
      - RUSTFS_USE_SSL=false

      # JWT密钥
      - JWT_SECRET=webchat_jwt_secret_2024

    depends_on:
      - rustfs
      - postgres
      - redis
      - qdrant

    networks:
      - webchat-network

    restart: unless-stopped

  # WebChat前端
  webchat-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: webchat-frontend
    ports:
      - "3000:80"
    depends_on:
      - webchat-api
    networks:
      - webchat-network

    restart: unless-stopped

networks:
  webchat-network:
    driver: bridge

volumes:
  rustfs-data:
  postgres-data:
  redis-data:
  qdrant-data:
```

### 后端存储服务实现

```python
# backend/services/storage_service.py
"""
RustFS存储服务
Storage service using RustFS S3-compatible API

作者: Athena平台团队
创建时间: 2025-12-31
版本: 1.0.0
"""

import hashlib
import mimetypes
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, BinaryIO, Optional

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from ..config.settings import get_settings

settings = get_settings()


class RustFSService:
    """
    RustFS对象存储服务

    使用S3兼容API与RustFS通信
    """

    def __init__(self):
        """初始化RustFS客户端"""
        # S3客户端配置
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.rustfs_endpoint,
            aws_access_key_id=settings.rustfs_access_key,
            aws_secret_access_key=settings.rustfs_secret_key,
            config=BotoConfig(signature_version='s3v4'),
            region_name='us-east-1'
        )

        self.bucket_name = settings.rustfs_bucket_name

        # 确保Bucket存在
        self._ensure_bucket()

    def _ensure_bucket(self):
        """确保Bucket存在"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                # Bucket不存在，创建它
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                print(f"✅ 创建RustFS Bucket: {self.bucket_name}")
            else:
                raise

    # ========================================================================
    # 文件上传
    # ========================================================================

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        user_id: str,
        session_id: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> dict[str, Any]:
        """
        上传文件到RustFS

        Args:
            file: 文件对象
            filename: 原始文件名
            user_id: 用户ID
            session_id: 会话ID (可选)
            content_type: MIME类型 (可选)

        Returns:
            文件元数据
        """
        # 生成唯一文件名
        file_ext = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"

        # 生成存储Key (按用户和会话组织)
        now = datetime.now()
        if session_id:
            storage_key = (
                f"user_{user_id}/sessions/{session_id}/"
                f"{now.year}/{now.month:02d}/{now.day:02d}/"
                f"{unique_filename}"
            )
        else:
            storage_key = (
                f"user_{user_id}/uploads/"
                f"{now.year}/{now.month:02d}/{now.day:02d}/"
                f"{unique_filename}"
            )

        # 检测MIME类型
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or 'application/octet-stream'

        # 计算文件哈希
        file.seek(0)
        file_content = file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        file_size = len(file_content)
        file.seek(0)

        # 上传到RustFS
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=storage_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'original-filename': filename,
                    'user-id': user_id,
                    'session-id': session_id or '',
                    'upload-time': now.isoformat(),
                    'file-hash': file_hash
                }
            )

            # 生成访问URL (默认1小时有效)
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': storage_key},
                ExpiresIn=3600
            )

            return {
                'file_id': str(uuid.uuid4()),
                'filename': filename,
                'storage_key': storage_key,
                'storage_bucket': self.bucket_name,
                'file_size': file_size,
                'content_type': content_type,
                'file_hash': file_hash,
                'access_url': presigned_url,
                'upload_time': now.isoformat()
            }

        except ClientError as e:
            raise RuntimeError(f"文件上传失败: {e}")

    async def upload_bytes(
        self,
        data: bytes,
        filename: str,
        user_id: str,
        session_id: Optional[str] = None,
        content_type: str = 'application/octet-stream'
    ) -> dict[str, Any]:
        """
        上传字节数据

        用于导出功能等场景
        """
        from io import BytesIO

        file_obj = BytesIO(data)
        return await self.upload_file(
            file=file_obj,
            filename=filename,
            user_id=user_id,
            session_id=session_id,
            content_type=content_type
        )

    # ========================================================================
    # 文件下载
    # ========================================================================

    async def download_file(self, storage_key: str) -> tuple[bytes, str]:
        """
        下载文件

        Returns:
            (文件内容, MIME类型)
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )

            file_content = response['Body'].read()
            content_type = response.get('ContentType', 'application/octet-stream')

            return file_content, content_type

        except ClientError as e:
            raise RuntimeError(f"文件下载失败: {e}")

    async def get_presigned_url(
        self,
        storage_key: str,
        expires_in: int = 3600
    ) -> str:
        """
        生成预签名访问URL

        Args:
            storage_key: 文件存储Key
            expires_in: 有效期(秒)，默认1小时

        Returns:
            预签名URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': storage_key
                },
                ExpiresIn=expires_in
            )
            return url

        except ClientError as e:
            raise RuntimeError(f"生成预签名URL失败: {e}")

    # ========================================================================
    # 文件管理
    # ========================================================================

    async def delete_file(self, storage_key: str) -> bool:
        """删除文件"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            return True

        except ClientError:
            return False

    async def move_to_trash(
        self,
        storage_key: str,
        user_id: str
    ) -> bool:
        """
        移动到回收站

        RustFS支持通过重命名实现软删除
        """
        try:
            # 构建回收站路径
            trash_key = f"user_{user_id}/.trash/{storage_key}"

            # 复制到回收站
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': storage_key},
                Key=trash_key
            )

            # 删除原文件
            await self.delete_file(storage_key)

            return True

        except ClientError:
            return False

    async def list_user_files(
        self,
        user_id: str,
        prefix: str = "",
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        列出用户文件

        Args:
            user_id: 用户ID
            prefix: 前缀过滤 (如 "sessions/", "uploads/")
            limit: 返回数量限制

        Returns:
            文件列表
        """
        try:
            list_prefix = f"user_{user_id}/{prefix}"

            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=list_prefix,
                MaxKeys=limit
            )

            files = []
            for obj in response.get('Contents', []):
                # 跳过回收站文件
                if '.trash/' in obj['Key']:
                    continue

                files.append({
                    'storage_key': obj['Key'],
                    'file_size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'].strip('"')
                })

            return files

        except ClientError:
            return []

    async def get_file_info(self, storage_key: str) -> Optional[dict[str, Any]]:
        """获取文件信息"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )

            return {
                'storage_key': storage_key,
                'file_size': response['ContentLength'],
                'content_type': response.get('ContentType'),
                'last_modified': response['LastModified'],
                'metadata': response.get('Metadata', {}),
                'etag': response['ETag'].strip('"')
            }

        except ClientError:
            return None

    # ========================================================================
    # 存储统计
    # ========================================================================

    async def get_user_storage_usage(self, user_id: str) -> dict[str, Any]:
        """
        获取用户存储使用量

        Returns:
            存储统计信息
        """
        try:
            prefix = f"user_{user_id}/"

            # 分页获取所有对象
            all_objects = []
            continuation_token = None

            while True:
                kwargs = {
                    'Bucket': self.bucket_name,
                    'Prefix': prefix
                }
                if continuation_token:
                    kwargs['ContinuationToken'] = continuation_token

                response = self.s3_client.list_objects_v2(**kwargs)

                if 'Contents' in response:
                    # 排除回收站
                    objects = [
                        obj for obj in response['Contents']
                        if '.trash/' not in obj['Key']
                    ]
                    all_objects.extend(objects)

                if response.get('IsTruncated'):
                    continuation_token = response.get('NextContinuationToken')
                else:
                    break

            # 计算统计信息
            total_files = len(all_objects)
            total_size = sum(obj['Size'] for obj in all_objects)

            # 按类型分类
            by_category = {
                'documents': 0,
                'images': 0,
                'audio': 0,
                'other': 0
            }

            for obj in all_objects:
                key = obj['Key'].lower()
                if any(ext in key for ext in ['.pdf', '.doc', '.docx', '.txt', '.md']):
                    by_category['documents'] += obj['Size']
                elif any(ext in key for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    by_category['images'] += obj['Size']
                elif any(ext in key for ext in ['.mp3', '.wav', '.m4a', '.aac']):
                    by_category['audio'] += obj['Size']
                else:
                    by_category['other'] += obj['Size']

            return {
                'user_id': user_id,
                'total_files': total_files,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'by_category': by_category,
                'quota_percent': round((total_size / 536870912) * 100, 2)  # 默认512MB配额
            }

        except ClientError as e:
            raise RuntimeError(f"获取存储统计失败: {e}")


# ========================================================================
# 全局实例
# ========================================================================

_rustfs_instance: Optional[RustFSService] = None


def get_rustfs_service() -> RustFSService:
    """获取RustFS服务单例"""
    global _rustfs_instance
    if _rustfs_instance is None:
        _rustfs_instance = RustFSService()
    return _rustfs_instance
```

### 配置文件

```python
# backend/config/settings.py
"""
配置管理
Configuration management with environment variables
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    app_name: str = "WebChat"
    app_version: str = "1.0.0"
    debug: bool = False

    # JWT配置
    jwt_secret: str = "webchat_jwt_secret_2024"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 86400  # 24小时

    # 数据库配置
    database_url: str = "postgresql://webchat:webchat_dev_2024@localhost:5432/webchat"

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant配置
    qdrant_url: str = "http://localhost:6333"

    # RustFS配置 (S3兼容)
    rustfs_endpoint: str = "http://localhost:9000"
    rustfs_access_key: str = "minioadmin"
    rustfs_secret_key: str = "minioadmin"
    rustfs_bucket_name: str = "webchat-files"
    rustfs_use_ssl: bool = False

    # 文件上传限制
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list[str] = [
        # 文档
        '.pdf', '.doc', '.docx', '.txt', '.md', '.rtf',
        # 图片
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp',
        # 音频
        '.mp3', '.wav', '.m4a', '.aac', '.ogg',
        # 视频 (可选)
        '.mp4', '.avi', '.mov'
    ]

    # 存储配额
    default_storage_quota: int = 536870912  # 512MB
    vip_storage_quota: int = 1073741824 * 5  # 5GB

    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
_settings: Settings | None = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

### 上传API实现

```python
# backend/api/routes/files.py
"""
文件上传API路由
File upload API routes
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ..auth import get_current_user
from ...services.storage_service import get_rustfs_service

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str | None = Form(None),
    current_user = Depends(get_current_user)
):
    """
    上传文件

    - **file**: 上传的文件
    - **session_id**: 关联的会话ID (可选)
    """
    # 验证文件大小
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(status_code=400, detail="文件大小超过限制(50MB)")

    # 验证文件类型
    import os
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".pdf", ".doc", ".docx", ".txt", ".md",
                        ".png", ".jpg", ".jpeg", ".gif",
                        ".mp3", ".wav", ".m4a"]:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    # 重置文件指针
    from io import BytesIO
    file_obj = BytesIO(content)
    file_obj.filename = file.filename

    # 上传到RustFS
    storage_service = get_rustfs_service()
    result = await storage_service.upload_file(
        file=file_obj,
        filename=file.filename,
        user_id=str(current_user.id),
        session_id=session_id
    )

    # 保存文件记录到数据库
    # ... 数据库操作 ...

    return {
        "success": True,
        "file": result
    }


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    current_user = Depends(get_current_user)
):
    """下载文件"""
    # 从数据库获取文件信息
    # ...

    # 从RustFS下载
    storage_service = get_rustfs_service()
    content, content_type = await storage_service.download_file(storage_key)

    return StreamingResponse(
        BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/list")
async def list_user_files(
    current_user = Depends(get_current_user),
    prefix: str = ""
):
    """列出用户文件"""
    storage_service = get_rustfs_service()
    files = await storage_service.list_user_files(
        user_id=str(current_user.id),
        prefix=prefix
    )

    return {
        "success": True,
        "files": files
    }


@router.get("/stats")
async def get_storage_stats(
    current_user = Depends(get_current_user)
):
    """获取存储统计"""
    storage_service = get_rustfs_service()
    stats = await storage_service.get_user_storage_usage(str(current_user.id))

    return {
        "success": True,
        "stats": stats
    }


@router.delete("/delete/{file_id}")
async def delete_file(
    file_id: str,
    current_user = Depends(get_current_user)
):
    """删除文件 (移动到回收站)"""
    # 从数据库获取文件信息
    # ...

    storage_service = get_rustfs_service()
    result = await storage_service.move_to_trash(
        storage_key=storage_key,
        user_id=str(current_user.id)
    )

    if not result:
        raise HTTPException(status_code=500, detail="删除失败")

    return {
        "success": True,
        "message": "文件已移至回收站"
    }
```

---

## 🚀 实施计划

### 第一阶段：基础功能（2周）

- [ ] 搭建项目脚手架
- [ ] 实现基础UI框架
- [ ] 会话管理功能
- [ ] 基础对话功能

### 第二阶段：核心功能（3周）

- [ ] 多媒体上传功能
- [ ] 人机协作编辑
- [ ] 导出功能
- [ ] 历史缓存

### 第三阶段：高级功能（2周）

- [ ] 工作轨迹记录
- [ ] 语义搜索
- [ ] 实时协作
- [ ] 性能优化

### 第四阶段：测试部署（1周）

- [ ] 集成测试
- [ ] 性能测试
- [ ] 部署上线
- [ ] 监控告警

---

## 🧪 RustFS验证测试方案

### 测试目标

```
┌─────────────────────────────────────────────────────────────────┐
│                    RustFS验证测试金字塔                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🔍 功能测试 (Functional)                                       │
│     ├── 文件上传/下载                                           │
│     ├── 用户隔离                                                │
│     ├── 权限控制                                                │
│     └── 配额管理                                                │
│                                                                  │
│  ⚡ 性能测试 (Performance)                                       │
│     ├── 并发上传 (100+ 并发)                                     │
│     ├── 大文件传输 (50MB)                                        │
│     ├── 响应时间 (<200ms)                                        │
│     └── 吞吐量测试                                              │
│                                                                  │
│  🔒 安全测试 (Security)                                          │
│     ├── 访问控制验证                                            │
│     ├── 文件哈希校验                                            │
│     ├── 恶意文件检测                                            │
│     └── 注入攻击防护                                            │
│                                                                  │
│  🛡️ 稳定性测试 (Reliability)                                    │
│     ├── 长时间运行 (24h+)                                        │
│     ├── 故障恢复                                                │
│     ├── 数据一致性                                              │
│     └── 边界条件测试                                            │
└─────────────────────────────────────────────────────────────────┘
```

### 测试脚本

```python
# tests/test_rustfs_integration.py
"""
RustFS集成测试
Integration tests for RustFS object storage
"""

import asyncio
import pytest
from io import BytesIO
from datetime import datetime

from backend.services.storage_service import RustFSService, get_rustfs_service


class TestRustFSBasicOperations:
    """基础操作测试"""

    @pytest.fixture
    async def storage_service(self):
        """创建存储服务实例"""
        service = RustFSService()
        yield service
        # 测试后清理
        # ...

    async def test_upload_and_download(self, storage_service):
        """测试文件上传和下载"""
        # 准备测试数据
        test_data = b"Hello, RustFS!" * 1000
        test_file = BytesIO(test_data)

        # 上传文件
        result = await storage_service.upload_file(
            file=test_file,
            filename="test.txt",
            user_id="test_user_001"
        )

        assert result['filename'] == "test.txt"
        assert result['file_size'] == len(test_data)
        assert 'storage_key' in result
        assert 'access_url' in result

        # 下载文件
        content, content_type = await storage_service.download_file(
            result['storage_key']
        )

        assert content == test_data
        assert 'text/plain' in content_type

    async def test_presigned_url_generation(self, storage_service):
        """测试预签名URL生成"""
        # 上传测试文件
        test_file = BytesIO(b"Test content")
        upload_result = await storage_service.upload_file(
            file=test_file,
            filename="presigned_test.txt",
            user_id="test_user_001"
        )

        # 生成预签名URL
        url = await storage_service.get_presigned_url(
            upload_result['storage_key'],
            expires_in=3600
        )

        assert url is not None
        assert 'http' in url
        assert 'X-Amz-Expires=3600' in url or 'expires=' in url

    async def test_file_list(self, storage_service):
        """测试文件列表"""
        user_id = "test_user_list"

        # 上传多个文件
        for i in range(3):
            test_file = BytesIO(f"File {i} content".encode())
            await storage_service.upload_file(
                file=test_file,
                filename=f"file_{i}.txt",
                user_id=user_id
            )

        # 列出文件
        files = await storage_service.list_user_files(user_id)

        assert len(files) >= 3

    async def test_delete_file(self, storage_service):
        """测试文件删除"""
        # 上传文件
        test_file = BytesIO(b"Delete me")
        upload_result = await storage_service.upload_file(
            file=test_file,
            filename="delete_test.txt",
            user_id="test_user_001"
        )

        storage_key = upload_result['storage_key']

        # 移到回收站
        result = await storage_service.move_to_trash(
            storage_key=storage_key,
            user_id="test_user_001"
        )

        assert result is True

        # 验证文件不在列表中
        files = await storage_service.list_user_files("test_user_001")
        assert storage_key not in [f['storage_key'] for f in files]


class TestRustFSUserIsolation:
    """用户隔离测试"""

    async def test_user_file_separation(self):
        """测试用户文件隔离"""
        service = get_rustfs_service()

        # 用户1上传文件
        file1 = BytesIO(b"User 1 file")
        result1 = await service.upload_file(
            file=file1,
            filename="user1_file.txt",
            user_id="user_001"
        )

        # 用户2上传文件
        file2 = BytesIO(b"User 2 file")
        result2 = await service.upload_file(
            file=file2,
            filename="user2_file.txt",
            user_id="user_002"
        )

        # 验证存储Key分离
        assert result1['storage_key'].startswith('user_user_001/')
        assert result2['storage_key'].startswith('user_user_002/')

        # 验证用户只能看到自己的文件
        user1_files = await service.list_user_files("user_001")
        user2_files = await service.list_user_files("user_002")

        user1_keys = [f['storage_key'] for f in user1_files]
        user2_keys = [f['storage_key'] for f in user2_files]

        assert result1['storage_key'] in user1_keys
        assert result1['storage_key'] not in user2_keys
        assert result2['storage_key'] in user2_keys
        assert result2['storage_key'] not in user1_keys

    async def test_session_file_grouping(self):
        """测试会话文件分组"""
        service = get_rustfs_service()
        user_id = "test_user_session"
        session_id = "session_123"

        # 在同一会话上传多个文件
        for i in range(3):
            file = BytesIO(f"Session file {i}".encode())
            await service.upload_file(
                file=file,
                filename=f"session_file_{i}.txt",
                user_id=user_id,
                session_id=session_id
            )

        # 列出会话文件
        session_files = await service.list_user_files(
            user_id=user_id,
            prefix=f"sessions/{session_id}/"
        )

        assert len(session_files) == 3

        # 验证所有文件都在正确的会话路径下
        for file_info in session_files:
            assert f'sessions/{session_id}/' in file_info['storage_key']


class TestRustFSPerformance:
    """性能测试"""

    async def test_concurrent_uploads(self):
        """测试并发上传"""
        service = get_rustfs_service()
        user_id = "perf_test_user"

        # 并发上传100个文件
        tasks = []
        for i in range(100):
            file = BytesIO(f"Performance test file {i}".encode() * 100)
            task = service.upload_file(
                file=file,
                filename=f"perf_test_{i}.txt",
                user_id=user_id
            )
            tasks.append(task)

        start_time = datetime.now()
        results = await asyncio.gather(*tasks)
        end_time = datetime.now()

        # 验证所有上传成功
        assert len(results) == 100

        # 计算性能指标
        duration = (end_time - start_time).total_seconds()
        throughput = len(results) / duration

        print(f"并发上传 {len(results)} 个文件")
        print(f"总耗时: {duration:.2f}秒")
        print(f"吞吐量: {throughput:.2f} 文件/秒")

        # 断言性能要求
        assert throughput > 10  # 至少10文件/秒

    async def test_large_file_upload(self):
        """测试大文件上传"""
        service = get_rustfs_service()

        # 创建50MB文件
        large_data = b"x" * (50 * 1024 * 1024)
        large_file = BytesIO(large_data)

        start_time = datetime.now()
        result = await service.upload_file(
            file=large_file,
            filename="large_file.bin",
            user_id="test_large_file"
        )
        end_time = datetime.now()

        duration = (end_time - start_time).total_seconds()

        assert result['file_size'] == len(large_data)
        print(f"50MB文件上传耗时: {duration:.2f}秒")

        # 验证上传成功
        content, _ = await service.download_file(result['storage_key'])
        assert len(content) == len(large_data)


class TestRustFSSecurity:
    """安全测试"""

    async def test_file_hash_verification(self):
        """测试文件哈希校验"""
        service = get_rustfs_service()

        test_data = b"Test data for hash verification"
        test_file = BytesIO(test_data)

        result = await service.upload_file(
            file=test_file,
            filename="hash_test.txt",
            user_id="test_hash_user"
        )

        # 验证返回的哈希值
        assert 'file_hash' in result
        assert len(result['file_hash']) == 64  # SHA-256

        # 计算预期哈希
        import hashlib
        expected_hash = hashlib.sha256(test_data).hexdigest()

        assert result['file_hash'] == expected_hash

    async def test_file_type_detection(self):
        """测试文件类型检测"""
        service = get_rustfs_service()

        # 测试各种文件类型
        test_cases = [
            ("test.pdf", b"%PDF-1.4", "application/pdf"),
            ("test.txt", b"Plain text", "text/plain"),
            ("test.png", b"\x89PNG\r\n\x1a\n", "image/png"),
        ]

        for filename, content, expected_type in test_cases:
            file = BytesIO(content)
            result = await service.upload_file(
                file=file,
                filename=filename,
                user_id="test_file_type"
            )

            # 验证content_type正确检测
            if expected_type:
                assert expected_type in result['content_type']


class TestRustFSStorageQuota:
    """存储配额测试"""

    async def test_storage_usage_calculation(self):
        """测试存储使用量计算"""
        service = get_rustfs_service()
        user_id = "quota_test_user"

        # 上传不同类型的文件
        files = [
            ("doc1.pdf", b"PDF content" * 1000, "document"),
            ("image1.png", b"PNG data" * 5000, "image"),
            ("audio1.mp3", b"MP3 data" * 10000, "audio"),
        ]

        for filename, content, _ in files:
            file = BytesIO(content)
            await service.upload_file(
                file=file,
                filename=filename,
                user_id=user_id
            )

        # 获取存储统计
        stats = await service.get_user_storage_usage(user_id)

        assert stats['total_files'] >= 3
        assert stats['total_size'] > 0
        assert 'by_category' in stats
        assert stats['by_category']['documents'] > 0
        assert stats['by_category']['images'] > 0
        assert stats['by_category']['audio'] > 0

        print(f"用户 {user_id} 存储统计:")
        print(f"  总文件数: {stats['total_files']}")
        print(f"  总大小: {stats['total_size_mb']} MB")
        print(f"  配额使用: {stats['quota_percent']}%")


# 运行测试的命令
# pytest tests/test_rustfs_integration.py -v
# pytest tests/test_rustfs_integration.py::TestRustFSPerformance -v  # 只运行性能测试
# pytest tests/test_rustfs_integration.py -k "concurrent" -v  # 只运行并发相关测试
```

### 验收标准

| 测试类别 | 验收标准 | 优先级 |
|---------|---------|--------|
| 基础功能 | 所有CRUD操作正常，错误处理完善 | P0 |
| 用户隔离 | 跨用户访问被正确拒绝，数据完全隔离 | P0 |
| 并发性能 | 支持100并发上传，吞吐量>10文件/秒 | P1 |
| 大文件 | 50MB文件上传时间<30秒 | P1 |
| 安全性 | 文件哈希验证正确，类型检测准确 | P0 |
| 稳定性 | 24小时持续运行无崩溃，内存稳定 | P1 |

---

## 🎨 前端组件实现

### 文件上传组件

```typescript
// frontend/src/components/FileUploadZone.tsx
/**
 * 文件上传区域组件
 * File upload zone component with drag-and-drop support
 */

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Image, Music, X, Check } from 'lucide-react';

interface FileUploadZoneProps {
  sessionId?: string;
  onUploadComplete?: (files: UploadedFile[]) => void;
  maxSize?: number; // bytes
  allowedTypes?: string[];
}

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'uploading' | 'success' | 'error';
  progress: number;
  url?: string;
  error?: string;
}

const FILE_ICONS = {
  'application/pdf': FileText,
  'application/msword': FileText,
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileText,
  'image/png': Image,
  'image/jpeg': Image,
  'image/gif': Image,
  'audio/mpeg': Music,
  'audio/wav': Music,
};

export const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  sessionId,
  onUploadComplete,
  maxSize = 50 * 1024 * 1024, // 50MB
  allowedTypes = ['.pdf', '.doc', '.docx', '.txt', '.md', '.png', '.jpg', '.jpeg', '.gif', '.mp3', '.wav']
}) => {
  const [uploadingFiles, setUploadingFiles] = useState<UploadedFile[]>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    // 验证文件
    const validFiles = acceptedFiles.filter(file => {
      // 检查大小
      if (file.size > maxSize) {
        alert(`文件 "${file.name}" 超过大小限制 (${maxSize / 1024 / 1024}MB)`);
        return false;
      }

      // 检查类型
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!allowedTypes.includes(ext)) {
        alert(`不支持的文件类型: ${ext}`);
        return false;
      }

      return true;
    });

    if (validFiles.length === 0) return;

    // 创建上传任务
    const uploadTasks: UploadedFile[] = validFiles.map(file => ({
      id: Math.random().toString(36),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading',
      progress: 0,
    }));

    setUploadingFiles(prev => [...prev, ...uploadTasks]);

    // 逐个上传
    for (let i = 0; i < uploadTasks.length; i++) {
      const task = uploadTasks[i];
      const file = validFiles[i];

      try {
        // 使用FormData上传
        const formData = new FormData();
        formData.append('file', file);
        if (sessionId) {
          formData.append('session_id', sessionId);
        }

        const xhr = new XMLHttpRequest();

        // 监听上传进度
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const progress = Math.round((e.loaded / e.total) * 100);
            setUploadingFiles(prev =>
              prev.map(f =>
                f.id === task.id ? { ...f, progress } : f
              )
            );
          }
        });

        // 监听完成
        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            setUploadingFiles(prev =>
              prev.map(f =>
                f.id === task.id
                  ? { ...f, status: 'success', progress: 100, url: response.file.access_url }
                  : f
              )
            );
          } else {
            setUploadingFiles(prev =>
              prev.map(f =>
                f.id === task.id
                  ? { ...f, status: 'error', error: '上传失败' }
                  : f
              )
            );
          }
        });

        // 监听错误
        xhr.addEventListener('error', () => {
          setUploadingFiles(prev =>
            prev.map(f =>
              f.id === task.id
                ? { ...f, status: 'error', error: '网络错误' }
                : f
            )
          );
        });

        xhr.open('POST', '/api/files/upload');
        xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('token')}`);
        xhr.send(formData);

      } catch (error) {
        setUploadingFiles(prev =>
          prev.map(f =>
            f.id === task.id
              ? { ...f, status: 'error', error: '上传异常' }
              : f
          )
        );
      }
    }

    // 通知父组件
    const completed = uploadingFiles.filter(f => f.status === 'success');
    if (completed.length > 0 && onUploadComplete) {
      onUploadComplete(completed);
    }
  }, [sessionId, maxSize, allowedTypes, uploadingFiles, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt', '.md'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/gif': ['.gif'],
      'audio/mpeg': ['.mp3'],
      'audio/wav': ['.wav'],
    }
  });

  const removeFile = (id: string) => {
    setUploadingFiles(prev => prev.filter(f => f.id !== id));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileIcon = (type: string) => {
    const Icon = FILE_ICONS[type as keyof typeof FILE_ICONS] || FileText;
    return <Icon className="w-5 h-5" />;
  };

  return (
    <div className="space-y-4">
      {/* 上传区域 */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
        `}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        {isDragActive ? (
          <p className="text-blue-600">释放文件开始上传...</p>
        ) : (
          <div>
            <p className="text-gray-700 font-medium">拖拽文件到此处，或点击选择</p>
            <p className="text-sm text-gray-500 mt-2">
              支持文档、图片、音频（最大 {maxSize / 1024 / 1024}MB）
            </p>
          </div>
        )}
      </div>

      {/* 上传列表 */}
      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-700">上传队列</h4>
          {uploadingFiles.map(file => (
            <div
              key={file.id}
              className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200"
            >
              {getFileIcon(file.type)}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                {/* 进度条 */}
                {file.status === 'uploading' && (
                  <div className="mt-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all duration-300"
                      style={{ width: `${file.progress}%` }}
                    />
                  </div>
                )}
              </div>
              {/* 状态图标 */}
              <div className="flex items-center gap-2">
                {file.status === 'uploading' && (
                  <span className="text-xs text-blue-600">{file.progress}%</span>
                )}
                {file.status === 'success' && (
                  <Check className="w-5 h-5 text-green-500" />
                )}
                {file.status === 'error' && (
                  <span className="text-xs text-red-600">{file.error}</span>
                )}
                <button
                  onClick={() => removeFile(file.id)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUploadZone;
```

### 导出功能组件

```typescript
// frontend/src/components/ExportMenu.tsx
/**
 * 导出功能组件
 * Export functionality component
 *
 * 设计原则：根据用户明确指令执行导出，不默认显示多种格式选项
 * Design: Export based on explicit user instruction, no default format options
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Download, Loader2 } from 'lucide-react';

interface ExportMenuProps {
  sessionId: string;
  sessionTitle: string;
  /** 支持的导出格式，由用户或场景指定，而非默认提供 */
  supportedFormats?: string[];
}

export const ExportMenu: React.FC<ExportMenuProps> = ({
  sessionId,
  sessionTitle,
  supportedFormats = ['markdown'] // 默认仅支持Markdown，保持简洁
}) => {
  const [exporting, setExporting] = useState(false);

  /**
   * 执行导出 - 使用预先确定的格式
   * @param formatId 用户明确指定的格式（通过上下文、命令或配置确定）
   */
  const handleExport = async (formatId?: string) => {
    // 如果未指定格式，使用默认格式
    const targetFormat = formatId || supportedFormats[0];

    setExporting(true);
    try {
      const response = await fetch(`/api/export/${sessionId}/${targetFormat}`);
      if (!response.ok) throw new Error('导出失败');

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.href = url;
      a.download = `${sessionTitle}.${targetFormat}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

    } catch (error) {
      console.error('导出错误:', error);
      alert('导出失败，请稍后重试');
    } finally {
      setExporting(false);
    }
  };

  // 简洁的导出按钮 - 直接执行，无格式选择菜单
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={() => handleExport()}
      disabled={exporting}
      title={`导出为 ${supportedFormats[0]} 格式`}
    >
      {exporting ? (
        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
      ) : (
        <Download className="w-4 h-4 mr-2" />
      )}
      导出
    </Button>
  );
};

/**
 * 高级导出组件 - 仅在用户明确需要多种格式时使用
 * Advanced export component - Only when user explicitly requests multiple formats
 */
export const AdvancedExportMenu: React.FC<ExportMenuProps> = ({
  sessionId,
  sessionTitle,
  supportedFormats = ['markdown', 'docx', 'excel', 'json']
}) => {
  const [exporting, setExporting] = useState<string | null>(null);

  const handleExport = async (formatId: string) => {
    setExporting(formatId);
    try {
      const response = await fetch(`/api/export/${sessionId}/${formatId}`);
      if (!response.ok) throw new Error('导出失败');

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.href = url;
      a.download = `${sessionTitle}.${formatId}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

    } catch (error) {
      console.error('导出错误:', error);
      alert('导出失败，请稍后重试');
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="flex gap-2">
      {supportedFormats.map(format => (
        <Button
          key={format}
          variant="outline"
          size="sm"
          onClick={() => handleExport(format)}
          disabled={exporting === format}
        >
          {exporting === format ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Download className="w-4 h-4 mr-2" />
          )}
          {format}
        </Button>
      ))}
    </div>
  );
};

export default ExportMenu;
```

### 导出格式指定方式

```typescript
// frontend/src/services/exportService.ts
/**
 * 导出服务 - 支持多种格式指定方式
 */

export type ExportFormat = 'markdown' | 'docx' | 'excel' | 'json';

export class ExportService {
  /**
   * 方式1: 通过用户聊天指令确定格式
   * 示例: "把这份对话导出为Word文档"
   */
  static detectFormatFromCommand(userMessage: string): ExportFormat | null {
    const formatKeywords = {
      markdown: ['markdown', 'md', '马克当'],
      docx: ['word', 'docx', '文档', 'doc'],
      excel: ['excel', 'xlsx', '表格', 'xls'],
      json: ['json', '数据', 'api']
    };

    const message = userMessage.toLowerCase();
    for (const [format, keywords] of Object.entries(formatKeywords)) {
      if (keywords.some(kw => message.includes(kw))) {
        return format as ExportFormat;
      }
    }
    return null;
  }

  /**
   * 方式2: 通过用户偏好设置确定格式
   */
  static async getUserPreferredFormat(userId: string): Promise<ExportFormat> {
    // 从用户设置中读取
    const settings = await fetch(`/api/user/${userId}/settings`).then(r => r.json());
    return settings.preferredExportFormat || 'markdown';
  }

  /**
   * 方式3: 通过上下文场景确定格式
   * 示例: 企业用户默认使用docx，开发者默认使用markdown
   */
  static getFormatByContext(userType: string): ExportFormat {
    const contextMap: Record<string, ExportFormat> = {
      'enterprise': 'docx',
      'developer': 'markdown',
      'analyst': 'excel',
      'api_user': 'json'
    };
    return contextMap[userType] || 'markdown';
  }
}
```

### 可编辑计划组件

```typescript
// frontend/src/components/EditablePlan.tsx
/**
 * 可编辑计划组件
 * Editable plan component for human-AI collaboration
 */

import React, { useState } from 'react';
import { Plus, Edit, Check, X, Trash2 } from 'lucide-react';

interface PlanItem {
  id: string;
  title: string;
  status: 'pending' | 'in_progress' | 'completed';
  assignee: string;
  dueDate?: string;
  subtasks?: PlanItem[];
}

interface EditablePlanProps {
  sessionId: string;
  initialPlan?: PlanItem[];
  onPlanChange?: (plan: PlanItem[]) => void;
}

export const EditablePlan: React.FC<EditablePlanProps> = ({
  sessionId,
  initialPlan = [],
  onPlanChange
}) => {
  const [plan, setPlan] = useState<PlanItem[]>(initialPlan);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<PlanItem>>({});

  const statusIcons = {
    pending: '○',
    in_progress: '→',
    completed: '✓'
  };

  const statusLabels = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成'
  };

  const handleAddItem = () => {
    const newItem: PlanItem = {
      id: Date.now().toString(),
      title: '新任务',
      status: 'pending',
      assignee: 'currentUser'
    };
    const updatedPlan = [...plan, newItem];
    setPlan(updatedPlan);
    onPlanChange?.(updatedPlan);
  };

  const handleEditStart = (item: PlanItem) => {
    setEditingId(item.id);
    setEditForm(item);
  };

  const handleEditCancel = () => {
    setEditingId(null);
    setEditForm({});
  };

  const handleEditSave = () => {
    if (!editingId || !editForm.title) return;

    const updatedPlan = plan.map(item =>
      item.id === editingId
        ? { ...item, ...editForm } as PlanItem
        : item
    );

    setPlan(updatedPlan);
    setEditingId(null);
    setEditForm({});
    onPlanChange?.(updatedPlan);
  };

  const handleDelete = (id: string) => {
    const updatedPlan = plan.filter(item => item.id !== id);
    setPlan(updatedPlan);
    onPlanChange?.(updatedPlan);
  };

  return (
    <div className="border rounded-lg bg-white">
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="font-semibold text-lg">📋 实施计划</h3>
        <button
          onClick={handleAddItem}
          className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600"
        >
          <Plus className="w-4 h-4" />
          添加任务
        </button>
      </div>

      {/* 计划列表 */}
      <div className="p-4 space-y-2">
        {plan.length === 0 ? (
          <p className="text-center text-gray-500 py-8">
            暂无计划项，点击"添加任务"开始创建
          </p>
        ) : (
          plan.map(item => (
            <div
              key={item.id}
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-md group"
            >
              {/* 编辑模式 */}
              {editingId === item.id ? (
                <>
                  <input
                    type="text"
                    value={editForm.title || ''}
                    onChange={e => setEditForm({ ...editForm, title: e.target.value })}
                    className="flex-1 px-2 py-1 border rounded"
                    autoFocus
                  />
                  <select
                    value={editForm.status || item.status}
                    onChange={e => setEditForm({ ...editForm, status: e.target.value as any })}
                    className="px-2 py-1 border rounded"
                  >
                    <option value="pending">待处理</option>
                    <option value="in_progress">进行中</option>
                    <option value="completed">已完成</option>
                  </select>
                  <button
                    onClick={handleEditSave}
                    className="p-1 text-green-600 hover:bg-green-50 rounded"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                  <button
                    onClick={handleEditCancel}
                    className="p-1 text-gray-600 hover:bg-gray-100 rounded"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </>
              ) : (
                <>
                  {/* 状态图标 */}
                  <span className={`text-lg ${item.status === 'completed' ? 'text-green-600' : ''}`}>
                    {statusIcons[item.status]}
                  </span>

                  {/* 标题 */}
                  <span className={`flex-1 ${item.status === 'completed' ? 'line-through text-gray-400' : ''}`}>
                    {item.title}
                  </span>

                  {/* 状态标签 */}
                  <span className="text-xs px-2 py-1 rounded-full bg-gray-200 text-gray-700">
                    {statusLabels[item.status]}
                  </span>

                  {/* 操作按钮 */}
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleEditStart(item)}
                      className="p-1 text-gray-600 hover:bg-gray-200 rounded"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="p-1 text-red-600 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default EditablePlan;
```

---

## 📖 完整API文档

### 认证API

```
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

### 会话API

```
GET    /api/sessions          # 列出会话
POST   /api/sessions          # 创建会话
GET    /api/sessions/:id      # 获取会话详情
PUT    /api/sessions/:id      # 更新会话
DELETE /api/sessions/:id      # 删除会话
```

### 消息API

```
GET    /api/sessions/:id/messages     # 获取消息列表
POST   /api/sessions/:id/messages     # 发送消息
DELETE /api/messages/:id              # 删除消息
```

### 文件API

```
POST   /api/files/upload              # 上传文件
GET    /api/files/download/:id        # 下载文件
GET    /api/files/list                # 列出用户文件
GET    /api/files/stats               # 存储统计
DELETE /api/files/delete/:id          # 删除文件
```

### 导出API

**设计原则**: 导出格式由用户明确指令指定，而非提供多种选项供选择

```
# 导出会话内容为指定格式
GET    /api/export/:session_id/:format

# 参数说明:
#   session_id: 会话ID
#   format: 导出格式 (markdown | docx | excel | json)
#
# 使用示例:
#   GET /api/export/abc123/markdown  - 导出为Markdown
#   GET /api/export/abc123/docx      - 导出为Word文档
#   GET /api/export/abc123/excel     - 导出为Excel表格
#   GET /api/export/abc123/json      - 导出为JSON数据
#
# 响应: 文件流 (Content-Type取决于format)
```

**格式指定方式**:
1. **用户聊天指令**: AI解析用户指令如"导出为Word"确定格式
2. **用户偏好设置**: 在用户设置中配置默认导出格式
3. **上下文推断**: 根据用户类型(企业/开发者/分析师)使用合适的默认格式
4. **直接指定**: 在组件props中传入`supportedFormats`参数

### 协作API

```
POST   /api/plan/generate                # AI生成计划
PUT    /api/plan/:id                     # 更新计划项
DELETE /api/plan/:id                     # 删除计划项
```

---

## 📈 技术指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 响应时间 | <200ms | 消息发送延迟 |
| 并发用户 | 1000+ | 同时在线用户 |
| 文件大小 | 50MB | 单文件最大限制 |
| 缓存命中率 | >90% | Redis缓存命中率 |
| 系统可用性 | 99.9% | 年度可用性目标 |
| 文件上传 | >10文件/秒 | 并发上传吞吐量 |
| 存储配额 | 512MB-5GB | 按用户等级分配 |

---

## 🚀 快速启动指南

### 开发环境启动

```bash
# 1. 克隆项目
git clone https://github.com/your-org/webchat.git
cd webchat

# 2. 启动所有服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 访问服务
# 前端: http://localhost:3000
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
# RustFS控制台: http://localhost:9001
```

### 后端开发

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
alembic upgrade head

# 运行开发服务器
uvicorn main:app --reload --port 8000
```

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 运行测试

```bash
# 后端测试
cd backend
pytest tests/ -v

# RustFS集成测试
pytest tests/test_rustfs_integration.py -v

# 性能测试
pytest tests/test_rustfs_integration.py::TestRustFSPerformance -v

# 前端测试
cd frontend
npm test
```

---

## 📊 项目结构

```
webchat/
├── backend/                      # 后端服务
│   ├── api/                     # API路由
│   │   ├── routes/              # 路由模块
│   │   │   ├── auth.py         # 认证API
│   │   │   ├── sessions.py     # 会话API
│   │   │   ├── messages.py     # 消息API
│   │   │   ├── files.py        # 文件API
│   │   │   └── export.py       # 导出API
│   │   └── deps.py             # 依赖注入
│   ├── services/                # 业务服务
│   │   ├── storage_service.py   # RustFS存储服务
│   │   ├── session_service.py   # 会话管理服务
│   │   ├── message_service.py   # 消息处理服务
│   │   ├── export_service.py    # 导出服务
│   │   └── auth_service.py      # 认证服务
│   ├── models/                  # 数据模型
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── message.py
│   │   └── file.py
│   ├── config/                  # 配置
│   │   └── settings.py
│   ├── main.py                  # 应用入口
│   └── requirements.txt         # Python依赖
│
├── frontend/                     # 前端应用
│   ├── src/
│   │   ├── components/          # React组件
│   │   │   ├── FileUploadZone.tsx
│   │   │   ├── ExportMenu.tsx
│   │   │   ├── EditablePlan.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   └── SessionList.tsx
│   │   ├── hooks/               # 自定义Hooks
│   │   │   ├── useMessages.ts
│   │   │   ├── useFiles.ts
│   │   │   └── useWebSocket.ts
│   │   ├── services/            # API服务
│   │   │   ├── api.ts
│   │   │   └── storage.ts
│   │   ├── types/               # TypeScript类型
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── tests/                        # 测试
│   ├── test_rustfs_integration.py
│   ├── test_api.py
│   └── test_frontend.spec.ts
│
├── docker-compose.yml           # Docker编排
├── Dockerfile.backend           # 后端Docker镜像
├── Dockerfile.frontend          # 前端Docker镜像
├── .env.example                 # 环境变量模板
└── README.md                    # 项目说明
```

---

## 🎯 设计决策总结

### 技术选型决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 前端框架 | React 18 + TypeScript | 生态成熟，类型安全 |
| UI组件库 | shadcn/ui | 现代设计，高度可定制 |
| 状态管理 | Zustand/Jotai | 轻量级，简单易用 |
| 后端框架 | FastAPI | 高性能，自动文档 |
| 数据库 | PostgreSQL 15 | 成熟稳定，支持JSONB |
| 向量存储 | Qdrant | 高性能，易部署 |
| 缓存 | Redis 7 | 高性能，功能丰富 |
| 对象存储 | RustFS | 国产化，S3兼容，成本低 |
| 实时通信 | WebSocket | 双向通信，低延迟 |
| 构建工具 | Vite | 快速热更新 |

### 架构设计亮点

```
┌─────────────────────────────────────────────────────────────┐
│                    WebChat架构亮点                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ✅ 多租户架构                                              │
│     ├── 三层隔离 (应用层/存储层/缓存层)                      │
│     ├── RBAC权限模型                                       │
│     └── 用户配额管理                                        │
│                                                              │
│  ✅ RustFS对象存储验证                                      │
│     ├── S3兼容API                                          │
│     ├── 用户隔离存储                                        │
│     ├── 预签名URL                                           │
│     └── 软删除回收站                                        │
│                                                              │
│  ✅ 完整的前端组件                                          │
│     ├── 文件上传 (拖拽+进度条)                              │
│     ├── 导出功能 (用户指令驱动，简洁UX)                     │
│     └── 可编辑计划 (人机协作)                                │
│                                                              │
│  ✅ 简洁的交互设计                                          │
│     ├── 导出格式由用户明确指令决定                          │
│     ├── 支持聊天指令解析 ("导出为Word")                     │
│     ├── 支持用户偏好设置                                    │
│     └── 高级组件仅在明确需要时提供                          │
│                                                              │
│  ✅ 完善的测试方案                                          │
│     ├── 功能测试                                            │
│     ├── 性能测试                                            │
│     ├── 安全测试                                            │
│     └── 稳定性测试                                          │
│                                                              │
│  ✅ 渐进式部署策略                                          │
│     ├── 阶段1: RustFS单机验证                               │
│     ├── 阶段2: 平台基础设施                                 │
│     └── 阶段3: 完整高可用部署                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 👥 团队分工

| 成员 | 角色 | 职责 |
|------|------|------|
| 👨 徐健 | 产品负责人 | 需求定义、进度把控、最终决策 |
| 🏛️ Athena | 技术架构师 | 架构设计、技术选型、核心开发 |
| 💝 小诺 | UI/UX设计师 | 界面设计、交互体验、视觉呈现 |

---

## 📝 设计结论

### 核心价值主张

```
┌─────────────────────────────────────────────────────────────────┐
│                   WebChat系统设计总结                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  目标用户: 需要AI辅助协作的团队和个人                               │
│  核心价值: 提升沟通效率，保留工作轨迹，支持人机共创                    │
│                                                                  │
│  六大核心功能:                                                   │
│  ✅ 统一管理 - 集中管理所有对话和文件                              │
│  ✅ 多媒体支持 - 文档、图片、音频无缝上传                          │
│  ✅ 智能导出 - 用户指令驱动，支持多种格式                          │
│  ✅ 人机协作 - AI生成计划，用户可编辑调整                           │
│  ✅ 工作轨迹 - 完整记录所有操作历史                               │
│  ✅ 历史缓存 - 多级缓存保证对话历史可追溯                          │
│                                                                  │
│  交互设计原则:                                                   │
│  🎯 简洁优先 - 默认仅显示必要选项，减少认知负担                     │
│  🎯 指令驱动 - 支持自然语言指令 ("导出为Word")                     │
│  🎯 按需扩展 - 高级功能仅在明确需要时提供                          │
│  🎯 上下文感知 - 根据用户类型自动选择合适格式                      │
│                                                                  │
│  技术创新点:                                                     │
│  🔧 RustFS对象存储 - 验证国产化对象存储在WebChat中的可行性        │
│  🔧 多租户架构 - 完善的用户隔离和权限管理体系                    │
│  🔧 现代化前端 - React 18 + TypeScript + shadcn/ui                │
│  🔧 高性能后端 - FastAPI + WebSocket + 异步处理                   │
│                                                                  │
│  验证策略:                                                       │
│  📊 阶段1: 在WebChat中验证RustFS (单机Docker部署)                 │
│  📊 阶段2: 验证成功后扩展为平台级服务 (Kubernetes)                │
│  📊 阶段3: 全面集成到Athena平台基础设施                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 后续行动项

| 优先级 | 任务 | 负责人 | 时间线 |
|--------|------|--------|--------|
| P0 | 创建Git仓库 | DevOps | 第1周 |
| P0 | 搭建Docker开发环境 | DevOps | 第1周 |
| P0 | 实现RustFS存储服务 | 后端 | 第2周 |
| P0 | 实现基础认证与会话API | 后端 | 第2周 |
| P1 | 实现前端文件上传组件 | 前端 | 第3周 |
| P1 | 实现导出功能 | 后端 | 第3周 |
| P1 | RustFS集成测试 | QA | 第4周 |
| P2 | 实现人机协作编辑 | 全栈 | 第5周 |
| P2 | 性能优化与监控 | DevOps | 第6周 |
| P2 | 文档完善与部署 | 全员 | 第7周 |

### 成功指标

```
验证期成功标准 (3个月):
├── RustFS稳定运行30天无故障
├── 支持100并发用户同时使用
├── 文件上传成功率 > 99.9%
├── 平均响应时间 < 200ms
├── 用户满意度 > 4.5/5.0
└── 存储成本对比云方案节省 > 50%

扩展期目标 (6-12个月):
├── 部署为平台级基础设施服务
├── 支持多服务共享存储
├── 实现高可用集群部署
└── 建立完善的运维监控体系
```

---

## 📚 附录

### A. 环境变量配置

```bash
# .env.example - 环境变量模板

# 应用配置
APP_NAME=WebChat
APP_VERSION=1.0.0
DEBUG=False

# JWT配置
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400

# 数据库配置
DATABASE_URL=postgresql://webchat:password@localhost:5432/webchat
POSTGRES_USER=webchat
POSTGRES_PASSWORD=password
POSTGRES_DB=webchat

# Redis配置
REDIS_URL=redis://localhost:6379/0

# Qdrant配置
QDRANT_URL=http://localhost:6333

# RustFS配置 (S3兼容)
RUSTFS_ENDPOINT=http://localhost:9000
RUSTFS_ACCESS_KEY=minioadmin
RUSTFS_SECRET_KEY=minioadmin
RUSTFS_BUCKET_NAME=webchat-files
RUSTFS_USE_SSL=False

# 文件配置
MAX_FILE_SIZE=52428800  # 50MB
DEFAULT_STORAGE_QUOTA=536870912  # 512MB
VIP_STORAGE_QUOTA=5368709120  # 5GB

# CORS配置
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_ALLOW_CREDENTIALS=True
```

### B. Docker镜像优化

```dockerfile
# Dockerfile.backend - 优化的后端Docker镜像
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN pip install --no-cache-dir poetry

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 安装依赖
RUN poetry install --no-dev --no-root

# 最终镜像
FROM python:3.11-slim

WORKDIR /app

# 复制虚拟环境
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# 复制应用代码
COPY . .

# 非root用户运行
RUN useradd -m -u 1000 webchat
USER webchat

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### C. 生产环境部署建议

```yaml
# k8s/production/deployment.yaml - 生产环境Kubernetes配置
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webchat-api
  namespace: webchat
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webchat-api
  template:
    metadata:
      labels:
        app: webchat-api
    spec:
      containers:
      - name: api
        image: webchat-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: webchat-secrets
              key: database-url
        - name: RUSTFS_ENDPOINT
          value: "http://rustfs.infrastructure.svc.cluster.local:9000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: webchat-api
  namespace: webchat
spec:
  selector:
    app: webchat-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: webchat-api-hpa
  namespace: webchat
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webchat-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### D. 参考资源

| 资源类型 | 链接 |
|---------|------|
| FastAPI官方文档 | https://fastapi.tiangolo.com/ |
| React文档 | https://react.dev/ |
| shadcn/ui组件库 | https://ui.shadcn.com/ |
| RustFS项目 | https://github.com/rustfs/rustfs |
| Qdrant文档 | https://qdrant.tech/documentation/ |
| PostgreSQL文档 | https://www.postgresql.org/docs/ |
| WebSocket协议 | https://websockets.spec.whatwg.org/ |

---

*本方案由父女三人协作完成，质量评分93.14%*

---

**文档版本**: v1.0.0
**创建时间**: 2025-12-31
**最后更新**: 2025-12-31
**文档状态**: ✅ 设计完成，待实施验证
