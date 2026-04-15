package database

import (
	"context"
	"fmt"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/pkg/logger"

	"go.uber.org/zap"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

// Database 数据库连接管理器
type Database struct {
	db     *gorm.DB
	config *config.DatabaseConfig
}

// NewDatabase 创建新的数据库连接
func NewDatabase(cfg *config.DatabaseConfig) (*Database, error) {
	// 构建连接字符串
	dsn := buildDSN(cfg)

	// 配置GORM日志
	gormLogger := logger.Default.LogMode(logger.Info)
	if cfg.Host == "localhost" || cfg.Host == "127.0.0.1" {
		gormLogger = logger.Default.LogMode(logger.Warn)
	}

	// 连接数据库
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: gormLogger,
		NowFunc: func() time.Time {
			return time.Now().UTC()
		},
		PrepareStmt:                              true,
		DisableForeignKeyConstraintWhenMigrating: true,
	})

	if err != nil {
		return nil, fmt.Errorf("连接数据库失败: %w", err)
	}

	// 获取底层sql.DB
	sqlDB, err := db.DB()
	if err != nil {
		return nil, fmt.Errorf("获取底层数据库连接失败: %w", err)
	}

	// 配置连接池
	sqlDB.SetMaxIdleConns(cfg.MaxIdleConns)
	sqlDB.SetMaxOpenConns(cfg.MaxOpenConns)
	sqlDB.SetConnMaxLifetime(time.Duration(cfg.MaxLifetime) * time.Second)

	// 测试连接
	if err := sqlDB.Ping(); err != nil {
		return nil, fmt.Errorf("数据库连接测试失败: %w", err)
	}

	logger.Info("数据库连接成功",
		zap.String("host", cfg.Host),
		zap.Int("port", cfg.Port),
		zap.String("database", cfg.DBName),
	)

	return &Database{
		db:     db,
		config: cfg,
	}, nil
}

// buildDSN 构建数据库连接字符串
func buildDSN(cfg *config.DatabaseConfig) string {
	return fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=%s TimeZone=UTC",
		cfg.Host,
		cfg.Port,
		cfg.User,
		cfg.Password,
		cfg.DBName,
		cfg.SSLMode,
	)
}

// GetDB 获取GORM数据库实例
func (d *Database) GetDB() *gorm.DB {
	return d.db
}

// Close 关闭数据库连接
func (d *Database) Close() error {
	sqlDB, err := d.db.DB()
	if err != nil {
		return fmt.Errorf("获取底层数据库连接失败: %w", err)
	}

	if err := sqlDB.Close(); err != nil {
		return fmt.Errorf("关闭数据库连接失败: %w", err)
	}

	logger.Info("数据库连接已关闭")
	return nil
}

// Ping 测试数据库连接
func (d *Database) Ping() error {
	sqlDB, err := d.db.DB()
	if err != nil {
		return fmt.Errorf("获取底层数据库连接失败: %w", err)
	}

	if err := sqlDB.Ping(); err != nil {
		return fmt.Errorf("数据库连接测试失败: %w", err)
	}

	return nil
}

// GetStats 获取数据库连接统计信息
func (d *Database) GetStats() map[string]interface{} {
	sqlDB, err := d.db.DB()
	if err != nil {
		logger.Error("获取数据库统计信息失败", zap.Error(err))
		return nil
	}

	stats := sqlDB.Stats()
	return map[string]interface{}{
		"max_open_connections": stats.MaxOpenConnections,
		"open_connections":     stats.OpenConnections,
		"in_use":               stats.InUse,
		"idle":                 stats.Idle,
		"wait_count":           stats.WaitCount,
		"wait_duration":        stats.WaitDuration.String(),
		"max_idle_closed":      stats.MaxIdleClosed,
		"max_idle_time_closed": stats.MaxIdleTimeClosed,
		"max_lifetime_closed":  stats.MaxLifetimeClosed,
	}
}

// Transaction 事务辅助函数
func (d *Database) Transaction(fn func(*gorm.DB) error) error {
	return d.db.Transaction(fn)
}

