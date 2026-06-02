import SwiftUI

struct RootView: View {
    @EnvironmentObject private var appState: AppState
    private let sessionStore = SessionStore()

    private var isErrorPresented: Binding<Bool> {
        Binding {
            appState.errorMessage != nil
        } set: { isPresented in
            if !isPresented {
                appState.errorMessage = nil
            }
        }
    }

    var body: some View {
        Group {
            if appState.currentUser == nil {
                UsernameView()
            } else {
                TripListView()
            }
        }
        .onAppear {
            guard appState.currentUser == nil else { return }
            appState.currentUser = sessionStore.loadUser()
        }
        .alert("提示", isPresented: isErrorPresented) {
            Button("好") {
                appState.errorMessage = nil
            }
        } message: {
            Text(appState.errorMessage ?? "")
        }
    }
}

#Preview {
    RootView()
        .environmentObject(AppState())
}
