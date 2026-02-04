### 1. Gatilho de Abertura

* O modal é disparado ao clicar no botão **[FRACIONAR]** que aparece automaticamente no rodapé da workstation quando o termômetro fica vermelho.
* O sistema já "sabe" qual é a última operação adicionada que causou o estouro e a sugere para o fracionamento.

### 2. Interface do Modal (UX)

O visual deve ser limpo, focando em "quanto sai" e "quanto fica".

* **Cabeçalho:** Nome da Operação + Tempo Unitário.
* **Seção de Divisão:**
* **Lado A (Mantém na WS Atual):** Input numérico para a quantidade de peças.
* **Lado B (Transborda para Próxima WS):** Cálculo automático do saldo.


* **Rodapé:** Botão **[CONFIRMAR DIVISÃO]** que só habilita se a soma de A + B for igual ao  (Tamanho do Lote).

### 3. Lógica de Recálculo (O "Pulo do Gato")

O backend não cria uma nova operação, ele cria uma **alocação parcial**.

* **Exemplo:**  peças. Operação #50 (Unir Lateral) tem 1.0 min.
* Se a WS 1 só tem 5 minutos livres, a Facilitadora define:
* **WS 1:** 5 peças (Carga: 5 min).
* **WS 2:** 15 peças (Carga: 15 min).


* **Resultado Visual:** O Card #50 aparece nas duas workstations, mas com um ícone de "divisão" e a quantidade parcial anotada no card.

---

### 4. Esboço Visual do Modal (Wireframe)

```text
__________________________________________________________
| FRACIONAR OPERAÇÃO: [102] PESPONTAR GOLA               |
| Tempo Unitário: 0.85s | Lote Total (TL): 16 peças      |
|________________________________________________________|
|                                                        |
|  QUANTO PERMANECE NA WS 1?      QUANTO VAI PARA WS 2?  |
|  [ 06 ] peças                   [ 10 ] peças           |
|  (Carga: 5.1 min)               (Carga: 8.5 min)       |
|________________________________________________________|
|                                                        |
| [ CANCELAR ]                        [ CONFIRMAR ]      |
|________________________________________________________|

```

### 5. Regras de Ouro para o Desenvolvedor

1. **Validação de Soma:** O modal não fecha se o usuário digitar valores que somados não batam com o .
2. **Sincronização:** Se o  mudar (porque o número de operadoras mudou), o fracionamento deve ser invalidado e refeito para manter a precisão.
3. **Visual do Card:** O card fracionado deve ganhar uma classe CSS `.card-partial` (talvez uma borda pontilhada) para que a Facilitadora saiba que aquela tarefa é compartilhada.

