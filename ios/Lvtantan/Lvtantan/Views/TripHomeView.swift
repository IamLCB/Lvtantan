import SwiftUI

struct TripHomeView: View {
    let tripId: String

    @EnvironmentObject private var appState: AppState
    @State private var isExpenseFormPresented = false
    @State private var poller: TripPoller?

    private var trip: APITripDetail? {
        guard let activeTrip = appState.activeTrip, activeTrip.id == tripId else {
            return nil
        }
        return activeTrip
    }

    var body: some View {
        List {
            if let trip {
                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(trip.name)
                            .font(.title2)
                            .fontWeight(.semibold)
                            .foregroundStyle(.primary)
                            .accessibilityAddTraits(.isHeader)

                        LabeledContent("邀请码", value: trip.inviteCode)
                            .font(.body)
                            .accessibilityElement(children: .combine)
                            .accessibilityLabel("邀请码")
                            .accessibilityValue(trip.inviteCode)
                    }
                    .padding(.vertical, 4)
                }

                Section {
                    ForEach(trip.members) { member in
                        HStack(spacing: 12) {
                            Image(systemName: "person.circle")
                                .font(.title3)
                                .foregroundStyle(.secondary)
                                .accessibilityHidden(true)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(member.name)
                                    .font(.body)
                                    .foregroundStyle(.primary)
                                Text(member.status)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .frame(minHeight: 44)
                        .accessibilityElement(children: .combine)
                        .accessibilityLabel(member.name)
                        .accessibilityValue(member.status)
                    }
                } header: {
                    Text("成员")
                }

                Section {
                    if recentExpenses(from: trip).isEmpty {
                        ContentUnavailableView(
                            "暂无支出",
                            systemImage: "receipt",
                            description: Text("点击右上角记一笔。")
                        )
                    } else {
                        ForEach(recentExpenses(from: trip)) { expense in
                            ExpenseRowView(expense: expense, currencyCode: trip.currencyCode)
                        }

                        NavigationLink {
                            ExpenseListView(trip: trip)
                        } label: {
                            Label("查看全部支出", systemImage: "list.bullet")
                                .frame(minHeight: 44)
                        }
                        .accessibilityHint("打开全部支出列表")
                    }
                } header: {
                    Text("最近支出")
                }
            } else {
                Section {
                    HStack {
                        Spacer()
                        ProgressView()
                            .controlSize(.large)
                            .accessibilityLabel("正在加载账本")
                        Spacer()
                    }
                    .frame(minHeight: 160)
                }
            }
        }
        .navigationTitle(trip?.name ?? "账本")
        .navigationBarTitleDisplayMode(.large)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("记一笔") {
                    isExpenseFormPresented = true
                }
                .disabled(trip == nil)
                .frame(minWidth: 44, minHeight: 44)
                .accessibilityHint("打开新增支出表单")
            }
        }
        .safeAreaInset(edge: .bottom) {
            NavigationLink {
                SettlementView(tripId: tripId)
            } label: {
                Label("结算", systemImage: "arrow.left.arrow.right")
                    .font(.headline)
                    .frame(maxWidth: .infinity, minHeight: 44)
            }
            .buttonStyle(.borderedProminent)
            .disabled(trip == nil)
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(.bar)
            .accessibilityHint("查看当前账本的结算结果")
        }
        .sheet(isPresented: $isExpenseFormPresented) {
            if let trip {
                ExpenseFormView(trip: trip) {
                    await poller?.refreshNow(tripId: tripId)
                }
            }
        }
        .onAppear {
            let newPoller = TripPoller(appState: appState)
            poller = newPoller
            newPoller.start(tripId: tripId)
        }
        .onDisappear {
            poller?.stop()
            poller = nil
        }
    }

    private func recentExpenses(from trip: APITripDetail) -> [APIExpense] {
        Array(trip.expenses.sorted { $0.spentAt > $1.spentAt }.prefix(5))
    }
}

#Preview {
    NavigationStack {
        TripHomeView(tripId: "preview-trip")
    }
    .environmentObject(AppState())
}
