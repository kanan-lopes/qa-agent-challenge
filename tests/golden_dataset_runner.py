import argparse
import json
import os
import uuid
from collections import Counter
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError


# ============================================================
# CONFIGURAÇÃO
# ============================================================

AWS_REGION = "us-east-1"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    PROJECT_ROOT
    / "datasets"
    / "golden_dataset.json"
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "results"
    / "baseline"
)

HARNESS_ARN = os.getenv("HARNESS_ARN")

PILOT_IDS = {
    "GD-001",
    "GD-011",
    "GD-016",
}


REQUIRED_FIELDS = {
    "id",
    "category",
    "descricao_pt",
    "objetivo_pt",
    "expected_answer",
    "expected_source",
    "tool_expected",
    "should_abstain",
    "expected_behavior",
}


# ============================================================
# GOLDEN DATASET
# ============================================================

def load_dataset(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Golden Dataset não encontrado em: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not isinstance(dataset, list):
        raise ValueError(
            "O Golden Dataset deve possuir uma lista JSON na raiz."
        )

    return dataset


def validate_case(case: dict, index: int) -> list[str]:
    errors = []

    case_id = case.get(
        "id",
        f"índice {index}",
    )

    missing_fields = (
        REQUIRED_FIELDS
        - case.keys()
    )

    if missing_fields:
        errors.append(
            f"{case_id}: campos obrigatórios ausentes: "
            f"{sorted(missing_fields)}"
        )

    has_input = "input" in case
    has_turns = "turns" in case

    if has_input == has_turns:
        errors.append(
            f"{case_id}: deve possuir exatamente "
            "'input' OU 'turns'."
        )

    if has_input:
        if (
            not isinstance(case["input"], str)
            or not case["input"].strip()
        ):
            errors.append(
                f"{case_id}: 'input' deve ser "
                "uma string não vazia."
            )

    if has_turns:
        turns = case["turns"]

        if not isinstance(turns, list):
            errors.append(
                f"{case_id}: 'turns' deve ser uma lista."
            )

        elif len(turns) < 2:
            errors.append(
                f"{case_id}: caso multi-turn precisa "
                "de pelo menos 2 turnos."
            )

        else:
            for number, turn in enumerate(
                turns,
                start=1,
            ):
                if (
                    not isinstance(turn, str)
                    or not turn.strip()
                ):
                    errors.append(
                        f"{case_id}: turno {number} inválido."
                    )

        if case.get("category") != "multi_turn":
            errors.append(
                f"{case_id}: casos com 'turns' devem "
                "usar category='multi_turn'."
            )

    if not isinstance(
        case.get("tool_expected"),
        bool,
    ):
        errors.append(
            f"{case_id}: 'tool_expected' deve "
            "ser true ou false."
        )

    if not isinstance(
        case.get("should_abstain"),
        bool,
    ):
        errors.append(
            f"{case_id}: 'should_abstain' deve "
            "ser true ou false."
        )

    expected_source = case.get(
        "expected_source"
    )

    if (
        expected_source is not None
        and not isinstance(
            expected_source,
            str,
        )
    ):
        errors.append(
            f"{case_id}: 'expected_source' deve "
            "ser string ou null."
        )

    return errors


def validate_dataset(
    dataset: list[dict],
) -> None:
    errors = []

    if len(dataset) != 18:
        errors.append(
            f"Esperados 18 casos, mas foram "
            f"encontrados {len(dataset)}."
        )

    ids = [
        case.get("id")
        for case in dataset
    ]

    duplicated_ids = [
        case_id
        for case_id, count
        in Counter(ids).items()
        if count > 1
    ]

    if duplicated_ids:
        errors.append(
            f"IDs duplicados: {duplicated_ids}"
        )

    expected_ids = [
        f"GD-{number:03d}"
        for number in range(1, 19)
    ]

    if ids != expected_ids:
        errors.append(
            "Os IDs não estão na sequência "
            "GD-001 até GD-018."
        )

    for index, case in enumerate(
        dataset,
        start=1,
    ):
        if not isinstance(case, dict):
            errors.append(
                f"Item {index}: deve ser um objeto JSON."
            )
            continue

        errors.extend(
            validate_case(
                case,
                index,
            )
        )

    if errors:
        print(
            "\n❌ Golden Dataset inválido.\n"
        )

        for error in errors:
            print(f"- {error}")

        raise SystemExit(1)

    print(
        "\n✅ Golden Dataset validado com sucesso!"
    )


# ============================================================
# AGENTCORE HARNESS
# ============================================================

def create_harness_client():
    if not HARNESS_ARN:
        raise RuntimeError(
            "A variável de ambiente HARNESS_ARN "
            "não está configurada."
        )

    return boto3.client(
        "bedrock-agentcore",
        region_name=AWS_REGION,
    )


def invoke_harness(
    client,
    text: str,
    actor_id: str,
    session_id: str,
) -> dict:
    """
    Executa um único turno no Harness.

    Importante:
    esta função NÃO determina se houve
    Retrieve real da Knowledge Base.
    Isso será validado posteriormente
    através de traces/observabilidade.
    """

    response = client.invoke_harness(
        harnessArn=HARNESS_ARN,
        qualifier="DEFAULT",
        runtimeSessionId=session_id,
        actorId=actor_id,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": text
                    }
                ],
            }
        ],
    )

    answer_parts = []
    runtime_errors = []

    for event in response["stream"]:

        if "contentBlockDelta" in event:
            delta = (
                event["contentBlockDelta"]
                .get("delta", {})
            )

            text_delta = delta.get("text")

            if text_delta:
                answer_parts.append(
                    text_delta
                )

        if "runtimeClientError" in event:
            runtime_errors.append(
                event["runtimeClientError"]
                .get(
                    "message",
                    "Erro não especificado",
                )
            )

    return {
        "answer": "".join(
            answer_parts
        ).strip(),
        "runtime_errors": runtime_errors,
    }


