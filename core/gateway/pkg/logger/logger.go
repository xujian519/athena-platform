package logger

import (
	"github.com/athena-workspace/core/gateway/internal/config"
	"go.uber.org/zap"
)

var log *zap.Logger

func Init(cfg config.LoggingConfig) {
	var err error
	loggerConfig := zap.NewProductionConfig()

	if cfg.Level == "debug" {
		loggerConfig.Level = zap.NewAtomicLevelAt(zap.DebugLevel)
	} else if cfg.Level == "info" {
		loggerConfig.Level = zap.NewAtomicLevelAt(zap.InfoLevel)
	} else if cfg.Level == "warn" {
		loggerConfig.Level = zap.NewAtomicLevelAt(zap.WarnLevel)
	} else if cfg.Level == "error" {
		loggerConfig.Level = zap.NewAtomicLevelAt(zap.ErrorLevel)
	}

	log, err = loggerConfig.Build()
	if err != nil {
		panic(err)
	}
}

func Info(format string, args ...interface{}) {
	if log != nil {
		log.Sugar().Infof(format, args...)
	}
}

func Debug(format string, args ...interface{}) {
	if log != nil {
		log.Sugar().Debugf(format, args...)
	}
}

func Warn(format string, args ...interface{}) {
	if log != nil {
		log.Sugar().Warnf(format, args...)
	}
}

func Error(format string, args ...interface{}) {
	if log != nil {
		log.Sugar().Errorf(format, args...)
	}
}

func Fatal(format string, args ...interface{}) {
	if log != nil {
		log.Sugar().Fatalf(format, args...)
	}
}
