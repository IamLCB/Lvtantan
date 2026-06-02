import SwiftUI

enum TripFormMode {
    case create
    case join

    var navigationTitle: String {
        switch self {
        case .create:
            "创建账本"
        case .join:
            "加入账本"
        }
    }

    var textFieldTitle: String {
        switch self {
        case .create:
            "旅行名称"
        case .join:
            "邀请码"
        }
    }

    var submitTitle: String {
        switch self {
        case .create:
            "创建账本"
        case .join:
            "加入账本"
        }
    }

    var failureMessage: String {
        switch self {
        case .create:
            "创建账本失败"
        case .join:
            "加入账本失败"
        }
    }

    var textInputAutocapitalization: TextInputAutocapitalization {
        switch self {
        case .create:
            .sentences
        case .join:
            .characters
        }
    }

    var textFieldHint: String {
        switch self {
        case .create:
            "输入旅行账本名称"
        case .join:
            "输入已有账本的邀请码"
        }
    }
}

struct TripFormView: View {
    let mode: TripFormMode

    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss
    @State private var text = ""
    @State private var isSubmitting = false

    private let apiClient = APIClient()

    private var trimmedText: String {
        text.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var canSubmit: Bool {
        !trimmedText.isEmpty && !isSubmitting
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField(mode.textFieldTitle, text: $text)
                        .textInputAutocapitalization(mode.textInputAutocapitalization)
                        .autocorrectionDisabled(mode == .join)
                        .submitLabel(.done)
                        .frame(minHeight: 44)
                        .accessibilityLabel(mode.textFieldTitle)
                        .accessibilityHint(mode.textFieldHint)
                        .onSubmit {
                            submitIfPossible()
                        }
                }

                Section {
                    Button {
                        submitIfPossible()
                    } label: {
                        if isSubmitting {
                            ProgressView()
                                .frame(maxWidth: .infinity, minHeight: 44)
                        } else {
                            Text(mode.submitTitle)
                                .frame(maxWidth: .infinity, minHeight: 44)
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!canSubmit)
                    .accessibilityLabel(mode.submitTitle)
                    .accessibilityHint(mode == .create ? "提交并创建账本" : "提交邀请码并加入账本")
                }
            }
            .navigationTitle(mode.navigationTitle)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") {
                        dismiss()
                    }
                    .disabled(isSubmitting)
                    .frame(minWidth: 44, minHeight: 44)
                }
            }
        }
    }

    private func submitIfPossible() {
        guard canSubmit else { return }
        isSubmitting = true
        Task {
            await submit()
        }
    }

    private func submit() async {
        guard let user = appState.currentUser else {
            isSubmitting = false
            return
        }
        defer { isSubmitting = false }

        do {
            let trip: APITripSummary
            if mode == .create {
                trip = try await apiClient.createTrip(name: trimmedText, userId: user.id)
            } else {
                trip = try await apiClient.joinTrip(inviteCode: trimmedText.uppercased(), userId: user.id)
            }

            if !appState.trips.contains(where: { $0.id == trip.id }) {
                appState.trips.append(trip)
            }
            dismiss()
        } catch {
            appState.errorMessage = mode.failureMessage
        }
    }
}

#Preview("Create") {
    TripFormView(mode: .create)
        .environmentObject(AppState())
}

#Preview("Join") {
    TripFormView(mode: .join)
        .environmentObject(AppState())
}
