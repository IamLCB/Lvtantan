# iOS App 开发环境准备

版本：v0.1  
日期：2026-06-02  
适用对象：第一次开发 iOS App 的开发者

## 1. 你需要准备什么

### 必需

- 一台 Mac。
- Xcode。
- 一个 Apple ID。
- iPhone 真机，建议有，但不是第一天必须。

### 可选但推荐

- Apple Developer Program 会员。
- Git。
- Cursor / VS Code / Codex 等辅助开发工具。
- Homebrew。

## 2. Mac 要求

iOS 原生开发需要 macOS 和 Xcode。你需要先确认自己的 Mac 能安装当前版本 Xcode。

操作：

1. 点击左上角 Apple 菜单。
2. 选择“关于本机”。
3. 查看 macOS 版本、芯片类型、内存。

建议：

- Apple Silicon 芯片，也就是 M1/M2/M3/M4 系列，会更舒服。
- 内存建议 16GB 或以上，8GB 也能学，但 Xcode、模拟器和浏览器一起开会比较吃力。
- 磁盘建议至少预留 40GB 到 60GB 空间。Xcode、模拟器和缓存会占不少空间。

## 3. 安装 Xcode

Xcode 是开发 iOS App 的官方 IDE，包含：

- Swift 编译器。
- iOS SDK。
- iOS Simulator。
- Interface tools。
- 调试、签名、打包工具。

截至 2026-06-02，Apple 官方 Xcode 支持页列出的最新正式版本是 Xcode 26.5，要求 macOS Tahoe 26.2 或更高版本。你的 Mac 如果还不能升级到这个 macOS 版本，就需要安装与你系统兼容的 Xcode 版本。

安装方式：

1. 打开 Mac App Store。
2. 搜索 Xcode。
3. 安装最新版 Xcode。

如果 App Store 下载很慢，也可以从 Apple Developer 网站下载，但通常需要登录 Apple ID。

安装完成后：

1. 打开 Xcode。
2. 同意许可协议。
3. 等待它安装额外组件。
4. 打开 Xcode Settings，确认 iOS 平台组件已安装。

验证命令：

```sh
xcodebuild -version
```

如果能看到 Xcode 版本号，说明命令行工具基本可用。

## 4. 安装 Command Line Tools

通常安装 Xcode 后已经包含命令行工具。如果后续运行命令提示缺失，可以执行：

```sh
xcode-select --install
```

也可以检查当前 Xcode 路径：

```sh
xcode-select -p
```

如果路径不是 Xcode 内部路径，可以设置：

