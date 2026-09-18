# -*- coding: utf-8 -*-
u"""
============================================================
 ESQUELETO — gerador das falas da folha viva

 ⚠️ REGRA DA CASA: o `falas.json` é a VERDADE. Texto escrito aqui = voz gravada.
    Texto mudou = voz regravada (o `entregar.yml` compara o carimbo sha1). É isto
    que acaba com "a tela diz uma coisa e a voz diz outra" — e atividade sem
    `falas.json` NÃO TEM COMO SER CONFERIDA, porque mp3 não se lê.

 ⚠️ UMA FONTE SÓ. As palavras, as frases e os textos moram no bloco
    `/*DADOS-INI*/` do `index.html` e são LIDOS daqui. Nada de segunda lista
    para desencontrar: já custou caro nesta casa um relatório sair zero com a
    folha inteira respondida.

 ⚠️ TODA TELA É NARRADA, e o alto-falante entra também em CADA RESPOSTA que a
    criança toca. Regra do Marcos: *"o alto-falante nas respostas também, para
    ajudar os alunos que não sabem ler"*. Sem isso a criança que ainda soletra
    escolhe pelo tamanho da palavra e a folha vira sorteio.

 ⚠️ A DICA NUNCA DIZ A RESPOSTA. Ela manda olhar uma pista, ou faz outra
    pergunta. Responder no segundo erro não é ajudar: é tirar da criança a única
    chance de pensar de novo.

 ⚠️ PALAVRAS QUE A VOZ ERRA (medido, e o portão `_qa/falas.py` reprova):
    "complete" vira "complite" — usar "preencha". Letra solta ("som S") sai como
    o NOME da letra: ancorar num exemplo ("o som de SAPO").

 Uso:  python3 <pasta>/gerar_falas.py
 Saída: reescreve os blocos FALAS e VOZOK do index.html, o `falas.json` e o
        `voz.txt`.
============================================================
"""
from __future__ import print_function

import collections
import io
import json
import os
import re
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
CAM = os.path.join(AQUI, u"index.html")
PREFIXO = u"hi_"                     # <- o prefixo desta atividade
VOZ = u"pt-BR-AntonioNeural"

D = io.open(CAM, encoding=u"utf-8").read()


def bloco(nome):
    u"""Lê um objeto do bloco DADOS do index.html. Uma fonte só.

    ⚠️ ELE CONTA AS CHAVES, e isso foi conserto de 15/set/2026. O esqueleto
       procurava o fim do objeto por uma marca de texto (`\n});`) — e QUALQUER
       objeto que não terminasse exatamente assim fazia a leitura passar
       adiante e engolir o bloco seguinte. No primeiro caderno do 2º ano os
       vinte e três blocos falharam de uma vez, todos com o mesmo erro, e a
       mensagem do json não dizia nada sobre a causa. Contar chave por chave
       (pulando as que estão DENTRO de texto) acha o fim de qualquer objeto.
    """
    i = D.find(u"var " + nome + u" = ")
    if i < 0:
        raise SystemExit(u"nao achei o bloco `var %s` no index.html" % nome)
    i = D.index(u"{", i)
    nivel, j, dentro, escapa = 0, i, False, False
    while j < len(D):
        c = D[j]
        if dentro:
            if escapa:
                escapa = False
            elif c == u"\\":
                escapa = True
            elif c == u'"':
                dentro = False
        else:
            if c == u'"':
                dentro = True
            elif c == u"{":
                nivel += 1
            elif c == u"}":
                nivel -= 1
                if nivel == 0:
                    j += 1
                    break
        j += 1
    txt = D[i:j]
    txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
    txt = re.sub(r'"\s*\+\s*\n\s*"', "", txt)                 # junta "a" + "b"
    txt = re.sub(r'([\{,]\s*)"?([A-Za-zÀ-ÿ_0-9]+)"?\s*:', r'\1"\2":', txt)
    txt = re.sub(r",(\s*[\}\]])", r"\1", txt)
    return json.loads(txt)


# ⚠️⚠️ A ENTIDADE HTML TAMBÉM É MARCAÇÃO, e isto foi lição paga (15/set/2026,
#    caderno de inglês do 8º ano). O `lp` tirava as TAGS e deixava as
#    ENTIDADES, então a lista de ingredientes da pizza — escrita com `&middot;`
#    para virar o ponto que separa os itens — ia para a fila de gravação como
#    *"Oil and middot Tomato sauce and middot Some onions"*. O portão
#    `_qa/revisor.py` pegou; se não pegasse, a voz teria dito isso à criança.
_ENT = {u"&middot;": u",", u"&nbsp;": u" ", u"&amp;": u" e ", u"&mdash;": u" ",
        u"&ndash;": u" ", u"&hellip;": u" ", u"&quot;": u'"', u"&lt;": u"",
        u"&gt;": u"", u"&#39;": u"'", u"&apos;": u"'"}


