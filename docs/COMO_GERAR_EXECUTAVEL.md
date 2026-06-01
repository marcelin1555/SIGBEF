# Como gerar o executável do SIGBEF

Há **três opções**, do mais simples ao mais profissional.

---

## Opção 1 — Pasta autônoma (mais rápido) [⏱ 3 min]

Gera uma pasta `dist/SIGBEF/` que pode ser copiada para qualquer
computador Windows e executada com duplo-clique.

### Passos

1. Garanta que o **Python 3.10+** está instalado e marcado em "Add to PATH".
2. Abra a pasta do projeto e dê **duplo-clique** em `build.bat`.
3. Aguarde alguns minutos. O executável final aparece em:

   ```
   dist\SIGBEF\SIGBEF.exe
   ```

4. **Para usar na biblioteca:** copie a pasta inteira `dist\SIGBEF\` para
   um pendrive ou rede e cole no computador da biblioteca. Dê duplo-clique
   em `SIGBEF.exe` para abrir.

> O banco de dados é criado automaticamente em
> `%APPDATA%\SIGBEF\sigbef.db` na primeira execução, com os dados de
> demonstração.

---

## Opção 2 — Instalador profissional .exe [⏱ 10 min]

Gera um instalador único `SIGBEF_Setup.exe` que cria atalhos no menu
Iniciar e na área de trabalho, com opção de desinstalação.

### Passos

1. Faça a Opção 1 primeiro (gerar `dist/SIGBEF/`).
2. Baixe o **Inno Setup**: <https://jrsoftware.org/isinfo.php>
3. Abra o arquivo `tools\sigbef_installer.iss` no Inno Setup Compiler.
4. Pressione **F9** (Compile).
5. O instalador é gerado em `Output\SIGBEF_Setup_v1.2.0.exe`.

### O que o instalador faz

- Pergunta o idioma (português brasileiro disponível)
- Mostra a licença MIT
- Permite escolher onde instalar
- Cria atalho no menu Iniciar
- Pergunta se quer atalho na área de trabalho
- Pergunta se quer um atalho separado para o **Modo Autoatendimento**
- Permite desinstalar pelo Painel de Controle

---

## Opção 3 — Modo kiosk no terminal de autoatendimento

Para o computador dedicado ao autoatendimento (com tela touchscreen):

1. Instale o SIGBEF (Opção 2)
2. Use o atalho "SIGBEF (Autoatendimento)" — abre direto no kiosk
3. *(Opcional)* Configure o atalho para iniciar com o Windows:
   - Pressione `Win + R` e digite `shell:startup`
   - Copie o atalho do Autoatendimento para essa pasta
   - O sistema abrirá automaticamente quando o computador ligar

---

## Solução de problemas

### "Python não encontrado"
Reinstale o Python marcando "Add python.exe to PATH" durante a instalação.

### Build é muito lento ou trava
O PyInstaller pode demorar 3-5 minutos na primeira vez. Antivírus pode
bloquear — adicione exceção para a pasta do projeto.

### O executável fica grande (~30 MB)
Normal — o PyInstaller embarca o interpretador Python inteiro. Para
reduzir, configure o `excludes` em `sigbef.spec`.

### Antivírus marca o .exe como suspeito
Comum com PyInstaller. Para uso institucional, considere assinar
digitalmente o executável (requer certificado de Code Signing).

### Quero um arquivo .msi para deploy via GPO
Use uma ferramenta como **MSIX Packaging Tool** ou **Advanced Installer**
em cima do `dist\SIGBEF\` gerado pela Opção 1.

---

## Atualizando o sistema

Quando você modificar o código:

1. Rode `build.bat` novamente
2. Distribua a nova pasta `dist\SIGBEF\` (ou gere novo instalador)
3. **Os dados não são perdidos** — eles ficam em `%APPDATA%\SIGBEF\`

Para fazer **backup do banco**:
```
%APPDATA%\SIGBEF\sigbef.db
```

Basta copiar esse arquivo. Para restaurar, sobrescreva-o.
