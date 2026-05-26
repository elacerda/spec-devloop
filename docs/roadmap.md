# Roadmap

## Visão geral

Este roadmap descreve a evolução do `spec-devloop` do MVP-0 (report-only) para versões futuras com integração de IA supervisora e executores.

## MVP-0: Validação estrutural e artefatos report-only

**Objetivo**: Validar estrutura de projeto e ciclos, reportar status, sem executar IA ou automação.

**Comandos**:
- `devloop doctor` — validar projeto specs e local readiness
- `devloop status` — mostrar resumo compacto de readiness
- `devloop init --check` — reportar apenas checks de init
- `devloop cycle list` — listar IDs de ciclos
- `devloop cycle check <cycle-id>` — validar estrutura de ciclo
- `devloop cycle summary <cycle-id>` — mostrar resumo compacto de ciclo
- `devloop cycle prompt <cycle-id>` — gerar prompt Markdown para execução manual

**Características**:
- report-only: não cria, modifica ou executa nada
- validação estrutural de arquivos YAML e Markdown
- saída clara de erros e warnings
- exit codes definidos (0=success, 2=validation error, 3=internal error)

**Não incluído**:
- sem IA supervisora
- sem execução de comandos
- sem integração com modelos
- sem automação

## Fase 1: Geração de próximo passo/prompt

**Objetivo**: IA supervisora gera o próximo passo/prompt para o humano executar.

**Características**:
- IA supervisora gera prompt para humano executar
- humano executa fora da ferramenta
- resultado é reportado pelo humano
- configuração de modelo/provedor em `.ai-loop/config/supervisor.yaml`

**Não incluído**:
- sem execução automática
- sem integração com executores
- sem validação automática de resultado

## Fase 2: Revisão de plano e resultado

**Objetivo**: IA supervisora revisa plano e resultado trazidos pelo humano.

**Características**:
- IA supervisora revisa plano e resultado
- humano traz evidências de execução
- IA supervisora recomenda aceite/rejeição/correção
- humano aprova decisão final

**Não incluído**:
- sem execução automática
- sem integração com executores
- sem validação automática de resultado

## Fase 3: Evidências e integração com providers

**Objetivo**: Coletar evidências, realizar validações e integrar gradualmente com providers de modelo.

**Características**:
- evidências são coletadas a partir de comandos, logs e ferramentas
- IA supervisora interpreta evidências e valida resultado
- IA supervisora gera relatório final
- integração com providers de modelo (vLLM, Ollama, OpenAI, etc.)

**Não incluído**:
- sem execução automática
- sem integração com executores
- sem automação completa

## Futuro: Integração direta com executores

**Objetivo**: Integração direta com executores, mantendo humano-no-loop.

**Características**:
- IA supervisora integra com executores
- humano monitora execução
- humano aprova decisões críticas
- humano revisa resultados

**Não incluído**:
- sem automação completa
- sem humano-fora-do-loop
- sem execução sem supervisão

## Princípios de evolução

1. **Report-only primeiro**: MVP-0 é report-only para validar estrutura antes de automação
2. **Humano-no-loop**: Humanos sempre aprovam decisões críticas
3. **Model-agnostic**: Flexibilidade em escolher modelo/provedor
4. **File-based**: Arquivos são a interface entre humanos e IA
5. **Local-first**: Execução local, sem dependência de nuvem
6. **Spec-first**: Especificações são a base para validação

## Non-goals

- Não transformar nomes provisórios de comandos em contrato
- Não alterar código ou testes durante documentação
- Não remover comandos existentes
- Não implementar integração real com modelo durante documentação