def lp(s):
    u"""tira a marcação e deixa o texto do jeito que a voz vai dizer"""
    t = re.sub(r"<[^>]+>", " ", s or u"")
    for _e, _v in _ENT.items():
        t = t.replace(_e, _v)
    t = re.sub(r"\s+", u" ", t)
    # ⚠️ e a tag que vira espaco deixa um vao ANTES da pontuacao ("o cinema ."),
    #    que o `_qa/revisor.py` acusa — com razao: a voz faz a pausa no lugar
    #    errado. Cola a pontuacao de volta na palavra.
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    # ⚠️ E A VIRGULA DA PAUSA PODE ENCOSTAR NUMA QUE JA EXISTIA (15/set/2026):
    #    a frase "My dad, ___ travels a lot" virou "My dad,, travels a lot" —
    #    duas virgulas coladas, que o Edge TTS le como uma pausa estranha e
    #    longa demais. Uma so, sempre.
    t = re.sub(r",\s*,+", u",", t)
    return t.strip()


def ch(w):
    return re.sub(r"[^a-z]", "",
                  unicodedata.normalize("NFKD", w.lower())
                  .encode("ascii", "ignore").decode())


# ⚠️⚠️ A ENTIDADE HTML TAMBÉM É MARCAÇÃO, e isto foi lição paga (15/set/2026,
#    caderno de inglês do 8º ano). O `lp` tirava as TAGS e deixava as
#    ENTIDADES, então a lista de ingredientes da pizza — escrita com `&middot;`
#    para virar o ponto que separa os itens — ia para a fila de gravação como
#    *"Oil and middot Tomato sauce and middot Some onions"*. O portão
#    `_qa/revisor.py` pegou; se não pegasse, a voz teria dito isso à criança.
_ENT = {u"&middot;": u",", u"&nbsp;": u" ", u"&amp;": u" e ", u"&mdash;": u" ",
        u"&ndash;": u" ", u"&hellip;": u" ", u"&quot;": u'"', u"&lt;": u"",
        u"&gt;": u"", u"&#39;": u"'", u"&apos;": u"'"}


def lp(s):
    u"""tira a marcação e deixa o texto do jeito que a voz vai dizer"""
    t = re.sub(r"<[^>]+>", " ", s or u"")
    for _e, _v in _ENT.items():
        t = t.replace(_e, _v)
    t = re.sub(r"\s+", u" ", t)
    # ⚠️ e a tag que vira espaco deixa um vao ANTES da pontuacao ("o cinema ."),
    #    que o `_qa/revisor.py` acusa — com razao: a voz faz a pausa no lugar
    #    errado. Cola a pontuacao de volta na palavra.
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    # ⚠️ E A VIRGULA DA PAUSA PODE ENCOSTAR NUMA QUE JA EXISTIA (15/set/2026):
    #    a frase "My dad, ___ travels a lot" virou "My dad,, travels a lot" —
    #    duas virgulas coladas, que o Edge TTS le como uma pausa estranha e
    #    longa demais. Uma so, sempre.
    t = re.sub(r",\s*,+", u",", t)
    return t.strip()


def ch(w):
    return re.sub(r"[^a-z]", "",
                  unicodedata.normalize("NFKD", w.lower())
                  .encode("ascii", "ignore").decode())


# ⚠️⚠️ A ENTIDADE HTML TAMBÉM É MARCAÇÃO, e isto foi lição paga (15/set/2026,
#    caderno de inglês do 8º ano). O `lp` tirava as TAGS e deixava as
#    ENTIDADES, então a lista de ingredientes da pizza — escrita com `&middot;`
#    para virar o ponto que separa os itens — ia para a fila de gravação como
#    *"Oil and middot Tomato sauce and middot Some onions"*. O portão
#    `_qa/revisor.py` pegou; se não pegasse, a voz teria dito isso à criança.
_ENT = {u"&middot;": u",", u"&nbsp;": u" ", u"&amp;": u" e ", u"&mdash;": u" ",
        u"&ndash;": u" ", u"&hellip;": u" ", u"&quot;": u'"', u"&lt;": u"",
        u"&gt;": u"", u"&#39;": u"'", u"&apos;": u"'"}


def lp(s):
    u"""tira a marcação e deixa o texto do jeito que a voz vai dizer"""
    t = re.sub(r"<[^>]+>", " ", s or u"")
    for _e, _v in _ENT.items():
        t = t.replace(_e, _v)
    t = re.sub(r"\s+", u" ", t)
    # ⚠️ e a tag que vira espaco deixa um vao ANTES da pontuacao ("o cinema ."),
    #    que o `_qa/revisor.py` acusa — com razao: a voz faz a pausa no lugar
    #    errado. Cola a pontuacao de volta na palavra.
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    # ⚠️ E A VIRGULA DA PAUSA PODE ENCOSTAR NUMA QUE JA EXISTIA (15/set/2026):
    #    a frase "My dad, ___ travels a lot" virou "My dad,, travels a lot" —
    #    duas virgulas coladas, que o Edge TTS le como uma pausa estranha e
    #    longa demais. Uma so, sempre.
    t = re.sub(r",\s*,+", u",", t)
    return t.strip()


