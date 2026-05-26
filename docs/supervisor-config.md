# Supervisor Configuration

## Purpose

O arquivo `.ai-loop/config/supervisor.yaml` define a configuração da IA supervisora para workflows futuros de desenvolvimento assistido por IA. Este arquivo especifica:

- **Provedor e modelo** da IA supervisora (e opcionalmente do worker)
- **Limites de operação** (context window, output tokens, temperatura)
- **Políticas de segurança** (aprobção humana, permissões de execução)
- **Conexão e credenciais** para providers compatíveis com OpenAI API

Este documento descreve o contrato futuro para este arquivo, mas **não é obrigatório no MVP-0**. O MVP-0 continua sendo report-only e não chama modelos.

## Non-goals

Este documento **não** define:

- Implementação de parser YAML no CLI
- Comandos novos que usem esta configuração
- Execução de comandos ou chamadas de modelo
- Validação runtime do arquivo
- Integração com providers reais no MVP-0

Estas funcionalidades podem ser adicionadas em versões futuras, após validação do MVP-0.

## Localização esperada

O arquivo deve viver em:

```
.ai-loop/config/supervisor.yaml
```

Este caminho é relativo à raiz do projeto. O arquivo é **opcional** no MVP-0 e será exigido apenas quando comandos futuros que dependam de IA supervisora forem implementados.

## Princípios de design

1. **Human-in-the-loop**: a supervisão humana é central. A IA não executa sem aprovação explícita.
2. **Model-agnostic**: o contrato não depende de um provider específico. Provedores compatíveis com OpenAI API são suportados.
3. **Local-first**: o arquivo vive no repositório local, versionado com o projeto.
4. **Secure by default**: segredos nunca são versionados. Credenciais são obtidas de variáveis de ambiente.
5. **Conservative by default**: no MVP-0, todas as operações perigosas (model calls, file writes, command execution) são desabilitadas por padrão.
6. **Explicit over implicit**: cada permissão deve ser concedida explicitamente no arquivo de configuração.

## Separação dos papéis

O contrato futuro distingue três papéis:

| Papel | Responsabilidade |
|-------|------------------|
| **supervisor** | Define scope, recomenda aceitação ou correção, orquestra o ciclo |
| **worker** | Executa tarefas, gera código, produz diffs |
| **human** | Aprova planos, revisa evidências, decide quando o ciclo está completo |

O mesmo modelo pode atuar como supervisor em um passo e worker em outro. Modelos podem ser diferentes ou o mesmo.

## Contrato mínimo futuro

O contrato mínimo para `.ai-loop/config/supervisor.yaml` é:

```yaml
schema_version: "0.1"

roles:
  supervisor:
    provider: string
    model: string
    locality: string

    limits:
      context_window_tokens: integer
      max_output_tokens: integer
      temperature: number

policy:
  require_human_approval: boolean
```

Este contrato é **mínimo** e pode ser expandido em versões futuras.

## Exemplo YAML canônico

```yaml
schema_version: "0.1"

roles:
  supervisor:
    provider: "openai-compatible"
    model: "qwen-coder-next"
    locality: "local"

    connection:
      endpoint: "http://localhost:8000/v1"
      credentials:
        api_key_env: "DEVLOOP_SUPERVISOR_API_KEY"

    limits:
      context_window_tokens: 65536
      max_output_tokens: 2048
      temperature: 0.2
      timeout_seconds: 120

  worker:
    mode: "manual-external"
    tool_hint: "cline"
    same_as: null

policy:
  require_human_approval: true
  require_plan_before_act: true
  allow_model_calls: false
  allow_file_writes: false
  allow_command_execution: false
```

Este exemplo é **canônico**: representa o formato esperado para validação futura e serve como referência para implementações.

## Referência dos campos principais

### `schema_version`

- **Tipo**: string
- **Obrigatório**: sim
- **Descrição**: Versão do schema do arquivo de configuração.
- **Valor atual**: `"0.1"`
- **Nota**: Permite evolução futura do contrato sem quebrar compatibilidade.

