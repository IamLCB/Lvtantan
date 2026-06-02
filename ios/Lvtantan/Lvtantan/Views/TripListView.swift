import SwiftUI

struct TripListView: View {
    @EnvironmentObject private var appState: AppState
    @State private var presentedSheet: TripListSheet?

    var body: some View {
        NavigationStack {
            List(appState.trips) { trip in
                NavigationLink {
                    TripHomeView(tripId: trip.id)
                } label: {
                    Text(trip.name)
                        .font(.body)
                        .foregroundStyle(.primary)
                }
                .accessibilityLabel(trip.name)
                .accessibilityHint("打开账本详情")
            }
            .overlay {
                if appState.trips.isEmpty {
                    ContentUnavailableView(
                        "暂无账本",
                        systemImage: "map",
                        description: Text("创建新账本，或用邀请码加入已有账本。")
                    )
                }
            }
            .navigationTitle("旅摊摊")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("加入") {
                        presentedSheet = .join
                    }
                    .frame(minWidth: 44, minHeight: 44)
                    .accessibilityHint("输入邀请码加入账本")
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("创建") {
                        presentedSheet = .create
                    }
                    .frame(minWidth: 44, minHeight: 44)
                    .accessibilityHint("创建新的旅行账本")
                }
            }
            .sheet(item: $presentedSheet) { sheet in
                TripFormView(mode: sheet.mode)
            }
        }
    }
}

private enum TripListSheet: Identifiable {
    case create
    case join

    var id: String {
        switch self {
        case .create:
            "create"
        case .join:
            "join"
        }
    }

    var mode: TripFormMode {
        switch self {
        case .create:
            .create
        case .join:
            .join
        }
    }
}

#Preview {
    TripListView()
        .environmentObject(AppState())
}
