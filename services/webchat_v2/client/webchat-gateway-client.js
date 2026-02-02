/**
 * WebChat V2 Gateway JavaScript客户端SDK
 * 用于前端应用与WebSocket Gateway通信
 *
 * 作者: Athena平台团队
 * 创建时间: 2025-01-31
 * 版本: 2.0.0
 *
 * 使用示例:
 * ```javascript
 * const client = new WebChatGatewayClient({
 *   url: 'ws://localhost:8000/gateway/ws',
 *   userId: 'user123',
 *   sessionId: 'session456'
 * });
 *
 * await client.connect();
 * const result = await client.call('platform_modules', {});
 * await client.disconnect();
 * ```
 */

class WebChatGatewayClient {
  /**
   * 构造函数
   * @param {Object} config - 配置对象
   * @param {string} config.url - WebSocket服务器地址
   * @param {string} config.userId - 用户ID
   * @param {string} [config.sessionId] - 会话ID（可选，自动生成）
   * @param {string} [config.token] - JWT认证token（可选）
   * @param {number} [config.timeout=10000] - 请求超时时间（毫秒）
   * @param {boolean} [config.autoReconnect=true] - 是否自动重连
   * @param {number} [config.reconnectInterval=3000] - 重连间隔（毫秒）
   * @param {Function} [config.onConnected] - 连接成功回调
   * @param {Function} [config.onDisconnected] - 断开连接回调
   * @param {Function} [config.onError] - 错误回调
   * @param {Function} [config.onEvent] - 事件回调
   */
  constructor(config = {}) {
    this.url = config.url || 'ws://localhost:8000/gateway/ws';
    this.userId = config.userId || 'guest';
    this.sessionId = config.sessionId || this._generateSessionId();
    this.token = config.token || null;
    this.timeout = config.timeout || 10000;
    this.autoReconnect = config.autoReconnect !== false;
    this.reconnectInterval = config.reconnectInterval || 3000;

    // 回调函数
    this.onConnected = config.onConnected || null;
    this.onDisconnected = config.onDisconnected || null;
    this.onError = config.onError || null;
    this.onEvent = config.onEvent || null;

    // 内部状态
    this.ws = null;
    this.connected = false;
    this.requestId = 0;
    this.pendingRequests = new Map();
    this.reconnectTimer = null;
    this.heartbeatTimer = null;
  }

  /**
   * 生成会话ID
   * @private
   */
  _generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  /**
   * 生成请求ID
   * @private
   */
  _generateRequestId() {
    this.requestId++;
    return `req_${this.requestId}`;
  }

  /**
   * 构建WebSocket URL
   * @private
   */
  _buildUrl() {
    let url = `${this.url}?user_id=${encodeURIComponent(this.userId)}&session_id=${encodeURIComponent(this.sessionId)}`;
    if (this.token) {
      url += `&token=${encodeURIComponent(this.token)}`;
    }
    return url;
  }