### `roles`

- **Tipo**: mapping
- **Obrigatório**: sim
- **Descrição**: Define os papéis que a IA assumirá no workflow.

#### `roles.supervisor`

- **Tipo**: mapping
- **Obrigatório**: sim
- **Descrição**: Configuração da IA supervisora/orquestradora.

##### `roles.supervisor.provider`

- **Tipo**: string
- **Obrigatório**: sim
- **Descrição**: Identificador do provider de modelo.
- **Valores esperados**:
  - `"openai-compatible"`: interface compatível com OpenAI API (não dependência da OpenAI)
  - `"ollama"`: provider local Ollama
  - `"vllm"`: provider local vLLM
  - Future providers conforme evolução do projeto

> **Nota sobre `openai-compatible`**: Este valor descreve uma **interface/protocolo** (compatibilidade com OpenAI API), não uma dependência da OpenAI. O provider pode ser local (vLLM, Ollama) ou remoto (OpenAI, Anthropic, ou qualquer serviço compatível).

##### `roles.supervisor.model`

- **Tipo**: string
- **Obrigatório**: sim
- **Descrição**: Nome do modelo a ser usado pelo supervisor.
- **Exemplos**: `"qwen-coder-next"`, `"gpt-4o"`, `"claude-3.5-sonnet"`

##### `roles.supervisor.locality`

- **Tipo**: string
- **Obrigatório**: sim
- **Descrição**: Indica se o modelo é local ou remoto.
- **Valores esperados**:
  - `"local"`: modelo rodando localmente (vLLM, Ollama, etc.)
  - `"remote"`: modelo rodando em nuvem (OpenAI, Anthropic, etc.)

##### `roles.supervisor.connection`

- **Tipo**: mapping
- **Obrigatório**: sim (para providers que exigem conexão)
- **Descrição**: Configuração de conexão com o provider.

###### `roles.supervisor.connection.endpoint`

- **Tipo**: string (URL)
- **Obrigatório**: sim (para providers remotos)
- **Descrição**: Endpoint da API compatível com OpenAI.
- **Exemplo**: `"http://localhost:8000/v1"` (vLLM), `"https://api.openai.com/v1"`

###### `roles.supervisor.connection.credentials`

- **Tipo**: mapping
- **Obrigatório**: sim (para providers que exigem autenticação)
- **Descrição**: Credenciais para autenticação no provider.

####### `roles.supervisor.connection.credentials.api_key_env`

- **Tipo**: string
- **Obrigatório**: sim (quando autenticação for necessária)
- **Descrição**: Nome da variável de ambiente que contém a API key.
- **Exemplo**: `"DEVLOOP_SUPERVISOR_API_KEY"`
- **Importante**: **Nunca** versione segredos no arquivo. Use variáveis de ambiente.

##### `roles.supervisor.limits`

- **Tipo**: mapping
- **Obrigatório**: sim
- **Descrição**: Limites de operação para o supervisor.

###### `roles.supervisor.limits.context_window_tokens`

- **Tipo**: integer
- **Obrigatório**: sim
- **Descrição**: Tamanho máximo do context window em tokens.
- **Exemplo**: `65536`

###### `roles.supervisor.limits.max_output_tokens`

- **Tipo**: integer
- **Obrigatório**: sim
- **Descrição**: Tamanho máximo da saída em tokens.
- **Exemplo**: `2048`

###### `roles.supervisor.limits.temperature`

- **Tipo**: number
- **Obrigatório**: sim
- **Descrição**: Temperatura para geração (0.0 = determinística, 1.0 = criativa).
- **Exemplo**: `0.2` (conservador para supervisão)

###### `roles.supervisor.limits.timeout_seconds`

- **Tipo**: integer
- **Obrigatório**: não (default pode ser definido pelo CLI)
- **Descrição**: Timeout em segundos para chamadas ao provider.
- **Exemplo**: `120`

