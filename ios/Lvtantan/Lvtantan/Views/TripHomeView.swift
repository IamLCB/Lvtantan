import SwiftUI

struct TripHomeView: View {
    let tripId: String

    var body: some View {
        Text("账本详情")
            .font(.body)
            .foregroundStyle(.primary)
            .navigationTitle("账本")
    }
}

#Preview {
    NavigationStack {
        TripHomeView(tripId: "preview-trip")
    }
}
