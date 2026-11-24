# 応用情報技術者試験 午後（科目B）過去問アーカイブと攻略・模試

## フォルダ構成

| パス | 内容 |
|---|---|
| `scripts/download_ap_pm.py` | IPA過去問ページから午後問題・解答例・採点講評PDFを一括ダウンロード |
| `scripts/build_subjects.py` | PDF→科目別Markdown（問題冊子はWindows標準OCR＋ページ画像、解答例・講評はテキスト抽出） |
| `data/pdf/` | ダウンロードしたPDF（33回×3種＝99ファイル） |
| `data/syllabus/` | APシラバス Ver.7.2（現行）・Ver.7.0、試験要綱 Ver.5.6 の原本とテキスト |
| `kakomon/01_security.md` 〜 `07_pm.md` | 7科目の過去問集（出題趣旨・問題OCR・ページ画像・解答例・採点講評） |
| `kakomon/08_strategy.md`，`09_service.md`，`10_audit.md` | 文系セット（経営戦略・サービスマネジメント・システム監査）の過去問集 |
| `kakomon/img/` | 問題ページ画像（`<科目番号>-<連番>_<試験>_q<問>_p<頁>.jpg`、1,704枚） |
| `manual/` | 科目別「完全攻略マニュアル」（10科目）と `00_文系セット総括.md` |
| `mock/` | Step 3：予想模試5回分の設計図、Step 4：予想問題 |

## 再実行

```powershell
uv venv .venv; uv pip install --python .venv requests pymupdf beautifulsoup4 winrt-runtime winrt-Windows.Media.Ocr winrt-Windows.Graphics.Imaging winrt-Windows.Storage.Streams winrt-Windows.Globalization winrt-Windows.Foundation winrt-Windows.Foundation.Collections
.\.venv\Scripts\python.exe -I scripts\download_ap_pm.py data\pdf
.\.venv\Scripts\python.exe -I scripts\build_subjects.py data\pdf kakomon
```

OCR結果は `kakomon/.ocr_cache/` にキャッシュされるので、2回目以降は数分で終わる。

## 収録状況（各科目ファイル共通：33回分。経営戦略は2013春以前が1回2問のため42問）

| 年度 | 春期 | 秋期 | 備考 |
|---|---|---|---|
| 2025（令和7） | ○ | ○ | |
| 2024（令和6） | ○ | ○ | |
| 2023（令和5） | ○ | ○ | |
| 2022（令和4） | ○ | ○ | |
| 2021（令和3） | ○ | ○ | |
| 2020（令和2） | — | ○ | 春期は中止、10月に実施 |
| 2019（平成31/令和元） | ○ | ○ | |
| 2018〜2012（平成30〜24） | ○ | ○ | |
| 2011（平成23） | ○ | ○ | 春期は震災で中止、6月に特別試験 |
| 2010〜2009（平成22〜21） | ○ | ○ | |

- 旧ソフトウェア開発技術者試験（〜2008年度）は、IPAサイトで過去問題の公開が終了しているため取得できない（年度ページが404）。
- 2026年度（CBT方式）の科目B問題は公開されていない。

### 問番号と科目の対応（`scripts/build_subjects.py` の ERA_A/B/C）

| 科目 | 2009春〜2013春（12問） | 2013秋（11問） | 2014春〜（11問） |
|---|---|---|---|
| 情報セキュリティ | 問9 | 問8 | 問1（必須） |
| プログラミング | 問2 | 問2 | 問3 |
| データベース | 問6 | 問5 | 問6 |
| システムアーキテクチャ | 問4 | 問3 | 問4 |
| ネットワーク | 問5 | 問4 | 問5 |
| 組込みシステム開発 | 問7 | 問6 | 問7 |
| プロジェクトマネジメント | 問10 | 問9 | 問9 |
| 経営戦略 | 問1，問3（情報戦略・戦略立案） | 問1 | 問2 |
| サービスマネジメント | 問11 | 問10 | 問10 |
| システム監査 | 問12 | 問11 | 問11 |

出典：独立行政法人情報処理推進機構（IPA）「過去問題」。問題本文はOCRのため誤認識を含む。正確な内容は各ページ画像で確認すること。
