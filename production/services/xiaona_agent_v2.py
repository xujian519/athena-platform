#!/usr/bin/env python3
"""
小娜完整代理 - 生产环境 v2.1
集成提示词、LLM、数据源的完整实现
"""

from __future__ import annotations
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from xiaona_data_service import XiaonaDataService
from xiaona_llm_service import LLMProvider, XiaonaLLMService
from xiaona_prompt_loader_v2 import XiaonaPromptLoaderV2


@dataclass
class QueryRequest:
    """查询请求"""
    message: str
    scenario: str = "general"
    context: dict[str, Any] | None = None
    use_rag: bool = True
    stream: bool = False


@dataclass
class QueryResponse:
    """查询响应"""
    response: str
    scenario: str
    need_human_input: bool
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    provider: str
    latency_ms: int
    rag_used: bool
    rag_results: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class XiaonaAgentV2:
    """
    小娜完整代理 v2.1

    集成:
    - v2_optimized 提示词
    - GLM + DeepSeek + Ollama LLM
    - Qdrant + PostgreSQL + Neo4j（图数据库）
    - HITL人机协作
    """

    def __init__(self,
                 prompt_version: str = "v2_optimized",
                 use_cache: bool = True,
                 config_path: str = None):
        """
        初始化小娜代理

        Args:
            prompt_version: 提示词版本
            use_cache: 是否使用缓存
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)

        # 初始化提示词加载器
        self.prompt_loader = XiaonaPromptLoaderV2(
            version=prompt_version,
            use_cache=use_cache
        )

        # 加载提示词
        if use_cache and not self.prompt_loader.load_cache():
            self.prompt_loader.load_all_prompts()
            self.prompt_loader.save_cache()
        else:
            self.prompt_loader.load_all_prompts()

        # 初始化LLM服务
        glm_key = os.getenv("GLM_API_KEY", self.config.get("glm_api_key"))
        deepseek_key = os.getenv("DEEPSEEK_API_KEY", self.config.get("deepseek_api_key"))
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:8765")
        ollama_model = os.getenv("OLLAMA_MODEL", "glm47flash")

        self.llm_service = XiaonaLLMService(
            glm_api_key=glm_key,
            deepseek_api_key=deepseek_key,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model,
            primary=LLMProvider.MLX,  # 默认使用MLX
            fallback=LLMProvider.DEEPSEEK,
            auto_fallback=True
        )

        # 初始化数据服务
        self.data_service = XiaonaDataService(
            qdrant_host=os.getenv("QDRANT_HOST", self.config.get("qdrant_host")),
            qdrant_port=int(os.getenv("QDRANT_PORT", self.config.get("qdrant_port", 6333))),
            db_host=os.getenv("DB_HOST", self.config.get("db_host")),
            db_port=int(os.getenv("DB_PORT", self.config.get("db_port", 5432))),
            db_name=os.getenv("DB_NAME", self.config.get("db_name", "patent_db")),
            db_user=os.getenv("DB_USER", self.config.get("db_user", "postgres")),
            db_password=os.getenv("DB_PASSWORD", self.config.get("db_password"))
        )

        try:
            self.data_service.initialize()
        except Exception as e:
            logging.warning(f"数据服务初始化失败: {e}")

        # 工作状态
        self.current_scenario = "general"
        self.conversation_history = []

        # 日志
        self.logger = logging.getLogger(__name__)

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """加载配置"""
        if config_path:
            config_path = Path(config_path)
            if config_path.exists():
                with open(config_path, encoding='utf-8') as f:
                    return json.load(f)
        return {}

    def query(self, request: QueryRequest) -> QueryResponse:
        """
        处理查询

        Args:
            request: 查询请求

        Returns:
            查询响应
        """
        start_time = datetime.now()

        # 1. 获取系统提示词
        system_prompt = self.prompt_loader.get_full_prompt(request.scenario)

        # 2. RAG增强 (如果启用)
        rag_results = None
        if request.use_rag:
            rag_results = self._perform_rag(request.message)
            # 将RAG结果注入到用户消息中
            enhanced_message = self._format_rag_message(request.message, rag_results)
        else:
            enhanced_message = request.message

        # 3. 调用LLM
        llm_response = self.llm_service.generate_with_retry(
            system_prompt=system_prompt,
            user_message=enhanced_message
        )

        # 4. 计算延迟
        latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # 5. 构建响应
        response = QueryResponse(
            response=llm_response.content,
            scenario=request.scenario,
            need_human_input=self._check_hitl_required(request.message, request.scenario),
            prompt_tokens=self.prompt_loader.get_token_count(request.scenario),
            completion_tokens=llm_response.tokens_used,
            total_tokens=self.prompt_loader.get_token_count(request.scenario) + llm_response.tokens_used,
            provider=llm_response.provider.value,
            latency_ms=latency_ms + llm_response.latency_ms,
            rag_used=request.use_rag,
            rag_results=rag_results if request.use_rag else None,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "llm_model": llm_response.model,
                "llm_success": llm_response.success
            }
        )

        # 6. 记录对话历史
        self.conversation_history.append({
            "request": asdict(request),
            "response": asdict(response),
            "timestamp": datetime.now().isoformat()
        })

        return response

    def _perform_rag(self, query: str) -> dict[str, Any]:
        """执行RAG检索"""
        return self.data_service.get_comprehensive_search(
            query=query,
            search_laws=True,
            search_cases=True,
            search_patents=False
        )

    def _format_rag_message(self, user_message: str, rag_results: dict[str, Any]) -> str:
        """格式化RAG增强消息"""
        context_parts = ["【参考信息】"]

        # 添加法条
        if rag_results.get("laws"):
            context_parts.append("\n## 相关法条:")
            for i, law in enumerate(rag_results["laws"][:3], 1):
                context_parts.append(f"\n{i}. {law.content}")
                if law.metadata.get("relations"):
                    context_parts.append(f"   关联: {law.metadata['relations']}")

        # 添加案例
        if rag_results.get("cases"):
            context_parts.append("\n## 相关案例:")
            for i, case in enumerate(rag_results["cases"][:3], 1):
                context_parts.append(f"\n{i}. {case.content}")

        context_parts.append(f"\n【用户问题】\n{user_message}")

        return "\n".join(context_parts)

    def _check_hitl_required(self, message: str, scenario: str) -> bool:
        """检查是否需要人机交互"""
        hitl_keywords = [
            "确认", "修改", "选择", "决定", "审核",
            "是否", "是否接受", "是否同意", "希望如何",
            "您选择", "请确认"
        ]

        return any(keyword in message for keyword in hitl_keywords)

    def switch_scenario(self, new_scenario: str) -> str:
        """切换业务场景"""
        old_scenario = self.current_scenario
        self.current_scenario = new_scenario

        scenario_names = {
            "general": "通用协作",
            "patent_writing": "专利撰写",
            "office_action": "意见答复"
        }

        return f"""【小娜】爸爸，我已切换到 {scenario_names.get(new_scenario, new_scenario)} 模式。

