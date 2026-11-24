"""解答例PDFの「出題趣旨」から各問の分野を判定する。"""
import re
import unicodedata
from pathlib import Path

import pymupdf

SUBJECTS = {
    "01_security": ("情報セキュリティ", ["セキュリティ", "暗号", "認証", "マルウェア", "脆弱性", "攻撃", "インシデント", "不正アクセス", "なりすまし", "電子署名", "ディジタル署名", "情報漏えい", "改ざん", "ゼロトラスト"]),
    "02_programming": ("プログラミング（アルゴリズム・データ構造）", ["アルゴリズム", "データ構造", "擬似言語", "プログラム", "再帰", "探索", "整列", "ソート", "計算量", "スタック", "キュー", "木構造", "グラフ"]),
    "03_database": ("データベース", ["データベース", "SQL", "E-R", "ＳＱＬ", "正規化", "関係モデル", "テーブル", "データモデル"]),
    "04_architecture": ("システムアーキテクチャ", ["システムアーキテクチャ", "システム構成", "可用性", "性能", "冗長", "稼働率", "クラウド", "仮想化", "負荷分散", "方式設計", "キャパシティ", "信頼性", "バックアップ", "コンテナ"]),
    "05_network": ("ネットワーク", ["ネットワーク", "TCP", "IP", "LAN", "ルータ", "DNS", "プロトコル", "VPN", "無線", "通信", "パケット", "スイッチ"]),
    "06_embedded": ("組込みシステム開発", ["組込み", "組み込み", "制御", "センサ", "ロボット", "マイコン", "タイマ", "モータ", "割込み", "IoT"]),
    "07_pm": ("プロジェクトマネジメント", ["プロジェクト", "スケジュール", "進捗", "WBS", "EVM", "見積", "要員", "ステークホルダ", "スコープ"]),
    # 文系セット（キーワードはbuild_subjectsでは使わない。分野は問番号で決まる）
    "08_strategy": ("経営戦略（2013春以前の情報戦略・戦略立案を含む）", []),
    "09_service": ("サービスマネジメント", []),
    "10_audit": ("システム監査", []),
}
# 対象外分野（経営戦略・開発・サービスマネジメント・監査）を見分けるための語
OTHER = ["経営", "戦略", "マーケティング", "SWOT", "会計", "サービスマネジメント", "ＩＴサービス", "ITサービス", "サービスデスク", "監査", "システム監査", "情報システム開発", "テスト", "オブジェクト指向", "UML", "要件定義", "財務", "事業", "投資", "SLA", "運用"]
# 出題趣旨の冒頭(第1文)は分野名を明示することが多いので重み付けする
Q_RE = re.compile(r"^\s*問\s*(\d+)\s*$", re.M)


def norm(t):
    return unicodedata.normalize("NFKC", t)


def split_by_q(text):
    """'問N' 見出しでテキストを分割し {N: 本文} を返す。"""
    text = norm(text)
    ms = list(Q_RE.finditer(text))
    out = {}
    for i, m in enumerate(ms):
        body = text[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(text)]
        out.setdefault(int(m.group(1)), body)
    return out


def shushi(body):
    m = re.search(r"出題趣旨(.*?)設問", body, re.S)
    return re.sub(r"\s+", "", m.group(1)) if m else ""


def classify(s):
    scores = {}
    for key, (_, kws) in SUBJECTS.items():
        scores[key] = sum(s.count(k) * (3 if k in s[:60] else 1) for k in kws)
    other = sum(s.count(k) * (3 if k in s[:60] else 1) for k in OTHER)
    best = max(scores, key=scores.get)
    return (best if scores[best] > other and scores[best] > 0 else None), scores, other


def pdf_text(path):
    return "".join(p.get_text() for p in pymupdf.open(path))


if __name__ == "__main__":
    import sys
    pdf = Path(sys.argv[1])
    for f in sorted(pdf.glob("*_ap_pm_ans.pdf")):
        ex = f.name.split("_")[0]
        for q, body in split_by_q(pdf_text(f)).items():
            s = shushi(body)
            k, sc, o = classify(s)
            print(f"{ex}\t問{q}\t{k}\t{o}\t{s[:70]}")
