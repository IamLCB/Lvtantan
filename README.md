# 旅摊摊 Lvtantan

旅摊摊是一款面向旅行、聚餐和短途活动的 iOS 共享记账 App。用户输入用户名即可轻注册，通过 6 位邀请码加入同一个账本，成员可以共同登记支出，系统按当前账本成员均分费用并生成结算建议。

## 当前状态

- iOS App：SwiftUI，最低支持 iOS 17。
- 后端：Python FastAPI。
- 数据库：默认 SQLite，文件位于 `backend/lvtantan.db`。
- 工程名：`Lvtantan`。
- Bundle Identifier：`com.iamnotlcb.lvtantan`。
- 本地 API 地址：`http://127.0.0.1:8000`。

## 目录结构

```text
.
├── backend/                 # FastAPI 后端
│   ├── app/                 # API、模型、服务
│   ├── tests/               # 后端测试
│   └── requirements.txt
├── docs/
│   ├── prd.md               # 产品需求文档
│   ├── ios-environment-setup.md
│   ├── local-debugging.md
│   ├── server-deployment.md
│   └── app-packaging.md
└── ios/Lvtantan/            # iOS SwiftUI 工程
```

## 快速启动

启动后端：

```sh
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

验证后端：

```sh
curl -s http://127.0.0.1:8000/health
```

预期返回：

```json
{"status":"ok"}
```

运行 iOS：

1. 打开 `ios/Lvtantan/Lvtantan.xcodeproj`。
2. 选择 `Lvtantan` scheme。
3. 选择一个 iPhone Simulator，例如 iPhone 17。
4. 点击 Xcode 的 Run。

## 常用命令

后端测试：

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

iOS 构建：

```sh
xcodebuild \
  -project ios/Lvtantan/Lvtantan.xcodeproj \
  -scheme Lvtantan \
  -destination 'platform=iOS Simulator,name=iPhone 17' \
  build
```

## 核心文档

- [PRD](docs/prd.md)
- [iOS 环境准备](docs/ios-environment-setup.md)
- [本地调试](docs/local-debugging.md)
- [服务端部署](docs/server-deployment.md)
- [App 打包与发布](docs/app-packaging.md)

## 当前 MVP 规则

- 用户名轻注册，不需要手机号、邮箱或密码。
- 同一账本内用户名唯一。
- 邀请码为 6 位字母数字码。
- 第一版只支持 CNY。
- 每笔支出默认由登记人付款。
- 每笔支出默认由账本内所有 active 成员均分。
- 后加入成员也会分摊加入前已有支出。
- 客户端通过轮询实现多人共同编辑后的近实时刷新。

## 注意事项

- iOS 当前默认连接 `http://127.0.0.1:8000`，生产发布前需要把 `APIClient` 的 `baseURL` 改成线上 API 地址，或改为通过构建配置注入。
- 当前后端默认使用 SQLite，适合 MVP、本地验证和小规模测试；正式生产建议补充迁移、备份、监控和更稳的数据库方案。
- Xcode 签名当前使用自动签名，发布到 TestFlight 或 App Store 前需要确认 Apple Developer Team、Bundle Identifier、版本号和 App 图标。
