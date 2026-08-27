# Site do Verbia Seridó

Site institucional da empresa, voltado para **banca, edital e investidor** —
não para venda. O site do produto continua sendo o do SIGBEF, em `site/`,
e este aqui não mexe naquele.

Uma página só, HTML e CSS, sem build e sem dependência. Abre com duplo
clique e sobe no Vercel como está.

## Rodar

Abra `index.html` no navegador. Não precisa de servidor nem de `npm install`.

## Publicar

```bash
npx vercel deploy --prod
```

Rode de dentro desta pasta. Como não há build, o Vercel serve o
`index.html` direto.

## Antes de publicar

**O nome ainda não foi verificado.** Este site existe separado do
`site/` justamente por isso: se "Verbia" colidir no INPI, esta pasta é
descartada sem tocar em nada que já está no ar.

Ordem da verificação:

1. **INPI**, classes 9 e 42 — buscar `Verbia` isolado, não o par
2. **JUCERN** — colisão de nome empresarial no RN
3. **registro.br** — `verbia.com.br` e `verbiaserido.com.br`

## O que falta preencher

A página tem uma seção marcada em vermelho tracejado, **"Preencher antes
de publicar"**. Ela está visível de propósito: são os números de impacto
que a banca procura primeiro, e eles não foram preenchidos com estimativa.

Os quatro primeiros saem do próprio SIGBEF, em **Relatórios**:

- livros catalogados
- alunos e professores cadastrados
- empréstimos registrados
- circulação antes do sistema, se houver registro
- data em que a bibliotecária começou a usar de verdade

Além disso, estão marcados com colchetes:

- os três nomes da equipe e o papel de cada um (seção "Quem faz")
- o e-mail de contato (rodapé)

Procure por `[` no `index.html` para achar todos.

## Números que já estão na página

Estes foram conferidos no repositório em 27 ago 2026 e a fonte está
citada no rodapé da seção:

| Número | De onde vem |
|---|---|
| 141 alterações | `git log --oneline \| wc -l` |
| 523 testes | `python -m unittest discover -s tests` |
| 12 versões | commits `chore(release)` no histórico |

Se for atualizar, atualize também a data da fonte na página.
