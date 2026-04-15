package middleware

import (
	"strconv"
	"time"

	"github.com/athena-workspace/core/gateway/pkg/metrics"
	"github.com/gin-gonic/gin"
)

func MetricsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		method := c.Request.Method
		userAgent := c.Request.UserAgent()

		userAgentType := getUserAgentType(userAgent)

		c.Next()

		duration := time.Since(start)
		status := strconv.Itoa(c.Writer.Status())

		var service string
		if c.GetString("service") != "" {
			service = c.GetString("service")
		} else {
			service = "unknown"
		}

		requestSize := c.Request.ContentLength
		responseSize := int64(c.Writer.Size())

		metrics.RecordHTTPRequest(
			method,
			path,
			status,
			service,
			userAgentType,
			duration,
			requestSize,
			responseSize,
		)
	}
}

func getUserAgentType(userAgent string) string {
	if userAgent == "" {
		return "unknown"
	}

	if len(userAgent) > 100 {
		userAgent = userAgent[:100]
	}

	if contains(userAgent, "Mozilla") {
		return "browser"
	}
	if contains(userAgent, "curl") || contains(userAgent, "wget") {
		return "cli"
	}
	if contains(userAgent, "python-requests") {
		return "python_client"
	}
	if contains(userAgent, "java") {
		return "java_client"
	}
	if contains(userAgent, "axios") || contains(userAgent, "fetch") {
		return "javascript_client"
	}

	return "other"
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr ||
		(len(s) > len(substr) &&
			(s[:len(substr)] == substr ||
				s[len(s)-len(substr):] == substr ||
				containsSubstring(s, substr))))
}

func containsSubstring(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
