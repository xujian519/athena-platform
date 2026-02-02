-- Athena工作平台数据库安全配置脚本
-- 作者: 徐健
-- 创建日期: 2025-12-13
-- 版本: PostgreSQL 15+

-- ====================================================================
-- 1. 创建安全管理角色
-- ====================================================================

-- 创建安全管理员角色
CREATE ROLE security_admin WITH
    NOLOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    INHERIT
    NOREPLICATION;

-- 创建审计角色
CREATE ROLE audit_admin WITH
    NOLOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    INHERIT
    NOREPLICATION;

-- 创建只读角色
CREATE ROLE readonly_user WITH
    NOLOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    INHERIT
    NOREPLICATION;

-- ====================================================================
-- 2. 数据库用户安全配置
-- ====================================================================

-- 修改默认postgres用户密码（请立即修改）
ALTER USER postgres WITH PASSWORD 'P@ssw0rd!2024#Strong';

-- 创建应用专用用户
CREATE USER athena_app WITH
    PASSWORD 'Ath3n@2024#AppSecure'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    INHERIT
    NOREPLICATION
    CONNECTION LIMIT 100;

-- 创建只读用户
CREATE USER athena_readonly WITH
    PASSWORD 'Ath3n@2024#ReadOnly'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    INHERIT
    NOREPLICATION
    CONNECTION LIMIT 50;

-- 创建备份用户
CREATE USER athena_backup WITH
    PASSWORD 'Ath3n@2024#Backup'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    INHERIT
    NOREPLICATION
    CONNECTION LIMIT 10;

-- ====================================================================
-- 3. 权限分配
-- ====================================================================

-- 授予角色权限
GRANT security_admin TO athena_app;
GRANT audit_admin TO athena_readonly;
GRANT readonly_user TO athena_readonly;

-- 为应用用户授予必要权限
GRANT CONNECT ON DATABASE athena_platform TO athena_app;
GRANT CONNECT ON DATABASE athena_platform TO athena_readonly;
GRANT CONNECT ON DATABASE athena_platform TO athena_backup;

-- 撤销public模式的默认权限
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE athena_platform FROM PUBLIC;

-- ====================================================================
-- 4. 启用行级安全 (Row Level Security)
-- ====================================================================

-- 启用行级安全
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE patents ENABLE ROW LEVEL SECURITY;
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- 创建用户访问策略
CREATE POLICY user_isolation_policy ON users
    FOR ALL
    TO athena_app
    USING (id = current_setting('app.current_user_id')::integer);

-- 创建专利访问策略
CREATE POLICY patent_access_policy ON patents
    FOR ALL
    TO athena_app
    USING (
        created_by = current_setting('app.current_user_id')::integer
        OR
        id IN (
            SELECT patent_id FROM user_patent_access
            WHERE user_id = current_setting('app.current_user_id')::integer
        )
    );

-- 创建API密钥访问策略
CREATE POLICY api_key_policy ON api_keys
    FOR ALL
    TO athena_app
    USING (user_id = current_setting('app.current_user_id')::integer);

-- 只读策略
CREATE POLICY readonly_patent_policy ON patents
    FOR SELECT
    TO athena_readonly
    USING (status = 'published');

-- ====================================================================
-- 5. 数据加密配置
-- ====================================================================

-- 创建加密扩展（需要pgcrypto）
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 创建加密函数
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data text, key text)
RETURNS text AS $$
BEGIN
    RETURN encode(
        encrypt(
            data::bytea,
            key::bytea,
            'aes'
        ),
        'base64'
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION decrypt_sensitive_data(encrypted_data text, key text)
RETURNS text AS $$
BEGIN
    RETURN convert_from(
        decrypt(
            decode(encrypted_data, 'base64'),
            key::bytea,
            'aes'
        ),
        'UTF8'
    );
END;
$$ LANGUAGE plpgsql;

-- 创建哈希函数
CREATE OR REPLACE FUNCTION hash_password(password text, salt text)
RETURNS text AS $$
BEGIN
    RETURN encode(
        digest(password || salt, 'sha256'),
        'hex'
    );
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- 6. 审计日志配置
-- ====================================================================

-- 创建审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    event_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_name TEXT,
    session_id TEXT,
    operation TEXT NOT NULL,
    object_type TEXT,
    object_name TEXT,
    statement TEXT,
    client_ip INET,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT
);

-- 创建审计日志索引
CREATE INDEX idx_audit_logs_event_time ON audit_logs(event_time);
CREATE INDEX idx_audit_logs_user_name ON audit_logs(user_name);
CREATE INDEX idx_audit_logs_operation ON audit_logs(operation);
CREATE INDEX idx_audit_logs_success ON audit_logs(success);

