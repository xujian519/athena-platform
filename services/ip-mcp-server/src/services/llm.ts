/**
 * LLM服务模块
 * 使用 OpenAI 兼容 API 连接 MLX 推理服务 (端口 8765)
 *
 * 从 Ollama 迁移到 MLX，使用标准 fetch + OpenAI Chat Completions API
 */

import type { LLMOptions, LLMResponse } from "../types/index.js";
import logger from "../utils/logger.js";

const DEFAULT_MODEL = process.env.MLX_MODEL || "glm47flash";
const MLX_BASE_URL = process.env.MLX_BASE_URL || "http://127.0.0.1:8765";

/**
 * 调用LLM生成响应（OpenAI Chat Completions API）
 */
export async function generateCompletion(
  prompt: string,
  options: LLMOptions = {},
): Promise<LLMResponse> {
  const model = options.model || DEFAULT_MODEL;
  const temperature = options.temperature ?? 0.7;
  const maxTokens = options.maxTokens ?? 2048;

  logger.info("Calling MLX LLM", { model, temperature, maxTokens });

  try {
    const messages = [];
    if (options.systemPrompt) {
      messages.push({ role: "system", content: options.systemPrompt });
    }
    messages.push({ role: "user", content: prompt });

    const response = await fetch(`${MLX_BASE_URL}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        messages,
        temperature,
        max_tokens: maxTokens,
        stream: false,
      }),
    });

    if (!response.ok) {
      throw new Error(`MLX API error: ${response.status} ${await response.text()}`);
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || "";

    logger.info("MLX LLM response received", { model });

    return {
      text: content,
      model,
      finishReason: "stop",
    };
  } catch (error) {
    logger.error("MLX LLM call failed", { error });
    throw new Error(
      `LLM调用失败: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

/**
 * 生成结构化JSON响应
 */
export async function generateJSON<T>(
  prompt: string,
  options: LLMOptions = {},
): Promise<T> {
  const jsonPrompt = `${prompt}\n\n请以有效的JSON格式返回结果，不要包含任何其他文本。`;

  const response = await generateCompletion(jsonPrompt, {
    ...options,
    temperature: options.temperature ?? 0.3,
  });

  try {
    const jsonMatch = response.text.match(/\{[\s\S]*\}|\[[\s\S]*\]/);
    if (!jsonMatch) {
      throw new Error("未找到JSON内容");
    }
    return JSON.parse(jsonMatch[0]) as T;
  } catch (error) {
    logger.error("Failed to parse JSON response", {
      error,
      responseText: response.text,
    });
    throw new Error(
      `JSON解析失败: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

/**
 * 流式生成响应（OpenAI Chat Completions stream）
 */
export async function* streamCompletion(
  prompt: string,
  options: LLMOptions = {},
): AsyncGenerator<string> {
  const model = options.model || DEFAULT_MODEL;

  logger.info("Starting MLX LLM stream", { model });

  try {
    const messages = [];
    if (options.systemPrompt) {
      messages.push({ role: "system", content: options.systemPrompt });
    }
    messages.push({ role: "user", content: prompt });

    const response = await fetch(`${MLX_BASE_URL}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        messages,
        temperature: options.temperature ?? 0.7,
        max_tokens: options.maxTokens ?? 2048,
        stream: true,
      }),
    });

    if (!response.ok) {
      throw new Error(`MLX API error: ${response.status} ${await response.text()}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n").filter((line) => line.startsWith("data: "));

      for (const line of lines) {
        const data = line.slice(6).trim();
        if (data === "[DONE]") continue;

        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices?.[0]?.delta?.content || "";
          if (content) yield content;
        } catch {
          // 忽略不完整的 JSON 片段
        }
      }
    }

    logger.info("MLX LLM stream completed", { model });
  } catch (error) {
    logger.error("MLX LLM stream failed", { error });
    throw new Error(
      `LLM流式调用失败: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

export default {
  generateCompletion,
  generateJSON,
  streamCompletion,
};
