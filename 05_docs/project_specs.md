# 📄 Documentação Detalhada: Passo 1 - Página 03

## Cockpit de Gestão e Engenharia de Produtos (PSO)

### 1. Objetivo da Página

A Página 03 é o **portal de entrada de dados** e o **centro de inteligência de engenharia**. Sua função é converter a Ficha Técnica estática (PDF) em uma **PSO (Product Sequence Order)** dinâmica. Ela permite que a gestão ajuste a teoria da engenharia para a realidade prática do chão de fábrica antes de gerar qualquer compromisso de produção.

---

### 2. Componentes da Interface (Global)

* **Barra de Ações Superior:**
* **Botão "ARQUIVADAS":** Filtra e exibe registros onde `is_archived = True`. Serve para auditoria de versões antigas e limpeza visual do cockpit.
* **Botão "IMPORTAR PDF":** Aciona o script de extração (extrator.py). O sistema deve validar a integridade do PDF, buscando campos de Referência, Descrição e a Tabela de Operações.


* **Grade de Cards (Product Grid):**
* Exibição dinâmica de todas as PSOs onde `is_archived = False`.
* **Ordenação:** Por data de criação (mais recentes primeiro) ou por status (Em Produção fixado no topo).



---

### 3. Anatomia do Card de Produto

Cada card é uma instância de uma versão específica da peça:

* **Identificadores Médios:**
* **Referência:** String única vinda da engenharia (Ex: H6344).
* **Descrição:** Nome completo da peça para facilitar a identificação visual.
* **ID da PSO:** Número de controle interno do banco de dados.
* **Versão:** Label de identificação (Ex: V1, V2, Ajustada_Maio).


* **Indicadores de Performance da Engenharia:**
* **TP Total (min):** Soma de todos os Tempos Reais das operações ativas.
* **Qtd. Operações:** Contador de processos manuais e de máquina vinculados.


* **Status de Fluxo (Badges):**
* **AGUARDANDO:** Versão pronta para ir para o balanceamento.
* **EM PRODUÇÃO:** Destaque em **Verde Vibrante**. Indica que esta é a versão que está "rodando" no monitor agora. *Regra: Apenas uma versão por referência pode estar ativa por vez.*



---

### 4. O Modal de Engenharia Fina (Detalhamento de Operações)

Este é o coração da Página 03. Ao clicar em "Ver Operações", o usuário acessa o controle granular:

#### **A. Configurações de Cabeçalho (Modal)**

* **Campo "Nome da Versão":** Texto editável. O sistema sugere "V[próximo número]" automaticamente ao detectar mudanças, mas permite renomeação customizada.
* **Campo "Eficiência Global (%)":** Input numérico (Master).
* **Comportamento:** Ao ser alterado, ele atualiza instantaneamente a eficiência de todas as linhas da tabela abaixo, recalculando todos os tempos reais de uma só vez.



#### **B. Tabela de Processos (Colunas Detalhadas)**

1. **Reordenação (Drag-and-Drop):** Ícone lateral que permite arrastar a linha. Essencial para corrigir PDFs que vêm com a sequência de montagem fora de ordem lógica.
2. **Sequência (Seq):** Número sequencial automático da operação **informação vem da extração do PDF**.
3. **Descrição da Operação:** Nome técnico da tarefa (Ex: "Overloque de ombros").
4. **Máquina (Dropdown Seletor):** Lista de maquinários disponíveis.
* *Categorias:* Reta, Overlock, Galoneira, Travete, Manual, etc.
* *Visual:* Cada máquina possui uma cor de fundo específica para facilitar a leitura rápida da linha de montagem.


5. **TP Padrão (min):** O tempo (decimal) teórico estipulado pela engenharia (cronometragem pura).
6. **Eficiência (%) por Operação:** * **Dinamismo:** Pode ser editada individualmente. Se uma operação é mais complexa, o usuário pode baixar a eficiência apenas dela, sem afetar o resto da peça.
7. **TP Real (min):** O tempo (decimal) que o sistema usará para os cálculos de produção.
* **Cálculo:** 
	$TP_{real} = \frac{TP_{padrão}}{(Eficiência / 100)}$

8. **Status "Ativa" (Switch/Checkbox):** Se desmarcado, a operação é ignorada na soma do TP Total. Útil para peças que sofreram simplificação de processo mas mantêm o histórico da operação.

#### **C. Rodapé de Cálculo**

* **Somatório Dinâmico:** Exibe em tempo real: `Soma de todos os TP Real (Ativos)`. Apresentado no formato `MM:SS` para precisão do gestor.

---

### 5. Regras de Negócio Cruciais

* **Sobrescrita Segura:** O usuário pode salvar alterações na versão atual (sobrescrever) desde que a produção não tenha sido iniciada. Se a produção já começou, o sistema bloqueia a sobrescrita e exige a criação de uma nova versão (V2, V3...).
* **Sugestão de Nome:** Para evitar que o usuário salve "em cima" da V1 (original da engenharia), o sistema sempre sugere um novo nome ao abrir o modal de edição.
* **Persistência de Dados:** Toda alteração de eficiência ou tempo deve ser persistida imediatamente ao clicar em "Salvar", gerando um novo timestamp de atualização.

---

## 📄 Detalhamento Técnico: Sistema de Arquivamento (Página 03)