```sh
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

## 5. Apple ID 与开发者账号

### 免费 Apple ID 能做什么

用普通 Apple ID 就可以：

- 在 Xcode 创建项目。
- 在模拟器运行 App。
- 在自己的 iPhone 上调试 App。

限制：

- 真机调试的签名有效期和能力有限。
- 无法提交 App Store。
- 一些高级能力可能不可用或受限。

### Apple Developer Program 会员

如果你想上架 App Store，或者长期稳定做真机测试，需要加入 Apple Developer Program。

截至 2026-06-02，Apple 官方说明的标准费用为每个会员年度 99 美元。具体费用和政策可能随地区和时间变化，最终以 Apple 官方页面为准。

建议：

- 学习阶段先不用急着付费。
- 等 App 基本可用、需要 TestFlight 或上架 App Store 时再加入。

## 6. 创建第一个 iOS 项目

在 Xcode 中：

1. File -> New -> Project。
2. 选择 iOS -> App。
3. Product Name 填 App 名称，例如 `旅摊摊`。
4. Interface 选择 SwiftUI。
5. Language 选择 Swift。
6. Storage 如果有 SwiftData 选项，可以选择 SwiftData；也可以先不选，后续手动加入。
7. Team 选择你的 Apple ID 对应团队。

建议首版配置：

- Interface: SwiftUI
- Language: Swift
- Minimum Deployments: iOS 17.0
- Storage: SwiftData

## 7. 运行模拟器

创建项目后：

1. 在 Xcode 顶部选择一个 iPhone 模拟器，例如 iPhone 16。
2. 点击运行按钮。
3. 等待编译和模拟器启动。

第一次启动会慢一些，后面会快很多。

如果模拟器列表为空：

1. Xcode -> Settings -> Platforms。
2. 安装 iOS Simulator runtime。

## 8. 连接 iPhone 真机

如果你有 iPhone，可以用真机测试。

准备：

- iPhone 和 Mac 登录或信任同一个 Apple ID。
- 用 USB 连接，或开启无线调试。
- iPhone 上信任这台 Mac。

Xcode 中：

1. 打开项目。
2. 顶部运行设备选择你的 iPhone。
3. Signing & Capabilities 中选择 Team。
4. 确认 Bundle Identifier 唯一，本项目使用 `com.iamnotlcb.lvtantan`。
5. 点击运行。

常见问题：

- 如果提示签名失败，检查 Team 和 Bundle Identifier。
- 如果提示 Developer Mode，按 iPhone 提示开启开发者模式。
- 如果免费账号提示证书限制，先删除旧的免费签名 App 或稍后重试。

## 9. 推荐开发工具

### Xcode

必须安装。负责创建项目、编译、调试、模拟器、真机运行、签名打包。

### Git

用于版本管理。建议每完成一个小功能就提交一次。

检查：

```sh
git --version
```

### Homebrew

可选，用来安装命令行工具。

官网：

```text
https://brew.sh/
```

### 辅助编辑器

可以继续用 Codex 协助写代码、改文件、跑测试。但 iOS 项目的编译、预览、签名、真机调试，仍然主要依赖 Xcode。

## 10. 学习路线建议

第一阶段：熟悉 SwiftUI

- Text、Button、Image、List、Form。
- NavigationStack。
- TabView。
- @State、@Binding、@Observable。

第二阶段：做旅摊摊核心功能

- 表单输入。
- 列表展示。
- 本机数据存储。
- 日期和金额格式化。

第三阶段：完善体验

- 空状态。
- 删除确认。
- 表单校验。
- 分类颜色和图标。
- 统计图表。

第四阶段：准备发布

- App 图标。
- 隐私说明。
- TestFlight。
- App Store Connect。
- 截图和上架信息。

## 11. 推荐项目结构

如果使用 SwiftUI + SwiftData，项目可以先这样组织：

```text
Lvtantan/
  LvtantanApp.swift
  Models/
    Transaction.swift
    Category.swift
    Account.swift
  Views/
    Transactions/
      TransactionListView.swift
      TransactionFormView.swift
    Statistics/
      StatisticsView.swift
    Settings/
      SettingsView.swift
      CategoryListView.swift
  Services/
    SeedDataService.swift
  Utilities/
    CurrencyFormatter.swift
    DateHelpers.swift
```

首版不用一开始拆太细，等功能稳定后再整理也可以。

## 12. 第一天建议完成的事

1. 安装并打开 Xcode。
2. 创建一个 SwiftUI iOS App 项目。
3. 在模拟器运行默认 App。
4. 修改首页文字并再次运行。
5. 初始化 Git 仓库。
6. 提交第一版代码。

示例命令：

```sh
git init
git add .
git commit -m "Initial iOS app project"
```

## 13. 当前项目前置决策

建议我们先确认：

1. App 名称：已定为“旅摊摊”。
2. 英文工程名：已定为 `Lvtantan`。
3. Bundle Identifier：已定为 `com.iamnotlcb.lvtantan`。
4. 最低 iOS 版本：推荐 iOS 17。
5. 数据存储：推荐服务端保存共享账本数据，本地缓存用户会话和最近账本。
6. 是否上架：学习阶段先不处理，上架前再准备 Apple Developer Program。
7. 是否先做中文界面：建议第一版只做中文，后续再国际化。

## 14. 官方资料

- Xcode 支持与资源：https://developer.apple.com/support/xcode/
- Apple Developer Program：https://developer.apple.com/programs/
- SwiftUI 文档：https://developer.apple.com/documentation/swiftui
- SwiftData 文档：https://developer.apple.com/documentation/swiftdata
- App Store Connect：https://appstoreconnect.apple.com/
