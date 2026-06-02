import XCTest
@testable import Lvtantan

final class MoneyExpressionTests: XCTestCase {
    func testAddsAndDivides() throws {
        XCTAssertEqual(try MoneyExpression.evaluate("100+20/2"), Decimal(110))
    }

    func testSupportsParentheses() throws {
        XCTAssertEqual(try MoneyExpression.evaluate("(100+20)/2"), Decimal(60))
    }

    func testUsesPlainRoundingForHalfCents() throws {
        XCTAssertEqual(try MoneyExpression.evaluate("2.225"), Decimal(string: "2.23")!)
    }

    func testRejectsNegativeResult() throws {
        XCTAssertThrowsError(try MoneyExpression.evaluate("1-2"))
    }
}
