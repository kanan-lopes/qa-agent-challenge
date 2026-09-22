# Execução da suíte formal DeepEval — Baseline

## 1. Onde colocar

Copie:

`test_baseline_deepeval.py`

para:

`evaluations/deepeval/test_baseline_deepeval.py`

A estrutura esperada é:

```text
qa-agent-challenge/
├── evaluations/
│   └── deepeval/
│       ├── reference_contexts.json
│       ├── README_reference_contexts.md
│       ├── README_reference_contexts_pt.md
│       ├── smoke_test.py
│       ├── ollama_structured_test.py
│       └── test_baseline_deepeval.py
└── results/
    └── baseline/
        └── golden_results_raw_972e97b8.json
```

## 2. Primeiro: pilot curto

No PowerShell, a partir da raiz do projeto:

```powershell
$env:DEEPEVAL_CASE_IDS="GD-003,GD-015"
deepeval test run .\evaluations\deepeval\test_baseline_deepeval.py -s
```

Esse pilot valida a suíte formal sem disparar os 20 turnos de uma vez.

## 3. Depois: execução formal completa

Remova o filtro:

```powershell
Remove-Item Env:DEEPEVAL_CASE_IDS -ErrorAction SilentlyContinue
```

Então execute:

```powershell
deepeval test run .\evaluations\deepeval\test_baseline_deepeval.py -s
```

## 4. O que será avaliado

- 18 Golden scenarios.
- GD-016 e GD-017 são expandidos em dois turnos cada.
- Total: 20 testes atômicos.
- Answer Relevancy: threshold 0.70.
- Reference-grounded Faithfulness: threshold 0.80.
- G-Eval Policy Answer Quality: threshold 0.80.
- GD-018 não recebe Faithfulness por ser um caso intencionalmente fora do escopo.

## 5. Importante sobre FAIL

A baseline é defeituosa por definição. Portanto, vários testes devem falhar.

Um `FAILED` por score abaixo do threshold é um resultado de QA válido.

O que caracteriza erro de infraestrutura é, por exemplo:
- traceback de Python;
- erro de conexão com Ollama;
- erro CUDA;
- arquivo não encontrado;
- erro de schema/structured output.

Não altere os thresholds ou o judge apenas para aumentar a taxa de PASS.
