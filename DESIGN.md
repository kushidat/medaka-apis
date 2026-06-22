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

**科学的な狙い（なぜこのデータを配るか）**：疾患研究に使えるメダカ（ヒト疾患モデル候補）を、
次の2経路で推定できるようにすることが目的の1つ。配布データは、この2経路を
SQLの結合（join）でたどれる状態にして渡す。
- 経路A（遺伝子のつながり）：メダカ系統 → メダカ遺伝子 → ヒト遺伝子（オルソログ）→ ヒト疾患。
  `medaka_diseaseID_throughMedgen_direct` がこの経路で推定したメダカ–ヒト疾患関係。
- 経路B（表現型の類似度）：メダカの表現型 ↔ ヒト疾患の表現型 のコサイン類似度。
  `medaka_disease_similarityScore` がこの経路で推定したメダカ–ヒト疾患関係。

`medaka_test`（メダカ系統メタデータ）が両経路の起点（アンカー）。

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
- グラフIRI（SPARQLの `GRAPH <...>` で使う名前）：`http://metadb.riken.jp/db/<graph>`
  （研究室提供のグラフリストのIRIに一致）。
  `https://knowledge.brc.riken.jp/bioresource/upload/db/<graph>` は**アップロード先**であって、
  クエリ用のグラフIRIではない。
  - Day0 の疎通確認で `http://metadb.riken.jp/db/<graph>` が応答することを実機で最終確認する。
- ライセンス：**CC BY**（配布物に出典・グラフIRI・取得日を必ず明記）

---

## 3. 配布対象グラフの確定

研究室提供のグラフリスト（`medaka_graph.txt`）に基づく**実体13本**と、配布要否の方針。
列「経路」は0章の経路A（遺伝子）/B（表現型）との対応。

| グラフ | 内容（提供者説明） | 経路 | 配布 | 方針・理由 |
|---|---|---|---|---|
| `medaka_test` | メダカ系統のメタデータ（系統・表現型注釈。zp=ZF表現型, za=ZF解剖学的部位） | 起点 | ○ | 全経路のアンカー（メダカ系統エンティティ） |
| `medaka_zp` | メダカ→ZF表現型の関係（Monarch gene_to_phenotypic_feature 由来） | B | ○ ※ | 表現型経路の素データ。**【要確認】**配布するか中間データ扱いか |
| `medaka_hp` | メダカ→ヒト表現型の関係（upheno.owl のZF↔ヒト表現型マッピング由来） | B | ○ | 表現型経路 |
| `medaka_medakaEnsemblGene` | メダカ→メダカEnsembl遺伝子（relatedGene） | A | ○ ※ | 遺伝子経路（Ensembl ID系）。**【要確認】**`ncbigeneMedaka`と統合か別建てか |
| `medaka_ensembl_entrezGene_mapping` | メダカ Ensembl ↔ Entrez(ncbigene) ID対応 | A補助 | △補助 | 共有ルックアップ表を1つ持ち、各遺伝子表からFK参照（列を増やさない） |
| `medaka_ncbigeneMedaka` | メダカ→メダカNCBI(Entrez)遺伝子 | A | ○ | 遺伝子経路（Entrez ID系） |
| `medaka_ncbigeneHuman_usingNcbigene` | メダカ→ヒト遺伝子(ncbigene) | A | ○ | 遺伝子経路。下の`nlm`版と**1テーブルに正規化** |
| `medaka_nlmNcbigeneHuman_usingNcbigene` | 同上。IRI接頭辞が違うだけ | A | ○ | 上と同一内容のID系違い。二重配布せず1テーブルに正規化 |
| `medaka_diseaseID_throughMedgen_direct` | 経路Aで推定したメダカ–ヒト疾患関係（ヒト遺伝子→ヒト疾患はMedGen由来。ordo/omim） | A | ○ | 中核（遺伝子経路の疾患関係） |
| `medaka_disease_similarityScore` | 経路Bで推定したメダカ–ヒト疾患関係（表現型コサイン類似度。疾患–表現型はHPO phenotype.hpoa由来） | B | ○ | 中核（表現型経路の疾患関係）。ordo/omim版の上位集合 |
| `medaka_ordo_similarityScore` | `medaka_disease_similarityScore` の部分集合（Orphanet分） | B | ✕除外 | 重複。上位集合を配布 |
| `medaka_omim_similarityScore` | 同・部分集合（OMIM分） | B | ✕除外 | 重複。上位集合を配布 |
| `medaka_medaka_similarityScore` | メダカ↔メダカの表現型類似度（似た表現型のメダカ） | B | ○ ※ | 表現型が似たメダカの探索。**【要確認】**配布対象に含めるか |

