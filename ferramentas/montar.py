"""Monta as aulas em questões: cada fontes/<nome>.json vira aulas/<nome>.html, arquivo único (abre com dois cliques).

Confere antes de gravar: 5 alternativas (A a E) e 5 comentários por questão; o comentário do gabarito começa por
"**Correta.**" e os demais por "**Errada.**"; nenhum assunto sem questão.
Uso: python -I ferramentas/montar.py
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(__file__).resolve().parent.parent
MODELO = (RAIZ / "ferramentas" / "modelo.html").read_text(encoding="utf-8")
GRIFA = (RAIZ / "ferramentas" / "grifa.js").read_text(encoding="utf-8")
LETRAS = ["A", "B", "C", "D", "E"]


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
        saida = RAIZ / "aulas" / f"{fonte.stem}.html"
        saida.write_text(html, encoding="utf-8", newline="\n")
        gab = "".join(q["gab"] for q in d["questoes"])
        print(f"{saida.relative_to(RAIZ)}: {len(d['questoes'])} questões · gabarito {gab} · {saida.stat().st_size:,} bytes".replace(",", "."))


if __name__ == "__main__":
    main()