  /**
   * 连接到WebSocket服务器
   * @returns {Promise<void>}
   */
  async connect() {
    return new Promise((resolve, reject) => {
      try {
        const url = this._buildUrl();
        console.log(`[WebChatGateway] 连接到: ${this.url}`);

        this.ws = new WebSocket(url);

        // 连接打开
        this.ws.onopen = () => {
          console.log('[WebChatGateway] WebSocket连接已建立');
          this.connected = true;
          this._startHeartbeat();
          if (this.onConnected) this.onConnected();
          resolve();
        };

        // 接收消息
        this.ws.onmessage = (event) => {
          this._handleMessage(event.data);
        };

        // 连接关闭
        this.ws.onclose = (event) => {
          console.log(`[WebChatGateway] WebSocket连接已关闭: code=${event.code}`);
          this.connected = false;
          this._cleanup();

          if (this.onDisconnected) this.onDisconnected(event);

          // 自动重连
          if (this.autoReconnect && !event.wasClean) {
            this._scheduleReconnect();
          }
        };

        // 连接错误
        this.ws.onerror = (error) => {
          console.error('[WebChatGateway] WebSocket错误:', error);
          if (this.onError) this.onError(error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.autoReconnect = false; // 禁用自动重连
    if (this.ws) {
      this.ws.close(1000, '客户端主动断开');
    }
    this._cleanup();
  }

  /**
   * 清理资源
   * @private
   */
  _cleanup() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    // 拒绝所有待处理的请求
    this.pendingRequests.forEach((resolver, requestId) => {
      resolver.reject(new Error('连接已关闭'));
    });
    this.pendingRequests.clear();
  }

  /**
   * 安排重连
   * @private
   */
  _scheduleReconnect() {
    if (this.reconnectTimer) return;

    console.log(`[WebChatGateway] ${this.reconnectInterval}ms后重连...`);
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect().catch(error => {
        console.error('[WebChatGateway] 重连失败:', error);
      });
    }, this.reconnectInterval);
  }

  /**
   * 处理接收到的消息
   * @private
   */
  _handleMessage(data) {
    try {
      const message = JSON.parse(data);

      // 响应消息
      if (message.type === 'response') {
        const pending = this.pendingRequests.get(message.id);
        if (pending) {
          this.pendingRequests.delete(message.id);
          pending.resolve(message);
        }
      }
      // 事件消息
      else if (message.type === 'event') {
        console.log(`[WebChatGateway] 收到事件: ${message.event}`);
        if (this.onEvent) this.onEvent(message);
      }
    } catch (error) {
      console.error('[WebChatGateway] 消息解析错误:', error);
    }
  }

  /**
   * 启动心跳检测
   * @private
   */
  _startHeartbeat() {
    // 检查连接状态
    this.heartbeatTimer = setInterval(() => {
      if (!this.connected || this.ws.readyState !== WebSocket.OPEN) {
        console.warn('[WebChatGateway] 检测到连接断开');
        this.ws.close();
      }
    }, 35000); // 35秒检查一次（服务器心跳间隔30秒）
  }

  /**
   * 发送请求并等待响应
   * @param {string} method - 方法名
   * @param {Object} params - 参数
   * @returns {Promise<Object>} 响应结果
   */
  async call(method, params = {}) {
    if (!this.connected || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('未连接到服务器');
    }

    const requestId = this._generateRequestId();
    const request = {
      type: 'request',
      id: requestId,
      method: method,
      params: params,
      timestamp: new Date().toISOString()
    };

    console.log(`[WebChatGateway] 发送请求: ${method}`);

    // 创建超时Promise
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('请求超时')), this.timeout);
    });

    // 创建响应Promise
    const responsePromise = new Promise((resolve, reject) => {
      this.pendingRequests.set(requestId, { resolve, reject });
    });

    // 发送请求
    try {
      this.ws.send(JSON.stringify(request));
    } catch (error) {
      this.pendingRequests.delete(requestId);
      throw error;
    }

    // 等待响应或超时
    try {
      const response = await Promise.race([responsePromise, timeoutPromise]);
      if (response.error) {
        throw new Error(response.error);
      }
      return response.result;
    } catch (error) {
      this.pendingRequests.delete(requestId);
      throw error;
    }
  }

  /**
   * 获取平台模块列表
   * @returns {Promise<Array>} 模块列表
   */
  async getModules() {
    const result = await this.call('platform_modules', {});
    return result.modules || [];
  }

  /**
   * 调用平台模块
   * @param {string} module - 模块名
   * @param {string} action - 操作名
   * @param {Object} params - 参数
   * @returns {Promise<Object>} 执行结果
   */
  async invokeModule(module, action, params = {}) {
    return await this.call('platform_invoke', {
      module: module,
      action: action,
      params: params
    });
  }

  /**
   * 发送聊天消息
   * @param {string} message - 消息内容
   * @returns {Promise<Object>} 响应结果
   */
  async sendMessage(message) {
    return await this.call('send', { message });
  }

  /**
   * 获取会话列表
   * @returns {Promise<Array>} 会话列表
   */
  async getSessions() {
    const result = await this.call('sessions_list', {});
    return result.sessions || [];
  }

  /**
   * 更新会话配置
   * @param {Object} updates - 更新内容
   * @returns {Promise<Object>} 更新结果
   */
  async updateSession(updates) {
    return await this.call('sessions_patch', { updates });
  }

  /**
   * 获取配置
   * @param {string} [key] - 配置键（可选）
   * @returns {Promise<*>} 配置值
   */
  async getConfig(key) {
    const params = key ? { key } : {};
    return await this.call('config_get', params);
  }

  /**
   * 设置配置
   * @param {string} key - 配置键
   * @param {*} value - 配置值
   * @returns {Promise<Object>} 设置结果
   */
  async setConfig(key, value) {
    return await this.call('config_set', { key, value });
  }

  /**
   * 获取连接状态
   * @returns {boolean} 是否已连接
   */
  isConnected() {
    return this.connected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * 生成JWT token (需要使用外部JWT库)
   * @param {string} secret - JWT密钥
   * @param {number} [expireHours=24] - 过期时间（小时）
   * @returns {string} JWT token
   */
  static generateJWT(secret, userId, expireHours = 24) {
    // 注意：需要引入jsonwebtoken库
    // const jwt = require('jsonwebtoken');
    // return jwt.sign({ user_id: userId }, secret, {
    //   expiresIn: `${expireHours}h`,
    //   issuer: 'webchat-gateway'
    // });
    throw new Error('需要引入jsonwebtoken库');
  }
}

// Node.js环境导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = WebChatGatewayClient;
}

// 浏览器环境
if (typeof window !== 'undefined') {
  window.WebChatGatewayClient = WebChatGatewayClient;
}
