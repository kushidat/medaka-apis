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
  "row_count": 2,
  "rows": [
    {
      "s": "実際のSPARQL結果の subject URI（例）",
      "p": "実際のSPARQL結果の predicate URI（例）",
      "o": "実際のSPARQL結果の object 値（URIまたはリテラル）"
    },
    {
      "s": "http://example.org/resource/2",
      "p": "http://example.org/property/name",
      "o": "sample literal"
    }
  ]
}
```

### テキスト形式（TSV）
```
<subject_URI_1>	<predicate_URI_1>	<object_1>
<subject_URI_2>	<predicate_URI_2>	<object_2>
```

## パラメータ説明

| パラメータ | 必須 | デフォルト | 説明 |
|----------|------|----------|------|
| `graph` | ✓ | - | named graph URI |
| `limit` | - | 500 | 取得行数の上限 |
| `offset` | - | 0 | スキップ行数 |