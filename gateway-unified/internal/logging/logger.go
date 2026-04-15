// Package logging - 结构化日志系统
// 提供简单的结构化日志功能，支持日志轮转
package logging

import (
	"fmt"
	"io"
	"log"
	"os"
	"sync"
)

// Logger 日志记录器
type Logger struct {
	mu           sync.Mutex
	logger       *log.Logger
	level        string
	rotateWriter *RotateWriter // 日志轮转写入器
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
			logger:       log.New(output, "[GATEWAY] ", log.LstdFlags|log.Lshortfile),
			level:        logLevel,
			rotateWriter: rotateWriter,
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
			logger: log.New(os.Stdout, "[GATEWAY] ", log.LstdFlags),
			level:  "info",
		}
	}
	return globalLogger
}

// logInternal 内部日志方法
func logInternal(level string, msg string, fields ...Field) {
	logger := getLogger()
	logger.mu.Lock()
	defer logger.mu.Unlock()

	prefix := fmt.Sprintf("[%s] ", level)
	logMsg := prefix + msg
	for _, f := range fields {
		logMsg += fmt.Sprintf(" %s=%v", f.Key(), f.Value())
	}
	logger.logger.Println(logMsg)
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
