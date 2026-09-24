import os
from collections import Counter
from pathlib import Path

import boto3

from bedrock_agentcore.evaluation import (
    AgentInvokerInput,
    AgentInvokerOutput,
    CloudWatchAgentSpanCollector,
    EvaluationRunConfig,
    EvaluatorConfig,
    FileDatasetProvider,
    OnDemandEvaluationDatasetRunner,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

AWS_REGION = "us-east-1"
HARNESS_QUALIFIER = "DEFAULT"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "evaluations"
    / "agentcore"
    / "baseline_ground_truth.json"
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "results"
    / "v2"
    / "evaluations"
)

RESULTS_PATH = (
    RESULTS_DIR
    / "agentcore_v2_policy_compliance_results.json"
)


# ============================================================
# VARIÁVEIS DE AMBIENTE
# ============================================================

HARNESS_ARN = os.getenv("HARNESS_ARN")

HARNESS_LOG_GROUP = os.getenv(
    "HARNESS_LOG_GROUP"
)

POLICY_COMPLIANCE_EVALUATOR_ID = os.getenv(
    "POLICY_COMPLIANCE_EVALUATOR_ID"
)


# ============================================================
# VALIDAÇÃO DA CONFIGURAÇÃO
# ============================================================

def validate_configuration():
    """
    Confirma se todos os recursos necessários estão
    configurados antes da execução.
    """

    if not HARNESS_ARN:
        raise RuntimeError(
            "A variável de ambiente HARNESS_ARN "
            "não está configurada."
        )

    if not HARNESS_LOG_GROUP:
        raise RuntimeError(
            "A variável de ambiente HARNESS_LOG_GROUP "
            "não está configurada."
        )

    if not POLICY_COMPLIANCE_EVALUATOR_ID:
        raise RuntimeError(
            "A variável de ambiente "
            "POLICY_COMPLIANCE_EVALUATOR_ID "
            "não está configurada."
        )

    if not GROUND_TRUTH_PATH.exists():
        raise FileNotFoundError(
            f"Ground truth não encontrado em: "
            f"{GROUND_TRUTH_PATH}"
        )


# ============================================================
# CLIENTE AGENTCORE
# ============================================================

agentcore_client = boto3.client(
    "bedrock-agentcore",
    region_name=AWS_REGION,
)


# ============================================================
# INVOCADOR DO HARNESS
# ============================================================

def agent_invoker(
    invoker_input: AgentInvokerInput,
) -> AgentInvokerOutput:
    """
    Executa um turno do Employee Policy Assistant.

    Cada cenário recebe uma sessão independente.

    Para cenários multi-turn:
    - o mesmo session_id é preservado;
    - o mesmo actor_id é preservado;
    - o contexto da conversa pode ser mantido.

    O actor_id é derivado da própria sessão para reduzir
    risco de contaminação de memória entre cenários.
    """

    payload = invoker_input.payload

    # ========================================================
    # EXTRAÇÃO DO TEXTO
    # ========================================================

    if isinstance(payload, str):
        user_text = payload

    elif isinstance(payload, dict):

        if isinstance(
            payload.get("content"),
            str,
        ):
            user_text = payload["content"]

        elif isinstance(
            payload.get("text"),
            str,
        ):
            user_text = payload["text"]

        else:
            user_text = str(payload)

    else:
        user_text = str(payload)

    session_id = invoker_input.session_id

    actor_id = (
        f"policy-eval-v2{session_id}"
    )

    print(
        "\n----------------------------------------"
    )

    print(
        f"Session ID: {session_id}"
    )

    print(
        f"Actor ID: {actor_id}"
    )

    print(
        f"\nEntrada:\n{user_text}"
    )

    # ========================================================
    # INVOCAÇÃO DO HARNESS
    # ========================================================

    response = agentcore_client.invoke_harness(
        harnessArn=HARNESS_ARN,
        qualifier=HARNESS_QUALIFIER,
        runtimeSessionId=session_id,
        actorId=actor_id,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": user_text
                    }
                ],
            }
        ],
    )

    # ========================================================
    # PROCESSAMENTO DO STREAM
    # ========================================================

    answer_parts = []
    runtime_errors = []

    for event in response["stream"]:

        if "contentBlockDelta" in event:

            delta = (
                event["contentBlockDelta"]
                .get(
                    "delta",
                    {},
                )
            )

            text_delta = delta.get(
                "text"
            )

            if text_delta:

                answer_parts.append(
                    text_delta
                )

        elif "runtimeClientError" in event:

            runtime_errors.append(
                event[
                    "runtimeClientError"
                ].get(
                    "message",
                    "Erro de runtime não especificado",
                )
            )

    answer = "".join(
        answer_parts
    ).strip()

    if runtime_errors:

        raise RuntimeError(
            " | ".join(
                runtime_errors
            )
        )

    print(
        f"\nResposta:\n{answer}"
    )

    return AgentInvokerOutput(
        agent_output=answer
    )


