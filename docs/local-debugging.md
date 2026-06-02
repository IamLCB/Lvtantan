# 本地调试指南

本文档用于在本机同时调试旅摊摊后端和 iOS App。

## 1. 前置条件

需要准备：

- macOS
- Xcode
- Python 3.13 或兼容版本
- Git
- 一个可用的 iPhone Simulator

后端依赖见 `backend/requirements.txt`。iOS 工程在 `ios/Lvtantan/Lvtantan.xcodeproj`。

## 2. 启动后端

```sh
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

后端默认运行在：

```text
http://127.0.0.1:8000
```

健康检查：

```sh
curl -s http://127.0.0.1:8000/health
```

预期返回：

```json
{"status":"ok"}
```

## 3. 运行 iOS App

1. 打开 `ios/Lvtantan/Lvtantan.xcodeproj`。
2. 选择 `Lvtantan` scheme。
3. 选择 iPhone Simulator。
4. 点击 Run。

iOS 代码当前默认连接：

```swift
http://127.0.0.1:8000
```

这个地址适用于本机 Xcode Simulator 调试。如果换成真机调试，`127.0.0.1` 会指向 iPhone 自己，不是 Mac；需要把 `APIClient` 的 `baseURL` 改成 Mac 在局域网里的 IP，例如：

```text
http://192.168.1.23:8000
```

同时后端启动时需要监听局域网地址：

```sh
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 4. 跑测试

后端：

```sh
cd backend
.venv/bin/pytest -v
```

iOS 单元测试：

```sh
xcodebuild -quiet \
  -project ios/Lvtantan/Lvtantan.xcodeproj \
  -scheme Lvtantan \
  -destination 'platform=iOS Simulator,name=iPhone 17' \
  -only-testing:LvtantanTests test
```

如果 `iPhone 17` 不存在，先用下面命令查看可用模拟器：

```sh
xcrun simctl list devices available
```

然后把 `name=iPhone 17` 换成你的设备名称。

## 5. 手工调试流程

建议按这个顺序验证：

1. 启动后端。
2. 确认 `/health` 正常。
3. 在 Xcode 运行 App。
4. 输入用户名完成轻注册。
5. 创建账本。
6. 确认账本首页展示邀请码。
7. 新增支出，金额可输入 `(100+20)/2`。
8. 打开结算页，确认成员余额和建议转账。
9. 用另一个用户名加入同一邀请码，验证两人成员列表和结算变化。

## 6. 常见问题

### App 提示网络失败

先确认后端还在运行：

```sh
curl -s http://127.0.0.1:8000/health
```

如果是模拟器，确认 `APIClient` 仍是 `127.0.0.1:8000`。如果是真机，改用 Mac 的局域网 IP。

### 8000 端口被占用

查看占用进程：

```sh
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

停止不需要的进程，或换一个端口。换端口后记得同步修改 iOS 的 API 地址。

### 想清空本地后端数据

停止后端后删除 SQLite 文件：

```sh
rm backend/lvtantan.db
```

重新启动后端时会自动创建表。

### Xcode 找不到模拟器

打开 Xcode：

1. Xcode -> Settings。
2. Platforms。
3. 安装 iOS Simulator runtime。

## 7. 调试 API 的示例

创建用户：

```sh
curl -s -X POST http://127.0.0.1:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"username":"小李"}'
```

创建账本：

```sh
curl -s -X POST http://127.0.0.1:8000/trips \
  -H 'Content-Type: application/json' \
  -d '{"name":"周末旅行","created_by_user_id":"替换成用户ID"}'
```

加入账本：

```sh
curl -s -X POST http://127.0.0.1:8000/trips/join \
  -H 'Content-Type: application/json' \
  -d '{"invite_code":"A7K2Q9","user_id":"替换成用户ID"}'
```

新增支出：

```sh
curl -s -X POST http://127.0.0.1:8000/trips/替换成账本ID/expenses \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "替换成用户ID",
    "amount": "60.00",
    "expression_text": "(100+20)/2",
    "category_name": "餐饮",
    "spent_at": "2026-06-02T12:00:00Z",
    "note": "晚饭"
  }'
```