-- 创建审计触发器函数
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        user_name,
        session_id,
        operation,
        object_type,
        object_name,
        statement,
        client_ip,
        success
    ) VALUES (
        current_user,
        current_setting('app.session_id', true),
        TG_OP,
        TG_TABLE_NAME,
        CASE
            WHEN TG_OP = 'DELETE' THEN OLD.id::text
            WHEN TG_OP = 'UPDATE' THEN NEW.id::text
            WHEN TG_OP = 'INSERT' THEN NEW.id::text
            ELSE NULL
        END,
        current_query(),
        inet_client_addr(),
        TRUE
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- 为关键表创建审计触发器
CREATE TRIGGER audit_users_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_patents_trigger
    AFTER INSERT OR UPDATE OR DELETE ON patents
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_api_keys_trigger
    AFTER INSERT OR UPDATE OR DELETE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- ====================================================================
-- 7. 数据库配置参数
-- ====================================================================

-- 设置日志配置
ALTER SYSTEM SET logging_collector = on;
ALTER SYSTEM SET log_directory = 'pg_log';
ALTER SYSTEM SET log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log';
ALTER SYSTEM SET log_rotation_age = '1d';
ALTER SYSTEM SET log_rotation_size = '100MB';
ALTER SYSTEM SET log_min_messages = warning;
ALTER SYSTEM SET log_min_error_statement = error;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_duration = on;
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_lock_waits = on;

-- 设置审计相关配置
ALTER SYSTEM SET pgaudit.log = 'all, -misc';
ALTER SYSTEM SET pgaudit.log_catalog = off;
ALTER SYSTEM SET pgaudit.log_parameter = on;
ALTER SYSTEM SET pgaudit.log_relation = on;
ALTER SYSTEM SET pgaudit.log_statement_once = off;
ALTER SYSTEM SET pgaudit.role = 'audit_admin';

-- 设置安全相关配置
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/var/lib/postgresql/server.crt';
ALTER SYSTEM SET ssl_key_file = '/var/lib/postgresql/server.key';
ALTER SYSTEM SET ssl_ca_file = '/var/lib/postgresql/ca.crt';
ALTER SYSTEM SET password_encryption = 'scram-sha-256';

-- 设置连接安全
ALTER SYSTEM SET listen_addresses = 'localhost';
ALTER SYSTEM SET port = 5432;
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements, pgaudit';

-- ====================================================================
-- 8. 数据库视图（隐藏敏感信息）
-- ====================================================================

-- 创建用户安全视图
CREATE OR REPLACE VIEW users_public AS
SELECT
    id,
    username,
    email,
    created_at,
    updated_at,
    last_login_at,
    is_active,
    is_verified
FROM users;

-- 授予只读用户访问权限
GRANT SELECT ON users_public TO athena_readonly;
GRANT SELECT ON users_public TO readonly_user;

-- 创建专利安全视图
CREATE OR REPLACE VIEW patents_public AS
SELECT
    id,
    title,
    abstract,
    applicant,
    inventor,
    status,
    created_at,
    updated_at
FROM patents
WHERE status = 'published';

GRANT SELECT ON patents_public TO athena_readonly;
GRANT SELECT ON patents_public TO readonly_user;

-- ====================================================================
-- 9. 定期清理任务
-- ====================================================================

-- 创建清理旧审计日志的函数
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(days_to_keep INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_logs
    WHERE event_time < NOW() - INTERVAL '1 day' * days_to_keep;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 创建定时任务（需要pg_cron扩展）
-- SELECT cron.schedule('cleanup-audit-logs', '0 2 * * *', 'SELECT cleanup_old_audit_logs();');

-- ====================================================================
-- 10. 备份恢复策略
-- ====================================================================

-- 创建备份角色
CREATE ROLE backup_role WITH
    NOLOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    INHERIT
    NOREPLICATION;

GRANT backup_role TO athena_backup;

-- 授予备份权限
GRANT CONNECT ON DATABASE athena_platform TO backup_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_role;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup_role;

-- 创建备份函数
CREATE OR REPLACE FUNCTION create_backup(backup_path TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    EXECUTE format('COPY (SELECT * FROM %I) TO %L WITH CSV HEADER', 'users', backup_path || '/users.csv');
    EXECUTE format('COPY (SELECT * FROM %I) TO %L WITH CSV HEADER', 'patents', backup_path || '/patents.csv');
    EXECUTE format('COPY (SELECT * FROM %I) TO %L WITH CSV HEADER', 'cases', backup_path || '/cases.csv');
    EXECUTE format('COPY (SELECT * FROM %I) TO %L WITH CSV HEADER', 'api_keys', backup_path || '/api_keys.csv');

    RETURN TRUE;
EXCEPTION WHEN OTHERS THEN
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- 11. 监控和告警
-- ====================================================================

-- 创建监控视图
CREATE OR REPLACE VIEW database_security_status AS
SELECT
    'failed_login_attempts' as metric,
    COUNT(*) as value
FROM audit_logs
WHERE operation = 'LOGIN' AND success = false AND event_time > NOW() - INTERVAL '1 hour'

UNION ALL

SELECT
    'sensitive_operations' as metric,
    COUNT(*) as value
FROM audit_logs
WHERE object_type IN ('users', 'api_keys')
    AND event_time > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'active_connections' as metric,
    COUNT(*) as value
FROM pg_stat_activity
WHERE state = 'active';

-- 授权访问监控视图
GRANT SELECT ON database_security_status TO athena_readonly;

-- ====================================================================
-- 执行完成提示
-- ====================================================================

-- 输出配置完成信息
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '数据库安全配置已完成';
    RAISE NOTICE '========================================';
    RAISE NOTICE '请执行以下操作：';
    RAISE NOTICE '1. 修改所有默认密码';
    RAISE NOTICE '2. 配置SSL证书';
    RAISE NOTICE '3. 重启PostgreSQL服务';
    RAISE NOTICE '4. 验证安全配置';
    RAISE NOTICE '5. 设置定期备份';
    RAISE NOTICE '========================================';
END $$;