#!/usr/bin/env python3
"""Count distinct header-nav and footer variants across every page.

Reports NON-EMPTY nav variants separately from pages whose <header> carries no
nav at all, because those are different defects and collapsing them hides one.
"""
import re, glob, collections

def scan(pat_nav=r'<nav[^>]*>(.*?)</nav>'):
    N = collections.Counter(); F = collections.Counter()
    no_header = no_footer = header_no_nav = 0
    for p in sorted(glob.glob('**/*.html', recursive=True)):
        t = open(p, encoding='utf-8', errors='replace').read()
        h = re.search(r'<header\b.*?</header>', t, re.S)
        if not h:
            no_header += 1
        else:
            n = re.search(pat_nav, h.group(0), re.S)
            items = tuple(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', a)).strip()
                          for a in re.findall(r'<a\b[^>]*>(.*?)</a>', n.group(1), re.S)) if n else ()
            if items: N[items] += 1
            else: header_no_nav += 1
        f = re.search(r'<footer\b.*?</footer>', t, re.S)
        if not f:
            no_footer += 1
        else:
            F[tuple(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', x)).strip().upper()
                    for x in re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', f.group(0), re.S))] += 1
    return N, F, no_header, no_footer, header_no_nav

if __name__ == '__main__':
    N, F, nh, nf, hnn = scan()
    print(f'  NON-EMPTY header nav variants : {len(N)}')
    print(f'  <header> present but no nav   : {hnn}')
    print(f'  pages with NO <header>        : {nh}')
    print(f'  footer variants               : {len(F)}')
    print(f'  pages with NO <footer>        : {nf}')
    for v, n in N.most_common():
        print(f'      nav x{n:<4} {list(v)}')
    for v, n in F.most_common():
        print(f'      footer x{n:<4} {list(v)}')
