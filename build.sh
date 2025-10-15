#!/bin/bash

# License Server Nuitka 打包脚本
# 用途：将 Python 项目编译成独立可执行文件

set -e  # 遇到错误立即退出

# 颜色输出定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_info "开始构建 License Server..."

# 0. 读取配置文件中的端口
CONFIG_FILE="server.conf"
if [ ! -f "$CONFIG_FILE" ]; then
    print_error "配置文件 $CONFIG_FILE 不存在"
    exit 1
fi

# 从配置文件中提取端口号
SERVER_PORT=$(grep -A 2 '\[server\]' "$CONFIG_FILE" | grep '^port' | awk -F '=' '{print $2}' | tr -d ' ')

if [ -z "$SERVER_PORT" ]; then
    print_error "无法从配置文件读取端口号"
    exit 1
fi

print_info "从配置文件读取到端口: $SERVER_PORT"

# 1. 检查 Python 版本
print_info "检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    print_error "未找到 python3，请先安装 Python 3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
print_info "Python 版本: $PYTHON_VERSION"

# 1.5 检查并安装系统依赖
print_info "检查系统依赖..."

# 检查 patchelf
if ! command -v patchelf &> /dev/null; then
    print_warn "未找到 patchelf，尝试安装..."
    
    # 检测系统包管理器并安装
    if command -v apt &> /dev/null; then
        print_info "使用 apt 安装 patchelf..."
        sudo apt update && sudo apt install -y patchelf
    elif command -v dnf &> /dev/null; then
        print_info "使用 dnf 安装 patchelf..."
        sudo dnf install -y patchelf
    elif command -v yum &> /dev/null; then
        print_info "使用 yum 安装 patchelf..."
        sudo yum install -y patchelf
    else
        print_error "无法自动安装 patchelf，请手动安装："
        print_error "  Ubuntu/Debian: sudo apt install patchelf"
        print_error "  CentOS/RHEL: sudo yum install patchelf"
        print_error "  Fedora: sudo dnf install patchelf"
        exit 1
    fi
    
    # 再次检查是否安装成功
    if ! command -v patchelf &> /dev/null; then
        print_error "patchelf 安装失败"
        exit 1
    fi
    print_info "patchelf 安装成功"
else
    print_info "patchelf 已安装"
fi

# 检查 gcc/g++（Nuitka 编译需要）
if ! command -v gcc &> /dev/null; then
    print_warn "未找到 gcc，Nuitka 编译需要 C 编译器"
    print_warn "建议安装: sudo apt install build-essential"
fi

# 2. 创建临时虚拟环境
VENV_DIR=".venv_build"
print_info "创建临时虚拟环境: $VENV_DIR"

if [ -d "$VENV_DIR" ]; then
    print_warn "虚拟环境已存在，删除旧环境..."
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"
print_info "虚拟环境创建成功"

# 3. 激活虚拟环境
print_info "激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 4. 升级 pip
print_info "升级 pip..."
pip install --upgrade pip

# 5. 安装依赖
print_info "根据 requirements.txt 安装依赖..."
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt 文件不存在"
    deactivate
    exit 1
fi

pip install -r requirements.txt
print_info "依赖安装完成"

# 6. 使用 Nuitka 编译
print_info "开始使用 Nuitka 编译..."

# 创建输出目录
OUTPUT_DIR="dist"
if [ -d "$OUTPUT_DIR" ]; then
    print_warn "输出目录已存在，清理旧文件..."
    rm -rf "$OUTPUT_DIR"
fi
mkdir -p "$OUTPUT_DIR"

# Nuitka 编译参数说明：
# --standalone: 创建独立可执行文件，包含所有依赖
# --onefile: 将所有内容打包成单个可执行文件
# --python-flag=no_site: 不包含 site-packages
# --enable-plugin=anti-bloat: 减少不必要的依赖
# --include-module: 显式包含模块
# --include-data-dir: 包含数据文件
# --output-dir: 输出目录
# --assume-yes-for-downloads: 自动下载需要的依赖

print_info "编译配置："
print_info "  - 模式: 独立可执行文件 (standalone + onefile)"
print_info "  - 入口文件: main.py"
print_info "  - 输出目录: $OUTPUT_DIR"

