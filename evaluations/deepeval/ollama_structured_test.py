from ollama import chat
from pydantic import BaseModel


class JudgeResult(BaseModel):
    score: float
    reason: str


MODEL = "gpt-oss:20b"


def main():
    print(f"Testando structured output com: {MODEL}")

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    "Evaluate whether the following answer is relevant "
                    "to the question.\n\n"
                    "Question: What is the daily meal reimbursement limit?\n"
                    "Answer: The company reimburses up to $75 per day.\n\n"
                    "Return a score from 0 to 1 and a short reason."
                ),
            }
        ],
        format=JudgeResult.model_json_schema(),
        options={
            "temperature": 0,
        },
    )

    result = JudgeResult.model_validate_json(
        response.message.content
    )

    print("\nStructured output OK")
    print(f"Score: {result.score}")
    print(f"Reason: {result.reason}")


if __name__ == "__main__":
    main()
