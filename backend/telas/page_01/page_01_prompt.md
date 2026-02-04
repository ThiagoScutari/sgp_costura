### 🚀 Prompt para a Tela 01: Dashboard Operacional (Mobile First)

> **Contexto:** Você é um desenvolvedor Front-end Sênior. Preciso do código HTML/CSS (Tailwind CSS) para a tela principal de um sistema de gestão têxtil (SGP Costura). Esta tela será acessada principalmente via **CELULAR**.
> **Diretrizes de Layout (Mobile):**
> 1. **Header Fixo:** Deve conter o nome "SGP - Sistema VAC", o status da conexão (dot verde) e um seletor discreto de OP ativa.
> 2. **O Metrônomo (Coração da Tela):** No topo, um Card centralizado com um cronômetro gigante. O fundo do card deve mudar de cor: **Azul** (rodando), **Cinza** (intervalo/turno) e **Vermelho Piscando** (pulso vencido/atraso). Abaixo do tempo, exibir "Próximo Lote em: [HH:MM]".
> 3. **Indicadores de Progresso (Cards Grandes):**
> * **Progresso da OP:** Uma barra de progresso horizontal larga. Texto: "Lote 08 de 24".
> * **Eficiência Atual:** Um indicador circular (Gauge) mostrando a % de eficiência em tempo real.
> 
> 
> 4. **Lista de Carrinhos Ativos (Checklist Mobile):** Abaixo dos indicadores, uma lista vertical de carrinhos que estão na "pista". Cada item da lista deve ter um botão de "CHECK" grande no lado direito, fácil de clicar com o polegar.
> 
> 
> **Paleta de Cores e Estilo:**
> * Use um tema "Dark Mode" ou "High Contrast" para facilitar a leitura sob as luzes da fábrica.
> * **Botão de Check:** Verde Vibrante (`#4CAF50`).
> * **Alertas:** Vermelho Crítico (`#F44336`).
> * Siga o rigor de **mínima carga cognitiva**: sem firulas, apenas dados e botões de ação.
> 
> 
> **Comportamento Responsivo:** No computador, os cards de indicadores devem ficar lado a lado. No celular, devem ser empilhados verticalmente para ocupar toda a largura da tela.
