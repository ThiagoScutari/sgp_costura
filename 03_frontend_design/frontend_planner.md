### 1. Princípios de Design (O Rigor Visual)

* **Regra de 3 Cliques:** Qualquer ação crítica (como o check de um carrinho ou o fracionamento) deve ser acessível em no máximo 3 cliques.
* **Contraste de Status (Semáforo):** O uso de cores será funcional, não decorativo.
* **Verde:** Fluxo nominal.
* **Amarelo:** Alerta de tendência (atraso iminente).
* **Vermelho:** Gargalo ou parada (ação imediata requerida).


* **Touch-First:** A interface da Facilitadora deve ser otimizada para tablets, com botões grandes (alvos de toque) para evitar erros de seleção.

---

### 2. Módulo de Balanceamento (O Tetris Operacional)

Este foi o maior gargalo que discutimos. O Front-end aqui precisa ser um **Quadro Kanban Dinâmico**.

* **Painel Lateral de "Cards de Operação":** Cada card mostra o nome da operação, o tempo final e o ícone da máquina.
* **As 4 Colunas (Workstations):** * No topo: Foto/Nome da Costureira e Nível de Skill.
* No corpo: Espaço para soltar os cards.
* No rodapé: **O Termômetro de Tempo.** Uma barra que cresce conforme os cards entram. Se passar de 30 min, a barra "sangra" em vermelho e o botão **[FRACIONAR]** aparece automaticamente no card que causou o estouro.


* **Feedback Visual de Dependência:** Se eu tentar colocar a "Op 20" antes da "Op 10", o card da 20 fica translúcido ou exibe uma linha vermelha conectando-a à dependência faltante.

---

### 3. O Dashboard de Execução (Gestão à Vista)

Aqui o design é focado na Gerente e na Facilitadora. Deve ser limpo ("Lean").

* **O "Big Number" (Pulso):** Um cronômetro central gigante. Ele é o coração do sistema.
* **Lista de Carrinhos (Checklist):** * Cards horizontais grandes.
* Botão **[CONCLUIR]** no lado direito, na cor verde vibrante.
* Informação visual: "Lote 5/16" para que ela saiba exatamente quanto falta para acabar a OP.



---

### 4. Wireframe Lógico (Arquitetura da Informação)

Para não repetirmos o erro do passado, precisamos definir a navegação:

1. **Home:** Lista de OPs Ativas (Visão Geral).
2. **Configuração/Engenharia:** Onde o Owner (você) refina a PSO.
3. **Planejamento:** A tela de arraste e solte para o balanceamento.
4. **Operação (Checklist):** A tela exclusiva da Facilitadora na pista.

---

### Pergunta de "Cético" para você:

No projeto anterior, qual foi o ponto exato de ruptura no Front-end?

1. **Complexidade:** Muitas informações na tela e a Facilitadora se perdia?
	- Não consegui fazer um bom layout de tela, ficou quebrando ao utilizar o kanban. FIcou péssimo o visual da tela!
2. **Performance:** O sistema era lento e não acompanhava o ritmo da costura?
	- Nem cheguei no ponto de colocar no ar, desisti durante os testes no MVP
3. **Rigidez:** Quando algo dava errado (ex: uma costureira faltava), era muito difícil "mexer" no sistema?
	- Não cheguei nesse ponto de validação também. O sistema estava instavel, quebrava em varias etapas, principalmente quando não seguia o fluxo primário. Qualquer coisa que precisasse voltar ou editar quebrava. 
