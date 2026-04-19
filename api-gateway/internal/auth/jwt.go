package auth

import (
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/internal/logging"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"go.uber.org/zap"
)

// TokenType 令牌类型
type TokenType string

const (
	AccessToken  TokenType = "access"
	RefreshToken TokenType = "refresh"
)

// Claims JWT声明
type Claims struct {
	UserID    string    `json:"user_id"`
	Username  string    `json:"username"`
	Email     string    `json:"email"`
	Role      string    `json:"role"`
	TokenType TokenType `json:"token_type"`
	jwt.RegisteredClaims
}

// UserInfo 用户信息
type UserInfo struct {
	UserID   string `json:"user_id"`
	Username string `json:"username"`
	Email    string `json:"email"`
	Role     string `json:"role"`
}

// TokenPair 令牌对
type TokenPair struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	ExpiresIn    int64  `json:"expires_in"`  // 访问令牌过期时间（秒）
	RefreshExp   int64  `json:"refresh_exp"` // 刷新令牌过期时间（秒）
}

// JWTManager JWT管理器
type JWTManager struct {
	secretKey []byte
	issuer    string
}

// NewJWTManager 创建JWT管理器
func NewJWTManager() (*JWTManager, error) {
	cfg := config.GetConfig()
	if cfg == nil {
		return nil, logging.ErrConfigNotLoaded
	}

	if cfg.Auth.JWTSecret == "" {
		return nil, logging.ErrInvalidToken
	}

	return &JWTManager{
		secretKey: []byte(cfg.Auth.JWTSecret),
		issuer:    cfg.Auth.Issuer,
	}, nil
}

// GenerateTokenPair 生成令牌对
func (j *JWTManager) GenerateTokenPair(user *UserInfo) (*TokenPair, error) {
	cfg := config.GetConfig()
	if cfg == nil {
		return nil, logging.ErrConfigNotLoaded
	}

	// 生成访问令牌
	accessToken, err := j.generateToken(user, AccessToken, time.Duration(cfg.Auth.AccessTokenExp)*time.Minute)
	if err != nil {
		logging.LogError(err, "生成访问令牌失败", zap.String("user_id", user.UserID))
		return nil, err
	}

	// 生成刷新令牌
	refreshToken, err := j.generateToken(user, RefreshToken, time.Duration(cfg.Auth.RefreshTokenExp)*time.Hour)
	if err != nil {
		logging.LogError(err, "生成刷新令牌失败", zap.String("user_id", user.UserID))
		return nil, err
	}

	return &TokenPair{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		ExpiresIn:    int64(cfg.Auth.AccessTokenExp * 60),    // 转换为秒
		RefreshExp:   int64(cfg.Auth.RefreshTokenExp * 3600), // 转换为秒
	}, nil
}

// generateToken 生成令牌
func (j *JWTManager) generateToken(user *UserInfo, tokenType TokenType, duration time.Duration) (string, error) {
	now := time.Now()
	claims := &Claims{
		UserID:    user.UserID,
		Username:  user.Username,
		Email:     user.Email,
		Role:      user.Role,
		TokenType: tokenType,
		RegisteredClaims: jwt.RegisteredClaims{
			ID:        uuid.New().String(),
			Issuer:    j.issuer,
			Subject:   user.UserID,
			Audience:  []string{"athena-gateway"},
			ExpiresAt: jwt.NewNumericDate(now.Add(duration)),
			NotBefore: jwt.NewNumericDate(now),
			IssuedAt:  jwt.NewNumericDate(now),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(j.secretKey)
}

// ValidateToken 验证令牌
func (j *JWTManager) ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, logging.ErrInvalidSigningMethod
		}
		return j.secretKey, nil
	})

	if err != nil {
		if err == jwt.ErrTokenExpired {
			return nil, logging.ErrTokenExpired
		}
		return nil, logging.ErrInvalidToken
	}

	if claims, ok := token.Claims.(*Claims); ok && token.Valid {
		// 验证发行者
		if claims.Issuer != j.issuer {
			return nil, logging.ErrInvalidToken
		}

		// 验证受众
		if len(claims.Audience) == 0 {
			return nil, logging.ErrInvalidToken
		}
		for _, aud := range claims.Audience {
			if aud == "athena-gateway" {
				goto audienceValid
			}
		}
		return nil, logging.ErrInvalidToken

	audienceValid:

		return claims, nil
	}

	return nil, logging.ErrInvalidToken
}

// RefreshToken 刷新令牌
func (j *JWTManager) RefreshToken(refreshTokenString string) (*TokenPair, error) {
	// 验证刷新令牌
	claims, err := j.ValidateToken(refreshTokenString)
	if err != nil {
		logging.LogError(err, "刷新令牌验证失败")
		return nil, err
	}

	// 确保是刷新令牌
	if claims.TokenType != RefreshToken {
		return nil, logging.ErrInvalidToken
	}

	// 创建用户信息
	user := &UserInfo{
		UserID:   claims.UserID,
		Username: claims.Username,
		Email:    claims.Email,
		Role:     claims.Role,
	}

	// 生成新的令牌对
	return j.GenerateTokenPair(user)
}

// ExtractTokenFromHeader 从请求头中提取令牌
func ExtractTokenFromHeader(authHeader string) (string, error) {
	if authHeader == "" {
		return "", logging.ErrTokenNotProvided
	}

	const bearerPrefix = "Bearer "
	if len(authHeader) < len(bearerPrefix) || authHeader[:len(bearerPrefix)] != bearerPrefix {
		return "", logging.ErrInvalidToken
	}

	return authHeader[len(bearerPrefix):], nil
}

// GenerateRandomKey 生成随机密钥
func GenerateRandomKey(length int) (string, error) {
	bytes := make([]byte, length)
	if _, err := rand.Read(bytes); err != nil {
		return "", fmt.Errorf("生成随机密钥失败: %w", err)
	}
	return base64.URLEncoding.EncodeToString(bytes), nil
}

// IsAdminUser 检查是否为管理员用户
func IsAdminUser(username string) bool {
	cfg := config.GetConfig()
	if cfg == nil {
		return false
	}

	for _, admin := range cfg.Auth.AdminUsers {
		if admin == username {
			return true
		}
	}
	return false
}

// IsPathSkipAuth 检查路径是否跳过认证
func IsPathSkipAuth(path string) bool {
	cfg := config.GetConfig()
	if cfg == nil {
		return false
	}

	for _, skipPath := range cfg.Auth.SkipAuthPaths {
		if path == skipPath {
			return true
		}
	}
	return false
}
