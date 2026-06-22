#!/usr/bin/env bash
# Day0 疎通確認 / connectivity check
# 目的: 各候補グラフが応答するか、2つのIRI名前空間のどちらが有効かを確認する。
# 使い方: bash 00_check_graphs.sh
# 出力: graph / namespace / responds(yes/no) / http の表。結果を貼って判定に使う。

set -uo pipefail

SPARQL="https://knowledge.brc.riken.jp/sparql"

# 候補グラフ（研究室提供リストの実体13本）
graphs=(
  medaka_test
  medaka_zp
  medaka_hp
  medaka_medakaEnsemblGene
  medaka_ensembl_entrezGene_mapping
  medaka_ncbigeneMedaka
  medaka_ncbigeneHuman_usingNcbigene
  medaka_nlmNcbigeneHuman_usingNcbigene
  medaka_diseaseID_throughMedgen_direct
  medaka_ordo_similarityScore
  medaka_omim_similarityScore
  medaka_medaka_similarityScore
  medaka_disease_similarityScore
)

# 試す2つの名前空間（どちらが正かをここで判定する）
namespaces=(
  "http://metadb.riken.jp/db"
  "https://knowledge.brc.riken.jp/bioresource/upload/db"
)

printf "%-42s %-58s %-9s %-5s\n" "graph" "namespace" "responds" "http"
printf '%.0s-' {1..118}; echo

for g in "${graphs[@]}"; do
  for ns in "${namespaces[@]}"; do
    iri="$ns/$g"
    query="SELECT ?s ?p ?o WHERE { GRAPH <$iri> { ?s ?p ?o } } LIMIT 1"
    resp=$(curl -s -m 30 -w $'\n%{http_code}' -G "$SPARQL" \
      --data-urlencode "query=$query" \
      -H "Accept: application/sparql-results+json")
    http=$(printf '%s' "$resp" | tail -n1)
    body=$(printf '%s' "$resp" | sed '$d')
    # bindings 配列に要素があれば応答ありと判定（簡易ヒューリスティック）
    if printf '%s' "$body" | tr -d '[:space:]' | grep -q '"bindings":\[{'; then
      responds="yes"
    else
      responds="no"
    fi
    printf "%-42s %-58s %-9s %-5s\n" "$g" "$ns" "$responds" "$http"
  done
done