def ch(w):
    return re.sub(r"[^a-z]", "",
                  unicodedata.normalize("NFKD", w.lower())
                  .encode("ascii", "ignore").decode())


# ⚠️⚠️ A ENTIDADE HTML TAMBÉM É MARCAÇÃO, e isto foi lição paga (15/set/2026,
#    caderno de inglês do 8º ano). O `lp` tirava as TAGS e deixava as
#    ENTIDADES, então a lista de ingredientes da pizza — escrita com `&middot;`
#    para virar o ponto que separa os itens — ia para a fila de gravação como
#    *"Oil and middot Tomato sauce and middot Some onions"*. O portão
#    `_qa/revisor.py` pegou; se não pegasse, a voz teria dito isso à criança.
_ENT = {u"&middot;": u",", u"&nbsp;": u" ", u"&amp;": u" e ", u"&mdash;": u" ",
        u"&ndash;": u" ", u"&hellip;": u" ", u"&quot;": u'"', u"&lt;": u"",
        u"&gt;": u"", u"&#39;": u"'", u"&apos;": u"'"}


def lp(s):
    u"""tira a marcação e deixa o texto do jeito que a voz vai dizer"""
    t = re.sub(r"<[^>]+>", " ", s or u"")
    for _e, _v in _ENT.items():
        t = t.replace(_e, _v)
    t = re.sub(r"\s+", u" ", t)
    # ⚠️ e a tag que vira espaco deixa um vao ANTES da pontuacao ("o cinema ."),
    #    que o `_qa/revisor.py` acusa — com razao: a voz faz a pausa no lugar
    #    errado. Cola a pontuacao de volta na palavra.
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    # ⚠️ E A VIRGULA DA PAUSA PODE ENCOSTAR NUMA QUE JA EXISTIA (15/set/2026):
    #    a frase "My dad, ___ travels a lot" virou "My dad,, travels a lot" —
    #    duas virgulas coladas, que o Edge TTS le como uma pausa estranha e
    #    longa demais. Uma so, sempre.
    t = re.sub(r",\s*,+", u",", t)
    return t.strip()


def ch(w):
    return re.sub(r"[^a-z]", "",
                  unicodedata.normalize("NFKD", w.lower())
                  .encode("ascii", "ignore").decode())


F = collections.OrderedDict()


def p(k, v):
    u"""⚠️ TODA fala passa por aqui LIMPA. Não é enfeite: quando a frase perde o
    travessão do discurso direto (`— Socorro! — gritou`), sobram dois espaços; a
    pista `ele ___ (correr)` vira `ele lacuna , verbo correr`; e um texto que já
    acaba em ponto ganha outro e sai `ela..`. Os TRÊS aconteceram neste caderno e
    quem pegou foi o portão `0o` (`_qa/revisor.py`) — a criança OUVIRIA isso."""
    t = re.sub(r"\s+", u" ", (v or u"")).strip()
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)     # espaço antes da pontuação
    t = re.sub(r"([,.;:!?])\1+", r"\1", t)     # ".." e ",,"
    t = re.sub(r"\.\s*\.", u".", t)
    F[k] = t








# ---------------------------------------------------------------------------
# AS FALAS DO MOTOR — estas toda folha viva tem
# ---------------------------------------------------------------------------
p(u"capa", u"O Problema da História. Trinta e cinco folhas sobre as histórias: quem está nelas, onde acontecem, qual é o problema e como ele se resolve. Escreva o seu nome ali embaixo e toque em Começar.")
p(u"folhaPronta", u"Folha pronta! Muito bem.")
p(u"escreva", u"Escreva a palavra usando o teclado.")
p(u"ligue", u"Toque numa peça do lado esquerdo e depois na do lado direito.")
p(u"toque_palavra", u"Primeiro toque numa peça ali embaixo. Depois toque na gaveta dela.")
p(u"quase", u"Quase! Tente de novo.")
p(u"cacatoque", u"Toque primeiro na primeira letra da palavra.")
p(u"pegue_lapis", u"Primeiro pegue uma canetinha ali em cima. Depois toque na palavra.")
p(u"novoCaderno", u"Caderno novo! Escreva o seu nome e toque em Começar.")
p(u"vozOn", u"Narração ligada!")
p(u"fim", u"Você chegou ao fim! Agora um desafio para levar: na próxima história que alguém contar para você, procure as quatro coisas. Quem está nela? Onde acontece? Qual é o problema? E como ele se resolve? Toda história tem as quatro.")

