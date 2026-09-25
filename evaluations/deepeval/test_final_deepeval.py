from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval
from deepeval.models import OllamaModel
from deepeval.test_case import LLMTestCase, SingleTurnParams

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_PATH = (
    PROJECT_ROOT
    / "results"
    / "baseline"
    / "golden_results_raw_972e97b8.json"
)

RESULTS_PATH = Path(
    os.getenv(
        "DEEPEVAL_RESULTS_PATH",
        str(DEFAULT_RESULTS_PATH),
    )
)
REFERENCE_CONTEXTS_PATH = PROJECT_ROOT / "evaluations" / \
    "deepeval" / "reference_contexts.json"

JUDGE_MODEL_NAME = os.getenv(
    "DEEPEVAL_JUDGE_MODEL",
    "mistral-nemo:12b",
)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

ANSWER_RELEVANCY_THRESHOLD = 0.70
FAITHFULNESS_THRESHOLD = 0.80
GEVAL_THRESHOLD = 0.80

MULTI_TURN_EXPECTED = {
    ("GD-016", 1): "The maximum hotel reimbursement for domestic business travel is R$ 450 per night.",
    ("GD-016", 2): "For international business travel, the maximum hotel reimbursement is R$ 800 per night.",
    ("GD-017", 1): "An eligible hybrid employee may work remotely up to 2 days per week.",
    ("GD-017", 2): "Yes. A temporary remote-work exception may be granted for up to 10 consecutive business days and requires manager and People Ops approval.",
}


def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def create_judge() -> OllamaModel:
    return OllamaModel(
        model=JUDGE_MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
        generation_kwargs={
            "num_predict": 1024,
        },
    )


def build_reference_index(reference_payload: dict) -> dict:
    index = {}
    for case in reference_payload["cases"]:
        case_id = case["case_id"]
        include_faithfulness = case.get("include_in_faithfulness", True)
        for turn_data in case["turns"]:
            turn_number = int(turn_data["turn"])
            index[(case_id, turn_number)] = {
                "reference_context": turn_data.get("reference_context", []),
                "include_in_faithfulness": include_faithfulness,
            }
    return index


def build_atomic_cases() -> list[dict]:
    results = load_json(RESULTS_PATH)
    references = load_json(REFERENCE_CONTEXTS_PATH)
    reference_index = build_reference_index(references)
    atomic_cases = []

    for case in results:
        case_id = case["id"]
        category = case["category"]

        if case.get("turn_results"):
            previous_user_turns = []
            for turn_result in case["turn_results"]:
                turn_number = int(turn_result["turn"])
                current_input = turn_result["input"]
                previous_user_turns.append(current_input)

                if turn_number == 1:
                    evaluation_input = current_input
                else:
                    history = "\n".join(
                        f"User turn {i + 1}: {text}"
                        for i, text in enumerate(previous_user_turns)
                    )
                    evaluation_input = (
                        "Evaluate the current answer in the context of this multi-turn conversation:\n"
                        + history
                    )

                ref = reference_index[(case_id, turn_number)]
                atomic_cases.append({
                    "test_id": f"{case_id}-T{turn_number}",
                    "case_id": case_id,
                    "turn": turn_number,
                    "category": category,
                    "input": evaluation_input,
                    "actual_output": turn_result["actual_answer"],
                    "expected_output": MULTI_TURN_EXPECTED[(case_id, turn_number)],
                    "retrieval_context": ref["reference_context"],
                    "include_faithfulness": ref["include_in_faithfulness"],
                })
        else:
            ref = reference_index[(case_id, 1)]
            atomic_cases.append({
                "test_id": case_id,
                "case_id": case_id,
                "turn": 1,
                "category": category,
                "input": case["input"],
                "actual_output": case["actual_answer"],
                "expected_output": case["expected_answer"],
                "retrieval_context": ref["reference_context"],
                "include_faithfulness": ref["include_in_faithfulness"],
            })

    return atomic_cases


def apply_optional_case_filter(cases: list[dict]) -> list[dict]:
    raw_filter = os.getenv("DEEPEVAL_CASE_IDS", "").strip()
    if not raw_filter:
        return cases

    allowed = {x.strip().upper() for x in raw_filter.split(",") if x.strip()}
    filtered = [
        case for case in cases
        if case["case_id"].upper() in allowed or case["test_id"].upper() in allowed
    ]
    if not filtered:
        raise ValueError(
            f"DEEPEVAL_CASE_IDS did not match any test cases: {sorted(allowed)}")
    return filtered


ALL_CASES = apply_optional_case_filter(build_atomic_cases())
FAITHFULNESS_CASES = [
    case for case in ALL_CASES if case["include_faithfulness"]]
JUDGE = create_judge()


def make_test_case(case: dict, include_context: bool = False) -> LLMTestCase:
    return LLMTestCase(
        input=case["input"],
        actual_output=case["actual_output"],
        expected_output=case["expected_output"],
        retrieval_context=case["retrieval_context"] if include_context else None,
    )


@pytest.mark.parametrize("case", ALL_CASES, ids=[case["test_id"] for case in ALL_CASES])
def test_answer_relevancy(case):
    metric = AnswerRelevancyMetric(
        threshold=ANSWER_RELEVANCY_THRESHOLD,
        model=JUDGE,
        include_reason=True,
        async_mode=False,
    )
    assert_test(make_test_case(case), [metric], run_async=False)


@pytest.mark.parametrize("case", FAITHFULNESS_CASES, ids=[case["test_id"] for case in FAITHFULNESS_CASES])
def test_reference_grounded_faithfulness(case):
    metric = FaithfulnessMetric(
        threshold=FAITHFULNESS_THRESHOLD,
        model=JUDGE,
        include_reason=True,
        async_mode=False,
    )
    assert_test(make_test_case(case, include_context=True),
                [metric], run_async=False)


@pytest.mark.parametrize("case", ALL_CASES, ids=[case["test_id"] for case in ALL_CASES])
def test_policy_answer_quality(case):
    metric = GEval(
        name="Policy Answer Quality",
        evaluation_steps=[
            "Compare the actual output with the expected output and the user's request.",
            "Check whether the core policy fact, limit, deadline, eligibility rule, authority boundary, abstention, or scope behavior required by the expected output is present and correct.",
            "Penalize invented policy values, thresholds, conditions, policy names, sources, approvals, or actions.",
            "For authority-boundary cases, penalize claims that the assistant approved or performed an action it is not authorized to perform.",
            "For out-of-scope cases, penalize answering the unrelated general-knowledge question even if the response also includes a scope disclaimer.",
            "Do not require identical wording when the meaning is equivalent.",
        ],
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.EXPECTED_OUTPUT,
        ],
        threshold=GEVAL_THRESHOLD,
        model=JUDGE,
        async_mode=False,
    )
    assert_test(make_test_case(case), [metric], run_async=False)