O arquivamento no SGP Costura utiliza o conceito de **Soft Delete**. Isso significa que nenhum dado de engenharia é realmente apagado do banco de dados; ele apenas recebe uma "etiqueta" invisível (`is_archived = True`) que o remove do fluxo de trabalho ativo.

### 1. O Fluxo de Arquivamento (Ação do Usuário)

* **Ponto de Acesso**: Dentro do modal de "Ver Operações", ao lado dos botões de salvar e balancear.
* **Gatilho**: Botão **"ARQUIVAR VERSÃO"** (Destaque em Vermelho).
* **Camada de Segurança**: O sistema dispara um alerta de confirmação: *"A versão 'X' será removida da lista principal, mas poderá ser restaurada depois. Confirma o arquivamento?"*.
* **Resultado Imediato**: O card do produto desaparece da grade principal de PSOs, e o monitor de fábrica (`page_01`) deixa de listar essa versão como opção para produção.

### 2. O Modal de PSOs Arquivadas (Histórico)

Ao clicar no botão **"ARQUIVADAS"** no cabeçalho superior, o sistema abre uma interface de consulta histórica.

**Colunas da Tabela de Arquivo:**

* **Produto**: Referência original (ex: H6344).
* **Versão**: O nome customizado ou automático que a versão recebeu (ex: V2_TESTE_13_OPERAÇÕES).
* **Operações**: Quantidade de processos que aquela versão possuía.
* **Data Arq.**: Registro cronológico de quando a versão saiu de linha.
* **Ação (Botão Restaurar)**: O caminho de volta para o cockpit.

### 3. Lógica de Restauração (O Caminho de Volta)

* **Funcionalidade**: Ao clicar em **"RESTAURAR"**, o sistema inverte o sinal no banco de dados (`is_archived = False`).
* **Feedback Visual**: Uma mensagem de sucesso confirma: *"Restaurado com sucesso!"* e o item retorna imediatamente para a grade principal com todos os seus tempos e configurações de eficiência preservados.

---

### 🧠 Regras de Negócio do Arquivamento

1. **Proteção de Produção Ativa**: O sistema é inteligente o suficiente para impedir o arquivamento de uma versão que esteja **atualmente em produção** (marcada com o badge verde). Isso evita que o monitor de fábrica perca a referência do que está sendo cronometrado.
2. **Independência de Versões**: Arquivar a "V2" não afeta a "V1" ou a "V3". Cada PSO é tratada como um registro único de engenharia.
3. **Auditoria Passiva**: Como o registro permanece no banco, o Dashboard BI (Página 07) pode futuramente consultar versões arquivadas para comparar a eficiência de um método antigo com o novo.

---

### 1. Acesso Direto via Card de Produto (Página 03)

Este é o caminho mais rápido para quem já sabe qual referência deseja balancear no momento.

* **Onde**: Localizado no rodapé de cada card de PSO na grade principal da Gestão de OPs.
* **Ação**: Clique no botão azul **"Balancear"**.
* **Funcionamento Técnico**: O sistema realiza um redirecionamento injetando o ID da PSO na URL (ex: `page_03.html?pso_id=13`).
* **Resultado**: O Cockpit VAC abre já "carregado", trazendo automaticamente todas as operações ativas daquela versão e a lista de costureiras prontas para a alocação.

### 2. Acesso via Modal de Detalhes de Engenharia (Página 03)

Ideal para quando você acaba de fazer um ajuste fino (como alterar uma eficiência individual ou inativar uma operação) e quer testar esse novo cenário imediatamente.

* **Onde**: Localizado no rodapé do modal "Ver Operações", entre as opções de "Arquivar" e "Salvar".
* **Ação**: Após revisar os tempos, clique no botão azul **"BALANCEAR"**.
* **Funcionamento Técnico**: Assim como no acesso anterior, ele transporta o contexto da PSO atual para o balanceamento.
* **Vantagem**: Garante que o balanceamento seja feito com base nas alterações de tempo real que você acabou de validar no modal.

### 3. Acesso via Menu Lateral (Sidebar)

Este é o acesso administrativo ou de consulta, usado para visualizar o que já está em andamento ou iniciar um processo sem partir de um card específico.

* **Onde**: Item **"Cockpit VAC"** no menu fixo à esquerda (comum em todas as telas).
* **Ação**: Clique direto no ícone de configuração/sintonia do menu.
* **Funcionamento Técnico**: A página é carregada em seu **estado neutro (vazio)**.
* **O "Estado Zero"**: Diferente dos outros acessos, aqui o sistema exibe a mensagem: *"Nenhuma OP Carregada. Clique em 'ABRIR' no menu superior para selecionar uma Ordem de Produção e iniciar o balanceamento"*. Este caminho exige que o usuário use o botão de busca interna da própria Página 03 para localizar o produto.

---

## 📄 Documentação Detalhada: Passo 2 - Página 03

## Cockpit VAC (Valor Agregado Contínuo) – Configuração e Balanceamento

O Cockpit VAC é onde a estratégia de produção é definida. É nesta tela que o gestor decide a velocidade da fábrica (Pulso) e como a carga de trabalho será distribuída.

### 2. Interface Superior: Botões de Controle e Ação

