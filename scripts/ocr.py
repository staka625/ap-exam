"""Windows標準OCR(日本語)でPNGバイト列をテキスト化する。"""
import asyncio

from winrt.windows.globalization import Language
from winrt.windows.graphics.imaging import BitmapDecoder
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream

_ENGINE = OcrEngine.try_create_from_language(Language("ja"))


async def _ocr(png: bytes) -> str:
    stream = InMemoryRandomAccessStream()
    w = DataWriter(stream)
    w.write_bytes(png)
    await w.store_async()
    stream.seek(0)
    bmp = await (await BitmapDecoder.create_async(stream)).get_software_bitmap_async()
    res = await _ENGINE.recognize_async(bmp)
    # Windows OCRの行順は表などで乱れるので、上→下、左→右に並べ直す
    def box(ln):
        rs = [w.bounding_rect for w in ln.words]
        top, bot = min(r.y for r in rs), max(r.y + r.height for r in rs)
        return (top + bot) / 2, bot - top, min(r.x for r in rs)
    items = sorted(((*box(ln), ln) for ln in res.lines), key=lambda t: t[0])
    hs = sorted(h for _, h, _, _ in items) or [1]
    tol = hs[len(hs) // 2] * 0.6  # 中央値の行高の6割以内なら同じ行とみなす
    rows, ordered = [], []
    for it in items:
        if rows and it[0] - rows[-1][0][0] < tol:
            rows[-1].append(it)
        else:
            rows.append([it])
    for row in rows:
        ordered += [ln for *_, ln in sorted(row, key=lambda t: t[2])]
    # 日本語OCRは単語間に空白を入れるので、行内の空白を除去する（英数字同士の間だけ残す）
    lines = []
    for ln in ordered:
        out = ""
        for wd in ln.words:
            t = wd.text
            if (out and out[-1].isascii() and out[-1].isalnum() and t[:1].isascii() and t[:1].isalnum()
                    and not (out[-1].isdigit() and t[:1].isdigit())):  # "問1 0" → "問10"
                out += " "
            out += t
        lines.append(out)
    return "\n".join(lines)


def ocr_png(png: bytes) -> str:
    return asyncio.run(_ocr(png))


if __name__ == "__main__":
    import sys
    print(ocr_png(open(sys.argv[1], "rb").read()))
