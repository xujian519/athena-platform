package middleware

import (
	"athena-gateway/internal/errors"
	"github.com/gin-gonic/gin"
	"net/http"
)

// ErrorHandlingMiddleware 将Gin未处理的错误统一转换为标准错误响应
func ErrorHandlingMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 继续处理链路
		c.Next()

		// 如果有错误被挂起，在这里统一处理
		if len(c.Errors) > 0 {
			// 使用第一个错误来构造 AppError，并输出统一结构的错误响应
			appErr := errors.FromGoError(c.Errors[0].Err)
			if appErr == nil {
				appErr = errors.NewAppError(http.StatusInternalServerError, "未处理的错误", nil)
			}
			errors.WriteAppError(c, appErr)
			c.Abort()
		}
	}
}