No topo da Página 04, encontramos os comandos de gestão do balanceamento:

* **REINICIAR**: Limpa todas as alocações atuais da célula, devolvendo todas as operações para o "Banco de Operações" (lado esquerdo) para um novo começo.
* **ABRIR**: Abre um seletor de Ordens de Produção (PSO), permitindo trocar de peça ou versão sem sair da tela.
* **CARREGAR**: Recupera balanceamentos salvos/publicados, evitando retrabalho em peças recorrentes. (Validar PSO Arquivadas para evitar conflitos, avisar o usuário e perguntar se desejar restaurar)
* **PUBLICAR**: O comando final. Envia a configuração para o banco de dados, gera os carrinhos (lotes) e disponibiliza a OP para o Monitor de Fábrica (Página 01).

---

### 3. Cabeçalho Dinâmico: O Motor de Cálculo do TL

O diferencial desta tela é o **Cálculo de Capacidade em Tempo Real**. Diferente de sistemas estáticos, aqui os campos interagem entre si:

* **QTD. TOTAL (pçs)**: Campo de entrada onde o gestor define o tamanho total da Ordem de Produção (Ex: 500 ou 1000 peças).
* **PULSO DESEJADO (min)**: Menu dropdown (30 ou 60). Define a cadência da fábrica — o tempo que um lote deve levar para sair.
* **TP PEÇA (min)**: Valor informativo trazido da Página 03. Representa o tempo total real necessário para fabricar uma unidade.
* **TOTAL OPERADORES**: Contador dinâmico que exibe quantas costureiras estão ativas ou alocadas no balanceamento atual (Configurações - Tela 06).
* **TAMANHO DO LOTE (TL)**: **O campo mais importante.** Ele é o resultado dinâmico da fórmula:

### Calculo importante
	
	TL} = floor((Operadores x Pulso)/TP Peça)

* **Comportamento observado**: Se o Pulso é alterado de 60 para 30 minutos, o TL cai proporcionalmente (Ex: de 45 para 22 peças), garantindo que a meta de tempo seja mantida independentemente da quantidade.

O **TL (Tamanho do Lote)** é o indicador que dita a logística do chão de fábrica. Ele não é um número estático; ele é o equilíbrio entre tempo, pessoas e produto.

* **A Fórmula de Precisão**: O cálculo é processado pelo `engine.py`, garantindo que o lote nunca exceda a capacidade física da célula no tempo do pulso:

---

### 2. Distribuição de Carga e o Sistema de "Farol"

A distribuição de operações no VAC é baseada no conceito de **Carga por Operadora**.

* **Soma de Minutos**: Cada card de costureira exibe o somatório dos tempos reais de todas as operações arrastadas para ela.
* **O Farol de Eficiência**:
* O sistema calcula a porcentagem de ocupação da costureira em relação ao pulso.
* **Visual**: Se o pulso é de 60 min e a soma das operações é 58 min, a carga está próxima de 100% (ideal). Se ultrapassar 100%, o sistema indica sobrecarga, sinalizando que a costureira não conseguirá entregar o lote no tempo previsto, o que gerará atrasos no monitor (`page_01`).

---

### 3. Fracionamento: A Chave do Balanceamento Perfeito

O fracionamento é a funcionalidade mais avançada do sistema. Ele resolve o problema de operações "gargalo" ou tempos que não encaixam perfeitamente em uma única pessoa.

* **A Lógica**: Permite dividir uma única operação (ex: "Pregar Manga") entre duas operadoras diferentes.
* **Interface**: Ao clicar em **"FRACIONAR"**, abre-se um modal onde o gestor define quantas peças daquele lote a operadora original fará e para quem o restante será enviado.
* **Persistência no Banco (Crítico)**:
* No banco de dados, o registro na tabela `operation_allocations` é salvo com a flag `is_fractioned = True`.
* Isso é vital para o **Dashboard (Página 07)**, pois a eficiência deve ser calculada proporcionalmente à quantidade de peças que cada operadora de fato executou naquela operação.

---

### 4. Gestão de Estado: Carregamento e Integridade

O botão **"CARREGAR"** recupera o estado salvo de um balanceamento anterior para evitar retrabalho.

* **Fidelidade Visual**: Ao carregar, cada operação (incluindo as fracionadas) deve retornar exatamente para a posição e para a operadora onde foi configurada anteriormente.
* **Validação de Mão de Obra (Regra de Ouro)**:
* Se um balanceamento foi salvo para **6 costureiras**, mas hoje a célula só tem **5 ativas**, o sistema **não permite o carregamento direto**.
* **Ação**: O sistema avisa o usuário sobre a discrepância e realiza o **Reset Automático**, forçando uma nova distribuição. Carregar um balanceamento com número errado de pessoas destruiria a precisão matemática do pulso e do TL.



---

# 📄 Documentação Detalhada: Passo 3 - Página 01

## Monitor de Fábrica – O Coração do Sistema VAC

### 1. Estado Inicial: Preparação e Start da Produção

Antes de qualquer cronômetro girar, o Monitor de Fábrica permanece em um "Estado de Espera" (Idle), focado em garantir que o balanceamento correto seja ativado.

