# 服务端部署指南

本文档说明如何把旅摊摊 FastAPI 后端部署到一台 Linux 服务器。当前后端适合 MVP 和小规模验证，默认使用 SQLite。

## 1. 当前服务端结构

后端目录：

```text
backend/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── routers/
│   └── services/
├── requirements.txt
└── tests/
```

入口：

```text
app.main:app
```

默认数据库：

```text
backend/lvtantan.db
```

默认数据库 URL：

```text
sqlite:///backend/lvtantan.db
```

也可以通过环境变量 `DATABASE_URL` 覆盖。注意：当前代码的数据库连接参数按 SQLite 编写，生产切换 PostgreSQL 等数据库前需要先调整 `backend/app/database.py`。

## 2. 服务器准备

建议最低配置：

- Linux 服务器。
- Python 3.13 或兼容版本。
- 一个普通部署用户，例如 `lvtantan`。
- Nginx 或其他反向代理。
- HTTPS 证书。

以下示例假设项目放在：

```text
/opt/lvtantan
```

## 3. 部署代码

```sh
sudo mkdir -p /opt/lvtantan
sudo chown -R "$USER":"$USER" /opt/lvtantan
cd /opt/lvtantan
git clone <你的仓库地址> .
```

安装依赖：

```sh
cd /opt/lvtantan/backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

验证：

```sh
.venv/bin/pytest -v
```

## 4. 直接启动验证

先用 uvicorn 验证服务能跑起来：

```sh
cd /opt/lvtantan/backend
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端检查：

```sh
curl -s http://127.0.0.1:8000/health
```

预期：

```json
{"status":"ok"}
```

## 5. systemd 常驻运行

创建服务文件：

```sh
sudo tee /etc/systemd/system/lvtantan-backend.service >/dev/null <<'EOF'
[Unit]
Description=Lvtantan FastAPI Backend
After=network.target

[Service]
WorkingDirectory=/opt/lvtantan/backend
ExecStart=/opt/lvtantan/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
```

启动：

```sh
sudo systemctl daemon-reload
sudo systemctl enable lvtantan-backend
sudo systemctl start lvtantan-backend
sudo systemctl status lvtantan-backend
```

查看日志：

```sh
journalctl -u lvtantan-backend -f
```

## 6. Nginx 反向代理

示例配置：

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置后：

```sh
sudo nginx -t
sudo systemctl reload nginx
```

生产环境建议配置 HTTPS。可以用你熟悉的证书方案，例如云厂商证书或 Let's Encrypt。

## 7. SQLite 数据与备份

当前 SQLite 文件默认在：

```text
/opt/lvtantan/backend/lvtantan.db
```

备份示例：

```sh
mkdir -p /opt/lvtantan/backups
cp /opt/lvtantan/backend/lvtantan.db \
  /opt/lvtantan/backups/lvtantan-$(date +%Y%m%d-%H%M%S).db
```

建议：

- 上线前确认备份脚本。
- 定期备份数据库文件。
- 部署更新前先备份。
- 如果多人频繁使用，后续改为 PostgreSQL，并补充数据库迁移工具。

## 8. 更新部署

```sh
cd /opt/lvtantan
git pull
cd backend
.venv/bin/pip install -r requirements.txt
.venv/bin/pytest -v
sudo systemctl restart lvtantan-backend
```

检查：

```sh
curl -s http://127.0.0.1:8000/health
sudo systemctl status lvtantan-backend
```

## 9. iOS 线上 API 地址

iOS 当前在 `APIClient` 中默认写死：

```swift
http://127.0.0.1:8000
```

发布给用户前，需要改为线上 HTTPS API，例如：

```text
https://api.example.com
```

更稳的做法是后续改成按构建配置注入：

- Debug 使用本地 API。
- Release 使用线上 API。

## 10. 上线检查清单

- 后端测试通过。
- `/health` 正常。
- Nginx 反向代理正常。
- HTTPS 正常。
- SQLite 文件有备份方案。
- systemd 服务设置了开机自启。
- iOS Release 包使用线上 API 地址。
- 服务器日志能查看。
- 端口只开放必要服务。
