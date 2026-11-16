# 上游 showdown 元数据的 UTF-8 BOM 会让 Showdown 崩溃

## 症状

客户端/服务端启动日志：

```
[Cobblemon Showdown/INFO]: [STDERR]: com.google.gson.JsonSyntaxException:
  Expected BEGIN_OBJECT but was STRING at line 1 column 1 path $
  at GraalShowdownUnbundler.loadShowdownMetadata
[Cobblemon Showdown/ERROR]: Uncaught exception in thread "Cobblemon Showdown"
java.lang.NullPointerException at GraalShowdownUnbundler.attemptUnbundle
```

表现是 Showdown 服务线程直接死掉、对战不可用，游戏本体还能继续跑。

## 原因

`GraalShowdownUnbundler` 用 `InputStreamReader` + Gson 读取 jar 内
`/data/cobblemon/showdown.json`。Gson 的 `JsonReader` **不会**跳过 UTF-8 BOM，
首个字符 U+FEFF 被当成未加引号的字符串起始，于是报 “Expected BEGIN_OBJECT but was STRING”。

上游 1.8.4 源码里这个文件带 BOM（`git show b79dbcca:common/src/main/resources/data/cobblemon/showdown.json` 以 `EF BB BF` 开头），
而官方发行包里没有——所以从源码自建就会引入该缺陷，直接用官方 jar 不会。

本仓库已删除该 BOM，内容仍为 `{"showdownVersion": 19}`。

## 防回归

`sre-distribution/package_cobblemon_variants.py` 打包时断言：`data/**/*.json` 不得以
`EF BB BF` 开头，否则直接失败。

## 验证

打包后 3 个变体均无 BOM；真实客户端↔完整服、客户端↔空壳服连接测试中，
两侧日志都出现 `Showdown has been started!`，且无 `Expected BEGIN_OBJECT` 与
`Cobblemon Showdown` 异常。
