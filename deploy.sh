#!/bin/bash

# ATradeReview 部署脚本

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

# 停止并删除旧容器
echo "📦 停止旧容器..."
docker-compose down 2>/dev/null

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
echo "   - 局域网: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "📋 常用命令："
echo "   - 查看日志: docker-compose logs -f"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart"
