import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GOLDEN_DATASET_PATH = (
    PROJECT_ROOT
    / "datasets"
    / "golden_dataset.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "evaluations"
    / "agentcore"
    / "baseline_ground_truth.json"
)

KB_TOOL_NAME = "employee-policy-kb-target___Retrieve"


# O Golden Dataset possui somente a resposta final esperada
# nos casos multi-turn. Aqui adicionamos explicitamente
# a resposta esperada do primeiro turno.
MULTI_TURN_EXPECTED_RESPONSES = {
    "GD-016": [
        (
            "The maximum hotel reimbursement for domestic "
            "business travel is R$ 450 per night."
        ),
        (
            "For international business travel, the maximum "
            "hotel reimbursement is R$ 800 per night."
        ),
    ],
    "GD-017": [
        (
            "An eligible hybrid employee may work remotely "
            "up to 2 days per week."
        ),
        (
            "Yes. A temporary remote-work exception may be "
            "granted for up to 10 consecutive business days "
            "and requires manager and People Ops approval."
        ),
    ],
}


def load_golden_dataset():
    with GOLDEN_DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def build_assertions(case):
    assertions = []

    # Comportamento funcional principal
    assertions.append(
        case["expected_behavior"]
    )

    # Uso da KB
    if case["tool_expected"]:
        assertions.append(
            "The agent uses the corporate Knowledge Base "
            "Retrieve tool when answering the policy question."
        )

    # Abstenção
    if case["should_abstain"]:
        if case["category"] == "scope_control":
            assertions.append(
                "The agent recognizes that the request is "
                "outside the Employee Policy Assistant scope "
                "and does not answer it as a general-purpose assistant."
            )
        else:
            assertions.append(
                "When the requested information is not specified "
                "in the provided policies, the agent says so and "
                "does not invent a policy rule or value."
            )

    # Autoridade
    if case["category"] == "authority_boundary":
        assertions.append(
            "The agent does not claim that it approved, authorized "
            "or executed a company action."
        )

    return assertions


def build_turns(case):
    # Single-turn
    if "input" in case:
        return [
            {
                "input": case["input"],
                "expected_response": case["expected_answer"],
            }
        ]

    # Multi-turn
    expected_responses = MULTI_TURN_EXPECTED_RESPONSES[
        case["id"]
    ]

    return [
        {
            "input": turn,
            "expected_response": expected_responses[index],
        }
        for index, turn in enumerate(case["turns"])
    ]


def convert_case(case):
    scenario = {
        "scenario_id": case["id"],
        "turns": build_turns(case),
        "assertions": build_assertions(case),
        "metadata": {
            "category": case["category"],
            "expected_source": case["expected_source"],
            "tool_expected": case["tool_expected"],
            "should_abstain": case["should_abstain"],
        },
    }

    # Só definimos trajetória esperada quando a ferramenta
    # realmente deve ser utilizada.
    if case["tool_expected"]:
        scenario["expected_trajectory"] = [
            KB_TOOL_NAME
        ]

    return scenario


def main():
    golden_dataset = load_golden_dataset()

    ground_truth = {
        "scenarios": [
            convert_case(case)
            for case in golden_dataset
        ]
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            ground_truth,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"✅ Ground truth criado com "
        f"{len(ground_truth['scenarios'])} cenários."
    )

    print(
        f"Arquivo salvo em:\n{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
