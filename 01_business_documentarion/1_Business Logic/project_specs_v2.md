# 📑 Documento de Visão de Produto: Sistema VAC v2

## 1. Objetivo do Sistema
Automatizar o planejamento, balanceamento e controle de produção têxtil, eliminando o gargalo de montagem de carrinhos e mantendo o ritmo através de um pulso de produção configurável (30 ou 60 minutos).

## 2. Arquitetura de Dados (Destaques)
* **PSO (Sequência Operacional):** Controle de versões (V0 e V1) com operações Preparatórias, Independentes e Dependentes.
* **Balanceamento Fine-Tuning:** Suporte ao fracionamento de operações entre costureiras no mesmo lote.
* **Configuração de Pulso:** Campo `pulse_duration` na tabela `PRODUCTION_PLANNING` para flexibilidade entre produtos simples e complexos.

## 3. Workflows Críticos

### Ciclo 1: Engenharia (Refinamento)
* Importação de PDF com *Hard Delete* de versões obsoletas.
* Loop de manutenção de operações: ajuste de tempos, máquinas macro e inativação.
* Aprovação técnica (Auditoria) para travar a versão de trabalho (PSO V1).

### Ciclo 2: Planejamento (O Metrônomo)
* **Cálculo de TL Dinâmico:** Baseado no `pulse_duration` (30 ou 60 min).
* **Interface Kanban Anti-Quebra:** Colunas fixas com scroll interno e identificação visual por cores de máquinas macro.
* **Termômetro de Carga:** Barra visual no rodapé de cada estação que alerta sobrecarga em tempo real.
* **Modal de Fracionamento:** Permite dividir o saldo de uma operação para a próxima estação se a carga exceder o pulso.

### Ciclo 3: Execução (Checklist Digital)
* Geração de Cards de Apoio Físico (A4 econômico).
* **Check Digital:** Botão "Finalizar" na interface da Facilitadora que registra o `finished_at`.
* **Gatilho de Dashboard:** O check-out de um carrinho reseta automaticamente o cronômetro do pulso para o próximo lote.

## 4. Regras de Cálculo (ERC)
* **TL (Tamanho do Lote):** `floor((Operators * pulse_duration) / TP)`. Arredondamento para baixo obrigatório.
* **Validação de Carga:** O limite do termômetro é definido pelo `pulse_duration` ativo.
* **Janela Útil:** Desconto automático de intervalos de almoço e paradas conforme `TURN_CALENDAR`.

## 5. Mapa de API e Permissões (RBAC)
* **Roles:**
    * **View:** Consulta de dashboards e OPs (sem edição).
    * **User (Facilitadora):** Consulta de PSO e realização de Check Digital de carrinhos.
    * **Owner:** Controle total (Configurações, Balanceamento, Engenharia, Usuários).
* **Endpoints Principais:**
    * `POST /api/pso/import` (Engenharia)
    * `POST /api/planning/balance` (Planejamento)
    * `PATCH /api/cart/finish/{id}` (Operação/Dashboard)

## 6. Design de Interface (Front-end)
* **Color Coding de Máquinas:** Borda lateral nos cards (Reta: Azul, Over: Roxo, Cobertura: Laranja, etc).
* **Cronômetro Central:** Visão gigante do tempo restante para o próximo pulso (Gestão à Vista).
* **Hierarquia Visual:** Layout de grid rígido para evitar quebras de interface durante o arraste de operações.