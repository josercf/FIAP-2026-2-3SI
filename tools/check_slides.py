#!/usr/bin/env python3
"""
Valida os decks Reveal.js procurando conteudo que estoura o slide.

O tema fixa cada <section> em 1280x720. Qualquer elemento que ultrapasse essa
caixa aparece cortado na projecao. Medir `scrollHeight` da section NAO detecta
isso de forma confiavel, entao aqui percorremos os descendentes e comparamos o
retangulo de cada um com a area util do slide (ja descontado o padding).

Uso:
    python3 tools/check_slides.py                      # todos os decks
    python3 tools/check_slides.py aulas-1sem/aulas/aula01.html
    python3 tools/check_slides.py --shots out/         # salva PNG dos slides com problema

Requer: pip install playwright && python3 -m playwright install chromium
"""
import http.server
import os
import socket
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LARGURA, ALTURA = 1280, 720
TOLERANCIA = 2  # px, para arredondamento de layout


def porta_livre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def servir(porta):
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(  # noqa: E731
        *a, directory=RAIZ, **k
    )
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", porta), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


# Executado no navegador: mede cada slide e devolve os elementos que vazam.
JS_MEDIR = """
() => {
  const secoes = [...document.querySelectorAll('.reveal .slides > section')];
  return secoes.map((sec, i) => {
    // Torna o slide mensuravel mesmo sem estar ativo
    const estiloAnterior = sec.getAttribute('style') || '';
    sec.style.display = 'block';
    sec.style.visibility = 'visible';
    sec.style.opacity = '1';

    const cs = getComputedStyle(sec);
    const padTop = parseFloat(cs.paddingTop);
    const padBottom = parseFloat(cs.paddingBottom);
    const padLeft = parseFloat(cs.paddingLeft);
    const padRight = parseFloat(cs.paddingRight);

    const base = sec.getBoundingClientRect();
    const limiteBaixo = base.top + 720 - padBottom;
    const limiteDireita = base.left + 1280 - padRight;

    const vazamentos = [];
    for (const el of sec.querySelectorAll('*')) {
      const ecs = getComputedStyle(el);
      if (ecs.display === 'none' || ecs.visibility === 'hidden') continue;
      // Rodape e barras sao posicionados de proposito na borda
      if (el.closest('.slide-footer, .top-bar, [class*="logo-header"]')) continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;

      const excessoBaixo = r.bottom - limiteBaixo;
      const excessoDireita = r.right - limiteDireita;
      if (excessoBaixo > 2 || excessoDireita > 2) {
        vazamentos.push({
          tag: el.tagName.toLowerCase(),
          classe: (el.className && el.className.baseVal !== undefined
                    ? el.className.baseVal : el.className || '').toString().slice(0, 40),
          texto: (el.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 60),
          abaixo: Math.round(excessoBaixo),
          direita: Math.round(excessoDireita),
        });
      }
    }

    sec.setAttribute('style', estiloAnterior);

    const titulo = sec.querySelector('h2');
    return {
      indice: i,
      titulo: titulo ? titulo.textContent.trim().slice(0, 55) : '(' + sec.className + ')',
      // so o vazamento mais grave por slide, para o relatorio nao explodir
      pior: vazamentos.sort((a, b) =>
        (b.abaixo + b.direita) - (a.abaixo + a.direita))[0] || null,
      total: vazamentos.length,
    };
  });
}
"""


def checar(page, url, nome, shots_dir=None):
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(900)
    slides = page.evaluate(JS_MEDIR)

    problemas = [s for s in slides if s["pior"]]
    print("\n%s  (%d slides)" % (nome, len(slides)))
    if not problemas:
        print("  OK: nenhum conteudo estourando 1280x720")
        return 0

    for s in problemas:
        p = s["pior"]
        eixo = []
        if p["abaixo"] > TOLERANCIA:
            eixo.append("%dpx abaixo do limite" % p["abaixo"])
        if p["direita"] > TOLERANCIA:
            eixo.append("%dpx a direita" % p["direita"])
        print("  slide %-2d  %-52s" % (s["indice"], s["titulo"]))
        print("           %s  <%s class=%r>" % (", ".join(eixo), p["tag"], p["classe"]))
        print("           texto: %s" % p["texto"])

        if shots_dir:
            os.makedirs(shots_dir, exist_ok=True)
            page.evaluate("i => Reveal.slide(i, 0)", s["indice"])
            page.wait_for_timeout(500)
            destino = os.path.join(
                shots_dir, "%s-slide%02d.png" % (nome.replace(".html", ""), s["indice"])
            )
            page.screenshot(path=destino)
            print("           screenshot: %s" % destino)

    return len(problemas)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    shots_dir = None
    if "--shots" in sys.argv:
        i = sys.argv.index("--shots")
        shots_dir = sys.argv[i + 1] if len(sys.argv) > i + 1 else "shots"

    if args:
        decks = args
    else:
        pasta = os.path.join(RAIZ, "aulas-1sem", "aulas")
        decks = [
            os.path.join("aulas-1sem", "aulas", f)
            for f in sorted(os.listdir(pasta))
            if f.endswith(".html")
        ]

    porta = porta_livre()
    httpd = servir(porta)
    total = 0

    try:
        with sync_playwright() as p:
            navegador = p.chromium.launch()
            page = navegador.new_page(viewport={"width": LARGURA, "height": ALTURA})
            for deck in decks:
                # Aceita caminho absoluto ou relativo: o servidor serve a partir da RAIZ
                rel = os.path.relpath(os.path.abspath(deck), RAIZ).replace(os.sep, "/")
                url = "http://127.0.0.1:%d/%s" % (porta, rel)
                total += checar(page, url, os.path.basename(deck), shots_dir)
            navegador.close()
    finally:
        httpd.shutdown()

    print("\n" + "=" * 62)
    if total:
        print("%d slide(s) com conteudo estourando." % total)
        return 1
    print("Todos os slides cabem em 1280x720.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
