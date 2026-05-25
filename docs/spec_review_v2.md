# Revisão crítica das especificações v2

## Resumo executivo

As especificações estão bem alinhadas com a visão central: `spec-devloop` é descrito de forma consistente como um CLI local, file-based, spec-first, humano-no-loop, independente de modelo, agente e backend. A direção de MVP com executor manual primeiro também está clara.

Ainda assim, há ajustes pequenos que deveriam ser feitos antes de tratar as specs como contrato estável de implementação. O principal problema não é de arquitetura, mas de precisão operacional: o comportamento exato de `devloop doctor`, os schemas mínimos dos YAMLs, o formato do estado gerenciado e a fronteira entre recomendação futura e requisito do MVP ainda estão parcialmente implícitos.

Decisão recomendada: **B) precisa de pequenos ajustes nas specs**.

## 1. Neutralidade de modelo, agente e backend

Avaliação: **boa**.

O projeto está claramente definido como:

- model-agnostic;
- agent-agnostic;
- backend-agnostic;
- provider-agnostic;
- IDE-agnostic.

Essa intenção aparece no `README.md`, em `.ai-loop/project.md`, em `.ai-loop/architecture.md`, em `.ai-loop/protocol.md` e nas políticas de agente/modelo. A regra mais importante está bem formulada: ferramentas concretas como Cline, Codex CLI, Roo, Continue, Aider, vLLM, Ollama, OpenAI e Anthropic são exemplos, adapters, providers ou integrações futuras, não premissas do core.

Risco residual: baixo. O vocabulário lista muitas ferramentas pelo nome, mas sempre como exemplos ou trabalho futuro. Isso não caracteriza acoplamento, desde que a implementação do MVP trate essas entradas como dados opcionais.

## 2. Separação entre core, adapters e providers

Avaliação: **boa, com um ponto a explicitar**.

`.ai-loop/architecture.md` define uma fronteira clara:

- core: loading/validation de specs, estados do protocolo, diretórios de ciclo, artefatos, comandos, git, relatórios e decisões humanas;
- adapters: tradução entre o protocolo genérico e ferramentas/executores específicos;
- providers: fontes opcionais de completions de modelo.

A separação conceitual também está reforçada por regras como:

```text
protocol != agent
agent != model provider
model provider != tool execution
specification != cycle artifact
cycle artifact != foundational rule
```

O ponto ainda fraco é que as specs não dizem exatamente qual camada deve validar cada arquivo de configuração no MVP. Para `doctor`, seria útil declarar explicitamente:

- validação de presença e sintaxe: core;
- validação semântica de `adapters.yaml`: core apenas até o contrato genérico;
- validação de comportamento específico de adapters/providers: fora do MVP.

## 3. Executor manual como MVP inicial

Avaliação: **claro e apropriado**.

O executor manual está bem posicionado como o primeiro fluxo suportado. As specs definem que o CLI gera artefatos/prompts, o humano usa qualquer ferramenta externa e salva os resultados no diretório do ciclo. Isso preserva a visão humano-no-loop sem criar dependência de Cline, Codex CLI ou outro agente.

O que falta para transformar isso em contrato operacional:

- nomear os arquivos mínimos de um ciclo manual válido;
- definir quais arquivos são criados pelo CLI e quais são preenchidos pelo humano;
- definir quando `doctor` deve apenas alertar sobre templates ausentes versus falhar;
- definir a diferença entre "manual executor disponível" e "manual cycle pronto para rodar".

Esses pontos não bloqueiam o `doctor`, mas vão bloquear uma implementação limpa de `devloop start` ou equivalente.

## 4. Ciclo de vida das especificações

Avaliação: **conceitualmente forte**.

`.ai-loop/specification_lifecycle.md` estabelece quatro classes úteis:

- specs fundacionais;
- configuração operacional;
- artefatos gerados de ciclo;
- estado runtime.

O README ainda adiciona a camada de policies como estável ou semi-estável, e a hierarquia de autoridade deixa claro que claims de agentes têm baixa autoridade sem evidência.

Ponto de atenção: há uma pequena diferença de taxonomia entre documentos. O README fala em quatro tipos incluindo "Policies" como classe separada; `specification_lifecycle.md` inclui policies dentro de "Foundational specifications". Isso não é uma contradição grave, mas pode gerar dúvida na implementação do doctor: policies são uma classe própria ou uma subclasse de specs fundacionais?

