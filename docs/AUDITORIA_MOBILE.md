# Auditoria do SIGBEF Mobile

Data: 23/07/2026. Metodo: auditoria multi-agente (5 dimensoes em paralelo:
rede, dados, telas, configuracao e erros factuais), com fase de verificacao
cetica que releu cada arquivo para confirmar ou refutar cada achado.

Numeros: 96 achados brutos, 95 confirmados, 1 refutado.
Gravidade: 6 criticos, 25 altos, 43 medios, 21 baixos.

Codigo auditado: commit 889eafa (baseline importado do Google AI Studio,
sem alteracoes).

---

# AUDITORIA DO SIGBEF MOBILE — RELATÓRIO FINAL

## 1. VEREDITO EM UMA FRASE

**(b) Demonstração autônoma com dados falsos.** O app não lê um único byte do desktop: todo o acervo, a aluna e os empréstimos vêm de uma lista escrita à mão dentro do próprio código, e a camada de rede (Retrofit, TokenManager, AuthInterceptor) é código morto — nenhum arquivo fora de `data/remote/` a referencia. A tela de conectar coleta o IP da biblioteca e joga fora. Não existe integração parcial: existe uma casca de integração que nunca foi ligada.

---

## 2. O QUE JÁ ESTÁ BOM

Não é pouco, e é justo registrar:

- **As regras visuais do produto foram respeitadas.** Não há sino de notificações, não há foto de perfil, o livro usa lombada colorida em vez de capa, o cartão usa série/turma (nunca "curso") e o TOMBO aparece na tela de detalhe. Isso é acerto de projeto, não sorte.
- **11 das 12 telas da spec existem e estão desenhadas.** Só falta a tela 6 (Reservar livro), que na prática virou a de detalhes.
- **Permissões impecáveis.** `AndroidManifest.xml` pede só `INTERNET` e `ACCESS_NETWORK_STATE`. Nenhuma permissão excessiva, sem CAMERA, sem localização, sem armazenamento.
- **`minSdk 24` / `targetSdk 36`** — faixa correta para celular modesto de aluno.
- **A paleta de marca está certa** em `app/src/main/java/com/example/ui/theme/Color.kt`: navy `1F4E79`, azul `2E75B6`, dourado `F2A900`.
- **Nenhuma chave real commitada.** O `.env.example` só tem placeholder comentado, e não existe `google-services.json` no repositório.
- **Nenhum dado real de aluno no código.** A matrícula `2026045892` e a senha `123456` são fictícias de demonstração — não há credencial verdadeira vazada.
- **A sigla CEFE nunca é expandida errado.** O problema aqui é o oposto: "Centro Educacional Felinto Elísio" não aparece em lugar nenhum do app.
- **A busca local funciona de verdade** (`Repository.searchLivros` → SQL no Room), e a tela 8 (`RenewInfoScreen.kt:97`) diz a verdade: "Para renovar, vá ao balcão da biblioteca."

---

## 3. BLOQUEADORES PARA USAR NUMA ESCOLA DE VERDADE

### 3.1 Botões que fingem agir (o mais grave)

| O quê | Arquivo |
|---|---|
| **RENOVAR LIVRO** grava `renovacaoPendente = 1` só no celular, o cartão carimba "RENOVAÇÃO SOLICITADA" e o botão vira "SOLICITADA" — **sem nenhum aviso ao aluno**. A um clique de distância, a tela 8 do mesmo app diz que renovar pelo app não existe. | `ui/screens/LoansScreen.kt:381-393` e `:345-359`; `data/local/Daos.kt:56` |
| **RESERVAR** grava a reserva local E abre um diálogo dizendo que reserva pelo app não funciona. Fechado o diálogo, fica o selo verde "RESERVADO NO SEU NOME". | `ui/screens/BookDetailScreen.kt:314-333`, `:340-360`, `:162` |
| Origem das duas: `reservarLivro` / `cancelarReserva` / `solicitarRenovacao` | `ui/SigbefViewModel.kt:107-126`; `data/Repository.kt:39-46` |

