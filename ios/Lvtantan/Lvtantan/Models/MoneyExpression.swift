import Foundation

enum MoneyExpressionError: Error {
    case invalidExpression
    case nonPositiveAmount
}

enum MoneyExpression {
    static func evaluate(_ input: String) throws -> Decimal {
        var parser = Parser(input)
        let value = try parser.parse()
        let roundedValue = round(value, scale: 2)

        guard roundedValue > 0 else {
            throw MoneyExpressionError.nonPositiveAmount
        }

        return roundedValue
    }

    private static func round(_ value: Decimal, scale: Int) -> Decimal {
        var source = value
        var result = Decimal()
        NSDecimalRound(&result, &source, scale, .plain)
        return result
    }
}

private struct Parser {
    private let characters: [Character]
    private var index = 0

    init(_ input: String) {
        characters = Array(input)
    }

    mutating func parse() throws -> Decimal {
        skipWhitespace()

        guard !isAtEnd else {
            throw MoneyExpressionError.invalidExpression
        }

        let value = try parseExpression()
        skipWhitespace()

        guard isAtEnd else {
            throw MoneyExpressionError.invalidExpression
        }

        return value
    }

    private mutating func parseExpression() throws -> Decimal {
        var value = try parseTerm()

        while true {
            skipWhitespace()

            if consume("+") {
                value += try parseTerm()
            } else if consume("-") {
                value -= try parseTerm()
            } else {
                return value
            }
        }
    }

    private mutating func parseTerm() throws -> Decimal {
        var value = try parseFactor()

        while true {
            skipWhitespace()

            if consume("*") {
                value *= try parseFactor()
            } else if consume("/") {
                let divisor = try parseFactor()

                guard divisor != 0 else {
                    throw MoneyExpressionError.invalidExpression
                }

                value /= divisor
            } else {
                return value
            }
        }
    }

    private mutating func parseFactor() throws -> Decimal {
        skipWhitespace()

        if consume("(") {
            let value = try parseExpression()
            skipWhitespace()

            guard consume(")") else {
                throw MoneyExpressionError.invalidExpression
            }

            return value
        }

        return try parseNumber()
    }

    private mutating func parseNumber() throws -> Decimal {
        let start = index
        var hasDigitsBeforeDecimal = false
        var hasDigitsAfterDecimal = false

        while let character = current, character.isWholeNumber {
            hasDigitsBeforeDecimal = true
            advance()
        }

        if consume(".") {
            while let character = current, character.isWholeNumber {
                hasDigitsAfterDecimal = true
                advance()
            }
        }

        guard hasDigitsBeforeDecimal || hasDigitsAfterDecimal else {
            throw MoneyExpressionError.invalidExpression
        }

        let token = String(characters[start..<index])
        let normalizedToken = token.first == "." ? "0\(token)" : token

        guard let value = Decimal(string: normalizedToken, locale: Locale(identifier: "en_US_POSIX")) else {
            throw MoneyExpressionError.invalidExpression
        }

        return value
    }

    private var current: Character? {
        isAtEnd ? nil : characters[index]
    }

    private var isAtEnd: Bool {
        index >= characters.count
    }

    private mutating func consume(_ character: Character) -> Bool {
        guard current == character else {
            return false
        }

        advance()
        return true
    }

    private mutating func advance() {
        index += 1
    }

    private mutating func skipWhitespace() {
        while let character = current, character.isWhitespace {
            advance()
        }
    }
}
