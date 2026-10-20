#!/usr/bin/env python3
"""Gera o blog estático (uma página HTML por artigo), o sitemap, o robots.txt e o llms.txt.

Como publicar um artigo novo:
  1. Edite scripts/posts.json (copie um bloco e preencha os campos).
  2. Rode:  python3 scripts/build_blog.py
  3. Faça commit e push das pastas geradas (blog/, sitemap.xml, robots.txt, llms.txt).

Campos de cada post em posts.json:
  slug         endereço da página (minúsculas, sem acento, com hífens): /blog/SLUG/
  aliases      endereços antigos (?artigo=...) que devem redirecionar para este
  tipo         Artigo | Atualização | Bastidores | Atividade
  tema         assunto livre (Bancário, Consumidor, Família...)
  date         data de publicação AAAA-MM-DD
  modified     data da última revisão AAAA-MM-DD (atualize ao revisar o texto)
  title        título da página (H1), com a pergunta ou o termo que a pessoa pesquisa
  seo_title    título curto para o Google (até ~60 caracteres)
  description  resumo para o Google (até ~155 caracteres)
  summary      resumo curto para os cartões do blog
  keywords     termos pesquisados (lista)
  quick        "Resposta rápida": 40 a 70 palavras respondendo direto à pergunta
  related      slugs de artigos relacionados ("Leia também")
  body         HTML do texto. Use <h2> para seções e, para FAQ, um
               <h2>Perguntas frequentes</h2> seguido de pares <h3>pergunta</h3><p>resposta</p>.
"""
import html, json, re, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.italobezerraadvogado.com.br"
NOME = "Italo Bezerra Advocacia"
AUTOR = "Italo Bezerra"
OAB = "OAB/PI 25603"
WA = "https://wa.me/5586999765214"
EMAIL = "silvaadvitalo@gmail.com"
IG = "https://www.instagram.com/italobezerraadvogado/"
TT = "https://www.tiktok.com/@italobezerra.advogado"
IMG_OG = SITE + "/contract-banner.jpg"
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
CLS = {"Atualização": "a", "Bastidores": "b", "Atividade": "x"}
TIPOS = ["Artigo", "Atualização", "Bastidores", "Atividade"]

e = lambda s: html.escape(s, quote=True)


def data_br(d):
    a, m, dia = d.split("-")
    return f"{int(dia)} de {MESES[int(m) - 1]} de {a}"


def texto(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def minutos(p):
    return max(1, round(len(texto(p["body"]).split()) / 190))


def slugify(s):
    s = texto(s).lower()
    for a, b in zip("áàâãäéèêëíìîïóòôõöúùûüç", "aaaaaeeeeiiiiooooouuuuc"):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60]


def prepara_corpo(body):
    """Coloca id nos <h2> e devolve (html, lista de (id, titulo))."""
    toc, usados = [], set()

    def f(m):
        t = texto(m.group(1))
        base = slugify(t) or "secao"
        i, n = base, 2
        while i in usados:
            i = f"{base}-{n}"
            n += 1
        usados.add(i)
        toc.append((i, t))
        return f'<h2 id="{i}">{m.group(1)}</h2>'

    return re.sub(r"<h2>(.*?)</h2>", f, body, flags=re.S), toc


def extrai_faq(body):
    m = re.search(r"<h2>Perguntas frequentes</h2>(.*?)(?=<h2>|<div class=\"call\">|<p><small>|$)", body, re.S)
    if not m:
        return []
    return [(texto(q), texto(a)) for q, a in re.findall(r"<h3>(.*?)</h3>\s*<p>(.*?)</p>", m.group(1), re.S)]


GTM_HEAD = """<script>
(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','GTM-WGFQX7LF');
</script>"""
GTM_BODY = '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-WGFQX7LF" height="0" width="0" style="display:none;visibility:hidden" title="Google Tag Manager"></iframe></noscript>'
FONTES = '<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@700;900&family=JetBrains+Mono:wght@400&family=Raleway:wght@400;500;600;700&display=swap" rel="stylesheet">'

