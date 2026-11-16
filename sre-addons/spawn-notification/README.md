# Cobblemon Spawn Notification — Fabric 1.21.1 / Cobblemon 1.8.4 移植

独立模块，不接入或修改 Cobblemon 根项目的 settings/build。Java 21，Mojmap 编译、intermediary 发布。
上游模组 ID `cobblemon_spawn_notification`、资源/配置命名空间 `spawn_notification`、版本 `1.5-fabric-1.2.1` 均保留；文件名中的 `mc1.21.1` 仅区分移植产物，不修改版本号。

## 来源与许可证

- 上游：<https://github.com/timinc-cobble/cobblemon-spawn-notification-1.5-fabric>，归档的 `main`。
- 提交：`21c2359d9246145d15ae06e92ef9b4f105f90d74`。
- 原目标：Minecraft 1.20.1 / Cobblemon 1.5.2。
- MIT，原作者 Timothy Metcalfe；`LICENSE` 原样保留并打入产物。
- `upstream/source.tar.gz` 是该提交的完整 `git archive`，包括原源码、资源、README、构建文件、wrapper 和许可证。
- `upstream/commit.txt` 保留完整提交/作者/时间信息；`upstream/sha256.json` 保存原文件逐项校验值。

## 完整版本功能与配置

配置仍为游戏目录下 `config/spawn_notification.json`，完整环境初始化时读取，重启生效。
以下是上游所有 15 个持久化字段及原默认值，没有改名或删除：

| 配置 | 默认 | 功能 |
| --- | --- | --- |
| `broadcastShiny` | `true` | 野生闪光出生通知与闪光描述；不控制声音 |
| `broadcastCoords` | `true` | 通知显示坐标 |
| `broadcastBiome` | `false` | 通知显示群系，使用原版群系翻译键 |
| `playShinySound` | `true` | 野生闪光出生时播放原 PLA 音效 |
| `playShinySoundPlayer` | `false` | 玩家放出闪光宝可梦时播放 PLA 音效，独立于野生音效开关 |
| `announceCrossDimensions` | `false` | 跨维度广播消息并显示维度 |
| `broadcastDespawns` | `false` | 捕获和野生宝可梦倒下通知 |
| `broadcastVolatileDespawns` | `false` | 实体卸载通知（沿用上游语义，见下文） |
| `broadcastSpeciesName` | `true` | 出生通知使用物种名，关闭后使用通用宝可梦名称 |
| `broadcastPlayerSpawnedOn` | `false` | 出生通知显示触发玩家刷新的玩家名 |
| `broadcastRange` | `-1` | 正数启用距离限制；作用于同维度消息和野生闪光音效 |
| `playerLimit` | `-1` | 距离限制生效时，正数只选择距离最近的前 N 位玩家 |
| `labelsForBroadcast` | `["legendary"]` | 按形态标签通知，默认保留传说；删除 `legendary` 即关闭传说标签通知，也支持 mythical 等 |
| `bucketsForBroadcast` | `[]` | 按刷新池中匹配该宝可梦的稀有度桶通知，支持 ultra-rare 等 |
| `formatting` | `label.legendary=LIGHT_PURPLE`, `bucket.ultra-rare=AQUA`, `shiny=GOLD` | 按特征翻译键设置文字样式 |

保留出生/消失消息组合、标签和桶前缀、物种翻译、坐标、群系、维度、玩家、三种消失原因、原 `en_us`/`pt_pt` 语言和原 `shiny.ogg` 字节。
消息选择和音效选择仍独立：跨维度消息优先于距离限制，声音不跨维度；玩家放出音效沿用附近世界广播，不受野生距离/人数限制影响。

## 实际 API 移植

核对了官方 Cobblemon `b79dbcca802e10fb7eda89c568a874f7891a2d28` 的真实 1.8.4 源码：

- `SpawnEvent.ctx` 已不存在，改用 `spawnablePosition`、`spawner.spawnPool`。
- 玩家刷新来源改由 `SpawnEvent.cause.entity` 读取（原 PlayerSpawner.getCauseEntity 已移除）。
- `PokemonSentPostEvent` 改为 `PokemonSentEvent.Post`；继续订阅 `POKEMON_SENT_POST`。
- 刷新桶从对象的 `bucket.name` 改为 1.8.4 的字符串 `bucket`。
- 所有 Yarn 类型/调用移植到 MC 1.21.1 Mojmap：Component、ResourceLocation、ServerLevel、ServerPlayer、ResourceKey<Level>、维度/群系键、位置和系统消息 API。
- SoundEvent 使用 `createVariableRangeEvent`，世界音效用服务端 `playSound`；距离过滤后的指定玩家音效使用 `ServerPlayer.playNotifySound` 真正发送私有声音包。
- 不对已取消的刷新发出消息/声音；野生声音不处理玩家所有的宝可梦。
- `sounds.json` 的字幕引用修正为上游语言文件已有的 `spawn_notification_shinysoundsubtitle`，原语言键与内容不变。
- 仍只注册上游五个 Cobblemon 订阅和 Fabric `ENTITY_UNLOAD` 回调，优先级保持 LOWEST，无 Mixin、命令、按键或新玩法。

