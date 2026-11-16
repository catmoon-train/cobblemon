import java.nio.file.Files;
import java.nio.file.FileSystems;
import java.nio.file.Path;
import java.util.Arrays;
import net.fabricmc.tinyremapper.NonClassCopyMode;
import net.fabricmc.tinyremapper.OutputConsumerPath;
import net.fabricmc.tinyremapper.TinyRemapper;
import net.fabricmc.tinyremapper.TinyUtils;
import net.fabricmc.loom.kotlin.remapping.KotlinMetadataTinyRemapperExtensionImpl;

/** 构建工具：复用 Loom 的 Kotlin 元数据重映射，不丢弃元数据或只替换依赖声明。 */
public final class BuildRemap {
    public static void main(String[] args) throws Exception {
        Path input = Path.of(args[0]), output = Path.of(args[1]), mappings = Path.of(args[2]);
        var remapper = TinyRemapper.newRemapper()
                .withMappings(TinyUtils.createTinyMappingProvider(mappings, "named", "intermediary"))
                .extension(KotlinMetadataTinyRemapperExtensionImpl.INSTANCE)
                .threads(2).build();
        try {
            remapper.readClassPath(Arrays.stream(args).skip(3).map(Path::of).toArray(Path[]::new));
            remapper.readInputs(input);
            try (var consumer = new OutputConsumerPath.Builder(output).build()) {
                consumer.addNonClassFiles(input, NonClassCopyMode.FIX_META_INF, remapper);
                remapper.apply(consumer);
            }
        } finally {
            remapper.finish();
        }
        try (var jar = FileSystems.newFileSystem(output)) {
            Files.writeString(jar.getPath("/META-INF/MANIFEST.MF"),
                    "Manifest-Version: 1.0\nFabric-Mapping-Namespace: intermediary\n\n");
        }
    }
}
