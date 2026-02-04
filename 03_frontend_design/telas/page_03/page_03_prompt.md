Esta é uma das telas mais críticas do sistema, pois é aqui que a "sujeira" do PDF é limpa para se tornar um plano de produção real. Como você usará o computador para essa parte, podemos aproveitar melhor o espaço de tela para uma **tabela de alta densidade**.

Aqui está o prompt detalhado para o Stitch, focado em **precisão e agilidade na edição**.

---

### 🚀 Prompt para a Tela 03: Engenharia de PSO (Ciclo 1)

> **Contexto:** Você é um desenvolvedor Front-end especializado em interfaces de ERP e produtividade. Preciso do HTML/CSS (Tailwind CSS) para a tela de Engenharia de PSO (Sequência Operacional) do sistema SGP Costura.
> **Diretrizes de Layout (Desktop Focus):**
> 1. **Cabeçalho de Ações:**
> * Botão de destaque: "**📥 IMPORTAR PDF**" (abre um seletor de arquivos).
> * Resumo dinâmico: "Tempo Total (TP): 11.67 min" | "Total de Operações: 22".
> * Botão de salvamento: "**💾 SALVAR VERSÃO V1**" (cor verde).
> 
> 
> 2. **Tabela de Edição de Operações (Rigorosa):**
> * Uma tabela que ocupa a largura total com as seguintes colunas:
> * **Seq:** (Input numérico pequeno).
> * **Descrição:** (Input de texto largo).
> * **Máquina Macro:** (Um Select/Dropdown que altera a cor de fundo da célula com base na seleção: Reta=Azul, Over=Roxo, Cobertura=Laranja, Catraca=Marrom).
> * **Tempo (s):** (Input numérico para o tempo centesimal).
> * **Status:** (Toggle/Switch para Inativar/Ativar operação).
> 
> 
> 
> 
> 3. **Funcionalidades de Edição:**
> * As linhas devem permitir reordenação (Drag handle).
> * Operações inativadas devem ficar com a linha opaca (estilo "disabled").
> 
> 
> 
> 
> **Paleta de Cores de Máquinas (CSS Variables):**
> * Aplique o Color Coding definido: `--reta: #2196F3`, `--over: #9C27B0`, `--cobertura: #FF9800`, `--catraca: #795548`.
> 
> 
> **Comportamento Reativo:** Sempre que um tempo for alterado ou uma operação inativada, o "Tempo Total (TP)" no cabeçalho deve ser recalculado instantaneamente via JavaScript.
