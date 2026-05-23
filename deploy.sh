#!/bin/bash

# ATradeReview 部署脚本

set -e

echo "🚀 开始部署 ATradeReview..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 自动检测后端容器名（兼容 docker-compose v1/v2 命名差异）
detect_backend_container() {
    docker ps --format '{{.Names}}' | grep -E '(^|[-_])backend([-_]|$)' | head -n 1
}

# 部署前自动备份
BACKUP_DIR="./backup"
BACKEND_CONTAINER="$(detect_backend_container || true)"

if [ -n "$BACKEND_CONTAINER" ]; then
    echo "💾 检测到运行中的后端容器: $BACKEND_CONTAINER，开始备份数据..."
    mkdir -p "$BACKUP_DIR"
    TS="$(date +%Y%m%d_%H%M%S)"

    # 优先备份新路径 /app/data，其次兼容旧路径 /app
    for f in users.db industries.db watchlist.json; do
        if docker exec "$BACKEND_CONTAINER" test -f "/app/data/$f" 2>/dev/null; then
            docker cp "$BACKEND_CONTAINER:/app/data/$f" "$BACKUP_DIR/${f}_${TS}" \
                && echo "  ✓ 已备份 /app/data/$f -> $BACKUP_DIR/${f}_${TS}"
        elif docker exec "$BACKEND_CONTAINER" test -f "/app/$f" 2>/dev/null; then
            docker cp "$BACKEND_CONTAINER:/app/$f" "$BACKUP_DIR/${f}_${TS}" \
                && echo "  ✓ 已备份 /app/$f -> $BACKUP_DIR/${f}_${TS}"
        fi
    done

    # 清理 30 天前的备份
    find "$BACKUP_DIR" -name "*.db_*" -mtime +30 -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "*.json_*" -mtime +30 -delete 2>/dev/null || true
else
    echo "ℹ️  未检测到运行中的后端容器，跳过备份（首次部署）"
fi

# 旧数据迁移：若旧 volume 把数据写在 /app 根目录，则迁移到 /app/data
if [ -n "$BACKEND_CONTAINER" ]; then
    NEED_MIGRATE=0
    for f in users.db industries.db watchlist.json; do
        if docker exec "$BACKEND_CONTAINER" sh -c "[ -f /app/$f ] && [ ! -f /app/data/$f ]" 2>/dev/null; then
            NEED_MIGRATE=1
            break
        fi
    done
    if [ "$NEED_MIGRATE" = "1" ]; then
        echo "🔄 检测到旧版数据布局，迁移 /app/*.db -> /app/data/ ..."
        docker exec "$BACKEND_CONTAINER" sh -c "mkdir -p /app/data && for f in users.db industries.db watchlist.json; do [ -f /app/\$f ] && [ ! -f /app/data/\$f ] && cp /app/\$f /app/data/\$f && echo '  ✓ 迁移 '\$f; done" || true
    fi
fi

# 停止并删除旧容器（不删除 volume！）
echo "📦 停止旧容器..."
docker-compose down 2>/dev/null || true

# 构建并启动
echo "🔨 构建镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose up -d

echo ""
echo "✅ 部署完成！"
echo ""
echo "📱 访问地址："
echo "   - 本机: http://localhost"
echo "   - 局域网: http://$(hostname -I 2>/dev/null | awk '{print $1}')"
echo ""
echo "📋 常用命令："
echo "   - 查看日志: docker-compose logs -f"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart"
echo "   - 备份目录: $BACKUP_DIR"