Isso viola a regra de produto 7 direto. O aluno vai ao balcão achando que tem reserva; o livro vence e vira atraso. Observação verificada: as mensagens "Reserva realizada com sucesso!" e "Solicitação enviada para a biblioteca!" **nunca aparecem na tela** — `actionNotification` não é coletado por nenhum composable. Quem engana é o selo persistente, não o toast.

Também na Home: `"Explore o acervo para reservar"` (`ui/screens/HomeScreen.kt:173`) ensina exatamente o caminho errado.

### 3.2 Dado falso apresentado como real

| O quê | Arquivo |
|---|---|
| Banco pré-povoado com 6 livros inventados, tombos falsos, 3 empréstimos e a aluna "Maria Eduarda Silva" (matrícula 2026045892, "BIBLIOTECA DO CEFE") | `data/local/SigbefDatabase.kt:50-171` |
| Fallback da tela de detalhe cai em Dom Casmurro tombo 4.821 se o acervo estiver vazio — dado compilado no APK, sobrevive a limpeza do banco | `MainActivity.kt:79`; `data/Repository.kt:61` |
| Usuária fictícia como identidade padrão de qualquer instalação, mais campos fantasma (`limMaxLivros = 3`) que não existem nem na entidade nem no DTO e são exibidos ao aluno | `data/Repository.kt:53-59`; `model/Models.kt:3-12`; `ui/screens/HomeScreen.kt:200,212` |
| Aviso `"1 vence em 3 dias"` é string fixa, sem nenhum cálculo de data | `ui/screens/HomeScreen.kt:165` |
| Código de barras do cartão é desenho pseudo-aleatório, sem simbologia — nenhum leitor decodifica (atenuante: a matrícula está impressa legível logo abaixo) | `ui/components/BarcodeView.kt:45-59` |
| Chip "Online" é toggle manual que abre marcado como conectado; a Home escreve "Conectado à BIBLIOTECA DO CEFE" com bolinha verde sem nunca ter feito uma requisição | `MainActivity.kt:164-198`; `ui/SigbefViewModel.kt:28,90-92`; `ui/screens/HomeScreen.kt:276` |
| Banner offline mente: "mostrando última consulta" — nunca houve consulta | `ui/components/NavigationComponents.kt:124` |
| Empréstimo marcado `atrasado = true` com devolução em 10/10/2026 (hoje é 23/07/2026); item do histórico "devolvido" em setembro de 2026 | `data/local/SigbefDatabase.kt:137-155` |
| Defaults do Dom Casmurro (tombo `4.821`, ISBN, sinopse) no modelo de domínio — armadilha latente, dispara no dia da integração | `model/Models.kt:19-22` |

### 3.3 Login de fachada

`ui/screens/LoginScreen.kt:50-51` traz matrícula e senha pré-preenchidas; a linha 174 é `onClick = { onLoginSuccess() }` — nenhuma validação, nenhuma rede, a matrícula digitada é descartada. E a linha 209 promete "Use a mesma matrícula e senha do sistema da biblioteca", o que faz o aluno acreditar que houve validação. Não é login com bug, é botão de avançar disfarçado.

### 3.4 Camada de rede: ficção completa

- `data/remote/RetrofitClient.kt:13` — base URL `https://sigbef-api.cefe.edu.br/`, domínio que contradiz a arquitetura documentada (API local, HTTP, porta 8765). *Não resolvi o DNS: a conclusão de que é inventado vem da contradição com `docs/API.md`, não de consulta.*
- `data/remote/SigbefApiService.kt` — **nenhuma** das 8 rotas existe. Os 4 GETs usam caminhos inventados (`api/v1/acervo/livros`, `api/v1/aluno/perfil`, `api/v1/emprestimos` sem matrícula); os 4 POSTs (login, reservar, cancelar-reserva, renovar) baterão em `405 — Esta API é somente leitura` (`sigbef/api.py:163-166`).
- `data/remote/ApiModels.kt` — DTOs não batem com o JSON real: falta o envelope `{total, livros}`, `autores` é lista no desktop e String no app, e o `tombo` no desktop está dentro de `exemplares[].numero_tombo`, não no livro.
- `AndroidManifest.xml` — sem `networkSecurityConfig`; com `targetSdk 36`, cleartext HTTP é bloqueado por padrão. No dia em que a URL for corrigida para `http://IP:8765`, toda chamada falha.
- **Isolamento entre alunos:** o token da API é estático e de sistema. Distribuir esse token no APK de cada aluno dá a qualquer um acesso aos empréstimos de qualquer matrícula. Já está registrado como bloqueador na própria spec (`docs/SIGBEF_MOBILE.md:132-136`).

