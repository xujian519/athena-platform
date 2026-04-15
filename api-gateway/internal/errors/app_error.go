package errors

import (
	"athena-gateway/pkg/response"
	"github.com/gin-gonic/gin"
	"net/http"
)

// AppError 定义应用级错误，以便在HTTP响应中使用统一结构返回
// Code 为HTTP状态码，Message 为错误信息，Err 携带可选的底层错误
type AppError struct {
	Code    int
	Message string
	Err     error
}

// NewAppError 创建一个新的应用错误对象
func NewAppError(code int, message string, err error) *AppError {
	return &AppError{Code: code, Message: message, Err: err}
}

// Error 实现 error 接口
func (e *AppError) Error() string {
	if e == nil {
		return ""
	}
	if e.Err != nil {
		return e.Err.Error()
	}
	return e.Message
}

// FromGoError 将普通错误转换为 AppError（默认内部服务器错误）
func FromGoError(err error) *AppError {
	if err == nil {
		return nil
	}
	return &AppError{Code: http.StatusInternalServerError, Message: "内部服务器错误", Err: err}
}

// WriteAppError 将 AppError 写入响应，遵循统一的响应格式
func WriteAppError(c *gin.Context, appErr *AppError) {
	if appErr == nil {
		return
	}
	code := appErr.Code
	if code == 0 {
		code = http.StatusInternalServerError
	}
	detail := ""
	if appErr.Err != nil {
		detail = appErr.Err.Error()
	}
	response.Error(c, code, appErr.Message, detail)
}
