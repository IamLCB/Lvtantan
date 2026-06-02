import Foundation

struct APIUser: Codable, Identifiable, Equatable {
    let id: String
    let username: String
}

struct APIMember: Codable, Identifiable, Equatable {
    let id: String
    let userId: String
    let name: String
    let status: String
}

struct APIExpense: Codable, Identifiable, Equatable {
    let id: String
    let tripId: String
    let amount: String
    let expressionText: String?
    let createdByMemberId: String
    let paidByMemberId: String
    let categoryName: String
    let spentAt: Date
    let note: String?
}

struct APITripSummary: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let inviteCode: String
    let currencyCode: String
    let status: String
    let version: Int
    let members: [APIMember]
}

struct APITripDetail: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let inviteCode: String
    let currencyCode: String
    let status: String
    let version: Int
    let members: [APIMember]
    let expenses: [APIExpense]
}

struct APISettlement: Codable, Equatable {
    let members: [APISettlementMember]
    let transfers: [APISettlementTransfer]
}

struct APISettlementMember: Codable, Equatable {
    let memberId: String
    let name: String
    let paid: String
    let owed: String
    let balance: String
}

struct APISettlementTransfer: Codable, Equatable {
    let fromMemberId: String
    let fromMemberName: String
    let toMemberId: String
    let toMemberName: String
    let amount: String
}
