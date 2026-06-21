# medaka-apis 配布プロジェクト 設計ドキュメント兼スケジュール

> このファイルの用途：Claude（または他LLM）のProjectに「常駐知識」として固定し、
> 毎回これを文脈に置いて作業する。目的のドリフト（READMEの体裁磨きへの没入など）を防ぐための
> 唯一の基準ドキュメントとする。
>
> 配置：この1ファイルを2か所に置く。(1) ClaudeのProjectに常駐知識としてアップロード、
> (2) リポジトリ `kushidat/medaka-apis` のルートに **`DESIGN.md`** という名前で保存（`git add DESIGN.md`）。
> 本文中の `DESIGN.md` はこのファイル自身（=ダウンロードした `medaka-apis_設計とスケジュール.md`）を指す。別ファイルではない。
>
> 記載ルール：確定していない事項は **【要確認】** と明記する。推測で埋めない。

---

## 0. プロジェクト目的（固定・最重要）

理研BioResourceのメダカ（*Oryzias latipes*）関連 **RDF知識グラフ** から、
**メダカとヒト疾患・遺伝子・表現型の関係データ** を抽出し、
**RDFを知らない外部研究者が、自分のリレーショナルDB（RDB）にロードしてSQLで正しく扱える形**
（CSV / TSV / JSON ＋ スキーマ定義 ＋ 用語辞書 ＋ 由来情報）で配布する。

成果は「mdテンプレートを作ること」でも「READMEを綺麗にすること」でもない。
**意味（semantic）と結合キー（join key）が分かる配布データ一式を、SQLで使える状態で公開すること** が完了条件。

---

## 1. 成果物（配布物）の定義

配布対象グラフごとに、以下を生成して GitHub Release で公開する。

| 区分 | ファイル | 内容 | RDB初心者向けの役割 |
|---|---|---|---|
| 監査層 | `data/raw/<graph>_triples.tsv` | s, p, o, graph の生トリプル | 再現性・監査用（通常は使わない） |
| 配布層 | `data/curated/<graph>.csv` (.tsv/.json) | グラフごとに**意味のある列名・キー**で整形した表 | これをDBにロードしてSQLで使う |
| 定義 | `schema/<graph>.schema.sql` | `CREATE TABLE` DDL（列名・型・PK/FK・索引） | そのままDBに流して表を作れる |
| 辞書 | `metadata/codebook.csv` | 列定義（テーブル名・列名・型・意味・例・備考） | 各列が何を表すかの説明書 |
| 辞書 | `metadata/predicate_catalog.csv` | 述語一覧（IRI・出現頻度・意味・想定型） | 元RDFの述語と列の対応 |
| 由来 | `metadata/provenance.json` | endpoint・graph IRI・実行SPARQL・取得日時・件数 | いつ何を取ったかの記録 |
| 台帳 | `metadata/manifest.csv` | file, source_graph, version, row_count, sha256, status(new/unchanged) | 段階公開で何が新規か据え置きかの真実の源（重複防止） |
| 整合 | `SHA256SUMS` | 各ファイルのハッシュ | 改ざん・破損チェック |
| 説明 | `README.md`（最小限） | 使い方・ロード手順・ライセンス・引用方法 | 入口 |

**配布層テーブルの設計方針（共通）**
- 機械IDと人間可読ラベルを**両方**持つ（例：`subject_id`＋`subject_label`）。
- 主キー（PK）と結合キー（FK）を必ず定義する（テーブル間をSQLで結合できること）。
- 欠損は `NA` で統一。
- スコア系の列は**尺度の定義**を codebook に明記（範囲・意味）。比較解釈の前提を残す。
- 文字コードは UTF-8、改行は LF に統一。
- **列定義は「データの中身を見てから」確定する**（後述 Day1。今は invented しない）。

---

## 2. データソース（確定情報）

- SPARQLエンドポイント：`https://knowledge.brc.riken.jp/sparql`
- SPARQList REST API：`https://splist.brc.riken.jp/sparqlist/`
  - 例：`medaka_sample_by_graph`（graph 指定でサンプル取得）, `bioresource_void`
