package logging

import "go.uber.org/zap"

func LogInfo(msg string, fields ...zap.Field) {
	log.Printf("[INFO] %s", msg)
}

func LogDebug(msg string, fields ...zap.Field) {
	log.Printf("[DEBUG] %s", msg)
}

func LogWarn(msg string, fields ...zap.Field) {
	log.Printf("[WARN] %s", msg)
}

func LogError(msg string, fields ...zap.Field) {
	log.Printf("[ERROR] %s", msg)
}
