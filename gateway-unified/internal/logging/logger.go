// Package logging - 结构化日志系统
// 提供简单的结构化日志功能，支持日志轮转
package logging

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// Logger 日志记录器
type Logger struct {
	mu           sync.Mutex
	logger       *log.Logger
	level        string
	rotateWriter *RotateWriter // 日志轮转写入器
	jsonFormat   bool          // 是否使用JSON格式
	serviceName  string        // 服务名称
}

// LogEntry JSON结构化日志条目
type LogEntry struct {
	Timestamp      string `json:"timestamp"`
	Level          string `json:"level"`
	Service        string `json:"service"`
	RequestID      string `json:"request_id,omitempty"`
	TraceID        string `json:"trace_id,omitempty"`
	SpanID         string `json:"span_id,omitempty"`
	Message        string `json:"message,omitempty"`
	Method         string `json:"method,omitempty"`
	Path           string `json:"path,omitempty"`
	Status         int    `json:"status,omitempty"`
	DurationMs     int64  `json:"duration_ms,omitempty"`
	UpstreamService string `json:"upstream_service,omitempty"`
	UpstreamDurationMs int64 `json:"upstream_duration_ms,omitempty"`
	ClientIP       string `json:"client_ip,omitempty"`
	UserAgent      string `json:"user_agent,omitempty"`
	Error          string `json:"error,omitempty"`
	Fields         map[string]interface{} `json:"-"`
}

var (
	globalLogger *Logger
	once         sync.Once
	rotateWriter *RotateWriter
)

// Init 初始化日志系统
func Init(cfg interface{}) error {
	var err error
	once.Do(func() {
		// 默认输出到stdout
		var output io.Writer = os.Stdout
		logLevel := "info"
		jsonFormat := true // 默认使用JSON格式
		serviceName := "gateway-unified"

		// TODO: 从cfg解析配置
		// 当前简化处理，直接使用stdout

		// 如果输出是文件路径，启用日志轮转
		outputStr := "stdout" // 默认值
		if outputStr == "stdout" {
			output = os.Stdout
		} else if outputStr == "stderr" {
			output = os.Stderr
		} else {
			// 文件输出，启用日志轮转
			rotateWriter, err = NewRotateWriter(outputStr, DefaultRotationConfig())
			if err != nil {
				// 回退到stdout
				output = os.Stdout
				fmt.Fprintf(os.Stderr, "日志轮转初始化失败，使用标准输出: %v\n", err)
			} else {
				output = rotateWriter
			}
		}

		globalLogger = &Logger{
			logger:       log.New(output, "", 0), // JSON格式不需要前缀
			level:        logLevel,
			rotateWriter: rotateWriter,
			jsonFormat:   jsonFormat,
			serviceName:  serviceName,
		}
		err = nil
	})
	return err
}

// Sync 同步日志
func Sync() error {
	if rotateWriter != nil {
		return rotateWriter.Close()
	}
	return nil
}

// getLogger 获取全局logger
func getLogger() *Logger {
	if globalLogger == nil {
		globalLogger = &Logger{
			logger:      log.New(os.Stdout, "", 0),
			level:       "info",
			jsonFormat:  true,
			serviceName: "gateway-unified",
		}
	}
	return globalLogger
}

// logInternal 内部日志方法
func logInternal(level string, msg string, fields ...Field) {
	logger := getLogger()
	logger.mu.Lock()
	defer logger.mu.Unlock()

	if logger.jsonFormat {
		// JSON结构化日志
		entry := LogEntry{
			Timestamp: time.Now().UTC().Format("2006-01-02T15:04:05.000Z"),
			Level:     level,
			Service:   logger.serviceName,
			Message:   msg,
			Fields:    make(map[string]interface{}),
		}

		// 解析字段
		for _, f := range fields {
			switch f.Key() {
			case "request_id":
				entry.RequestID = fmt.Sprintf("%v", f.Value())
			case "trace_id":
				entry.TraceID = fmt.Sprintf("%v", f.Value())
			case "span_id":
				entry.SpanID = fmt.Sprintf("%v", f.Value())
			case "method":
				entry.Method = fmt.Sprintf("%v", f.Value())
			case "path":
				entry.Path = fmt.Sprintf("%v", f.Value())
			case "status":
				if status, ok := f.Value().(int); ok {
					entry.Status = status
				}
			case "duration_ms":
				if duration, ok := f.Value().(int64); ok {
					entry.DurationMs = duration
				}
			case "upstream_service":
				entry.UpstreamService = fmt.Sprintf("%v", f.Value())
			case "upstream_duration_ms":
				if duration, ok := f.Value().(int64); ok {
					entry.UpstreamDurationMs = duration
				}
			case "client_ip":
				entry.ClientIP = fmt.Sprintf("%v", f.Value())
			case "user_agent":
				entry.UserAgent = fmt.Sprintf("%v", f.Value())
			case "error":
				entry.Error = fmt.Sprintf("%v", f.Value())
			default:
				entry.Fields[f.Key()] = f.Value()
			}
		}

		// 序列化为JSON
		jsonBytes, err := json.Marshal(entry)
		if err != nil {
			// 降级到普通日志
			logger.logger.Printf("[JSON_SERIALIZE_ERROR] %s %v", msg, fields)
			return
		}
		logger.logger.Println(string(jsonBytes))
	} else {
		// 普通文本日志（向后兼容）
		prefix := fmt.Sprintf("[%s] ", level)
		logMsg := prefix + msg
		for _, f := range fields {
			logMsg += fmt.Sprintf(" %s=%v", f.Key(), f.Value())
		}
		logger.logger.Println(logMsg)
	}
}