def semLacuna(s):
    u"""⚠️ A LACUNA NÃO SE NARRA (regra da casa, `SEQUENCIAS-DIDATICAS §2c`), e
    neste caderno ela some com reticências: o verso fica em suspenso, que é
    exatamente como um adulto o leria em voz alta para a criança completar —
    *"O cachimbo é de barro, bate no…"*. A correção diz o verso INTEIRO."""
    return re.sub(r"\s*_{2,}\s*\.?", u"…", lp(s))



ENUN = [
 u"Toda história tem gente ou bichos dentro dela. Olhe a figura e diga se ele está nessa história.",
 u"Marque todos os que estão na história e toque em Conferir. Cuidado com os que não estão.",
 u"Toque numa figura e depois na história em que ela aparece.",
 u"Toda história acontece em algum lugar. Onde acontece cada uma?",
 u"Puxe o lugar até a história dele, ou toque num e depois no outro.",
 u"Agora escreva o lugar. As casinhas dizem quantas letras tem a palavra.",
 u"As cenas da fábula do leão estão embaralhadas. Puxe cada uma para o lugar dela, "
 u"da primeira à última.",
 u"Agora a corrida da lebre e da tartaruga. Ponha as cenas na ordem certa.",
 u"Duas coisas aconteceram. Toque na que veio primeiro.",
 u"Toda história tem um problema: uma coisa que dá errado. Qual era o de cada uma?",
 u"O problema é de alguém, e aparece num momento da história. Pense bem antes de tocar.",
 u"Leia a fábula e toque nas palavras que dizem qual era o problema. Depois confira.",
 u"Depois do problema vem a solução: como aquilo se resolveu. Toque nela.",
 u"E se tivesse sido diferente? Pense no que quase aconteceu.",
 u"Em cada fábula alguém resolveu o problema. Escreva quem foi.",
 u"As histórias dizem como cada personagem é, com poucas palavras. Qual combina?",
 u"Leia a frase. Ela fala da lebre ou da tartaruga? Leve para a gaveta certa.",
 u"Agora separe: isto é o problema da história, ou é a solução dele?",
 u"Os personagens sentem coisas. Pense em como você se sentiria no lugar dele.",
 u"Ligue o momento da história ao que o personagem sentiu ali.",
 u"Agora ligue cada história à lição que ela deixa.",
 u"Toda história acontece num tempo. Leia a frase: ela já aconteceu, acontece agora, "
 u"ou vai acontecer?",
 u"Leia o título de cada grupo e marque só as frases que cabem nele.",
 u"Hoje acontece; ontem aconteceu. Escreva o verbo do jeito de ontem.",
 u"Ache na grade quem a pista descreve: toque na primeira letra e depois na última.",
 u"Agora as coisas da história. Na grade não há acento: procure SOLUCAO, não solução.",
 u"Toque numa pista, escute e escreva a palavra.",
 u"Nesta, toque nas palavras que dizem como o problema se resolveu. Depois confira.",
 u"E nesta, toque nas palavras que contam o erro da lebre. Depois confira.",
 u"No fim de uma fábula fica uma lição. Qual é a de cada uma?",
 u"Escreva o nome de cada um. Você já sabe todos: eles estiveram no caderno inteiro.",
 u"Agora o título é seu. Escreva uma palavra que combine com a história.",
 u"As duas frases contam a mesma história, mas só uma conta certo. Qual?",
 u"Agora a história é sua. Cada figura tem um papel: puxe o papel para a figura "
 u"que você escolher para ele.",
 u"Você já fez tudo isto sem os nomes. Agora eles: leve cada exemplo para a linha dele."]
assert len(ENUN) == 35, len(ENUN)
for _i, _t in enumerate(ENUN):
    p(u"p%denun" % (_i + 1), _t)

ELOGIO = [u"Isso mesmo!", u"Muito bem!", u"Você acertou!", u"Boa!", u"Exatamente!", u"É isso aí!"]
DICAS = [u"Volte à fábula e leia de novo, devagar. A resposta está lá dentro.",
         u"Conte a história na sua cabeça, do começo ao fim, e veja onde isto se encaixa.",
         u"Pense: o que essa parte muda na história? Se tirar, a história ainda funciona?",
         u"Leia as opções em voz alta. Só uma combina com o que aconteceu."]


def elogio(n):
    return ELOGIO[n % len(ELOGIO)]


def dica(n):
    return DICAS[n % len(DICAS)]


ITENS = bloco(u"ITENS")


def pote(pi):
    v = ITENS[u"p%d" % pi]
    return v[0] if v and isinstance(v[0], list) else v


def palavras(*ws):
    for _w in ws:
        if _w:
            _t = lp(_w)
            _t = _t[0].upper() + _t[1:]
            p(u"pal_" + ch(_w), _t if _t[-1:] in u".!?" else _t + u".")


