"""
SIGBEF — Geração de QR Code em Python puro.

Gera QR Codes **reais** (escaneáveis por qualquer celular), sem dependência
externa, no mesmo espírito do `barcode_util.py` (que implementa Code 128).

Usado no pareamento do aplicativo móvel: a bibliotecária abre a tela de
Integrações, o aluno aponta a câmera e o app já sabe o endereço do servidor
e recebe o código de pareamento.

Escopo deliberadamente reduzido ao necessário:
  - Modo byte (8 bits), suficiente para URLs.
  - Nível de correção de erro M (recupera ~15%), bom para tela.
  - Versões 2 a 10 (até 271 bytes), escolhidas automaticamente.

Renderiza em canvas Tk (tela) e em SVG (impressão/documentação).
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Tabelas do padrão ISO/IEC 18004
# ---------------------------------------------------------------------------

# Capacidade em bytes (modo byte, nível M), índice = versão
_CAPACIDADE_M = {
    1: 14, 2: 26, 3: 42, 4: 62, 5: 84, 6: 106, 7: 122, 8: 152, 9: 180,
    10: 213,
}

# (total de codewords, codewords de dados, nº de blocos do grupo 1,
#  codewords de dados por bloco g1, nº blocos g2, codewords dados por bloco g2)
_BLOCOS_M = {
    1: (26, 16, 1, 16, 0, 0),
    2: (44, 28, 1, 28, 0, 0),
    3: (70, 44, 1, 44, 0, 0),
    4: (100, 64, 2, 32, 0, 0),
    5: (134, 86, 2, 43, 0, 0),
    6: (172, 108, 4, 27, 0, 0),
    7: (196, 124, 4, 31, 0, 0),
    8: (242, 154, 2, 38, 2, 39),
    9: (292, 182, 3, 36, 2, 37),
    10: (346, 216, 4, 43, 1, 44),
}

# Posições centrais dos padrões de alinhamento, por versão
# (a versão 1 não tem nenhum)
_ALINHAMENTO = {
    1: [],
    2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
    7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50],
}

# Informação de formato (nível M + máscara 0..7), 15 bits já com BCH
_FORMATO_M = [
    0x5412, 0x5125, 0x5E7C, 0x5B4B, 0x45F9, 0x40CE, 0x4F97, 0x4AA0,
]


# ---------------------------------------------------------------------------
# Aritmética em GF(256) para Reed-Solomon
# ---------------------------------------------------------------------------
_EXP = [0] * 512
_LOG = [0] * 256


def _init_galois() -> None:
    x = 1
    for i in range(255):
        _EXP[i] = x
        _LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D  # polinômio primitivo do QR
    for i in range(255, 512):
        _EXP[i] = _EXP[i - 255]


_init_galois()


def _mult(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def _polinomio_gerador(grau: int) -> list[int]:
    """Polinômio gerador de Reed-Solomon para `grau` codewords de correção."""
    poli = [1]
    for i in range(grau):
        novo = [0] * (len(poli) + 1)
        for j, coef in enumerate(poli):
            novo[j] ^= coef
            novo[j + 1] ^= _mult(coef, _EXP[i])
        poli = novo
    return poli


def _correcao_erro(dados: list[int], qtd: int) -> list[int]:
    """Calcula os codewords de correção de erro de um bloco."""
    gerador = _polinomio_gerador(qtd)
    resto = list(dados) + [0] * qtd
    for i in range(len(dados)):
        coef = resto[i]
        if coef:
            for j, g in enumerate(gerador):
                resto[i + j] ^= _mult(g, coef)
    return resto[len(dados):]


# ---------------------------------------------------------------------------
# Montagem dos dados
# ---------------------------------------------------------------------------
def _escolher_versao(qtd_bytes: int) -> int:
    for versao in sorted(_CAPACIDADE_M):
        if qtd_bytes <= _CAPACIDADE_M[versao]:
            return versao
    raise ValueError(
        f"Texto longo demais para QR nível M ({qtd_bytes} bytes; "
        f"máximo {_CAPACIDADE_M[max(_CAPACIDADE_M)]})."
    )


def _bits_de_dados(texto: str, versao: int) -> list[int]:
    """Sequência de bits: modo + tamanho + dados + terminador + preenchimento."""
    dados = texto.encode("utf-8")
    total_cw = _BLOCOS_M[versao][1]
    bits: list[int] = []

    # Modo byte = 0100
    for b in (0, 1, 0, 0):
        bits.append(b)
    # Contador de caracteres: 8 bits para versões 1..9, 16 para 10+
    largura = 8 if versao < 10 else 16
    for i in range(largura - 1, -1, -1):
        bits.append((len(dados) >> i) & 1)
    # Dados
    for byte in dados:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)

    # Terminador (até 4 zeros)
    capacidade_bits = total_cw * 8
    for _ in range(min(4, capacidade_bits - len(bits))):
        bits.append(0)
    # Completa o último byte
    while len(bits) % 8:
        bits.append(0)
    # Preenchimento alternado 0xEC / 0x11
    preenchimento = (0xEC, 0x11)
    idx = 0
    while len(bits) < capacidade_bits:
        for i in range(7, -1, -1):
            bits.append((preenchimento[idx % 2] >> i) & 1)
        idx += 1
    return bits


def _codewords_finais(texto: str, versao: int) -> list[int]:
    """Aplica blocos e Reed-Solomon, devolvendo os codewords intercalados."""
    bits = _bits_de_dados(texto, versao)
    dados = [int("".join(str(b) for b in bits[i:i + 8]), 2)
             for i in range(0, len(bits), 8)]

    total_cw, dados_cw, g1, cw_g1, g2, cw_g2 = _BLOCOS_M[versao]
    blocos: list[list[int]] = []
    pos = 0
    for _ in range(g1):
        blocos.append(dados[pos:pos + cw_g1])
        pos += cw_g1
    for _ in range(g2):
        blocos.append(dados[pos:pos + cw_g2])
        pos += cw_g2

    qtd_correcao = (total_cw - dados_cw) // (g1 + g2)
    blocos_ec = [_correcao_erro(b, qtd_correcao) for b in blocos]

    # Intercala os codewords de dados e depois os de correção
    saida: list[int] = []
    for i in range(max(len(b) for b in blocos)):
        for bloco in blocos:
            if i < len(bloco):
                saida.append(bloco[i])
    for i in range(qtd_correcao):
        for bloco in blocos_ec:
            saida.append(bloco[i])
    return saida


# ---------------------------------------------------------------------------
# Matriz
# ---------------------------------------------------------------------------
def _nova_matriz(tamanho: int):
    """Matriz de módulos e matriz de 'reservado' (padrões fixos)."""
    return ([[0] * tamanho for _ in range(tamanho)],
            [[False] * tamanho for _ in range(tamanho)])


def _por_localizador(m, res, linha: int, col: int) -> None:
    """Desenha um localizador 7x7 e sua separação."""
    for dl in range(-1, 8):
        for dc in range(-1, 8):
            l, c = linha + dl, col + dc
            if not (0 <= l < len(m) and 0 <= c < len(m)):
                continue
            borda = dl in (0, 6) and 0 <= dc <= 6
            lateral = dc in (0, 6) and 0 <= dl <= 6
            miolo = 2 <= dl <= 4 and 2 <= dc <= 4
            m[l][c] = 1 if (borda or lateral or miolo) else 0
            res[l][c] = True


def _padroes_fixos(m, res, versao: int) -> None:
    tam = len(m)
    _por_localizador(m, res, 0, 0)
    _por_localizador(m, res, 0, tam - 7)
    _por_localizador(m, res, tam - 7, 0)

    # Temporizadores
    for i in range(8, tam - 8):
        v = 1 if i % 2 == 0 else 0
        m[6][i] = v
        res[6][i] = True
        m[i][6] = v
        res[i][6] = True

    # Alinhamento
    centros = _ALINHAMENTO[versao]
    for lc in centros:
        for cc in centros:
            # não sobrepõe os localizadores
            if (lc, cc) in ((6, 6), (6, centros[-1]), (centros[-1], 6)):
                continue
            for dl in range(-2, 3):
                for dc in range(-2, 3):
                    l, c = lc + dl, cc + dc
                    borda = max(abs(dl), abs(dc)) == 2
                    centro = dl == 0 and dc == 0
                    m[l][c] = 1 if (borda or centro) else 0
                    res[l][c] = True

    # Módulo escuro fixo
    m[tam - 8][8] = 1
    res[tam - 8][8] = True

    # Reserva área da informação de formato
    for i in range(9):
        if not res[8][i]:
            res[8][i] = True
        if not res[i][8]:
            res[i][8] = True
    for i in range(8):
        res[8][tam - 1 - i] = True
        res[tam - 1 - i][8] = True


def _preencher_dados(m, res, codewords: list[int]) -> None:
    """Percorre em ziguezague da direita para a esquerda, de baixo para cima."""
    tam = len(m)
    bits = []
    for cw in codewords:
        for i in range(7, -1, -1):
            bits.append((cw >> i) & 1)

    idx = 0
    col = tam - 1
    subindo = True
    while col > 0:
        if col == 6:  # coluna do temporizador é pulada
            col -= 1
        linhas = range(tam - 1, -1, -1) if subindo else range(tam)
        for linha in linhas:
            for dc in (0, 1):
                c = col - dc
                if res[linha][c]:
                    continue
                m[linha][c] = bits[idx] if idx < len(bits) else 0
                idx += 1
        col -= 2
        subindo = not subindo


def _mascara(padrao: int, linha: int, col: int) -> bool:
    if padrao == 0:
        return (linha + col) % 2 == 0
    if padrao == 1:
        return linha % 2 == 0
    if padrao == 2:
        return col % 3 == 0
    if padrao == 3:
        return (linha + col) % 3 == 0
    if padrao == 4:
        return (linha // 2 + col // 3) % 2 == 0
    if padrao == 5:
        return (linha * col) % 2 + (linha * col) % 3 == 0
    if padrao == 6:
        return ((linha * col) % 2 + (linha * col) % 3) % 2 == 0
    return ((linha + col) % 2 + (linha * col) % 3) % 2 == 0


def _penalidade(m) -> int:
    """Pontuação das 4 regras do padrão — menor é melhor."""
    tam = len(m)
    total = 0

    # Regra 1: sequências de 5+ módulos iguais
    for eixo in range(2):
        for i in range(tam):
            seq, anterior = 0, -1
            for j in range(tam):
                v = m[i][j] if eixo == 0 else m[j][i]
                if v == anterior:
                    seq += 1
                else:
                    if seq >= 5:
                        total += 3 + (seq - 5)
                    seq, anterior = 1, v
            if seq >= 5:
                total += 3 + (seq - 5)

    # Regra 2: blocos 2x2 da mesma cor
    for i in range(tam - 1):
        for j in range(tam - 1):
            if m[i][j] == m[i][j + 1] == m[i + 1][j] == m[i + 1][j + 1]:
                total += 3

    # Regra 3: padrão 1:1:3:1:1 com 4 claros (parecido com localizador)
    alvo1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]
    alvo2 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]
    for i in range(tam):
        for j in range(tam - 10):
            linha = [m[i][j + k] for k in range(11)]
            if linha in (alvo1, alvo2):
                total += 40
            coluna = [m[j + k][i] for k in range(11)]
            if coluna in (alvo1, alvo2):
                total += 40

    # Regra 4: desequilíbrio entre claros e escuros
    escuros = sum(sum(l) for l in m)
    proporcao = escuros * 100 // (tam * tam)
    total += 10 * (abs(proporcao - 50) // 5)
    return total


def _aplicar_formato(m, padrao: int) -> None:
    """Escreve as duas cópias da informação de formato.

    Cópia 1 (em volta do localizador superior esquerdo) guarda os 15 bits
    do mais significativo para o menos. Cópia 2 é dividida: os 8 bits
    baixos na linha 8, da direita para a esquerda, e os 7 altos na coluna
    8, de baixo para cima — pulando o módulo escuro fixo em (tam-8, 8).
    """
    tam = len(m)
    formato = _FORMATO_M[padrao]

    # Cópia 1: posição k recebe o bit (14 - k)
    for k in range(15):
        bit = (formato >> (14 - k)) & 1
        if k < 6:
            m[8][k] = bit
        elif k == 6:
            m[8][7] = bit
        elif k == 7:
            m[8][8] = bit
        elif k == 8:
            m[7][8] = bit
        else:
            m[14 - k][8] = bit

    # Cópia 2, parte da linha 8: bits 0..7
    for i in range(8):
        m[8][tam - 1 - i] = (formato >> i) & 1
    # Cópia 2, parte da coluna 8: bits 14..8
    for i in range(7):
        m[tam - 1 - i][8] = (formato >> (14 - i)) & 1


def matriz(texto: str) -> list[list[int]]:
    """Devolve a matriz do QR Code (1 = módulo escuro), sem borda."""
    if not texto:
        raise ValueError("Texto vazio.")
    versao = _escolher_versao(len(texto.encode("utf-8")))
    tam = 17 + versao * 4

    codewords = _codewords_finais(texto, versao)

    melhor, melhor_nota = None, None
    for padrao in range(8):
        m, res = _nova_matriz(tam)
        _padroes_fixos(m, res, versao)
        _preencher_dados(m, res, codewords)
        for i in range(tam):
            for j in range(tam):
                if not res[i][j] and _mascara(padrao, i, j):
                    m[i][j] ^= 1
        _aplicar_formato(m, padrao)
        nota = _penalidade(m)
        if melhor_nota is None or nota < melhor_nota:
            melhor, melhor_nota = m, nota
    return melhor


# ---------------------------------------------------------------------------
# Renderização
# ---------------------------------------------------------------------------
def desenhar_qr(canvas, texto: str, x0: int = 0, y0: int = 0,
                modulo: int = 6, borda: int = 4,
                cor: str = "#000000", fundo: str = "#FFFFFF") -> int:
    """Desenha o QR num canvas Tk. Devolve o lado total em pixels."""
    m = matriz(texto)
    tam = len(m)
    lado = (tam + borda * 2) * modulo
    canvas.create_rectangle(x0, y0, x0 + lado, y0 + lado,
                            fill=fundo, outline=fundo)
    for i in range(tam):
        for j in range(tam):
            if m[i][j]:
                x = x0 + (j + borda) * modulo
                y = y0 + (i + borda) * modulo
                canvas.create_rectangle(x, y, x + modulo, y + modulo,
                                        fill=cor, outline=cor)
    return lado


def gerar_svg(texto: str, modulo: int = 6, borda: int = 4,
              cor: str = "#000000", fundo: str = "#FFFFFF") -> str:
    """Devolve o QR como SVG (para imprimir ou colar na documentação)."""
    m = matriz(texto)
    tam = len(m)
    lado = (tam + borda * 2) * modulo
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{lado}" '
        f'height="{lado}" viewBox="0 0 {lado} {lado}">',
        f'<rect width="{lado}" height="{lado}" fill="{fundo}"/>',
    ]
    for i in range(tam):
        for j in range(tam):
            if m[i][j]:
                x = (j + borda) * modulo
                y = (i + borda) * modulo
                partes.append(
                    f'<rect x="{x}" y="{y}" width="{modulo}" '
                    f'height="{modulo}" fill="{cor}"/>'
                )
    partes.append("</svg>")
    return "".join(partes)
