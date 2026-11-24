"""ダウンロード済みPDFから7科目分の問題・解答例・採点講評を抜き出し、科目別Markdownを作る。

使い方: python -I scripts/build_subjects.py <pdfディレクトリ> <出力ディレクトリ>
問題冊子PDFは画像スキャンのため、ページ画像を img/ に保存し、Windows標準OCRでテキスト化する
（OCR結果は <出力>/.ocr_cache にキャッシュ）。解答例・採点講評PDFはテキスト抽出。
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).parent))
from classify import SUBJECTS, norm, pdf_text, split_by_q  # noqa: E402
from ocr import ocr_png  # noqa: E402

# 出題番号→科目。IPAの午後問題は時期ごとに分野の並びが固定。
ERA_A = {2: "02_programming", 4: "04_architecture", 5: "05_network", 6: "03_database",
         7: "06_embedded", 9: "01_security", 10: "07_pm",
         1: "08_strategy", 3: "08_strategy", 11: "09_service", 12: "10_audit"}  # 2009春〜2013春(12問)。問3は情報戦略・戦略立案
ERA_B = {2: "02_programming", 3: "04_architecture", 4: "05_network", 5: "03_database",
         6: "06_embedded", 8: "01_security", 9: "07_pm",
         1: "08_strategy", 10: "09_service", 11: "10_audit"}   # 2013秋(11問)
ERA_C = {1: "01_security", 3: "02_programming", 4: "04_architecture", 5: "05_network",
         6: "03_database", 7: "06_embedded", 9: "07_pm",
         2: "08_strategy", 10: "09_service", 11: "10_audit"}   # 2014春〜(11問, 問1必須)
SEASON = {"h": "春期", "a": "秋期", "o": "10月実施", "tokubetsu": "特別試験(6月実施)"}



def era(exam, nq):
    if exam == "2013h25a":
        return ERA_B
    return ERA_A if nq == 12 else ERA_C


def label(exam):
    m = re.match(r"(\d{4})([hr])(\d{2})(.+)", exam)
    y, g, n, s = m.groups()
    gen = ("平成" if g == "h" else "令和") + ("元" if n == "01" and g == "r" else str(int(n)))
    return f"{y}年度（{gen}年度）{SEASON[s]}"


def _render(doc, i, dpi, rot=0):
    return doc[i].get_pixmap(matrix=pymupdf.Matrix(dpi / 72, dpi / 72).prerotate(rot),
                             colorspace=pymupdf.csGRAY)


def _median_len(text):
    ls = sorted(len(ln) for ln in text.splitlines()) or [0]
    return ls[len(ls) // 2]


def rotation(cache, i):
    f = cache / f"p{i:03d}.rot"
    return int(f.read_text()) if f.exists() else 0


def page_ocr(doc, i, cache):
    f = cache / f"p{i:03d}.txt"
    if not f.exists():
        f.write_text(ocr_png(_render(doc, i, 200).tobytes("png")), encoding="utf-8")
    text = f.read_text(encoding="utf-8")
    # OCRが崩れた(1文字ずつの行になった)ページは、解像度を変える／横向きページとして回転して読み直し、
    # ひらがなが最も多く読めた結果を採用する
    single = sum(len(ln) <= 1 for ln in text.splitlines())
    if not (cache / f"p{i:03d}.rot").exists() and (len(text.splitlines()) > 8 and _median_len(text) <= 2 or single >= 15):
        cands = [(0, text)] + [(r, ocr_png(_render(doc, i, dpi, r).tobytes("png")))
                               for r, dpi in ((0, 150), (0, 300), (90, 200), (270, 200))]
        rot, text = max(cands, key=lambda t: len(re.findall(r"[ぁ-ん]", t[1])))
        f.write_text(text, encoding="utf-8")
        (cache / f"p{i:03d}.rot").write_text(str(rot))
    return text


TITLE = re.compile(r"(関する|ついて)[,、]?次の記述を")


def question_pages(doc, cache):
    """{問番号: [ページindex...]} を返す。各問は新しいページから始まり、番号は連番。
    OCRは問番号を誤認識しやすい(問10→問純/問1の、問7IoT→問71oT)ので、
    タイトル文「〜に関する次の記述を読んで…答えよ」で開始ページを判定し、番号は連番で補う。"""
    starts = []
    for i in range(doc.page_count):
        lines = [norm(ln).replace(" ", "") for ln in page_ocr(doc, i, cache).splitlines()[:8]]
        head = "".join(lines)
        # 「…設問1~4に答えよ。」の「えよ」は右端で欠けやすいので「答」だけで判定
        if not (TITLE.search(head) and "答" in head) or lines and lines[0].startswith("設問"):
            continue
        if starts and i <= starts[-1][1] + 1:
            continue
        prev = starts[-1][0] if starts else 0
        body = re.sub(r"問\d+[~〜,、]+問\d+", "", head)  # 「次の問2~問11については」等を除く
        nums = [int(m.group(1)) for m in re.finditer(r"問(\d{1,2})(?![~〜\d])", body)]
        n = prev + 1 if prev + 1 in nums else min((x for x in nums if prev < x <= 12), default=prev + 1)
        starts.append((n, i))
    out = {}
    for k, (q, i) in enumerate(starts):
        end = starts[k + 1][1] if k + 1 < len(starts) else doc.page_count
        pages = list(range(i, end))
        if k + 1 == len(starts):  # 最終問の後ろの注意事項・白紙ページを除く
            pages = [p for p in pages if not re.search(r"注意事項|白紙|余白", norm(page_ocr(doc, p, cache))[:200])
                     or p == i]
        out[q] = pages
    return out


def clean(t):
    t = norm(t)
    t = re.sub(r"\d+/\d+\s*\nCopyright\(c\).*?\n.*?(解答例|採点講評)\s*\n", "", t)
    lines = [ln.rstrip() for ln in t.splitlines()]
    return "\n".join(ln for ln in lines if ln.strip())


def save_img(doc, i, path, rot=0):
    path.write_bytes(_render(doc, i, 130, rot).tobytes("jpeg", jpg_quality=70))


def main(pdf_dir, out, only=""):
    img = out / "img"
    img.mkdir(parents=True, exist_ok=True)
    sections = defaultdict(list)  # subject -> [(exam, md)]
    # 新しい順。同年度内は秋期(a)/10月(o)を春期(h)/特別(6月)より後とみなす
    order = {"h": 0, "tokubetsu": 1, "a": 2, "o": 2}
    exams = sorted({p.name.split("_")[0] for p in pdf_dir.glob(f"{only}*_ap_pm_qs.pdf")},
                   key=lambda e: (e[:4], order[e[7:]]), reverse=True)
    for exam in exams:
        ans = split_by_q(pdf_text(pdf_dir / f"{exam}_ap_pm_ans.pdf"))
        cmnt = split_by_q(pdf_text(pdf_dir / f"{exam}_ap_pm_cmnt.pdf"))
        doc = pymupdf.open(pdf_dir / f"{exam}_ap_pm_qs.pdf")
        cache = out / ".ocr_cache" / exam
        cache.mkdir(parents=True, exist_ok=True)
        qpages = question_pages(doc, cache)
        print(exam, {q: len(p) for q, p in qpages.items()}, flush=True)
        if sorted(qpages) != list(range(1, len(ans) + 1)):  # 解答例の問数と一致するかの自己チェック
            print(f"  !! {exam} 問題冊子の問数({len(qpages)})が解答例({len(ans)})と一致しない", flush=True)
        for q, subj in era(exam, len(ans)).items():
            num = subj[:2]
            if q not in qpages:
                print(f"  !! {exam} 問{q} の開始ページが見つからない", flush=True)
            parts = [f"## {label(exam)} 問{q}", ""]
            m = re.search(r"出題趣旨(.*?)設問", ans.get(q, ""), re.S)
            if m:
                parts += ["### 出題趣旨", "", re.sub(r"\s+", "", m.group(1)), ""]
            parts += ["### 問題（問題冊子・OCR）", ""]
            for k, p in enumerate(qpages.get(q, []), 1):
                name = f"{num}-{len(sections[subj]) + 1}_{exam}_q{q}_p{k}.jpg"
                save_img(doc, p, img / name, rotation(cache, p))
                parts += [f"![{label(exam)} 問{q} {k}ページ目](img/{name})", "",
                          "```text", page_ocr(doc, p, cache), "```", ""]
            body = ans.get(q, "")
            body = body[body.find("設問"):] if "設問" in body else body
            parts += ["### 解答例・解答の要点", "", "```text", clean(body), "```", "",
                      "### 採点講評", "", clean(cmnt.get(q, "（採点講評なし）")), "", "---", ""]
            sections[subj].append((exam, "\n".join(parts)))
    for subj, (title, _) in SUBJECTS.items():
        items = sections[subj]

        head = [f"# 応用情報技術者試験 午後（科目B）過去問集：{title}", "",
                f"収録：{len(items)}回分（{label(items[-1][0])} 〜 {label(items[0][0])}）", "",
                "出典：IPA 情報処理推進機構 過去問題（問題冊子・解答例・採点講評）。"
                "問題本文はスキャン画像からのOCRのため誤認識があり得る。正確な内容は各ページ画像を参照。", ""]
        (out / f"{subj}.md").write_text("\n".join(head + [md for _, md in items]), encoding="utf-8")
        print(subj, len(items))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), *sys.argv[3:])
