import json
from pathlib import Path

from deepeval.metrics import (
    AnswerRelevancyMetric,
    GEval,
)
from deepeval.models import OllamaModel
from deepeval.test_case import (
    LLMTestCase,
    SingleTurnParams,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASELINE_RESULTS_PATH = (
    PROJECT_ROOT
    / "results"
    / "baseline"
    / "golden_results_raw_972e97b8.json"
)

OLLAMA_BASE_URL = "http://localhost:11434"

JUDGE_MODEL_NAME = "gpt-oss:20b"


# ============================================================
# CASOS DO SMOKE TEST
# ============================================================
#
# GD-003:
#   política factual / reimbursement.
#   É um bom caso para observar uma resposta problemática.
#
# GD-015:
#   authority boundary.
#   É um bom contraste porque o agente acerta parte importante
#   do comportamento.
#
# Não estamos tentando calcular a baseline completa aqui.
# Queremos apenas verificar o funcionamento do judge local.
# ============================================================

SMOKE_CASE_IDS = [
    "GD-003",
    "GD-015",
]


# ============================================================
# MODELO JUIZ
# ============================================================

def create_judge():
    """
    Cria o modelo local usado pelo DeepEval como LLM-as-a-Judge.
    """

    return OllamaModel(
        model=JUDGE_MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
    )


# ============================================================
# CARREGAMENTO DOS RESULTADOS DA BASELINE
# ============================================================

def load_baseline_results():
    """
    Usa respostas já congeladas da baseline oficial.

    O smoke test NÃO reexecuta o AgentCore Harness.
    """

    if not BASELINE_RESULTS_PATH.exists():
        raise FileNotFoundError(
            "Arquivo da baseline não encontrado:\n"
            f"{BASELINE_RESULTS_PATH}"
        )

    with BASELINE_RESULTS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def find_case(results, case_id):
    """
    Localiza um caso pelo ID.
    """

    for case in results:
        if case.get("id") == case_id:
            return case

    raise ValueError(
        f"Caso {case_id} não encontrado "
        "na baseline."
    )


# ============================================================
# MÉTRICAS
# ============================================================

def create_answer_relevancy_metric(judge):
    """
    Threshold exigido pelo projeto:
    Answer Relevancy >= 0.70
    """

    return AnswerRelevancyMetric(
        threshold=0.70,
        model=judge,
        include_reason=True,
        async_mode=False,
    )


def create_g_eval_metric(judge):
    """
    G-Eval de qualidade da resposta em relação
    ao expected answer.

    Threshold exigido pelo projeto:
    G-Eval >= 0.80
    """

    return GEval(
        name="Policy Answer Quality",

        evaluation_steps=[
            (
                "Compare the actual output with the expected "
                "output for the employee policy question."
            ),
            (
                "Check whether the actual output provides the "
                "essential policy information required by the "
                "expected output."
            ),
            (
                "Penalize incorrect policy values, thresholds, "
                "deadlines, eligibility rules, approval rules, "
                "or other policy facts."
            ),
            (
                "Penalize answers that omit the core information "
                "needed to answer the user's question."
            ),
            (
                "Do not require identical wording when the actual "
                "output conveys the same correct meaning."
            ),
        ],

        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.EXPECTED_OUTPUT,
        ],

        threshold=0.80,
        model=judge,
        async_mode=False,
    )


# ============================================================
# VALIDAÇÃO DO SCORE
# ============================================================

def validate_metric_result(
    metric_name,
    score,
):
    """
    O smoke test verifica apenas se o DeepEval conseguiu
    produzir um score válido.

    Ele NÃO exige que o Agent v1 passe no threshold.
    """

    if score is None:
        raise RuntimeError(
            f"{metric_name} não retornou score."
        )

    if not isinstance(score, (int, float)):
        raise TypeError(
            f"{metric_name} retornou score inválido: "
            f"{score!r}"
        )

    if not 0 <= float(score) <= 1:
        raise ValueError(
            f"{metric_name} retornou score fora "
            f"do intervalo 0-1: {score}"
        )


# ============================================================
# EXECUÇÃO DE UM CASO
# ============================================================

def evaluate_case(
    case,
    judge,
):
    """
    Avalia um único caso usando duas métricas.
    """

    case_id = case["id"]

    user_input = case["input"]
    actual_output = case["actual_answer"]
    expected_output = case["expected_answer"]

    test_case = LLMTestCase(
        input=user_input,
        actual_output=actual_output,
        expected_output=expected_output,
    )

    print(
        "\n\n"
        "========================================"
    )

    print(
        f"CASO: {case_id}"
    )

    print(
        "========================================"
    )

    print(
        f"\nInput:\n{user_input}"
    )

    print(
        f"\nActual output:\n{actual_output}"
    )

    print(
        f"\nExpected output:\n{expected_output}"
    )

    # ========================================================
    # ANSWER RELEVANCY
    # ========================================================

    answer_relevancy = (
        create_answer_relevancy_metric(
            judge
        )
    )

    print(
        "\nExecutando Answer Relevancy..."
    )

    answer_relevancy.measure(
        test_case
    )

    validate_metric_result(
        "Answer Relevancy",
        answer_relevancy.score,
    )

    print(
        f"\nAnswer Relevancy score: "
        f"{answer_relevancy.score}"
    )

    print(
        "Threshold: 0.70"
    )

    print(
        f"Passou: "
        f"{answer_relevancy.score >= 0.70}"
    )

    print(
        f"Reason:\n"
        f"{answer_relevancy.reason}"
    )

    # ========================================================
    # G-EVAL
    # ========================================================

    g_eval = create_g_eval_metric(
        judge
    )

    print(
        "\nExecutando G-Eval..."
    )

    g_eval.measure(
        test_case
    )

    validate_metric_result(
        "G-Eval",
        g_eval.score,
    )

    print(
        f"\nG-Eval score: "
        f"{g_eval.score}"
    )

    print(
        "Threshold: 0.80"
    )

    print(
        f"Passou: "
        f"{g_eval.score >= 0.80}"
    )

    print(
        f"Reason:\n"
        f"{g_eval.reason}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "========================================"
    )

    print(
        "DEEPEVAL + OLLAMA SMOKE TEST"
    )

    print(
        "========================================"
    )

    print(
        f"\nJudge model: "
        f"{JUDGE_MODEL_NAME}"
    )

    print(
        f"Ollama URL: "
        f"{OLLAMA_BASE_URL}"
    )

    print(
        f"Baseline:"
        f"\n{BASELINE_RESULTS_PATH}"
    )

    print(
        "\nEste smoke test NÃO executa "
        "o AgentCore novamente."
    )

    print(
        "Ele utiliza respostas já congeladas "
        "da baseline."
    )

    results = (
        load_baseline_results()
    )

    judge = create_judge()

    for case_id in SMOKE_CASE_IDS:

        case = find_case(
            results,
            case_id,
        )

        evaluate_case(
            case,
            judge,
        )

    print(
        "\n\n========================================"
    )

    print(
        "SMOKE TEST CONCLUÍDO"
    )

    print(
        "========================================"
    )

    print(
        "\nSe os dois casos produziram scores "
        "entre 0 e 1 e razões coerentes, "
        "a integração DeepEval + Ollama "
        "está funcional."
    )


if __name__ == "__main__":
    main()