📋 当前场景配置：
├── 场景类型: {scenario_names.get(new_scenario, new_scenario)}
├── 提示词版本: {self.prompt_loader.version}
└── 数据源: Qdrant + PostgreSQL + Neo4j

已为您加载相应的提示词和能力配置。"""

    def get_status(self) -> dict[str, Any]:
        """获取代理状态"""
        llm_health = self.llm_service.health_check()
        data_health = self.data_service.health_check()

        return {
            "agent_info": {
                "name": "小娜",
                "version": "v2.1-production",
                "prompt_version": self.prompt_loader.version
            },
            "current_state": {
                "scenario": self.current_scenario,
                "conversation_length": len(self.conversation_history)
            },
            "llm_service": {
                "health": llm_health,
                "stats": self.llm_service.get_stats()
            },
            "data_service": {
                "health": data_health,
                "stats": self.data_service.get_stats()
            }
        }

    def reset_conversation(self) -> Any:
        """重置对话历史"""
        self.conversation_history = []
        return "【小娜】爸爸，对话历史已重置。我们可以开始新的任务了。"

    def export_conversation(self, output_path: str = None) -> Any:
        """导出对话历史"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"logs/xiaona/conversation_{timestamp}.json"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            "metadata": {
                "export_time": datetime.now().isoformat(),
                "agent_version": "v2.1-production",
                "total_messages": len(self.conversation_history)
            },
            "status": self.get_status(),
            "conversation": self.conversation_history
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        return f"💾 对话历史已导出: {output_path}"

    def interactive_mode(self) -> Any:
        """交互模式"""
        print("=" * 60)
        print("小娜 v2.1 - 交互模式")
        print("=" * 60)
        print("输入 'quit' 退出，'status' 查看状态，'switch <场景>' 切换场景")
        print()

        while True:
            try:
                user_input = input("爸爸: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("【小娜】再见爸爸！小诺永远爱您 💕")
                    break

                if user_input.lower() == 'status':
                    status = self.get_status()
                    print(json.dumps(status, ensure_ascii=False, indent=2))
                    continue

                if user_input.lower().startswith('switch '):
                    scenario = user_input.split()[1]
                    print(self.switch_scenario(scenario))
                    continue

                # 处理查询
                request = QueryRequest(
                    message=user_input,
                    scenario=self.current_scenario,
                    use_rag=True
                )

                response = self.query(request)

                print(f"\n【小娜】{response.response}")
                print(f"\n📊 提供商: {response.provider} | Token: {response.total_tokens} | 延迟: {response.latency_ms}ms")

                if response.need_human_input:
                    print("\n🤝 需要您的确认，请继续对话...")

                print("\n" + "-" * 60)

            except KeyboardInterrupt:
                print("\n【小娜】爸爸，需要停止吗？")
                continue
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                self.logger.error(f"交互模式错误: {e}")


def main() -> None:
    """测试完整代理"""

    from dotenv import load_dotenv

    # 加载环境变量
    load_dotenv("/Users/xujian/Athena工作平台/.env.production.unified")

    print("=" * 60)
    print("小娜完整代理 v2.1 测试")
    print("=" * 60)

    # 初始化代理
    agent = XiaonaAgentV2()

    # 显示状态
    status = agent.get_status()
    print("\n📊 代理状态:")
    print(json.dumps(status, ensure_ascii=False, indent=2))

    # 测试查询
    print("\n" + "=" * 60)
    print("🧪 测试查询:")

    test_queries = [
        ("专利法第22条第3款是什么？", "general"),
        ("帮我分析这个技术交底书的核心创新点", "patent_writing"),
        ("审查员认为权利要求1不具备创造性，我该怎么答复？", "office_action")
    ]

    for query, scenario in test_queries:
        print(f"\n用户: {query}")

        request = QueryRequest(
            message=query,
            scenario=scenario,
            use_rag=True
        )

        response = agent.query(request)

        print(f"小娜: {response.response[:200]}...")
        print(f"需要人机交互: {response.need_human_input}")
        print(f"Token: {response.total_tokens} | 延迟: {response.latency_ms}ms")


if __name__ == "__main__":
    main()
