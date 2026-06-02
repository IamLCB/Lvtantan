import XCTest
@testable import Lvtantan

@MainActor
final class TripPollerTests: XCTestCase {
    func testCancelledPollerDoesNotPublishFetchedTrip() async throws {
        let appState = AppState()
        let client = DelayedTripClient()
        let poller = TripPoller(appState: appState, apiClient: client, interval: .seconds(10))

        poller.start(tripId: "trip-a")
        await client.waitForRequest()
        poller.stop()

        client.resume(with: Self.trip(id: "trip-a", version: 1))
        try await Task.sleep(for: .milliseconds(50))

        XCTAssertNil(appState.activeTrip)
    }

    private static func trip(id: String, version: Int) -> APITripDetail {
        APITripDetail(
            id: id,
            name: "Trip",
            inviteCode: "ABC123",
            currencyCode: "CNY",
            status: "active",
            version: version,
            members: [],
            expenses: []
        )
    }
}

@MainActor
private final class DelayedTripClient: TripAPIClient {
    private var continuation: CheckedContinuation<APITripDetail, Error>?
    private var requestContinuation: CheckedContinuation<Void, Never>?
    private var hasRequest = false

    func getTrip(id: String) async throws -> APITripDetail {
        try await withCheckedThrowingContinuation { continuation in
            self.continuation = continuation
            hasRequest = true
            requestContinuation?.resume()
            requestContinuation = nil
        }
    }

    func createExpense(tripId: String, request: CreateExpenseRequest) async throws -> APIExpense {
        throw URLError(.unsupportedURL)
    }

    func resume(with trip: APITripDetail) {
        continuation?.resume(returning: trip)
        continuation = nil
    }

    func waitForRequest() async {
        guard !hasRequest else {
            return
        }

        await withCheckedContinuation { continuation in
            requestContinuation = continuation
        }
    }
}
