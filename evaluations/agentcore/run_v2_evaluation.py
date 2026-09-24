import os
from pathlib import Path

import boto3

from bedrock_agentcore.evaluation import (
    AgentInvokerInput,
    AgentInvokerOutput,
    CloudWatchAgentSpanCollector,
    Dataset,
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

RESPONSE_RESULTS_PATH = (
    RESULTS_DIR
    / "agentcore_v2_response_results.json"
)

TRAJECTORY_RESULTS_PATH = (
    RESULTS_DIR
    / "agentcore_v2_trajectory_results.json"
)


HARNESS_ARN = os.getenv("HARNESS_ARN")
HARNESS_LOG_GROUP = os.getenv("HARNESS_LOG_GROUP")


# ============================================================
# AVALIADORES
# ============================================================

# Aplicados aos 18 cenários.
RESPONSE_EVALUATOR_IDS = [
    "Builtin.Correctness",
    "Builtin.GoalSuccessRate",
]

# Aplicado apenas aos cenários que possuem expected_trajectory.
TRAJECTORY_EVALUATOR_IDS = [
    "Builtin.TrajectoryAnyOrderMatch",
]


# ============================================================
# VALIDAÇÃO DA CONFIGURAÇÃO
# ============================================================

def validate_configuration():
    """
    Confirma se todas as configurações necessárias estão
    disponíveis antes de iniciar qualquer chamada à AWS.
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

    if not GROUND_TRUTH_PATH.exists():
        raise FileNotFoundError(
            f"Ground truth não encontrado em: "
            f"{GROUND_TRUTH_PATH}"
        )


# ============================================================
# CLIENTE DO AGENTCORE
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
    Executa um único turno no AgentCore Harness.

    O OnDemandEvaluationDatasetRunner cria uma sessão
    independente por cenário.

    Em cenários multi-turn, o session_id permanece o mesmo
    durante todos os turnos, preservando o contexto.

    O Actor ID também é derivado da sessão para evitar
    contaminação da AgentCore Memory entre cenários.
    """

    payload = invoker_input.payload

    # ========================================================
    # EXTRAÇÃO DO TEXTO DO INPUT
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
        f"agentcore-eval-v2{session_id}"
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

    answer_parts = []
    runtime_errors = []

    # ========================================================
    # LEITURA DO STREAM
    # ========================================================

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
# DATASETS
# ============================================================

def load_datasets():
    """
    Cria dois datasets independentes.

    response_dataset:
        contém todos os 18 cenários.

        Será utilizado por:
        - Builtin.Correctness
        - Builtin.GoalSuccessRate

    trajectory_dataset:
        contém somente cenários que possuem
        expected_trajectory.

        No nosso projeto são 17 cenários, pois GD-018
        não espera uso da Knowledge Base.

        Será utilizado por:
        - Builtin.TrajectoryAnyOrderMatch
    """

    provider = FileDatasetProvider(
        str(GROUND_TRUTH_PATH)
    )

    full_dataset = (
        provider.get_dataset()
    )

    trajectory_scenarios = [
        scenario
        for scenario
        in full_dataset.scenarios
        if getattr(
            scenario,
            "expected_trajectory",
            None,
        )
    ]

    trajectory_dataset = Dataset(
        scenarios=trajectory_scenarios
    )

    return (
        full_dataset,
        trajectory_dataset,
    )


# ============================================================
# CLOUDWATCH SPAN COLLECTOR
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

def create_evaluation_config(
    evaluator_ids: list[str],
):
    """
    Cria a configuração utilizada em uma rodada de avaliação.
    """

    return EvaluationRunConfig(
        evaluator_config=EvaluatorConfig(
            evaluator_ids=evaluator_ids,
        ),

        # Tempo dado ao CloudWatch para ingerir os traces.
        evaluation_delay_seconds=180,

        # Evita paralelismo excessivo para nosso pequeno dataset.
        max_concurrent_scenarios=3,
    )


# ============================================================
# IMPRESSÃO DOS RESULTADOS
# ============================================================

def print_results(
    result,
    title: str,
):
    """
    Exibe os resultados de forma legível no terminal.
    """

    print(
        "\n\n========================================"
    )

    print(title)

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
# SALVAMENTO
# ============================================================

def save_results(
    result,
    output_path: Path,
):
    """
    Salva os resultados completos sem alterar a estrutura
    retornada pelo AgentCore.
    """

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        result.model_dump_json(
            indent=2
        ),
        encoding="utf-8",
    )

    print(
        f"\nResultados salvos em:"
        f"\n{output_path}"
    )


