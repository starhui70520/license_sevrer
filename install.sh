#!/bin/bash

# License Server 安装脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker
if ! command -v docker &> /dev/null; then
    print_error "未找到 Docker"
    exit 1
fi

# 检查镜像
if ! docker images | grep -q "license-server"; then
    print_error "未找到 license-server 镜像，请先运行 ./build.sh"
    exit 1
fi

# 创建网络
if ! docker network ls | grep -q "net"; then
    print_info "创建 Docker 网络..."
    docker network create net
fi

# 创建数据目录
print_info "创建数据目录..."
mkdir -p mysql/data mysql/mysql-init

# 启动服务
print_info "启动服务..."
cd docker
docker compose up -d

print_info "服务启动成功！"
print_info "查看状态: docker compose ps"
print_info "查看日志: docker compose logs -f"