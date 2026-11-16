# 旧骑乘配置 → Cobblemon 1.8.4 原生骑乘

无需也不要安装 `cobblemonridingfabric-1.3.7.jar`。这是独立实现的数据补齐和只读配置转换，不包含旧模组字节码、图片或旧网络/移动框架；旧模组为 All rights reserved，不能据此推定已取得其转载许可。

## 默认数据

- 补齐 Nidoking、Ninetales、Tentacruel、Rapidash、Dodrio、Exeggutor、Meganium、Feraligatr、Steelix、Stantler、Swampert、Mightyena、Luxray、Yanmega、Samurott、Stoutland、Sawsbuck、Avalugg、Skeledirge 共 19 种原本缺失或失效的原生骑乘数据。
- 旧表 46 个有效名称及错拼 `Espahtla` 的正确目标 Espathra，全部至少有驾驶员和一位乘客。原本更多的座位不减少。模型中实际补充定位点，不只增加空座位声明；保留已有驾驶员定位点和原生动画。新增乘客定位在驾驶员后方 12 模型像素；没有驾驶员点的模型使用躯干背部位置。美术贴合度仍需游戏内验收。
- 修复这些物种及其形态内 `behaviour` 单数、顶层 `stats` 的旧格式，改为原生 `behaviours` 按 LAND/AIR/LIQUID 分组，并保留已有逐模式范围。新物种没有官方骑乘数值时使用中等 `20-60` 范围，仍由原生表达式计算，而不是照搬旧 200 耐力值。
- 已有原生模式、速度/体力范围、音效和多座位保留。例如 Blastoise 的火箭飞行、Gyarados 的飞行、Metagross 的四座。Magnezone 保留原生近地悬浮，不强制变成地面跑步。

## 使用世界根旧配置

将自己已有的 `pokemonRideConfig.json` 留在**世界根目录**：独立服务器通常为 `world/pokemonRideConfig.json`，单人游戏为 `saves/<世界>/pokemonRideConfig.json`，不是 `config/`。
服务器启动以及原生物种数据 `/reload` 后读取。文件不会创建、覆盖、删除或改写；不存在时仅使用上述原生数据。只转换配置中的条目，未列出的原生可骑物种不会被禁用。变更后建议召回并重新放出已有坐骑，再骑乘；运行中座位数量变化时先下骑。连接中的玩家应重新连接以确认完整物种同步。

```json
{
  "mustAllowEntityRiding": false,
  "pokemonTypes": {
    "Charizard": {
      "formName": "normal",
      "stamina": 0,
      "mountType": ["WALK", "FLY"],
      "ridingOffSet": [0.0, 1.0, 0.0],
      "passengersOffSet": [[0.0, 1.0, -0.75]],
      "speedModifier": 1.0
    }
  }
}
```

**注意旧坐标顺序为 `[Z, Y, X]`**。上例乘客数组表示世界实体局部 X=-0.75、Y=1、Z=0，而不是后方；若要在后方使用 `[-0.75, 1.0, 0.0]`。坐标为方块单位，随驾驶员朝向旋转，不是模型像素。明确提供的 offset 直接替代定位点，不会重复加上模型位置；两端使用同一定位算法。原始旧零乘客 offset 也如实保留，可能使乘客处于实体原点；需要时由服主调整文件。

### 转换约定

