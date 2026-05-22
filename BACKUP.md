# 数据备份与维护指南

## Docker Volume 数据持久化说明

本项目使用 Docker 命名卷 (`trade_db`) 持久化数据库文件，避免重新部署时生产数据被覆盖。

数据文件统一存放在容器的 `/app/data/` 目录中（由环境变量 `DATA_DIR` 控制），volume 仅挂载该子目录，不会影响代码层。

包含的数据文件：
- `/app/data/users.db` — 用户、订阅、自选股快照等
- `/app/data/industries.db` — 行业分类
- `/app/data/watchlist.json` — 全局自选股（旧版兼容）

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
docker cp trade-review-backend-1:/app/data/users.db ./backup/users.db

# 备份 industries.db
docker cp trade-review-backend-1:/app/data/industries.db ./backup/industries.db

# 备份 watchlist.json
docker cp trade-review-backend-1:/app/data/watchlist.json ./backup/watchlist.json
```

> 提示：`./deploy.sh` 已内置部署前自动备份，会把数据写入 `./backup/<file>_<时间戳>`，保留 30 天。

### 恢复数据库
```bash
# 恢复单个文件
docker cp ./backup/users.db trade-review-backend-1:/app/data/users.db
docker cp ./backup/industries.db trade-review-backend-1:/app/data/industries.db

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
0 2 * * * cd /path/to/TradeReview && mkdir -p ./backup && docker cp trade-review-backend-1:/app/data/users.db ./backup/users.db_$(date +\%Y\%m\%d) && docker cp trade-review-backend-1:/app/data/industries.db ./backup/industries.db_$(date +\%Y\%m\%d)
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

### 已有生产数据的迁移（旧版 → 新版）
如果你之前的 `docker-compose.yml` 把 volume 挂载到 `/app`（而不是 `/app/data`），新版部署脚本会自动：

1. 备份当前数据到 `./backup/`
2. 检测 `/app/*.db` 旧路径，将其复制到 `/app/data/*.db`
3. 重新构建并启动服务（新代码会从 `/app/data/` 读取）

只需运行：
```bash
./deploy.sh
```

如出现异常，按 `./backup/` 中带时间戳的文件回滚即可。

### Schema 自动迁移
后端启动时会调用 `migrate_user_db()` 与 `migrate_industry_db()`，自动为已有表补齐缺失列（基于 `db_migrate.ensure_columns`）。
> 注意：SQLite 的 `ALTER TABLE ADD COLUMN` 不能加 `UNIQUE/PRIMARY KEY/CURRENT_TIMESTAMP DEFAULT`，迁移工具会自动剥离这些不兼容子句；如需结构性变更（删除列、修改类型），仍需手工编写迁移脚本。

---

## 故障排查

### Volume 挂载异常
```bash
# 查看容器挂载点
docker inspect trade-review-backend-1 | grep Mounts -A 20

# 进入容器检查文件
docker exec -it trade-review-backend-1 ls -la /app/data/
```

### 部署后数据重置
如果遇到部署后数据重置的情况，可能是 volume 名称不匹配：
1. 检查新容器名称：`docker ps | grep backend`
2. 检查旧 volume 名称：`docker volume ls | grep trade`
3. 从旧 volume 备份数据后恢复

---

## 数据安全建议

1. **部署前必须备份** - `./deploy.sh` 会自动备份；手工部署时执行备份命令
2. **定期备份** - 配置 crontab 自动备份
3. **异地备份** - 定期将备份文件下载到其他机器
4. **版本升级** - 大版本升级前先做完整备份