# ============================================================
# EXECUÇÃO DE CASOS
# ============================================================

def run_single_turn_case(
    client,
    case: dict,
    actor_prefix: str,
    run_id: str,
) -> dict:
    case_id = case["id"]

    actor_id = (
        f"{actor_prefix}-{run_id}-{case_id.lower()}"
    )

    session_id = str(
        uuid.uuid4()
    )

    print(
        f"\n▶ {case_id}"
    )

    print(
        f"Pergunta: {case['input']}"
    )

    result = invoke_harness(
        client=client,
        text=case["input"],
        actor_id=actor_id,
        session_id=session_id,
    )

    print(
        f"Resposta: {result['answer']}"
    )

    return {
        "id": case_id,
        "category": case["category"],
        "input": case["input"],
        "expected_answer": (
            case["expected_answer"]
        ),
        "actual_answer": (
            result["answer"]
        ),
        "expected_source": (
            case["expected_source"]
        ),
        "tool_expected": (
            case["tool_expected"]
        ),
        "should_abstain": (
            case["should_abstain"]
        ),
        "expected_behavior": (
            case["expected_behavior"]
        ),
        "run_id": run_id,
        "actor_id": actor_id,
        "session_id": session_id,

        # Ainda não inferimos isso pela resposta.
        "tool_observed": None,

        "execution_status": (
            "completed"
            if not result["runtime_errors"]
            else "runtime_error"
        ),

        "runtime_errors": (
            result["runtime_errors"]
        ),
    }


