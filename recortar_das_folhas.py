# -*- coding: utf-8 -*-
u"""
============================================================
 RECORTAR AS FIGURAS DAS FOLHAS DE PAPEL — O Problema da História (2º ano)

 ⭐ A REGRA QUE MANDA AQUI (Marcos, 14/set/2026): *"procure na internet, nada de
    imagem gerada por IA, utilize das atividades"*.

 ⚠️⚠️ E NESTE CADERNO HÁ UMA SEGUNDA REGRA, QUE NÃO É DE ESTILO E SIM DE
    DIREITO: **dezoito das quarenta folhas colhidas são história em quadrinhos
    com personagem REGISTRADO** — Turma da Mônica, Chico Bento, Menino
    Maluquinho, Snoopy —, com o aviso de copyright impresso na própria folha.
    O GESTO delas entra (quem são os personagens · onde se passa · que título
    você daria · reconte com suas palavras); o desenho e o texto, **não**. É por
    isso que este caderno tem menos figura que os outros: as figuras boas da
    colheita estão justamente nessas folhas. Ver o `POTE-NARRA2.md`.

 As três folhas de onde as figuras saíram são livres:
   · d31 — *"Circule abaixo os animais que aparecem na história"* (A Pomba e a
     Formiga, fábula de Esopo): leão, gato, pomba, pato e formiga, coloridos. Os
     dois primeiros são INTRUSOS na fábula, e é isso que a folha ensina.
   · d32 — a corrida da lebre e da tartaruga (Esopo).
   · d36 — *"PINTE OS PERSONAGENS QUE APARECEM NO TEXTO"* (Assembleia dos Ratos,
     Esopo): o ratinho a traço limpo.
   · d19 — *"Montando a história"*: as peças recortáveis de um cenário livre
     (castelo, dragão, galinha, ovo, vaca, nuvem, menino, saco). São elas que
     deixam a criança MONTAR a própria história na folha 34.

 ⚠️ AS PEÇAS DA d19 VÊM CERCADAS POR UMA MOLDURA TRACEJADA (a linha de recorte
    da folha de papel). Quem a apaga é o `tira_linha_impressa`, e ele foi escrito
    exatamente para isso: uma moldura tracejada não ENVOLVE nada — são quarenta
    risquinhos soltos, cada um minúsculo e encostado na beirada.

 ⚠️ E O NOME TEM DE BATER COM O DESENHO. Conferir OLHANDO a folha de contato.

 ⚠️ DUAS PEÇAS DA d19 FICARAM DE FORA, e as duas pela folha de contato:
    · o OVO — o contorno dele encosta na moldura tracejada, e ao tirar a moldura
      saiu meio ovo: um arco solto, que não é desenho de nada;
    · o DRAGÃO — o desenho é um emaranhado de asas e folhas, e eu não consigo
      dizer com honestidade que uma criança de sete anos o reconhece. Figura cujo
      nome eu não posso garantir é figura que ensina errado.

 Uso:  python3 _narra2/recortar_das_folhas.py
============================================================
"""
from __future__ import print_function

import io
import json
import os
import sys

try:
    from PIL import Image
except ImportError as e:                                   # pragma: no cover
    print(u"preciso de Pillow (%s)" % e)
    sys.exit(2)

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, u"_padrao"))
from recorte_folha import (limpa_fundo, tira_halo, aperta,          # noqa: E402
                           tira_linha_impressa)

FOLHAS = os.path.join(RAIZ, u"_sequencias", u"folhas_narra2")
DEST = os.path.join(AQUI, u"img")
PREFIXO = u"hi_"
MAIOR = 300

D31 = u"d31_bb11a2.png"
D32 = u"d32_c383fa.jpg"
D36 = u"d36_26c238.jpg"
D19 = u"d19_456b73.jpg"

PECAS = [
    # --- d31: os animais da fábula, e os dois intrusos --------------------
    (u"leao",     D31,  132, 1268,  317, 1505),
    (u"gato",     D31,  366, 1327,  533, 1504),
    (u"pomba",    D31,  568, 1290,  777, 1505),
    (u"pato",     D31,  825, 1290, 1039, 1499),
    (u"formiga",  D31, 1057, 1282, 1283, 1499),

    # --- d32: a corrida -----------------------------------------------------
    (u"corrida",  D32,  858,  489, 1247,  864),

    # --- d36: o ratinho da assembleia --------------------------------------
    (u"ratinho",  D36,  400, 1175,  590, 1395),

    # --- d19: as peças de montar a história --------------------------------
    (u"nuvem",    D19,  574, 1172,  948, 1375),
    (u"castelo",  D19,  977, 1165, 1235, 1546),
    (u"menino",   D19,  109, 1500,  333, 1820),
    (u"saco",     D19,  368, 1534,  538, 1744),
    (u"galinha",  D19,  519, 1384,  709, 1574),
    (u"vaca",     D19,  621, 1630,  845, 1820),
]

