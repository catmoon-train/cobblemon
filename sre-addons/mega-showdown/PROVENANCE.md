# Mega Showdown import provenance

- Read-only source snapshot: `G:/download/CobblemonMegaShowdown-main`.
- Upstream: https://github.com/yajatkaul/CobblemonMegaShowdown
- Author: Yajat Kaul / YajatKaul; contributor: Provismet. Original README and asset credits remain intact.
- Version: `1.3.3+1.8.4+1.21.1-release`; Minecraft 1.21.1; Cobblemon 1.8.4.
- No source `.git` metadata was supplied; no upstream commit identity is claimed.
- `UPSTREAM-MANIFEST.json` contains every imported original file's SHA-256 before local edits.
- LICENSE.md is preserved byte-for-byte: Mega Showdown License v2.1, with distinct asset terms and publication/commercial permission requirements. This import is not a relicensing.
- Local import/build only: no publication, upload, deployment, commit, resource split, or gameplay reduction.

## Exclusions

Only local/build/cache paths are excluded: `.git`, `.gradle`, `.idea`, `build`, `run`, `.architectury-transformer`, `.kotlin`, `bin`, `.env`, `.cache`.
Common, Fabric, NeoForge, generated resources, licenses, changelog, wrapper, CI metadata, all sources and assets are retained.

## Minimal local changes

1. `build.gradle`: fixed Loom/Architectury/Kotlin releases; omit dotenv and release-upload integration; restrict Fabric dependency repositories; validate/use the explicit named Cobblemon API as compile-only files.
2. `settings.gradle`: configure only common/Fabric; retain NeoForge files but do not resolve that platform; omit unused dotenv plugin mapping.
3. `gradle.properties`: Fabric-only platforms; heap <=3 GiB; <=2 workers; Kotlin incremental off/in-process. Mod and runtime dependency versions remain unchanged.
4. `gradle/wrapper/gradle-wrapper.properties`: Gradle 8.14.3.
5. `common/build.gradle`: unavailable Cobblemon Maven coordinate replaced by root's local named API dependency.
6. `fabric/build.gradle`: same local API replacement; compile-only Graal SDK 22.3.0 restores the relevant lost POM dependency; preserve JSON escapes during metadata expansion.
7. `README.md`: append reproducible local commands, dependencies, results, and limits; retain all original text/credits.
8. Add this provenance, the original SHA-256 manifest, verification records, and the production jar separately from caches.

No original Java/Kotlin, mixin source, generated data, resource, or license was edited. Runtime dependencies are not packaged into Mega Showdown.

## Riding merge

6 species files changed only in `riding` blocks to carry the native 1.8.4 riding data rebuilt in this workspace;
no other gameplay byte changed. See README section "Riding compatibility merge" and `verification/riding-merge.json`.
