# 部署指南

本文档详细介绍如何在生产环境中部署 License Server。

## 环境要求

- **操作系统**: Linux (Ubuntu 20.04+ / CentOS 7+ / Debian 10+)
- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **内存**: 至少 2GB
- **磁盘**: 至少 10GB 可用空间

## 部署步骤

### 1. 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# 或
sudo yum update -y  # CentOS

# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 克隆代码

```bash
git clone <repository-url>
cd license_server
```

### 3. 配置服务

#### 3.1 配置数据库密码

复制配置示例文件并修改：

```bash
cp server.conf.example server.conf
cp docker/docker-compose.yml.example docker/docker-compose.yml
```

编辑 `server.conf`:

```ini
[db]
host = license_mysql
port = 3306
user = license_user
password = YOUR_STRONG_PASSWORD_HERE  # 修改此处
dbname = license_db

[server]
host = 0.0.0.0
port = 2712
debug = false
```

编辑 `docker/docker-compose.yml`:

```yaml
environment:
  MYSQL_ROOT_PASSWORD: "YOUR_ROOT_PASSWORD_HERE"  # 修改此处
  MYSQL_DATABASE: "license_db"
  MYSQL_USER: "license_user"
  MYSQL_PASSWORD: "YOUR_STRONG_PASSWORD_HERE"  # 修改此处，需与 server.conf 一致
```

**注意**: 确保两个文件中的密码一致！

#### 3.2 密码强度建议

- 至少 16 个字符
- 包含大小写字母、数字和特殊字符
- 不使用常见密码或字典词汇

生成强密码示例：

```bash
# 使用 openssl 生成 32 位随机密码
openssl rand -base64 32
```

### 4. 构建镜像

```bash
chmod +x build.sh
./build.sh
```

### 5. 启动服务

```bash
chmod +x install.sh
./install.sh
```

### 6. 验证服务

```bash
# 检查容器状态
docker ps

# 测试健康检查
curl http://localhost:2712/health

# 查看日志
cd docker
docker compose logs -f license-server
```

## 配置 Nginx 反向代理（推荐）

### 1. 安装 Nginx

```bash
sudo apt install nginx -y  # Ubuntu/Debian
# 或
sudo yum install nginx -y  # CentOS
```

### 2. 配置反向代理

```bash
sudo cp license.example.com.conf /etc/nginx/sites-available/license
sudo ln -s /etc/nginx/sites-available/license /etc/nginx/sites-enabled/
```

编辑配置文件：

```bash
sudo nano /etc/nginx/sites-available/license
```

修改域名和 IP 白名单：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 修改为你的域名

    # IP 白名单（可选）
    allow 192.168.1.0/24;
    deny all;

    location / {
        proxy_pass http://localhost:2712;
        # ...其他配置
    }
}
```

### 3. 测试并重启 Nginx

```bash
sudo nginx -t
sudo systemctl restart nginx
```

## 配置 HTTPS (Let's Encrypt)

### 1. 安装 Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 2. 获取证书

```bash
sudo certbot --nginx -d your-domain.com
```

### 3. 自动续期

```bash
sudo certbot renew --dry-run
```

## 防火墙配置

### UFW (Ubuntu)

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 2712/tcp  # 如果需要直接访问
sudo ufw enable
```

### Firewalld (CentOS)

```bash
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=2712/tcp
sudo firewall-cmd --reload
```

## 备份策略

### 数据库备份

创建备份脚本 `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backup/mysql"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

docker exec license_mysql mysqldump -u root -pYOUR_ROOT_PASSWORD \
  --databases license_db > $BACKUP_DIR/license_db_$DATE.sql

# 保留最近 7 天的备份
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/license_db_$DATE.sql"
```

添加到 crontab:

```bash
chmod +x backup.sh
crontab -e

# 每天凌晨 2 点备份
0 2 * * * /path/to/backup.sh
```

### 恢复备份

```bash
docker exec -i license_mysql mysql -u root -pYOUR_ROOT_PASSWORD \
  license_db < /backup/mysql/license_db_YYYYMMDD_HHMMSS.sql
```

## 监控和日志

### 查看服务日志

```bash
# 实时查看日志
cd docker
docker compose logs -f license-server

# 查看最近 100 行日志
docker compose logs --tail=100 license-server
```

### 查看数据库日志

```bash
docker compose logs -f mysql
```

### 磁盘空间监控

```bash
# 检查磁盘使用情况
df -h

# 检查 Docker 磁盘使用
docker system df
```

### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看特定容器
docker stats license-server license_mysql
```

## 更新服务

### 更新代码

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
./build.sh

# 重启服务
cd docker
docker compose down
docker compose up -d
```

### 零停机更新

```bash
# 1. 构建新镜像
./build.sh

# 2. 使用滚动更新
cd docker
docker compose up -d --no-deps --build license-server
```

## 故障排查

### 服务无法启动

1. **检查端口占用**
   ```bash
   sudo netstat -nltp | grep 2712
   ```

2. **检查日志**
   ```bash
   docker compose logs license-server
   ```

3. **检查配置文件**
   ```bash
   cat server.conf
   ```

### 数据库连接失败

1. **检查 MySQL 容器**
   ```bash
   docker ps | grep mysql
   docker compose logs mysql
   ```

2. **测试数据库连接**
   ```bash
   docker exec -it license_mysql mysql -u license_user -p
   ```

3. **检查网络连接**
   ```bash
   docker network inspect net
   ```

### 内存不足

```bash
# 清理 Docker 缓存
docker system prune -a

# 重启 Docker 服务
sudo systemctl restart docker
```

## 安全加固

### 1. 禁用 root 远程登录

编辑 `/etc/ssh/sshd_config`:

```
PermitRootLogin no
```

### 2. 配置 Fail2ban

```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. 定期更新系统

```bash
# 设置自动更新（Ubuntu）
sudo apt install unattended-upgrades -y
```

### 4. 限制 Docker API 访问

不要暴露 Docker API 到公网，仅本地访问。

## 性能优化

### 1. MySQL 优化

编辑 `docker-compose.yml`，添加 MySQL 配置:

```yaml
mysql:
  command:
    - --max_connections=200
    - --innodb_buffer_pool_size=512M
```

### 2. 应用层优化

- 调整连接池大小（在 `db.py` 中）
- 启用缓存机制
- 使用 CDN（如果有静态资源）

## 技术支持

如有问题，请：

1. 查看本文档的故障排查部分
2. 查看项目 README.md
3. 提交 GitHub Issue
