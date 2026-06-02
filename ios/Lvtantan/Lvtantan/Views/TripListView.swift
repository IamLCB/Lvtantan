import SwiftUI

struct TripListView: View {
    var body: some View {
        NavigationStack {
            Text("账本列表")
                .font(.body)
                .foregroundStyle(.primary)
                .navigationTitle("旅摊摊")
                .navigationBarTitleDisplayMode(.large)
        }
    }
}

#Preview {
    TripListView()
}