### 3.5 Violação da regra 6 (nada de nuvem) — de configuração, não de tráfego

`app/build.gradle.kts` linhas 9, 75, 98, 109: plugin `google-services`, `firebase-bom`, `firebase-ai`, `firebase-appcheck-recaptcha`. `metadata.json` declara `MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API`. `AndroidManifest.xml:9` tem `allowBackup="true"` com `backup_rules.xml` e `data_extraction_rules.xml` inteiramente comentados. O `README.md` é o boilerplate do AI Studio, com banner do Google e instrução para criar chave Gemini.

**Ressalva honesta:** nada disso gera tráfego hoje. Não existe `google-services.json`, o build usa `missingGoogleServicesStrategy = WARN`, e `grep -i firebase|gemini` em todo `app/src` retorna zero linhas de Kotlin. O Firebase nunca inicializa. É peso morto e contradição de discurso — a `ConnectScreen.kt:197` exibe ao aluno "Seus dados ficam na escola. Nada vai para a internet." — não exfiltração em curso.

### 3.6 O projeto não gera APK

- Não existe `debug.keystore` nem `.jks` no `rootDir`, mas `build.gradle.kts:34-39,49` obriga o `debugConfig`. `assembleDebug` falha em `validateSigningDebug`. Correção: uma linha (o próprio README a documenta).
- **Não existe Gradle wrapper** (`gradlew`, `gradlew.bat`, `gradle/wrapper/`). Não consegui executar o build para confirmar nada disso na prática — as conclusões vêm de leitura do DSL.
- Source set de teste **não compila**: `app/src/test/java/com/example/GreetingScreenshotTest.kt:24` chama `Greeting("Robolectric")`, função que não existe em lugar nenhum. `ExampleRobolectricTest.kt:19` espera `"My Application"` enquanto `strings.xml` diz `SIGBEF`.
- **Não consegui determinar** se AGP 9.1.1 é compatível com o Compose BOM 2024.09.00 e o Kotlin 2.2.10 declarados — isso exige rodar o build.

### 3.7 Repositório

`git ls-files sigbef-mobile/` retorna vazio: o app inteiro está untracked. Pior, o `.gitignore` da raiz tem a regra `data/` (escrita para o SQLite do desktop em Python) e ela **silenciosamente exclui do commit o pacote `data/` do Android**, confirmado por `git check-ignore -v`. Se você commitar hoje, perde Room, DAOs e Repository sem perceber.

### 3.8 Defeitos menores de tela (não bloqueiam, mas o aluno vê)

- Chips **"Didáticos"** e **"HQ"** nunca retornam nada — nenhuma categoria semeada casa com eles, e a tela ainda sugere "verifique a ortografia", culpando o aluno (`ui/screens/AcervoScreen.kt:80`).
- Campo de busca **desabilitado no modo offline**, embora 100% dos dados venham do Room local (`AcervoScreen.kt:170`).
- Livro **EMPRESTADO exibido com CheckCircle verde**, e a previsão de devolução não aparece no detalhe (`BookDetailScreen.kt:153-169`).
- **"VER SIMILARES"** só volta ao acervo; **"Ver todo o histórico"** tem lambda vazia.
- `applicationId = "com.aistudio.sigbef.mobile"` e `namespace = "com.example"` — trocar depois de distribuir obriga reinstalação manual em todos os aparelhos.
- `"Matemática (Gelson Iezzi)"` renderiza como "Matemática (Gelson Iezzi) (Gelson Iezzi)" no histórico.
- `"Graphic Novel"` em inglês na tela de um aluno de escola pública. (As demais categorias — "Ciências Exatas", "Tecnologia" — **não** violam regra nenhuma: o desktop usa categoria como texto livre, conferido em `sigbef/seed.py`.)