> ※印（`zp`, `medakaEnsemblGene`, `medaka_similarityScore`）は、DESIGN旧版に未記載だった4本のうちの判定保留分。
> Day0 で研究室として配布要否を確定する。残り1本 `nlmNcbigeneHuman` は `ncbigeneHuman` への正規化で吸収。

**結合の地図（どの列でSQL結合するか／実サンプルに基づく・創作なし）**
- **メダカ系統ID**（`http://lod.nbrp/Medaka/<id>`）が全グラフ共通の結合キー。
  ただしサンプルに `MT104` 形式と `337` 形式が混在 → **【要確認/Day1】** ID表記の正規化が必要。
- **遺伝子**：`ncbigene` ID（`identifiers.org/ncbigene/...`）が `ncbigeneMedaka`・`ncbigeneHuman` を結ぶ。
  `ensembl` ID（`ENSORLG...`）が `medakaEnsemblGene` を結び、`ensembl_entrezGene_mapping` が両者を橋渡し。
- **疾患**：ordo（Orphanet）/ omim ID が `diseaseID_throughMedgen_direct` と `disease_similarityScore` を結ぶ。
  → 経路Aと経路Bを「同じ疾患ID」で突き合わせれば、両経路が支持するメダカ–疾患関係を抽出できる。

> **【要確認】** 配布対象の最終確定（特に ※印3本）を Day0 冒頭で研究室として決める。
> Day1〜2 で短期完了するため、まずは**疾患推定の中核**（`medaka_test`, `medaka_disease_similarityScore`,
> `medaka_diseaseID_throughMedgen_direct`, `medaka_hp`）で v0.1 を切り、遺伝子系・補助は v0.2 に回してよい（後述 8章）。

---

## 3.5 類似度スコアグラフのRDFスキーマと素データ由来

研究室提供のスキーマ図（マウス版）と `medaka_graph.txt` のサンプルに基づく。述語が一致するためメダカも同型。

**`*_similarityScore` の reified スキーマ（1件の関係＝1つの association ノード）**
- association ノード
  - `sio:SIO_000628`（refers to）→ 対象メダカ（`http://lod.nbrp/Medaka/<id>`）
  - `sio:SIO_000628`（refers to）→ 疾患ID（ordo: `identifiers.org/orphanet/<id>` ／ omim: `purl.bioontology.org/ontology/OMIM/<id>`）
  - `sio:SIO_000216`（has measurement value）→ 指標ノード
- 指標ノード
  - `rdf:type` → 指標種別（例：`cosine_index_between_medaka_and_ordo`）
  - `sio:SIO_000300`（has value）→ スコア値（`xsd:float`）
- 指標はスキーマ図上 **Jaccard / Dice / Simpson / Cosine の4種**が定義されうる。
  メダカのサンプルはコサインのみ確認 → **【要確認/Day1】** メダカが実際に持つ指標を実データで確認。

**配布層テーブル設計（案・Day1で確定）**
`medaka_disease_similarityScore(medaka_id, medaka_label, disease_id, disease_source[ordo|omim], measure[jaccard|dice|simpson|cosine], score)`
／ PK=(medaka_id, disease_id, measure)。**measure 列**を持たせれば複数指標を1表に正規化でき、指標が増えても列が増えない。

**各グラフの素データ由来（`provenance.json` の根拠）**
- 遺伝子→表現型：モデル生物は各プロジェクト提供（zebrafish＝Monarch KG の `zfin_gene_to_phenotype`）。→ `medaka_zp` の素データ系。
- モデル生物表現型→ヒト表現型(HP)：uPheno（`upheno_all.owl`）等のマッピング。→ `medaka_hp` の素データ系。
- HP→疾患：`hpoa`（`hpoa_disease_phenotype`, Monarch KG）。→ `medaka_disease_similarityScore` の疾患–表現型側。

> スコープ注記：スキーマ検討図には Mouse/Rat や MA/ZFA/Uberon など **medaka-apis の範囲外**の要素も含まれる。
> これらは背景文脈であり、配布対象には入れない。

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
遺伝子系・表現型素データ（`medaka_ncbigeneMedaka`, `ncbigeneHuman`(+`nlm`版を正規化),
`medakaEnsemblGene`, 共有 `ensembl_entrezGene_mapping`, `medaka_zp`, `medaka_medaka_similarityScore`）は
v0.2 以降に回す。これでDay2公開を確実にできる。

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
