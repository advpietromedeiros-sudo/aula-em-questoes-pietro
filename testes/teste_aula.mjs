// Teste da aula em questões no Chrome headless (CDP), simulando o professor em sala: lista inicial; para cada questão,
// marca a resposta da turma, revela o gabarito, abre os 5 comentários um a um (o da correta primeiro) e a dica;
// confere o placar, a tecla R, a paleta de grifos (G) e que não há erro de script.
// Uso: python -I ferramentas/montar.py && node testes/teste_aula.mjs [aulas/<arquivo>.html] [pasta-de-prints]
import { existsSync, mkdirSync, writeFileSync, rmSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path'; import { spawn } from 'node:child_process'; import { tmpdir } from 'node:os';
import { pathToFileURL } from 'node:url';
const ARQ = resolve(process.argv[2] || 'aulas/lmp-e-adm-publica.html'), PR = resolve(process.argv[3] || '.scratch/prints');
mkdirSync(PR, { recursive: true });
const D = JSON.parse(readFileSync(ARQ, 'utf8').match(/<script id="dados" type="application\/json">([\s\S]*?)<\/script>/)[1].replace(/<\\\//g, '</'));
const NAV = ['C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync);
const perfil = join(tmpdir(), 'aulaq-' + Date.now()), porta = 9100 + Math.floor(Math.random() * 200);
const nav = spawn(NAV, ['--headless=new', `--remote-debugging-port=${porta}`, '--window-size=1366,768', `--user-data-dir=${perfil}`, 'about:blank'], { stdio: 'ignore' });
const espera = ms => new Promise(r => setTimeout(r, ms));
let alvo; for (let i = 0; i < 60 && !alvo; i++) { await espera(250); try { alvo = (await (await fetch(`http://127.0.0.1:${porta}/json`)).json()).find(t => t.type === 'page'); } catch { } }
const ws = new WebSocket(alvo.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r));
let id = 0; const pend = new Map(), erros = [];
ws.addEventListener('message', ev => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } if (m.method === 'Runtime.exceptionThrown') erros.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text); });
const cdp = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); setTimeout(() => { if (pend.has(i)) { pend.delete(i); r({}); } }, 45000); });
const av = async e => (await cdp('Runtime.evaluate', { expression: e, returnByValue: true })).result?.result?.value;
const tecla = async (key) => { const vk = { ArrowRight: 39, ArrowLeft: 37, Home: 36 }[key] || key.toUpperCase().charCodeAt(0);
  await cdp('Input.dispatchKeyEvent', { type: 'keyDown', key, code: key.length === 1 ? 'Key' + key.toUpperCase() : key, text: key.length === 1 ? key : undefined, windowsVirtualKeyCode: vk });
  await cdp('Input.dispatchKeyEvent', { type: 'keyUp', key, windowsVirtualKeyCode: vk }); await espera(120); };
const print = async n => { await espera(500); const r = await cdp('Page.captureScreenshot', { format: 'png' }); if (r.result) writeFileSync(join(PR, n), Buffer.from(r.result.data, 'base64')); };
const res = []; const ok = (n, c, d = '') => { res.push(!!c); console.log(`${c ? 'OK   ' : 'FALHA'} ${n}${!c && d ? ' · ' + d : ''}`); };
await cdp('Runtime.enable'); await cdp('Page.enable'); await cdp('Page.navigate', { url: pathToFileURL(ARQ).href }); await espera(2500);