ESCRITORIO = {
    "@type": "LegalService",
    "@id": SITE + "/#escritorio",
    "name": NOME,
    "url": SITE + "/",
    "image": SITE + "/lawyer-hero.jpg",
    "email": EMAIL,
    "telephone": "+55-86-99976-5214",
    "openingHours": "Mo-Fr 08:00-18:00",
    "areaServed": {"@type": "Country", "name": "Brasil"},
    "knowsAbout": ["Direito Bancário", "Direito do Consumidor", "Direito de Família", "Superendividamento", "Revisão de contratos bancários"],
    "sameAs": [IG, TT],
}
PESSOA = {
    "@type": "Person",
    "@id": SITE + "/#italo",
    "name": AUTOR,
    "jobTitle": "Advogado",
    "identifier": {"@type": "PropertyValue", "name": "OAB/PI", "value": "25603"},
    "url": SITE + "/",
    "image": SITE + "/lawyer-hero.jpg",
    "worksFor": {"@id": SITE + "/#escritorio"},
    "knowsAbout": ["Direito Bancário", "Direito do Consumidor", "Superendividamento", "Contratos bancários"],
    "sameAs": [IG, TT],
}

NAV = """<header class="nav">
  <div class="c">
    <a class="logo" href="/blog/">Italo Bezerra Advocacia<small>blog</small></a>
    <nav aria-label="Principal"><ul id="menu"><li><a href="/blog/">Publicações</a></li><li><a href="/">Site do escritório</a></li><li><a href="/#contato">Contato</a></li></ul></nav><button class="menu-btn" type="button" aria-controls="menu" aria-expanded="false">Menu</button>
    <a class="btn bp wpp" href="__WA__" target="_blank" rel="noopener noreferrer">WhatsApp</a>
  </div>
</header>"""

RODAPE = """<footer>
  <div class="c">
    <span class="logo">Italo Bezerra Advocacia</span>
    <p>Direito Bancário, do Consumidor e de Família · OAB/PI 25603 · silvaadvitalo@gmail.com · Atendimento online em todo o Brasil</p>
    <p>O conteúdo deste blog tem caráter informativo e educativo. Não constitui aconselhamento jurídico, não cria relação advogado-cliente nem promete resultado. Cada caso exige análise individual.</p>
    <p>© <span id="ano"></span> Italo Bezerra Advocacia</p>
  </div>
</footer>
<a class="wa wpp" href="__WA__" target="_blank" rel="noopener noreferrer" aria-label="Falar com Italo Bezerra pelo WhatsApp">WhatsApp</a>"""

SCRIPT = """<script>
document.getElementById("ano").textContent=new Date().getFullYear();
var nv=document.querySelector(".nav"),mb=document.querySelector(".menu-btn");
function fecha(){nv.classList.remove("open");mb.setAttribute("aria-expanded","false")}
mb.addEventListener("click",function(){mb.setAttribute("aria-expanded",nv.classList.toggle("open"))});
nv.querySelectorAll("ul a").forEach(function(a){a.addEventListener("click",fecha)});
document.addEventListener("keydown",function(e){if(e.key==="Escape")fecha()});
window.addEventListener("resize",function(){if(innerWidth>1000)fecha()});
document.querySelectorAll(".wpp").forEach(function(a){a.addEventListener("click",function(){window.dataLayer=window.dataLayer||[];window.dataLayer.push({event:"clique_whatsapp",local:a.className.indexOf("wa")>-1&&a.className.indexOf("btn")<0?"flutuante":"pagina"});});});
__EXTRA__
</script>"""


def jsonld(grafo):
    return '<script type="application/ld+json">\n' + json.dumps({"@context": "https://schema.org", "@graph": grafo}, ensure_ascii=False) + "\n</script>"


def card(p):
    return (f'<a class="post {CLS.get(p["tipo"], "")}" data-tipo="{e(p["tipo"])}" href="/blog/{p["slug"]}/"><span class="meta">{e(p["tipo"])} · {e(p["tema"])}</span>'
            f'<h3>{e(p["title"])}</h3><p>{e(p["summary"])}</p><span class="meta">{data_br(p["date"])} · {minutos(p)} min</span></a>')


