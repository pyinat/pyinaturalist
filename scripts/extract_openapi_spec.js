// Extract OpenAPI spec from v2 API (embedded in swagger-ui-init.js)
// Usage: node scripts/extract_openapi_spec.js > openapi_spec_v2.json
const url = process.argv[2] || 'https://api.inaturalist.org/v2/docs/swagger-ui-init.js';

fetch(url)
  .then(res => res.text())
  .then(js => {
    const match = js.match(/"swaggerDoc":\s*(\{)/);
    let start = match.index + match[0].length - 1;
    let braces = 0, inString = false, escape = false;

    for (let i = start; i < js.length; i++) {
      if (escape) { escape = false; continue; }
      if (js[i] === '\\') { escape = true; continue; }
      if (js[i] === '"' && !escape) { inString = !inString; continue; }
      if (inString) continue;
      if (js[i] === '{') braces++;
      if (js[i] === '}' && --braces === 0) {
        const spec = JSON.parse(js.slice(start, i + 1));
        console.log(JSON.stringify(spec, null, 2));
        return;
      }
    }
  });
