package pool

import (
	"context"
	"database/sql"
	"fmt"
	"sync"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/internal/logging"
	_ "github.com/lib/pq"
	"go.uber.org/zap"
)

// DatabasePool 数据库连接池管理器
type DatabasePool struct {
	db     *sql.DB
	config *config.DatabaseConfig
	mutex  sync.RWMutex
}

// NewDatabasePool 创建新的数据库连接池
func NewDatabasePool(cfg *config.DatabaseConfig) (*DatabasePool, error) {
	dsn := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		cfg.Host, cfg.Port, cfg.Username, cfg.Password, cfg.Database)

	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("打开数据库连接失败: %w", err)
	}

	// 设置连接池参数
	db.SetMaxOpenConns(cfg.MaxOpenConns)
	db.SetMaxIdleConns(cfg.MaxIdleConns)
	db.SetConnMaxLifetime(time.Duration(cfg.ConnMaxLifetime) * time.Second)

	// 测试连接
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("数据库连接测试失败: %w", err)
	}

	pool := &DatabasePool{
		db:     db,
		config: cfg,
	}

	// 启动连接池监控
	go pool.monitor()

	logging.LogInfo("数据库连接池初始化成功",
		zap.Int("max_open_conns", cfg.MaxOpenConns),
		zap.Int("max_idle_conns", cfg.MaxIdleConns),
		zap.Int("conn_max_lifetime", cfg.ConnMaxLifetime),
	)

	return pool, nil
}

// GetDB 获取数据库连接
func (p *DatabasePool) GetDB() *sql.DB {
	p.mutex.RLock()
	defer p.mutex.RUnlock()
	return p.db
}

// Query 执行查询
func (p *DatabasePool) Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	return p.db.QueryContext(ctx, query, args...)
}

// QueryRow 执行单行查询
func (p *DatabasePool) QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row {
	return p.db.QueryRowContext(ctx, query, args...)
}

// Exec 执行非查询语句
func (p *DatabasePool) Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	return p.db.ExecContext(ctx, query, args...)
}

// Close 关闭连接池
func (p *DatabasePool) Close() error {
	p.mutex.Lock()
	defer p.mutex.Unlock()

	if p.db != nil {
		return p.db.Close()
	}
	return nil
}

// Stats 获取连接池统计信息
func (p *DatabasePool) Stats() sql.DBStats {
	p.mutex.RLock()
	defer p.mutex.RUnlock()
	return p.db.Stats()
}

// monitor 监控连接池状态
func (p *DatabasePool) monitor() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		stats := p.Stats()

		logging.LogInfo("数据库连接池状态",
			zap.Int("open_connections", stats.OpenConnections),
			zap.Int("in_use", stats.InUse),
			zap.Int("idle", stats.Idle),
			zap.Int64("wait_count", stats.WaitCount),
			zap.Duration("wait_duration", stats.WaitDuration),
			zap.Int64("max_idle_closed", stats.MaxIdleClosed),
			zap.Int64("max_idle_time_closed", stats.MaxIdleTimeClosed),
			zap.Int64("max_lifetime_closed", stats.MaxLifetimeClosed),
		)

		// 警告检测
		if stats.WaitCount > 100 {
			logging.LogWarn("数据库连接池等待次数过多",
				zap.Int64("wait_count", stats.WaitCount),
				zap.Duration("wait_duration", stats.WaitDuration),
			)
		}

		if float64(stats.InUse)/float64(stats.OpenConnections) > 0.8 {
			logging.LogWarn("数据库连接池使用率过高",
				zap.Int("in_use", stats.InUse),
				zap.Int("open_connections", stats.OpenConnections),
				zap.Float64("usage_rate", float64(stats.InUse)/float64(stats.OpenConnections)),
			)
		}
	}
}

// HealthCheck 健康检查
func (p *DatabasePool) HealthCheck(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	if err := p.db.PingContext(ctx); err != nil {
		return fmt.Errorf("数据库健康检查失败: %w", err)
	}

	return nil
}
