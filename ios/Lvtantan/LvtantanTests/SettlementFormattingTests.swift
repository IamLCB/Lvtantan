import XCTest
@testable import Lvtantan

final class SettlementFormattingTests: XCTestCase {
    func testTransferTextFormatsSettlementTransfer() {
        let transfer = APISettlementTransfer(
            fromMemberId: "member-li",
            fromMemberName: "小李",
            toMemberId: "member-wang",
            toMemberName: "小王",
            amount: "50.00"
        )

        XCTAssertEqual(SettlementView.transferText(transfer), "小李 转给 小王 50.00 元")
    }
}