# ============================================================
# DATASET
# ============================================================

def load_dataset():
    """
    Carrega os 18 cenários do ground truth.

    Como PolicyCompliance é um avaliador em nível de sessão,
    cada cenário resultará em uma única avaliação, inclusive
    GD-016 e GD-017, que possuem múltiplos turnos.
    """

    provider = FileDatasetProvider(
        str(GROUND_TRUTH_PATH)
    )

    return provider.get_dataset()


# ============================================================
# CLOUDWATCH
# ============================================================

def create_span_collector():
    """
    Recupera os spans produzidos pelo Harness no CloudWatch.
    """

    return CloudWatchAgentSpanCollector(
        log_group_name=HARNESS_LOG_GROUP,
        region=AWS_REGION,
    )


# ============================================================
# CONFIGURAÇÃO DA AVALIAÇÃO
# ============================================================

def create_evaluation_config():
    """
    Configura a execução do custom evaluator PolicyCompliance.
    """

    return EvaluationRunConfig(
        evaluator_config=EvaluatorConfig(
            evaluator_ids=[
                POLICY_COMPLIANCE_EVALUATOR_ID
            ],
        ),

        # Tempo para os traces chegarem ao CloudWatch.
        evaluation_delay_seconds=180,

        # Paralelismo moderado para evitar excesso de
        # chamadas simultâneas durante a baseline.
        max_concurrent_scenarios=3,
    )


# ============================================================
# IMPRESSÃO DOS RESULTADOS
# ============================================================

def print_results(result):
    """
    Mostra o resultado individual de cada cenário.
    """

    print(
        "\n\n========================================"
    )

    print(
        "POLICY COMPLIANCE — V2"
    )

    print(
        "========================================"
    )

    completed = 0
    failed = 0

    for scenario in result.scenario_results:

        print(
            f"\nCenário: "
            f"{scenario.scenario_id}"
        )

        print(
            f"Status: "
            f"{scenario.status}"
        )

        if scenario.error:

            failed += 1

            print(
                f"Erro estrutural: "
                f"{scenario.error}"
            )

            continue

        completed += 1

        for evaluator in (
            scenario.evaluator_results
        ):

            print(
                f"\n  Avaliador: "
                f"{evaluator.evaluator_id}"
            )

            for evaluation_result in (
                evaluator.results
            ):

                value = (
                    evaluation_result.get(
                        "value"
                    )
                )

                label = (
                    evaluation_result.get(
                        "label"
                    )
                )

                explanation = (
                    evaluation_result.get(
                        "explanation"
                    )
                )

                error_code = (
                    evaluation_result.get(
                        "errorCode"
                    )
                )

                error_message = (
                    evaluation_result.get(
                        "errorMessage"
                    )
                )

                print(
                    f"    Score: "
                    f"{value}"
                )

                print(
                    f"    Label: "
                    f"{label}"
                )

                if explanation:

                    print(
                        f"    Explicação: "
                        f"{explanation}"
                    )

                if error_code:

                    print(
                        f"    Erro do avaliador: "
                        f"{error_code}"
                    )

                if error_message:

                    print(
                        f"    Mensagem: "
                        f"{error_message}"
                    )

                ignored = (
                    evaluation_result.get(
                        "ignoredReferenceInputFields",
                        [],
                    )
                )

                if ignored:

                    print(
                        "    Ground truth ignorado: "
                        f"{ignored}"
                    )

    print(
        "\n----------------------------------------"
    )

    print(
        f"Cenários concluídos: "
        f"{completed}"
    )

    print(
        f"Cenários com falha estrutural: "
        f"{failed}"
    )


