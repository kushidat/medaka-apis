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
  --data-urlencode "query=SELECT ?s ?p ?o FROM <http://metadb.riken.jp/db/medaka_test> WHERE { ?s ?p ?o . } LIMIT 500"
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

## 注意事項

- `rows[].o` は **URI の場合**と **リテラルの場合**があります。
- 本テンプレートの `rows` は `query.results.bindings` をそのまま整形して返すため、値はグラフ内容に依存します。
- `row_count` は取得件数（`rows.length`）です。
## Changelog

- 2026-06-21: レスポンス例を「実データ依存」の説明に修正。
- 2026-06-21: `rows[].o` が URI / リテラル両対応である注意事項を追加。
- 2026-06-21: TSV例をタブ区切り前提に修正。
- 2026-06-21: README先頭の不要な空行を削除。
- 2026-06-21: `medaka_sample_by_graph.md` に出力注意事項を追記。
- 2026-06-21: curl実行例を `--data-urlencode` 使用の可読版に変更。

## HTTPステータスとエラーレスポンス

- `200 OK`: 正常終了（`rows`, `row_count` を返却）
- `400 Bad Request`: 必須パラメータ不足・不正（例: `graph` 未指定）
- `502 Bad Gateway`: 上流SPARQLエンドポイント異常
- `500 Internal Server Error`: その他の予期しない例外

### エラーレスポンス例（JSON）
```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "graph parameter is required"
  }
}
