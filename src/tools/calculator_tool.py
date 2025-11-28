from pydantic import BaseModel
import operator

class CalculatorInput(BaseModel):
    expression: str

def calculate(inp: CalculatorInput) -> dict[str, float | str]:
    """
    주어진 문자열 형식의 간단한 사칙연산 수식을 계산합니다.
    예: "1 + 2", "10 * 5"
    복잡한 연산이나 괄호는 지원하지 않습니다.
    """
    ops = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
    }

    try:
        parts = inp.expression.split()
        if len(parts) != 3:
            raise ValueError("수식은 '숫자 연산자 숫자' 형식이어야 합니다 (예: '5 * 2').")

        num1, op, num2 = parts
        num1 = float(num1)
        num2 = float(num2)

        if op not in ops:
            raise ValueError(f"지원하지 않는 연산자입니다: {op}")

        result = ops[op](num1, num2)
        return {"result": result}
    except (ValueError, ZeroDivisionError) as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Test cases
    test_expressions = ["10 + 5", "10 - 5", "10 * 5", "10 / 5", "5 / 0", "5 * 2 + 3", "invalid"]
    for expr in test_expressions:
        calc_input = CalculatorInput(expression=expr)
        calc_result = calculate(calc_input)
        print(f"Expression: '{expr}', Result: {calc_result}")