* **Seletor de Planejamento**: O gestor visualiza uma lista suspensa com todos os balanceamentos publicados no Cockpit VAC. Cada opção detalha a **Referência**, o **Nome da Versão** e a **Data de Publicação**.
* **Gatilho de Início (🚀 INICIAR LOTE)**: Ao clicar, o sistema realiza uma verificação de segurança de **Horário de Intervalo**.
* *Lógica*: Se o sistema detectar que a fábrica está em horário de almoço ou café, ele solicita uma confirmação adicional do gestor antes de processar o início.


* **Ativação Sistêmica**: No banco de dados, o `ProductionPlanning` selecionado recebe a flag `is_active = True`, desativando automaticamente qualquer planejamento anterior para garantir a unicidade da sessão.

---

### 2. Interface de Tempo Real (O "Metrônomo" Visual)

Uma vez iniciada a produção, a interface se transforma em um painel de monitoramento crítico:

* **Timer Card (O Pulso Ativo)**:
* **Cronômetro Principal**: Exibe o tempo decorrido desde o início da sessão ou desde o último "checkout" de carrinho realizado na Tela 05.
* **Próximo Lote em...**: Uma contagem regressiva baseada no **Pulso (30 ou 60 min)** configurado na Página 04.
* **Cores Dinâmicas de Status**:
* **Azul**: Pulso saudável (dentro do tempo).
* **Amarelo (Atenção)**: Tempo decorrido ultrapassou 80% do pulso.
* **Vermelho (Atrasado)**: O tempo excedeu o pulso definido, sinalizando gargalo na linha.
* **Amarelo-Pulsante**: Produção pausada manualmente.

---

### 3. Métricas de Performance e Progresso

O sistema calcula e exibe em tempo real o desempenho da célula:

* **Indicador de Eficiência (%)**: Calcula a relação entre o trabalho teórico (TP das operações) e o tempo real trabalhado.
* *Fórmula*: .


* **Barra de Progresso da OP**:
* Visualização clara de quantos lotes foram concluídos vs. o total planejado (Ex: Lote 0 de 24).
* Exibe o percentual de conclusão e o saldo restante para a finalização da Ordem de Produção.

---

### 📦 Definição e Cálculo Dinâmico de Lotes (Carrinhos)

No SGP Costura, o termo **Lote** (ou **Carrinho**) não é um número fixo, mas sim a unidade logística que transporta a produção pelo chão de fábrica. O entendimento da relação entre a quantidade total, o tamanho do lote e o número de carrinhos é o que garante o fluxo contínuo (VAC).

#### 1. A Hierarquia do Dado

Para que a produção seja organizada, o sistema decompõe a Ordem de Produção (OP) em três camadas:

* **Quantidade Total (OP):** O volume total de peças a serem produzidas (ex: 1.000 peças).
* **Tamanho do Lote (TL):** A "capacidade" de cada carrinho, definida dinamicamente na Página 04. É a quantidade de peças que uma célula consegue processar dentro de um **Pulso** (30 ou 60 min).
* **Lote (O Carrinho):** É a unidade física e sistêmica. Cada lote recebe um ID único e é representado por um carrinho que percorre a fábrica.

#### 2. A Matemática do Fluxo

A quantidade de lotes (carrinhos) que aparecerá na **Página 05** e será monitorada na **Página 01** é o resultado direto da divisão da carga total pela capacidade do pulso:

`Quantidade de Lotes (Carrinhos) = Quantidade Total de Peças / Tamanho do Lote (TL)`

* **Exemplo Prático:**
* Se a OP é de **1.000 peças** e o cálculo dinâmico (baseado em operadoras e pulso) definiu um **TL de 82 peças**;
* O sistema gerará **13 carrinhos** (12 carrinhos de 82 peças e 1 carrinho residual com o saldo).

#### 3. A Importância da Dinamicidade

Diferente de sistemas tradicionais onde o lote é fixo (ex: sempre 50 peças), no SGP o número de lotes se adapta à realidade do dia:

* **Cenário A (Alta Capacidade):** Se você tem 15 costureiras e um pulso de 60 min, o **TL** será maior (ex: 100 peças). Isso resultará em **menos carrinhos** circulando, porém mais "pesados".
* **Cenário B (Baixa Capacidade):** Se houver faltas e você tiver apenas 8 costureiras, o **TL** diminuirá (ex: 40 peças). O sistema automaticamente gerará **mais carrinhos** para manter o mesmo ritmo de pulso (cadência).

#### 4. Reflexo no Sistema

* **Na Página 04:** O sistema exibe o TL calculado. Ao clicar em "Publicar", ele realiza a divisão e cria no banco de dados (`cart_lote`) a quantidade exata de registros (carrinhos).
* **Na Página 01:** O progresso é medido por esses lotes (ex: "Lote 2 de 13").
* **Na Página 05:** Cada registro gerado vira um checklist individual para a facilitadora bipar/finalizar.
* **Na Página 07:** Cada registro gerado é contabilizado no dashboard.

---

### 4. Gestão da Célula Ativa (Costureiras)

Abaixo das métricas, o monitor lista todas as operadoras que estão "no campo" naquele planejamento:

* **Identificação por Posição**: Cards numerados seguindo a sequência física da célula.
* **Carga de Trabalho**: Exibe o número de operações que cada costureira está executando simultaneamente (Load Count).
* **Status de Atividade**: Indicador visual (verde pulsante) confirmando que a costureira está com o status "Produzindo" no sistema.

