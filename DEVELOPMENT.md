# 开发指南

本文档面向开发者，介绍如何进行本地开发和贡献代码。

## 开发环境设置

### 1. 克隆项目

```bash
git clone <repository-url>
cd license_server
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动 MySQL（开发环境）

```bash
docker run -d \
  --name dev_mysql \
  -e MYSQL_ROOT_PASSWORD=dev_password \
  -e MYSQL_DATABASE=license_db \
  -e MYSQL_USER=dev_user \
  -e MYSQL_PASSWORD=dev_password \
  -p 3306:3306 \
  -v $(pwd)/mysql/mysql-init:/docker-entrypoint-initdb.d \
  mysql:8.0
```

### 5. 配置开发环境

创建 `server.conf`:

```ini
[db]
host = localhost
port = 3306
user = dev_user
password = dev_password
dbname = license_db

[server]
host = 0.0.0.0
port = 2712
debug = true  # 开发环境启用调试
```

### 6. 运行服务

```bash
python main.py
```

## 项目结构

```
license_server/
├── main.py           # FastAPI 主应用，定义 API 路由
├── models.py         # Pydantic 数据模型
├── mana.py           # 业务逻辑管理模块
├── db.py             # 数据库操作封装
├── logger.py         # 日志模块
├── server.conf       # 配置文件
└── requirements.txt  # Python 依赖
```

## 核心模块说明

### main.py

主应用入口，定义以下 API 端点：

- `GET /` - 根路径，返回欢迎信息
- `GET /health` - 健康检查
- `POST /register` - 设备注册
- `POST /verify-signature` - 签名验证

### models.py

定义所有数据模型：

- `Device` - 设备信息模型
- `RegisterRequest` - 注册请求模型
- `RegisterResponse` - 注册响应模型
- `VerifySignatureRequest` - 签名验证请求模型
- `VerifySignatureResponse` - 签名验证响应模型

### mana.py

业务逻辑模块，包含：

- `generate_usn()` - 生成唯一序列号
- `register_device()` - 注册设备
- `check_device_registered()` - 检查设备是否已注册
- `verify_signature1()` - 验证签名

### db.py

数据库操作封装：

- `LicenseDB` - 数据库连接管理类
- `init()` - 初始化连接池
- `execute()` - 执行 SQL
- `query()` - 查询数据

## 开发流程

### 1. 创建功能分支

```bash
git checkout -b feature/new-feature
```

### 2. 编写代码

遵循 Python PEP 8 编码规范。

### 3. 测试

```bash
# 运行测试（如果有）
pytest

# 手动测试 API
curl -X POST http://localhost:2712/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_model": "TEST-001",
    "manufacturer_id": "MFG-001",
    "system_uuid": "test-uuid",
    "baseboard_serial": "test-baseboard",
    "disk_serial": "test-disk",
    "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
  }'
```

### 4. 提交代码

```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

### 5. 创建 Pull Request

在 GitHub 上创建 PR，等待代码审查。

## API 测试

### 使用 curl

```bash
# 健康检查
curl http://localhost:2712/health

# 注册设备
curl -X POST http://localhost:2712/register \
  -H "Content-Type: application/json" \
  -d @test_register.json

# 验证签名
curl -X POST http://localhost:2712/verify-signature \
  -H "Content-Type: application/json" \
  -d @test_verify.json
```

### 使用 Python requests

```python
import requests

# 注册
response = requests.post(
    "http://localhost:2712/register",
    json={
        "device_model": "TEST-001",
        "manufacturer_id": "MFG-001",
        "system_uuid": "test-uuid",
        "baseboard_serial": "test-baseboard",
        "disk_serial": "test-disk",
        "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
    }
)
print(response.json())
```

## 调试

### 启用调试日志

在 `server.conf` 中设置：

```ini
[server]
debug = true
```

### 使用 VS Code 调试

创建 `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "main:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "2712"
            ],
            "jinja": true
        }
    ]
}
```

## 数据库管理

### 连接数据库

```bash
docker exec -it dev_mysql mysql -u dev_user -p
```

### 查看设备表

```sql
USE license_db;
SELECT * FROM devices;
```

### 清空测试数据

```sql
TRUNCATE TABLE devices;
```

## 代码风格

### 使用 Black 格式化

```bash
pip install black
black *.py
```

### 使用 flake8 检查

```bash
pip install flake8
flake8 *.py
```

### 使用 mypy 类型检查

```bash
pip install mypy
mypy *.py
```

## 贡献指南

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构
- `test:` 测试
- `chore:` 构建/工具

示例：

```
feat: add device status query endpoint
fix: correct USN generation logic
docs: update API documentation
```

### 代码审查清单

- [ ] 代码遵循 PEP 8 规范
- [ ] 添加了必要的注释
- [ ] 更新了相关文档
- [ ] 测试通过
- [ ] 没有引入安全漏洞

## 性能分析

### 使用 cProfile

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 你的代码

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats()
```

### 使用 line_profiler

```bash
pip install line_profiler
kernprof -l -v your_script.py
```

## 常见问题

### Q: 数据库连接失败

A: 检查 MySQL 容器是否运行，配置是否正确。

### Q: 模块导入错误

A: 确保虚拟环境已激活，依赖已安装。

### Q: 端口被占用

A: 使用 `lsof -i :2712` 查找占用进程。

## 参考资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Pydantic 文档](https://pydantic-docs.helpmanual.io/)
- [aiomysql 文档](https://aiomysql.readthedocs.io/)
- [Python asyncio 文档](https://docs.python.org/3/library/asyncio.html)