- グラフIRIの形式：`http://metadb.riken.jp/db/<graph>` および
  `https://knowledge.brc.riken.jp/bioresource/upload/db/<graph>`
  - **【要確認】** 配布対象として正となるグラフIRI（上記どちらの名前空間か）を Day0 で1つに確定する。
- ライセンス：**CC BY**（配布物に出典・グラフIRI・取得日を必ず明記）

---

## 3. 配布対象グラフの確定

ユーザー（研究室）提供の各グラフの意味と、配布要否の方針。

| グラフ | 内容（提供者説明） | 配布 | 方針・理由 |
|---|---|---|---|
| `medaka_test` | 実験用メダカのメタデータ。zp=ゼブラフィッシュ表現型, za=同・解剖学的部位 | ○ | 中核メタデータ |
| `medaka_disease_similarityScore` | メダカ–表現型, ヒト疾患(ordo,omim)–表現型 の**類似度**で推測したメダカ–ヒト疾患関係。疾患–表現型はHPO(phenotype.hpoa)由来 | ○ | 中核。ordo/omim版の上位集合 |
| `medaka_diseaseID_throughMedgen_direct` | メダカ–メダカ遺伝子, メダカ遺伝子–ヒト遺伝子, ヒト遺伝子–ヒト疾患 から推測したメダカ–ヒト疾患関係 | ○ | 中核（別経路の疾患関係） |
| `medaka_hp` | メダカ–ヒト表現型の関係。ZF表現型–ヒト表現型マッピング(upheno.owl)由来 | ○ | 中核（表現型） |
| `medaka_ncbigeneMedaka` | メダカ–メダカNCBI遺伝子の関係（改変メダカと改変遺伝子など） | ○ | 中核（遺伝子） |
| `medaka_ncbigeneHuman_usingNcbigene` | メダカと関係するヒト遺伝子(ncbigene) | ○（要正規化） | **【要確認】** IRIプレフィックス違いの2系統あり。1テーブルに正規化するか別列で持つか Day1 で決定 |
| `medaka_ensembl_entrezGene_mapping` | メダカ Ensembl ↔ Entrez 遺伝子IDのマッピング | △補助 | **【要確認】** 単独配布せず、遺伝子テーブルの結合補助として同梱が妥当か確認 |
| `medaka_ordo_similarityScore` | `medaka_disease_similarityScore` の**部分集合** | ✕除外 | 上位集合を配布するため重複。除外で合意済み |
| `medaka_omim_similarityScore` | 同上・部分集合 | ✕除外 | 同上 |

> **【要確認】** 上記の○印グラフが配布対象の最終確定でよいか、Day0 冒頭で研究室として確定する。
> Day1〜2 で短期完了するため、**まずは中核4〜5本に絞って公開し、補助は次バッチ**でもよい（後述 8章）。

---

## 4. リポジトリ構成

```
kushidat/medaka-apis/
├── README.md                     # 配布者向け・最小限
├── DESIGN.md                     # 本ドキュメント（基準・常駐知識）
├── queries/                      # グラフごとの抽出SPARQL（再現用）
│   ├── _00_full_sample.rq        # 全件 or 代表サンプル（中身確認用）
│   ├── _01_predicate_freq.rq     # 述語頻度
│   └── <graph>.rq                # 配布層抽出クエリ
├── scripts/
│   ├── extract.sh                # SPARQList/curl で抽出（バッチ）
│   └── build.py                  # JSON応答 → CSV/TSV/JSON/schema へ整形（バッチ）
├── data/
│   ├── raw/<graph>_triples.tsv
│   └── curated/<graph>.{csv,tsv,json}
├── schema/<graph>.schema.sql
├── metadata/{codebook.csv,predicate_catalog.csv,provenance.json}
└── SHA256SUMS
```

