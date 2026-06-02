import Foundation

@MainActor
final class TripPoller {
    private let appState: AppState
    private let apiClient: TripAPIClient
    private let interval: Duration
    private var task: Task<Void, Never>?
    private var activeTripId: String?

    convenience init(appState: AppState, interval: Duration = .seconds(4)) {
        self.init(appState: appState, apiClient: APIClient(), interval: interval)
    }

    init(appState: AppState, apiClient: TripAPIClient, interval: Duration = .seconds(4)) {
        self.appState = appState
        self.apiClient = apiClient
        self.interval = interval
    }

    func start(tripId: String) {
        stop()
        activeTripId = tripId

        if appState.activeTrip?.id != tripId {
            appState.activeTrip = nil
        }

        task = Task { [weak self] in
            await self?.poll(tripId: tripId)
        }
    }

    func stop() {
        task?.cancel()
        task = nil
        activeTripId = nil
    }

    func refreshNow(tripId: String) async {
        do {
            let trip = try await apiClient.getTrip(id: tripId)
            guard activeTripId == tripId, !Task.isCancelled, trip.id == tripId else {
                return
            }
            publishIfNeeded(trip)
        } catch {
            guard activeTripId == tripId, !Task.isCancelled else {
                return
            }
            appState.errorMessage = "刷新账本失败"
        }
    }

    private func poll(tripId: String) async {
        while !Task.isCancelled {
            await refreshNow(tripId: tripId)

            do {
                try await Task.sleep(for: interval)
            } catch {
                return
            }
        }
    }

    private func publishIfNeeded(_ trip: APITripDetail) {
        guard appState.activeTrip != trip else {
            return
        }
        appState.activeTrip = trip
    }
}
