# 专利说明书附图（SVG矢量图版本）

> 由于ComfyUI是AI图像生成工具，不适合绘制专利附图
> 现提供SVG矢量图版本，可直接用浏览器打开或导入CAD软件

---

## 使用说明

### 方法一：直接在浏览器中查看

1. 复制下方的SVG代码
2. 保存为 `.svg` 文件（如 `figure1.svg`）
3. 用浏览器（Chrome、Edge、Safari）打开
4. 可缩放查看，矢量图不失真

### 方法二：导入到CAD软件

1. 将SVG文件导入到AutoCAD/中望CAD
2. 使用 `IMPORT` 命令
3. 在CAD中进一步编辑和标注

### 方法三：使用在线工具转换

1. 打开 https://www.aconvert.com/cn/svg-to-dwg/
2. 上传SVG文件
3. 转换为DWG格式
4. 在AutoCAD中打开编辑

---

## 图1：整体结构示意图

```svg
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <!-- 背景填充 -->
  <rect x="0" y="0" width="800" height="600" fill="#ffffff"/>

  <!-- 标题 -->
  <text x="400" y="30" text-anchor="middle" font-size="20" font-weight="bold">图1：整体结构示意图</text>

  <!-- 壳体 -->
  <rect x="100" y="80" width="600" height="450" fill="#f0f0f0" stroke="#000" stroke-width="2"/>

  <!-- 封头-上 -->
  <rect x="120" y="100" width="560" height="60" fill="#e0e0e0" stroke="#000" stroke-width="2"/>
  <text x="140" y="115" font-size="14">封头(30)</text>

  <!-- 管程进口 -->
  <rect x="140" y="120" width="60" height="25" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <text x="170" y="137" text-anchor="middle" font-size="11">管程进口(31)</text>

  <!-- 管程出口 -->
  <rect x="600" y="120" width="60" height="25" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <text x="630" y="137" text-anchor="middle" font-size="11">管程出口(32)</text>

  <!-- 管板-上 -->
  <rect x="120" y="160" width="560" height="15" fill="#d0d0d0" stroke="#000" stroke-width="2"/>
  <text x="350" y="172" font-size="12">管板(20)</text>

  <!-- 换热管束区域 -->
  <rect x="130" y="180" width="540" height="280" fill="#e8e8e8" stroke="#000" stroke-width="1"/>

  <!-- 换热管示意 -->
  <g id="tubes">
    <ellipse cx="180" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="200" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="220" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="240" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="260" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="280" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="300" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="320" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="340" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="360" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="380" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="400" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="420" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="440" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="460" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="480" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="500" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="520" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="540" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="560" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="580" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="600" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
    <ellipse cx="620" cy="200" rx="8" ry="8" fill="#ffffff" stroke="#000" stroke-width="1"/>
  </g>

  <!-- 复合式扰流组件 -->
  <g transform="translate(150, 240)">
    <path d="M0 20 L500 20 L490 40 L10 40 Z" fill="#d8d8d8" stroke="#000" stroke-width="1.5"/>
    <path d="M0 70 L500 70 L490 50 L10 50 Z" fill="#d8d8d8" stroke="#000" stroke-width="1.5"/>
    <path d="M0 120 L500 120 L490 100 L10 100 Z" fill="#d8d8d8" stroke="#000" stroke-width="1.5"/>
    <path d="M0 170 L500 170 L490 150 L10 150 Z" fill="#d8d8d8" stroke="#000" stroke-width="1.5"/>
    <path d="M0 220 L500 220 L490 200 L10 200 Z" fill="#d8d8d8" stroke="#000" stroke-width="1.5"/>
    <text x="250" y="125" text-anchor="middle" font-size="12">复合式扰流组件(50)</text>
  </g>

  <!-- 管板-下 -->
  <rect x="120" y="460" width="560" height="15" fill="#d0d0d0" stroke="#000" stroke-width="2"/>

  <!-- 封头-下 -->
  <rect x="120" y="480" width="560" height="40" fill="#e0e0e0" stroke="#000" stroke-width="2"/>

  <!-- 壳程进口 -->
  <rect x="100" y="240" width="30" height="40" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <text x="115" y="265" text-anchor="middle" font-size="10" writing-mode="tb">壳程进口(11)</text>

  <!-- 壳程出口 -->
  <rect x="670" y="350" width="30" height="40" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <text x="685" y="375" text-anchor="middle" font-size="10" writing-mode="tb">壳程出口(12)</text>

  <!-- 标注线：换热管束 -->
  <line x1="690" y1="200" x2="650" y2="200" stroke="#000" stroke-width="1"/>
  <text x="695" y="200" font-size="11">换热管束(40)</text>

  <!-- 标注线：复合式扰流组件 -->
  <line x1="690" y1="310" x2="670" y2="310" stroke="#000" stroke-width="1"/>
  <text x="695" y="310" font-size="11">复合式扰流组件(50)</text>

</svg>
```

