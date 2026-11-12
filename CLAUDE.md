# CLAUDE.md — Aula em Questões · Prof. Pietro Medeiros

> As regras gerais estão no `CLAUDE.md` da pasta-mãe e no `0 Readme First/HARNESS.md` de lá. Aqui fica só o que é deste projeto.

- **O que é:** aulas para resolver **em sala, no projetor**: questões objetivas no estilo de banca, com **todas as alternativas
  comentadas**, reveladas passo a passo (resposta da turma → gabarito → um comentário por vez → dica do professor). Pedido do titular
  em 12/11/2026.
- **Como se faz uma aula:** escreve-se `fontes/<nome>.json` e roda-se `python -I ferramentas/montar.py`, que confere a estrutura e gera
  `aulas/<nome>.html` (arquivo único, abre com dois cliques, sem internet). Não se edita o HTML gerado.
- **Prova:** `node testes/teste_aula.mjs aulas/<nome>.html` (Chrome headless; percorre todas as questões como o professor faria).
- **Pilha:** HTML/CSS/JS puro + Python (montador) + Node (teste). ⚠️ Fora da pilha do roteiro (§P4), como as demais aulas em HTML do titular.
- **Destino:** material de aula do titular; candidato a funcionalidade do portal Pietro Medeiros.
- **Estado:** `0 Readme First/FAROL.md` · **Decisões:** `docs/DECISOES.md` · **Origem:** `docs/PROCEDENCIA.md`.
