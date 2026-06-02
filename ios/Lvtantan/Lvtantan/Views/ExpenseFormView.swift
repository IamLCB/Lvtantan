import SwiftUI

struct ExpenseFormView: View {
    let trip: APITripDetail
    let onSaved: () async -> Void

    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss
    @FocusState private var focusedField: Field?
    @State private var amountExpression = ""
    @State private var categoryName = "餐饮"
    @State private var note = ""
    @State private var isSubmitting = false
    @State private var errorMessage: String?
    @State private var submissionTask: Task<Void, Never>?

    private let apiClient: TripAPIClient = APIClient()
    private let categories = ["餐饮", "交通", "住宿", "门票", "购物", "娱乐", "其他"]

    private var trimmedAmountExpression: String {
        amountExpression.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var trimmedNote: String {
        note.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var canSubmit: Bool {
        evaluatedAmount != nil && !isSubmitting && submissionTask == nil
    }

    private var evaluatedAmount: Decimal? {
        try? MoneyExpression.evaluate(trimmedAmountExpression)
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("金额，例如 100+20/2", text: $amountExpression)
                        .keyboardType(.numbersAndPunctuation)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .focused($focusedField, equals: .amount)
                        .submitLabel(.next)
                        .frame(minHeight: 44)
                        .accessibilityLabel("金额")
                        .accessibilityHint("输入金额或四则运算表达式")

                    Picker("类别", selection: $categoryName) {
                        ForEach(categories, id: \.self) { category in
                            Text(category).tag(category)
                        }
                    }
                    .frame(minHeight: 44)
                    .accessibilityHint("选择支出类别")

                    TextField("备注", text: $note, axis: .vertical)
                        .lineLimit(2...4)
                        .focused($focusedField, equals: .note)
                        .frame(minHeight: 44)
                        .accessibilityLabel("备注")
                        .accessibilityHint("可选，填写支出说明")
                }

                Section {
                    Text("付款人：我")
                        .frame(minHeight: 44)
                    Text("分摊：账本内所有成员")
                        .frame(minHeight: 44)
                }

                if let errorMessage {
                    Section {
                        Text(errorMessage)
                            .font(.body)
                            .foregroundStyle(.red)
                            .accessibilityLabel(errorMessage)
                    }
                }

                Section {
                    Button {
                        submitIfPossible()
                    } label: {
                        HStack {
                            Spacer()
                            if isSubmitting {
                                ProgressView()
                                    .accessibilityHidden(true)
                                Text("保存中")
                            } else {
                                Text("保存支出")
                            }
                            Spacer()
                        }
                        .frame(minHeight: 44)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!canSubmit)
                    .accessibilityLabel(isSubmitting ? "保存中" : "保存支出")
                    .accessibilityHint("保存当前支出")
                }
            }
            .navigationTitle("记一笔")
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
        .interactiveDismissDisabled(isSubmitting)
        .onAppear {
            focusedField = .amount
        }
        .onDisappear {
            cancelSubmission()
        }
    }

    private func submitIfPossible() {
        guard canSubmit else { return }
        isSubmitting = true
        errorMessage = nil
        submissionTask = Task {
            await submit()
        }
    }

    private func submit() async {
        guard let user = appState.currentUser else {
            errorMessage = "保存支出失败，请检查金额"
            finishSubmission()
            return
        }

        do {
            guard let amount = evaluatedAmount else {
                errorMessage = "保存支出失败，请检查金额"
                finishSubmission()
                return
            }
            let request = CreateExpenseRequest(
                userId: user.id,
                amount: decimalString(from: amount),
                expressionText: trimmedAmountExpression,
                categoryName: categoryName,
                spentAt: .now,
                note: trimmedNote.isEmpty ? nil : trimmedNote
            )
            _ = try await apiClient.createExpense(tripId: trip.id, request: request)
            guard !Task.isCancelled else { return }

            await onSaved()
            guard !Task.isCancelled else { return }

            finishSubmission()
            dismiss()
        } catch {
            guard !Task.isCancelled else { return }

            errorMessage = "保存支出失败，请检查金额"
            finishSubmission()
        }
    }

    private enum Field {
        case amount
        case note
    }

    private func decimalString(from decimal: Decimal) -> String {
        let formatter = NumberFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.numberStyle = .decimal
        formatter.minimumFractionDigits = 2
        formatter.maximumFractionDigits = 2
        formatter.usesGroupingSeparator = false
        return formatter.string(from: NSDecimalNumber(decimal: decimal)) ?? "\(decimal)"
    }

    private func finishSubmission() {
        isSubmitting = false
        submissionTask = nil
    }

    private func cancelSubmission() {
        submissionTask?.cancel()
        submissionTask = nil
        isSubmitting = false
    }
}

#Preview {
    ExpenseFormView(
        trip: APITripDetail(
            id: "trip",
            name: "杭州",
            inviteCode: "ABC123",
            currencyCode: "CNY",
            status: "active",
            version: 1,
            members: [],
            expenses: []
        ),
        onSaved: {}
    )
    .environmentObject(AppState())
}
