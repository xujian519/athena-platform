package logging

import "errors"

var (
	// 配置相关错误
	ErrConfigNotLoaded  = errors.New("配置未加载")
	ErrInvalidLogOutput = errors.New("无效的日志输出类型")
	ErrCreateLogDir     = errors.New("创建日志目录失败")

	// JWT相关错误
	ErrInvalidToken         = errors.New("无效的令牌")
	ErrTokenExpired         = errors.New("令牌已过期")
	ErrInvalidSigningMethod = errors.New("无效的签名方法")
	ErrTokenNotProvided     = errors.New("未提供令牌")

	// 认证相关错误
	ErrInvalidCredentials = errors.New("无效的凭据")
	ErrUserNotFound       = errors.New("用户不存在")
	ErrUserDisabled       = errors.New("用户已禁用")
	ErrPermissionDenied   = errors.New("权限不足")
	ErrAccountLocked      = errors.New("账户已锁定")

	// 服务器相关错误
	ErrServerStartup    = errors.New("服务器启动失败")
	ErrServerShutdown   = errors.New("服务器关闭失败")
	ErrGracefulShutdown = errors.New("优雅关闭失败")

	// 中间件相关错误
	ErrMiddlewareSetup   = errors.New("中间件设置失败")
	ErrRateLimitExceeded = errors.New("请求频率超限")
	ErrInvalidHeaders    = errors.New("无效的请求头")

	// 代理相关错误
	ErrUpstreamUnavailable     = errors.New("上游服务不可用")
	ErrUpstreamTimeout         = errors.New("上游服务超时")
	ErrUpstreamError           = errors.New("上游服务错误")
	ErrInvalidUpstreamResponse = errors.New("上游服务响应无效")

	// 配置相关错误
	ErrInvalidConfig    = errors.New("无效的配置")
	ErrConfigLoad       = errors.New("配置加载失败")
	ErrConfigValidation = errors.New("配置验证失败")

	// 响应相关错误
	ErrResponseWrite   = errors.New("响应写入失败")
	ErrJSONMarshal     = errors.New("JSON序列化失败")
	ErrInvalidResponse = errors.New("无效的响应")

	// 健康检查相关错误
	ErrHealthCheck        = errors.New("健康检查失败")
	ErrServiceNotReady    = errors.New("服务未就绪")
	ErrDatabaseConnection = errors.New("数据库连接失败")

	// 通用错误
	ErrInternalServer   = errors.New("内部服务器错误")
	ErrBadRequest       = errors.New("请求参数错误")
	ErrUnauthorized     = errors.New("未授权")
	ErrForbidden        = errors.New("禁止访问")
	ErrNotFound         = errors.New("资源不存在")
	ErrMethodNotAllowed = errors.New("方法不允许")
	ErrRequestTimeout   = errors.New("请求超时")
	ErrTooManyRequests  = errors.New("请求过于频繁")
)
