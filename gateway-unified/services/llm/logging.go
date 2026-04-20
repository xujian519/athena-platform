// Package llm - 本地日志包装器
package llm

import (
	"fmt"
	"log"
	"os"
)

// 本地日志函数（替代主模块internal/logging）
func LogInfo(msg string, args ...interface{}) {
	log.Printf("[INFO] %s", fmt.Sprintf(msg, args...))
}

func LogDebug(msg string, args ...interface{}) {
	if os.Getenv("DEBUG") != "" || os.Getenv("TRACE") != "" {
		log.Printf("[DEBUG] %s", fmt.Sprintf(msg, args...))
	}
}

func LogWarn(msg string, args ...interface{}) {
	log.Printf("[WARN] %s", fmt.Sprintf(msg, args...))
}

func LogError(msg string, args ...interface{}) {
	log.Printf("[ERROR] %s", fmt.Sprintf(msg, args...))
}
