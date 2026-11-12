"""Monta as aulas em questões: cada fontes/<nome>.json vira aulas/<nome>.html, arquivo único (abre com dois cliques).

Confere antes de gravar: 5 alternativas (A a E) e 5 comentários por questão; o comentário do gabarito começa por
"**Correta.**" e os demais por "**Errada.**"; nenhum assunto sem questão.
Uso: python -I ferramentas/montar.py
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(__file__).resolve().parent.parent
MODELO = (RAIZ / "ferramentas" / "modelo.html").read_text(encoding="utf-8")
GRIFA = (RAIZ / "ferramentas" / "grifa.js").read_text(encoding="utf-8")
LETRAS = ["A", "B", "C", "D", "E"]


ABSOLUTAS = re.compile(r"\b(apenas|somente|só|sempre|nunca|necessariamente|exclusivamente|únic[ao]|todo|toda|qualquer|"
                       r"nenhum|nenhuma|vedad[ao]|jamais)\b", re.I)


def vicios(d: dict) -> list:
    """Vícios que entregam o gabarito sem saber o conteúdo (pedido do titular, 12/11/2026):
    a correta ser a alternativa mais longa; palavras absolutas só nas erradas. Só vale para questões de alternativas longas
    (as de "I, II e III" têm alternativas curtas e não entram na conta)."""
    longas = [q for q in d["questoes"] if sum(len(v) for v in q["alts"].values()) / 5 > 40]
    if not longas:
        return []
    maior = sum(1 for q in longas if max(q["alts"], key=lambda x: len(q["alts"][x])) == q["gab"])
    abs_c = sum(1 for q in longas if ABSOLUTAS.search(q["alts"][q["gab"]]))
    abs_e = sum(1 for q in longas for x in LETRAS if x != q["gab"] and ABSOLUTAS.search(q["alts"][x]))
    print(f"  vícios: correta é a mais longa em {maior}/{len(longas)} · palavra absoluta na correta em {abs_c}/{len(longas)}"
          f" · nas erradas em {abs_e}/{4 * len(longas)}")
    e = []
    if maior > len(longas) / 4:
        e.append(f"a correta é a alternativa mais longa em {maior} de {len(longas)} questões (máximo: 1/4)")
    if abs_e and not abs_c:
        e.append("palavras absolutas só aparecem nas alternativas erradas")
    return e


def conferir(d: dict, nome: str) -> None:
    erros = []
    for i, q in enumerate(d["questoes"], 1):
        if sorted(q["alts"]) != LETRAS or sorted(q["coment"]) != LETRAS:
            erros.append(f"q{i}: precisa de A a E em alternativas e comentários")
            continue
        if q["gab"] not in LETRAS or not q["coment"][q["gab"]].startswith("**Correta.**"):
            erros.append(f"q{i}: o comentário do gabarito {q['gab']} deve começar por **Correta.**")
        erros += [f"q{i}{x}: comentário de alternativa errada deve começar por **Errada.**"
                  for x in LETRAS if x != q["gab"] and not q["coment"][x].startswith("**Errada.**")]
        if q["assunto"] not in d["assuntos"]:
            erros.append(f"q{i}: assunto {q['assunto']} não está em 'assuntos'")
        if not q.get("dica"):
            erros.append(f"q{i}: falta a dica do professor")
    erros += vicios(d)
    ce = d.get("ce") or []
    for i, x in enumerate(ce, 1):
        if x.get("gab") not in ("C", "E") or not x.get("texto") or not x.get("coment") or x.get("assunto") not in d["assuntos"]:
            erros.append(f"item C/E {i}: precisa de assunto, gab (C ou E), texto e coment")
    if ce:
        c = sum(x["gab"] == "C" for x in ce)
        if not 0.4 <= c / len(ce) <= 0.6:
            erros.append(f"itens C/E desequilibrados: {c} certos de {len(ce)}")
        g = "".join(x["gab"] for x in ce)
        alt = sum(a != b for a, b in zip(g, g[1:])) / max(1, len(g) - 1)
        if alt > 0.7:
            erros.append(f"gabarito C/E alterna demais ({alt:.0%}): embaralhe a ordem")
        print(f"  itens C/E: {len(ce)} · certos {c} · errados {len(ce) - c} · alternância {alt:.0%}")
    vazios = [a for a in d["assuntos"] if not any(q["assunto"] == a for q in d["questoes"])]
    erros += [f"assunto sem questão: {a}" for a in vazios]
    if erros:
        sys.exit(f"{nome}: recusado\n  " + "\n  ".join(erros))


def main() -> None:
    (RAIZ / "aulas").mkdir(exist_ok=True)
    for fonte in sorted((RAIZ / "fontes").glob("*.json")):
        d = json.loads(fonte.read_text(encoding="utf-8"))
        conferir(d, fonte.name)
        curto = " e ".join(d["assuntos"].values())
        dados = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
        html = (MODELO.replace("__TITULO_CURTO__", curto).replace("__TITULO__", d["titulo"])
                .replace("__DADOS__", dados).replace("__GRIFA__", GRIFA))
        rev = d.get("revisao") or []
        if rev:
            import shutil
            destino = RAIZ / "aulas" / "revisao"
            destino.mkdir(exist_ok=True)
            for r in rev:
                orig = RAIZ / "fontes" / "revisao" / r["arquivo"]
                if not orig.exists():
                    sys.exit(f"{fonte.name}: imagem da revisão não encontrada: {orig.name}")
                if r["assunto"] not in d["assuntos"]:
                    sys.exit(f"{fonte.name}: revisão {orig.name} com assunto desconhecido")
                shutil.copyfile(orig, destino / r["arquivo"])
        saida = RAIZ / "aulas" / f"{fonte.stem}.html"
        saida.write_text(html, encoding="utf-8", newline="\n")
        gab = "".join(q["gab"] for q in d["questoes"])
        print(f"{saida.relative_to(RAIZ)}: {len(d['questoes'])} questões · gabarito {gab} · {saida.stat().st_size:,} bytes".replace(",", "."))


if __name__ == "__main__":
    main()