| 旧字段 | 原生转换及限制 |
| --- | --- |
| 物种键 | 忽略大小写；支持本体名称、带命名空间的 ID；`Espahtla` 显式映射 `espathra`。未知名称记录警告、跳过该条。 |
| `formName` | null/缺省/none/normal/base 只匹配标准形态；其它名称忽略大小写精确匹配形态名称，不会套到所有地区形态。标准形态覆盖也通过原生 Species 同步，即使该物种没有 forms 列表。 |
| `mountType` | 必须为 1–4 项字符串数组。WALK 补原生 horse，FLY 缺模式时补 hover；已有飞行风格和其它原生模式不删除。明确配置 SWIM 时液体模式转 submarine，保留已有液体 stats 和音效，支持原生下潜而不是只在水面行驶。 |
| `LAVA_SWIM` | 复用 submarine，限定岩浆；与 SWIM 同时配置才允许两种液体。只配置 WALK+LAVA_SWIM 不会额外获得水中游泳。**不提供抗火或任何伤害豁免，骑手和非耐火坐骑仍会受伤**，请勿将此配置理解为安全横渡岩浆。 |
| `speedModifier` | 缺省/1 保持原生速度。自定义值是有限数字 0.05–4，乘到原生速度表达式；horse 的普通步行也乘同一倍率。不是旧模组两次 move 的速度复刻，水中侧移/升降及飞行风格的专用参数仍由原生规则决定。 |
| `stamina` | 缺省/0/200 为保留原生平衡的哨兵值，**不覆盖原生体力**。其它整数 1–72000 转原生 `staminaExpr = ticks / 20` 秒；原生消耗场景、恢复倍率、飞行坠落、水下呼吸规则不改变。不是旧“只冲刺扣体力”的逐 tick 复刻，也不是 STAMINA stat。 |
| `ridingOffSet` | 三个有限数字，每轴 -16–16；只替换驾驶员位置。未给出则保留原生驾驶员定位。 |
| `passengersOffSet` | 0–7 个同样格式的坐标（含驾驶员最多 8 座）；明确给出时座位数量以该数组为准，包括空数组代表无额外乘客。未给出则保留原生乘客座位；新自定义可骑物种没有原座位且无 offset 时提供有效的双座坐标。 |
| `mustAllowEntityRiding` | 只接受 boolean；原文件保持不变，true 会警告。**不启用旧扫描装载生物规则**；仍可通过原生座位机制承载已经合法上骑的实体。 |

文件上限 1 MiB、条目上限 1024；拒绝 NaN/Infinity、数值字符串、负耐力、分数耐力、零/负速度、错误坐标维度和过多乘客。未知类型/形态、重复别名目标及无可转换表达式的第三方骑乘风格均警告并整条跳过，不应用半个条目。重新读取前恢复原始覆盖，倍率不会反复累乘；删除配置后再 reload 恢复原生数据。

全部转换结果由服务端写入原生 FormData/RidingProperties/Settings/Seat，经现有 SpeciesRegistrySyncPacket 编解码同步；没有旧 ConfigS2C，也没有客户端读取世界配置。新增 Seat offset、horse 普通步行倍率、submarine 液体限制均补充对称编解码。**客户端和服务端必须使用同一新版构建**，不兼容未修改的原版 1.8.4 骑乘数据协议。

## 明确不迁移的旧规则

不新增按键，继续使用原生互动轮盘上骑、R 下骑、原生移动/跳跃/冲刺和自由视角。旧 K 下骑和左 Alt 扫描载生物不注册；左 Alt 继续原生自由视角。保留原生所有权、距离、战斗、体型、拴绳和空中下骑等安全限制，不新增放出自动上骑。

不迁移骑手全伤免疫、岩浆坐骑全伤免疫、不显示燃烧、飞行零跌落伤害或低落差免伤。不迁移普通无限飞行/无限潜水、旧独立冲刺体力池、旧升降速度、表面下潜瞬移、旧跳跃/台阶/冲刺阈值、旧移动容差及网络/AI 补丁。普通飞行仍消耗原生体力，耗尽行为与原生一致；Lapras 等未明确出现在用户旧配置里时仍保留官方水面风格。这些是有意保留原生平衡的行为差异，不能称为与旧模组数值完全等价。

## 检查和待验收

运行 `python -X utf8 sre-distribution/riding-compat/check_riding_compat.py` 检查 47 个目标及所有现有模型的有效座位/原生格式，以及转换代码的关键静态契约；不代替 JVM 单元测试或游戏验证。`species-manifest.json` 给出每个物种和模型的精确路径。

完整 Gradle 构建由主代理合并其它功能后统一执行，此任务未运行。还需游戏中验证：标准/地区形态的双人定位与转向，原生已有多座位不回退，服务端重连同步，世界切换/reload 不累乘，非法配置警告和回退，自定义 offset 和座位数量，horse 普通步行/冲刺倍率，submarine 升降与液体限制，飞行耗尽，以及伤害确实未被豁免。
