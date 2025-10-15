-- 创建数据库（如果环境变量已指定可选）
CREATE DATABASE IF NOT EXISTS license_db;
USE license_db;

-- 创建表
CREATE TABLE IF NOT EXISTS devices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY, -- 主键
    system_uuid CHAR(36) NOT NULL,        -- 系统 UUID
    baseboard_serial VARCHAR(64) NOT NULL,-- 主板序列号
    disk_serial VARCHAR(64) NOT NULL,     -- 磁盘序列号
    device_model VARCHAR(32),             -- 设备型号
    manufacturer_id VARCHAR(32),          -- 制造商 ID
    iso_date CHAR(4),                     -- 生产日期（ISO 格式）
    usn VARCHAR(32) NOT NULL,             -- 唯一序列号
    public_key TEXT,                      -- 公钥 PEM 格式
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, -- 更新时间
    UNIQUE KEY uq_system_uuid (system_uuid), -- 唯一约束
    UNIQUE KEY uq_baseboard_serial (baseboard_serial), -- 唯一约束
    UNIQUE KEY uq_disk_serial (disk_serial), -- 唯一约束
    UNIQUE KEY uq_usn (usn) -- 唯一约束
);