> **進め方の原則（前回の反省）**：1ターン1コマンドで刻まない。
> 「複数編集＋コミットを1本のスクリプトにまとめて」依頼し、**一括実行 → 最後に `git log`/`diff` を1回だけ確認**する。

---

## 5. 2日間（最長）タイムスケジュール

実行はローカル（`~/dev/github/kushidat/medaka-apis`）。LLMは設計・SPARQL/スクリプト生成・実出力の判定に使う。
各ステップに**判定可能な成功条件**を置く。完了したら次へ。

### Day 0 — 準備（目安 1時間）

| # | 作業 | 成功条件 |
|---|---|---|
| 0-1 | 配布対象グラフ（3章○印）と正となるグラフIRIを研究室として確定 | 対象グラフのリストとIRIが1枚に固定された |
| 0-2 | 本 `DESIGN.md` を repo ルートに置き、Project常駐知識に登録 | `git add DESIGN.md && commit && push` 完了 |
| 0-3 | `medaka_sample_by_graph` API で各対象グラフが応答するか疎通確認 | 全対象グラフで `rows` が返る（または不足を記録） |

### Day 1 — 中身の確認とテーブル設計（実装日）

| # | 作業 | 成功条件 |
|---|---|---|
| 1-1 | 各対象グラフを**全件 or 代表サンプル抽出**（`_00_full_sample.rq` / SPARQList）。中身を実際に見る | グラフごとに s/p/o の実例が手元にある |
| 1-2 | **述語頻度**を取得（`_01_predicate_freq.rq`）。どの述語が主軸か把握 | グラフごとに述語一覧＋件数が出た |
| 1-3 | 1-1/1-2 を根拠に、**グラフごとの配布層テーブルを設計**（意味のある列名・PK/FK・型）。`schema/<graph>.schema.sql` と `codebook.csv` に確定 | 各テーブルの列定義が確定し、創作なしで根拠（述語IRI）に紐づく |
| 1-4 | 抽出SPARQL（`<graph>.rq`）と整形スクリプト（`extract.sh`/`build.py`）を**1バッチ**で作成 | サンプル1グラフで CSV/TSV/JSON が生成できた |

> 1-3 がこのプロジェクトの本丸。**ここを飛ばして整形・公開に進まない。**
> ncbigeneHuman の2系統、ensembl↔entrez mapping の扱い（4本に絞るか）もここで決着させる。

### Day 2 — 生成・検証・公開

| # | 作業 | 成功条件 |
|---|---|---|
| 2-1 | 全対象グラフを `extract.sh`→`build.py` で**一括生成**（raw + curated + schema） | 全対象の data/ と schema/ が揃った |
| 2-2 | `codebook.csv` / `predicate_catalog.csv` / `provenance.json`（endpoint・graph・SPARQL・日時・件数）生成 | メタデータ4点が揃った |
| 2-3 | **検証**：件数一致、PK一意性、FK整合、NA統一、UTF-8/LF、`schema.sql`でテーブル作成→ロードが通る | 検証スクリプトが全項目PASS |
| 2-4 | `SHA256SUMS` 生成 | 全配布ファイルのハッシュ記録 |
| 2-5 | `README.md`（最小限）：用途・ロード手順例（`CREATE TABLE`＋`LOAD/COPY`）・列の見方・CC BY・引用テンプレ。**体裁磨きはしない** | 第三者がREADMEだけで1テーブルをDBにロードできる |
| 2-6 | **GitHub Release** で配布物一式を公開（タグ付け、CC BY明記） | Release URL が発行され、ダウンロードして検証2-3が再現する |

完了条件＝ **2-6 が満たされ、外部研究者がReleaseを落として `schema.sql` でテーブルを作り、curated データをロードしてSQLで結合クエリが書ける状態**。

---

## 6. 抽出SPARQLの出発点（テンプレート）

実際の列設計は Day1 の中身確認後に確定する。以下は**確認用の出発点**であり、これをそのまま配布層にしない。

```sparql
# _00_full_sample.rq : 中身確認（まず眺める）
SELECT ?s ?p ?o
FROM <GRAPH_IRI>
WHERE { ?s ?p ?o . }
LIMIT 1000
```