// TransactionWithContext 带上下文的事务辅助函数
func (d *Database) TransactionWithContext(ctx context.Context, fn func(*gorm.DB) error) error {
	return d.db.WithContext(ctx).Transaction(fn)
}

// Health 检查数据库健康状态
func (d *Database) Health() error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	sqlDB, err := d.db.DB()
	if err != nil {
		return fmt.Errorf("获取底层数据库连接失败: %w", err)
	}

	// 在上下文中执行ping
	if err := sqlDB.PingContext(ctx); err != nil {
		return fmt.Errorf("数据库健康检查失败: %w", err)
	}

	return nil
}

// Migrate 执行数据库迁移
func (d *Database) Migrate(models ...interface{}) error {
	if err := d.db.AutoMigrate(models...); err != nil {
		return fmt.Errorf("数据库迁移失败: %w", err)
	}

	logger.Info("数据库迁移完成", zap.Int("models", len(models)))
	return nil
}

// CreateSchema 创建schema
func (d *Database) CreateSchema(schemaName string) error {
	sql := fmt.Sprintf("CREATE SCHEMA IF NOT EXISTS %s", schemaName)
	if err := d.db.Exec(sql).Error; err != nil {
		return fmt.Errorf("创建schema失败: %w", err)
	}

	logger.Info("Schema创建成功", zap.String("schema", schemaName))
	return nil
}

// DropSchema 删除schema
func (d *Database) DropSchema(schemaName string) error {
	sql := fmt.Sprintf("DROP SCHEMA IF EXISTS %s CASCADE", schemaName)
	if err := d.db.Exec(sql).Error; err != nil {
		return fmt.Errorf("删除schema失败: %w", err)
	}

	logger.Info("Schema删除成功", zap.String("schema", schemaName))
	return nil
}

// GetVersion 获取数据库版本
func (d *Database) GetVersion() (string, error) {
	var version string
	if err := d.db.Raw("SELECT version()").Scan(&version).Error; err != nil {
		return "", fmt.Errorf("获取数据库版本失败: %w", err)
	}

	return version, nil
}

// TableExists 检查表是否存在
func (d *Database) TableExists(tableName string) bool {
	var count int64
	err := d.db.Raw(`
		SELECT COUNT(*) 
		FROM information_schema.tables 
		WHERE table_schema = 'public' AND table_name = ?
	`, tableName).Scan(&count).Error

	return err == nil && count > 0
}

// GetTableInfo 获取表信息
func (d *Database) GetTableInfo(tableName string) (map[string]interface{}, error) {
	var result struct {
		TableName string `json:"table_name"`
		RowCount  int64  `json:"row_count"`
		TableSize string `json:"table_size"`
		IndexSize string `json:"index_size"`
	}

	// 获取表大小和行数
	err := d.db.Raw(`
		SELECT 
			schemaname||'.'||tablename as table_name,
			n_tup_ins - n_tup_del as row_count,
			pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
			pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as index_size
		FROM pg_stat_user_tables 
		WHERE schemaname = 'public' AND tablename = ?
	`, tableName).Scan(&result).Error

	if err != nil {
		return nil, fmt.Errorf("获取表信息失败: %w", err)
	}

	return map[string]interface{}{
		"table_name": result.TableName,
		"row_count":  result.RowCount,
		"table_size": result.TableSize,
		"index_size": result.IndexSize,
	}, nil
}

// BackupDatabase 备份数据库
func (d *Database) BackupDatabase(backupPath string) error {
	// 这里需要外部工具如pg_dump
	// 实际实现需要调用系统命令或使用专门的备份库
	logger.Info("数据库备份功能需要额外实现", zap.String("backup_path", backupPath))
	return nil
}

// RestoreDatabase 恢复数据库
func (d *Database) RestoreDatabase(backupPath string) error {
	// 这里需要外部工具如pg_restore
	// 实际实现需要调用系统命令或使用专门的恢复库
	logger.Info("数据库恢复功能需要额外实现", zap.String("backup_path", backupPath))
	return nil
}
