import json
from collections import Counter
from pathlib import Path


# Caminho raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Golden Dataset
DATASET_PATH = PROJECT_ROOT / "datasets" / "golden_dataset.json"


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


def load_dataset(path: Path) -> list[dict]:
    """
    Carrega o Golden Dataset a partir do arquivo JSON.
    """

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
    """
    Valida individualmente um caso do Golden Dataset.

    Retorna uma lista de erros encontrados.
    """

    errors = []

    # Verifica campos obrigatórios
    missing_fields = REQUIRED_FIELDS - case.keys()

    if missing_fields:
        errors.append(
            f"Campos obrigatórios ausentes: {sorted(missing_fields)}"
        )

    case_id = case.get("id", f"índice {index}")

    # Cada caso deve possuir input OU turns
    has_input = "input" in case
    has_turns = "turns" in case

    if has_input == has_turns:
        errors.append(
            "O caso deve possuir exatamente um dos campos: "
            "'input' ou 'turns'."
        )

    # Validação de caso single-turn
    if has_input:
        if not isinstance(case["input"], str) or not case["input"].strip():
            errors.append(
                "O campo 'input' deve ser uma string não vazia."
            )

    # Validação de caso multi-turn
    if has_turns:
        turns = case["turns"]

        if not isinstance(turns, list):
            errors.append(
                "O campo 'turns' deve ser uma lista."
            )
        else:
            if len(turns) < 2:
                errors.append(
                    "Um caso multi-turn deve possuir pelo menos 2 turnos."
                )

            for turn_index, turn in enumerate(turns, start=1):
                if not isinstance(turn, str) or not turn.strip():
                    errors.append(
                        f"Turno {turn_index} deve ser uma string não vazia."
                    )

        if case.get("category") != "multi_turn":
            errors.append(
                "Casos com 'turns' devem possuir "
                "category = 'multi_turn'."
            )

    # Tipos básicos
    if not isinstance(case.get("tool_expected"), bool):
        errors.append(
            "'tool_expected' deve ser true ou false."
        )

    if not isinstance(case.get("should_abstain"), bool):
        errors.append(
            "'should_abstain' deve ser true ou false."
        )

    expected_source = case.get("expected_source")

    if expected_source is not None and not isinstance(expected_source, str):
        errors.append(
            "'expected_source' deve ser uma string ou null."
        )

    if errors:
        return [
            f"{case_id}: {error}"
            for error in errors
        ]

    return []


def validate_dataset(dataset: list[dict]) -> None:
    """
    Valida a estrutura completa do Golden Dataset.
    """

    errors = []

    # Quantidade esperada atualmente
    if len(dataset) != 18:
        errors.append(
            f"Esperados 18 casos, mas foram encontrados {len(dataset)}."
        )

    # IDs
    ids = [case.get("id") for case in dataset]

    duplicated_ids = [
        case_id
        for case_id, count in Counter(ids).items()
        if count > 1
    ]

    if duplicated_ids:
        errors.append(
            f"IDs duplicados encontrados: {duplicated_ids}"
        )

    # Verifica sequência GD-001 ... GD-018
    expected_ids = [
        f"GD-{number:03d}"
        for number in range(1, 19)
    ]

    if ids != expected_ids:
        errors.append(
            "Os IDs não estão na sequência esperada "
            "GD-001 até GD-018."
        )

    # Valida cada caso
    for index, case in enumerate(dataset, start=1):

        if not isinstance(case, dict):
            errors.append(
                f"Item {index}: o caso deve ser um objeto JSON."
            )
            continue

        errors.extend(
            validate_case(case, index)
        )

    # Resultado
    if errors:
        print("\n❌ Golden Dataset inválido.\n")

        for error in errors:
            print(f"- {error}")

        raise SystemExit(1)

    print("\n✅ Golden Dataset validado com sucesso!")


def print_summary(dataset: list[dict]) -> None:
    """
    Exibe um resumo simples da composição do dataset.
    """

    categories = Counter(
        case["category"]
        for case in dataset
    )

    tool_expected_count = sum(
        case["tool_expected"]
        for case in dataset
    )

    abstention_count = sum(
        case["should_abstain"]
        for case in dataset
    )

    multi_turn_count = sum(
        "turns" in case
        for case in dataset
    )

    print("\n--- Resumo do Golden Dataset ---")
    print(f"Total de casos: {len(dataset)}")

    print("\nCasos por categoria:")

    for category, count in categories.items():
        print(f"  {category}: {count}")

    print(
        f"\nCasos que esperam uso de ferramenta: "
        f"{tool_expected_count}"
    )

    print(
        f"Casos que esperam abstenção: "
        f"{abstention_count}"
    )

    print(
        f"Casos multi-turn: "
        f"{multi_turn_count}"
    )


def main():
    print(f"Carregando dataset: {DATASET_PATH}")

    dataset = load_dataset(DATASET_PATH)

    validate_dataset(dataset)

    print_summary(dataset)


if __name__ == "__main__":
    main()