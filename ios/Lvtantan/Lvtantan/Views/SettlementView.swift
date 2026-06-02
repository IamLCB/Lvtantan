import SwiftUI

struct SettlementView: View {
    let tripId: String

    var body: some View {
        Text("结算")
            .font(.body)
            .foregroundStyle(.primary)
            .navigationTitle("结算")
    }
}

#Preview {
    NavigationStack {
        SettlementView(tripId: "preview-trip")
    }
}