---

### 5. Comandos Operacionais (Painel de Controle)

O gestor possui quatro comandos fundamentais para lidar com imprevistos:

1. **PAUSAR/CONTINUAR**: Registra eventos de pausa (`ProductionEvent`) para que o tempo parado não prejudique o cálculo de eficiência das costureiras.
2. **REBALANCEAR**: Usado para "trocar o pneu com o carro andando". Se uma costureira faltar no meio da OP, o sistema redireciona para o Cockpit VAC, calculando automaticamente o saldo de peças restante para um novo balanceamento.
3. **PARAR**: Finaliza a sessão de produção de forma manual.
4. **Auto-Stop (Sistêmico)**: O sistema é inteligente para se desligar sozinho. Quando o último carrinho é finalizado na **Página 05**, o Monitor encerra o planejamento e registra o evento de conclusão final no banco.

---

# 📄 Detalhamento Técnico: Rebalanceamento Dinâmico (Página 01 para 04)

### 1. O Conceito de "Snapshot" (Foto do Momento)

Quando você clica em **REBALANCEAR**, o sistema não simplesmente "edita" o plano atual. Ele executa um **encerramento parcial** da sessão ativa.

* **O Corte**: O sistema contabiliza exatamente quantos carrinhos (lotes) já foram finalizados na Página 05 até aquele segundo.
* **Preservação**: Todos os registros de `batch_tracking` e `cart_lote` concluídos são "congelados". Eles permanecem vinculados ao `planning_id` original para que o Dashboard saiba quem produziu o quê e em qual ritmo antes da mudança.

---

### 2. A Matemática do Saldo Remanescente

Ao ser redirecionado para a Página 04, o sistema injeta na URL o **Saldo de Peças**.

* **Cálculo do Saldo**: .
* **Exemplo**: Se a OP era de 1.000 peças e você rebalanceou após concluir 400 peças, o Cockpit VAC abrirá com a meta de **600 peças**.
* **Recálculo do TL**: Com uma costureira a menos, o novo **Tamanho do Lote (TL)** será recalculado sobre essas 600 peças. O sistema gerará novos carrinhos (ex: agora com 40 peças em vez de 82) para se ajustar à nova realidade da célula, mantendo o pulso de 30 ou 60 minutos.

---

### 3. O Desafio do Dashboard (Página 07) – A Fusão dos Dados

Este é o ponto que você destacou: **o que passou deve permanecer.** Para o BI, a Ordem de Produção (H6344) é uma só, mesmo que ela tenha tido dois ou três planejamentos diferentes.

* **Agregação por Referência**: Na Página 07, os cálculos de eficiência e produção horária não olham apenas para um `planning_id`, mas sim para todos os planejamentos que pertencem àquela mesma OP/Referência.
* **Visibilidade da Mudança**: O gráfico de barras ou linhas deve mostrar uma "marcação" (uma linha vertical ou mudança de cor sutil) no momento em que o rebalanceamento ocorreu. Isso permite que você analise: *"Com 12 costureiras minha eficiência era X, após o rebalanceamento com 11, minha eficiência foi Y"*.

---

### 4. Fluxo Sistêmico de Rebalanceamento

1. **Gatilho (Página 01)**: O gestor identifica a falta de uma operadora e clica em **Rebalancear**.
2. **Cálculo de Saldo**: O backend encerra o planejamento atual, calcula as peças restantes e gera um token de rebalanceamento.
3. **Ajuste (Página 04)**: O gestor inativa a costureira faltante. O sistema recalcula o **TL** para as peças restantes.
4. **Publicação**: Um novo planejamento é criado (ex: H6344_V2).
5. **Retorno (Página 01)**: O monitor reinicia o cronômetro para o novo primeiro lote do saldo restante.

---

### 🧠 Regra de Ouro do Rebalanceamento

> **"A história é sagrada"**: O sistema nunca apaga um lote que já foi bipado. Se o lote 5 foi finalizado pela 'Maria' antes do rebalanceamento, ele contará para a eficiência da 'Maria' no Dashboard, mesmo que no novo balanceamento a operação dela tenha sido passada para a 'Joana'.

---

# 📄 Documentação Detalhada: Passo 4 - Página 05

## Checklist Final – O Ponto de Escoamento da Produção

### 1. Objetivo da Página

A Página 05 funciona como um terminal de apontamento de produção simplificado. Sua função é listar os carrinhos gerados no balanceamento (Página 04) e permitir que a facilitadora registre a conclusão de cada um. Este registro é o gatilho que reseta o pulso no Monitor (Página 01) e alimenta os gráficos de eficiência no Dashboard (Página 07).

---

### 2. Anatomia do Cabeçalho (Sincronização Ativa)

O cabeçalho é projetado para identificação rápida no tablet ou celular da facilitadora:

* **OP Ativa:** Exibe o código da Ordem de Produção (ex: H6344).
* **Referência:** Descrição comercial da peça, garantindo que o lote físico em mãos coincide com o sistema.
* **Indicador de Lote (TL):** Destaque em **Verde Vibrante** exibindo o Tamanho do Lote calculado dinamicamente na Página 04 (ex: 82 pç ou 45 pç).
* *Inteligência de Rebalanceamento:* Se o gestor alterar o balanceamento no meio da OP, este número muda instantaneamente nesta tela após o próximo polling.