// LogInfo 信息日志
func LogInfo(msg string, fields ...Field) {
	logInternal("INFO", msg, fields...)
}

// LogWarn 警告日志
func LogWarn(msg string, fields ...Field) {
	logInternal("WARN", msg, fields...)
}

// LogError 错误日志
func LogError(msg string, fields ...Field) {
	logInternal("ERROR", msg, fields...)
}

// LogFatal 致命错误日志
func LogFatal(msg string, fields ...Field) {
	logInternal("FATAL", msg, fields...)
}

// LogDebug 调试日志
func LogDebug(msg string, fields ...Field) {
	logInternal("DEBUG", msg, fields...)
}

// ==================== 新增：基于Gin上下文的日志函数 ====================

// 关键字常量
const (
	// 上下文键
	RequestIDKey = "request_id"
	TraceIDKey   = "trace_id"
	SpanIDKey    = "span_id"
	UserIDKey    = "user_id"
	ServiceKey   = "service"

	// 日志级别
	LevelDebug = "debug"
	LevelInfo  = "info"
	LevelWarn  = "warn"
	LevelError = "error"
)

// 从Gin上下文提取追踪字段
func extractTraceFields(c *gin.Context) []Field {
	if c == nil {
		return []Field{}
	}

	fields := []Field{}

	if requestID, exists := c.Get("request_id"); exists {
		if id, ok := requestID.(string); ok {
			fields = append(fields, String("request_id", id))
		}
	}

	if traceID := c.GetHeader("X-Trace-ID"); traceID != "" {
		fields = append(fields, String("trace_id", traceID))
	}

	if spanID := c.GetHeader("X-Span-ID"); spanID != "" {
		fields = append(fields, String("span_id", spanID))
	}

	if userID := c.GetHeader("X-User-ID"); userID != "" {
		fields = append(fields, String("user_id", userID))
	}

	return fields
}

// LogInfoWithContext 带上下文的信息日志
func LogInfoWithContext(c *gin.Context, msg string, fields ...Field) {
	allFields := append(extractTraceFields(c), fields...)
	logInternal("INFO", msg, allFields...)
}

// LogWarnWithContext 带上下文的警告日志
func LogWarnWithContext(c *gin.Context, msg string, fields ...Field) {
	allFields := append(extractTraceFields(c), fields...)
	logInternal("WARN", msg, allFields...)
}

// LogErrorWithContext 带上下文的错误日志
func LogErrorWithContext(c *gin.Context, msg string, fields ...Field) {
	allFields := append(extractTraceFields(c), fields...)
	logInternal("ERROR", msg, allFields...)
}

// LogDebugWithContext 带上下文的调试日志
func LogDebugWithContext(c *gin.Context, msg string, fields ...Field) {
	allFields := append(extractTraceFields(c), fields...)
	logInternal("DEBUG", msg, allFields...)
}

// ==================== 新增：请求追踪中间件 ====================

// RequestLoggingMiddleware 请求日志中间件
func RequestLoggingMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()

		// 处理请求
		c.Next()

		// 记录日志
		duration := time.Since(start)
		LogInfoWithContext(c, "HTTP请求",
			String("method", c.Request.Method),
			String("path", c.Request.URL.Path),
			Int("status", c.Writer.Status()),
			Duration("duration", duration),
			String("client_ip", c.ClientIP()),
		)
	}
}

// TracingMiddleware 链路追踪中间件
func TracingMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 生成或获取 Trace ID
		traceID := c.GetHeader("X-Trace-ID")
		if traceID == "" {
			traceID = uuid.New().String()
		}
		c.Header("X-Trace-ID", traceID)

		// 生成 Span ID
		spanID := uuid.New().String()
		c.Header("X-Span-ID", spanID)

		// 存储到上下文
		c.Set("trace_id", traceID)
		c.Set("span_id", spanID)

		c.Next()
	}
}
