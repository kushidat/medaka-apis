# medaka_sample_by_graph
指定グラフからトリプルをサンプル取得（構造確認用）

## Parameters
* `graph` （必須。named graph URI を指定）
  * 例: `http://metadb.riken.jp/db/medaka_test`
* `limit` （任意, default 500）
* `offset`（任意, default 0）

## Endpoint
https://knowledge.brc.riken.jp/sparql

## `query`
```sparql
SELECT ?s ?p ?o
FROM <{{graph}}>
WHERE {
  ?s ?p ?o .
}
{{#if limit}}
LIMIT {{limit}}
{{else}}
LIMIT 500
{{/if}}
{{#if offset}}
OFFSET {{offset}}
{{else}}
OFFSET 0
{{/if}}
```

## Output
```javascript
({
  json({query, graph, limit, offset}) {
    return {
      graph: (graph || '').trim(),
      limit: limit ? Number(limit) : 500,
      offset: offset ? Number(offset) : 0,
      row_count: query.results.bindings.length,
      rows: query.results.bindings.map((r) => ({
        s: r.s?.value ?? null,
        p: r.p?.value ?? null,
        o: r.o?.value ?? null
      }))
    };
  },
  text({query}) {
    return query.results.bindings.map((r) =>
      [r.s?.value ?? '', r.p?.value ?? '', r.o?.value ?? ''].join('\t')
    ).join('\n');
  }
})
```