ok('A1 · a capa lista as 16 questões, separadas por assunto', (await av(`document.querySelectorAll('.lista button').length`)) === D.questoes.length && (await av(`document.querySelectorAll('.capa .ass').length`)) === Object.keys(D.assuntos).length);
await print('0-capa.png');
await tecla('ArrowRight');
let falhas = [], acertos = 0;
for (let i = 0; i < D.questoes.length; i++) {
  const q = D.questoes[i], marca = i % 3 === 0 ? (q.gab === 'A' ? 'B' : 'A') : q.gab;  // a turma erra 1 em cada 3
  if (marca === q.gab) acertos++;
  await tecla(marca.toLowerCase());
  const m = await av(`document.querySelector('.alt.marcada')?.dataset.alt`);
  if (m !== marca) falhas.push(`q${i + 1}: marcação ${m}`);
  await tecla('ArrowRight');  // revela
  const certa = await av(`[...document.querySelectorAll('.alt.certa')].map(b=>b.dataset.alt).join()`), errada = await av(`[...document.querySelectorAll('.alt.errada')].map(b=>b.dataset.alt).join()`);
  if (certa !== q.gab || errada !== (marca === q.gab ? '' : marca)) falhas.push(`q${i + 1}: revelou certa=${certa} errada=${errada}`);
  const ordem = [];
  for (let k = 0; k < 5; k++) { await tecla('ArrowRight'); ordem.push(await av(`[...document.querySelectorAll('.com.on')].length`)); }
  const primeira = await av(`(()=>{const c=[...document.querySelectorAll('.com.on')];return c.length})()`);
  if (ordem.join() !== '1,2,3,4,5') falhas.push(`q${i + 1}: comentários ${ordem.join()}`);
  if (i === 0) { await print('1-questao-comentada.png'); }
  await tecla('ArrowRight');  // dica
  if (!(await av(`document.getElementById('dica').classList.contains('on')`))) falhas.push(`q${i + 1}: sem dica`);
  if (i === 1) await print('2-questao-com-dica.png');
  await tecla('ArrowRight');  // próxima
}
ok(`A2 · nas 16 questões: marca a turma, revela certa/errada, 5 comentários um a um e a dica`, falhas.length === 0, falhas.slice(0, 4).join(' | '));
const placar = await av(`document.getElementById('placar').textContent`);
ok(`A3 · placar no fim confere (${acertos} acertos)`, placar.includes(`${acertos} ✓`) && placar.includes(`${D.questoes.length - acertos} ✗`) && (await av(`document.querySelector('.capa h2').textContent`)).includes(`${acertos} acerto`), placar);
await print('3-placar.png');
await av(`document.querySelector('[data-ir="4"]').click()`); await espera(300);
await tecla('ArrowLeft'); await tecla('ArrowLeft');
const aposDois = await av(`document.querySelectorAll('.com.on').length`), dicaFora = !(await av(`document.getElementById('dica').classList.contains('on')`));
for (let k = 0; k < 5; k++) await tecla('ArrowLeft');  // 4 comentários + o gabarito
const semGab = await av(`document.querySelectorAll('.alt.certa').length`);
ok('A4 · ← desfaz um passo por vez: da questão comentada volta a dica e um comentário; depois esconde o gabarito', aposDois === 4 && dicaFora && semGab === 0, `${aposDois} ${dicaFora} ${semGab}`);
await tecla('r');
ok('A5 · R revela tudo de uma vez (5 comentários e dica)', (await av(`document.querySelectorAll('.com.on').length`)) === 5 && (await av(`document.getElementById('dica').classList.contains('on')`)));
await tecla('g');
ok('A6 · tecla G abre a paleta de grifos', await av(`(()=>{const p=document.getElementById('grf-paleta');return !!p&&!p.hidden})()`));
await tecla('g');
ok('A7 · texto justificado e negrito convertidos (sem ** na tela)', !(await av(`document.body.innerText.includes('**')`)) && /p,li,\.txt\{text-align:justify/.test(readFileSync(ARQ, 'utf8')));
ok('A8 · nenhum erro de script', erros.length === 0, erros.slice(0, 3).join(' | '));
ws.close(); nav.kill(); try { rmSync(perfil, { recursive: true, force: true }); } catch { }
console.log(`\n${res.filter(Boolean).length} de ${res.length} OK`);
process.exit(res.every(Boolean) ? 0 : 1);