#### `roles.worker`

- **Tipo**: mapping
- **Obrigatório**: sim
- **Descrição**: Configuração da IA worker/troubleshooter.

##### `roles.worker.mode`

- **Tipo**: string
- **Obrigatório**: sim
- **Descrição**: Modo de operação do worker.
- **Valores esperados**:
  - `"manual-external"`: worker opera externamente (ex: Cline, Codex, Roo) - o humano executa manualmente
  - `"auto-internal"`: worker opera internamente ao CLI (futuro)
  - `"none"`: sem worker configurado (futuro)

> **Nota sobre `mode: "manual-external"`**: Este valor indica que o worker opera fora do CLI, geralmente por meio de ferramentas externas como Cline, Codex, Roo, etc. O CLI gera prompts e o humano executa manualmente. Não é dependência arquitetural de nenhuma ferramenta específica.

##### `roles.worker.tool_hint`

- **Tipo**: string
- **Obrigatório**: não (default pode ser "none")
- **Descrição**: Dica operacional sobre qual ferramenta o worker pode usar.
- **Valores esperados**:
  - `"cline"`: dica para usar Cline como worker
  - `"codex"`: dica para usar Codex CLI como worker
  - `"roo"`: dica para usar Roo como worker
  - `"none"`: sem dica específica
- **Importante**: Este é apenas um **hint operacional**, não uma dependência arquitetural. O CLI não depende de nenhuma ferramenta específica.

##### `roles.worker.same_as`

- **Tipo**: string | null
- **Obrigatório**: não (default: null)
- **Descrição**: Permite indicar que worker e supervisor compartilham a mesma configuração subjacente.
- **Valores esperados**:
  - `null`: worker tem configuração independente
  - `"supervisor"`: worker usa a mesma configuração que supervisor (futuro)
- **Nota**: Útil para simplificar configuração quando supervisor e worker usam o mesmo provider/modelo.

### `policy`

- **Tipo**: mapping
- **Obrigatório**: sim
- **Descrição**: Políticas de segurança e controle de acesso.

#### `policy.require_human_approval`

- **Tipo**: boolean
- **Obrigatório**: sim
- **Descrição**: Exige aprovação humana explícita antes de qualquer operação perigosa.
- **Valor padrão**: `true` (conservador por padrão no MVP-0)

#### `policy.require_plan_before_act`

- **Tipo**: boolean
- **Obrigatório**: não (default: `false` no MVP-0)
- **Descrição**: Exige que o supervisor gere um plano antes de qualquer ação.
- **Valor padrão**: `false` (pode ser adicionado em versões futuras)

#### `policy.allow_model_calls`

- **Tipo**: boolean
- **Obrigatório**: sim
- **Descrição**: Permite chamadas a modelos de IA.
- **Valor padrão no MVP-0**: `false` (preserva comportamento report-only)
- **Importante**: `false` preserva o comportamento conservador até que comandos futuros explicitamente mudem este contrato.

#### `policy.allow_file_writes`

- **Tipo**: boolean
- **Obrigatório**: sim
- **Descrição**: Permite escrita de arquivos no sistema de arquivos.
- **Valor padrão no MVP-0**: `false` (preserva comportamento report-only)
- **Importante**: `false` preserva o comportamento conservador até que comandos futuros explicitamente mudem este contrato.

#### `policy.allow_command_execution`

- **Tipo**: boolean
- **Obrigatório**: sim
- **Descrição**: Permite execução de comandos no sistema operacional.
- **Valor padrão no MVP-0**: `false` (preserva comportamento report-only)
- **Importante**: `false` preserva o comportamento conservador até que comandos futuros explicitamente mudem este contrato.

## Política de segurança

### Princípios

