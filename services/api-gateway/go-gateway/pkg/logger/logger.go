package logger

import (
	"os"
	"path/filepath"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"gopkg.in/natefinch/lumberjack.v2"
)

var log *zap.Logger

// InitLogger 初始化日志系统
func InitLogger() {
	// 创建日志配置
	config := zap.NewProductionConfig()

	// 设置时间编码
	config.EncoderConfig.TimeKey = "timestamp"
	config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder

	// 设置级别
	config.Level = zap.NewAtomicLevelAt(getLogLevel())

	// 设置输出路径
	config.OutputPaths = []string{"stdout", getLogFilePath()}
	config.ErrorOutputPaths = []string{"stderr", getLogFilePath("error")}

	// 构建logger
	var err error
	log, err = config.Build(
		zap.AddCaller(),
		zap.AddStacktrace(zapcore.ErrorLevel),
	)
	if err != nil {
		panic(err)
	}
}

// getLogLevel 获取日志级别
func getLogLevel() zapcore.Level {
	level := os.Getenv("LOG_LEVEL")
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

// getLogFilePath 获取日志文件路径
func getLogFilePath(suffix ...string) string {
	logDir := os.Getenv("LOG_DIR")
	if logDir == "" {
		logDir = "./logs"
	}

	// 确保日志目录存在
	if err := os.MkdirAll(logDir, 0755); err != nil {
		panic(err)
	}

	filename := "gateway.log"
	if len(suffix) > 0 && suffix[0] != "" {
		filename = "gateway-" + suffix[0] + ".log"
	}

	return filepath.Join(logDir, filename)
}

// Debug 记录调试信息
func Debug(msg string, fields ...zap.Field) {
	log.Debug(msg, fields...)
}

// Info 记录信息
func Info(msg string, fields ...zap.Field) {
	log.Info(msg, fields...)
}

// Warn 记录警告信息
func Warn(msg string, fields ...zap.Field) {
	log.Warn(msg, fields...)
}

// Error 记录错误信息
func Error(msg string, fields ...zap.Field) {
	log.Error(msg, fields...)
}

// Fatal 记录致命错误
func Fatal(msg string, fields ...zap.Field) {
	log.Fatal(msg, fields...)
}

// Sync 同步日志
func Sync() {
	log.Sync()
}

// GetLogger 获取日志器实例
func GetLogger() *zap.Logger {
	return log
}

// WithFields 添加字段
func WithFields(fields ...zap.Field) *zap.Logger {
	return log.With(fields...)
}

// CreateRotatingLogger 创建轮转日志器
func CreateRotatingLogger(filename string, maxSize, maxBackups int) zapcore.WriteSyncer {
	logDir := os.Getenv("LOG_DIR")
	if logDir == "" {
		logDir = "./logs"
	}

	// 确保日志目录存在
	if err := os.MkdirAll(logDir, 0755); err != nil {
		panic(err)
	}

	// 创建轮转文件写入器
	return zapcore.AddSync(&lumberjack.Logger{
		Filename:   filepath.Join(logDir, filename),
		MaxSize:    maxSize, // MB
		MaxBackups: maxBackups,
		MaxAge:     30, // days
		Compress:   true,
	})
}

// InitDevelopmentLogger 初始化开发环境日志器
func InitDevelopmentLogger() {
	config := zap.NewDevelopmentConfig()
	config.EncoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
	config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder

	var err error
	log, err = config.Build(
		zap.AddCaller(),
		zap.AddStacktrace(zapcore.ErrorLevel),
	)
	if err != nil {
		panic(err)
	}
}

// InitProductionLogger 初始化生产环境日志器
func InitProductionLogger() {
	core := zapcore.NewCore(
		zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()),
		CreateRotatingLogger("gateway.log", 100, 10),
		zapcore.InfoLevel,
	)

	errorCore := zapcore.NewCore(
		zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()),
		CreateRotatingLogger("gateway-error.log", 100, 10),
		zapcore.ErrorLevel,
	)

	log = zap.New(zapcore.NewTee(core, errorCore), zap.AddCaller())
}

// AccessLogger 访问日志器
type AccessLogger struct {
	logger *zap.Logger
}

// NewAccessLogger 创建访问日志器
func NewAccessLogger() *AccessLogger {
	accessLog := CreateRotatingLogger("access.log", 100, 10)
	core := zapcore.NewCore(
		zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()),
		accessLog,
		zapcore.InfoLevel,
	)

	return &AccessLogger{
		logger: zap.New(core),
	}
}

// LogRequest 记录请求日志
func (al *AccessLogger) LogRequest(method, path, query, ip, userAgent string, statusCode int, duration int64) {
	al.logger.Info("HTTP Request",
		zap.String("method", method),
		zap.String("path", path),
		zap.String("query", query),
		zap.String("ip", ip),
		zap.String("user_agent", userAgent),
		zap.Int("status_code", statusCode),
		zap.Int64("duration_ms", duration),
	)
}

// AuditLogger 审计日志器
type AuditLogger struct {
	logger *zap.Logger
}

// NewAuditLogger 创建审计日志器
func NewAuditLogger() *AuditLogger {
	auditLog := CreateRotatingLogger("audit.log", 100, 10)
	core := zapcore.NewCore(
		zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()),
		auditLog,
		zapcore.InfoLevel,
	)

	return &AuditLogger{
		logger: zap.New(core),
	}
}

// LogAudit 记录审计日志
func (al *AuditLogger) LogAudit(userID, action, resource, resourceID, ip, userAgent, details string) {
	al.logger.Info("Audit Event",
		zap.String("user_id", userID),
		zap.String("action", action),
		zap.String("resource", resource),
		zap.String("resource_id", resourceID),
		zap.String("ip", ip),
		zap.String("user_agent", userAgent),
		zap.String("details", details),
	)
}