python -m nuitka \
    --standalone \
    --onefile \
    --assume-yes-for-downloads \
    --output-dir="$OUTPUT_DIR" \
    --output-filename=license_server \
    --enable-plugin=anti-bloat \
    --include-module=models \
    --include-module=mana \
    --include-module=db \
    --include-module=logger \
    --include-module=fastapi \
    --include-module=uvicorn \
    --include-module=aiomysql \
    --include-module=cryptography \
    --include-module=pydantic \
    --follow-imports \
    --python-flag=no_site \
    --show-progress \
    --show-memory \
    main.py

if [ $? -eq 0 ]; then
    print_info "编译成功！"
else
    print_error "编译失败！"
    deactivate
    exit 1
fi

# 7. 复制配置文件到输出目录
print_info "复制配置文件..."
if [ -f "server.conf" ]; then
    cp server.conf "$OUTPUT_DIR/"
    print_info "已复制 server.conf"
fi

# 9. 显示可执行文件信息
print_info "可执行文件信息："
ls -lh "$OUTPUT_DIR"/license_server
file "$OUTPUT_DIR"/license_server

# 10. 停用虚拟环境
deactivate
print_info "虚拟环境已停用"

# 11. 清理临时虚拟环境
print_info "清理临时虚拟环境..."
rm -rf "$VENV_DIR"
print_info "虚拟环境清理完成"

# 12. 创建临时构建目录
print_info "创建临时构建目录..."
BUILD_TEMP_DIR=".build_temp"

if [ -d "$BUILD_TEMP_DIR" ]; then
    rm -rf "$BUILD_TEMP_DIR"
fi

mkdir -p "$BUILD_TEMP_DIR"

# 复制可执行文件
if [ -f "$OUTPUT_DIR/license_server" ]; then
    print_info "复制可执行文件到临时目录..."
    cp "$OUTPUT_DIR/license_server" "$BUILD_TEMP_DIR/"
    chmod +x "$BUILD_TEMP_DIR/license_server"
else
    print_error "未找到可执行文件: $OUTPUT_DIR/license_server"
    exit 1
fi

# 复制配置文件
if [ -f "server.conf" ]; then
    print_info "复制配置文件到临时目录..."
    cp server.conf "$BUILD_TEMP_DIR/"
else
    print_error "未找到 server.conf 配置文件"
    exit 1
fi

# 13. 创建临时 Dockerfile（使用读取到的端口）
print_info "创建临时 Dockerfile..."
print_info "Dockerfile 配置端口: $SERVER_PORT"
cat > "$BUILD_TEMP_DIR/Dockerfile" << EOF
FROM ubuntu:22.04

WORKDIR /app

COPY license_server /app/
COPY server.conf /app/

RUN chmod +x /app/license_server
RUN apt-get update && apt-get install -y curl
EXPOSE ${SERVER_PORT}

CMD ["/app/license_server"]
EOF

# 14. 构建 Docker 镜像
print_info "开始构建 Docker 镜像..."
docker build -t license-server:latest "$BUILD_TEMP_DIR"

if [ $? -eq 0 ]; then
    print_info "Docker 镜像构建成功！"
else
    print_error "Docker 镜像构建失败！"
    exit 1
fi

# 15. 清理所有临时文件
print_info "清理所有临时文件..."
rm -rf "$BUILD_TEMP_DIR"
rm -rf "$OUTPUT_DIR"

# 16. 显示最终结果
print_info "================================================"
print_info "构建完成！"
print_info ""
print_info "🐳 Docker 镜像: license-server:latest"
print_info "📡 监听端口: $SERVER_PORT"
print_info ""
print_info "查看镜像信息:"
docker images | grep license-server
print_info ""
print_info "启动命令 (自行编写脚本):"
print_info "  docker run -d --name license-server -p $SERVER_PORT:$SERVER_PORT license-server:latest"
print_info "  或使用 docker compose: docker compose up -d"
print_info ""
print_info "导出镜像:"
print_info "  docker save license-server:latest | gzip > license-server.tar.gz"
print_info "================================================"