---

## 图4：渐变式导流结构（核心创新点）

```svg
<svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
  <!-- 背景 -->
  <rect x="0" y="0" width="600" height="400" fill="#ffffff"/>

  <!-- 标题 -->
  <text x="300" y="30" text-anchor="middle" font-size="18" font-weight="bold">图4：渐变式导流结构局部放大图</text>
  <text x="300" y="55" text-anchor="middle" font-size="12" fill="#666">（A处局部放大）</text>

  <!-- 扰流板主体 -->
  <rect x="50" y="100" width="500" height="180" fill="#e0e0e0" stroke="#000" stroke-width="2"/>
  <text x="300" y="120" text-anchor="middle" font-size="12">扰流板(51)板面</text>

  <!-- 壳体内壁示意 -->
  <path d="M500 100 Q530 190 500 280" fill="none" stroke="#333" stroke-width="3" stroke-dasharray="10,5"/>
  <text x="540" y="200" font-size="11">壳体内壁</text>

  <!-- 边缘区域 -->
  <rect x="400" y="100" width="150" height="180" fill="#d0ffd0" stroke="#000" stroke-width="1" stroke-dasharray="5,3"/>
  <text x="475" y="90" text-anchor="middle" font-size="11">边缘区域(515)</text>

  <!-- 导流孔 - 渐变大小 -->
  <!-- 大孔（中部） -->
  <circle cx="420" cy="120" r="12" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <circle cx="440" cy="130" r="11" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <circle cx="460" cy="140" r="10" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <circle cx="480" cy="150" r="9" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <circle cx="500" cy="160" r="8" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <circle cx="515" cy="170" r="7" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <circle cx="525" cy="180" r="6" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <circle cx="430" cy="200" r="12" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <circle cx="450" cy="210" r="11" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <circle cx="470" cy="220" r="10" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <circle cx="490" cy="230" r="9" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <circle cx="505" cy="240" r="8" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <circle cx="515" cy="250" r="7" fill="#ffffff" stroke="#000" stroke-width="1.5"/>
  <circle cx="525" cy="260" r="6" fill="#ffffff" stroke="#000" stroke-width="1.5"/>

  <!-- 导流斜面 -->
  <line x1="408" y1="130" x2="430" y2="130" stroke="#ff6600" stroke-width="3"/>
  <line x1="428" y1="150" x2="448" y2="150" stroke="#ff6600" stroke-width="3"/>
  <line x1="448" y1="170" x2="466" y2="170" stroke="#ff6600" stroke-width="3"/>
  <line x1="466" y1="190" x2="482" y2="190" stroke="#ff6600" stroke-width="3"/>
  <line x1="480" y1="210" x2="494" y2="210" stroke="#ff6600" stroke-width="3"/>
  <line x1="492" y1="230" x2="504" y2="230" stroke="#ff6600" stroke-width="3"/>
  <line x1="500" y1="250" x2="510" y2="250" stroke="#ff6600" stroke-width="3"/>
  <line x1="506" y1="270" x2="514" y2="270" stroke="#ff6600" stroke-width="3"/>

  <!-- 图例说明 -->
  <rect x="50" y="320" width="300" height="70" fill="#fffbe0" stroke="#000" stroke-width="1.5"/>
  <text x="200" y="340" text-anchor="middle" font-size="12" font-weight="bold">技术参数</text>
  <text x="60" y="355" font-size="11">• 导流孔孔径：12mm → 6mm（渐变）</text>
  <text x="60" y="370" font-size="11">• 导流斜面角度：30-45°</text>
  <text x="60" y="385" font-size="11">• 分布密度：间距30mm → 20mm</text>

  <!-- 流体方向箭头 -->
  <path d="M80 160 L120 160" stroke="#0066cc" stroke-width="2" marker-end="url(#arrowhead)"/>
  <text x="100" y="150" text-anchor="middle" font-size="10" fill="#0066cc">流体流动</text>

  <!-- 箭头定义 -->
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#0066cc"/>
    </marker>
  </defs>

</svg>
```

