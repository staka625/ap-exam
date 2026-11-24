"""IPA過去問ページから応用情報技術者試験 午後(科目B) の問題・解答例・採点講評PDFを一括ダウンロードする。

使い方: python -I scripts/download_ap_pm.py [保存先ディレクトリ]
※旧ソフトウェア開発技術者試験(〜H20)はIPAサイトで公開終了しており取得できない。
"""
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

INDEX = "https://www.ipa.go.jp/shiken/mondai-kaiotu/index.html"
H = {"User-Agent": "Mozilla/5.0 (past-exam downloader)"}
# 期区分: h=春, a=秋, o=2020年10月, tokubetsu=2011年特別
PDF_RE = re.compile(r"/(\d{4}[hr]\d{2}(?:[aho]|tokubetsu)_ap_pm_(?:qs|ans|cmnt)\.pdf)$")
YEAR_RE = re.compile(r"/shiken/mondai-kaiotu/\d{4}[hr]\d{2}\.html$")


def soup(url):
    r = requests.get(url, headers=H, timeout=60)
    r.raise_for_status()
    return BeautifulSoup(r.content, "html.parser")


def main(out=Path("data/pdf")):
    out.mkdir(parents=True, exist_ok=True)
    years = sorted({urljoin(INDEX, a["href"]) for a in soup(INDEX).find_all("a", href=True)
                    if YEAR_RE.search(a["href"])}, reverse=True)
    print(f"{len(years)} year pages")
    n = 0
    for y in years:
        for a in soup(y).find_all("a", href=True):
            m = PDF_RE.search(a["href"])
            if not m:
                continue
            dst = out / m.group(1)
            if dst.exists() and dst.stat().st_size > 0:
                continue
            r = requests.get(urljoin(y, a["href"]), headers=H, timeout=120)
            r.raise_for_status()
            assert r.content[:5] == b"%PDF-", f"not a PDF: {a['href']}"
            dst.write_bytes(r.content)
            n += 1
            print("saved", dst.name, len(r.content))
            time.sleep(1)  # IPAサーバへの負荷を抑える
    print(f"downloaded {n} new files; total {len(list(out.glob('*.pdf')))}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/pdf"))