Recomendação pragmática: tratar policies como **subclasse de foundational specifications** no ciclo de vida, mas como **grupo separado de arquivos opcionais** para relatório do `doctor`.

## 5. Acoplamento residual a ferramentas específicas

Avaliação: **sem acoplamento bloqueante**.

Há várias menções a Cline, Codex CLI, vLLM, Roo, Continue, Aider, Ollama, OpenAI, Anthropic, OpenHands e SWE-agent. Em geral, todas aparecem como:

- exemplos;
- adapters futuros;
- providers futuros;
- influências de arquitetura;
- anti-exemplos de acoplamento a evitar.

Não encontrei exigência de depender de Cline, Codex CLI, vLLM, Qwen, Roo, Continue, Aider ou qualquer ferramenta específica no MVP.

Risco residual: `.ai-loop/architecture.md` lista `pyproject.toml`, `uv`, `typer`, `rich`, `pydantic`, `pyyaml`/`ruamel.yaml`, `pytest`, `ruff` e type checkers como recomendações. Isso é aceitável para arquitetura futura, mas conflita com a instrução atual de não criar pacote Python agora. A spec deveria separar melhor:

- "recomendado para implementação Python futura";
- "necessário para `devloop doctor`";
- "não necessário antes do esqueleto do pacote".

## 6. Arquivos obrigatórios mínimos

Avaliação: **claros para o primeiro doctor**.

O conjunto mínimo aparece no README e em `.ai-loop/config/commands.yaml`:

```text
.ai-loop/project.md
.ai-loop/architecture.md
.ai-loop/protocol.md
.ai-loop/config/commands.yaml
```

Isso é suficiente para implementar a primeira versão de `devloop doctor`.

Ajuste sugerido: declarar quais ausências devem ser erro, warning ou info. Por exemplo:

- mínimo obrigatório ausente: erro;
- optional policy/config ausente: warning ou info;
- templates de ciclo ausentes: warning enquanto só houver doctor, erro quando comandos de ciclo forem implementados;
- diretórios `.ai-loop/cycles` e `.ai-loop/state` ausentes: warning com sugestão ou erro dependendo se o doctor deve criar diretórios ou apenas validar.

## 7. Contradições entre specs centrais

Avaliação: **sem contradição arquitetural grave, mas há tensões menores**.

Principais tensões:

1. **Policies como classe separada ou specs fundacionais.**  
   README separa "Foundational specifications" e "Policies"; `specification_lifecycle.md` inclui policies como exemplos de foundational specifications. A solução simples é explicitar que policies são specs fundacionais especializadas, mas reportadas separadamente.

2. **MVP mínimo versus MVP amplo.**  
   README recomenda começar por `devloop doctor`. `docs/mvp.md` define um MVP que inclui status, criação de ciclos, executor manual, relatórios, estado, git diff e comandos configurados. Isso é coerente se `doctor` for Milestone 1, mas seria excessivo se interpretado como escopo da primeira implementação.

3. **Arquitetura Python sugerida versus proibição de iniciar pacote agora.**  
   `.ai-loop/architecture.md` recomenda `pyproject.toml` e ferramentas Python. Isso não contradiz a visão do projeto, mas precisa ficar claramente marcado como posterior ao fechamento da spec review e não como ação automática.

4. **Estado gerenciado citado, mas não contratado.**  
   `specification_lifecycle.md` e `.ai-loop/state/README.md` citam `loop_state.json` e `current_cycle.json`, mas não definem schema mínimo, campos obrigatórios ou política de atualização.

Nenhuma dessas tensões exige redesenho relevante.

## 8. Suficiência de commands.yaml, providers.yaml, adapters.yaml e allowed_paths.yaml

Avaliação: **suficientes para um MVP inicial de validação, ainda incompletos como contrato de execução**.

Validação realizada nesta revisão: os quatro YAMLs em `.ai-loop/config/` foram parseados com sucesso usando o parser YAML disponível no sistema.

Para `devloop doctor`, eles parecem suficientes para:

- checar presença do arquivo;
- validar sintaxe YAML;
- relatar provider default `none`;
- relatar adapter default `manual`;
- checar diretórios gerenciados;
- listar comandos configurados;
- listar path sets e permissões por tipo de ciclo.

Limitações para execução posterior:

