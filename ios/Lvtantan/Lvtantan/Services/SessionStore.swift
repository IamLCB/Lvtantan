import Foundation

struct SessionStore {
    private let userIdKey = "lvtantan.userId"
    private let usernameKey = "lvtantan.username"

    func loadUser() -> APIUser? {
        guard let id = UserDefaults.standard.string(forKey: userIdKey),
              let username = UserDefaults.standard.string(forKey: usernameKey) else {
            return nil
        }
        return APIUser(id: id, username: username)
    }

    func save(user: APIUser) {
        UserDefaults.standard.set(user.id, forKey: userIdKey)
        UserDefaults.standard.set(user.username, forKey: usernameKey)
    }
}
