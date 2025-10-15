# License Server

基于 FastAPI 的许可证注册服务，用于管理设备注册、公钥存储和签名验证。

## 功能特性

- 🔐 设备注册与唯一序列号（USN）生成
- 🔑 客户端公钥管理
- ✅ 数字签名验证
- 🗄️ MySQL 数据库持久化
- 🐳 Docker 容器化部署

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd license_server
```

### 2. 配置服务

复制配置文件并修改密码：

```bash
cp server.conf.example server.conf
cp docker/docker-compose.yml.example docker/docker-compose.yml
```

编辑 `server.conf`：

```ini
[db]
host = license_mysql
port = 3306
user = license_user
password = your_secure_password_here  # 修改为强密码
dbname = license_db
```

编辑 `docker/docker-compose.yml`，修改数据库密码（需与 server.conf 一致）：

```yaml
environment:
  MYSQL_ROOT_PASSWORD: "your_root_password_here"
  MYSQL_PASSWORD: "your_secure_password_here"  # 与 server.conf 一致
```

### 3. 构建并启动

```bash
./build.sh
./install.sh
```

### 4. 验证

```bash
curl http://localhost:2712/health
```

## API 接口

### 健康检查
```
GET /health
```

### 设备注册
```
POST /register
Content-Type: application/json

{
  "device_model": "MODEL-001",
  "manufacturer_id": "MFG-001",
  "system_uuid": "uuid",
  "baseboard_serial": "serial",
  "disk_serial": "serial",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
}
```

### 验证签名
```
POST /verify-signature
Content-Type: application/json

{
  "usn": "MODEL-MFG-2501-000001",
  "message": "message to verify",
  "signature_b64": "base64_signature"
}
```

## 数据库表结构

```sql
CREATE TABLE devices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    system_uuid CHAR(36) NOT NULL UNIQUE,
    baseboard_serial VARCHAR(64) NOT NULL UNIQUE,
    disk_serial VARCHAR(64) NOT NULL UNIQUE,
    device_model VARCHAR(32),
    manufacturer_id VARCHAR(32),
    iso_date CHAR(4),
    usn VARCHAR(32) NOT NULL UNIQUE,
    public_key TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 管理命令

```bash
# 查看日志
cd docker && docker compose logs -f

# 停止服务
./done.sh

# 重启服务
cd docker && docker compose restart
```

## 配置 Nginx（可选）

参考 `license.example.com.conf` 配置反向代理和 HTTPS。

## 安全建议

- ⚠️ 部署前务必修改默认密码
- 🔒 生产环境启用 HTTPS
- 🛡️ 配置防火墙和 IP 白名单
- 💾 定期备份数据库

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 MySQL
docker run -d --name dev_mysql \
  -e MYSQL_ROOT_PASSWORD=dev_pass \
  -e MYSQL_DATABASE=license_db \
  -p 3306:3306 mysql:8.0

# 运行服务
python main.py
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