# ============================================================
# EXECUÇÃO DE UMA RODADA
# ============================================================

def run_evaluation(
    dataset,
    evaluator_ids: list[str],
    title: str,
    output_path: Path,
):
    """
    Executa uma rodada completa:

    1. Invoca os cenários;
    2. aguarda ingestão dos traces;
    3. recupera spans no CloudWatch;
    4. executa os avaliadores;
    5. salva os resultados.
    """

    print(
        "\n\n########################################"
    )

    print(title)

    print(
        "########################################"
    )

    print(
        f"\nQuantidade de cenários: "
        f"{len(dataset.scenarios)}"
    )

    print(
        "\nAvaliadores:"
    )

    for evaluator_id in evaluator_ids:

        print(
            f"  - {evaluator_id}"
        )

    span_collector = (
        create_span_collector()
    )

    config = (
        create_evaluation_config(
            evaluator_ids
        )
    )

    runner = (
        OnDemandEvaluationDatasetRunner(
            region=AWS_REGION
        )
    )

    print(
        "\nIniciando execução..."
    )

    result = runner.run(
        agent_invoker=agent_invoker,
        dataset=dataset,
        span_collector=span_collector,
        config=config,
    )

    print_results(
        result,
        title,
    )

    save_results(
        result,
        output_path,
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    validate_configuration()

    print(
        "Carregando ground truth..."
    )

    (
        response_dataset,
        trajectory_dataset,
    ) = load_datasets()

    print(
        f"\nGround truth:"
        f"\n{GROUND_TRUTH_PATH}"
    )

    print(
        f"\nLog Group:"
        f"\n{HARNESS_LOG_GROUP}"
    )

    print(
        "\nResumo dos datasets:"
    )

    print(
        "  Resposta/comportamento: "
        f"{len(response_dataset.scenarios)} "
        "cenários"
    )

    print(
        "  Trajetória: "
        f"{len(trajectory_dataset.scenarios)} "
        "cenários"
    )

    # ========================================================
    # RODADA A
    #
    # Todos os 18 cenários.
    #
    # Correctness:
    # compara actual response com expected_response.
    #
    # GoalSuccessRate:
    # verifica as assertions definidas no ground truth.
    # ========================================================

    run_evaluation(
        dataset=response_dataset,

        evaluator_ids=(
            RESPONSE_EVALUATOR_IDS
        ),

        title=(
            "V2 — CORRECTNESS "
            "E GOAL SUCCESS RATE"
        ),

        output_path=(
            RESPONSE_RESULTS_PATH
        ),
    )

    # ========================================================
    # RODADA B
    #
    # Somente os 17 cenários que esperam uso da KB.
    #
    # TrajectoryAnyOrderMatch:
    # verifica se Retrieve aparece na trajetória.
    # ========================================================

    run_evaluation(
        dataset=trajectory_dataset,

        evaluator_ids=(
            TRAJECTORY_EVALUATOR_IDS
        ),

        title=(
            "v2 — TRAJECTORY "
            "ANY ORDER MATCH"
        ),

        output_path=(
            TRAJECTORY_RESULTS_PATH
        ),
    )

    # ========================================================
    # FINAL
    # ========================================================

    print(
        "\n\n========================================"
    )

    print(
        "AVALIAÇÃO FORMAL DA V2 CONCLUÍDA"
    )

    print(
        "========================================"
    )

    print(
        "\nResultados de resposta/comportamento:"
    )

    print(
        RESPONSE_RESULTS_PATH
    )

    print(
        "\nResultados de trajetória:"
    )

    print(
        TRAJECTORY_RESULTS_PATH
    )


if __name__ == "__main__":
    main()