# --- as folhas de PERGUNTA ---------------------------------------------------
for _pi, _nome in ((1, u"QUEM"), (4, u"ONDE"), (9, u"ANTES"), (10, u"PROB1"), (11, u"PROB2"),
                   (13, u"RESOL1"), (14, u"RESOL2"), (16, u"COMOE"), (19, u"SENTE"),
                   (22, u"TEMPO"), (30, u"MORAL")):
    _D = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _X = _D[_k]
        palavras(*_X[u"ops"])
        p(u"prg_" + _k, lp(_X[u"f"]))
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + lp(_X[u"f"]) + u" " +
          _X[u"r"][0].upper() + _X[u"r"][1:] + u".")
        p(u"dica%d_%s" % (_pi, _k), dica(_n))

# --- 33: qual frase reconta certo ---------------------------------------------
RECONTO = bloco(u"RECONTO")
for _n, _k in enumerate(pote(33)):
    _R = RECONTO[_k]
    p(u"prg_" + _k, lp(_R[u"f"]))
    p(u"frs_%s_c" % _k, lp(_R[u"certa"]))
    p(u"frs_%s_o" % _k, lp(_R[u"outra"]))
    p(u"certo33_" + _k, elogio(_n) + u" " + lp(_R[u"certa"]))
    p(u"dica33_" + _k, u"Leia as duas com calma. Uma delas troca quem fez o quê.")

# --- 2 e 23: marque vários ----------------------------------------------------
for _pi, _nome in ((2, u"MARQ"), (23, u"MARQ2")):
    _D = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _M = _D[_k]
        for _q in _M[u"pecas"]:
            p(u"mrc_%s_%s" % (_k, _q[u"k"]), lp(_q[u"t"])[0].upper() + lp(_q[u"t"])[1:] + u".")
        _ok = [_q[u"t"] for _q in _M[u"pecas"] if _q[u"ok"]]
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" São " + u", ".join(_ok) + u".")
        p(u"dica%d_%s" % (_pi, _k), u"Vá uma por uma e pergunte: esta aparece mesmo na história?")

# --- 3, 20 e 21: ligar --------------------------------------------------------
LIGP = bloco(u"LIGP")
for _n, _k in enumerate(pote(3)):
    _L = LIGP[_k]
    p(u"fig_" + _k, _L[u"n"][0].upper() + _L[u"n"][1:] + u".")
    p(u"lg_" + _k + u"_d", lp(_L[u"b"])[0].upper() + lp(_L[u"b"])[1:] + u".")
    p(u"certo3_" + _k, elogio(_n) + u" " + _L[u"n"][0].upper() + _L[u"n"][1:] +
      u" está em " + _L[u"b"] + u".")
    p(u"dica3_" + _k, u"Lembre em qual fábula você viu esse bicho.")
for _pi, _nome in ((20, u"LIGS"), (21, u"LIGF")):
    _D = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _L = _D[_k]
        p(u"lg_" + _k + u"_e", lp(_L[u"a"]) + u".")
        p(u"lg_" + _k + u"_d", lp(_L[u"b"])[0].upper() + lp(_L[u"b"])[1:] + u".")
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + lp(_L[u"a"]) + u": " + _L[u"b"] + u".")
        p(u"dica%d_%s" % (_pi, _k), dica(_n))

# --- 5, 7, 8 e 34: puxar e soltar ----------------------------------------------
SOLTA1 = bloco(u"SOLTA1")
for _n, _k in enumerate(pote(5)):
    _X = SOLTA1[_k]
    p(u"vrs_" + _k, lp(_X[u"v"]) + u".")
    p(u"rot_" + _k, lp(_X[u"rot"])[0].upper() + lp(_X[u"rot"])[1:] + u".")
    p(u"certo5_" + _k, elogio(_n) + u" " + lp(_X[u"v"]) + u" acontece " + _X[u"rot"] + u".")
    p(u"dica5_" + _k, dica(_n))
for _pi, _nome in ((7, u"ORDEM1"), (8, u"ORDEM2")):
    _D = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _X = _D[_k]
        p(u"pos_" + _k, _X[u"pos"] + u".")
        p(u"cena_" + _k, lp(_X[u"v"]) + u".")
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + _X[u"pos"] + u": " + lp(_X[u"v"]) + u".")
        p(u"dica%d_%s" % (_pi, _k), u"Conte a fábula do começo. O que aconteceu antes disto?")
MONTA = bloco(u"MONTA")
for _n, _k in enumerate(pote(34)):
    _X = MONTA[_k]
    p(u"fig_" + _k, u"Figura: " + _X[u"fig"] + u".")
    p(u"rot_" + _k, lp(_X[u"rot"])[0].upper() + lp(_X[u"rot"])[1:] + u".")
    p(u"certo34_" + _k, elogio(_n) + u" Escolha sua, e ela cabe na história.")
    p(u"dica34_" + _k, u"Não há errado aqui: escolha a figura que você quiser para esse papel "
                       u"e leve o papel até ela.")