```sparql
# _01_predicate_freq.rq : 述語頻度（主軸の述語を知る）
SELECT ?p (COUNT(*) AS ?n)
FROM <GRAPH_IRI>
WHERE { ?s ?p ?o . }
GROUP BY ?p
ORDER BY DESC(?n)
```

> SPARQList API 経由なら `https://splist.brc.riken.jp/sparqlist/api/medaka_sample_by_graph?graph=<GRAPH_IRI>&limit=&offset=` を起点に、
> graph を必ず指定する（指定しないと他グラフが100件以上混ざる、と確認済み）。

---

## 7. やらないこと（スコープ外・ドリフト防止）

- README の目次・空行・末尾改行・見出し和訳などの**体裁磨き**を作業項目にしない（最後にまとめて1回）。
- 配布対象でないグラフ（ordo/omim similarity）への作業。
- データの中身を見る前のテーブル列の創作・仮置き。
- 1ターン1コマンドの逐次実行（バッチにまとめる）。
- 「実行していないのに完了報告」。完了は **実出力（件数・SHA・Release URL）** でのみ宣言する。

---

## 8. 短縮オプション（2日が厳しい場合）

優先度順に**中核4本**（`medaka_test`, `medaka_disease_similarityScore`,
`medaka_diseaseID_throughMedgen_direct`, `medaka_hp`）だけで先にRelease（v0.1）し、
遺伝子系（`medaka_ncbigeneMedaka`, `ncbigeneHuman`, `ensembl_entrezGene_mapping`）は v0.2 に回す。
これでDay2公開を確実にできる。

> **【要確認】** v0.1 を中核4本で切るか、遺伝子系まで含めて一括公開するか。

---

## 9. 段階公開と重複防止ポリシー

段階公開（v0.1, v0.2 …）で**ファイルと作業が重複しない**ための規則。重複には「データの重複」と
「作業・ファイルの重複」の2種類があり、対策が異なる。

**データの重複は正規化で消す**
- `medaka_ordo_similarityScore` / `medaka_omim_similarityScore` は `disease_similarityScore` の部分集合 → 配布しない（合意済み）。
- `ncbigeneHuman` の2系統（IRIプレフィックス違い）→ **1テーブルに正規化**。同じヒト遺伝子を二重に配布しない。
- `ensembl ↔ entrez` mapping は各遺伝子テーブルに列を増やさず、**共有ルックアップ表を1つ**持ち FK で参照する。

**作業・ファイルの重複は「追加のみのリリース」で防ぐ**
1. **1グラフ＝1配布ファイル＝固定名**。テーブルは元グラフと1対1。リリースをまたいでファイルを分割・改名しない。
2. 新リリースは原則 **ファイルを追加するだけ**。v0.2 は v0.1 のファイルを作り直さず、新規分のみ生成する。
3. **リポジトリをgitで単一のソース**として管理し、各 Release は「その時点のスナップショット＋新規ファイル一覧」を示すだけにする。
4. パイプライン（`extract.sh`/`build.py`）は**設定駆動・冪等**にする。「どのグラフをどのバージョンで出すか」の一覧を持ち、再実行しても未生成分だけを作る（完成済みの作り直しを発生させない）。
5. `metadata/manifest.csv` を**真実の源**とし、毎回 status(new/unchanged) を機械的に判定して二重公開を検知する。
6. スキーマ変更が必要なときだけバージョンを上げ、`codebook.csv` と changelog に記録する（既存テーブルの破壊的変更は避ける）。

**段階公開の推奨単位**：v0.1＝中核4本（`medaka_test`, `medaka_disease_similarityScore`,
`medaka_diseaseID_throughMedgen_direct`, `medaka_hp`） → v0.2＝遺伝子系（`medaka_ncbigeneMedaka`,
`ncbigeneHuman`, 共有 `ensembl_entrezGene_mapping`）。各リリースは manifest に追記され、既存ファイルは unchanged のまま据え置く。
