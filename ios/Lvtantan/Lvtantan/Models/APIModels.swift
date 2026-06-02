import Foundation

struct APIUser: Codable, Identifiable, Equatable {
    let id: String
    let username: String
}

struct APITripSummary: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let inviteCode: String
}

struct APITripDetail: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let inviteCode: String
}
