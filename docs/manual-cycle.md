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
status: draft
```

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

## Non-goals for MVP-0

O MVP-0 é conservador e report-only. As seguintes funcionalidades são intencionalmente excluídas:

- sem `cycle new`
- sem `cycle list`
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