---

## 4. O QUE FALTA PARA INTEGRAR DE FATO, EM ORDEM DE EXECUÇÃO

**Passo 0 — Parar de mentir (antes de qualquer código de rede).**
Remover os botões RESERVAR / CANCELAR RESERVA / RENOVAR LIVRO, os campos `reservadoPeloUsuario` e `renovacaoPendente`, e os selos correspondentes. Substituir por texto: "Para reservar/renovar, procure o balcão." Trocar `"Explore o acervo para reservar"` na Home.

**Passo 1 — Apagar os dados falsos.**
Remover `initialLivros`, `initialEmprestimos`, `prepopulateDatabase`, o `addCallback`, `sampleLivros`, `sampleEmprestimos`, `defaultUsuario` e todos os defaults de `Models.kt`. Telas passam a mostrar estado vazio honesto. Subir a versão do schema com migração destrutiva, para que aparelhos que já rodaram esta build percam os 6 livros e a aluna falsos.

**Passo 2 — Limpar o scaffold do AI Studio.**
Tirar Firebase/Gemini/AppCheck, plugin `google-services`, blocos `secrets{}`/`googleServices{}`, `.env.example`, `MAJOR_CAPABILITY_SERVER_SIDE_GEMINI_API` do `metadata.json`, e reescrever o README em português. Definir `allowBackup="false"`. Fixar `applicationId`/`namespace` definitivos **agora**.

**Passo 3 — Fazer o projeto compilar.**
Remover a linha `signingConfig = signingConfigs.getByName("debugConfig")`, gerar e commitar o Gradle wrapper, apagar os três testes de template. Acrescentar `*.jks`, `*.keystore` e `google-services.json` ao `.gitignore`, corrigir a regra `data/` para `/sigbef/data/`, e fazer o commit inicial do app.

**Passo 4 — Ligar a rede de verdade.**
1. `ConnectScreen` deixa de descartar o endereço: `MainActivity` recebe o `String`, persiste, e o Repository o usa.
2. Remover `DEFAULT_BASE_URL`; `getApiService` passa a exigir `baseUrl` obrigatório, validado como endereço de rede local.
3. Criar `res/xml/network_security_config.xml` permitindo cleartext só para a faixa local e referenciar no manifesto.
4. Reescrever `SigbefApiService` com as rotas reais: `GET api/v1/ping`, `api/v1/livros?q=&disponiveis=`, `api/v1/livros/{id}`, `api/v1/usuarios/{matricula}/emprestimos`. Apagar os 4 POSTs e o `getPerfil`.
5. Reescrever os DTOs a partir do payload real (envelope, `autores` como lista, `exemplares[].numero_tombo`). `spineColorHex` deriva de hash local, nunca da API.
6. Injetar o cliente no `SigbefRepository`, gravar no Room como cache, expor data/hora da última sincronização.
7. `isOffline` passa a vir de `ConnectivityManager` + `GET /api/v1/ping`. Remover o chip manual da build de produção.
8. `HttpLoggingInterceptor` condicionado a `BuildConfig.DEBUG` + `redactHeader("Authorization")` — **antes** de a primeira requisição existir.

**Passo 5 — Derivar o que hoje é chumbado.**
Parsear `dataDevolucao` (dd/MM/yyyy), calcular `atrasado` e o aviso de vencimento com números reais. Unificar chips de filtro com as categorias que o acervo realmente devolve.