---

## 图5：管间扰动元件结构示意图

```svg
<svg width="700" height="500" xmlns="http://www.w3.org/2000/svg">
  <!-- 背景 -->
  <rect x="0" y="0" width="700" height="500" fill="#ffffff"/>

  <!-- 标题 -->
  <text x="350" y="30" text-anchor="middle" font-size="18" font-weight="bold">图5：管间扰动元件结构示意图</text>

  <!-- 主视图 -->
  <rect x="50" y="70" width="280" height="200" fill="#f8f8f8" stroke="#000" stroke-width="1.5"/>
  <text x="190" y="90" text-anchor="middle" font-size="12" font-weight="bold">【主视图】</text>

  <!-- 换热管 -->
  <circle cx="120" cy="150" r="20" fill="#ffffff" stroke="#000" stroke-width="2"/>
  <circle cx="260" cy="150" r="20" fill="#ffffff" stroke="#000" stroke-width="2"/>

  <!-- 波纹片 -->
  <g transform="translate(190, 150)">
    <path d="M-60 -20 Q-40 0 -20 20 T20 20 T60 20 T100 20" fill="none" stroke="#ff6600" stroke-width="3"/>
    <path d="M-60 0 Q-40 20 -20 40 T20 40 T60 40 T100 40" fill="none" stroke="#ff6600" stroke-width="3"/>
    <path d="M-60 20 Q-40 40 -20 60 T20 60 T60 60 T100 60" fill="none" stroke="#ff6600" stroke-width="3"/>
  </g>

  <!-- 固定翼 -->
  <rect x="130" y="130" width="20" height="40" fill="#9090ff" stroke="#000" stroke-width="1"/>
  <rect x="250" y="130" width="20" height="40" fill="#9090ff" stroke="#000" stroke-width="1"/>

  <!-- 标注 -->
  <text x="190" y="210" text-anchor="middle" font-size="10">波纹片(521)</text>
  <text x="140" y="125" text-anchor="middle" font-size="9">固定翼</text>
  <text x="260" y="125" text-anchor="middle" font-size="9">固定翼</text>

  <!-- 俯视图 -->
  <rect x="370" y="70" width="280" height="180" fill="#f8f8f8" stroke="#000" stroke-width="1.5"/>
  <text x="510" y="90" text-anchor="middle" font-size="12" font-weight="bold">【俯视图】</text>

  <!-- 换热管 -->
  <circle cx="440" cy="120" r="20" fill="#ffffff" stroke="#000" stroke-width="2"/>
  <circle cx="580" cy="120" r="20" fill="#ffffff" stroke="#000" stroke-width="2"/>
  <circle cx="440" cy="200" r="20" fill="#ffffff" stroke="#000" stroke-width="2"/>
  <circle cx="580" cy="200" r="20" fill="#ffffff" stroke="#000" stroke-width="2"/>

  <!-- 固定翼 -->
  <rect x="450" y="100" width="20" height="40" fill="#9090ff" stroke="#000" stroke-width="1"/>
  <rect x="570" y="100" width="20" height="40" fill="#9090ff" stroke="#000" stroke-width="1"/>
  <rect x="450" y="180" width="20" height="40" fill="#9090ff" stroke="#000" stroke-width="1"/>
  <rect x="570" y="180" width="20" height="40" fill="#9090ff" stroke="#000" stroke-width="1"/>

  <!-- 侧视图 -->
  <rect x="50" y="300" width="280" height="180" fill="#f8f8f8" stroke="#000" stroke-width="1.5"/>
  <text x="190" y="320" text-anchor="middle" font-size="12" font-weight="bold">【侧视图】</text>

  <!-- 换热管 -->
  <rect x="120" y="340" width="20" height="80" fill="#ffffff" stroke="#000" stroke-width="2"/>

  <!-- 波纹片示意 -->
  <path d="M150 360 L150 400" stroke="#ff6600" stroke-width="2" stroke-dasharray="3,2"/>
  <path d="M155 365 L155 395" stroke="#ff6600" stroke-width="2" stroke-dasharray="3,2"/>
  <path d="M160 370 L160 390" stroke="#ff6600" stroke-width="2" stroke-dasharray="3,2"/>

  <!-- 固定翼 -->
  <rect x="140" y="350" width="40" height="15" fill="#9090ff" stroke="#000" stroke-width="1"/>

  <!-- 技术参数表 -->
  <rect x="400" y="300" width="280" height="180" fill="#fffbe0" stroke="#000" stroke-width="1.5"/>
  <text x="540" y="320" text-anchor="middle" font-size="12" font-weight="bold">技术参数</text>
  <text x="420" y="345" font-size="11">• 波纹角度：45-60°</text>
  <text x="420" y="365" font-size="11">• 波纹高度：3-8mm</text>
  <text x="420" y="385" font-size="11">• 波纹间距：5-12mm</text>
  <text x="420" y="405" font-size="11">• 固定翼长度：10-20mm</text>
  <text x="420" y="425" font-size="11">• 材质：不锈钢/铝合金</text>
  <text x="420" y="445" font-size="11">• 安装方式：弹性卡扣</text>
  <text x="420" y="465" font-size="11">• 作用：破坏边界层</text>

</svg>
```

