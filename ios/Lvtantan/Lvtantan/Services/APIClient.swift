import Foundation

protocol TripAPIClient {
    func getTrip(id: String) async throws -> APITripDetail
    func createExpense(tripId: String, request: CreateExpenseRequest) async throws -> APIExpense
}

final class APIClient: TripAPIClient {
    let baseURL: URL
    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(baseURL: URL = URL(string: "http://127.0.0.1:8000")!, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
        self.decoder = JSONDecoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.decoder.dateDecodingStrategy = .custom(Self.decodeISO8601Date)
        self.encoder = JSONEncoder()
        self.encoder.keyEncodingStrategy = .convertToSnakeCase
        self.encoder.dateEncodingStrategy = .iso8601
    }

    func createUser(username: String) async throws -> APIUser {
        try await request("users", method: "POST", body: CreateUserRequest(username: username))
    }

    func createTrip(name: String, userId: String) async throws -> APITripSummary {
        try await request("trips", method: "POST", body: CreateTripRequest(name: name, createdByUserId: userId))
    }

    func joinTrip(inviteCode: String, userId: String) async throws -> APITripSummary {
        try await request("trips/join", method: "POST", body: JoinTripRequest(inviteCode: inviteCode, userId: userId))
    }

    func getTrip(id: String) async throws -> APITripDetail {
        try await request("trips/\(id)", method: "GET", body: Optional<String>.none)
    }

    func createExpense(tripId: String, request: CreateExpenseRequest) async throws -> APIExpense {
        try await self.request("trips/\(tripId)/expenses", method: "POST", body: request)
    }

    func getSettlement(tripId: String) async throws -> APISettlement {
        try await request("trips/\(tripId)/settlement", method: "GET", body: Optional<String>.none)
    }

    private func request<Response: Decodable, Body: Encodable>(
        _ path: String,
        method: String,
        body: Body?
    ) async throws -> Response {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let body {
            request.httpBody = try encoder.encode(body)
        }

        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200..<300).contains(httpResponse.statusCode) else {
            throw URLError(.badServerResponse)
        }
        return try decoder.decode(Response.self, from: data)
    }

    nonisolated private static func decodeISO8601Date(from decoder: Decoder) throws -> Date {
        let container = try decoder.singleValueContainer()
        let value = try container.decode(String.self)
        let formatters = [
            makeISO8601Formatter(formatOptions: [.withInternetDateTime, .withFractionalSeconds]),
            makeISO8601Formatter(formatOptions: [.withInternetDateTime])
        ]

        for formatter in formatters {
            if let date = formatter.date(from: value) {
                return date
            }
        }

        throw DecodingError.dataCorruptedError(
            in: container,
            debugDescription: "Expected ISO8601 date string."
        )
    }

    nonisolated private static func makeISO8601Formatter(
        formatOptions: ISO8601DateFormatter.Options
    ) -> ISO8601DateFormatter {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = formatOptions
        return formatter
    }
}

private struct CreateUserRequest: Encodable {
    let username: String
}

private struct CreateTripRequest: Encodable {
    let name: String
    let createdByUserId: String
}

private struct JoinTripRequest: Encodable {
    let inviteCode: String
    let userId: String
}

struct CreateExpenseRequest: Encodable {
    let userId: String
    let amount: String
    let expressionText: String?
    let categoryName: String
    let spentAt: Date
    let note: String?
}
