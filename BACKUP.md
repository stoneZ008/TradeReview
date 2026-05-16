# 数据备份与维护指南

## Docker Volume 数据持久化说明

本项目使用 Docker 命名卷 (`trade_db`) 持久化数据库文件，避免重新部署时生产数据被覆盖。

---

## 常用维护命令

### 查看 Volume 信息
```bash
# 查看所有 volume
docker volume ls

# 查看 trade_db 详情
docker volume inspect trade-review_trade_db
```

### 备份数据库
```bash
# 创建备份目录
mkdir -p ./backup

# 备份 users.db
docker cp trade-review-backend-1:/app/users.db ./backup/users.db

# 备份 industries.db
docker cp trade-review-backend-1:/app/industries.db ./backup/industries.db

# 备份 watchlist.json
docker cp trade-review-backend-1:/app/watchlist.json ./backup/watchlist.json
```

### 恢复数据库
```bash
# 恢复单个文件
docker cp ./backup/users.db trade-review-backend-1:/app/users.db
docker cp ./backup/industries.db trade-review-backend-1:/app/industries.db

# 重启服务使恢复生效
docker-compose restart backend
```

### 定时备份（推荐）
添加到 crontab 实现每日自动备份：
```bash
crontab -e
```

添加以下内容（每天凌晨 2 点备份）：
```
0 2 * * * cd /path/to/TradeReview && mkdir -p ./backup && docker cp trade-review-backend-1:/app/users.db ./backup/users.db_$(date +\%Y\%m\%d) && docker cp trade-review-backend-1:/app/industries.db ./backup/industries.db_$(date +\%Y\%m\%d)
```

### 清理旧备份
```bash
# 删除 7 天前的备份文件
find ./backup -name "*.db_*" -mtime +7 -delete
```

---

## 部署注意事项

### 全新部署
直接运行部署脚本即可，volume 会自动创建并初始化：
```bash
./deploy.sh
```

### 已有生产数据的迁移
如果已有正在运行的生产环境，按以下步骤迁移：

1. **先备份现有数据**
   ```bash
   mkdir -p ./backup
   docker cp trade-review_backend_1:/app/users.db ./backup/
   docker cp trade-review_backend_1:/app/industries.db ./backup/
   ```

2. **停止服务**
   ```bash
   docker-compose down
   ```

3. **重新部署**
   ```bash
   ./deploy.sh
   ```

4. **验证数据**
   - 登录系统，检查用户和数据是否正常
   - 若数据丢失，使用备份文件恢复

---

## 故障排查

### Volume 挂载异常
```bash
# 查看容器挂载点
docker inspect trade-review-backend-1 | grep Mounts -A 20

# 进入容器检查文件
docker exec -it trade-review-backend-1 ls -la /app/*.db
```

### 部署后数据重置
如果遇到部署后数据重置的情况，可能是 volume 名称不匹配：
1. 检查新容器名称：`docker ps | grep backend`
2. 检查旧 volume 名称：`docker volume ls | grep trade`
3. 从旧 volume 备份数据后恢复

---

## 数据安全建议

1. **部署前必须备份** - 每次部署前执行备份命令
2. **定期备份** - 配置 crontab 自动备份
3. **异地备份** - 定期将备份文件下载到其他机器
4. **版本升级** - 大版本升级前先做完整备份
