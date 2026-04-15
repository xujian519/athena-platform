package server

import (
	"bytes"
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"time"

	"athena-gateway/internal/auth"
	"athena-gateway/internal/cache"
	"athena-gateway/internal/config"
	"athena-gateway/internal/handlers"
	"athena-gateway/internal/logging"
	"athena-gateway/internal/middleware"
	"athena-gateway/internal/performance"
	"athena-gateway/internal/pool"
	"athena-gateway/internal/ratelimit"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

type Server struct {
	config            *config.Config
	httpServer        *http.Server
	router            *gin.Engine
	jwtManager        *auth.JWTManager
	healthHandler     *handlers.HealthHandler
	authHandler       *handlers.AuthHandler
	adminHandler      *handlers.AdminHandler
	cacheManager      *cache.MultiLevelCache
	rateLimiter       *ratelimit.AdaptiveRateLimiter
	resourceMonitor   *performance.ResourceMonitor
	resourceOptimizer *performance.ResourceOptimizer
	dbPool            *pool.DatabasePool
	httpClientPool    *pool.HTTPClientPool
}

type responseBodyWriter struct {
	gin.ResponseWriter
	body *bytes.Buffer
}

func (w *responseBodyWriter) Write(b []byte) (int, error) {
	w.body.Write(b)
	return w.ResponseWriter.Write(b)
}

// NewServer 创建新的HTTP服务器
func NewServer(version string) (*Server, error) {
	// 加载配置
	cfg, err := config.LoadConfig("")
	if err != nil {
		return nil, fmt.Errorf("加载配置失败: %w", err)
	}

	// 设置Gin模式
	if cfg.IsProduction() {
		gin.SetMode(gin.ReleaseMode)
	} else {
		gin.SetMode(gin.DebugMode)
	}

	// 创建路由器
	router := gin.New()

	jwtManager, err := auth.NewJWTManager()
	if err != nil {
		return nil, fmt.Errorf("创建JWT管理器失败: %w", err)
	}

	healthHandler := handlers.NewHealthHandler(version)
	authHandler := handlers.NewAuthHandler(jwtManager)
	adminHandler := handlers.NewAdminHandler(version)

	cacheManager, err := cache.NewMultiLevelCache(&cfg.Redis)
	if err != nil {
		logging.LogWarn("多级缓存初始化失败，将禁用缓存功能", zap.Error(err))
	}

	rateLimiter, err := ratelimit.NewAdaptiveRateLimiter(&cfg.RateLimit)
	if err != nil {
		logging.LogWarn("自适应限流器初始化失败，将禁用限流功能", zap.Error(err))
	}

	resourceMonitor := performance.NewResourceMonitor(&cfg.Performance)
	resourceOptimizer := performance.NewResourceOptimizer(resourceMonitor, &cfg.Performance)

	dbPool, err := pool.NewDatabasePool(&cfg.Database)
	if err != nil {
		logging.LogWarn("数据库连接池初始化失败", zap.Error(err))
	}

	httpClientPool := pool.NewHTTPClientPool(&cfg.HTTPClient)

	server := &Server{
		config:            cfg,
		router:            router,
		jwtManager:        jwtManager,
		healthHandler:     healthHandler,
		authHandler:       authHandler,
		adminHandler:      adminHandler,
		cacheManager:      cacheManager,
		rateLimiter:       rateLimiter,
		resourceMonitor:   resourceMonitor,
		resourceOptimizer: resourceOptimizer,
		dbPool:            dbPool,
		httpClientPool:    httpClientPool,
	}

	server.setupMiddleware()
	server.setupRoutes()
	server.startPerformanceComponents()

	// 创建HTTP服务器
	server.httpServer = &http.Server{
		Addr:         cfg.GetServerAddr(),
		Handler:      router,
		ReadTimeout:  time.Duration(cfg.Server.ReadTimeout) * time.Second,
		WriteTimeout: time.Duration(cfg.Server.WriteTimeout) * time.Second,
		IdleTimeout:  time.Duration(cfg.Server.IdleTimeout) * time.Second,
	}

	return server, nil
}

// setupMiddleware 设置中间件
func (s *Server) setupMiddleware() {
	// 恢复中间件
	s.router.Use(middleware.RecoveryMiddleware())

	// 统一错误处理中间件：将Gin错误转换为统一的错误响应
	s.router.Use(middleware.ErrorHandlingMiddleware())

	// 请求ID中间件
	s.router.Use(middleware.RequestIDMiddleware())

	// 日志中间件
	s.router.Use(middleware.LoggingMiddleware())

	s.router.Use(middleware.CORSMiddleware())
	s.router.Use(middleware.SecurityHeadersMiddleware())
	s.router.Use(middleware.TimeoutMiddleware(30 * time.Second))

	if s.cacheManager != nil {
		s.router.Use(s.setupCacheMiddleware())
	}

	if s.rateLimiter != nil {
		s.router.Use(s.setupRateLimitMiddleware())
	}

	if s.config.Performance.EnablePprof {
		middleware.SetupPprofRoutes(s.router, &s.config.Performance)
		s.router.Use(middleware.PprofMiddleware(&s.config.Performance))
		if s.config.IsProduction() {
			s.router.Use(middleware.SecurityMiddlewareForPprof())
		}
	}
}

func (s *Server) setupCacheMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		if s.cacheManager == nil {
			c.Next()
			return
		}

		path := c.Request.URL.Path
		method := c.Request.Method

		if method != "GET" && method != "HEAD" {
			c.Next()
			return
		}

		writer := &responseBodyWriter{ResponseWriter: c.Writer, body: &bytes.Buffer{}}
		c.Writer = writer

		ctx, cancel := context.WithTimeout(c.Request.Context(), 5*time.Second)
		defer cancel()

		if cachedData, err := s.cacheManager.Get(ctx, "response:"+path); err == nil {
			logging.LogInfo("缓存命中",
				zap.String("path", path),
				zap.String("method", method),
			)
			c.Data(200, "application/json", cachedData.([]byte))
			c.Abort()
			return
		}

		c.Next()

		if c.Writer.Status() == 200 {
			responseData := writer.body.Bytes()
			if len(responseData) > 0 {
				s.cacheManager.Set(ctx, "response:"+path, responseData, 5*time.Minute)
				logging.LogInfo("响应已缓存",
					zap.String("path", path),
					zap.Int("size", len(responseData)),
				)
			}
		}
	}
}

