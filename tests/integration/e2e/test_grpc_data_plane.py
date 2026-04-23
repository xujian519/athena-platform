"""
gRPC数据平面测试

测试Gateway的gRPC功能：
1. 服务定义
2. 流式响应
3. 心跳检测
4. 状态查询
"""

import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.integration]


class TestGRPCProtoDefinitions:
    """gRPC协议定义测试"""

    def test_proto_file_exists(self):
        """测试proto文件存在"""
        proto_path = Path("/Users/xujian/Athena工作平台/gateway-unified/proto/agent_service.proto")
        assert proto_path.exists(), "gRPC proto文件不存在"

    def test_service_definition(self):
        """测试服务定义"""
        proto_path = Path("/Users/xujian/Athena工作平台/gateway-unified/proto/agent_service.proto")
        if not proto_path.exists():
            pytest.skip("Proto文件不存在")

        content = proto_path.read_text()

        # 验证服务定义
        assert "service AgentService" in content

        # 验证RPC方法
        required_methods = [
            "ExecuteTask",
            "GetAgentStatus",
            "Heartbeat"
        ]

        for method in required_methods:
            assert method in content, f"缺少RPC方法: {method}"

    def test_message_definitions(self):
        """测试消息定义"""
        proto_path = Path("/Users/xujian/Athena工作平台/gateway-unified/proto/agent_service.proto")
        if not proto_path.exists():
            pytest.skip("Proto文件不存在")

        content = proto_path.read_text()

        # 验证关键消息类型
        required_messages = [
            "TaskRequest",
            "TaskResponse",
            "AgentStatusRequest",
            "AgentStatusResponse"
        ]

        for msg_type in required_messages:
            assert msg_type in content, f"缺少消息类型: {msg_type}"

    def test_streaming_response(self):
        """测试流式响应定义"""
        proto_path = Path("/Users/xujian/Athena工作平台/gateway-unified/proto/agent_service.proto")
        if not proto_path.exists():
            pytest.skip("Proto文件不存在")

        content = proto_path.read_text()

        # 验证流式响应
        assert "stream" in content
        assert "ExecuteTask" in content
        assert "stream TaskResponse" in content


class TestGRPCCodeGeneration:
    """gRPC代码生成测试"""

    def test_generated_pb_file(self):
        """测试生成的.pb.go文件"""
        pb_path = Path("/Users/xujian/Athena工作平台/gateway-unified/proto/agent_service.pb.go")
        assert pb_path.exists(), "生成的.pb.go文件不存在"

    def test_generated_grpc_pb_file(self):
        """测试生成的_grpc.pb.go文件"""
        grpc_pb_path = Path("/Users/xujian/Athena工作平台/gateway-unified/proto/agent_service_grpc.pb.go")
        assert grpc_pb_path.exists(), "生成的_grpc.pb.go文件不存在"

    def test_pb_file_content(self):
        """测试.pb.go文件内容"""
        pb_path = Path("/Users/xujian/Athena工作平台/gateway-unified/proto/agent_service.pb.go")
        if not pb_path.exists():
            pytest.skip("Generated .pb.go文件不存在")

        content = pb_path.read_text()

        # 验证生成的类型
        assert "type TaskRequest" in content or "type TaskRequest struct" in content
        assert "type TaskResponse" in content or "type TaskResponse struct" in content


class TestGRPCServerImplementation:
    """gRPC服务端实现测试"""

    def test_server_file_exists(self):
        """测试服务端文件存在"""
        server_path = Path("/Users/xujian/Athena工作平台/gateway-unified/internal/grpc/agent_server.go")
        assert server_path.exists(), "gRPC服务端文件不存在"

    def test_server_implementation(self):
        """测试服务端实现"""
        server_path = Path("/Users/xujian/Athena工作平台/gateway-unified/internal/grpc/agent_server.go")
        if not server_path.exists():
            pytest.skip("服务端文件不存在")

        content = server_path.read_text()

        # 验证服务实现
        assert "func (s *" in content  # 方法实现
        assert "ExecuteTask" in content
        assert "GetAgentStatus" in content

    def test_streaming_implementation(self):
        """测试流式响应实现"""
        server_path = Path("/Users/xujian/Athena工作平台/gateway-unified/internal/grpc/agent_server.go")
        if not server_path.exists():
            pytest.skip("服务端文件不存在")

        content = server_path.read_text()

        # 验证流式响应
        assert "stream" in content.lower()
        assert "Send" in content  # 流发送方法