# --- 6, 15, 24, 31: escrever nas casinhas --------------------------------------
for _pi, _nome in ((6, u"GRD1"), (15, u"GRD2"), (24, u"GRD3"), (31, u"GRD4")):
    _D = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _G = _D[_k]
        p(u"grd_" + _k, semLacuna(_G[u"p"]) + u" " + lp(_G[u"d"]))
        _c = lp(_G[u"p"]).replace(u"___", _G[u"w"].lower()).replace(u"…", u" " + _G[u"w"].lower()).strip()
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + _c[0].upper() + _c[1:])
        p(u"dica%d_%s" % (_pi, _k), u"Conte as casinhas e diga a palavra devagar, letra por letra.")

# --- 32: o título é seu --------------------------------------------------------
PROD = bloco(u"PROD")
for _n, _k in enumerate(pote(32)):
    _X = PROD[_k]
    p(u"prd_" + _k, u"Escreva " + _X[u"q"] + u".")
    p(u"certo32_" + _k, elogio(_n) + u" O título é seu e combina com a história.")
    p(u"dica32_" + _k, u"Pense no personagem principal e no problema dele. "
                       u"Um título curto com os dois já serve.")

# --- 12, 28 e 29: achar no texto ------------------------------------------------
TXT = bloco(u"TXT")
for _pi, _tk in ((12, u"tx1"), (28, u"tx2"), (29, u"tx3")):
    _T = TXT[_tk]
    _nw = 0
    for _lin in _T[u"linhas"]:
        for _w in _lin:
            p(u"tx%d_%d" % (_pi, _nw), _w)
            _nw += 1
    p(u"certo%d_t" % _pi, u"Muito bem! As palavras eram " + u", ".join(_T[u"ok"]) + u".")
    p(u"dica%d_t" % _pi, u"Leia a fábula linha por linha. Procure a linha em que a história "
                         u"vira do avesso.")

# --- 17 e 18: as gavetas --------------------------------------------------------
GAV = bloco(u"GAV")
_GAVTXT = {u"l": u"Gaveta da lebre.", u"t": u"Gaveta da tartaruga.",
           u"p": u"Gaveta do problema.", u"s": u"Gaveta da solução."}
for _gk, _G in GAV.items():
    for _C in _G[u"cols"]:
        p(u"gav_%s_%s" % (_gk, _C[u"k"]), _GAVTXT[_C[u"k"]])
_GAVCERTO = {u"l": u" é da lebre.", u"t": u" é da tartaruga.",
             u"p": u" é o problema.", u"s": u" é a solução."}
_GAVDICA = {u"gA": u"Quem corria depressa e quem andava devagar? Volte à corrida.",
            u"gB": u"Pergunte: isto é a coisa que deu errado, ou é a saída que apareceu depois?"}
for _pi, _gk in ((17, u"gA"), (18, u"gB")):
    for _n, _k in enumerate(pote(_pi)):
        _X = GAV[_gk][u"pal"][_k]
        p(u"diz2_%s_%s" % (_gk, _k), lp(_X[u"p"])[0].upper() + lp(_X[u"p"])[1:] + u".")
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " +
          lp(_X[u"p"])[0].upper() + lp(_X[u"p"])[1:] + _GAVCERTO[_X[u"c"]])
        p(u"dica%d_%s" % (_pi, _k), _GAVDICA[_gk])

# --- 25 e 26: os caça-palavras --------------------------------------------------
for _pi, _nome in ((25, u"CACA"), (26, u"CACA2")):
    _C = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _P = _C[u"pal"][_k]
        p(u"cp_" + _k, _P[u"pista"][0].upper() + _P[u"pista"][1:] + u".")
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" Achou.")

# --- 27: a cruzadinha -----------------------------------------------------------
CRZD = bloco(u"CRZD")
for _n, _k in enumerate(pote(27)):
    _P = CRZD[_k]
    p(u"crz_" + _k, lp(_P[u"d"]) + u".")
    p(u"certo27_" + _k, elogio(_n) + u" " + lp(_P[u"d"]) + u": " + _P[u"p"].capitalize() + u".")
    p(u"dica27_" + _k, u"Conte as casinhas e lembre da fábula em que isso aconteceu.")

# --- 35: o cartaz ⭐ os nomes vêm por último -------------------------------------
CART = bloco(u"CART")
for _L in CART[u"linhas"]:
    p(u"cart_" + _L[u"k"], u"%s: %s. Por exemplo, %s." % (_L[u"t"].capitalize(), _L[u"d"], _L[u"e"]))
_CARTCERTO = {u"p": u" é um personagem: quem está na história.",
              u"l": u" é o lugar: onde a história acontece.",
              u"c": u" é o problema: o que dá errado.",
              u"s": u" é a solução: como o problema se resolve."}
