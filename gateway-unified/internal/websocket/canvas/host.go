package canvas

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"sync/atomic"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// CanvasHost Canvas Host服务
// 负责渲染UI界面并实时更新
type CanvasHost struct {
	canvases      map[string]*Canvas
	mu            sync.RWMutex
	ctx           context.Context
	cancel        context.CancelFunc
	counter       uint64 // 原子计数器，用于生成唯一ID
}

// Canvas Canvas实例
type Canvas struct {
	ID            string
	SessionID     string
	Title         string
	HTML          string
	CSS           string
	JS            string
	Data          map[string]interface{}
	CreatedAt     time.Time
	UpdatedAt     time.Time
}

// NewCanvasHost 创建Canvas Host
func NewCanvasHost() *CanvasHost {
	ctx, cancel := context.WithCancel(context.Background())

	return &CanvasHost{
		canvases: make(map[string]*Canvas),
		ctx:      ctx,
		cancel:   cancel,
	}
}

// CreateCanvas 创建新Canvas
func (ch *CanvasHost) CreateCanvas(sessionID, title string) *Canvas {
	// 使用原子计数器生成唯一ID，避免并发冲突
	id := atomic.AddUint64(&ch.counter, 1)
	canvasID := fmt.Sprintf("canvas_%d", id)

	canvas := &Canvas{
		ID:        canvasID,
		SessionID: sessionID,
		Title:     title,
		HTML:      ch.getDefaultHTML(),
		CSS:       ch.getDefaultCSS(),
		JS:        ch.getDefaultJS(),
		Data:      make(map[string]interface{}),
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	ch.mu.Lock()
	ch.canvases[canvasID] = canvas
	ch.mu.Unlock()

	logging.LogInfo("Canvas已创建",
		logging.String("canvas_id", canvasID),
		logging.String("session_id", sessionID),
		logging.String("title", title),
	)

	return canvas
}

// GetCanvas 获取Canvas
func (ch *CanvasHost) GetCanvas(canvasID string) (*Canvas, bool) {
	ch.mu.RLock()
	defer ch.mu.RUnlock()

	canvas, exists := ch.canvases[canvasID]
	return canvas, exists
}

// UpdateCanvas 更新Canvas
func (ch *CanvasHost) UpdateCanvas(canvasID string, updates map[string]interface{}) error {
	ch.mu.Lock()
	defer ch.mu.Unlock()

	canvas, exists := ch.canvases[canvasID]
	if !exists {
		return fmt.Errorf("Canvas不存在: %s", canvasID)
	}

	// 更新字段
	if html, ok := updates["html"].(string); ok {
		canvas.HTML = html
	}
	if css, ok := updates["css"].(string); ok {
		canvas.CSS = css
	}
	if js, ok := updates["js"].(string); ok {
		canvas.JS = js
	}
	if data, ok := updates["data"].(map[string]interface{}); ok {
		canvas.Data = data
	}

	canvas.UpdatedAt = time.Now()

	logging.LogInfo("Canvas已更新",
		logging.String("canvas_id", canvasID),
	)

	return nil
}

// DeleteCanvas 删除Canvas
func (ch *CanvasHost) DeleteCanvas(canvasID string) {
	ch.mu.Lock()
	defer ch.mu.Unlock()

	if _, exists := ch.canvases[canvasID]; exists {
		delete(ch.canvases, canvasID)
		logging.LogInfo("Canvas已删除",
			logging.String("canvas_id", canvasID),
		)
	}
}

// Render 渲染Canvas为HTML
func (ch *CanvasHost) Render(canvasID string) (string, error) {
	ch.mu.RLock()
	canvas, exists := ch.canvases[canvasID]
	ch.mu.RUnlock()

	if !exists {
		return "", fmt.Errorf("Canvas不存在: %s", canvasID)
	}

	// 序列化数据
	dataJSON, _ := json.Marshal(canvas.Data)

	// 渲染完整HTML
	html := fmt.Sprintf(`<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%s</title>
    <style>
%s
    </style>
</head>
<body>
    <div id="app">
%s
    </div>
    <script>
        var canvasData = %s;
%s
    </script>
</body>
</html>`, canvas.Title, canvas.CSS, canvas.HTML, string(dataJSON), canvas.JS)

	return html, nil
}

// GetCanvasesBySession 获取会话的所有Canvas
func (ch *CanvasHost) GetCanvasesBySession(sessionID string) []*Canvas {
	ch.mu.RLock()
	defer ch.mu.RUnlock()

	canvases := make([]*Canvas, 0)
	for _, canvas := range ch.canvases {
		if canvas.SessionID == sessionID {
			canvases = append(canvases, canvas)
		}
	}

	return canvases
}

// Close 关闭Canvas Host
func (ch *CanvasHost) Close() {
	ch.cancel()

	ch.mu.Lock()
	defer ch.mu.Unlock()

	// 清理所有Canvas
	ch.canvases = make(map[string]*Canvas)
}

// === 默认模板 ===

// getDefaultHTML 获取默认HTML
func (ch *CanvasHost) getDefaultHTML() string {
	return `
<div class="loading">
    <div class="spinner"></div>
    <p>加载中...</p>
</div>
<div class="container" style="display: none;">
    <header>
        <h1>Athena工作平台</h1>
    </header>
    <main>
        <div id="content"></div>
        <div id="progress"></div>
        <div id="results"></div>
    </main>
</div>
`
}

// getDefaultCSS 获取默认CSS
func (ch *CanvasHost) getDefaultCSS() string {
	return `
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: #333;
}

.loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    color: white;
}

.spinner {
    width: 50px;
    height: 50px;
    border: 5px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background: rgba(255, 255, 255, 0.95);
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

main {
    background: rgba(255, 255, 255, 0.95);
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

#progress {
    margin: 20px 0;
}

.progress-bar {
    width: 100%;
    height: 30px;
    background: #e0e0e0;
    border-radius: 15px;
    overflow: hidden;
    margin: 10px 0;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    transition: width 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
}

#results {
    margin-top: 20px;
}

.result-card {
    background: #f8f9fa;
    border-left: 4px solid #667eea;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
}
`
}

// getDefaultJS 获取默认JavaScript
func (ch *CanvasHost) getDefaultJS() string {
	return `
// WebSocket连接
let ws = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

// 初始化WebSocket
function initWebSocket() {
    const wsUrl = 'ws://' + window.location.host + '/ws?client_id=' + generateClientID();
    ws = new WebSocket(wsUrl);

    ws.onopen = function() {
        console.log('WebSocket已连接');
        reconnectAttempts = 0;

        // 发送握手消息
        sendHandshake();
    };

    ws.onmessage = function(event) {
        const message = JSON.parse(event.data);
        handleMessage(message);
    };

    ws.onclose = function() {
        console.log('WebSocket已断开');

        // 尝试重连
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            setTimeout(initWebSocket, 3000);
        }
    };

    ws.onerror = function(error) {
        console.error('WebSocket错误:', error);
    };
}

// 发送握手消息
function sendHandshake() {
    const message = {
        id: generateMessageID(),
        type: 'handshake',
        timestamp: Date.now() * 1000000,
        session_id: null,
        data: {
            client_id: generateClientID(),
            auth_token: 'demo_token',
            capabilities: ['canvas', 'task', 'query'],
            user_agent: navigator.userAgent
        }
    };

    ws.send(JSON.stringify(message));
}

// 处理消息
function handleMessage(message) {
    console.log('收到消息:', message);

    switch (message.type) {
        case 'handshake':
            handleHandshake(message);
            break;
        case 'progress':
            handleProgress(message);
            break;
        case 'response':
            handleResponse(message);
            break;
        case 'error':
            handleError(message);
            break;
        default:
            console.log('未知消息类型:', message.type);
    }
}

// 处理握手响应
function handleHandshake(message) {
    console.log('握手成功, session_id:', message.session_id);

    // 隐藏加载动画
    document.querySelector('.loading').style.display = 'none';
    document.querySelector('.container').style.display = 'block';
}

// 处理进度更新
function handleProgress(message) {
    const progress = message.data.progress;
    const status = message.data.status;

    const progressBar = document.querySelector('#progress');
    progressBar.innerHTML =
        '<h3>处理进度</h3>' +
        '<div class="progress-bar">' +
        '   <div class="progress-fill" style="width: ' + progress + '%">' +
        '       ' + progress + '%' +
        '   </div>' +
        '</div>' +
        '<p>' + status + '</p>';
}

// 处理响应
function handleResponse(message) {
    if (message.success) {
        displayResult(message.data.result);
    }
}

// 处理错误
function handleError(message) {
    console.error('错误:', message.data.error_msg);
    alert('错误: ' + message.data.error_msg);
}

// 显示结果
function displayResult(result) {
    const resultsDiv = document.querySelector('#results');
    const resultCard = document.createElement('div');
    resultCard.className = 'result-card';
    resultCard.innerHTML = JSON.stringify(result, null, 2);
    resultsDiv.appendChild(resultCard);
}

// 生成客户端ID
function generateClientID() {
    return 'client_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// 生成消息ID
function generateMessageID() {
    return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// 发送任务请求
function sendTask(taskType, targetAgent, parameters) {
    const message = {
        id: generateMessageID(),
        type: 'task',
        timestamp: Date.now() * 1000000,
        session_id: canvasData.session_id || null,
        data: {
            task_type: taskType,
            target_agent: targetAgent,
            priority: 5,
            parameters: parameters
        }
    };

    ws.send(JSON.stringify(message));
}

// 页面加载完成后初始化
window.addEventListener('load', function() {
    initWebSocket();
});
`
}
