# iOS App 打包与发布指南

本文档说明如何把旅摊摊 iOS App 从本地工程打包成可测试或可上架的版本。

## 1. 当前 App 配置

- 工程路径：`ios/Lvtantan/Lvtantan.xcodeproj`
- Scheme：`Lvtantan`
- Bundle Identifier：`com.iamnotlcb.lvtantan`
- Minimum Deployment：iOS 17.0
- Version：`1.0`
- Build：`1`
- Signing：Automatic

## 2. 打包前检查

### 后端地址

当前 `APIClient` 默认连接：

```swift
http://127.0.0.1:8000
```

这只适合本地模拟器调试。准备 TestFlight 或 App Store 包之前，必须改为线上 HTTPS API 地址，或改成构建配置注入。

建议：

- Debug：`http://127.0.0.1:8000`
- Release：`https://你的线上 API 域名`

### App 图标

确认图标资源已放入：

```text
ios/Lvtantan/Lvtantan/Assets.xcassets/AppIcon.appiconset
```

Xcode 中检查：

1. 打开 target `Lvtantan`。
2. Build Settings 搜索 `App Icon`。
3. 确认使用 `AppIcon`。

### 签名

Xcode 中检查：

1. 选中项目。
2. 选中 target `Lvtantan`。
3. Signing & Capabilities。
4. Team 选择你的 Apple Developer Team。
5. Bundle Identifier 确认为 `com.iamnotlcb.lvtantan`。
6. 勾选 Automatically manage signing。

如果要上传 TestFlight 或 App Store，需要 Apple Developer Program 账号。

## 3. 打包前跑测试

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

iOS Release 构建：

```sh
xcodebuild \
  -project ios/Lvtantan/Lvtantan.xcodeproj \
  -scheme Lvtantan \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  build
```

## 4. 在 Xcode 中 Archive

1. 打开 `ios/Lvtantan/Lvtantan.xcodeproj`。
2. 顶部 Scheme 选择 `Lvtantan`。
3. Run Destination 选择 `Any iOS Device` 或 `Generic iOS Device`。
4. 菜单选择 Product -> Archive。
5. 等待 Archive 完成。
6. Xcode 自动打开 Organizer。

如果 Product -> Archive 是灰色，通常是因为当前 Run Destination 选的是 Simulator。切换到 generic iOS device 后再试。

## 5. 导出本地安装包

在 Organizer 里：

1. 选中刚生成的 Archive。
2. 点击 Distribute App。
3. 选择分发方式。

常见方式：

- Debugging：给自己设备调试。
- Release Testing：给内部测试。
- App Store Connect：上传 TestFlight 或 App Store。

根据向导选择 signing certificate 和 provisioning profile。使用自动签名时，Xcode 通常会自动处理。

## 6. 上传 TestFlight

前置条件：

- 已加入 Apple Developer Program。
- App Store Connect 中已创建 App。
- Bundle Identifier 与 Xcode 一致。

流程：

1. Xcode Product -> Archive。
2. Organizer -> Distribute App。
3. 选择 App Store Connect。
4. 选择 Upload。
5. 按向导完成上传。
6. 到 App Store Connect 查看构建版本处理状态。
7. 处理完成后添加内部测试人员或外部测试组。

## 7. 提交 App Store

上架前需要准备：

- App 名称：旅摊摊。
- 副标题、描述、关键词。
- 截图。
- 隐私政策 URL。
- App 分类。
- 年龄分级。
- 联系方式。
- 版本号和构建号。

如果后端保存用户数据，需要认真填写 App Privacy。当前 App 会把用户名、账本、成员和支出数据保存到服务端。

## 8. 版本号规则

当前：

```text
MARKETING_VERSION = 1.0
CURRENT_PROJECT_VERSION = 1
```

建议：

- 功能版本变化时递增 Version，例如 `1.0` -> `1.1`。
- 每次上传 App Store Connect 都递增 Build，例如 `1` -> `2`。

Xcode 修改位置：

1. Target `Lvtantan`。
2. General。
3. Identity。
4. Version 和 Build。

## 9. 常见问题

### Archive 失败

检查：

- 是否选择 generic iOS device。
- Signing Team 是否正确。
- Bundle Identifier 是否唯一。
- App 图标是否完整。
- Release build 是否能通过。

### 上传后 TestFlight 不能测试

检查：

- App Store Connect 构建是否处理完成。
- 是否添加了测试人员。
- 外部测试是否需要 Beta App Review。

### 真机打开后连不上后端

检查：

- Release 包是否仍连接 `127.0.0.1`。
- 线上 API 是否使用 HTTPS。
- 服务器 `/health` 是否正常。
- 后端域名证书是否有效。

## 10. 发布检查清单

- 后端线上服务可用。
- iOS Release 使用线上 API 地址。
- 后端测试通过。
- iOS 单元测试通过。
- App 图标完整。
- Version 和 Build 已更新。
- Signing Team 正确。
- Archive 成功。
- TestFlight 冒烟测试通过。
- App Store Connect 隐私信息填写完整。