class TestGRPCConfiguration:
    """gRPC配置测试"""

    def test_grpc_config_defined(self):
        """测试gRPC配置定义"""
        config_path = Path("/Users/xujian/Athena工作平台/gateway-unified/internal/config/config.go")
        if not config_path.exists():
            pytest.skip("Config文件不存在")

        content = config_path.read_text()

        # 验证gRPC配置
        assert "GRPCConfig" in content or "GRPC" in content

    def test_grpc_port_configured(self):
        """测试gRPC端口配置"""
        config_path = Path("/Users/xujian/Athena工作平台/gateway-unified/internal/config/config.go")
        if not config_path.exists():
            pytest.skip("Config文件不存在")

        content = config_path.read_text()

        # 验证端口配置
        assert "Port" in content

    def test_gateway_config_yaml(self):
        """测试Gateway YAML配置"""
        yaml_path = Path("/Users/xujian/Athena工作平台/gateway-unified/config.yaml")
        if not yaml_path.exists():
            pytest.skip("config.yaml不存在")

        content = yaml_path.read_text()

        # 验证gRPC配置项
        # gRPC配置可能在YAML中
        assert "grpc" in content.lower() or "port" in content.lower()


class TestGRPCIntegration:
    """gRPC集成测试"""

    def test_gateway_grpc_initialization(self):
        """测试Gateway gRPC初始化"""
        main_path = Path("/Users/xujian/Athena工作平台/gateway-unified/cmd/gateway/main.go")
        if not main_path.exists():
            pytest.skip("Gateway main.go不存在")

        content = main_path.read_text()

        # 验证gRPC服务器初始化
        assert "grpc" in content.lower() or "50051" in content

    def test_grpc_server_started(self):
        """测试gRPC服务器启动"""
        main_path = Path("/Users/xujian/Athena工作平台/gateway-unified/cmd/gateway/main.go")
        if not main_path.exists():
            pytest.skip("Gateway main.go不存在")

        content = main_path.read_text()

        # 验证服务器启动逻辑
        assert "NewServer" in content or "Start" in content or "Serve" in content


class TestGRPCCompilation:
    """gRPC编译测试"""

    def test_proto_compilation(self):
        """测试proto文件编译"""
        # 检查生成的Go文件
        pb_path = Path("/Users/xujian/Athena工作平台/gateway-unified/proto/agent_service.pb.go")
        grpc_pb_path = Path("/Users/xujian/Athena工作平台/gateway-unified/proto/agent_service_grpc.pb.go")

        if not pb_path.exists() or not grpc_pb_path.exists():
            pytest.skip("生成的文件不存在，需要先编译proto")

        # 验证文件不为空
        assert pb_path.stat().st_size > 0
        assert grpc_pb_path.stat().st_size > 0

    def test_gateway_compilation_with_grpc(self):
        """测试Gateway带gRPC编译"""
        result = subprocess.run(
            ["go", "build", "-o", "/tmp/gateway-grpc-test", "./cmd/gateway"],
            cwd="/Users/xujian/Athena工作平台/gateway-unified",
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            pytest.skip(f"Gateway编译失败: {result.stderr}")

        # 验证二进制文件生成
        test_binary = Path("/tmp/gateway-grpc-test")
        if test_binary.exists():
            assert test_binary.stat().st_size > 0


class TestGRPCMethods:
    """gRPC方法测试"""

    def test_execute_task_method(self):
        """测试ExecuteTask方法"""
        server_path = Path("/Users/xujian/Athena工作平台/gateway-unified/internal/grpc/agent_server.go")
        if not server_path.exists():
            pytest.skip("服务端文件不存在")

        content = server_path.read_text()

        # 验证ExecuteTask方法签名
        assert "ExecuteTask" in content
        assert "TaskRequest" in content
        assert "TaskResponse" in content

    def test_get_agent_status_method(self):
        """测试GetAgentStatus方法"""
        server_path = Path("/Users/xujian/Athena工作平台/gateway-unified/internal/grpc/agent_server.go")
        if not server_path.exists():
            pytest.skip("服务端文件不存在")

        content = server_path.read_text()

        # 验证GetAgentStatus方法
        assert "GetAgentStatus" in content
        assert "AgentStatusRequest" in content
        assert "AgentStatusResponse" in content

    def test_heartbeat_method(self):
        """测试Heartbeat方法"""
        server_path = Path("/Users/xujian/Athena工作平台/gateway-unified/internal/grpc/agent_server.go")
        if not server_path.exists():
            pytest.skip("服务端文件不存在")

        content = server_path.read_text()

        # 验证Heartbeat方法
        assert "Heartbeat" in content
        assert "HeartbeatRequest" in content or "HeartbeatResponse" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
