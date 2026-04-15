package middleware

import (
	"github.com/gin-gonic/gin"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/propagation"
	"net/http"
)

func TracingMiddleware(serviceName string) gin.HandlerFunc {
	return gin.HandlerFunc(func(c *gin.Context) {
		ctx := otel.GetTextMapPropagator().Extract(c.Request.Context(), propagation.HeaderCarrier(c.Request.Header))

		tracer := otel.Tracer(serviceName)
		ctx, span := tracer.Start(ctx, c.Request.Method+" "+c.Request.URL.Path)
		defer span.End()

		c.Request = c.Request.WithContext(ctx)

		c.Next()

		statusCode := c.Writer.Status()

		if statusCode >= 400 {
			span.SetStatus(codes.Error, http.StatusText(statusCode))
		} else {
			span.SetStatus(codes.Ok, "OK")
		}
	})
}

func TracingHeadersMiddleware() gin.HandlerFunc {
	return gin.HandlerFunc(func(c *gin.Context) {
		propagator := otel.GetTextMapPropagator()
		headers := make(map[string]string)

		propagator.Inject(c.Request.Context(), propagation.MapCarrier(headers))

		for key, value := range headers {
			c.Request.Header.Set(key, value)
		}

		c.Next()
	})
}
