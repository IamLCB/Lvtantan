import SwiftUI

struct ExpenseListView: View {
    let trip: APITripDetail

    private var sortedExpenses: [APIExpense] {
        trip.expenses.sorted { $0.spentAt > $1.spentAt }
    }

    var body: some View {
        List {
            if sortedExpenses.isEmpty {
                ContentUnavailableView(
                    "暂无支出",
                    systemImage: "receipt",
                    description: Text("记一笔后会显示在这里。")
                )
            } else {
                ForEach(sortedExpenses) { expense in
                    ExpenseRowView(expense: expense, currencyCode: trip.currencyCode)
                }
            }
        }
        .navigationTitle("全部支出")
        .navigationBarTitleDisplayMode(.large)
    }
}

struct ExpenseRowView: View {
    let expense: APIExpense
    let currencyCode: String

    private var subtitle: String {
        if let note = expense.note?.trimmingCharacters(in: .whitespacesAndNewlines), !note.isEmpty {
            return note
        }
        return expense.spentAt.formatted(date: .abbreviated, time: .shortened)
    }

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                Text(expense.categoryName)
                    .font(.body)
                    .foregroundStyle(.primary)
                Text(subtitle)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }

            Spacer(minLength: 12)

            Text(formattedAmount)
                .font(.headline)
                .monospacedDigit()
                .foregroundStyle(.primary)
        }
        .frame(minHeight: 44)
        .accessibilityElement(children: .combine)
        .accessibilityLabel(expense.categoryName)
        .accessibilityValue("\(formattedAmount), \(subtitle)")
    }

    private var formattedAmount: String {
        let decimal = Decimal(string: expense.amount, locale: Locale(identifier: "en_US_POSIX")) ?? 0
        return "\(currencyCode) \(decimal.formatted(.number.precision(.fractionLength(2))))"
    }
}

#Preview {
    NavigationStack {
        ExpenseListView(
            trip: APITripDetail(
                id: "trip",
                name: "杭州",
                inviteCode: "ABC123",
                currencyCode: "CNY",
                status: "active",
                version: 1,
                members: [],
                expenses: [
                    APIExpense(
                        id: "expense",
                        tripId: "trip",
                        amount: "88.50",
                        expressionText: nil,
                        createdByMemberId: "member",
                        paidByMemberId: "member",
                        categoryName: "餐饮",
                        spentAt: .now,
                        note: "晚餐"
                    )
                ]
            )
        )
    }
}