1. **Conservativo por padrão**: todas as operações perigosas são desabilitadas por padrão no MVP-0.
2. **Aprovação explícita**: operações que afetam o sistema exigem aprovação humana explícita.
3. **Segredos não versionados**: credenciais devem vir de variáveis de ambiente, nunca do arquivo de configuração.
4. **Escopo limitado**: cada permissão deve ser concedida explicitamente e com justificativa.

### Valores padrão no MVP-0

| Política | Valor padrão | Justificativa |
|----------|--------------|---------------|
| `allow_model_calls` | `false` | MVP-0 é report-only, não chama modelos |
| `allow_file_writes` | `false` | MVP-0 não modifica arquivos |
| `allow_command_execution` | `false` | MVP-0 não executa comandos |
| `require_human_approval` | `true` | Supervisão humana é central |

### Evolução futura

Comandos futuros podem exigir políticas diferentes. Por exemplo:

- `devloop cycle plan`: pode exigir `allow_model_calls: true` e `require_plan_before_act: true`
- `devloop cycle execute`: pode exigir `allow_file_writes: true` e `allow_command_execution: true`

Estes comandos **não existem no MVP-0** e são mencionados apenas como exemplo de evolução futura.

## Validação futura

### Estrutura de validação

A validação do arquivo `.ai-loop/config/supervisor.yaml` será feita por uma **future supervisor-aware validation command** (ex: `devloop supervisor check` ou extensão de `devloop doctor`).

### Regras de validação

1. **Schema version**: deve ser `"0.1"` ou versão suportada pelo CLI.
2. **Roles obrigatórios**: `supervisor` deve estar presente.
3. **Provider válido**: deve ser um provider suportado (ex: `"openai-compatible"`, `"ollama"`, `"vllm"`).
4. **Model não vazio**: string não vazia.
5. **Locality válida**: `"local"` ou `"remote"`.
6. **Connection obrigatória para providers remotos**: endpoint e credenciais devem ser fornecidos.
7. **Credenciais seguras**: `api_key_env` deve ser uma variável de ambiente válida (não segredos inline).
8. **Limits válidos**: valores numéricos positivos para context_window_tokens, max_output_tokens, temperature (0-1), timeout_seconds.
9. **Policy obrigatória**: todas as políticas obrigatórias devem estar presentes.
10. **same_as válido**: se usado, deve referenciar um papel existente.

### Comportamento no MVP-0

No MVP-0, a validação deste arquivo **não é obrigatória**. O CLI reporta warnings para arquivos ausentes que são recomendados, mas não erros (a menos que o comando específico os exija).

## Relação com o MVP-0

### O que muda no MVP-0?

**Nada.** O MVP-0 continua sendo:

- **Report-only**: comandos apenas reportam estado, não executam ações.
- **Sem chamadas de modelo**: nenhum comando chama modelos de IA.
- **Sem execução de comandos**: nenhum comando executa comandos do sistema.
- **Sem modificação de arquivos**: comandos não criam/modificam arquivos em `.ai-loop/`.

### Quando `.ai-loop/config/supervisor.yaml` será necessário?

Apenas quando comandos futuros que dependam de IA supervisora forem implementados. Exemplos de comandos futuros:

- `devloop supervisor check`: valida configuração e disponibilidade do provider
- `devloop cycle plan`: gera plano usando IA supervisora
- `devloop cycle execute`: executa plano usando IA worker

Estes comandos **não existem no MVP-0**.

### Migration path

1. **MVP-0**: `.ai-loop/config/supervisor.yaml` é opcional, não usado.
2. **MVP-1+**: comandos que dependem de IA exigem o arquivo.
3. **Futuro**: validação obrigatória do arquivo antes de comandos que o usam.

## Non-goals (reiteração)

Este documento **não** define:

- Implementação de parser YAML no CLI
- Comandos novos que usem esta configuração
- Execução de comandos ou chamadas de modelo
- Validação runtime do arquivo
- Integração com providers reais no MVP-0

Estas funcionalidades podem ser adicionadas em versões futuras