# ============================================================
# RESUMO QUANTITATIVO
# ============================================================

def print_summary(result):
    """
    Calcula a distribuição dos scores e a média do
    PolicyCompliance.
    """

    scores = []
    labels = []

    for scenario in result.scenario_results:

        if scenario.error:
            continue

        for evaluator in (
            scenario.evaluator_results
        ):

            for evaluation_result in (
                evaluator.results
            ):

                value = (
                    evaluation_result.get(
                        "value"
                    )
                )

                label = (
                    evaluation_result.get(
                        "label"
                    )
                )

                if isinstance(
                    value,
                    (int, float),
                ):
                    scores.append(
                        float(value)
                    )

                if label:
                    labels.append(
                        label
                    )

    print(
        "\n\n========================================"
    )

    print(
        "RESUMO QUANTITATIVO"
    )

    print(
        "========================================"
    )

    if not scores:

        print(
            "Nenhum score numérico válido "
            "foi encontrado."
        )

        return

    average_score = (
        sum(scores)
        / len(scores)
    )

    print(
        f"\nAvaliações válidas: "
        f"{len(scores)}"
    )

    print(
        f"Score médio: "
        f"{average_score:.3f}"
    )

    score_distribution = Counter(
        scores
    )

    print(
        "\nDistribuição por score:"
    )

    for score in sorted(
        score_distribution.keys()
    ):

        count = (
            score_distribution[score]
        )

        percentage = (
            count
            / len(scores)
            * 100
        )

        print(
            f"  {score:.2f}: "
            f"{count} "
            f"({percentage:.1f}%)"
        )

    if labels:

        label_distribution = Counter(
            labels
        )

        print(
            "\nDistribuição por label:"
        )

        for label, count in (
            label_distribution.items()
        ):

            percentage = (
                count
                / len(labels)
                * 100
            )

            print(
                f"  {label}: "
                f"{count} "
                f"({percentage:.1f}%)"
            )


# ============================================================
# SALVAMENTO
# ============================================================

def save_results(result):
    """
    Preserva a resposta completa do AgentCore em JSON.
    """

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULTS_PATH.write_text(
        result.model_dump_json(
            indent=2
        ),
        encoding="utf-8",
    )

    print(
        f"\nResultados salvos em:"
        f"\n{RESULTS_PATH}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    validate_configuration()

    print(
        "Carregando ground truth..."
    )

    dataset = load_dataset()

    print(
        f"\nGround truth:"
        f"\n{GROUND_TRUTH_PATH}"
    )

    print(
        f"\nCenários: "
        f"{len(dataset.scenarios)}"
    )

    print(
        f"\nHarness:"
        f"\n{HARNESS_ARN}"
    )

    print(
        f"\nLog Group:"
        f"\n{HARNESS_LOG_GROUP}"
    )

    print(
        f"\nCustom evaluator:"
        f"\n{POLICY_COMPLIANCE_EVALUATOR_ID}"
    )

    print(
        "\nNível esperado do avaliador: SESSION"
    )

    span_collector = (
        create_span_collector()
    )

    config = (
        create_evaluation_config()
    )

    runner = (
        OnDemandEvaluationDatasetRunner(
            region=AWS_REGION
        )
    )

    print(
        "\n\nIniciando avaliação "
        "PolicyCompliance..."
    )

    print(
        "\nFluxo:"
        "\n1. Executar os 18 cenários"
        "\n2. Aguardar ingestão dos traces"
        "\n3. Recuperar spans do CloudWatch"
        "\n4. Executar PolicyCompliance"
        "\n5. Salvar resultados"
    )

    result = runner.run(
        agent_invoker=agent_invoker,
        dataset=dataset,
        span_collector=span_collector,
        config=config,
    )

    print_results(
        result
    )

    print_summary(
        result
    )

    save_results(
        result
    )

    print(
        "\n\n========================================"
    )

    print(
        "POLICY COMPLIANCE V2 CONCLUÍDA"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()