---

## 图6：自适应支撑系统结构示意图

```svg
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <!-- 背景 -->
  <rect x="0" y="0" width="800" height="600" fill="#ffffff"/>

  <!-- 标题 -->
  <text x="400" y="30" text-anchor="middle" font-size="18" font-weight="bold">图6：自适应支撑系统结构示意图</text>

  <!-- 壳体内壁 -->
  <rect x="50" y="100" width="700" height="400" fill="#f0f0f0" stroke="#000" stroke-width="2"/>
  <text x="60" y="120" font-size="12">壳体(10)内壁</text>

  <!-- 滑动导轨 -->
  <rect x="70" y="150" width="30" height="300" fill="#909090" stroke="#000" stroke-width="2"/>
  <text x="85" y="170" font-size="10" writing-mode="tb">滑动导轨(62)</text>

  <!-- 换热管束示意 -->
  <rect x="150" y="200" width="500" height="60" fill="#e0e0e0" stroke="#000" stroke-width="2"/>
  <text x="400" y="235" text-anchor="middle" font-size="12">换热管束(40)</text>

  <!-- 弹性支撑座 -->
  <g transform="translate(400, 350)">
    <!-- 支撑座本体 -->
    <rect x="-60" y="0" width="120" height="80" fill="#d0d0d0" stroke="#000" stroke-width="2"/>
    <text x="0" y="-15" text-anchor="middle" font-size="11">弹性支撑座(61)</text>

    <!-- 弹性元件 -->
    <rect x="-30" y="20" width="60" height="30" fill="#ff9999" stroke="#000" stroke-width="1.5"/>
    <path d="M-20 35 L-20 25 L20 25 L20 35" fill="#ffcccc" stroke="#000" stroke-width="1"/>
    <path d="M-10 35 L-10 25 L10 25 L10 35" fill="#ffcccc" stroke="#000" stroke-width="1"/>
    <path d="M0 35 L0 25 L20 25 L20 35" fill="#ffcccc" stroke="#000" stroke-width="1"/>
    <path d="M10 35 L10 25 L30 25 L30 35" fill="#ffcccc" stroke="#000" stroke-width="1"/>
    <text x="0" y="15" text-anchor="middle" font-size="9">弹性元件(612)</text>

    <!-- 支撑板 -->
    <rect x="-50" y="-20" width="100" height="15" fill="#9090ff" stroke="#000" stroke-width="1.5"/>
    <line x1="0" y1="-20" x2="0" y2="20" stroke="#000" stroke-width="2" stroke-dasharray="3,2"/>
    <text x="60" y="-10" font-size="9">支撑板(613)</text>
  </g>

  <!-- 定位锁定机构放大图 -->
  <rect x="600" y="400" width="180" height="180" fill="#fffbe0" stroke="#000" stroke-width="1.5"/>
  <text x="690" y="420" text-anchor="middle" font-size="11" font-weight="bold">定位锁定机构(63)</text>

  <!-- 偏心轮 -->
  <circle cx="690" cy="460" r="25" fill="#e0e0e0" stroke="#000" stroke-width="2"/>
  <circle cx="690" cy="460" r="15" fill="#ffffff" stroke="#000" stroke-width="1"/>

  <!-- 锁定槽 -->
  <path d="M690 445 L680 455 L700 455" fill="none" stroke="#ff6600" stroke-width="2"/>

  <!-- 操作手柄 -->
  <line x1="715" y1="460" x2="745" y2="460" stroke="#000" stroke-width="3"/>
  <rect x="740" y="450" width="15" height="20" fill="#909090" stroke="#000" stroke-width="1.5"/>

  <!-- 锁定销 -->
  <rect x="650" y="455" width="25" height="8" fill="#ffcc00" stroke="#000" stroke-width="1"/>
  <line x1="675" y1="459" x2="690" y2="460" stroke="#000" stroke-width="1.5" stroke-dasharray="2,1"/>

  <!-- 工作原理说明 -->
  <rect x="50" y="520" width="700" height="70" fill="#f0f8ff" stroke="#000" stroke-width="1"/>
  <text x="400" y="540" text-anchor="middle" font-size="12" font-weight="bold">工作原理</text>
  <text x="70" y="558" font-size="11">1. 热膨胀：换热管束伸长ΔT → 2. 弹性压缩：F=K×ΔL → 3. 滑动导向：沿导轨移动 → 4. 锁定：嵌入锁定槽</text>

</svg>
```

