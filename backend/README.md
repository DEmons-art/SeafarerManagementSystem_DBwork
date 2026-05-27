# FastAPI 后端说明

后端主入口是 `app/main.py`，业务接口在 `app/api.py`，业务 SQL 和状态流转在 `app/services.py`。

## main.py 负责什么

`app/main.py` 只负责应用外壳：

- 创建 FastAPI 应用
- 注册 CORS
- 指定 UTF-8 JSON 响应
- 统一处理参数校验错误和业务错误
- 创建数据库连接配置，并放到 `app.state.database`
- 挂载 `api.py` 中声明的接口

业务逻辑不要塞进 `main.py`。船员、航次、状态更新等规则都放在 `services.py`。

## Docker 快速启动

推荐从项目根目录用 Docker Compose 启动：

```powershell
docker compose up --build
```

启动后：

```text
后端接口：http://localhost:3000
接口文档：http://localhost:3000/docs
健康检查：http://localhost:3000/health
```

再次启动已有容器：

```powershell
docker compose up -d
```

## MySQL 依赖

后端依赖 Docker Compose 里的 MySQL 8 镜像和 `db` 容器：

```yaml
db:
  image: mysql:8.0
```

Compose 中后端连接的是：

```text
mysql+pymysql://root:123456@db:3306/SeafarerDB?charset=utf8mb4
```

所以单独运行后端前，必须先有可连接的 MySQL。正常开发建议直接使用：

```powershell
docker compose up --build
```

这样会自动等待 MySQL 容器健康后再启动后端。

## 数据库重置

`init.sql` 会在 MySQL 数据卷第一次创建时执行。需要重置数据库时，在项目根目录运行：

```powershell
docker compose down -v
docker compose up --build
```

注意：`docker compose down -v` 会删除 Docker 里的 MySQL 数据卷。
