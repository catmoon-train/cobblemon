![](https://media.forgecdn.net/attachments/description/1189523/description_6488e172-95fe-46d0-b211-c47ba4ba1b76.png)
![](https://media.forgecdn.net/attachments/description/1189523/description_b45b4497-b99b-478b-bb78-816ecf83e727.png)

![](https://media.forgecdn.net/attachments/description/1189523/description_4bd2641e-5eea-4372-ad16-c23019a5a43e.png)
![](https://media.forgecdn.net/attachments/description/1189523/description_4b74b831-b235-42c6-ab80-34dd9c3f2ce1.png)

![](https://media.forgecdn.net/attachments/description/1189523/description_a2e4b377-84ff-4037-8f79-7e1a07b626ec.png)

---

## **Datapack Support**

![](https://media.forgecdn.net/attachments/description/1189523/description_97ed6f11-026f-449b-97ee-86e1500c2794.png)

You can datapack almost everything in this mod, including:

* Custom Megas
* Gigantamax (G-Max) forms
* Custom Pokémon types
* And much more

📖 Wiki:
[https://github.com/yajatkaul/CobblemonMegaShowdown/wiki](https://github.com/yajatkaul/CobblemonMegaShowdown/wiki)

---

## **Accessories Integration**

![](https://media.forgecdn.net/attachments/description/1189523/description_b8f1e56c-7f90-47dd-948c-e096d5b53918.png)

![](https://media.forgecdn.net/attachments/description/1189523/description_231b647f-88e3-485a-b07f-1ed063068956.png)

---

## **Features**

* Datapackable features
* Cosmetics support
* All form changes
* Riding supported
* All 48 Megas
* Accessories support
* Adds Primals
* Adds battle mechanics:

  * Tera gimmick
  * Mega Evolution
  * Z-Moves
  * Dynamax
  * Ultra Burst
* All fusion Pokémon

---

## **Credits**

All credits and model usage details are listed here:
👉 [https://docs.google.com/spreadsheets/d/1VPRia2W_7wqhbwSGv1845qmXw_FtjZ4FDhr58fRZFSM/edit?usp=sharing](https://docs.google.com/spreadsheets/d/1VPRia2W_7wqhbwSGv1845qmXw_FtjZ4FDhr58fRZFSM/edit?usp=sharing)

---

## **Incompatibilities**

Known incompatible addons/datapacks:
👉 [https://docs.google.com/spreadsheets/d/1pVLaT_dkQnQ2oO1IrJwf0RzkZNgqds2RMlYYOtqBVGg/edit?usp=sharing](https://docs.google.com/spreadsheets/d/1pVLaT_dkQnQ2oO1IrJwf0RzkZNgqds2RMlYYOtqBVGg/edit?usp=sharing)

---

## **Socials**

This mod includes all the megas that exist. For any help or questions, you can join my Discord:

[![Join us on Discord](https://substackcdn.com/image/fetch/w_1456,c_limit,f_auto,q_auto\:good,fl_progressive\:steep/https://substack-post-media.s3.amazonaws.com/public/images/8a41e45e-aac9-44e5-8b69-55a81058ecbf_875x280.png)](https://discord.gg/egeWG4GXhN)


## Local Fabric source import

Complete upstream source/assets import, **1.3.3+1.8.4+1.21.1-release**, for Minecraft 1.21.1 and Cobblemon 1.8.4.
Common/Fabric and generated data are built together; NeoForge source remains intact but is not configured.
No gameplay source, mixin, or original resource was edited except the riding compatibility merge described below.
See `PROVENANCE.md`, `UPSTREAM-MANIFEST.json`, and the unchanged `LICENSE.md`.

### Riding compatibility merge (required by the train Cobblemon build)

Mega ships complete `data/cobblemon/species/*` files for the species it touches, so those files replace core
species data instead of extending it. Without a merge, the 1.8.4 native riding fixes (driver + passenger seats,
extra riding modes, legacy `pokemonRideConfig.json` conversion) were silently reverted for these species.

Only `generation1/blastoise`, `generation1/charizard`, `generation1/lapras`, `generation3/metagross`,
`generation3/swampert`, `generation8a/ursaluna` changed: the top-level `riding` block (and the same-named form
riding blocks) now come from the Cobblemon build in this workspace. Every other field - stats, moves, evolutions,
abilities, spawn data, drops, form lists - is byte-identical to upstream (verified by a JSON diff that ignores
`riding`). `ursaluna` form `Bloodmoon` keeps its upstream zero seats because its model has no seat locator; this
limit is recorded in `verification/riding-merge.json`.

Reproduce the merge (read-only on the core build, in-place on this module):

```bash
python -X utf8 "$PI_SCRATCH_DIR/merge_mega_riding.py" \n  --core "<workspace>/common/src/main/resources" \n  --mega "<workspace>/sre-addons/mega-showdown/common/src/main/resources" \n  --report "<workspace>/sre-addons/mega-showdown/verification/riding-merge.json"
```
No publication, deployment, commit, resource split, or feature removal was performed.

### Reproduce (Windows Git Bash, from this module directory)

Use Java 21 and the **named/Mojang-mapped dev-shadow** Cobblemon API, never its production/intermediary jar for compilation.
Copy into the H: scratch build directory, excluding caches:

```bash
export JAVA_HOME='C:/Program Files/Zulu/zulu-21'
export PATH="$JAVA_HOME/bin:$PATH"
export GRADLE_USER_HOME='H:/gradle-home'
export GRADLE_RO_DEP_CACHE='C:/Users/canyuesama/.gradle/caches'
export BUILD_ROOT="$PI_SCRATCH_DIR/addons-work/mega-showdown"
export COBBLEMON_NAMED_JAR="$PI_SCRATCH_DIR/cobblemon-1.8.4-upstream/fabric/build/libs/Cobblemon-fabric-1.8.4+1.21.1-dev-shadow.jar"
python -X utf8 - <<'COPY'
import os, shutil
shutil.copytree('.', os.environ['BUILD_ROOT'], dirs_exist_ok=True, ignore=shutil.ignore_patterns('.git', '.gradle', '.idea', 'build', 'run', '.architectury-transformer', '.kotlin', 'bin', '.env', '.cache'))
COPY
set -o pipefail
bash ./gradlew -p "$BUILD_ROOT" :fabric:clean :fabric:remapJar -PcobblemonNamedJar="$COBBLEMON_NAMED_JAR" -Dfabric.loom.ci=true -Pkotlin.incremental=false --max-workers=2 --no-daemon --console=plain -Dorg.gradle.internal.http.connectionTimeout=15000 -Dorg.gradle.internal.http.socketTimeout=15000 2>&1 | tee "$PI_SCRATCH_DIR/mega-showdown-build-final.log"
```

The wrapper pins Gradle 8.14.3. Build properties cap heap at 3 GiB/workers at 2 and disable Kotlin incremental compilation with in-process compilation.
Fixed plugins: Loom 1.11.458, Architectury 3.4.164, Kotlin 2.2.20, Shadow 8.1.1.
The verified build used the equivalent preinstalled Gradle binary at `H:/gradle-home/wrapper/dists/gradle-8.14.3-bin/cv11ve7ro1n3o1j4so8xd9n66/gradle-8.14.3/bin/gradle`.
Online resolution can be necessary on a cold cache; Cobblemon snapshot resolution is not used.

Output: `$BUILD_ROOT/fabric/build/libs/mega_showdown-fabric-1.3.3+1.8.4+1.21.1-release.jar`.
An identical production jar is retained in this module's `fabric/build/libs/`. Do not install `-dev-shadow.jar`.
Final log: `verification/fabric-remapJar.log`; machine-readable outcome/hashes: `verification/result.json`.

### Dependencies

- Minecraft 1.21.1, Java 21, Fabric Loader 0.17.3.
- Fabric API 0.116.7+1.21.1.
- Cobblemon Fabric 1.8.4+1.21.1 (full production jar at runtime).
- Architectury API 13.0.8 (common/Fabric).
- Fabric Language Kotlin 1.13.7+kotlin.2.2.21.
- Accessories 1.1.0-beta.52+1.21.1 (common/Fabric).
- owo-lib: Accessories requires >=0.12.15.1+1.21; install an MC 1.21.1-compatible release.
- Jade 15.10.5+fabric: retained upstream compilation/development dependency for Jade integration, not bundled.
- Graal SDK `org.graalvm.sdk:graal-sdk:22.3.0`: compile-only, restoring missing local-jar Maven metadata; Cobblemon already bundles Graal SDK/JS/Regex/Truffle at runtime.

Mod dependencies are not bundled into Mega Showdown. Original entrypoints/dependency metadata remain intact.
Unused dotenv/release-upload integration is omitted. Fabric version expansion now preserves JSON escapes, avoiding upstream's invalid literal newlines in `fabric.mod.json`.

### Verified outcome and limits

`:fabric:remapJar` succeeded against the real local Cobblemon API; no API errors remain.
Production jar: 295 classes; all 4,123 common main resources, 610 generated resources, and 2 Fabric resources are present; `fabric.mod.json` parses as strict JSON.
All original gameplay source and resource bytes, including unconfigured NeoForge sources, are unchanged.
No game/client/server launch or gameplay test was run. Gradle 9 deprecation warnings do not prevent the pinned Gradle 8 build.
Upstream permission requirements for public derivatives, redistribution, assets, and commercial usage remain applicable; this import does not relicense anything.
