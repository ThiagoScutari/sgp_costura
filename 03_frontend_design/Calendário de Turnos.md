### 🕒 Módulo: Configuração de Turnos e Intervalos

Este módulo alimenta a lógica de **Janela Útil** do motor de cronometragem. O sistema deve "pausar" a contagem do pulso (30/60 min) sempre que o horário atual cair dentro de um intervalo cadastrado.

#### 1. Interface de Cadastro

* **Definição de Turno:** Horário de Início e Horário de Término da jornada (ex: 05:00 às 14:48).
* **Lista de Intervalos:** Uma tabela onde o Owner adiciona as paradas programadas.
* *Exemplo:* Almoço (10:00 - 11:00), Café Manhã (07:30 - 07:45).


* **Dias da Semana:** Checkbox para aplicar o turno (Segunda a Sexta, Sábado, etc.).

#### 2. Lógica de "Pausa Ativa" (Back-end)

O cronômetro do Dashboard não para visualmente, mas o cálculo de `is_delayed` ignora esse tempo.

* **Regra:** Se o `pulse_start` foi às 09:45 e o pulso é de 30 min, ele venceria às 10:15. Porém, se há um almoço das 10:00 às 11:00, o sistema soma esse intervalo, e o novo vencimento real passa a ser **11:15**.

---

### 🎨 Esboço Visual (Grid de Horários)

```text
__________________________________________________________
| CONFIGURAÇÃO DE TURNO: [ Geral Têxtil ]                |
|________________________________________________________|
|                                                        |
| JORNADA: Início [ 05:00 ]  Fim [ 14:48 ]               |
|                                                        |
| INTERVALOS PROGRAMADOS:                                |
| 1. [ Café Manhã ] das [ 07:30 ] às [ 07:45 ] [ REMOVER]|
| 2. [ Almoço     ] das [ 10:00 ] às [ 11:00 ] [ REMOVER]|
|                                                        |
| [ + ADICIONAR INTERVALO ]                              |
|________________________________________________________|
|                                                        |
| [ CANCELAR ]                          [ SALVAR TURNO ] |
|________________________________________________________|

```

### 🛠️ Especificação para o Desenvolvedor

1. **Validação de Sobreposição:** O sistema não deve permitir cadastrar um intervalo que comece antes do turno iniciar ou termine após o turno acabar.
2. **Cálculo de Tempo Restante:** O endpoint da API que retorna o tempo do pulso deve sempre fazer a conta: `Tempo_Restante = (Pulse_Duration + Intervalos_No_Caminho) - Tempo_Decorrido`.
3. **Visual no Dashboard:** Quando a fábrica estiver em horário de intervalo, o cronômetro central deve mudar para um status de **"EM INTERVALO"** (cor cinza ou azul claro), indicando que a cadência está pausada.