for _n, _k in enumerate(pote(35)):
    _X = CART[u"exem"][_k]
    p(u"ex_" + _k, lp(_X[u"p"])[0].upper() + lp(_X[u"p"])[1:] + u".")
    p(u"certo35_" + _k, elogio(_n) + u" " + lp(_X[u"p"])[0].upper() + lp(_X[u"p"])[1:] + _CARTCERTO[_X[u"c"]])
    p(u"dica35_" + _k, u"Olhe o exemplo que já está em cada linha do cartaz e compare com este.")


# ==============================================================================
#  AS SÍLABAS FALADAS — e este bloco é obrigatório em caderno que fale sílaba
#
#  ⚠️⚠️ POR QUE NÃO DÁ PARA SINTETIZAR A SÍLABA SOLTA (e a casa já pagou por
#     isto DUAS vezes — set/2026 e 16/set/2026, as duas o Marcos ouvindo):
#     a voz não lê SOM, lê PALAVRA. Entregue "SA" a ela e ela soletra "esse-á";
#     "VA" vira "vê-á"; "ÇÃ" ela nem tenta, porque ç não começa palavra em
#     português. Escrever a sílaba "como se fala" conserta UM caso e nunca
#     fecha a família.
#
#  O QUE FUNCIONA é o contrário: gravar a PALAVRA INTEIRA — que a voz pronuncia
#  certo, porque é palavra de verdade — alinhar letra a letra com o
#  `ctc-forced-aligner` e CORTAR a sílaba de dentro dela. Quem faz isso é o
#  `_padrao/silabas_voz.py`, dentro do `entregar.yml`, lendo o `silabas.json`
#  que sai daqui. O portão é o `_qa/silabas.py`.
#
#  COMO SE USA: para cada palavra do caderno, uma linha
#      _reg(u"CAVALO", [u"CA", u"VA", u"LO"])
#  e, no app, a sílaba fala por `falarSilaba(null, 0, "VA")` — nunca por
#  `falar("sil_va")`. Caderno que não fala sílaba não escreve nada: o
#  `silabas.json` sai com `"palavras": {}` e o `entregar.yml` nem baixa o
#  alinhador por ele.
#
#  ⚠️ NÃO HÁ FALA DE RESERVA POR SÍLABA. Faltando o recorte, o app diz a
#     PALAVRA INTEIRA. Uma reserva sintetizada seria o defeito voltando pela
#     porta dos fundos — e calado, que é pior.
# ==============================================================================
_SIL_DE = {}          # palavra -> [sílabas, NA ORDEM da palavra]
_MAPA_SIL = {}        # sílaba  -> [palavra, posição]
_RECUSADAS = []


def _reg(palavra, silabas):
    u"""⚠️ A LISTA TEM DE ESTAR NA ORDEM DA PALAVRA. O alinhador corta pelos
    limites das letras: ["RO","CAR"] para CARRO faz sair "ro" onde devia sair
    "car" — e a criança ouve o pedaço errado, sem erro nenhum na tela. Folha de
    ORDENAR guarda as sílabas EMBARALHADAS: passe-as por `_ordena` antes.
    ⚠️ E ganha sempre a partição MAIS FINA: "PIPO"+"CA" fecha PIPOCA sem ser
    separação silábica, e sobrescrevendo PI-PO-CA deixaria a sílaba PI muda."""
    silabas = list(silabas)
    if u"".join(silabas).upper() != palavra.upper():
        _RECUSADAS.append((palavra, silabas))
        return
    velha = _SIL_DE.get(palavra.lower())
    if velha and len(velha) >= len(silabas):
        return
    _SIL_DE[palavra.lower()] = silabas


def _ordena(palavra, embaralhadas):
    u"""as mesmas sílabas na ORDEM em que formam a palavra — sem inventar
    nenhuma: encaixa da esquerda para a direita e desiste se não fechar."""
    resto, saida, alvo = list(embaralhadas), [], palavra.upper()
    while alvo:
        for _i, _sb in enumerate(resto):
            if alvo.startswith(_sb.upper()):
                saida.append(_sb)
                alvo = alvo[len(_sb):]
                resto.pop(_i)
                break
        else:
            return None
    return saida if not resto else None


def _achaSilaba(s):
    u"""a palavra de onde a sílaba será recortada. Ganha a MAIS CURTA: menos
    letras na gravação, menos lugar para o alinhador errar."""
    cand = [_w for _w in sorted(_SIL_DE) if s in _SIL_DE[_w]]
    if not cand:
        return None
    _w = min(cand, key=lambda w: (len(_SIL_DE[w]), len(w), w))
    return [_w, _SIL_DE[_w].index(s)]


