# Como gerar o APK do SIGBEF Mobile

Guia para publicar o aplicativo do aluno. O equivalente deste documento
para o desktop é `COMO_GERAR_EXECUTAVEL.md`.

O app **não vai para a Play Store**: a escola distribui o APK
diretamente (site, QR code, Bluetooth, cabo). Isso evita conta de
desenvolvedor paga e revisão da loja — mas obriga a assinar o APK por
conta própria, que é o assunto deste guia.

---

## 1. Por que assinar

O Android recusa instalar um APK sem assinatura. Além disso, a
assinatura é o que permite **atualizar** o app depois: o sistema só
aceita uma atualização assinada com a mesma chave da versão instalada.

> **A chave não se recupera e não se revoga.** Se você perder o arquivo
> ou a senha, não existe recuperação: será preciso gerar outra chave,
> e todo aluno terá que **desinstalar** o app e instalar de novo do
> zero. Guarde o `.jks` e as senhas em lugar seguro — de preferência
> em dois lugares, fora do computador da biblioteca.

---

## 2. Gerar a chave (uma vez só, na vida do projeto)

Precisa do `keytool`, que vem com o Java. No computador do Marcello ele
está em:

```
C:\Program Files\Eclipse Adoptium\jdk-17.0.14.7-hotspot\bin\keytool.exe
```

Rode, escolhendo **onde salvar fora do repositório** (a pasta do projeto
está protegida pelo `.gitignore`, mas o mais seguro é nem colocar lá):

```bash
keytool -genkeypair -v -keystore sigbef-release.jks -alias upload -keyalg RSA -keysize 4096 -validity 10000
```

O comando pergunta:

| Pergunta | O que responder |
|---|---|
| Senha do keystore | Escolha uma e **anote** |
| Nome e sobrenome (CN) | `SIGBEF` |
| Unidade organizacional | `Biblioteca` |
| Organização | Nome da escola |
| Cidade / Estado / País | `Jardim do Seridó` / `RN` / `BR` |
| Senha da chave | Pode ser a mesma do keystore |

`-validity 10000` são ~27 anos: o app precisa continuar atualizável
por muito tempo, e renovar chave de app distribuído fora de loja é
trabalhoso.

---

## 3. Gerar o APK assinado

O build lê a chave e as senhas do ambiente — elas **nunca** entram no
código nem em arquivo versionado.

```bash
export KEYSTORE_PATH=/caminho/para/sigbef-release.jks
export STORE_PASSWORD='sua-senha-do-keystore'
export KEY_PASSWORD='sua-senha-da-chave'
cd sigbef-mobile && ./gradlew assembleRelease
```

No PowerShell, as três primeiras linhas viram:

```
$env:KEYSTORE_PATH = "C:\caminho\para\sigbef-release.jks"
$env:STORE_PASSWORD = "sua-senha-do-keystore"
$env:KEY_PASSWORD   = "sua-senha-da-chave"
```

Se você usou um alias diferente de `upload`, defina também
`KEY_ALIAS`.

Sem a chave no caminho indicado, o build **não falha**: ele gera um APK
sem assinatura, útil para testar. Se a chave existir mas as senhas
faltarem, aí sim ele para e diz o que está faltando.

---

## 4. Qual arquivo entregar

O build gera um APK **por arquitetura**, porque o leitor de QR carrega
um motor nativo de ~5 MB para cada uma. Os arquivos saem em
`sigbef-mobile/app/build/outputs/apk/release/`:

| Arquivo | Quando usar |
|---|---|
| `app-arm64-v8a-release.apk` | **Quase todo celular atual.** É o que distribuir por padrão (~20 MB) |
| `app-armeabi-v7a-release.apk` | Aparelhos antigos, 32 bits (~18 MB) |
| `app-universal-release.apk` | Quando não dá para saber o aparelho — passar por cabo, WhatsApp, pendrive (~35 MB) |
| `app-x86*-release.apk` | Só emulador. Não distribuir |

Na dúvida, entregue o **universal**: pesa mais, mas instala em qualquer
aparelho e evita o aluno baixar o arquivo errado.

Para conferir se saiu assinado:

```bash
apksigner verify --print-certs app-arm64-v8a-release.apk
```

---

## 5. Antes de distribuir, confira a rede da escola

O app depende de o celular enxergar o computador da biblioteca no Wi-Fi.
Redes com **isolamento de clientes** ligado impedem isso, e o sintoma
parece defeito do app ("Não encontrei a biblioteca nesse endereço", com
o endereço certo). Ver `SIGBEF_MOBILE.md` §7 para reconhecer e resolver.

---

## 6. Atualizações

Ao publicar uma versão nova, suba `versionCode` (número inteiro, sempre
maior que o anterior) e `versionName` (o que o usuário lê) em
`sigbef-mobile/app/build.gradle.kts`. O Android recusa instalar por cima
uma versão com `versionCode` igual ou menor.

Assine sempre com **a mesma chave**. Chave diferente = o Android trata
como outro app, e a instalação por cima falha.