DE_ONDE = {
    D31: u"d31 — Circule abaixo os animais que aparecem na história (A Pomba e a Formiga, Esopo)",
    D32: u"d32 — A Lebre e a Tartaruga (Esopo), interpretação de texto",
    D36: u"d36 — PINTE OS PERSONAGENS QUE APARECEM NO TEXTO (Assembleia dos Ratos, Esopo)",
    D19: u"d19 — Montando a história: as peças recortáveis do cenário",
}


def so_a_maior_ilha(c):
    u"""Fica só com a MAIOR mancha de tinta do recorte.

    ⚠️ AQUI ELA É OBRIGATÓRIA, e o `tira_linha_impressa` não bastou: as peças da
       d19 vêm cercadas por uma MOLDURA TRACEJADA, e os tracinhos dela não
       encostam na beirada do recorte (a moldura corre POR DENTRO da caixa) — a
       regra do `tira_linha_impressa` pede pedaço pequeno E encostado na borda.
       Aqui a conta é outra e mais simples: o desenho é uma mancha só, e tudo o
       que não for ela sai. Também limpa a linha da célula que vinha com o
       ratinho da d36."""
    import numpy as np
    from scipy import ndimage as nd
    a = np.asarray(c)
    alfa = a[..., 3] > 24
    if not alfa.any():
        return c
    rot, n = nd.label(nd.binary_dilation(alfa, np.ones((3, 3), bool)))
    if n < 2:
        return c
    tam = nd.sum(alfa, rot, range(1, n + 1))
    guarda = int(np.argmax(tam)) + 1
    px = c.load()
    for y, x in zip(*np.where(alfa & (rot != guarda))):
        r, g, b, _ = px[int(x), int(y)]
        px[int(x), int(y)] = (r, g, b, 0)
    return c


def recorta(folha, x1, y1, x2, y2, limpar=False):
    c = folha.crop((x1, y1, x2, y2))
    c = limpa_fundo(c)
    c = tira_halo(c)
    c = aperta(c)
    if c is not None:
        c = aperta(tira_linha_impressa(c))
    if c is not None and limpar:
        c = aperta(so_a_maior_ilha(c))
    return c


def main():
    if not os.path.isdir(FOLHAS):
        print(u"⛔ não achei %s" % FOLHAS)
        return 2
    abertas, feitas, origem = {}, [], {}
    cam = os.path.join(DEST, u"ORIGEM.json")
    if os.path.exists(cam):
        origem = json.load(io.open(cam, encoding=u"utf-8"))
    for nome, arq, x1, y1, x2, y2 in PECAS:
        if arq not in abertas:
            abertas[arq] = Image.open(os.path.join(FOLHAS, arq)).convert(u"RGB")
        c = recorta(abertas[arq], x1, y1, x2, y2, limpar=(arq in (D19, D36)))
        if c is None:
            print(u"  ⚠️  %-10s saiu VAZIA" % nome)
            continue
        if max(c.size) > MAIOR:
            f = float(MAIOR) / max(c.size)
            c = c.resize((max(1, int(c.width * f)), max(1, int(c.height * f))), Image.LANCZOS)
        alvo = PREFIXO + nome + u".png"
        c.save(os.path.join(DEST, alvo), optimize=True)
        origem[alvo] = u"folha:%s" % DE_ONDE[arq]
        feitas.append((alvo, c.size))
        print(u"  ✓ %-16s %3dx%-3d  <- %s" % (alvo, c.width, c.height, arq[:3]))
    io.open(cam, u"w", encoding=u"utf-8").write(
        json.dumps(origem, indent=1, sort_keys=True, ensure_ascii=False))
    print(u"\n%d figuras, todas recortadas de folha de papel." % len(feitas))
    folha_de_contato(feitas)
    return 0


def folha_de_contato(feitas):
    from PIL import ImageDraw
    COLS, CEL, LAB = 5, 180, 26
    linhas = (len(feitas) + COLS - 1) // COLS
    p = Image.new(u"RGB", (COLS * (CEL + 10) + 10, linhas * (CEL + LAB + 10) + 10), (250, 250, 248))
    d = ImageDraw.Draw(p)
    for i, (alvo, _) in enumerate(feitas):
        im = Image.open(os.path.join(DEST, alvo)).convert(u"RGBA")
        im.thumbnail((CEL, CEL))
        x = 10 + (i % COLS) * (CEL + 10)
        y = 10 + (i // COLS) * (CEL + LAB + 10)
        d.rectangle([x, y, x + CEL, y + CEL], outline=(215, 215, 210))
        fundo = Image.new(u"RGBA", im.size, (255, 255, 255, 255))
        fundo.alpha_composite(im)
        p.paste(fundo.convert(u"RGB"), (x + (CEL - im.width) // 2, y + (CEL - im.height) // 2))
        d.text((x + 3, y + CEL + 6), alvo[len(PREFIXO):-4], fill=(40, 44, 52))
    cam = os.path.join(AQUI, u"_contato.png")
    p.save(cam, optimize=True)
    print(u"folha de contato: %s  — OLHAR antes de seguir" % cam)


if __name__ == u"__main__":
    sys.exit(main())
