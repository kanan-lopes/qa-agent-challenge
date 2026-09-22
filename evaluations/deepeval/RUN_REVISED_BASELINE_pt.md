# Execução revisada da baseline DeepEval

Esta versão separa cada métrica em um teste pytest independente.

Isso evita que Answer Relevancy + Faithfulness + G-Eval compartilhem o mesmo orçamento externo de tempo do DeepEval para um Golden case.

Use:

```powershell
$env:DEEPEVAL_JUDGE_MODEL="qwen3:8b"
$env:DEEPEVAL_MODEL_THINKING="0"
$env:DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE="300"
$env:DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE="900"
$env:DEEPEVAL_CASE_IDS="GD-003"
```

Depois:

```powershell
deepeval test run .\evaluations\deepeval\test_baseline_deepeval.py -s
```

Com GD-003, devem existir três testes separados:
- test_answer_relevancy[GD-003]
- test_reference_grounded_faithfulness[GD-003]
- test_policy_answer_quality[GD-003]

Score abaixo do threshold = resultado válido da baseline.
Score None / timeout / CUDA / erro de conexão ou schema = falha de infraestrutura.
