# ATradeReview 部署指南

## 腾讯云服务器配置

### 1. 购买服务器
- 推荐配置：2核4G（约￥50/月）
- 操作系统：Ubuntu 20.04 LTS
- 地域：离用户最近的城市

### 2. 安全组配置
在腾讯云控制台 → 安全组 → 添加入站规则：
| 协议 | 端口 | 来源 |
|------|------|------|
| TCP | 80 | 0.0.0.0/0 |
| TCP | 443 | 0.0.0.0/0 |
| TCP | 22 | 您的IP地址 |

### 3. 安装Docker
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com | sudo sh

# 添加当前用户到docker组
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo apt install -y docker-compose

# 重新登录使生效
```

### 4. 部署应用
```bash
# 上传代码到服务器
scp -r ./ATradeReview root@您的服务器IP:~/

# SSH登录服务器
ssh root@您的服务器IP

# 进入目录并部署
cd ATradeReview
./deploy.sh
```

### 5. 手机访问
部署完成后，手机浏览器访问：`http://您的服务器IP`

## 配置HTTPS（推荐）

### 使用Let's Encrypt免费证书
```bash
# 安装certbot
sudo apt install -y certbot

# 如果有域名，获取证书
sudo certbot certonly --standalone -d yourdomain.com

# 配置Nginx使用HTTPS（修改frontend/nginx.conf）
```

## 常见问题

### Q: 手机无法访问？
检查安全组是否开放80端口。

### Q: 数据获取失败？
服务器需要能访问东方财富API，检查网络。

### Q: 如何更新？
```bash
cd ATradeReview
git pull
docker-compose down
docker-compose build
docker-compose up -d
```
