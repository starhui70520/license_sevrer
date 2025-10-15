<<<<<<< HEAD
# license_sevrer
license_sevrer
=======
# License Server

基于 FastAPI 的许可证注册服务，用于管理设备注册、公钥存储和签名验证。

## 功能特性

- 🔐 设备注册与唯一序列号（USN）生成
- 🔑 客户端公钥管理
- ✅ 数字签名验证
- 🗄️ MySQL 数据库持久化
- 🐳 Docker 容器化部署
- 📊 健康检查接口

## 项目结构

```
license_server/
├── main.py                    # FastAPI 主应用
├── models.py                  # 数据模型定义
├── mana.py                    # 业务逻辑管理
├── db.py                      # 数据库操作封装
├── logger.py                  # 日志模块
├── server.conf                # 服务配置文件
├── requirements.txt           # Python 依赖
├── build.sh                   # Docker 构建脚本
├── install.sh                 # 安装脚本
├── done.sh                    # 停止脚本
├── docker/
│   └── docker-compose.yml    # Docker Compose 配置
└── mysql/
    └── mysql-init/
        └── init.sql          # 数据库初始化脚本
```

## 快速开始

### 前置要求

- Docker 和 Docker Compose
- Python 3.9+ (如果本地开发)

### 使用 Docker 部署（推荐）

1. **克隆项目**

```bash
git clone <repository-url>
cd license_server
```

2. **配置服务**

编辑 `server.conf` 文件，修改数据库连接信息：

```ini
[db]
host = license_mysql
port = 3306
user = your_db_user
password = your_db_password
dbname = license_db

[server]
host = 0.0.0.0
port = 2712
debug = false
```

编辑 `docker/docker-compose.yml`，修改数据库密码：

```yaml
environment:
  MYSQL_ROOT_PASSWORD: "your_root_password"
  MYSQL_DATABASE: "license_db"
  MYSQL_USER: "your_db_user"
  MYSQL_PASSWORD: "your_db_password"
```

3. **构建 Docker 镜像**

```bash
./build.sh
```

4. **启动服务**

```bash
./install.sh
```

5. **验证服务**

```bash
curl http://localhost:2712/health
```

### 本地开发

1. **安装依赖**

```bash
pip install -r requirements.txt
```

2. **启动 MySQL**

```bash
docker run -d \
  --name license_mysql \
  -e MYSQL_ROOT_PASSWORD=your_password \
  -e MYSQL_DATABASE=license_db \
  -e MYSQL_USER=your_user \
  -e MYSQL_PASSWORD=your_password \
  -p 3306:3306 \
  mysql:8.0
```

3. **运行服务**

```bash
python main.py
```

## API 文档

### 1. 健康检查

```
GET /health
```

响应：
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00"
}
```

### 2. 设备注册

```
POST /register
```

请求体：
```json
{
  "device_model": "MODEL-001",
  "manufacturer_id": "MFG-001",
  "system_uuid": "123e4567-e89b-12d3-a456-426614174000",
  "baseboard_serial": "BSN123456",
  "disk_serial": "DSN789012",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
}
```

响应：
```json
{
  "usn": "MODEL-MFG-2501-000001",
  "message": "注册成功"
}
```

### 3. 验证签名

```
POST /verify-signature
```

请求体：
```json
{
  "usn": "MODEL-MFG-2501-000001",
  "message": "要验证的消息内容",
  "signature_b64": "base64编码的签名"
}
```

响应：
```json
{
  "valid": true,
  "detail": "签名有效"
}
```

## 数据库表结构

### devices 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| system_uuid | CHAR(36) | 系统 UUID，唯一 |
| baseboard_serial | VARCHAR(64) | 主板序列号，唯一 |
| disk_serial | VARCHAR(64) | 磁盘序列号，唯一 |
| device_model | VARCHAR(32) | 设备型号 |
| manufacturer_id | VARCHAR(32) | 制造商 ID |
| iso_date | CHAR(4) | 生产日期（YYWW 格式） |
| usn | VARCHAR(32) | 唯一序列号，唯一 |
| public_key | TEXT | 公钥 PEM 格式 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 配置说明

### server.conf

- `[db]` 数据库配置
  - `host`: 数据库主机地址
  - `port`: 数据库端口
  - `user`: 数据库用户名
  - `password`: 数据库密码
  - `dbname`: 数据库名称

- `[server]` 服务配置
  - `host`: 服务监听地址
  - `port`: 服务端口
  - `debug`: 调试模式

## 管理命令

### 查看服务状态

```bash
cd docker
docker compose ps
```

### 查看日志

```bash
cd docker
docker compose logs -f license-server
```

### 停止服务

```bash
./done.sh
```

### 重启服务

```bash
cd docker
docker compose restart
```

## 安全建议

1. **修改默认密码**：部署前务必修改数据库密码
2. **使用 HTTPS**：生产环境建议配置 Nginx 反向代理并启用 SSL
3. **IP 白名单**：配置防火墙或 Nginx 限制访问 IP
4. **定期备份**：定期备份 MySQL 数据
5. **环境变量**：敏感信息建议使用环境变量而非配置文件

## Nginx 反向代理配置（可选）

参考 `license.example.com.conf` 文件配置 Nginx 反向代理。

## 故障排查

### 服务无法启动

1. 检查端口占用：`netstat -nltp | grep 2712`
2. 检查 Docker 日志：`docker compose logs license-server`
3. 检查数据库连接：确认 MySQL 服务正常运行

### 数据库连接失败

1. 确认 MySQL 容器运行：`docker ps | grep mysql`
2. 检查配置文件中的连接信息
3. 测试数据库连接：`mysql -h localhost -u user -p`

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请提交 Issue。
>>>>>>> ade64e2 (Initial commit: License Server - Open Source Version)
