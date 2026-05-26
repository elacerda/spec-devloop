# Manual Cycle Contract

## Purpose

Um ciclo manual representa uma unidade de trabalho humana validável pelo devloop. Ele captura a intenção do usuário, o resultado da execução e evidências de validação, mantendo o controle total sobre o processo em modo conservador report-only.

## Separation between docs/ and .ai-loop/

O projeto mantém uma separação clara entre dois tipos de conteúdo:

- **docs/**: contém documentação humana, contratos conceituais e decisões de design. Este diretório é para leitura e referência por humanos.

- **.ai-loop/**: contém artefatos operacionais que o devloop valida ou poderá validar. Este diretório é para uso operacional pelo sistema.

- **.ai-loop/cycles/**: contém instâncias concretas de ciclos manuais, organizados por cycle-id.

Esta separação garante que documentação conceitual e estado operacional não se misturem, mantendo o projeto claro e manutenível.

## Directory layout

O layout mínimo de um ciclo manual é:

```
.ai-loop/cycles/<cycle-id>/
├── meta.yaml
├── task.md
└── report.md
```

Onde `<cycle-id>` é um identificador único e seguro para o ciclo.

## Required artifacts

### meta.yaml

Arquivo YAML contendo metadados parseáveis mínimos do ciclo. Deve ser válido e conter os campos obrigatórios definidos pelo schema.

### task.md

Arquivo Markdown contendo a intenção humana da tarefa/ciclo. Descreve o que o usuário pretende alcançar com este ciclo.

### report.md

Arquivo Markdown contendo o resultado da execução, evidência manual, validação e observações. Serve como registro do que foi feito e como foi validado.

## meta.yaml schema

O schema mínimo para `meta.yaml` é:

```yaml
schema_version: "0"
cycle_id: c-001
created_at: "2026-05-26"
status: planned
```

### status (obrigatório)

O campo `status` é **obrigatório** e é validado pelo comando `devloop cycle check <cycle-id>`.

Valores aceitos:
- `planned`
- `ready_for_worker`
- `in_progress`
- `waiting_review`
- `completed`
- `blocked`

> **Nota para MVP-0**: O comando `devloop cycle check` continua report-only. Ele valida que `status` está na lista permitida (`planned`, `ready_for_worker`, `in_progress`, `waiting_review`, `completed`, `blocked`), mas não executa transições de estado nem modifica arquivos.

### Campos obrigatórios

- `schema_version`: string representando a versão do schema (atualmente "0").
- `cycle_id`: string única e segura identificando o ciclo.
- `created_at`: string de data no formato YYYY-MM-DD.
- `status`: string indicando o estado atual do ciclo.

## Validation behavior

O comando `devloop cycle check <cycle-id>` executa as seguintes validações no MVP-0:

1. **cycle-id seguro**: o identificador passado como argumento é válido e seguro para uso em caminhos de arquivo.
2. **diretório do ciclo existe**: o diretório `.ai-loop/cycles/<cycle-id>/` existe.
3. **arquivos obrigatórios existem**: `meta.yaml`, `task.md` e `report.md` existem no diretório do ciclo.
4. **meta.yaml é YAML válido**: o arquivo pode ser parseado como YAML.
5. **meta.yaml é mapping**: o YAML parseado é um mapping (dicionário), não uma lista ou valor escalar.
6. **campos mínimos existem**: `schema_version`, `cycle_id`, `created_at` e `status` estão presentes no mapping.
7. **campos mínimos são strings não vazias**: todos os campos obrigatórios são strings com conteúdo não vazio.
8. **cycle_id do YAML bate com o argumento**: o valor de `cycle_id` no YAML deve ser idêntico ao argumento passado ao comando.

Se todas as validações passam, o comando reporta sucesso. Caso contrário, reporta os erros encontrados.

## Report-only guarantees

O comando `devloop cycle check <cycle-id>` é conservador e report-only no MVP-0. Ele:

- **não cria arquivos**
- **não cria diretórios**
- **não modifica arquivos**
- **não executa commands.yaml**
- **não chama modelos, agentes ou backends**

Este comportamento garante que o comando seja seguro para execução e não cause efeitos colaterais indesejados.

## Exit codes

O comando retorna os seguintes códigos de saída:

- **0**: ciclo válido, todas as validações passaram.
- **2**: erros de validação, o ciclo não atende aos requisitos mínimos.
- **3**: falha interna inesperada, erro não previsto durante a execução.

## Enumeração de ciclos

Ciclos manuais podem ser enumerados com o comando:

```bash
devloop cycle list
```

Este comando lista subdiretórios imediatos de `.ai-loop/cycles/`, ordenados alfabeticamente. Ele não valida ciclos - apenas reporta a existência de diretórios. A saída vazia indica sucesso (exit 0), não erros.

Para validação detalhada de um ciclo específico, continue usando:

```bash
devloop cycle check <cycle-id>
```

A validação detalhada verifica todos os requisitos do contrato de ciclo manual descrito neste documento.

## Geração de prompt para execução manual

Um ciclo validado pode ser convertido em um prompt Markdown para execução por ferramentas externas de desenvolvimento assistido (Cline, Codex, Continue, Roo, Aider, etc.):

```bash
devloop cycle prompt <cycle-id>
```

Este comando:

- **reutiliza** a validação de `devloop cycle check <cycle-id>`
- **inclui** contexto do projeto (`.ai-loop/project.md`)
- **inclui** arquitetura/protocolo (`.ai-loop/architecture.md`, `.ai-loop/protocol.md`)
- **inclui** objetivo da microtarefa (`task.md`)
- **inclui** comandos de aceite (`commands.yaml`, se presente)
- **inclui** arquivos permitidos (`allowed_paths.yaml`, se presente)
- **inclui** instruções conservadoras para o agente
- **não inclui** o conteúdo de `report.md` por padrão

### Arquivos obrigatórios

- `.ai-loop/project.md`
- `.ai-loop/architecture.md`
- `.ai-loop/protocol.md`
- `.ai-loop/cycles/<cycle-id>/meta.yaml`
- `.ai-loop/cycles/<cycle-id>/task.md`
- `.ai-loop/cycles/<cycle-id>/report.md`

### Arquivos opcionais

- `.ai-loop/config/commands.yaml`
- `.ai-loop/config/allowed_paths.yaml`

### Saída

O comando imprime em stdout um prompt Markdown estruturado com as seções descritas acima. A saída é destinada a ser copiada e colada em ferramentas externas de desenvolvimento assistido.

### Exit codes

- **0**: ciclo válido, prompt gerado com sucesso.
- **2**: erros de validação, o ciclo não atende aos requisitos mínimos.
- **3**: falha interna inesperada, erro não previsto durante a execução.

### Report-only guarantees

O comando `devloop cycle prompt <cycle-id>` é conservador e report-only no MVP-0. Ele:

- **não cria arquivos**
- **não cria diretórios**
- **não modifica arquivos**
- **não executa commands.yaml**
- **não chama modelos, agentes ou backends**

Este comportamento garante que o comando seja seguro para execução e não cause efeitos colaterais indesejados.

## Cycle summary command

O comando `devloop cycle summary <cycle-id>` exibe um resumo compacto de um ciclo manual, mostrando apenas o estado atual sem sugerir próximos passos ou modificar arquivos.

### Comportamento

- **report-only**: não cria, modifica ou executa nada
- **reutiliza** a validação de `devloop cycle check <cycle-id>`
- **mostra** resumo estruturado do ciclo
- **não sugere** próximo passo
- **não modifica** arquivos ou diretórios

### Saída

O comando imprime em stdout as seguintes informações:

- **cycle id**: identificador do ciclo
- **status**: estado atual do ciclo (ou `missing` se o ciclo não existir)
- **created_at**: data de criação (ou `missing` se ausente)
- **required files**: lista de arquivos obrigatórios com status (present/missing)
- **optional files**: lista de arquivos opcionais com status (present/missing)
- **errors**: número total de erros de validação

### Arquivos obrigatórios

- `meta.yaml`: metadados do ciclo
- `task.md`: descrição da tarefa
- `report.md`: relato da execução

### Arquivos opcionais

- `plan.md`: plano antes da execução (futuro)
- `evidence.md`: evidências como testes, logs, revisão (futuro)

Arquivos opcionais ausentes **não são erros** e não afetam o exit code.

### Exit codes

- **0**: ciclo válido, todas as validações passaram.
- **2**: erros de validação, o ciclo não atende aos requisitos mínimos.
- **3**: falha interna inesperada, erro não previsto durante a execução.

### Report-only guarantees

O comando `devloop cycle summary <cycle-id>` é conservador e report-only no MVP-0. Ele:

- **não cria arquivos**
- **não cria diretórios**
- **não modifica arquivos**
- **não executa commands.yaml**
- **não chama modelos, agentes ou backends**

Este comportamento garante que o comando seja seguro para execução e não cause efeitos colaterais indesejados.

## Relação com o futuro loop supervisionado

O ciclo manual é a base para o futuro loop supervisionado por IA. As mesmas estruturas de arquivo (`meta.yaml`, `task.md`, `report.md`) serão reutilizadas, mas com novos significados e usos:

- **MVP-0**: ciclo manual é criado e executado pelo humano
- **MVP-1**: IA supervisora gera o próximo passo/prompt para o humano executar
- **MVP-2**: IA supervisora revisa o plano e resultado trazidos pelo humano
- **MVP-3**: IA supervisora integra com providers de modelo para coletar evidências

O ciclo manual fornece:

- **Estrutura**: uma consistência de formato para todos os ciclos
- **Evidência**: um lugar para registrar o que foi feito e o que foi encontrado
- **Auditabilidade**: uma trilha clara de decisões e ações

## Non-goals for MVP-0

O MVP-0 é conservador e report-only. As seguintes funcionalidades são intencionalmente excluídas:

- sem `cycle new`
- sem `cycle status`
- sem templates automáticos
- sem alteração de `.ai-loop/state`
- sem enum rígido de status
- sem parse semântico de `created_at`
- sem executor
- sem automação
- sem integração com modelos, agentes ou backends

Estas funcionalidades podem ser adicionadas em versões futuras, após validação do MVP-0.

## Nota final

Este documento vive em `docs/` porque é documentação humana, descrevendo contratos conceituais e operacionais.

Os ciclos reais vivem em `.ai-loop/cycles/`, onde o devloop valida e opera sobre eles.
