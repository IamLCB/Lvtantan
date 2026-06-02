import SwiftUI

struct MemberListView: View {
    let members: [APIMember]

    var body: some View {
        List(members) { member in
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
            .accessibilityElement(children: .ignore)
            .accessibilityLabel(member.name)
            .accessibilityValue(member.status)
        }
        .navigationTitle("成员")
    }
}

#Preview {
    NavigationStack {
        MemberListView(
            members: [
                APIMember(id: "member-1", userId: "user-1", name: "小王", status: "active"),
                APIMember(id: "member-2", userId: "user-2", name: "小李", status: "active")
            ]
        )
    }
}
