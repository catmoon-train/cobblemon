# 附属模组的“运行代码类资源”必须留在 JAR

## 症状

客户端卡在加载 98%，最大化窗口后黑屏；日志（`logs/latest.log`）末尾：

```
Caused by: net.minecraft.class_2973: Invalid shaders/core/tera_crystal_fire.json: File not found
  at MegaShowdownFabricClient.lambda$onInitializeClient$0
Caused by: java.io.FileNotFoundException: mega_showdown:shaders/core/tera_crystal.vsh
```

## 原因

资源外置时把所有 `assets/<mod>/**` 都搬进了资源包，包括**着色器源码**（`.vsh`/`.fsh`）。
Mega 的 `IrisIgnoreShader` 在 `GameRenderer` 着色器重载时直接构造 `ShaderInstance`，
此时若客户端没有启用我们的资源包，`.vsh/.fsh` 根本不存在 → 着色器重载抛异常 →
渲染线程卡死/黑屏。

同类问题还有 `assets/mega_showdown/showdown/*.js`（Showdown 战斗脚本）：缺失会让对战初始化拿到 null。

## 规则

`package_addon_variants.py` 的 `runtime_resource()` 把这些路径视为运行代码，**留在 JAR、不进资源包**：

- `assets/*/shaders/**`（含 `core/*.json`、`.vsh`、`.fsh`）
- `assets/*/post_effect/**`
- `assets/mega_showdown/showdown/**`

打包时还会断言：源码里所有 `assets/**/*.vsh|*.fsh|*.glsl|*.js` 必须出现在客户端 JAR 内，
且不得出现在资源包里。

## 验证

`verify_shader_boot.py`（scratch）在**不启用任何资源包**的情况下启动真实客户端：

- 旧打包（着色器只在资源包）：`shaderCrash=True`
- 新打包（着色器在 JAR）：`shaderCrash=False`，客户端正常启动

正式连接验证中客户端日志 `could not reload shaders` 计数为 0。
