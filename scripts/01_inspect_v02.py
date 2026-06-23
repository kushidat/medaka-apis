#!/usr/bin/env python3
# v0.2: 遺伝子系グラフ（5本）の「述語頻度」と「代表サンプル」を取得して中身を確認する。
# 使い方: python3 scripts/01_inspect_v02.py
# 出力をそのまま貼り、テーブル設計（1-3）の根拠にする。
#
# 対象グラフ（v0.2）:
#   - medaka_ncbigeneMedaka
#   - medaka_ncbigeneHuman_usingNcbigene
#   - medaka_nlmNcbigeneHuman_usingNcbigene
#   - medaka_medakaEnsemblGene
#   - medaka_ensembl_entrezGene_mapping
#
# 注意: 述語頻度は COUNT を使う。大きいグラフで遅い/タイムアウトする場合は
#       SAMPLE_LIMIT ベースの軽い版に切り替えて再実行すること。

import json
import sys
import urllib.parse
import urllib.request

SPARQL = "https://knowledge.brc.riken.jp/sparql"
NS = "http://metadb.riken.jp/db"

GRAPHS = [
    "medaka_ncbigeneMedaka",
    "medaka_ncbigeneHuman_usingNcbigene",
    "medaka_nlmNcbigeneHuman_usingNcbigene",
    "medaka_medakaEnsemblGene",
    "medaka_ensembl_entrezGene_mapping",
]

SAMPLE_LIMIT = 30


def run(query):
    params = urllib.parse.urlencode({"query": query})
    url = f"{SPARQL}?{params}"
    req = urllib.request.Request(
        url, headers={"Accept": "application/sparql-results+json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def predicate_freq(iri):
    q = (
        f"SELECT ?p (COUNT(*) AS ?n) WHERE {{ GRAPH <{iri}> {{ ?s ?p ?o }} }} "
        f"GROUP BY ?p ORDER BY DESC(?n)"
    )
    data = run(q)
    return [(b["p"]["value"], b["n"]["value"]) for b in data["results"]["bindings"]]


def sample(iri, limit=SAMPLE_LIMIT):
    q = f"SELECT ?s ?p ?o WHERE {{ GRAPH <{iri}> {{ ?s ?p ?o }} }} LIMIT {limit}"
    data = run(q)
    return [
        (b["s"]["value"], b["p"]["value"], b["o"]["value"])
        for b in data["results"]["bindings"]
    ]


for g in GRAPHS:
    iri = f"{NS}/{g}"
    print("=" * 100)
    print(f"GRAPH: {g}   <{iri}>")
    print("=" * 100)
    try:
        print("\n-- 述語頻度 (count / predicate) --")
        for p, n in predicate_freq(iri):
            print(f"{n:>12}  {p}")

        print(f"\n-- 代表サンプル s/p/o (最大{SAMPLE_LIMIT}件) --")
        for s, p, o in sample(iri):
            print(f"  S: {s}")
            print(f"  P: {p}")
            print(f"  O: {o}")
            print("  -")
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  (このグラフでエラー。出力ごと貼ってください。)")
    print()
