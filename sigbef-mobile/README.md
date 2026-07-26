# SIGBEF Mobile

Aplicativo Android para **alunos e professores** consultarem o acervo da
biblioteca da escola, acompanharem os próprios empréstimos e usarem o
cartão de biblioteca digital.

Faz parte do [SIGBEF](../README.md), sistema gratuito e de código aberto de
gestão de biblioteca escolar, em produção no CEFE (Jardim do Seridó/RN).

## Como funciona

O aplicativo **não tem servidor próprio e não usa nuvem**. Ele conversa
apenas com o SIGBEF desktop, que roda no computador da biblioteca, pela
rede local (Wi-Fi) da escola:

```
[celular do aluno]  ──── Wi-Fi da escola ────►  [computador da biblioteca]
   SIGBEF Mobile                                    SIGBEF desktop
   cache local (Room)                               API REST :8765
                                                    banco SQLite
```

O desktop é a fonte da verdade. O acervo o aplicativo só lê; as únicas
coisas que ele grava são as do próprio aluno — reserva, cancelamento de
reserva e renovação —, e cada uma passa pelas regras da biblioteca antes
de valer.

> **A rede da escola não pode ter isolamento de clientes.** Esse recurso
> ("AP isolation", "modo visitante") impede que dois aparelhos do mesmo
> Wi-Fi se enxerguem, e o app nunca acha a biblioteca — com a mensagem
> enganosa de endereço errado. Ver [SIGBEF_MOBILE.md §7](../docs/SIGBEF_MOBILE.md).

### Primeiro uso

1. A bibliotecária abre **Configurações → Integrações → Parear celular** no
   SIGBEF desktop, que mostra um QR code com o endereço do servidor.
2. O aluno aponta a câmera para o QR (ou digita o endereço, se preferir) e
   entra com a **mesma matrícula e senha** do sistema da biblioteca.
3. Pronto. O cartão digital continua funcionando mesmo sem rede.

O QR code **não contém senha nem token** de propósito: ele fica exposto na
tela do computador, e quem o fotografasse ganharia acesso indevido. Cada
aluno recebe um acesso próprio ao entrar, que só enxerga os dados dele.

## O que o aplicativo faz

- Consultar o acervo (busca por título, autor, ISBN ou tombo)
- Ver os próprios empréstimos, prazos, atrasos e o histórico de leituras
- **Renovar** um empréstimo, quando as regras da biblioteca permitem
- **Entrar na fila de espera** de um livro emprestado, e sair dela
- Cartão de biblioteca digital, com código de barras real, lido pelo
  mesmo leitor do balcão — funciona offline
- "Minha leitura": quanto o aluno já leu e sugestões de próximos livros
- Pareamento com a biblioteca lendo um QR code pela câmera

## O que ele **não** faz

**Emprestar e devolver**, que são operações de balcão: exigem o livro na
mão, e nenhum aplicativo resolve isso.

A renovação tem regras, e quem decide é a biblioteca, não o app: livro
atrasado não renova, livro com alguém na fila de espera não renova, e há
um limite de renovações seguidas. Quando o botão não aparece, no lugar
dele vem a frase que explica o porquê — escrita pelo servidor.

## Desenvolvimento

**Requisitos:** Android Studio, JDK 17, SDK Android (minSdk 24).

```bash
./gradlew assembleDebug      # gera app/build/outputs/apk/debug/
```

- **Linguagem:** Kotlin · **Interface:** Jetpack Compose (Material 3)
- **Arquitetura:** MVVM, com Room como cache local e Retrofit para a API
- **Identidade visual:** ver [docs/DESIGN.md](../docs/DESIGN.md)
- **Especificação:** ver [docs/SIGBEF_MOBILE.md](../docs/SIGBEF_MOBILE.md)

### Histórico

A primeira versão foi gerada no Google AI Studio e funcionava como
demonstração autônoma, com acervo e usuária fictícios embutidos no código.
A auditoria em [docs/AUDITORIA_MOBILE.md](../docs/AUDITORIA_MOBILE.md)
registra o que foi encontrado e corrigido.
