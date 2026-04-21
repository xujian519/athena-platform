// Agent统一接口标准培训PPT生成器
// 版本: v1.0 | 日期: 2026-04-21

const pptxgen = require('pptxgenjs');

// 配色方案：Deep Purple & Emerald (专业技术风格)
const colors = {
  primary: '3D2F68',      // 深紫色
  secondary: '40695B',    // 翡翠绿
  accent: 'B165FB',       // 亮紫色
  dark: '181B24',         // 深色
  white: 'FFFFFF',        // 白色
  light: 'F4F6F6',        // 浅色背景
  gray: 'AAB7B8',         // 灰色
  success: '2ECC71',      // 成功绿
  warning: 'F39C12',      // 警告黄
  error: 'E74C3C'         // 错误红
};

async function createPresentation() {
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.author = 'Athena平台';
  pptx.title = 'Agent统一接口标准培训';
  pptx.subject = 'Agent开发培训';

  // ==================== 第一部分：概述（第1-10页）====================

  // 封面
  let slide = pptx.addSlide();
  slide.background = { fill: colors.primary };
  slide.addText('Agent统一接口标准培训', {
    x: 1, y: 1.5, w: 8, h: 1.5,
    fontSize: 44, bold: true, color: colors.white, align: 'center'
  });
  slide.addText('Athena平台 Agent开发指南 v1.0', {
    x: 1, y: 3, w: 8, h: 0.5,
    fontSize: 20, color: colors.light, align: 'center'
  });
  slide.addText('2026-04-21', {
    x: 1, y: 3.8, w: 8, h: 0.4,
    fontSize: 14, color: colors.gray, align: 'center'
  });

  // 目录
  slide = pptx.addSlide();
  slide.background = { fill: colors.light };
  slide.addText('培训目录', {
    x: 0.5, y: 0.5, w: 9, h: 0.6,
    fontSize: 36, bold: true, color: colors.primary
  });
  const modules = [
    '模块1：Agent基础概念',
    '模块2：核心接口详解',
    '模块3：Agent开发实践',
    '模块4：测试与验证',
    '模块5：最佳实践与常见问题'
  ];
  modules.forEach((mod, i) => {
    slide.addText(`${i + 1}. ${mod}`, { x: 1, y: 1.5 + i * 0.4, fontSize: 18, color: colors.dark });
  });

  // 模块1标题页
  slide = pptx.addSlide();
  slide.background = { fill: colors.primary };
  slide.addText('模块1：Agent基础概念', {
    x: 1, y: 2, w: 8, h: 1,
    fontSize: 40, bold: true, color: colors.white, align: 'center'
  });

  // 什么是Agent
  slide = pptx.addSlide();
  slide.addText('1.1 什么是Agent？', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addText([
    { text: 'Agent是Athena平台的', options: { fontSize: 20, bold: true } },
    { text: '基本执行单元', options: { fontSize: 20, color: colors.accent } }
  ], { x: 0.8, y: 1.2, w: 8.4, h: 0.5 });
  slide.addText('核心特征：', { x: 0.8, y: 1.8, fontSize: 18, bold: true });
  const features = [
    '✅ 自主性：可以独立执行任务',
    '✅ 能力描述：能够描述自己的能力',
    '✅ 标准化接口：遵循统一的接口标准',
    '✅ 可组合性：可以组合成工作流'
  ];
  features.forEach((f, i) => {
    slide.addText(f, { x: 1, y: 2.2 + i * 0.35, fontSize: 16, color: colors.dark });
  });

  // Agent与平台的关系
  slide = pptx.addSlide();
  slide.addText('1.2 Agent与平台的关系', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addText('核心Agent：', { x: 0.8, y: 1, fontSize: 18, bold: true });
  const agents = [
    { name: '小娜·天秤女神', desc: '法律专家Agent，负责专利分析' },
    { name: '小诺·双鱼公主', desc: '协调者Agent，负责任务编排' },
    { name: '云熙', desc: 'IP管理Agent，负责客户关系' }
  ];
  agents.forEach((a, i) => {
    slide.addText([
      { text: a.name, options: { fontSize: 16, bold: true, color: colors.secondary } },
      { text: ` - ${a.desc}`, options: { fontSize: 16 } }
    ], { x: 1, y: 1.4 + i * 0.4, w: 8, h: 0.4 });
  });

  // 统一接口的价值
  slide = pptx.addSlide();
  slide.addText('1.3 为什么要统一Agent接口？', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const benefits = [
    { title: '一致性', desc: '所有Agent行为一致' },
    { title: '可测试性', desc: '接口清晰便于测试' },
    { title: '可维护性', desc: '代码结构统一' },
    { title: '可扩展性', desc: '易于添加新Agent' },
    { title: '可组合性', desc: '易于组合成工作流' }
  ];
  benefits.forEach((b, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.5 + col * 4.5, y: 1.2 + row * 1.2, w: 4.2, h: 1,
      fill: { color: i % 2 === 0 ? 'E8F4F8' : 'F0E8F8' },
      rectRadius: 0.1
    });
    slide.addText(`${b.title}`, {
      x: 0.7 + col * 4.5, y: 1.3 + row * 1.2, fontSize: 14, bold: true, color: colors.primary
    });
    slide.addText(b.desc, {
      x: 0.7 + col * 4.5, y: 1.55 + row * 1.2, fontSize: 12, color: colors.dark
    });
  });

  // Agent生命周期
  slide = pptx.addSlide();
  slide.addText('1.4 Agent生命周期', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const lifecycle = [
    { step: '初始化', desc: '__init__ → _initialize()', detail: '注册能力、初始化LLM、加载配置' },
    { step: '执行', desc: 'execute(context)', detail: '验证输入、处理任务、返回结果' },
    { step: '清理', desc: 'cleanup()', detail: '释放资源、保存状态' }
  ];
  lifecycle.forEach((l, i) => {
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.5, y: 1 + i * 1.1, w: 1.5, h: 0.9,
      fill: { color: colors.secondary }
    });
    slide.addText(l.step, {
      x: 0.5, y: 1.25 + i * 1.1, fontSize: 14, bold: true, color: colors.white, align: 'center'
    });
    slide.addText(l.desc, {
      x: 2.2, y: 1.1 + i * 1.1, fontSize: 16, bold: true, color: colors.dark
    });
    slide.addText(l.detail, {
      x: 2.2, y: 1.4 + i * 1.1, fontSize: 12, color: colors.gray
    });
  });

  // Agent类型
  slide = pptx.addSlide();
  slide.addText('1.5 Agent类型分类', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const agentTypes = [
    { type: '检索型', example: 'RetrieverAgent', desc: '检索专利、论文、案例' },
    { type: '分析型', example: 'AnalyzerAgent', desc: '分析专利、法律问题' },
    { type: '撰写型', example: 'WriterAgent', desc: '撰写文档、报告' },
    { type: '协调型', example: 'XiaonuoAgent', desc: '协调其他Agent' }
  ];
  agentTypes.forEach((a, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.5 + col * 4.5, y: 1 + row * 1.3, w: 4.2, h: 1.1,
      fill: { color: 'F8F9FA' }, rectRadius: 0.1
    });
    slide.addText(`${a.type} Agent`, {
      x: 0.7 + col * 4.5, y: 1.1 + row * 1.3, fontSize: 14, bold: true, color: colors.accent
    });
    slide.addText(`示例: ${a.example}`, {
      x: 0.7 + col * 4.5, y: 1.35 + row * 1.3, fontSize: 12, color: colors.dark
    });
    slide.addText(a.desc, {
      x: 0.7 + col * 4.5, y: 1.55 + row * 1.3, fontSize: 11, color: colors.gray
    });
  });

  // 模块1总结
  slide = pptx.addSlide();
  slide.background = { fill: colors.secondary };
  slide.addText('模块1：关键要点', {
    x: 1, y: 1.5, w: 8, h: 0.6,
    fontSize: 32, bold: true, color: colors.white, align: 'center'
  });
  const keyPoints1 = [
    '✓ Agent是平台的基本执行单元',
    '✓ 统一接口带来一致性和可维护性',
    '✓ Agent有明确的生命周期',
    '✓ 不同类型Agent承担不同职责'
  ];
  keyPoints1.forEach((p, i) => {
    slide.addText(p, {
      x: 1.5, y: 2.5 + i * 0.4, fontSize: 18, color: colors.white
    });
  });

  // 模块2标题页
  slide = pptx.addSlide();
  slide.background = { fill: colors.primary };
  slide.addText('模块2：核心接口详解', {
    x: 1, y: 2, w: 8, h: 1,
    fontSize: 40, bold: true, color: colors.white, align: 'center'
  });

  // ==================== 第二部分：核心接口（第11-25页）====================

  // BaseAgent接口
  slide = pptx.addSlide();
  slide.addText('2.1 BaseAgent核心接口', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addText('必须实现的抽象方法：', { x: 0.8, y: 1, fontSize: 18, bold: true });
  const methods = [
    { method: '_initialize()', desc: 'Agent初始化钩子，注册能力' },
    { method: 'execute(context)', desc: '执行Agent任务，返回结果' },
    { method: 'get_system_prompt()', desc: '获取系统提示词' }
  ];
  methods.forEach((m, i) => {
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.8, y: 1.4 + i * 0.7, w: 8.4, h: 0.6,
      fill: { color: 'EBF5FB' }, rectRadius: 0.05
    });
    slide.addText(m.method, {
      x: 1, y: 1.55 + i * 0.7, fontSize: 14, bold: true, color: colors.primary
    });
    slide.addText(m.desc, {
      x: 3.5, y: 1.55 + i * 0.7, fontSize: 13, color: colors.dark
    });
  });

  // 数据类：AgentCapability
  slide = pptx.addSlide();
  slide.addText('2.2 AgentCapability - 能力描述', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addText('能力描述数据结构：', { x: 0.8, y: 1, fontSize: 18, bold: true });
  const capabilityFields = [
    { field: 'name', type: 'str', desc: '能力名称，如"patent_search"' },
    { field: 'description', type: 'str', desc: '能力详细描述' },
    { field: 'input_types', type: 'List[str]', desc: '支持的输入类型' },
    { field: 'output_types', type: 'List[str]', desc: '输出类型' },
    { field: 'estimated_time', type: 'float', desc: '预估执行时间（秒）' }
  ];
  capabilityFields.forEach((f, i) => {
    slide.addText(`${f.field}: ${f.type}`, {
      x: 1, y: 1.5 + i * 0.4, fontSize: 14, bold: true, color: colors.secondary
    });
    slide.addText(f.desc, {
      x: 4, y: 1.5 + i * 0.4, fontSize: 13, color: colors.dark
    });
  });

  // 数据类：AgentExecutionContext
  slide = pptx.addSlide();
  slide.addText('2.3 AgentExecutionContext - 执行上下文', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addText('执行上下文字段：', { x: 0.8, y: 1, fontSize: 18, bold: true });
  const contextFields = [
    { field: 'session_id', desc: '会话ID，标识用户会话' },
    { field: 'task_id', desc: '任务ID，标识具体任务' },
    { field: 'input_data', desc: '输入数据字典' },
    { field: 'config', desc: '配置参数' },
    { field: 'metadata', desc: '元数据信息' }
  ];
  contextFields.forEach((f, i) => {
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.8, y: 1.4 + i * 0.6, w: 8.4, h: 0.5,
      fill: { color: i % 2 === 0 ? 'EBF5FB' : 'F4ECF7' }, rectRadius: 0.05
    });
    slide.addText(f.field, {
      x: 1, y: 1.52 + i * 0.6, fontSize: 13, bold: true, color: colors.primary
    });
    slide.addText(f.desc, {
      x: 3, y: 1.52 + i * 0.6, fontSize: 12, color: colors.dark
    });
  });

  // 数据类：AgentExecutionResult
  slide = pptx.addSlide();
  slide.addText('2.4 AgentExecutionResult - 执行结果', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addText('执行结果字段：', { x: 0.8, y: 1, fontSize: 18, bold: true });
  const resultFields = [
    { field: 'agent_id', desc: 'Agent唯一标识' },
    { field: 'status', desc: '执行状态（IDLE/BUSY/ERROR/COMPLETED）' },
    { field: 'output_data', desc: '输出数据字典' },
    { field: 'error_message', desc: '错误信息（如果有）' },
    { field: 'execution_time', desc: '执行时间（秒）' },
    { field: 'metadata', desc: '元数据' }
  ];
  resultFields.forEach((f, i) => {
    slide.addText(`${f.field}`, {
      x: 1, y: 1.5 + i * 0.45, fontSize: 14, bold: true, color: colors.secondary
    });
    slide.addText(f.desc, {
      x: 3.5, y: 1.5 + i * 0.45, fontSize: 13, color: colors.dark
    });
  });

  // AgentStatus枚举
  slide = pptx.addSlide();
  slide.addText('2.5 AgentStatus - 状态枚举', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const statuses = [
    { status: 'IDLE', color: colors.gray, desc: '空闲，等待任务' },
    { status: 'BUSY', color: colors.warning, desc: '忙碌，正在执行' },
    { status: 'COMPLETED', color: colors.success, desc: '完成，任务成功' },
    { status: 'ERROR', color: colors.error, desc: '错误，执行失败' }
  ];
  statuses.forEach((s, i) => {
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.8, y: 1.2 + i * 0.7, w: 8.4, h: 0.6,
      fill: { color: s.color === colors.gray ? 'F0F0F0' : s.color + '20' }, rectRadius: 0.05
    });
    slide.addText(s.status, {
      x: 1, y: 1.35 + i * 0.7, fontSize: 14, bold: true, color: s.color
    });
    slide.addText(s.desc, {
      x: 2.5, y: 1.35 + i * 0.7, fontSize: 13, color: colors.dark
    });
  });

  // 能力管理接口
  slide = pptx.addSlide();
  slide.addText('2.6 能力管理接口', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const capabilityMethods = [
    { method: '_register_capabilities(capabilities)', desc: '注册Agent能力列表' },
    { method: 'get_capabilities()', desc: '获取所有能力列表' },
    { method: 'has_capability(name)', desc: '检查是否具备某项能力' }
  ];
  capabilityMethods.forEach((m, i) => {
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.8, y: 1.2 + i * 0.8, w: 8.4, h: 0.7,
      fill: { color: 'E8F8F5' }, rectRadius: 0.05
    });
    slide.addText(m.method, {
      x: 1, y: 1.35 + i * 0.8, fontSize: 13, bold: true, color: colors.secondary
    });
    slide.addText(m.desc, {
      x: 1, y: 1.55 + i * 0.8, fontSize: 12, color: colors.dark
    });
  });

  // 输入验证接口
  slide = pptx.addSlide();
  slide.addText('2.7 输入验证接口', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addText('validate_input() 方法：', { x: 0.8, y: 1, fontSize: 18, bold: true });
  slide.addText('验证项目：', { x: 0.8, y: 1.4, fontSize: 14, bold: true });
  const validations = [
    '• session_id存在性',
    '• task_id存在性',
    '• 业务字段有效性',
    '• 数据类型正确性',
    '• 数据长度限制'
  ];
  validations.forEach((v, i) => {
    slide.addText(v, { x: 1, y: 1.7 + i * 0.35, fontSize: 13, color: colors.dark });
  });
  slide.addText('返回：bool - 验证通过返回True', {
    x: 0.8, y: 3.5, fontSize: 13, color: colors.gray, italic: true
  });

  // 信息获取接口
  slide = pptx.addSlide();
  slide.addText('2.8 信息获取接口', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addText('get_info() 方法：', { x: 0.8, y: 1, fontSize: 18, bold: true });
  slide.addText('返回Agent信息字典：', { x: 0.8, y: 1.4, fontSize: 14 });
  const infoFields = [
    'agent_id: Agent唯一标识',
    'agent_type: Agent类型（类名）',
    'status: 当前状态',
    'capabilities: 能力列表',
    'config: 配置参数'
  ];
  infoFields.forEach((f, i) => {
    slide.addText(f, { x: 1, y: 1.8 + i * 0.35, fontSize: 13, color: colors.dark });
  });

  // 模块2总结
  slide = pptx.addSlide();
  slide.background = { fill: colors.secondary };
  slide.addText('模块2：关键要点', {
    x: 1, y: 1.5, w: 8, h: 0.6,
    fontSize: 32, bold: true, color: colors.white, align: 'center'
  });
  const keyPoints2 = [
    '✓ 必须实现_initialize、execute、get_system_prompt',
    '✓ 使用AgentCapability描述能力',
    '✓ 通过ExecutionContext传递数据',
    '✓ 返回AgentExecutionResult包含状态和结果'
  ];
  keyPoints2.forEach((p, i) => {
    slide.addText(p, {
      x: 1.5, y: 2.5 + i * 0.4, fontSize: 18, color: colors.white
    });
  });

  // ==================== 第三部分：开发实践（第26-40页）====================

  // 模块3标题页
  slide = pptx.addSlide();
  slide.background = { fill: colors.primary };
  slide.addText('模块3：Agent开发实践', {
    x: 1, y: 2, w: 8, h: 1,
    fontSize: 40, bold: true, color: colors.white, align: 'center'
  });

  // 创建Agent的步骤
  slide = pptx.addSlide();
  slide.addText('3.1 创建Agent的5步法', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const steps = [
    { step: 'Step 1', desc: '继承BaseXiaonaComponent基类' },
    { step: 'Step 2', desc: '实现_initialize()注册能力' },
    { step: 'Step 3', desc: '实现execute()处理任务' },
    { step: 'Step 4', desc: '实现get_system_prompt()' },
    { step: 'Step 5', desc: '编写测试用例' }
  ];
  steps.forEach((s, i) => {
    const y = 1.2 + i * 0.5;
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.8, y: y, w: 8.4, h: 0.45,
      fill: { color: i % 2 === 0 ? 'EBF5FB' : 'F4ECF7' }, rectRadius: 0.05
    });
    slide.addText(s.step, {
      x: 1, y: y + 0.12, fontSize: 14, bold: true, color: colors.primary
    });
    slide.addText(s.desc, {
      x: 2.2, y: y + 0.12, fontSize: 13, color: colors.dark
    });
  });

  // 代码示例：Agent类框架
  slide = pptx.addSlide();
  slide.addText('3.2 Agent类框架示例', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1, w: 9, h: 3,
    fill: { color: '1E1E1E' }, rectRadius: 0.1
  });
  const codeLines = [
    'class MyAgent(BaseXiaonaComponent):',
    '    def _initialize(self) -> None:',
    '        self._register_capabilities([...])',
    '',
    '    async def execute(self, context) -> AgentExecutionResult:',
    '        # 处理任务逻辑',
    '        return AgentExecutionResult(...)',
    '',
    '    def get_system_prompt(self) -> str:',
    '        return "你是..."'
  ];
  codeLines.forEach((line, i) => {
    slide.addText(line, {
      x: 0.7, y: 1.1 + i * 0.28, fontSize: 11, color: 'D4D4D4', fontFace: 'Courier New'
    });
  });

  // 注册能力示例
  slide = pptx.addSlide();
  slide.addText('3.3 注册能力示例', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1, w: 9, h: 2.5,
    fill: { color: '1E1E1E' }, rectRadius: 0.1
  });
  const capabilityCode = [
    'def _initialize(self) -> None:',
    '    self._register_capabilities([',
    '        AgentCapability(',
    '            name="patent_search",',
    '            description="在专利数据库中检索相关专利",',
    '            input_types=["查询关键词", "技术领域"],',
    '            output_types=["专利列表"],',
    '            estimated_time=15.0,',
    '        ),',
    '    ])'
  ];
  capabilityCode.forEach((line, i) => {
    slide.addText(line, {
      x: 0.7, y: 1.1 + i * 0.28, fontSize: 10, color: 'D4D4D4', fontFace: 'Courier New'
    });
  });

  // execute方法示例
  slide = pptx.addSlide();
  slide.addText('3.4 execute方法示例', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1, w: 9, h: 3,
    fill: { color: '1E1E1E' }, rectRadius: 0.1
  });
  const executeCode = [
    'async def execute(self, context) -> AgentExecutionResult:',
    '    try:',
    '        # 验证输入',
    '        if not self.validate_input(context):',
    '            return AgentExecutionResult(status=AgentStatus.ERROR, ...)',
    '',
    '        # 处理任务',
    '        result = await self._do_work(context.input_data)',
    '',
    '        # 返回成功结果',
    '        return AgentExecutionResult(',
    '            status=AgentStatus.COMPLETED,',
    '            output_data=result,',
    '        )',
    '    except Exception as e:',
    '        return AgentExecutionResult(status=AgentStatus.ERROR, ...)'
  ];
  executeCode.forEach((line, i) => {
    slide.addText(line, {
      x: 0.7, y: 1.1 + i * 0.26, fontSize: 10, color: 'D4D4D4', fontFace: 'Courier New'
    });
  });

  // 使用LLM
  slide = pptx.addSlide();
  slide.addText('3.5 在Agent中调用LLM', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addText('初始化LLM：', { x: 0.8, y: 1, fontSize: 16, bold: true });
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1.3, w: 9, h: 1,
    fill: { color: '1E1E1E' }, rectRadius: 0.1
  });
  slide.addText('from core.llm.unified_llm_manager import UnifiedLLMManager\nself.llm = UnifiedLLMManager()', {
    x: 0.7, y: 1.4, fontSize: 11, color: 'D4D4D4', fontFace: 'Courier New'
  });
  slide.addText('调用LLM：', { x: 0.8, y: 2.5, fontSize: 16, bold: true });
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 2.8, w: 9, h: 0.8,
    fill: { color: '1E1E1E' }, rectRadius: 0.1
  });
  slide.addText('response = await self.llm.generate(\n    prompt=prompt,\n    system_prompt=self.get_system_prompt(),\n    model="kimi-k2.5",\n)', {
    x: 0.7, y: 2.9, fontSize: 10, color: 'D4D4D4', fontFace: 'Courier New'
  });

  // 使用工具
  slide = pptx.addSlide();
  slide.addText('3.6 在Agent中使用工具', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addText('获取工具注册表：', { x: 0.8, y: 1, fontSize: 16, bold: true });
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1.3, w: 9, h: 0.6,
    fill: { color: '1E1E1E' }, rectRadius: 0.1
  });
  slide.addText('from core.tools.unified_registry import get_unified_registry\nself.tool_registry = get_unified_registry()', {
    x: 0.7, y: 1.4, fontSize: 11, color: 'D4D4D4', fontFace: 'Courier New'
  });
  slide.addText('调用工具：', { x: 0.8, y: 2.1, fontSize: 16, bold: true });
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 2.4, w: 9, h: 1,
    fill: { color: '1E1E1E' }, rectRadius: 0.1
  });
  slide.addText('tool = self.tool_registry.get("patent_search")\nresult = await tool.function(query="...", database="cnipa")', {
    x: 0.7, y: 2.5, fontSize: 11, color: 'D4D4D4', fontFace: 'Courier New'
  });

  // 处理前序Agent结果
  slide = pptx.addSlide();
  slide.addText('3.7 处理前序Agent结果', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1, w: 9, h: 2.5,
    fill: { color: '1E1E1E' }, rectRadius: 0.1
  });
  const previousCode = [
    '# 获取前序Agent的结果',
    'previous_results = context.input_data.get("previous_results", {})',
    '',
    '# 使用前序结果',
    'if "retriever" in previous_results:',
    '    patents = previous_results["retriever"]["patents"]',
    '    # 使用检索结果进行分析',
    '    result = await self._analyze_patents(patents)',
    'else:',
    '    # 不使用前序结果，独立执行',
    '    result = await self._do_work(context.input_data["user_input"])'
  ];
  previousCode.forEach((line, i) => {
    slide.addText(line, {
      x: 0.7, y: 1.1 + i * 0.26, fontSize: 10, color: 'D4D4D4', fontFace: 'Courier New'
    });
  });

  // 错误处理
  slide = pptx.addSlide();
  slide.addText('3.8 错误处理最佳实践', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const errorPractices = [
    { title: '捕获所有异常', desc: '使用try-except包裹所有可能失败的代码' },
    { title: '返回错误结果', desc: '返回带ERROR状态的AgentExecutionResult' },
    { title: '记录详细日志', desc: '使用logger.exception记录异常堆栈' },
    { title: '提供清晰错误信息', desc: 'error_message应描述问题原因' }
  ];
  errorPractices.forEach((p, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.5 + col * 4.5, y: 1 + row * 0.9, w: 4.2, h: 0.8,
      fill: { color: 'FEF5E7' }, rectRadius: 0.05
    });
    slide.addText(p.title, {
      x: 0.7 + col * 4.5, y: 1.1 + row * 0.9, fontSize: 13, bold: true, color: colors.warning
    });
    slide.addText(p.desc, {
      x: 0.7 + col * 4.5, y: 1.35 + row * 0.9, fontSize: 11, color: colors.dark
    });
  });

  // 日志记录
  slide = pptx.addSlide();
  slide.addText('3.9 日志记录指南', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const logLevels = [
    { level: 'INFO', color: colors.secondary, example: 'self.logger.info(f"开始执行: {task_id}")' },
    { level: 'DEBUG', color: colors.gray, example: 'self.logger.debug(f"输入数据: {input}")' },
    { level: 'WARNING', color: colors.warning, example: 'self.logger.warning(f"结果较少: {count}")' },
    { level: 'ERROR', color: colors.error, example: 'self.logger.error(f"任务失败: {error}")' },
    { level: 'EXCEPTION', color: colors.error, example: 'self.logger.exception(f"执行异常")' }
  ];
  logLevels.forEach((l, i) => {
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.8, y: 1 + i * 0.5, w: 8.4, h: 0.45,
      fill: { color: l.color + '15' }, rectRadius: 0.03
    });
    slide.addText(l.level, {
      x: 1, y: 1.1 + i * 0.5, fontSize: 11, bold: true, color: l.color
    });
    slide.addText(l.example, {
      x: 2, y: 1.1 + i * 0.5, fontSize: 10, color: colors.dark, fontFace: 'Courier New'
    });
  });

  // 模块3总结
  slide = pptx.addSlide();
  slide.background = { fill: colors.secondary };
  slide.addText('模块3：关键要点', {
    x: 1, y: 1.5, w: 8, h: 0.6,
    fontSize: 32, bold: true, color: colors.white, align: 'center'
  });
  const keyPoints3 = [
    '✓ 5步创建Agent：继承→初始化→执行→提示词→测试',
    '✓ 在_initialize中注册能力',
    '✓ 在execute中处理任务并返回结果',
    '✓ 做好错误处理和日志记录'
  ];
  keyPoints3.forEach((p, i) => {
    slide.addText(p, {
      x: 1.5, y: 2.5 + i * 0.4, fontSize: 18, color: colors.white
    });
  });

  // ==================== 第四部分：测试与验证（第41-50页）====================

  // 模块4标题页
  slide = pptx.addSlide();
  slide.background = { fill: colors.primary };
  slide.addText('模块4：测试与验证', {
    x: 1, y: 2, w: 8, h: 1,
    fontSize: 40, bold: true, color: colors.white, align: 'center'
  });

  // 测试类型
  slide = pptx.addSlide();
  slide.addText('4.1 测试类型', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const testTypes = [
    { type: '单元测试', desc: '测试单个方法功能', mark: 'pytest -m unit' },
    { type: '集成测试', desc: '测试Agent与其他组件协作', mark: 'pytest -m integration' },
    { type: '端到端测试', desc: '测试完整工作流', mark: 'pytest -m e2e' }
  ];
  testTypes.forEach((t, i) => {
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.8, y: 1 + i * 0.9, w: 8.4, h: 0.8,
      fill: { color: i % 2 === 0 ? 'EBF5FB' : 'E8F8F5' }, rectRadius: 0.05
    });
    slide.addText(t.type, {
      x: 1, y: 1.15 + i * 0.9, fontSize: 16, bold: true, color: colors.primary
    });
    slide.addText(t.desc, {
      x: 1, y: 1.4 + i * 0.9, fontSize: 12, color: colors.dark
    });
    slide.addText(t.mark, {
      x: 6.5, y: 1.15 + i * 0.9, fontSize: 11, color: colors.gray, fontFace: 'Courier New'
    });
  });

  // 单元测试示例
  slide = pptx.addSlide();
  slide.addText('4.2 单元测试示例', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1, w: 9, h: 2.8,
    fill: { color: '1E1E1E' }, rectRadius: 0.1
  });
  const testCode = [
    '@pytest.mark.asyncio',
    'async def test_execute_success():',
    '    """测试正常执行"""',
    '    agent = MyAgent(agent_id="test_agent")',
    '    context = AgentExecutionContext(',
    '        session_id="SESSION_001",',
    '        task_id="TASK_001",',
    '        input_data={"user_input": "test"},',
    '        config={},',
    '        metadata={},',
    '    )',
    '    result = await agent.execute(context)',
    '    assert result.status == AgentStatus.COMPLETED',
    '    assert result.output_data is not None'
  ];
  testCode.forEach((line, i) => {
    slide.addText(line, {
      x: 0.7, y: 1.1 + i * 0.23, fontSize: 10, color: 'D4D4D4', fontFace: 'Courier New'
    });
  });

  // Mock LLM响应
  slide = pptx.addSlide();
  slide.addText('4.3 模拟LLM响应', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1, w: 9, h: 2.5,
    fill: { color: '1E1E1E' }, rectRadius: 0.1
  });
  const mockCode = [
    'from unittest.mock import AsyncMock, patch',
    '',
    '@pytest.mark.asyncio',
    'async def test_with_mocked_llm():',
    '    agent = MyAgent(agent_id="test_agent")',
    '    ',
    '    # Mock LLM响应',
    '    with patch.object(agent.llm, \'generate\',',
    '                      new_callable=AsyncMock) as mock_llm:',
    '        mock_llm.return_value = \'{"result": "mocked"}\'',
    '        ',
    '        result = await agent.execute(context)',
    '        assert result.output_data["result"] == "mocked"'
  ];
  mockCode.forEach((line, i) => {
    slide.addText(line, {
      x: 0.7, y: 1.1 + i * 0.23, fontSize: 10, color: 'D4D4D4', fontFace: 'Courier New'
    });
  });

  // 测试覆盖率
  slide = pptx.addSlide();
  slide.addText('4.4 测试覆盖率', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addText('生成覆盖率报告：', { x: 0.8, y: 1, fontSize: 16, bold: true });
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.8, y: 1.3, w: 8.4, h: 0.5,
    fill: { color: '1E1E1E' }, rectRadius: 0.05
  });
  slide.addText('pytest --cov=core.agents.my_agent --cov-report=html', {
    x: 1, y: 1.4, fontSize: 12, color: 'D4D4D4', fontFace: 'Courier New'
  });
  slide.addText('覆盖率目标：', { x: 0.8, y: 2, fontSize: 16, bold: true });
  const coverageGoals = [
    { target: '核心模块', coverage: '>80%' },
    { target: '整体项目', coverage: '>70%' }
  ];
  coverageGoals.forEach((g, i) => {
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.8, y: 2.3 + i * 0.4, w: 8.4, h: 0.35,
      fill: { color: i === 0 ? 'D5F4E6' : 'FFEAA7' }, rectRadius: 0.05
    });
    slide.addText(g.target, {
      x: 1, y: 2.38 + i * 0.4, fontSize: 13, bold: true, color: colors.dark
    });
    slide.addText(g.coverage, {
      x: 7, y: 2.38 + i * 0.4, fontSize: 14, bold: true, color: colors.success
    });
  });

  // 接口合规性检查
  slide = pptx.addSlide();
  slide.addText('4.5 接口合规性检查', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  slide.addText('使用InterfaceComplianceChecker：', { x: 0.8, y: 1, fontSize: 14 });
  slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1.3, w: 9, h: 2,
    fill: { color: '1E1E1E' }, rectRadius: 0.1
  });
  const complianceCode = [
    'from tests.agents.test_interface_compliance_simple import InterfaceComplianceChecker',
    '',
    'def test_compliance():',
    '    agent = MyAgent(agent_id="test")',
    '    checker = InterfaceComplianceChecker()',
    '    results = checker.check_agent_instance(agent)',
    '    ',
    '    # 打印结果',
    '    for result in results["passed"]:',
    '        print(f"✅ {result[\'check\']}")',
    '    for result in results["failed"]:',
    '        print(f"❌ {result[\'check\']}")',
    '    ',
    '    assert len(results["failed"]) == 0'
  ];
  complianceCode.forEach((line, i) => {
    slide.addText(line, {
      x: 0.7, y: 1.4 + i * 0.23, fontSize: 9, color: 'D4D4D4', fontFace: 'Courier New'
    });
  });

  // 模块4总结
  slide = pptx.addSlide();
  slide.background = { fill: colors.secondary };
  slide.addText('模块4：关键要点', {
    x: 1, y: 1.5, w: 8, h: 0.6,
    fontSize: 32, bold: true, color: colors.white, align: 'center'
  });
  const keyPoints4 = [
    '✓ 使用pytest进行单元测试和集成测试',
    '✓ 使用Mock模拟LLM响应',
    '✓ 目标覆盖率：核心>80%，整体>70%',
    '✓ 使用InterfaceComplianceChecker检查合规性'
  ];
  keyPoints4.forEach((p, i) => {
    slide.addText(p, {
      x: 1.5, y: 2.5 + i * 0.4, fontSize: 18, color: colors.white
    });
  });

  // ==================== 第五部分：最佳实践（第51-60页）====================

  // 模块5标题页
  slide = pptx.addSlide();
  slide.background = { fill: colors.primary };
  slide.addText('模块5：最佳实践', {
    x: 1, y: 2, w: 8, h: 1,
    fontSize: 40, bold: true, color: colors.white, align: 'center'
  });

  // 能力设计原则
  slide = pptx.addSlide();
  slide.addText('5.1 能力设计原则', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const designPrinciples = [
    { principle: '✓ 单一职责', desc: '一个能力做一件事' },
    { principle: '✓ 清晰命名', desc: '使用动词+名词，如patent_search' },
    { principle: '✓ 合理估算', desc: '基于实际测试预估时间' },
    { principle: '✓ 明确输入输出', desc: '清楚描述支持的类型' }
  ];
  designPrinciples.forEach((p, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.5 + col * 4.5, y: 1 + row * 0.9, w: 4.2, h: 0.8,
      fill: { color: 'E8F8F5' }, rectRadius: 0.05
    });
    slide.addText(p.principle, {
      x: 0.7 + col * 4.5, y: 1.1 + row * 0.9, fontSize: 14, bold: true, color: colors.secondary
    });
    slide.addText(p.desc, {
      x: 0.7 + col * 4.5, y: 1.35 + row * 0.9, fontSize: 11, color: colors.dark
    });
  });

  // 错误处理最佳实践
  slide = pptx.addSlide();
  slide.addText('5.2 错误处理最佳实践', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const errorBest = [
    { do: '✓ DO', text: '捕获所有异常并返回错误结果' },
    { do: '❌ DON\'T', text: '让异常向上传播' },
    { do: '✓ DO', text: '记录详细的错误日志' },
    { do: '❌ DON\'T', text: '只记录简单的错误消息' },
    { do: '✓ DO', text: '提供清晰的错误信息给用户' },
    { do: '❌ DON\'T', text: '暴露技术栈信息' }
  ];
  errorBest.forEach((e, i) => {
    slide.addText(e.text, {
      x: 0.8, y: 1 + i * 0.4, fontSize: 12,
      color: e.do.includes('DO') ? colors.success : colors.error
    });
  });

  // 性能优化
  slide = pptx.addSlide();
  slide.addText('5.3 性能优化技巧', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const perfTips = [
    { tip: '使用异步操作', desc: 'async/await避免阻塞' },
    { tip: '并行执行', desc: '使用asyncio.gather并行处理独立任务' },
    { tip: '缓存响应', desc: '缓存LLM响应减少重复调用' },
    { tip: '限制并发', desc: '控制并发数量避免资源耗尽' }
  ];
  perfTips.forEach((p, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.5 + col * 4.5, y: 1 + row * 0.9, w: 4.2, h: 0.8,
      fill: { color: 'FEF9E7' }, rectRadius: 0.05
    });
    slide.addText(p.tip, {
      x: 0.7 + col * 4.5, y: 1.1 + row * 0.9, fontSize: 13, bold: true, color: colors.warning
    });
    slide.addText(p.desc, {
      x: 0.7 + col * 4.5, y: 1.35 + row * 0.9, fontSize: 11, color: colors.dark
    });
  });

  // 常见错误
  slide = pptx.addSlide();
  slide.addText('5.4 常见错误', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const commonErrors = [
    { error: '忘记注册能力', fix: '在_initialize中调用_register_capabilities' },
    { error: '未验证输入', fix: '实现validate_input方法' },
    { error: '返回异常而非结果', fix: '捕获异常并返回ERROR状态结果' },
    { error: '缺少日志', fix: '使用self.logger记录关键操作' },
    { error: '同步调用异步方法', fix: '使用await调用异步方法' }
  ];
  commonErrors.forEach((e, i) => {
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.8, y: 1 + i * 0.5, w: 8.4, h: 0.45,
      fill: { color: 'FADBD8' }, rectRadius: 0.03
    });
    slide.addText(e.error, {
      x: 1, y: 1.1 + i * 0.5, fontSize: 12, bold: true, color: colors.error
    });
    slide.addText(`→ ${e.fix}`, {
      x: 3.5, y: 1.1 + i * 0.5, fontSize: 11, color: colors.dark
    });
  });

  // 部署流程
  slide = pptx.addSlide();
  slide.addText('5.5 Agent部署流程', {
    x: 0.5, y: 0.4, w: 9, h: 0.5,
    fontSize: 28, bold: true, color: colors.primary
  });
  const deploySteps = [
    { step: '1', desc: '放置代码到core/agents/', icon: '📁' },
    { step: '2', desc: '注册Agent到AgentRegistry', icon: '📝' },
    { step: '3', desc: '运行测试验证功能', icon: '🧪' },
    { step: '4', desc: '重启平台服务', icon: '🔄' }
  ];
  deploySteps.forEach((s, i) => {
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
      x: 0.8 + i * 2.2, y: 1.5, w: 2, h: 1.5,
      fill: { color: colors.secondary }, rectRadius: 0.1
    });
    slide.addText(`${s.icon} ${s.step}`, {
      x: 0.8 + i * 2.2, y: 1.7, fontSize: 24, color: colors.white, align: 'center'
    });
    slide.addText(s.desc, {
      x: 0.8 + i * 2.2, y: 2.3, fontSize: 10, color: colors.white, align: 'center'
    });
  });

  // 培训总结
  slide = pptx.addSlide();
  slide.background = { fill: colors.primary };
  slide.addText('培训总结', {
    x: 1, y: 1, w: 8, h: 0.6,
    fontSize: 36, bold: true, color: colors.white, align: 'center'
  });
  const summary = [
    '✓ Agent是平台的基本执行单元',
    '✓ 统一接口确保一致性和可维护性',
    '✓ 5步创建Agent：继承→初始化→执行→提示词→测试',
    '✓ 完整的测试覆盖和合规性检查',
    '✓ 遵循最佳实践避免常见错误'
  ];
  summary.forEach((s, i) => {
    slide.addText(s, {
      x: 1.5, y: 2 + i * 0.4, fontSize: 18, color: colors.white
    });
  });

  // 结束页
  slide = pptx.addSlide();
  slide.background = { fill: colors.secondary };
  slide.addText('谢谢！', {
    x: 1, y: 1.5, w: 8, h: 0.6,
    fontSize: 48, bold: true, color: colors.white, align: 'center'
  });
  slide.addText('Q&A', {
    x: 1, y: 2.5, w: 8, h: 0.4,
    fontSize: 28, color: colors.light, align: 'center'
  });
  slide.addText('参考文档：docs/guides/AGENT_*.md', {
    x: 1, y: 3.5, w: 8, h: 0.3,
    fontSize: 14, color: colors.white, align: 'center'
  });

  // 保存文件
  await pptx.writeFile({ fileName: 'AGENT_STANDARD_TRAINING.pptx' });
  console.log('PPT生成成功！共', pptx.slides.length, '页');
}

createPresentation().catch(console.error);
