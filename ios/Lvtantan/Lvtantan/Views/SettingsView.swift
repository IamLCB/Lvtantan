import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        Form {
            Section("当前用户") {
                Text(appState.currentUser?.username ?? "未登录")
                    .font(.body)
                    .foregroundStyle(.primary)
                    .accessibilityLabel("当前用户")
                    .accessibilityValue(appState.currentUser?.username ?? "未登录")
            }

            Section("数据说明") {
                Text("账本数据保存在服务端，用于多人实时共享。")
                    .font(.body)
                    .foregroundStyle(.primary)
            }
        }
        .navigationTitle("设置")
    }
}

#Preview {
    NavigationStack {
        SettingsView()
    }
    .environmentObject(AppState())
}
