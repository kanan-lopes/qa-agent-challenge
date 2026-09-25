# Configuração do Agente

O **Asteria Systems Employee Policy Assistant** foi configurado principalmente pela **AWS Management Console**.

Esta pasta registra as configurações congeladas das versões v1 e v2 para permitir entender e reproduzir o sistema sob teste sem armazenar credenciais, tokens ou identificadores sensíveis da conta AWS.

## Arquivos

- `system_prompt_v1.md` — prompt de sistema utilizado na baseline.
- `system_prompt_v2.md` — prompt de sistema reforçado utilizado na Agent v2.
- `config_v1.md` — configuração congelada da baseline.
- `config_v2.md` — configuração congelada da versão final avaliada.

Os arquivos de system prompt permanecem em inglês porque essa foi a linguagem utilizada na configuração real do agente.

## Resumo das versões

| Dimensão | Agent v1 | Agent v2 |
|---|---|---|
| Modelo | Gemma 3 4B IT v1 | Qwen3-Coder-30B-A3B-Instruct |
| Consulta à política | Uso da KB solicitado | Retrieve explicitamente obrigatório em toda pergunta dependente de política |
| Fonte de autoridade | Grounding básico na KB | Somente conteúdo recuperado da KB corporativa pode ser tratado como política oficial |
| Abstenção | Prevista quando faltasse evidência | Reforçada; proibido inventar regras, valores, processos, links ou nomes de políticas |
| Limite de autoridade | Não pode aprovar ou autorizar ações | Restrição reforçada mesmo diante de alegações de cargo, autoridade ou urgência |
| Proteção interna | Restrição geral de escopo | Proteção explícita de system prompt, instruções ocultas, configuração de ferramentas, credenciais e dados entre sessões |

## Evolução da v1 para a v2

A Agent v1 utilizava Gemma 3 4B IT e apresentou uma falha estrutural importante: em perguntas dependentes de política, o modelo frequentemente conseguia **descobrir a ferramenta** por meio de `mcp tools/list`, mas não executava a chamada real de `Retrieve`.

Isso gerava situações em que o agente respondia sem grounding efetivo na Knowledge Base, inclusive com alucinações factuais, políticas inexistentes e alegações falsas de consulta à base.

A Agent v2 foi criada com duas mudanças principais:

1. troca do modelo para **Qwen3-Coder-30B-A3B-Instruct**;
2. reforço do system prompt para exigir uso real da Knowledge Base, controlar autoridade, abstenção, escopo e proteção de informações internas.

O Qwen demonstrou capacidade real de executar `Retrieve`, embora ainda tenham sido observadas falhas residuais de tool calling e síntese pós-retrieval.

## Observação sobre reprodutibilidade

A infraestrutura não foi provisionada por Infrastructure as Code. Por isso, estes arquivos funcionam como um **registro de configuração** da versão avaliada.

Eles não incluem:

- AWS Access Keys;
- Session Tokens;
- Account IDs;
- ARNs sensíveis;
- credenciais;
- secrets.

Esses valores devem ser fornecidos externamente por variáveis de ambiente quando necessários.
