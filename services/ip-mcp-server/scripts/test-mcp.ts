#!/usr/bin/env bun
/**
 * MCP Server 测试脚本
 * 测试所有主要工具的可用性和功能
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 测试配置
const CONFIG = {
  serverPath: join(__dirname, "../dist/index.js"),
  timeout: 30000,
};

// 日志工具
function log(
  level: "info" | "success" | "error" | "warn",
  message: string,
  data?: unknown,
) {
  const timestamp = new Date().toISOString();
  const icons = { info: "ℹ️", success: "✅", error: "❌", warn: "⚠️" };
  console.log(`[${timestamp}] ${icons[level]} ${message}`);
  if (data !== undefined) {
    console.log(JSON.stringify(data, null, 2));
  }
}

// 测试工具：理解交底书
async function testUnderstandDisclosure(client: Client) {
  log("info", "测试工具: understand_disclosure");

  const testData = {
    content: `一种智能手表，包括显示屏、处理器、电池和传感器，用于监测用户的心率和步数。

详细技术说明：
本发明涉及一种智能可穿戴设备，具体是一种智能手表。

技术背景：
现有的智能手表通常功能单一，用户体验不佳。本发明旨在提供一种功能更完善、用户体验更好的智能手表。

技术方案：
智能手表包括：
1. 显示屏 - 用于显示时间、健康数据等信息
2. 处理器 - 用于处理各种传感器数据和控制设备运行
3. 电池 - 为设备提供电源
4. 传感器 - 包括心率传感器和加速度计，用于监测用户健康数据

有益效果：
本发明的智能手表能够实时监测用户健康数据，提供更好的用户体验。`,
    language: "zh",
  };

  try {
    const result = await client.callTool({
      name: "understand_disclosure",
      arguments: testData,
    });

    log("success", "understand_disclosure 测试通过", result);
    return true;
  } catch (error) {
    log("error", "understand_disclosure 测试失败", error);
    return false;
  }
}

// 测试工具：撰写说明书
async function testDraftSpecification(client: Client) {
  log("info", "测试工具: draft_specification");

  const testData = {
    inventionTitle: "一种智能手表",
    technicalField: "智能可穿戴设备领域",
    backgroundArt: `现有的智能手表通常功能单一，用户体验不佳。具体存在的问题包括：
1. 传感器精度不足，健康数据监测不准确
2. 电池续航时间短，需要频繁充电
3. 用户界面不够友好，操作复杂`,
    summary: `本发明提供一种智能手表，包括显示屏、处理器、电池和传感器，用于监测用户的心率和步数。

本发明解决的技术问题：
- 提高健康数据监测的准确性
- 延长电池续航时间
- 改善用户交互体验`,
    embodiments: [
      {
        title: "实施方式1：整体结构",
        description: `智能手表包括表体1、表带2、显示屏3、处理器4、电池5、心率传感器6和加速度计7。

表体1采用防水设计，内部安装处理器4和电池5。显示屏3安装在表体1正面，心率传感器6安装在表体1背面，与佩戴者皮肤接触。

处理器4采用低功耗芯片，用于接收和处理传感器数据，控制显示屏3显示信息，并管理电池5的供电。`,
      },
      {
        title: "实施方式2：心率监测",
        description: `心率传感器6采用光电容积脉搏波描记法(PPG)技术，包括绿色LED光源和光电二极管。

工作时，绿色LED照射皮肤，血液对绿光的吸收量随脉搏变化，光电二极管检测反射光强度的变化，从而计算出心率数据。

处理器4对采集的原始信号进行滤波处理，去除运动伪影和噪声干扰，提高心率监测的准确性。`,
      },
    ],
    claims: [
      "一种智能手表，包括：表体；显示屏，设置在所述表体正面；处理器，设置在所述表体内；电池，用于为所述智能手表供电；心率传感器，设置在所述表体背面，与所述处理器电连接；和加速度计，设置在所述表体内，与所述处理器电连接。",
      "根据权利要求1所述的智能手表，其特征在于，所述心率传感器包括绿色LED光源和光电二极管，采用光电容积脉搏波描记法检测心率。",
      "根据权利要求1所述的智能手表，其特征在于，所述处理器采用低功耗芯片，用于接收和处理所述心率传感器和所述加速度计的数据。",
    ],
    language: "zh",
  };

  try {
    const result = await client.callTool({
      name: "draft_specification",
      arguments: testData,
    });

    log("success", "draft_specification 测试通过", result);
    return true;
  } catch (error) {
    log("error", "draft_specification 测试失败", error);
    return false;
  }
}

// 测试工具：生成权利要求
async function testGenerateClaims(client: Client) {
  log("info", "测试工具: generate_claims");

  const testData = {
    inventionTitle: "一种智能手表",
    technicalField: "智能可穿戴设备",
    problemSolved: "现有智能手表功能单一，健康监测不准确，续航时间短",
    technicalSolution: `智能手表包括表体、显示屏、处理器、电池、心率传感器和加速度计。

心率传感器采用PPG技术，包括绿色LED光源和光电二极管，通过检测血液对绿光的吸收变化来计算心率。

处理器采用低功耗芯片，对传感器数据进行滤波处理，去除噪声干扰，提高监测准确性。`,
    beneficialEffects:
      "实时监测健康数据，提高监测准确性，延长续航时间，改善用户体验",
    priorArt: [
      "现有智能手表传感器精度不足",
      "电池续航时间短，需要频繁充电",
      "用户界面不够友好，操作复杂",
    ],
    embodiments: [
      "实施方式1：整体结构 - 包括表体、表带、显示屏、处理器、电池、心率传感器和加速度计",
      "实施方式2：心率监测 - 心率传感器采用PPG技术，包括绿色LED光源和光电二极管",
    ],
    claimType: "independent",
    language: "zh",
  };

  try {
    const result = await client.callTool({
      name: "generate_claims",
      arguments: testData,
    });

    log("success", "generate_claims 测试通过", result);
    return true;
  } catch (error) {
    log("error", "generate_claims 测试失败", error);
    return false;
  }
}

// 主测试函数
async function runTests() {
  log("info", "=====================================");
  log("info", "MCP Server 测试脚本启动");
  log("info", `测试时间: ${new Date().toISOString()}`);
  log("info", `服务器路径: ${CONFIG.serverPath}`);
  log("info", "=====================================");

  const results = {
    understandDisclosure: false,
    draftSpecification: false,
    generateClaims: false,
  };

  try {
    // 创建客户端连接
    log("info", "正在连接到 MCP Server...");
    const transport = new StdioClientTransport({
      command: "bun",
      args: [CONFIG.serverPath],
    });

    const client = new Client(
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
    log("success", "成功连接到 MCP Server");

    // 列出可用工具
    log("info", "获取可用工具列表...");
    const toolsResponse = await client.listTools();
    log("info", `发现 ${toolsResponse.tools.length} 个可用工具:`);
    toolsResponse.tools.forEach((tool) => {
      log(
        "info",
        `  - ${tool.name}: ${tool.description?.substring(0, 100)}...`,
      );
    });

    // 运行各项测试
    log("info", "=====================================");
    log("info", "开始运行功能测试");
    log("info", "=====================================");

    results.understandDisclosure = await testUnderstandDisclosure(client);
    results.draftSpecification = await testDraftSpecification(client);
    results.generateClaims = await testGenerateClaims(client);

    // 关闭连接
    log("info", "正在关闭连接...");
    await client.close();
    log("success", "连接已关闭");
  } catch (error) {
    log("error", "测试过程中发生错误", error);
    process.exit(1);
  }

  // 输出测试报告
  log("info", "=====================================");
  log("info", "测试报告");
  log("info", "=====================================");

  const passed = Object.values(results).filter(Boolean).length;
  const total = Object.values(results).length;

  Object.entries(results).forEach(([name, result]) => {
    const status = result ? "✅ 通过" : "❌ 失败";
    log(result ? "success" : "error", `${name}: ${status}`);
  });

  log("info", "-------------------------------------");
  log(
    passed === total ? "success" : "warn",
    `总计: ${passed}/${total} 项测试通过`,
  );

  if (passed !== total) {
    process.exit(1);
  }
}

// 运行测试
runTests().catch((error) => {
  console.error("测试脚本执行失败:", error);
  process.exit(1);
});
