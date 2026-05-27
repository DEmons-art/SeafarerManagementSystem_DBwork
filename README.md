# 出海船员管理系统

这是一个保留原版功能范围的出海船员管理系统：静态 HTML 前端、FastAPI 后端、MySQL 数据库。

## 主入口改动

后端主入口在 `backend/app/main.py`。

当前 `main.py` 主要负责：

- 创建 FastAPI 应用：`create_app()`
- 注册 CORS，允许前端静态页面访问后端接口
- 使用 UTF-8 JSON 响应，避免中文提示乱码
- 统一处理请求参数错误和业务错误，返回 `{ success, message }` 格式
- 把数据库连接对象挂到 `app.state.database`
- 挂载 `backend/app/api.py` 中的接口路由

业务 SQL 和状态流转不写在 `main.py`，集中在 `backend/app/services.py`。例如：

- 新增船员写入 `crew_info`
- 分配航次写入 `voyage_records`，并把船员设为出海中
- 召回船员时，把进行中的航次更新为 `已抵达`，并记录实际到达时间

## Docker 快速使用

先启动 Docker Desktop，然后在项目根目录执行：

```powershell
docker compose up --build
```

启动后访问：

```text
前端页面：http://localhost:8080
后端接口：http://localhost:3000
接口文档：http://localhost:3000/docs
健康检查：http://localhost:3000/health
```

再次启动已有容器：

```powershell
docker compose up -d
```

停止容器：

```powershell
docker compose down
```

## MySQL 依赖说明

后端依赖 Docker Compose 中的 MySQL 8 镜像：

```yaml
db:
  image: mysql:8.0
```

`backend` 服务不会自己创建数据库进程，它通过环境变量连接 `db` 容器：

```text
SEAFARER_DATABASE_URL=mysql+pymysql://root:123456@db:3306/SeafarerDB?charset=utf8mb4
```

也就是说，正常开发时不要只单独启动后端；需要先让 Docker 里的 MySQL 容器启动并通过健康检查。`docker-compose.yml` 已经配置了：

```text
backend depends_on db: service_healthy
```

## 数据库初始化和重置

初始化脚本是根目录的 `init.sql`，会在 MySQL 容器第一次创建数据卷时自动执行。

如果改了表结构或想重置开发数据：

```powershell
docker compose down -v
docker compose up --build
```

注意：`docker compose down -v` 会删除 Docker 中的 MySQL 数据卷，开发环境可以用，正式数据不要这样清。

## 默认账号

| 账号 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `admin123` | 管理员 |
| `user01` | `123456` | 普通船员 |

## 常用接口

```text
GET    /health
POST   /api/login
GET    /api/crews
POST   /api/crews
DELETE /api/crews/{crew_id}
PUT    /api/crews/{crew_id}/status
GET    /api/stats
GET    /api/voyages
POST   /api/voyages
GET    /api/my-profile/{crew_id}
GET    /api/my-voyages/{crew_id}
```
