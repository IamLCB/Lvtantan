import SwiftUI
import UIKit

struct SettlementView: View {
    let tripId: String

    @EnvironmentObject private var appState: AppState
    @State private var settlement: APISettlement?

    private let apiClient = APIClient()

    var body: some View {
        List {
            if let settlement {
                Section("成员") {
                    ForEach(settlement.members, id: \.memberId) { member in
                        SettlementMemberRow(member: member)
                    }
                }

                Section("建议转账") {
                    if settlement.transfers.isEmpty {
                        ContentUnavailableView(
                            "无需转账",
                            systemImage: "checkmark.circle",
                            description: Text("当前账本已经结清。")
                        )
                    } else {
                        ForEach(settlement.transfers, id: \.settlementIdentity) { transfer in
                            Text(Self.transferText(transfer))
                                .font(.body)
                                .foregroundStyle(.primary)
                                .frame(minHeight: 44, alignment: .leading)
                                .accessibilityLabel("建议转账")
                                .accessibilityValue(Self.transferText(transfer))
                        }
                    }

                    Button("复制结算结果") {
                        UIPasteboard.general.string = settlement.transfers
                            .map(Self.transferText)
                            .joined(separator: "\n")
                    }
                    .disabled(settlement.transfers.isEmpty)
                    .frame(minHeight: 44)
                    .accessibilityHint("复制所有建议转账到剪贴板")
                }
            } else {
                Section {
                    HStack {
                        Spacer()
                        ProgressView()
                            .controlSize(.large)
                            .accessibilityLabel("正在加载结算")
                        Spacer()
                    }
                    .frame(minHeight: 160)
                }
            }
        }
        .navigationTitle("结算")
        .task {
            await loadSettlement()
        }
    }

    nonisolated static func transferText(_ transfer: APISettlementTransfer) -> String {
        "\(transfer.fromMemberName) 转给 \(transfer.toMemberName) \(transfer.amount) 元"
    }

    @MainActor
    private func loadSettlement() async {
        do {
            settlement = try await apiClient.getSettlement(tripId: tripId)
        } catch {
            appState.errorMessage = "获取结算失败"
        }
    }
}

private struct SettlementMemberRow: View {
    let member: APISettlementMember

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(member.name)
                .font(.body)
                .foregroundStyle(.primary)
            LabeledContent("余额", value: member.balance)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(minHeight: 44)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(member.name)
        .accessibilityValue("余额 \(member.balance)")
    }
}

private extension APISettlementTransfer {
    var settlementIdentity: String {
        [
            fromMemberId,
            toMemberId,
            amount,
            fromMemberName,
            toMemberName
        ].joined(separator: "|")
    }
}

#Preview {
    NavigationStack {
        SettlementView(tripId: "preview-trip")
    }
    .environmentObject(AppState())
}