## 空壳/精简版本

唯一 Fabric 入口是纯 Java `SpawnNotificationBootstrap`，只引用 Fabric Loader API 与 JDK。
先读取 `cobblemon` 元数据中的 `train:variant`，字符串值为 `registry-only-shell` 时立即返回；不会加载 Kotlin 实现、Cobblemon API、Minecraft 类型，不会读写配置、创建音效对象或订阅任何事件。
只有完整环境才通过字符串反射加载 `SpawnNotification.INSTANCE`；完整环境初始化错误不会被伪装成成功。

本 mod **没有方块、物品、实体或其他必须与空壳同步的静态注册内容**。
精简组合可以完全不加载本 mod；需要保留相同 mod 列表时，也可直接使用本移植 JAR，其入口在空壳中无功能。
这不是在空壳里保留出生通知：空壳没有对应玩法/事件，全部通知和声音都停止。

资源目前仍内置，方便完整版本直接使用。统一外置时可搬出 `assets/spawn_notification/`；客户端必须仍获得语言与声音资源，才能正常显示翻译及播放 PLA 音效。

## 依赖

运行必须：Fabric Loader >=0.17.2、Fabric API、MC 1.21.1、Java >=21、Cobblemon >=1.8.4 <1.9.0（完整或约定元数据的空壳）。
完整实现需要 Kotlin 2.2.20 标准运行库，完整 Cobblemon 已提供，不另外内嵌或新增运行库。
没有额外可选依赖；上游 README 所提的 Cloth Config 在代码中并未使用，因此不要求安装。
空壳入口本身不需要 Kotlin 或 Cobblemon API。

## 可复现构建（无需启动 Gradle/游戏）

在本机已授权的工具链上执行：

```bash
python -X utf8 "G:/download/cobblemon-main (1)/cobblemon-main/sre-addons/spawn-notification/build.py" \
  --cobblemon-build "$PI_SCRATCH_DIR/cobblemon-1.8.4-upstream" \
  --gradle-home "H:/gradle-home" \
  --output "$PI_SCRATCH_DIR/spawn-notification-build" --test
```

- 不写源目录，所有类、临时目录、测试配置、JAR、参数文件都写到 H 盘的 `--output`。
- 非增量 `javac --release 21` + Kotlin 2.2.20 `K2JVMCompiler -jvm-target 21`，避免跨盘 Kotlin 增量路径问题。
- 只读使用 `common/build/devlibs/common-1.8.4+1.21.1-dev.jar`、同构建的 Mojmap MC merged JAR 和 `fabric/build/loom-cache/remapped_working/` 内 Fabric API 0.116.6。
- MC 库按 1.21.1 `mojang_minecraft_info.json` 的实际版本，从 H 缓存、现有用户 Gradle 缓存只读查找；不下载、不往 C 盘创建缓存。
- 使用已缓存 TinyRemapper 0.14.0、mapping-io 0.8.0、ASM 9.10.1 和 Architectury Loom 1.11.458（缓存坐标 1.11-SNAPSHOT）的 KotlinMetadataTinyRemapperExtension；同时正确重映射字节码和 Kotlin 元数据。
- 完整编译 classpath 记录于输出 `named-classpath.txt`/`build-report.json`；编译器和重映射器 classpath 及全部命令参数记录于 `javac.args`、`kotlinc.args`、`remap-tool-javac.args`、`remap.args`。均无需主项目 settings/build。
- 发布产物为 `spawnnotification-1.5-fabric-1.2.1-mc1.21.1.jar`，不要部署 `-named.jar` 开发产物。

## 验证结果与边界

已通过真实 1.8.4 开发类上的 JVM 21 编译与完整 intermediary/Kotlin 元数据重映射。
`--test` 通过：生产入口在禁止 Cobblemon/Minecraft/Kotlin/Fabric API 类加载的隔离 JVM 中安全跳过空壳；缺省/其他/非字符串变体走完整初始化入口，异常不被吞掉；所有 15 个配置字段的默认值/自定义值、格式/翻译参数与 JSON 文件往返；上游存档哈希、许可证、原音频和语言资源、字幕、JVM 21 字节码与发布命名空间校验。
完整入口分派测试使用测试替身，不冒充实际 Cobblemon 玩法运行验证。

未启动实际客户端、服务端、GUI 或组合测试，未部署桌面。主 agent 仍需验证真实刷新/捕获/倒下/放出事件、收件人范围、跨维度消息与实际音效。
沿用上游边界：volatile despawn 实际监听实体卸载，包含区块卸载和玩家所有宝可梦卸载，可能与捕获通知同时出现；`broadcastSpeciesName` 原本仅作用于出生消息；配置加载器的异常回退/重写策略保持上游原状。
