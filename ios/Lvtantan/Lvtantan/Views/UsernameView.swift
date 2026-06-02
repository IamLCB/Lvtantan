import SwiftUI

struct UsernameView: View {
    @EnvironmentObject private var appState: AppState
    @State private var username = ""
    @State private var isSubmitting = false

    private let apiClient = APIClient()
    private let sessionStore = SessionStore()

    private var trimmedUsername: String {
        username.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var isSubmitDisabled: Bool {
        trimmedUsername.isEmpty || isSubmitting
    }

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            VStack(spacing: 12) {
                Text("旅摊摊")
                    .font(.largeTitle.bold())
                    .foregroundStyle(.primary)
                    .multilineTextAlignment(.center)

                TextField("输入用户名", text: $username)
                    .textFieldStyle(.roundedBorder)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .submitLabel(.go)
                    .accessibilityLabel("用户名")
                    .accessibilityHint("输入用于进入旅摊摊的用户名")
                    .onSubmit {
                        guard !isSubmitDisabled else { return }
                        Task { await submit() }
                    }
            }

            Button {
                Task { await submit() }
            } label: {
                HStack(spacing: 8) {
                    if isSubmitting {
                        ProgressView()
                            .controlSize(.small)
                    }
                    Text(isSubmitting ? "创建中..." : "进入")
                        .font(.body.weight(.semibold))
                }
                .frame(maxWidth: .infinity, minHeight: 44)
            }
            .buttonStyle(.borderedProminent)
            .disabled(isSubmitDisabled)
            .accessibilityLabel(isSubmitting ? "正在创建用户" : "进入")
            .accessibilityHint("创建用户并进入账本列表")

            Spacer()
        }
        .padding(24)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemBackground))
    }

    private func submit() async {
        guard !isSubmitDisabled else { return }

        isSubmitting = true
        defer { isSubmitting = false }

        do {
            let user = try await apiClient.createUser(username: trimmedUsername)
            sessionStore.save(user: user)
            appState.currentUser = user
        } catch {
            appState.errorMessage = "创建用户失败，请稍后再试"
        }
    }
}

#Preview {
    UsernameView()
        .environmentObject(AppState())
}