def _mapeia(soltas):
    u"""monta o SILMAP das sílabas que o app fala sozinhas, e DEVOLVE as órfãs.
    ⚠️ Sílaba órfã não é erro — o app diz a palavra inteira — mas tem de sair
    IMPRESSA, senão aquele botão emudece sem ninguém saber. Distratora que não
    mora em palavra nenhuma do caderno pede uma PALAVRA-CARREGADORA: uma
    palavra de verdade, curta, registrada só para ser gravada e cortada."""
    orfas = []
    for _s in sorted(set(soltas)):
        _achou = _achaSilaba(_s)
        if _achou:
            _MAPA_SIL[_s] = _achou
        else:
            orfas.append(_s)
    # e a PALAVRA INTEIRA de cada uma precisa existir como fala: é dela que o
    # recorte sai, e é ela que o app diz quando o recorte falta.
    for _w in sorted(_SIL_DE):
        p(u"pal_" + ch(_w), _w.upper() + u".")
    return orfas


_ORFAS = _mapeia([])          # <- passe aqui TODA sílaba que o app fala sozinha


# ---------------------------------------------------------------------------
# A SAÍDA
# ---------------------------------------------------------------------------
def chave(s):
    u"""O nome do mp3 sai do TEXTO, não da chave da fala — assim duas chaves que
    dizem a mesma frase gravam um arquivo só."""
    s = re.sub(r"\s+", u" ", s or u"").strip().lower()
    hh = 5381
    for c in s:
        hh = ((hh * 33) ^ ord(c)) & 0xFFFFFFFF
    d, out = hh, u""
    if d == 0:
        return u"0"
    while d:
        out = u"0123456789abcdefghijklmnopqrstuvwxyz"[d % 36] + out
        d //= 36
    return out


falas, vistos = [], {}
for k in sorted(F.keys()):
    txt = F[k]
    if not txt:
        continue
    c = chave(txt)
    if c in vistos:
        continue
    vistos[c] = 1
    falas.append({u"id": PREFIXO + c, u"texto": txt, u"voz": VOZ})

html = io.open(CAM, encoding=u"utf-8").read()
blocoF = (u"/*FALAS-INI*/\nvar FALAS = "
          + json.dumps(F, ensure_ascii=False, indent=1, sort_keys=True) + u";\n/*FALAS-FIM*/")
blocoV = (u"/*VOZOK-INI*/var VOZOK = "
          + json.dumps(dict((c, 1) for c in vistos), ensure_ascii=False) + u";/*VOZOK-FIM*/")
novo = re.sub(r"/\*FALAS-INI\*/.*?/\*FALAS-FIM\*/", lambda m: blocoF, html, flags=re.S)
novo = re.sub(r"/\*VOZOK-INI\*/.*?/\*VOZOK-FIM\*/", lambda m: blocoV, novo, flags=re.S)

# ⭐ o `silabas.json` é o que o `entregar.yml` lê para cortar cada sílaba de
#    dentro do mp3 da palavra inteira, e o `SILMAP` é o que o app usa para saber
#    de qual palavra veio cada pedaço. Uma fonte só para os dois.
io.open(os.path.join(AQUI, u"silabas.json"), u"w", encoding=u"utf-8").write(
    json.dumps({u"prefixo": PREFIXO, u"voz": VOZ,
                u"palavras": dict((w, _SIL_DE[w]) for w in sorted(_SIL_DE))},
               ensure_ascii=False, indent=1))
blocoS = (u"/*SILMAP-INI*/var SILMAP = "
          + json.dumps(_MAPA_SIL, ensure_ascii=False, sort_keys=True) + u";/*SILMAP-FIM*/")
novo = re.sub(r"/\*SILMAP-INI\*/.*?/\*SILMAP-FIM\*/", lambda m: blocoS, novo, flags=re.S)
io.open(CAM, u"w", encoding=u"utf-8").write(novo)
io.open(os.path.join(AQUI, u"falas.json"), u"w", encoding=u"utf-8").write(
    json.dumps(falas, ensure_ascii=False, indent=1))
io.open(os.path.join(AQUI, u"voz.txt"), u"w", encoding=u"utf-8").write(VOZ + u"\n")
print(u"FALAS: %d chaves; falas.json: %d fala(s) para gravar; "
      u"silabas: %d palavra(s) para recortar, %d silaba(s) no mapa"
      % (len(F), len(falas), len(_SIL_DE), len(_MAPA_SIL)))
if _ORFAS:
    print(u"   \u26a0\ufe0f %d silaba(s) SEM palavra de origem (o app dira a palavra "
          u"inteira): %s" % (len(_ORFAS), u", ".join(_ORFAS)))
if _RECUSADAS:
    print(u"   \u26a0\ufe0f %d lista(s) recusada(s) por nao formarem a palavra: %s"
          % (len(_RECUSADAS), u", ".join(
              u"%s=%s" % (w, u"-".join(sl)) for w, sl in _RECUSADAS[:8])))
