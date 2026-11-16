# Cobblenav Fabric 1.21.1 / Cobblemon 1.8.4 本地构建

上游 main 提交 b5633dd83b7fd0cd59e7cf47bd84c5285cecb048，版本2.4.2、MPL-2.0，原代码和多平台构建保持原样。独立 `train-build` 使用固定的 Architectury Loom1.11.458 / Kotlin2.2.20，直接编译 common+fabric 全部源码，对本地真实1.8.4 named API完成编译及 intermediary 生产重映射。上游原配置声明1.8.0，本地校验目标为1.8.4。

```bash
GRADLE_USER_HOME=H:/gradle-home GRADLE_RO_DEP_CACHE=C:/Users/canyuesama/.gradle/caches \n  gradle -p train-build remapJar -PcobblemonNamedJar="<Cobblemon1.8.4-dev-shadow.jar绝对路径>" \n  -Dfabric.loom.ci=true -Dorg.gradle.jvmargs=-Xmx3G -Pkotlin.incremental=false \n  -Pkotlin.compiler.execution.strategy=in-process --max-workers=2 --console=plain
```

使用Java21/Gradle8.14.3，生产JAR在train-build/build/libs；named API仅编译使用，不能安装到游戏。真实服务端已完成导航注册和数据加载；完整客户端对512MiB精简服连接通过（120tick、模型985、注册表一致），组合最终验证见根sre-distribution记录。

客户端/完整服保留全部413个外层class及玩法数据；美术外置，保留已有en_us/zh_cn（上游没有zh_tw）。空壳为独立Java注册壳，只保留29物品及1物品栏分组；不加载原Mixin、Kotlin和宝可梦API，不提供导航玩法或旧存档兼容。
