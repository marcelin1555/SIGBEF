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

O desktop é a fonte da verdade. O aplicativo só lê.

### Primeiro uso

1. A bibliotecária abre **Configurações → Integrações → Parear celular** no
   SIGBEF desktop, que mostra um QR code com o endereço do servidor.
2. O aluno escaneia (ou digita o endereço) e entra com a **mesma matrícula
   e senha** do sistema da biblioteca.
3. Pronto. O cartão digital continua funcionando mesmo sem rede.

O QR code **não contém senha nem token** de propósito: ele fica exposto na
tela do computador, e quem o fotografasse ganharia acesso indevido. Cada
aluno recebe um acesso próprio ao entrar, que só enxerga os dados dele.

## O que o aplicativo faz

- Consultar o acervo (busca por título, autor ou categoria)
- Ver os próprios empréstimos, prazos e atrasos
- Cartão de biblioteca digital, com código de barras, disponível offline
- Modo offline com a última consulta em cache

## O que ele **não** faz

Emprestar, devolver, renovar e reservar são operações de **balcão**. A API
da biblioteca é somente leitura, então o aplicativo não oferece esses
botões: prometer uma ação que a bibliotecária nunca receberia seria pior
que não ter a função.

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
