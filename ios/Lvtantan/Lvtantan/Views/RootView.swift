import SwiftUI

struct RootView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            Group {
                if appState.currentUser == nil {
                    Text("旅摊摊")
                        .font(.largeTitle.bold())
                        .foregroundStyle(.primary)
                } else {
                    Text("账本列表")
                        .font(.title)
                        .foregroundStyle(.primary)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color(.systemBackground))
        }
    }
}

#Preview {
    RootView()
        .environmentObject(AppState())
}