**Passo 6 — Depende do desktop, não do app.**
- **R1 (pareamento por QR):** o desktop precisa exibir um QR com endereço + porta + token. Só então faz sentido implementar CameraX/ML Kit e pedir `CAMERA`. Enquanto isso, esconder o botão "Escanear QR code" e deixar só entrada manual.
- **R2 (identidade por aluno):** hoje o token é estático e de sistema, sem vínculo com matrícula. Sem R2 no desktop, **não existe login possível** — ou o app entra direto no modo consulta com o token de CONSULTA (que recebe 403 nas rotas de leitores), ou não há tela de login. Não dá para resolver no app.
- **R3 (API de escrita):** reserva e renovação online exigem POST no desktop, o que hoje contraria a regra de produto 7. Decisão de produto, não de código.
- **R4 (sinopse):** o banco do desktop não tem esse campo. Enquanto não tiver, omitir a seção Sinopse.

---

## 5. ESFORÇO ESTIMADO

### Minutos a poucas horas (baixo) — dá para fazer hoje

| Bloco | Esforço |
|---|---|
| Remover Firebase/Gemini/AppCheck + `metadata.json` + README | baixo |
| `allowBackup="false"` | minutos |
| Remover a linha `debugConfig` | 1 linha |
| Esvaziar campos do login e tirar o texto que promete validação | minutos |
| Remover IPs chumbados (`ConnectScreen.kt:53,142`) e `DEFAULT_BASE_URL` | minutos |
| Remover "VER SIMILARES", "Ver todo o histórico", chip Online | minutos |
| Apagar os 3 testes de template e as cores roxas do `colors.xml` | minutos |
| Corrigir chips / `"Graphic Novel"` → `"HQ"` / autores no formato natural | baixo |
| Guardar o logging interceptor com `BuildConfig.DEBUG` | minutos |
| `networkSecurityConfig` | baixo |
| Corrigir `.gitignore` e commitar o app | baixo |
| Buscar sempre habilitada offline; EMPRESTADO em cinza + previsão de devolução | baixo |

### Meio dia a alguns dias (médio)

| Bloco | Esforço |
|---|---|
| Remover reserva/renovação ponta a ponta (ViewModel → Repository → DAO → entidades → 2 telas) | médio |
| Remover o seed e implementar estados vazios em todas as telas | médio |
| Trocar `namespace`/`applicationId` e mover o pacote (inclui test/androidTest) | médio |
| Gerar wrapper e fazer o build passar de fato | médio, com incerteza — não consegui executar o Gradle |
| Reescrever DTOs contra o JSON real e propagar o endereço da ConnectScreen até o Retrofit | médio |
| Cálculo de atraso e vencimento a partir de datas | médio |
| Código de barras: gerar simbologia real ou assumir só a matrícula em texto | médio |

### Alto — e boa parte não é trabalho de app

| Bloco | Esforço | Observação |
|---|---|---|
| Sincronização real: Repository → API → Room como cache, com erro e "última sincronização" visíveis | alto | é o coração da integração |
| Leitor de QR (CameraX + permissão + tratamento de negação) | alto | **bloqueado por R1 no desktop** |
| Identidade por aluno | alto | **bloqueado por R2 no desktop.** Enquanto o token for estático e de sistema, distribuí-lo no APK de cada aluno é problema de arquitetura, com ou sem criptografia |
| Reserva/renovação online | alto | **bloqueado por R3 e por decisão de produto** (a regra 7 diz que isso é do balcão) |

---

## O QUE NÃO CONSEGUI DETERMINAR

Sendo explícito, para você não tomar decisão em cima de suposição minha:

1. **Se o projeto compila.** Não há Gradle wrapper e não executei build nenhum. Tudo sobre falha de assinatura e de compilação dos testes vem de leitura do DSL e de `grep`.
2. **Se o domínio `sigbef-api.cefe.edu.br` existe ou a quem pertence.** Não resolvi o DNS. A conclusão de que é inventado vem da contradição com a arquitetura documentada.
3. **Compatibilidade entre AGP 9.1.1, Kotlin 2.2.10 e Compose BOM 2024.09.00.** Só um build responde.
4. **Comportamento em aparelho real** — bloqueio de cleartext, Auto Backup, splash. Nada foi verificado em dispositivo.
5. **A inferência de que o app nunca foi executado contra a API real** é plausível e coerente com tudo o mais, mas continua sendo inferência.
