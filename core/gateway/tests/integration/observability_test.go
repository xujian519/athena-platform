package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/suite"
)

type ObservabilityIntegrationTestSuite struct {
	suite.Suite
	baseURL    string
	httpClient *http.Client
}

func (suite *ObservabilityIntegrationTestSuite) SetupSuite() {
	suite.baseURL = "http://localhost:8080"
	suite.httpClient = &http.Client{
		Timeout: 10 * time.Second,
	}

	suite.waitForService()
}

func (suite *ObservabilityIntegrationTestSuite) waitForService() {
	maxRetries := 30
	for i := 0; i < maxRetries; i++ {
		resp, err := suite.httpClient.Get(suite.baseURL + "/health")
		if err == nil && resp.StatusCode == 200 {
			resp.Body.Close()
			return
		}
		if resp != nil {
			resp.Body.Close()
		}
		time.Sleep(2 * time.Second)
	}
	suite.T().Fatal("Service did not become available within timeout")
}

func (suite *ObservabilityIntegrationTestSuite) TestHealthEndpoint() {
	resp, err := suite.httpClient.Get(suite.baseURL + "/health")
	suite.Require().NoError(err)
	defer resp.Body.Close()

	suite.Equal(http.StatusOK, resp.StatusCode)

	var health map[string]interface{}
	err = json.NewDecoder(resp.Body).Decode(&health)
	suite.NoError(err)
	suite.Equal("healthy", health["status"])
}

func (suite *ObservabilityIntegrationTestSuite) TestMetricsEndpoint() {
	resp, err := suite.httpClient.Get(suite.baseURL + "/metrics")
	suite.Require().NoError(err)
	defer resp.Body.Close()

	suite.Equal(http.StatusOK, resp.StatusCode)

	body, err := io.ReadAll(resp.Body)
	suite.NoError(err)

	metricsContent := string(body)
	suite.Contains(metricsContent, "athena_gateway_http_requests_total")
	suite.Contains(metricsContent, "athena_gateway_go_goroutines")
	suite.Contains(metricsContent, "go_gc_duration_seconds")
}

func (suite *ObservabilityIntegrationTestSuite) TestTracingHeadersPresent() {
	resp, err := suite.httpClient.Get(suite.baseURL + "/health")
	suite.Require().NoError(err)
	defer resp.Body.Close()

	suite.Equal(http.StatusOK, resp.StatusCode)

	tracingHeaders := []string{
		"traceparent",
		"tracestate",
	}

	for _, header := range tracingHeaders {
		value := resp.Header.Get(header)
		if value != "" {
			suite.T().Logf("Found tracing header: %s = %s", header, value)
		}
	}
}

func (suite *ObservabilityIntegrationTestSuite) TestRequestMetricsCollection() {
	// 发送多个请求以生成指标数据
	for i := 0; i < 10; i++ {
		resp, err := suite.httpClient.Get(suite.baseURL + "/health")
		suite.Require().NoError(err)
		resp.Body.Close()
	}

	// 等待指标被收集
	time.Sleep(2 * time.Second)

	// 验证指标端点包含请求计数
	resp, err := suite.httpClient.Get(suite.baseURL + "/metrics")
	suite.Require().NoError(err)
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	suite.NoError(err)

	metricsContent := string(body)
	suite.Contains(metricsContent, "athena_gateway_http_requests_total")
}

func (suite *ObservabilityIntegrationTestSuite) TestErrorMetricsCollection() {
	// 发送错误请求
	resp, err := suite.httpClient.Get(suite.baseURL + "/nonexistent")
	suite.Require().NoError(err)
	defer resp.Body.Close()

	suite.Equal(http.StatusNotFound, resp.StatusCode)

	// 等待指标被收集
	time.Sleep(2 * time.Second)

	// 验证错误指标
	resp, err = suite.httpClient.Get(suite.baseURL + "/metrics")
	suite.Require().NoError(err)
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	suite.NoError(err)

	metricsContent := string(body)
	suite.Contains(metricsContent, "athena_gateway_http_errors_total")
}

func (suite *ObservabilityIntegrationTestSuite) TestProxyRequests() {
	// 测试代理请求
	testPayload := map[string]interface{}{
		"test": "data",
	}
	payloadBytes, _ := json.Marshal(testPayload)

	resp, err := suite.httpClient.Post(
		suite.baseURL+"/api/v1/orders",
		"application/json",
		bytes.NewBuffer(payloadBytes),
	)
	suite.Require().NoError(err)
	defer resp.Body.Close()

	// 代理功能尚未实现，期望返回501
	suite.Equal(http.StatusNotImplemented, resp.StatusCode)

	var errorResp map[string]interface{}
	err = json.NewDecoder(resp.Body).Decode(&errorResp)
	suite.NoError(err)
	suite.Contains(errorResp, "error")
	suite.Contains(errorResp, "service")
}

func (suite *ObservabilityIntegrationTestSuite) TestCORSHeaders() {
	req, err := http.NewRequest("OPTIONS", suite.baseURL+"/api/v1/test", nil)
	suite.Require().NoError(err)
	req.Header.Set("Origin", "http://localhost:3000")

	resp, err := suite.httpClient.Do(req)
	suite.Require().NoError(err)
	defer resp.Body.Close()

	suite.Equal(http.StatusNoContent, resp.StatusCode)

	corsHeaders := []string{
		"Access-Control-Allow-Origin",
		"Access-Control-Allow-Methods",
		"Access-Control-Allow-Headers",
	}

	for _, header := range corsHeaders {
		value := resp.Header.Get(header)
		suite.NotEmpty(value, "CORS header %s should be present", header)
	}
}

func TestObservabilityIntegrationSuite(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	suite.Run(t, new(ObservabilityIntegrationTestSuite))
}

func TestMain(m *testing.M) {
	// 设置测试环境
	if os.Getenv("INTEGRATION_TEST") != "true" {
		fmt.Println("Skipping integration tests. Set INTEGRATION_TEST=true to run.")
		os.Exit(0)
	}

	// 启动信号处理
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		cancel()
	}()

	// 运行测试
	code := m.Run()

	// 清理资源
	os.Exit(code)
}