---

## 文件保存说明

### 如何保存和使用SVG文件

#### 方法一：保存单个SVG文件

1. 复制上任意一张图的SVG代码
2. 打开文本编辑器（记事本、TextEdit等）
3. 粘贴代码
4. 保存为 `figure1.svg`（注意后缀是.svg）
5. 双击文件用浏览器打开

#### 方法二：批量保存所有SVG文件

将所有SVG代码分别保存为：
- `figure1.svg` - 整体结构示意图
- `figure4.svg` - 渐变式导流结构
- `figure5.svg` - 管间扰动元件
- `figure6.svg` - 自适应支撑系统

#### 方法三：在浏览器中预览

1. 将SVG代码复制到在线SVG查看器：https://www.svgviewer.dev/
2. 粘贴代码
3. 点击"Render"预览效果

---

## 🎨 推荐的CAD绘制软件

### 免费方案

| 软件 | 特点 | 推荐度 |
|------|------|--------|
| **LibreCAD** | 开源免费，兼容AutoCAD | ⭐⭐⭐⭐⭐ |
| **QCAD** | 免费版功能够用 | ⭐⭐⭐⭐ |
| **FreeCAD** | 3D建模功能强 | ⭐⭐⭐⭐ |

### 付费方案

| 软件 | 特点 | 适用场景 |
|------|------|---------|
| **AutoCAD** | 行业标准 | 正式专利申请 |
| **中望CAD** | 国产软件，中文 | 快速上手 |
| **CAXA** | 简单易学 | 初学者 |

### 在线方案（无需安装）

| 网站 | 功能 | 链接 |
|------|------|------|
| **draw.io** | 免费在线绘图 | https://app.diagrams.net/ |
| **ProcessOn** | 流程图专用 | https://www.processon.com/ |

---

**文件路径**：`/Users/xujian/Athena工作平台/专利说明书_附图_SVG版本.md`