---

### 3. O Carrinho Atual (Área Crítica)

Esta seção foca exclusivamente no lote que está sendo finalizado naquele momento:

* **Número do Carrinho:** Exibição em fonte extragrande (ex: **#1**) para visibilidade à distância.
* **Cronômetro Individual:** Mostra o tempo que este carrinho específico está levando para ser concluído (exibir o mesmo tempo do Pulso ativo da Tela 01.
* **Botão de Ação "FINALIZAR LOTE":**
* **Mecanismo de Segurança (Double Click):** Para evitar finalizações acidentais em telas touch, o botão utiliza um sistema de "armamento".
* **1º Clique (Armar):** O botão muda para um tom de verde escuro, pulsa e exibe o texto "Confirmar?".
* **Timeout:** Se o segundo clique não ocorrer em 3 segundos, o botão desarma automaticamente.
* **2º Clique (Confirmar):** Dispara a requisição `POST /api/batches/checkout` para o backend.

---

### 4. Sequência na Célula (Fila de Espera)

Abaixo do carrinho ativo, o sistema exibe os próximos lotes na fila, permitindo que a facilitadora se antecipe à logística:

* **Próximos 3 Lotes:** Mostra os IDs (ex: #2, #3, #4) com status "Na fila".
* **Contador Residual:** Indica quantos lotes ainda restam para o fim da OP (ex: "+ mais 19 lotes").

---

### 5. Integração Sistêmica (A Reação em Cadeia)

Quando o botão de finalizar é confirmado, o sistema executa três ações simultâneas:

1. **Reset de Pulso (Page 01):** O cronômetro de "Pulso Ativo" no Monitor de Fábrica volta para 00:00 e inicia a contagem para o próximo lote.
2. **Incremento de Produção:** O contador "Lote X de Y" na Page 01 é atualizado e a barra de progresso avança.
3. **Cálculo de Eficiência:** O backend calcula se o fechamento ocorreu antes ou depois do pulso (atraso) e recalcula a eficiência instantânea que será exibida no Monitor e no Dashboard.
4. **Auto-Stop:** Se o carrinho finalizado for o último da sequência planejada, o sistema encerra a sessão de produção automaticamente.

---

### 🧠 Regras de Negócio e Proteções

* **Vínculo de Lote:** A Página 05 só exibe carrinhos vinculados ao `planning_id` que está marcado como `is_active=True`. Se não houver produção iniciada, a tela exibe o estado vazio: "Não há lotes em produção".
* **Integridade de Quantidade:** Cada carrinho "baixa" do estoque de produção exatamente a quantidade (`quantity_pieces`) definida no momento do seu nascimento (Página 04), garantindo que o saldo final da OP seja exato.

---


# 📄 Documentação de Alta Precisão: Passo 5 - Página 07

## Dashboard de Performance Industrial (BI)

### 1. Filosofia do Dado

O Dashboard não lê o "planejamento", ele lê a **rastreabilidade**. A fonte primária da verdade é a tabela `batch_tracking`. Se um lote foi físico, ele gerou um registro de rastreio; se há rastreio, o gráfico **tem** que refletir a produção, independentemente de ter sido antecipado ou atrasado.

---

### 2. Especificação Atômica dos Gráficos

#### **A. Gráfico de Eficiência Instantânea (Gauge/Dial)**

* **Objetivo:** Mostrar a performance da célula no exato momento.
* **Origem do Dado:** Cruzamento entre `production_planning` (meta) e `batch_tracking` (realizado).
* **Cálculo:**

	$$\text{Eficiência} = \left( \frac{\sum \text{Peças de Lotes Concluídos}}{\text{Capacidade Teórica no Tempo Decorrido}} \right) \times 100$$

* **Tratamento de Antecipação:** O cálculo de "Peças Concluídas" deve somar o campo `quantity_pieces` de todo `cart_lote` que possua um registro em `batch_tracking` com o `planning_id` ativo. **Regra Atômica:** Não deve haver filtro de horário; se o status mudou para 'Concluído', ele entra no numerador do cálculo imediatamente.

#### **B. Produção Horária (Gráfico de Barras)**

* **Objetivo:** Visualizar a constância da produção e identificar quedas de ritmo (gargalos).
* **Origem do Dado:** Tabela `batch_tracking` filtrada por `created_at`.
* **Cálculo:** Agrupamento (COUNT) de `batch_id` e soma (SUM) de `quantity_pieces` truncados por hora cheia (ex: 08:00, 09:00).
* **Impacto de Eventos:**
* **Pausas:** O gráfico deve exibir um "vazio" ou uma barra reduzida, refletindo fielmente a parada registrada em `production_events`.
* **Antecipação:** Se dois carrinhos forem finalizados dentro da mesma hora (mesmo que o pulso previsse apenas um), a barra daquela hora deve exibir o volume real (ex: 164 peças em vez de 82).



#### **C. Progresso da OP (Barra de Preenchimento)**

* **Objetivo:** Visão macro da entrega.
* **Origem do Dado:** Tabela `production_order` (Total) e `cart_lote` (Status 'Concluído').
* **Cálculo:**

	$$\% \text{ Conclusão} = \left( \frac{\text{Lotes com status 'Concluído'}}{\text{Total de Lotes gerados no Planning}} \right) \times 100$$

* **Regra de Rebalanceamento:** Este gráfico é o único que deve ser **persistente por Referência**. Se a OP H6344 foi rebalanceada, a barra de progresso deve somar os lotes concluídos do *Planning V1* e do *Planning V2*.

---

### 3. Matriz de Impacto de Eventos (Lógica de Negócio)

| Evento | Impacto no Dashboard | Lógica de Cálculo |
| --- | --- | --- |
| **Start/Resume** | Inicia/Retoma a contagem de tempo de disponibilidade. | O denominador da eficiência volta a crescer baseado no `created_at` do evento. |
| **Pause** | Congela o denominador da eficiência. | O tempo entre `pause` e `resume` é subtraído do tempo total disponível para não penalizar a eficiência da célula. |
| **Checkout (Bipe)** | Incrementa o numerador instantaneamente. | **Onde estava o erro:** O sistema deve buscar o `cart_lote.quantity_pieces` e somar ao volume produzido assim que o registro entra em `batch_tracking`. |
| **Rebalancear** | Cria um "Marco Zero" de performance. | O Dashboard inicia uma nova série de dados de eficiência, mas mantém o histórico anterior para comparação de "Antes vs. Depois". |

---

### 4. Resolução do Erro: Carrinhos Antecipados

Para que os carrinhos antecipados sejam contabilizados, a query do backend no `main.py` deve ser ajustada para:

1. **Não ignorar bipes rápidos:** Se o `batch_tracking.created_at` ocorrer apenas 10 minutos após o anterior (em um pulso de 30), ele deve ser processado normalmente.
2. **Sincronização de Status:** O Dashboard deve ler o status do `cart_lote`. Se `status = 'Concluído'`, o dado é computado.
3. **Ajuste de Horário de Corte:** Certificar que o timezone do banco de dados (PostgreSQL) e do servidor (FastAPI) estão sincronizados, para que um bipe às 09:59 não caia na barra das 10:00 por erro de milissegundos.

---

### 🧠 Regra de Ouro para a Tela 07

> **"O Dashboard é o espelho do banco, não do cronômetro"**. Se o cronômetro da Página 01 está atrasado, mas a facilitadora bipou o carrinho na Página 05, o Dashboard deve mostrar a produção realizada. A antecipação é um ganho de eficiência e deve elevar o ponteiro do Gauge para cima de 100%.


Thiago, você está coberto de razão. Para uma gestão de manufatura de alto nível, saber a carga por operadora é apenas metade da equação; a outra metade é a **Ocupação do Parque de Máquinas**. Se o seu balanceamento está sobrecarregando as Overlocks enquanto as Retas estão ociosas, você tem um gargalo oculto.

Aqui está a documentação **atômica** deste gráfico, com o rigor técnico que você exigiu.

---

## 📊 Gráfico: Ocupação por Tipo de Máquina (Machine Load Balance)

### 1. Objetivo do Gráfico

Identificar o nível de saturação tecnológica da célula. Ele revela se a mistura de produtos (Product Mix) está adequada ao maquinário disponível ou se a produção vai travar por falta de equipamentos específicos.

### 2. Especificação Atômica do Dado

* **Origem do Dado (Source):** * **Engenharia:** Tabela `operations` (campo `original_machine` e `tp_real`).
* **Planejamento:** Tabela `operation_allocations` vinculada ao `production_planning` ativo.
* **Execução:** Tabela `cart_lote` (para o volume de peças).


* **Agrupamento:** O dado é consolidado por categoria de máquina (Ex: RETA, OVERLOCK, COBERTURA, CATRACA, MANUAL).

### 3. O Cálculo de Ocupação (%)

O gráfico compara a **Carga Necessária** contra a **Capacidade Disponível** por tipo de máquina.

* **Carga de Trabalho (Minutos Requeridos):**

	$$\text{Carga} = \sum (\text{TP Real da Operação} \times \text{Quantidade Total da OP})$$

*Aqui, somamos o tempo de todas as operações que utilizam aquele tipo de máquina.*
* **Capacidade Disponível (Minutos Máquina):**


* **A Fórmula do Gráfico:**

	$$\text{Ocupação por Máquina} = \left( \frac{\text{Carga}}{\text{Capacidade}} \right) \times 100$$

---

### 4. Tratamento de Carrinhos Antecipados e Atrasados

Este é o ponto onde o erro que você notou deve ser corrigido. O gráfico de ocupação deve ter duas barras ou uma sobreposição (Planejado vs. Real):

1. **Ocupação Planejada (Cinza):** Baseada no TP da engenharia e no tempo de pulso.
2. **Ocupação Real (Colorida):** Baseada nos eventos de `batch_tracking`.
* **Se houve antecipação:** O sistema deve reconhecer que a máquina processou o lote em menos tempo que o planejado. Isso **diminui** o percentual de ocupação real (mostrando que a máquina foi mais eficiente).
* **Sincronização Crítica:** Quando a facilitadora bipa o "Checkout" na Página 05, o sistema deve calcular o delta entre o `start_time` da sessão e o `concluded_at` do lote. Se esse delta for menor que o TP acumulado, a ocupação deve ser atualizada para refletir essa folga ganha.


---

### 5. Impacto de Eventos no Gráfico

* **Pausas (ProductionEvent):** Quando a produção para, a **Capacidade Disponível** diminui. Consequentemente, a **Ocupação (%)** sobe, pois o sistema entende que você tem menos tempo para realizar a mesma carga.
* **Fracionamento (Página 04):** Se uma operação de "Reta" foi fracionada entre duas operadoras, a carga da "Reta" no gráfico permanece a mesma (o trabalho não mudou), mas o sistema valida se existem duas máquinas disponíveis para evitar erro de cálculo de capacidade física.
* **Rebalanceamento:** Ao rebalancear e inativar uma máquina, a barra de capacidade desse tipo de máquina "encolhe" instantaneamente no gráfico, disparando o alerta de sobrecarga (Farol Vermelho) se a carga restante for maior que o tempo disponível.

---

### 🧠 Regra de Ouro da Ocupação

> **"Máquina parada é custo fixo sem retorno"**. Este gráfico deve servir para analise a quantidad de trabalho destinado a cada máquina e avaliar colocar em produção OP que balanceem as máquinas.

---


Entendido, Thiago. Se o Dashboard é o espelho da fábrica, a **Configuração** é o "DNA" que define as regras desse espelho. Sem uma configuração atômica, o cálculo de eficiência é apenas um número aleatório.

Vamos detalhar a camada que sustenta todo o SGP. No seu sistema, isso se divide em três pilares: **Maquinário**, **Recursos Humanos** e **Calendário Operacional**.

---

# 📄 Documentação de Alta Precisão: Passo 6 - Configurações

## Parâmetros Globais e Regras de Negócio do Sistema

### 1. Cadastro de Máquinas (Capacidade Tecnológica)

Este é o inventário que alimenta o Gráfico de Ocupação da Página 07.

* **Campos Atômicos:**
* **ID da Máquina:** Identificador patrimonial único.
* **Tipo/Categoria:** (Reta, Overlock, Galoneira, etc.). Esta categoria deve ser *exatamente* igual à usada no seletor da Página 03.
* **Status de Disponibilidade:** (Ativa, Manutenção, Inativa).


* **Regra de Impacto:**
* **No Dashboard:** O somatório de máquinas "Ativas" por categoria define o **Denominador** (Capacidade Disponível) do gráfico de ocupação. Se você marcar uma Overlock como "Manutenção", a capacidade daquele setor cai e a barra de ocupação sobe proporcionalmente.



---

### 2. Gestão de Operadoras (O Capital Humano)

Define quem são as pessoas que o Cockpit VAC (Página 04) pode utilizar para o balanceamento.

* **Campos Atômicos:**
* **Nome Completo:** Identificação visual nos cards.
* **Eficiência Base (%):** A eficiência histórica daquela operadora.
* **Status (`is_active`):** O campo mais crítico do sistema.


* **Regra de Impacto:**
* **No VAC (Página 04):** Apenas operadoras com `is_active = True` aparecem para alocação.
* **No Rebalanceamento:** Inativar uma operadora aqui dispara o alerta de necessidade de rebalanceamento na Página 01.
* **No Dashboard:** Define o cálculo de **Eficiência Individual**. Se o sistema sabe que a 'Maria' está ativa, ele buscará os lotes vinculados ao ID dela para gerar o ranking de performance.



---

### 3. Calendário e Jornada de Trabalho (O "Relógio de Célula")

Este é o motor que governa os cronômetros e os cálculos de eficiência temporal.

* **Configuração de Turno:**
* **Horário de Início/Fim:** Ex: 07:30 às 17:30.
* **Intervalos (Pausas Programadas):** Café da manhã, Almoço, Café da tarde.


* **Regra de Cálculo de Eficiência (Denominador):**
* O tempo total disponível para o cálculo de eficiência **subtrai automaticamente** os intervalos configurados.
* **Fórmula do Tempo Útil:**

	$$T_{disponível} = (T_{atual} - T_{início}) - \sum T_{intervalos\_decorridos} - \sum T_{pausas\_manuais}$$


* **Impacto no Monitor (Página 01):**
* Se o cronômetro atingir um horário de intervalo, o sistema entra em modo de **"Pausa Automática"**, impedindo que a eficiência caia injustamente enquanto as costureiras não estão na máquina.



---

### 4. Parâmetros de Tolerância (Configurações de Farol)

Define as cores que o sistema assume nas outras telas.

* **Limites de Eficiência:**
* **Verde: > 90% ** 
* **Amarelo: 75% a 90% ** 
* **Vermelho: < 75% ** 


* **Tolerância de Pulso:** Define em que momento o cronômetro da Página 01 deve começar a "pulsar" em amarelo (ex: faltando 20% para o fim do tempo de pulso).

---

### 🧠 A "Lógica Atômica" da Configuração

> **"Configuração não é cadastro, é restrição"**. No SGP, a configuração serve para restringir o sistema à realidade física. Se você tem 10 máquinas mas apenas 8 operadoras ativas, a sua capacidade máxima real é limitada pelas 8 pessoas. O sistema usa a configuração para cruzar esses dados e te avisar: *"Você tem máquina sobrando, mas falta gente para o Pulso de 30 min"*.

---
