package br.rn.cefe.sigbef.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * Cores do SIGBEF, iguais às do site e do desktop.
 *
 * A fonte da verdade é `docs/DESIGN.md`; os mesmos valores vivem em
 * `sigbef/ui_tema.py` (desktop) e `site/tailwind.config.js`. Mudou aqui,
 * atualize lá — e vice-versa.
 *
 * A regra de dominância do guia vale nas telas: **navy domina (60–70%),
 * azul apoia, dourado é a única faísca.** Dourado nunca em bloco grande.
 *
 * Nenhuma tela deve escrever `Color(0xFF…)` na mão. Se faltar um tom,
 * ele nasce aqui, com nome — foi assim que uma paleta paralela do
 * scaffold (D1E4FF, 7CBAFF, 604100, 42474F) se espalhou por sete telas
 * sem nunca ter pertencido à marca.
 */

// ------------------------------------------------------------- marca
val SigbefNavy = Color(0xFF1F4E79)
val SigbefBlue = Color(0xFF2E75B6)
val SigbefGold = Color(0xFFF2A900)

// ------------------------------------------------------------- base
val SigbefBackground = Color(0xFFF5F7FA)
val SigbefSurface = Color(0xFFFFFFFF)
val SigbefSurfaceContainerLow = Color(0xFFE8ECF1)
val SigbefLine = Color(0xFFD5DAE0)

val SigbefInk = Color(0xFF1A1A1A)

/**
 * Texto secundário. Não é o `gray-400` do Tailwind de propósito: a
 * auditoria WCAG de 23/07/2026 reprovou aquele tom sobre branco (2,5:1).
 * Este passa em AA.
 */
val SigbefMuted = Color(0xFF5C6A78)

// ------------------------------------------------------------ estado
// Feedback, nunca decoração.
val SigbefSuccess = Color(0xFF2E7D32)
val SigbefWarning = Color(0xFFEF6C00)
val SigbefError = Color(0xFFC62828)

// ------------------------------------------- fundos de pílula e aviso
// Versões lavadas das cores de estado. Chapadas em vez de alpha porque
// as mesmas pílulas aparecem sobre cartão branco e sobre o fundo cinza:
// com alpha, o mesmo componente mudaria de tom conforme o lugar.
val SigbefSuccessFundo = Color(0xFFE6F2E7)
val SigbefWarningFundo = Color(0xFFFDEFE0)
val SigbefErrorFundo = Color(0xFFFBE7E7)
val SigbefBlueFundo = Color(0xFFE4EDF7)

/** Texto sobre `SigbefWarningFundo`, escuro o bastante para AA. */
val SigbefWarningInk = Color(0xFF6B3A00)