def run_multi_turn_case(
    client,
    case: dict,
    actor_prefix: str,
    run_id: str,
) -> dict:
    case_id = case["id"]

    actor_id = (
        f"{actor_prefix}-{run_id}-{case_id.lower()}"
    )

    # O MESMO session_id será usado
    # em todos os turnos deste teste.
    session_id = str(
        uuid.uuid4()
    )

    turn_results = []

    print(
        f"\n▶ {case_id} — MULTI-TURN"
    )

    for turn_number, turn in enumerate(
        case["turns"],
        start=1,
    ):
        print(
            f"\nTurno {turn_number}: {turn}"
        )

        result = invoke_harness(
            client=client,
            text=turn,
            actor_id=actor_id,
            session_id=session_id,
        )

        print(
            f"Resposta: {result['answer']}"
        )

        turn_results.append(
            {
                "turn": turn_number,
                "input": turn,
                "actual_answer": (
                    result["answer"]
                ),
                "runtime_errors": (
                    result["runtime_errors"]
                ),
            }
        )

    final_answer = (
        turn_results[-1]["actual_answer"]
        if turn_results
        else ""
    )

    has_error = any(
        turn["runtime_errors"]
        for turn in turn_results
    )

    return {
        "id": case_id,
        "category": case["category"],
        "turns": case["turns"],
        "expected_answer": (
            case["expected_answer"]
        ),
        "actual_answer": final_answer,
        "turn_results": turn_results,
        "expected_source": (
            case["expected_source"]
        ),
        "tool_expected": (
            case["tool_expected"]
        ),
        "should_abstain": (
            case["should_abstain"]
        ),
        "expected_behavior": (
            case["expected_behavior"]
        ),
        "run_id": run_id,
        "actor_id": actor_id,
        "session_id": session_id,
        "tool_observed": None,
        "execution_status": (
            "runtime_error"
            if has_error
            else "completed"
        ),
    }


def run_case(
    client,
    case: dict,
    actor_prefix: str,
    run_id: str,
) -> dict:

    if "turns" in case:
        return run_multi_turn_case(
            client,
            case,
            actor_prefix,
            run_id,
        )

    return run_single_turn_case(
        client,
        case,
        actor_prefix,
        run_id,
    )


# ============================================================
# SALVAMENTO
# ============================================================

def save_results(
    results: list[dict],
    filename: str,
) -> Path:
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        RESULTS_DIR
        / filename
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return output_path


# ============================================================
# MODOS DE EXECUÇÃO
# ============================================================

def select_cases(
    dataset: list[dict],
    mode: str,
) -> list[dict]:

    if mode == "pilot":
        return [
            case
            for case in dataset
            if case["id"] in PILOT_IDS
        ]

    if mode == "all":
        return dataset

    return []


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=[
            "validate",
            "pilot",
            "all",
        ],
        default="validate",
        help=(
            "validate = apenas valida o dataset; "
            "pilot = GD-001, GD-011 e GD-016; "
            "all = executa todos os 18 casos."
        ),
    )

    args = parser.parse_args()

    print(
        f"Carregando dataset: {DATASET_PATH}"
    )

    dataset = load_dataset(
        DATASET_PATH
    )

    validate_dataset(
        dataset
    )

    if args.mode == "validate":
        print(
            "\nValidação concluída. "
            "Nenhuma chamada à AWS foi realizada."
        )
        return

    client = create_harness_client()

    selected_cases = select_cases(
        dataset,
        args.mode,
    )

    run_id = uuid.uuid4().hex[:8]

    if args.mode == "pilot":
        actor_prefix = "pilot"
    else:
        actor_prefix = "baseline-full"

    print(
        f"\nRun ID: {run_id}"
    )

    print(
        f"Prefixo dos Actor IDs: {actor_prefix}"
    )

    print(
        f"\nCasos selecionados: "
        f"{len(selected_cases)}"
    )

    results = []

    for case in selected_cases:
        try:
            result = run_case(
                client,
                case,
                actor_prefix,
                run_id,
            )

        except (
            ClientError,
            BotoCoreError,
            Exception,
        ) as error:
            print(
                f"\n❌ Erro em {case['id']}: "
                f"{error}"
            )

            result = {
                "id": case["id"],
                "category": (
                    case["category"]
                ),
                "execution_status": "error",
                "error": str(error),
            }

        results.append(
            result
        )

    if args.mode == "pilot":
        filename = (
            f"golden_results_raw_pilot_{run_id}.json"
        )
    else:
        filename = (
            f"golden_results_raw_{run_id}.json"
        )

    output_path = save_results(
        results,
        filename,
    )

    print(
        "\n================================"
    )

    print(
        "Execução concluída."
    )

    print(
        f"Resultados salvos em:\n"
        f"{output_path}"
    )


if __name__ == "__main__":
    main()
