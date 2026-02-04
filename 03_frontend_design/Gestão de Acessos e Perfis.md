### 🛡️ Módulo: Gestão de Acessos e Perfis (Roles)

Esta tela é de uso exclusivo do **Owner**. Nela, você fará a gestão de quem pode apenas olhar os dados e quem pode operar o sistema na pista.

#### 1. Interface de Gerenciamento

* **Lista de Usuários:** Uma tabela limpa contendo: Nome, E-mail, Último Acesso e a **Role Atual**.
* **Ações Rápidas:** Botões para "Redefinir Senha", "Editar" e "Desativar" (nunca deletar, para manter o histórico).

#### 2. Matriz de Permissões (Visão do Front-end)

Ao editar um usuário, o sistema deve apresentar as opções de Role. No Front-end, isso deve ser acompanhado de um "Helper Text" para não deixar dúvidas:

* **View (Observador):** * *Texto de apoio:* "Acesso apenas para leitura. Ideal para TV da fábrica ou gerência de outros setores."
* *Bloqueio:* Desabilita todos os botões de `SAVE`, `IMPORT` e `FINISH`.


* **User (Facilitadora):** * *Texto de apoio:* "Operação de pista. Pode visualizar OPs e realizar o check digital de conclusão."
* *Bloqueio:* Esconde o menu de "Engenharia de PSO" e desabilita o arraste no "Balanceamento".


* **Owner (Administrador):** * *Texto de apoio:* "Acesso total ao sistema. Configurações, planejamento e gestão de usuários."

---

### 🎨 Esboço Visual (Wireframe do Modal de Edição)

```text
__________________________________________________________
| EDITAR USUÁRIO: [ Maria Silva ]                        |
|________________________________________________________|
|                                                        |
|  NOME COMPLETO: [ Maria Silva                ]         |
|  E-MAIL:        [ maria@texcotton.com.br     ]         |
|                                                        |
|  PERFIL DE ACESSO (ROLE):                              |
|  ( ) VIEW  - Somente Visualização                      |
|  (●) USER  - Operação e Checklist                      |
|  ( ) OWNER - Gestão Total                              |
|________________________________________________________|
|                                                        |
| [ CANCELAR ]                      [ SALVAR ALTERAÇÃO ] |
|________________________________________________________|

```

### 🛠️ Lógica de Segurança para o Desenvolvedor

1. **Proteção de Rota:** O Front-end deve verificar o Token do usuário no carregamento. Se um `USER` tentar acessar a URL `/configuracoes`, o sistema deve redirecioná-lo para o Dashboard com um alerta de "Acesso Negado".
2. **Estado Global:** A `Role` do usuário deve estar disponível em todo o estado do aplicativo (ex: via Context API ou Redux).
3. **Dinamismo de Interface:** 

```javascript

// Exemplo lógico:
if (user.role !== 'OWNER') {
renderButton('IMPORTAR_PDF', { disabled: true });
}

```