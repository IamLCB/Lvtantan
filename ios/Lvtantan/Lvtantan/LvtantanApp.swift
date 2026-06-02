//
//  LvtantanApp.swift
//  Lvtantan
//
//  Created by 陆诚彬 on 2026/6/2.
//

import SwiftUI

@main
struct LvtantanApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(appState)
        }
    }
}
