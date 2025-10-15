# 脱敏说明

此项目为开源版本，已对以下敏感信息进行脱敏处理：

## 已脱敏的内容

### 1. 数据库凭据
- ❌ 原密码已移除
- ✅ 替换为 `your_secure_password_here`
- 📁 影响文件：
  - `server.conf` → 改为 `server.conf.example`
  - `docker/docker-compose.yml` → 保留示例版本

### 2. 域名和 IP 地址
- ❌ 原域名 `license.lzwcai.com` 已移除
- ✅ 替换为 `license.example.com`
- ❌ 原 IP 白名单已移除
- ✅ 改为示例注释
- 📁 影响文件：
  - `license.lzwcai.com.conf` → 改名为 `license.example.com.conf`

### 3. 其他敏感配置
- MySQL root 密码
- MySQL 用户密码
- 所有与特定公司相关的标识符

## 使用前配置

在使用此项目前，您需要：

1. **复制示例配置文件**
   ```bash
   cp server.conf.example server.conf
   cp docker/docker-compose.yml.example docker/docker-compose.yml
   ```

2. **修改密码**
   - 编辑 `server.conf`，修改数据库密码
   - 编辑 `docker/docker-compose.yml`，修改数据库密码
   - 确保两处密码一致

3. **修改域名（如果使用 Nginx）**
   - 复制 `license.example.com.conf` 到 Nginx 配置目录
   - 修改其中的域名和 IP 白名单

## 配置清单

- [ ] 复制 `server.conf.example` 为 `server.conf`
- [ ] 在 `server.conf` 中设置数据库密码
- [ ] 复制 `docker/docker-compose.yml.example` 为 `docker/docker-compose.yml`
- [ ] 在 `docker-compose.yml` 中设置数据库密码
- [ ] 确保两个文件中的密码一致
- [ ] （可选）配置 Nginx 反向代理
- [ ] （可选）配置 SSL 证书

## 安全提示

⚠️ **重要提醒**：

1. **切勿将 `server.conf` 提交到版本控制系统**（已在 `.gitignore` 中）
2. **使用强密码**（至少 16 位，包含大小写字母、数字和特殊字符）
3. **生产环境务必启用 HTTPS**
4. **配置防火墙和 IP 白名单**
5. **定期备份数据库**

## 生成强密码

```bash
# 使用 openssl 生成 32 位随机密码
openssl rand -base64 32

# 或使用 pwgen
pwgen -s 32 1
```

## 文件对照表

| 原文件 | 脱敏后文件 | 说明 |
|--------|-----------|------|
| `server.conf` | `server.conf.example` | 配置示例，需复制并修改 |
| `docker-compose.yml` | `docker-compose.yml.example` | 配置示例，需复制并修改 |
| `license.lzwcai.com.conf` | `license.example.com.conf` | Nginx 配置示例 |

## 验证脱敏

您可以使用以下命令验证项目中不包含敏感信息：

```bash
# 搜索可能的敏感信息
grep -r "Lzwc" .
grep -r "lzwcai" .
grep -r "183.239" .

# 应该没有结果（或只在此说明文件中出现）
```

## 完整部署指南

请参阅：
- `README.md` - 快速开始指南
- `DEPLOYMENT.md` - 生产环境部署详细说明
- `DEVELOPMENT.md` - 开发环境设置和贡献指南