- não há versão de schema dos arquivos;
- não há campos obrigatórios formalizados por tipo de YAML;
- `commands.yaml` mistura comandos futuros com `available_after: python_project_initialized`, mas não define como o doctor detecta esse marco;
- `allowed_paths.yaml` cobre permissões por tipo de ciclo, mas ainda não define precedência clara quando patterns se sobrepõem;
- `providers.yaml` e `adapters.yaml` são bons como inventário, mas ainda não definem validação semântica mínima além de enabled/type/default.

Para o primeiro `doctor`, isso é aceitável desde que a implementação seja conservadora e relate lacunas em vez de inferir comportamento demais.

## 9. Escopo excessivo para o primeiro MVP

Avaliação: **há risco de escopo excessivo se "MVP" for interpretado como primeira entrega única**.

`docs/mvp.md` lista um MVP bastante amplo: CLI, loader, validator, doctor, status, criação de ciclo, executor manual, relatório, estado JSON/YAML, git diff e execução de comandos configurados.

Essa lista é razoável como MVP completo, mas grande demais para a primeira implementação. A própria documentação mitiga isso ao definir `devloop doctor` como primeiro comando e Milestone 1 como validação de specs.

Recomendação: manter o MVP amplo como horizonte, mas declarar um **MVP-0** ou **Milestone 1 contract** para `doctor`:

- não cria pacote além do necessário para o comando;
- não cria ciclo;
- não chama modelo;
- não chama adapter;
- não executa comandos de teste/lint;
- valida presença, sintaxe, diretórios e coerência básica;
- retorna exit code previsível.

## 10. Segurança para iniciar `devloop doctor`

Avaliação: **sim, é seguro iniciar `devloop doctor` como implementação estreita**, mas as specs devem receber pequenos ajustes para reduzir ambiguidades.

O `doctor` é o comando mais seguro para começar porque:

- não edita código de produto;
- não chama modelos;
- não executa agente externo;
- não precisa de provider;
- pode operar apenas sobre arquivos locais;
- reforça o contrato spec-first antes de automação.

O que ainda deve ser decidido antes ou durante a implementação:

- exit codes;
- severidade de cada problema: error/warning/info;
- se o doctor pode criar diretórios ausentes ou apenas reportar;
- schema mínimo de `commands.yaml`, `providers.yaml`, `adapters.yaml`, `allowed_paths.yaml`;
- formato de saída humana versus saída machine-readable futura;
- comportamento quando o repositório não é git;
- comportamento quando a worktree está suja durante apenas o doctor.

## Ajustes sugeridos em ordem de prioridade

1. **Definir o contrato do `devloop doctor`.**  
   Especificar checks, severidades, exit codes, se cria diretórios ou apenas reporta, e quais arquivos opcionais geram warning versus info.

2. **Formalizar schemas mínimos dos YAMLs.**  
   Adicionar uma pequena seção por arquivo com campos obrigatórios, tipos esperados e validações semânticas mínimas.

3. **Resolver a taxonomia de policies.**  
   Declarar que policies são specs fundacionais especializadas, mas podem ser agrupadas separadamente em relatórios.

4. **Separar "MVP completo" de "primeira entrega".**  
   Nomear `devloop doctor` como Milestone 1 ou MVP-0 para evitar que status, ciclo manual, reports e execução de comandos entrem cedo demais.

5. **Definir estado gerenciado mínimo.**  
   Mesmo que `doctor` não use estado, documentar se `loop_state.json` e `current_cycle.json` são obrigatórios, gerados sob demanda ou futuros.

6. **Explicitar que tooling Python é recomendação futura.**  
   Evitar que `pyproject.toml`, `uv`, `typer`, `rich` ou `pydantic` sejam lidos como requisitos antes da implementação do pacote.

7. **Definir precedência de patterns em `allowed_paths.yaml`.**  
   Importante para ciclos futuros, especialmente quando `docs/**` e arquivos específicos se sobrepõem.

8. **Adicionar uma pequena matriz de prontidão.**  
   Exemplo: "ready_for_doctor", "ready_for_manual_cycle", "ready_for_evidence_collection".

## Decisão recomendada

**B) precisa de pequenos ajustes nas specs.**

Não há necessidade de redesenho relevante. A visão está preservada: spec-first, file-based, local CLI, humano-no-loop e executor manual primeiro. Também não há dependência obrigatória de agente externo ou provider.

É seguro iniciar a implementação de `devloop doctor` se o escopo for mantido estreito e se as lacunas acima forem tratadas como parte do contrato inicial do comando, não como convite para automação prematura.
