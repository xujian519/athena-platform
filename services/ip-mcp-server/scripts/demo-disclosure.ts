#!/usr/bin/env bun
/**
 * 交底书理解演示脚本
 * 演示 MCP Server 如何理解技术交底书并生成分析报告
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 颜色输出
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  dim: "\x1b[2m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  magenta: "\x1b[35m",
  cyan: "\x1b[36m",
};

function color(name: keyof typeof colors, text: string) {
  return `${colors[name]}${text}${colors.reset}`;
}

function printSection(title: string) {
  console.log();
  console.log(color("cyan", "═".repeat(60)));
  console.log(color("bright", `  ${title}`));
  console.log(color("cyan", "═".repeat(60)));
  console.log();
}

function printSubSection(title: string) {
  console.log();
  console.log(color("yellow", `▸ ${title}`));
  console.log(color("dim", "─".repeat(50)));
}

// 示例交底书
const SAMPLE_DISCLOSURE = `技术交底书：智能健康监测手表

【发明名称】
一种集成多传感器融合的健康监测智能手表

【技术领域】
本发明涉及可穿戴智能设备领域，特别是涉及一种能够实时监测用户健康状态的智能手表。

【背景技术】
现有的智能手表虽然具备一定的健康监测功能，但普遍存在以下问题：
1. 传感器数据单一，仅依靠加速度计或单一光电传感器，监测精度有限；
2. 数据处理能力不足，无法实时分析复杂的生理信号；
3. 功耗管理不当，频繁充电影响用户体验；
4. 缺乏智能预警功能，无法在异常情况下及时提醒用户。

【发明内容】
本发明的目的在于提供一种集成多传感器融合的健康监测智能手表，解决现有技术中监测精度低、功耗高、功能单一的问题。

为实现上述目的，本发明采用以下技术方案：

一种智能手表，包括：
外壳组件，包括表壳和表带；
显示模块，设置在表壳正面，包括触控显示屏；
核心处理模块，包括低功耗处理器、存储器和通信单元；
多传感器采集模块，包括：
  - 光电心率传感器，采用多波长LED和光电二极管；
  - 三轴加速度计，用于检测运动和姿态；
  - 血氧饱和度传感器；
  - 温度传感器，用于监测体表温度；
电源管理模块，包括可充电电池和电源管理芯片；
智能分析模块，用于融合多传感器数据进行健康状态分析；
预警模块，用于在检测到异常健康指标时发出警报。

【有益效果】
本发明通过集成多传感器融合技术，具有以下有益效果：
1. 监测精度高 - 通过多传感器数据融合和智能算法，显著提高健康数据监测的准确性；
2. 功耗优化 - 采用低功耗处理器和智能电源管理，延长续航时间至7天以上；
3. 功能丰富 - 集成心率、血氧、体温等多维度健康监测功能；
4. 智能预警 - 实时分析健康数据，及时预警异常情况，保障用户健康安全。

【附图说明】
图1为本发明智能手表的整体结构示意图；
图2为多传感器采集模块的组成框图；
图3为智能分析模块的数据处理流程图。

【具体实施方式】
以下结合附图对本发明的具体实施方式进行详细说明。

实施例1：整体结构设计
如图1所示，本发明的智能手表包括外壳组件、显示模块、核心处理模块、多传感器采集模块、电源管理模块、智能分析模块和预警模块。

外壳组件采用医用级不锈钢和硅胶材质，确保佩戴舒适性和耐用性。表壳尺寸为44mm×38mm×10.7mm，重量约45克，适合全天候佩戴。

显示模块采用1.78英寸AMOLED触控显示屏，分辨率为448×368像素，支持Always-On显示功能，在保证信息可视性的同时优化功耗。

实施例2：多传感器融合采集
如图2所示，多传感器采集模块包括四个核心传感器：

心率传感器采用多波长PPG技术，配置绿色(525nm)、红色(660nm)和红外(940nm)三种LED光源，配合高灵敏度光电二极管，实现医疗级心率监测精度(误差<±2bpm)。

三轴加速度计采用低功耗MEMS传感器，量程为±16g，采样频率为100Hz，用于检测运动状态、计步和姿态识别。

血氧传感器采用反射式PPG技术，通过红外和红光的双波长测量，实现血氧饱和度(SpO2)监测，测量范围为70%-100%，精度为±2%。

温度传感器采用高精度热敏电阻，测量范围为20°C-45°C，精度为±0.1°C，用于监测体表温度变化。

实施例3：智能分析与预警
如图3所示，智能分析模块采用多层级数据处理架构：

数据采集层负责各传感器的原始数据采集和预处理，包括滤波、去噪和校准。

特征提取层从预处理后的数据中提取关键特征，如心率变异性(HRV)、步态特征、血氧波形等。

融合分析层采用机器学习算法，对多源特征进行融合分析，建立个人健康基线模型，识别异常模式。

预警模块基于融合分析结果，当检测到以下异常情况时触发警报：
- 心率持续异常(>120bpm或<40bpm超过5分钟)
- 血氧饱和度低于90%
- 体温异常(>38°C或<35°C)
- 跌倒检测(通过加速度计数据分析)

预警方式包括手表震动提醒、屏幕显示警告信息，以及通过配套手机APP向紧急联系人发送通知。

通过上述实施方式，本发明的智能手表实现了高精度健康监测、低功耗长续航、智能预警等功能，为用户提供全面的健康守护。`;

// 主函数
async function main() {
  printSection("IP MCP Server 测试脚本");
  console.log(color("dim", `启动时间: ${new Date().toLocaleString()}`));
  console.log(color("dim", `服务器路径: ${CONFIG.serverPath}`));

  let client: Client | null = null;
  let transport: StdioClientTransport | null = null;

  try {
    // 1. 连接到服务器
    printSection("1. 建立连接");
    console.log(color("blue", "正在启动 MCP Server..."));

    transport = new StdioClientTransport({
      command: "bun",
      args: [CONFIG.serverPath],
    });

    client = new Client(
      {
        name: "mcp-test-client",
        version: "1.0.0",
      },
      {
        capabilities: {
          prompts: {},
          resources: {},
          tools: {},
        },
      },
    );

    await client.connect(transport);
    console.log(color("green", "✓ 成功连接到 MCP Server"));

    // 2. 获取工具列表
    printSection("2. 可用工具列表");
    const toolsResponse = await client.listTools();
    console.log(
      color("blue", `发现 ${toolsResponse.tools.length} 个可用工具:`),
    );
    console.log();

    toolsResponse.tools.forEach((tool, index) => {
      console.log(color("yellow", `${index + 1}. ${tool.name}`));
      console.log(color("dim", `   ${tool.description || "无描述"}`));
      console.log();
    });

    // 3. 测试 understand_disclosure
    printSection("3. 测试 understand_disclosure 工具");
    console.log(color("blue", "发送示例交底书进行分析..."));
    console.log(color("dim", `交底书长度: ${SAMPLE_DISCLOSURE.length} 字符`));
    console.log();

    const understandResult = await client.callTool({
      name: "understand_disclosure",
      arguments: {
        content: SAMPLE_DISCLOSURE,
        language: "zh",
      },
    });

    console.log(color("green", "✓ 分析完成"));
    console.log();

    // 显示分析结果
    if (understandResult.content && Array.isArray(understandResult.content)) {
      const textContent = understandResult.content.find(
        (c: { type: string; text?: string }) => c.type === "text",
      );
      if (textContent?.text) {
        try {
          const parsed = JSON.parse(textContent.text);
          printSubSection("分析结果概览");
          console.log(
            color("cyan", "发明标题:"),
            parsed.inventionTitle || "N/A",
          );
          console.log(
            color("cyan", "技术领域:"),
            parsed.technicalField || "N/A",
          );
          console.log(
            color("cyan", "核心问题数:"),
            parsed.problems?.length || 0,
          );
          console.log(
            color("cyan", "技术效果数:"),
            parsed.effects?.length || 0,
          );
          console.log(
            color("cyan", "实施方式数:"),
            parsed.embodiments?.length || 0,
          );
        } catch (e) {
          console.log(color("yellow", "⚠ 无法解析结果，原始输出:"));
          console.log(textContent.text.substring(0, 500) + "...");
        }
      }
    }

    // 4. 测试 draft_specification
    printSection("4. 测试 draft_specification 工具");
    console.log(color("blue", "生成专利说明书片段..."));
    console.log();

    const specResult = await client.callTool({
      name: "draft_specification",
      arguments: {
        inventionTitle: "一种智能手表",
        technicalField: "智能可穿戴设备领域",
        backgroundArt: `现有的智能手表通常功能单一，用户体验不佳。具体存在的问题包括：
1. 传感器数据单一，监测精度有限
2. 数据处理能力不足，无法实时分析复杂生理信号
3. 功耗管理不当，频繁充电影响用户体验`,
        summary: `本发明提供一种集成多传感器的智能手表，包括显示屏、处理器、电池和传感器，用于监测用户健康数据。

本发明通过多传感器数据融合和智能算法，显著提高健康数据监测的准确性；采用低功耗处理器和智能电源管理，延长续航时间。`,
        embodiments: [
          {
            title: "实施方式1：整体结构",
            description: `智能手表包括表体、表带、显示屏、处理器、电池、心率传感器和加速度计。

表体采用医用级不锈钢材质，显示屏采用AMOLED触控屏，处理器采用低功耗芯片用于处理传感器数据。`,
          },
        ],
        claims: [
          "一种智能手表，包括：表体；显示屏，设置在所述表体正面；处理器，设置在所述表体内；电池，用于为所述智能手表供电；心率传感器，设置在所述表体背面，与所述处理器电连接；和加速度计，设置在所述表体内，与所述处理器电连接。",
          "根据权利要求1所述的智能手表，其特征在于，所述心率传感器包括绿色LED光源和光电二极管，采用光电容积脉搏波描记法检测心率。",
        ],
        language: "zh",
      },
    });

    console.log(color("green", "✓ 说明书生成完成"));
    console.log();

    // 显示生成的说明书片段
    if (specResult.content && Array.isArray(specResult.content)) {
      const textContent = specResult.content.find(
        (c: { type: string; text?: string }) => c.type === "text",
      );
      if (textContent?.text) {
        printSubSection("生成的说明书片段");
        console.log(color("dim", textContent.text.substring(0, 800) + "..."));
        console.log();
        console.log(color("blue", `总长度: ${textContent.text.length} 字符`));
      }
    }

    // 5. 测试 generate_claims
    printSection("5. 测试 generate_claims 工具");
    console.log(color("blue", "生成专利权利要求..."));
    console.log();

    const claimsResult = await client.callTool({
      name: "generate_claims",
      arguments: {
        inventionTitle: "一种智能手表",
        technicalField: "智能可穿戴设备",
        problemSolved: "现有智能手表传感器精度不足，监测数据不准确，续航时间短",
        technicalSolution: `智能手表包括表体、显示屏、处理器、电池、心率传感器和加速度计。

心率传感器采用PPG技术，配置绿色、红色和红外LED光源，配合高灵敏度光电二极管，实现医疗级心率监测精度。

处理器采用低功耗芯片，对多传感器数据进行融合分析和智能算法处理。`,
        beneficialEffects:
          "提高健康数据监测准确性，延长续航时间，实现智能预警功能",
        priorArt: [
          "现有智能手表传感器精度不足，监测数据不准确",
          "电池续航时间短，需要频繁充电",
          "缺乏智能分析功能，无法实时预警",
        ],
        embodiments: [
          "实施方式1：整体结构 - 包括表体、显示屏、处理器、电池、心率传感器和加速度计",
          "实施方式2：心率监测 - 采用PPG技术，配置多波长LED光源和高灵敏度光电二极管",
        ],
        claimType: "independent",
        language: "zh",
      },
    });

    console.log(color("green", "✓ 权利要求生成完成"));
    console.log();

    // 显示生成的权利要求
    if (claimsResult.content && Array.isArray(claimsResult.content)) {
      const textContent = claimsResult.content.find(
        (c: { type: string; text?: string }) => c.type === "text",
      );
      if (textContent?.text) {
        printSubSection("生成的权利要求");
        console.log(textContent.text);
      }
    }

    // 测试完成
    printSection("测试完成");
    console.log(color("green", "✅ 所有测试已成功完成!"));
    console.log();
    console.log(color("blue", "测试总结:"));
    console.log(`  - 服务器连接: ${color("green", "✓ 正常")}`);
    console.log(`  - 工具列表: ${color("green", "✓ 已获取")}`);
    console.log(`  - understand_disclosure: ${color("green", "✓ 通过")}`);
    console.log(`  - draft_specification: ${color("green", "✓ 通过")}`);
    console.log(`  - generate_claims: ${color("green", "✓ 通过")}`);

    await client.close();
  } catch (error) {
    log("error", "测试失败", error);
    process.exit(1);
  }
}

// 运行测试
runTests();
