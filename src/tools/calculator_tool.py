from pydantic import BaseModel
import operator

class CalculatorInput(BaseModel):
    expression: str

def calculate(inp: CalculatorInput) -> dict[str, float | str]:
    print(f"[Tool] calculate: {inp.expression}")
    ops = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
    }

    try:
        parts = inp.expression.split()
        if len(parts) != 3:
            raise ValueError("Format: 'number operator number' (e.g., '5 * 2')")

        num1, op, num2 = parts
        num1 = float(num1)
        num2 = float(num2)

        if op not in ops:
            raise ValueError(f"Unsupported operator: {op}")

        result = ops[op](num1, num2)
        return {"result": result}
    except (ValueError, ZeroDivisionError) as e:
        return {"error": str(e)}
