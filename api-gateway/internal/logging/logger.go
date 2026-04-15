package logging

import (
	"io"
	"os"
	"path/filepath"

	"athena-gateway/internal/config"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"gopkg.in/natefinch/lumberjack.v2"
)

var (
	Logger *zap.Logger
	Sugar  *zap.SugaredLogger
)

// InitLogger 初始化日志系统
func InitLogger() error {
	cfg := config.GetConfig()
	if cfg == nil {
		return ErrConfigNotLoaded
	}

	// 创建编码器配置
	encoderConfig := createEncoderConfig(cfg.Logging.Format)

	// 创建核心
	var core zapcore.Core
	var err error

	switch cfg.Logging.Output {
	case "file":
		core, err = createFileCore(encoderConfig, cfg)
	case "stdout":
		core = createStdoutCore(encoderConfig)
	default:
		return ErrInvalidLogOutput
	}

	if err != nil {
		return err
	}

	// 创建日志器
	Logger = zap.New(core, zap.AddCaller(), zap.AddStacktrace(zapcore.ErrorLevel))
	Sugar = Logger.Sugar()

	// 测试日志输出
	Logger.Info("日志系统初始化完成",
		zap.String("level", cfg.Logging.Level),
		zap.String("format", cfg.Logging.Format),
		zap.String("output", cfg.Logging.Output),
	)

	return nil
}

// createEncoderConfig 创建编码器配置
func createEncoderConfig(format string) zapcore.EncoderConfig {
	if format == "json" {
		return zapcore.EncoderConfig{
			TimeKey:        "timestamp",
			LevelKey:       "level",
			NameKey:        "logger",
			CallerKey:      "caller",
			MessageKey:     "message",
			StacktraceKey:  "stacktrace",
			LineEnding:     zapcore.DefaultLineEnding,
			EncodeLevel:    zapcore.LowercaseLevelEncoder,
			EncodeTime:     zapcore.ISO8601TimeEncoder,
			EncodeDuration: zapcore.SecondsDurationEncoder,
			EncodeCaller:   zapcore.ShortCallerEncoder,
		}
	}

	// 文本格式
	return zapcore.EncoderConfig{
		TimeKey:        "T",
		LevelKey:       "L",
		NameKey:        "N",
		CallerKey:      "C",
		FunctionKey:    zapcore.OmitKey,
		MessageKey:     "M",
		StacktraceKey:  "S",
		LineEnding:     zapcore.DefaultLineEnding,
		EncodeLevel:    zapcore.CapitalLevelEncoder,
		EncodeTime:     zapcore.ISO8601TimeEncoder,
		EncodeDuration: zapcore.StringDurationEncoder,
		EncodeCaller:   zapcore.ShortCallerEncoder,
	}
}

// createFileCore 创建文件输出核心
func createFileCore(encoderConfig zapcore.EncoderConfig, cfg *config.Config) (zapcore.Core, error) {
	// 确保日志目录存在
	logDir := filepath.Dir(cfg.Logging.FilePath)
	if err := os.MkdirAll(logDir, 0755); err != nil {
		return nil, ErrCreateLogDir
	}

	// 创建lumberjack日志轮转
	writer := &lumberjack.Logger{
		Filename:   cfg.Logging.FilePath,
		MaxSize:    cfg.Logging.MaxSize,
		MaxBackups: cfg.Logging.MaxBackups,
		MaxAge:     cfg.Logging.MaxAge,
		Compress:   cfg.Logging.Compress,
	}

	return zapcore.NewCore(
		zapcore.NewJSONEncoder(encoderConfig),
		zapcore.AddSync(writer),
		getLogLevel(cfg.Logging.Level),
	), nil
}

// createStdoutCore 创建标准输出核心
func createStdoutCore(encoderConfig zapcore.EncoderConfig) zapcore.Core {
	return zapcore.NewCore(
		zapcore.NewConsoleEncoder(encoderConfig),
		zapcore.AddSync(os.Stdout),
		getLogLevel(config.GetConfig().Logging.Level),
	)
}

// getLogLevel 获取日志级别
func getLogLevel(level string) zapcore.Level {
	switch level {
	case "debug":
		return zapcore.DebugLevel
	case "info":
		return zapcore.InfoLevel
	case "warn":
		return zapcore.WarnLevel
	case "error":
		return zapcore.ErrorLevel
	default:
		return zapcore.InfoLevel
	}
}

// LogRequest 记录HTTP请求日志
func LogRequest(method, path string, statusCode int, duration int64, clientIP string, userAgent string) {
	Logger.Info("HTTP请求",
		zap.String("method", method),
		zap.String("path", path),
		zap.Int("status_code", statusCode),
		zap.Int64("duration_ms", duration),
		zap.String("client_ip", clientIP),
		zap.String("user_agent", userAgent),
	)
}

// LogError 记录错误日志
func LogError(err error, message string, fields ...zap.Field) {
	allFields := append([]zap.Field{zap.Error(err)}, fields...)
	Logger.Error(message, allFields...)
}

// LogPanic 记录Panic日志
func LogPanic(message string, fields ...zap.Field) {
	Logger.Panic(message, fields...)
}

// LogInfo 记录信息日志
func LogInfo(message string, fields ...zap.Field) {
	Logger.Info(message, fields...)
}

// LogDebug 记录调试日志
func LogDebug(message string, fields ...zap.Field) {
	Logger.Debug(message, fields...)
}

// LogWarn 记录警告日志
func LogWarn(message string, fields ...zap.Field) {
	Logger.Warn(message, fields...)
}

// WithRequestID 为日志添加请求ID
func WithRequestID(requestID string) *zap.Logger {
	if Logger == nil {
		return zap.NewNop()
	}
	return Logger.With(zap.String("request_id", requestID))
}

// WithUser 为日志添加用户信息
func WithUser(userID, username string) *zap.Logger {
	return Logger.With(
		zap.String("user_id", userID),
		zap.String("username", username),
	)
}

// WithService 为日志添加服务信息
func WithService(serviceName string) *zap.Logger {
	return Logger.With(zap.String("service", serviceName))
}

// Sync 同步日志缓冲区
func Sync() error {
	if Logger != nil {
		return Logger.Sync()
	}
	return nil
}

// Close 关闭日志系统
func Close() {
	if err := Sync(); err != nil {
		// 忽略sync错误，因为程序正在退出
	}
}

// 创建日志级别转换函数
func ParseLogLevel(level string) zapcore.Level {
	switch level {
	case "debug":
		return zapcore.DebugLevel
	case "info":
		return zapcore.InfoLevel
	case "warn":
		return zapcore.WarnLevel
	case "error":
		return zapcore.ErrorLevel
	default:
		return zapcore.InfoLevel
	}
}

// MultiWriter 创建多输出写入器
func MultiWriter(writers ...io.Writer) io.Writer {
	return io.MultiWriter(writers...)
}
