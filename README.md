# medaka-apis

Medaka向けSPARQL APIテンプレート集です。

## Files
- [`medaka_sample_by_graph.md`](./medaka_sample_by_graph.md)
  - 指定した named graph からトリプルをサンプル取得するテンプレート

## 使い方

### 実行例
```bash
curl -X POST "https://knowledge.brc.riken.jp/sparql" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "query=SELECT%20%3Fs%20%3Fp%20%3Fo%20FROM%20%3Chttp%3A%2F%2Fmetadb.riken.jp%2Fdb%2Fmedaka_test%3E%20WHERE%20%7B%3Fs%20%3Fp%20%3Fo%20.%7D%20LIMIT%20500"
```

### レスポンス例（JSON）
```json
{
  "graph": "http://metadb.riken.jp/db/medaka_test",
  "limit": 500,
  "offset": 0,
  "row_count": 3,
  "rows": [
    {
      "s": "http://example.org/medaka/gene/001",
      "p": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
      "o": "http://example.org/Gene"
    },
    {
      "s": "http://example.org/medaka/gene/001",
      "p": "http://example.org/name",
      "o": "gene_name_001"
    },
    {
      "s": "http://example.org/medaka/gene/001",
      "p": "http://example.org/description",
      "o": "Description of gene 001"
    }
  ]
}
```

### テキスト形式（TSV）
```
http://example.org/medaka/gene/001	http://www.w3.org/1999/02/22-rdf-syntax-ns#type	http://example.org/Gene
http://example.org/medaka/gene/001	http://example.org/name	gene_name_001
http://example.org/medaka/gene/001	http://example.org/description	Description of gene 001
```

## パラメータ説明

| パラメータ | 必須 | デフォルト | 説明 |
|----------|------|----------|------|
| `graph` | ✓ | - | named graph URI |
| `limit` | - | 500 | 取得行数の上限 |
| `offset` | - | 0 | スキップ行数 |
