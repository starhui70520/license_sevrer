#!/bin/bash

# License Server 健康检查脚本

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 检查容器健康状态
check_health() {
    local container=$1
    local status=$(docker inspect "$container" --format='{{.State.Health.Status}}' 2>/dev/null)
    
    if [ -z "$status" ]; then
        echo "not_found"
    else
        echo "$status"
    fi
}

print_info "检查服务健康状态..."
echo ""

# 检查 MySQL
mysql_status=$(check_health "license_mysql")
if [ "$mysql_status" == "healthy" ]; then
    print_info "✓ MySQL:          healthy"
elif [ "$mysql_status" == "not_found" ]; then
    print_error "✗ MySQL:          容器不存在"
else
    print_warn "⚠ MySQL:          $mysql_status"
fi

# 检查 License Server
server_status=$(check_health "license-server")
if [ "$server_status" == "healthy" ]; then
    print_info "✓ License Server: healthy"
elif [ "$server_status" == "not_found" ]; then
    print_error "✗ License Server: 容器不存在"
else
    print_warn "⚠ License Server: $server_status"
fi

echo ""

# 判断总体状态
if [ "$mysql_status" == "healthy" ] && [ "$server_status" == "healthy" ]; then
    print_info "所有服务运行正常！"
    exit 0
else
    print_error "部分服务异常，请检查日志"
    exit 1
fi