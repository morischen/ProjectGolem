// Generate TypeScript types from contracts/*.schema.json (TS half of ADR-0004).
// Output (src/*.ts) is committed and must not be hand-edited; edit the schema and
// rerun `pnpm gen:contracts`. json-schema-to-typescript formats output via prettier.
import { compileFromFile } from "json-schema-to-typescript";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const contractsDir = resolve(here, "../../../../contracts");
const outDir = resolve(here, "../src");
const schemas = ["evidence", "verdict", "claim"];

await mkdir(outDir, { recursive: true });

const indexLines = [];
for (const name of schemas) {
  const ts = await compileFromFile(
    resolve(contractsDir, `${name}.schema.json`),
    {
      bannerComment: `/* generated from contracts/${name}.schema.json — DO NOT EDIT (ADR-0004) */`,
      additionalProperties: false,
    },
  );
  await writeFile(resolve(outDir, `${name}.ts`), ts);
  indexLines.push(`export * from "./${name}";`);
}
await writeFile(resolve(outDir, "index.ts"), indexLines.join("\n") + "\n");

console.log(`Generated ${schemas.length} contract modules into ${outDir}`);
