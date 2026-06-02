import Foundation
import Combine

@MainActor
final class AppState: ObservableObject {
    @Published var currentUser: APIUser?
    @Published var trips: [APITripSummary] = []
    @Published var activeTrip: APITripDetail?
    @Published var errorMessage: String?
}