func (s *Server) Shutdown() error {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if s.cacheManager != nil {
		if err := s.cacheManager.Close(ctx); err != nil {
			logging.LogError(err, "关闭缓存管理器失败")
		}
	}

	if s.dbPool != nil {
		if err := s.dbPool.Close(); err != nil {
			logging.LogError(err, "关闭数据库连接池失败")
		}
	}

	if s.httpClientPool != nil {
		s.httpClientPool.Close()
	}

	return s.httpServer.Shutdown(ctx)
}

func (s *Server) setupRateLimitMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		if s.rateLimiter == nil {
			c.Next()
			return
		}

		clientIP := c.ClientIP()
		path := c.Request.URL.Path

		if !s.rateLimiter.Allow(c.Request.Context(), clientIP) {
			logging.LogWarn("请求被限流",
				zap.String("client_ip", clientIP),
				zap.String("path", path),
				zap.String("method", c.Request.Method),
			)
			result := s.rateLimiter.Limit(c.Request.Context(), clientIP)
			c.JSON(429, result)
			c.Abort()
			return
		}

		c.Next()
	}
}

// GetRouter 获取路由器（用于测试）
func (s *Server) GetRouter() *gin.Engine {
	return s.router
}

// GetJWTManager 获取JWT管理器（用于测试）
func (s *Server) GetJWTManager() *auth.JWTManager {
	return s.jwtManager
}

// Run 运行服务器（启动并处理优雅关闭）
func (s *Server) Run() error {
	// 启动服务器（在goroutine中）
	go func() {
		if err := s.Start(); err != nil && err != http.ErrServerClosed {
			logging.LogError(err, "服务器启动失败")
		}
	}()

	// 等待优雅关闭
	return s.GracefulShutdown()
}

// setupRoutes 设置路由
func (s *Server) setupRoutes() {
	// 健康检查路由
	s.router.GET("/health", s.healthHandler.BasicHealth)
	s.router.GET("/ready", s.healthHandler.Readiness)
	s.router.GET("/ping", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "pong"})
	})

	// API路由组
	api := s.router.Group("/api/v1")
	{
		// 认证路由
		api.POST("/auth/login", s.authHandler.Login)
		api.POST("/auth/refresh", s.authHandler.RefreshToken)
		api.POST("/auth/logout", s.authHandler.Logout)

		// 管理路由 (需要认证)
		admin := api.Group("/admin")
		{
			// TODO: 添加认证中间件
			admin.GET("/status", s.adminHandler.Status)
			admin.GET("/metrics", s.adminHandler.Metrics)
		}
	}
}

// startPerformanceComponents 启动性能监控组件
func (s *Server) startPerformanceComponents() {
	// 性能监控组件将在实际运行时启动
	// 这里暂时只记录日志
	logging.LogInfo("性能监控组件已初始化")
}

// Start 启动HTTP服务器
func (s *Server) Start() error {
	logging.LogInfo("启动HTTP服务器",
		zap.String("addr", s.httpServer.Addr),
		zap.Bool("production", s.config.IsProduction()),
	)

	if err := s.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		return fmt.Errorf("服务器启动失败: %w", err)
	}

	return nil
}

// GracefulShutdown 优雅关闭服务器
func (s *Server) GracefulShutdown() error {
	// 等待中断信号
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, os.Kill)
	<-quit

	logging.LogInfo("开始优雅关闭服务器...")

	// 设置关闭超时
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// 关闭HTTP服务器
	if err := s.httpServer.Shutdown(ctx); err != nil {
		return fmt.Errorf("服务器关闭失败: %w", err)
	}

	logging.LogInfo("服务器已优雅关闭")
	return nil
}