def pagina_post(p, todos):
    url = f'{SITE}/blog/{p["slug"]}/'
    corpo, toc = prepara_corpo(p["body"])
    faq = extrai_faq(p["body"])
    titulo_head = f'{p["seo_title"]} | Italo Bezerra'
    msg = f'Olá, li o artigo "{p["title"]}" no seu site e gostaria de uma orientação.'
    wa_post = WA + "?text=" + __import__("urllib.parse").parse.quote(msg)
    grafo = [
        ESCRITORIO,
        PESSOA,
        {
            "@type": "BlogPosting",
            "@id": url + "#artigo",
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            "headline": p["title"],
            "description": p["description"],
            "inLanguage": "pt-BR",
            "datePublished": p["date"],
            "dateModified": p["modified"],
            "image": IMG_OG,
            "keywords": ", ".join(p["keywords"]),
            "articleSection": p["tema"],
            "wordCount": len(texto(p["body"]).split()),
            "author": {"@id": SITE + "/#italo"},
            "publisher": {"@id": SITE + "/#escritorio"},
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"},
                {"@type": "ListItem", "position": 3, "name": p["title"], "item": url},
            ],
        },
    ]
    if faq:
        grafo.append({"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    toc_html = ""
    if len(toc) >= 4:
        toc_html = '<nav class="toc" aria-label="Neste texto"><b>Neste texto</b><ol>' + "".join(f'<li><a href="#{i}">{e(t)}</a></li>' for i, t in toc) + "</ol></nav>"
    rel = [q for s in p.get("related", []) for q in todos if q["slug"] == s]
    rel_inline = ""
    if rel:
        rel_inline = '<div class="call"><b>Leia também</b><ul class="lt">' + "".join(f'<li><a href="/blog/{q["slug"]}/">{e(q["title"])}</a></li>' for q in rel) + "</ul></div>"
    outros = rel + [q for q in todos if q is not p and q not in rel]
    outros = outros[:3]
    mais = '<section class="rel"><div class="c"><h2>Mais publicações</h2><div class="posts">' + "".join(card(q) for q in outros) + "</div></div></section>"
    atualizado = f' · Atualizado em {data_br(p["modified"])}' if p["modified"] != p["date"] else ""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#2D2D2D">
<title>{e(titulo_head)}</title>
<meta name="description" content="{e(p["description"])}">
<meta name="keywords" content="{e(", ".join(p["keywords"]))}">
<meta name="author" content="{AUTOR}">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large,max-video-preview:-1">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="{NOME}">
<meta property="og:title" content="{e(p["seo_title"])}">
<meta property="og:description" content="{e(p["description"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{IMG_OG}">
<meta property="article:published_time" content="{p["date"]}">
<meta property="article:modified_time" content="{p["modified"]}">
<meta property="article:author" content="{AUTOR}">
<meta property="article:section" content="{e(p["tema"])}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(p["seo_title"])}">
<meta name="twitter:description" content="{e(p["description"])}">
<meta name="twitter:image" content="{IMG_OG}">
{FONTES}
{GTM_HEAD}
<link rel="stylesheet" href="/blog/blog.css">
{jsonld(grafo)}
</head>
<body>
{GTM_BODY}
{NAV.replace("__WA__", WA)}
<main>
<article class="art">
<nav class="crumb" aria-label="Você está em"><a href="/">Início</a> › <a href="/blog/">Blog</a> › <span>{e(p["tema"])}</span></nav>
<h1>{e(p["title"])}</h1>
<p class="meta">{e(p["tipo"])} · {e(p["tema"])} · Por {AUTOR}, {OAB} · Publicado em <time datetime="{p["date"]}">{data_br(p["date"])}</time>{atualizado.replace("Atualizado em", "Atualizado em")} · {minutos(p)} min de leitura</p>
<div class="quick" role="note"><b>Resposta rápida</b><p>{e(p["quick"])}</p></div>
{toc_html}
<div class="corpo">{corpo}
{rel_inline}</div>
<div class="autor"><img src="/lawyer-hero.jpg" alt="Italo Bezerra, advogado" width="76" height="76" loading="lazy"><p><b>{AUTOR} · {OAB}</b>Advogado com atuação em Direito Bancário, do Consumidor e de Família, com experiência em ações revisionais, superendividamento e análise de contratos bancários. Atendimento online em todo o Brasil. <a href="/#quem-somos">Conheça o escritório</a>.</p></div>
<p class="aviso">Este texto tem caráter informativo e não constitui aconselhamento jurídico nem promessa de resultado. A análise de cada caso depende dos documentos e das circunstâncias concretas. Última revisão em {data_br(p["modified"])}.</p>
</article>
</main>
{mais}
<section class="end">
  <div class="c">
    <h2>Seu caso não está no texto?</h2>
    <p>Cada situação tem detalhes próprios. Conte o que aconteceu e o escritório orienta os próximos passos.</p>
    <a class="btn bl wpp" href="{wa_post}" target="_blank" rel="noopener noreferrer">Falar pelo WhatsApp</a>
  </div>
</section>
{RODAPE.replace("__WA__", wa_post)}
{SCRIPT.replace("__EXTRA__", "")}
</body>
</html>
"""


def pagina_lista(posts):
    posts = sorted(posts, key=lambda p: p["date"], reverse=True)
    destaque = next((p for p in posts if p.get("destaque")), posts[0])
    resto = [p for p in posts if p is not destaque]
    mapa = {a: p["slug"] for p in posts for a in p.get("aliases", [])}
    feat = (f'<a class="feat" id="dest" href="/blog/{destaque["slug"]}/"><div class="tx"><span class="meta">Em destaque · {e(destaque["tipo"])} · {e(destaque["tema"])}</span>'
            f'<h2>{e(destaque["title"])}</h2><p>{e(destaque["summary"])}</p><span class="more">Ler agora</span></div>'
            f'<div class="side"><div><b>{minutos(destaque)}</b><span>minutos de leitura<br>{data_br(destaque["date"])}</span></div></div></a>')
    chips = "".join(f'<button type="button" data-f="{c}" aria-pressed="{str(i == 0).lower()}">{c}</button>' for i, c in enumerate(["Todos"] + TIPOS))
    url = SITE + "/blog/"
    desc = "Artigos em linguagem simples sobre Direito Bancário, do Consumidor e superendividamento: CET, golpe do Pix, financiamento, alienação fiduciária e mais."
    grafo = [
        ESCRITORIO,
        PESSOA,
        {"@type": "Blog", "@id": url + "#blog", "name": "Blog " + NOME, "url": url, "inLanguage": "pt-BR", "description": desc,
         "publisher": {"@id": SITE + "/#escritorio"}, "author": {"@id": SITE + "/#italo"},
         "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": f'{SITE}/blog/{p["slug"]}/', "datePublished": p["date"]} for p in posts]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": url}]},
    ]
    extra = ("var MAPA=" + json.dumps(mapa, ensure_ascii=False) + ";\n"
             "var q=new URLSearchParams(location.search).get('artigo');if(q){location.replace('/blog/'+(MAPA[q]||q)+'/');}\n"
             "var chips=document.getElementById('chips');chips.addEventListener('click',function(ev){var b=ev.target;if(b.tagName!=='BUTTON')return;var f=b.getAttribute('data-f');"
             "chips.querySelectorAll('button').forEach(function(x){x.setAttribute('aria-pressed',x===b)});"
             "document.getElementById('dest').hidden=f!=='Todos';"
             "var n=0;document.querySelectorAll('#lista .post').forEach(function(c){var ok=f==='Todos'||c.getAttribute('data-tipo')===f;c.hidden=!ok;if(ok)n++;});"
             "document.getElementById('vazio').hidden=n>0;});")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#2D2D2D">
<title>Blog de Direito Bancário e do Consumidor | {NOME}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="{NOME}">
<meta property="og:title" content="Blog de Direito Bancário e do Consumidor | {NOME}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{IMG_OG}">
<meta name="twitter:card" content="summary_large_image">
{FONTES}
{GTM_HEAD}
<link rel="stylesheet" href="/blog/blog.css">
{jsonld(grafo)}
</head>
<body>
{GTM_BODY}
{NAV.replace("__WA__", WA)}
<main>
<section class="bh"><div class="c"><h1>Notas de quem trabalha com banco, contrato e dívida todos os dias.</h1><p>Artigos explicativos em linguagem simples, atualizações da minha trajetória e bastidores da advocacia. Um caderno público que cresce com o tempo.</p><div class="chips" id="chips" role="group" aria-label="Filtrar por tipo">{chips}</div></div></section>
<section class="sec"><div class="c">{feat}<div class="posts" id="lista" aria-live="polite">{"".join(card(p) for p in resto)}</div><p class="vazio" id="vazio" hidden>Ainda não há publicações neste tipo. Volte em breve.</p></div></section>
</main>
<section class="end">
  <div class="c">
    <h2>Seu caso não está nos textos?</h2>
    <p>Cada situação tem detalhes próprios. Conte o que aconteceu e o escritório orienta os próximos passos.</p>
    <a class="btn bl wpp" href="{WA}" target="_blank" rel="noopener noreferrer">Falar pelo WhatsApp</a>
  </div>
</section>
{RODAPE.replace("__WA__", WA)}
{SCRIPT.replace("__EXTRA__", extra)}
</body>
</html>
"""


def main():
    posts = json.load(open(os.path.join(RAIZ, "scripts", "posts.json"), encoding="utf-8"))
    slugs = [p["slug"] for p in posts]
    assert len(slugs) == len(set(slugs)), "slug repetido"
    posts = sorted(posts, key=lambda p: p["date"], reverse=True)
    # páginas dos artigos
    for p in posts:
        pasta = os.path.join(RAIZ, "blog", p["slug"])
        os.makedirs(pasta, exist_ok=True)
        open(os.path.join(pasta, "index.html"), "w", encoding="utf-8").write(pagina_post(p, posts))
    # listagem
    open(os.path.join(RAIZ, "blog", "index.html"), "w", encoding="utf-8").write(pagina_lista(posts))
    # sitemap
    urls = [(SITE + "/", max(p["modified"] for p in posts), "1.0"), (SITE + "/financiamento/", None, "0.8"), (SITE + "/blog/", max(p["modified"] for p in posts), "0.9")]
    urls += [(f'{SITE}/blog/{p["slug"]}/', p["modified"], "0.8") for p in posts]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u, lm, pr in urls:
        sm += f"  <url><loc>{u}</loc>" + (f"<lastmod>{lm}</lastmod>" if lm else "") + f"<priority>{pr}</priority></url>\n"
    sm += "</urlset>\n"
    open(os.path.join(RAIZ, "sitemap.xml"), "w", encoding="utf-8").write(sm)
    # robots
    bots = ["Googlebot", "Bingbot", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended"]
    rb = "# Todos os buscadores e assistentes de IA podem ler o site.\nUser-agent: *\nAllow: /\nDisallow: /scripts/\n\n"
    rb += "".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots)
    rb += f"Sitemap: {SITE}/sitemap.xml\n"
    open(os.path.join(RAIZ, "robots.txt"), "w", encoding="utf-8").write(rb)
    # llms.txt
    ll = f"# {NOME}\n\n> Escritório de advocacia de {AUTOR} ({OAB}), com atuação em Direito Bancário, do Consumidor e de Família. Atendimento online em todo o Brasil. Contato: {EMAIL}, WhatsApp +55 86 99976-5214.\n\n"
    ll += "O conteúdo do blog é informativo, em linguagem simples, escrito pelo advogado. Não substitui a análise de um caso concreto.\n\n## Páginas principais\n\n"
    ll += f"- [Escritório]({SITE}/): áreas de atuação, diretrizes de atendimento e contato.\n- [Revisão de financiamento de veículos]({SITE}/financiamento/): quando um contrato de financiamento de veículo pode ser analisado.\n- [Blog]({SITE}/blog/): artigos sobre crédito, contratos bancários, superendividamento e golpes.\n\n## Artigos\n\n"
    ll += "".join(f'- [{p["title"]}]({SITE}/blog/{p["slug"]}/): {p["description"]}\n' for p in posts)
    open(os.path.join(RAIZ, "llms.txt"), "w", encoding="utf-8").write(ll)
    print("Geradas", len(posts), "páginas + blog/index.html, sitemap.xml, robots.txt, llms.txt")


if __name__ == "__main__":
    main()
