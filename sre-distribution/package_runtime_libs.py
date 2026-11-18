"""从 Cobblemon 构建包提取、修补（Java 25 Truffle）并精简独立运行库模组 Cobblemon-runtime-libs。"""
from __future__ import annotations

import argparse
import io
import json
import pathlib
import subprocess
import tempfile
import zipfile

PATCH_TRUFFLE_JAVA = r"""
import org.objectweb.asm.*;
import java.nio.file.*;

public class PatchTruffle {
    public static void main(String[] args) throws Exception {
        byte[] bytes = Files.readAllBytes(Path.of(args[0]));
        ClassReader cr = new ClassReader(bytes);
        ClassWriter cw = new ClassWriter(cr, ClassWriter.COMPUTE_MAXS | ClassWriter.COMPUTE_FRAMES);
        cr.accept(new ClassVisitor(Opcodes.ASM9, cw) {
            @Override
            public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
                if (name.equals("ensureLibraryInitialized") && descriptor.equals("()V")) {
                    MethodVisitor mv = super.visitMethod(access, name, descriptor, signature, exceptions);
                    mv.visitCode();
                    Label start = new Label();
                    Label end = new Label();
                    Label handler = new Label();
                    mv.visitTryCatchBlock(start, end, handler, "java/lang/ClassNotFoundException");
                    mv.visitMethodInsn(Opcodes.INVOKESTATIC, "com/oracle/truffle/api/CompilerAsserts", "neverPartOfCompilation", "()V", false);
                    mv.visitLabel(start);
                    mv.visitVarInsn(Opcodes.ALOAD, 0);
                    mv.visitFieldInsn(Opcodes.GETFIELD, "com/oracle/truffle/api/library/LibraryFactory", "libraryClass", "Ljava/lang/Class;");
                    mv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/lang/Class", "getName", "()Ljava/lang/String;", false);
                    mv.visitInsn(Opcodes.ICONST_1);
                    mv.visitVarInsn(Opcodes.ALOAD, 0);
                    mv.visitFieldInsn(Opcodes.GETFIELD, "com/oracle/truffle/api/library/LibraryFactory", "libraryClass", "Ljava/lang/Class;");
                    mv.visitMethodInsn(Opcodes.INVOKEVIRTUAL, "java/lang/Class", "getClassLoader", "()Ljava/lang/ClassLoader;", false);
                    mv.visitMethodInsn(Opcodes.INVOKESTATIC, "java/lang/Class", "forName", "(Ljava/lang/String;ZLjava/lang/ClassLoader;)Ljava/lang/Class;", false);
                    mv.visitInsn(Opcodes.POP);
                    mv.visitLabel(end);
                    mv.visitInsn(Opcodes.RETURN);
                    mv.visitLabel(handler);
                    mv.visitVarInsn(Opcodes.ASTORE, 1);
                    mv.visitTypeInsn(Opcodes.NEW, "java/lang/IllegalStateException");
                    mv.visitInsn(Opcodes.DUP);
                    mv.visitVarInsn(Opcodes.ALOAD, 1);
                    mv.visitMethodInsn(Opcodes.INVOKESPECIAL, "java/lang/IllegalStateException", "<init>", "(Ljava/lang/Throwable;)V", false);
                    mv.visitInsn(Opcodes.ATHROW);
                    mv.visitMaxs(0, 0);
                    mv.visitEnd();
                    return null;
                }
                return super.visitMethod(access, name, descriptor, signature, exceptions);
            }
        }, 0);
        Files.write(Path.of(args[1]), cw.toByteArray());
    }
}
"""

ICU_KEEP_STEMS = (
    "root",
    "en",
    "zh",
    "pool",
    "res_index",
    "icustd",
    "unames",
    "ucase",
    "uprops",
    "ubidi",
    "nfc",
    "nfkc",
    "nfkc_cf",
    "uts46",
    "pnames",
    "cnvalias",
    "confusables",
    "dayPeriods",
    "genderList",
    "keyTypeData",
    "likelySubtags",
    "metaZones",
    "numberingSystems",
    "pluralRanges",
    "plurals",
    "supplementalData",
    "timezoneTypes",
    "windowsZones",
    "zoneinfo64",
    "grammaticalFeatures",
    "units",
)
ICU_DROP_NON_RES = {
    "brkitr/burmesedict.dict",
    "brkitr/khmerdict.dict",
    "brkitr/laodict.dict",
    "brkitr/thaidict.dict",
}
FLK_KEEP_JARS = (
    "kotlin-stdlib-",
    "kotlin-reflect-",
)


def default_java21_tool(name: str) -> pathlib.Path:
    for candidate in [
        pathlib.Path(rf"C:\Program Files\Zulu\zulu-21\bin\{name}"),
        pathlib.Path(rf"G:\exmo\StarRailExpress2\jdk-21.0.6+7\bin\{name}"),
    ]:
        if candidate.is_file():
            return candidate
    return pathlib.Path(name)


def default_asm_jar() -> pathlib.Path:
    return next(
        p
        for p in pathlib.Path.home().joinpath(".gradle/caches").rglob("asm-9.*.jar")
        if "sources" not in p.name and "javadoc" not in p.name
    )


def patch_truffle_bytes(truffle_bytes: bytes, workdir: pathlib.Path, javac: pathlib.Path, java: pathlib.Path, asm_jar: pathlib.Path) -> bytes:
    patch_dir = workdir / "patch_truffle"
    patch_dir.mkdir(parents=True, exist_ok=True)
    java_file = patch_dir / "PatchTruffle.java"
    java_file.write_text(PATCH_TRUFFLE_JAVA, encoding="utf-8")
    subprocess.run([str(javac), "-cp", str(asm_jar), str(java_file)], check=True)

    orig_jar = patch_dir / "truffle-orig.jar"
    orig_jar.write_bytes(truffle_bytes)
    with zipfile.ZipFile(orig_jar, "r") as zin:
        orig_cls = patch_dir / "LibraryFactory.orig.class"
        orig_cls.write_bytes(zin.read("com/oracle/truffle/api/library/LibraryFactory.class"))

    patched_cls = patch_dir / "LibraryFactory.patched.class"
    subprocess.run(
        [str(java), "-cp", f"{patch_dir};{asm_jar};{orig_jar}", "PatchTruffle", str(orig_cls), str(patched_cls)],
        check=True,
    )
    patched_bytes = patched_cls.read_bytes()

    out_buf = io.BytesIO()
    with zipfile.ZipFile(orig_jar, "r") as zin, zipfile.ZipFile(out_buf, "w", compression=zipfile.ZIP_STORED) as zout:
        for info in zin.infolist():
            if info.is_dir():
                continue
            content = patched_bytes if info.filename == "com/oracle/truffle/api/library/LibraryFactory.class" else zin.read(info.filename)
            zi = zipfile.ZipInfo(info.filename)
            zi.compress_type = zipfile.ZIP_STORED
            zout.writestr(zi, content)
    return out_buf.getvalue()


def trim_flk_bytes(flk_bytes: bytes) -> tuple[bytes, dict]:
    out_buf = io.BytesIO()
    kept_jars, dropped_jars = [], []
    with zipfile.ZipFile(io.BytesIO(flk_bytes), "r") as zin, zipfile.ZipFile(out_buf, "w", compression=zipfile.ZIP_STORED) as zout:
        fmj = json.loads(zin.read("fabric.mod.json").decode("utf-8"))
        new_jars = []
        for entry in fmj.get("jars", []):
            name = pathlib.Path(entry["file"]).name
            if any(name.startswith(prefix) for prefix in FLK_KEEP_JARS):
                new_jars.append(entry)
                kept_jars.append(name)
            else:
                dropped_jars.append(name)
        fmj["jars"] = new_jars

        keep_set = {entry["file"] for entry in new_jars}
        for info in zin.infolist():
            if info.is_dir():
                continue
            fn = info.filename
            if fn.startswith("META-INF/jars/") and fn not in keep_set:
                continue
            data = (json.dumps(fmj, ensure_ascii=False, indent=2) + "\n").encode("utf-8") if fn == "fabric.mod.json" else zin.read(fn)
            zi = zipfile.ZipInfo(fn)
            zi.compress_type = zipfile.ZIP_STORED
            zout.writestr(zi, data)
    return out_buf.getvalue(), {"kept": kept_jars, "dropped": dropped_jars}


def trim_icu_bytes(icu_bytes: bytes) -> tuple[bytes, dict]:
    out_buf = io.BytesIO()
    kept_files, dropped_files, dropped_bytes = 0, 0, 0
    prefix = "com/ibm/icu/impl/data/icudt71b/"
    with zipfile.ZipFile(io.BytesIO(icu_bytes), "r") as zin, zipfile.ZipFile(out_buf, "w", compression=zipfile.ZIP_STORED) as zout:
        for info in zin.infolist():
            if info.is_dir():
                continue
            fn = info.filename
            if fn.startswith(prefix):
                rel = fn[len(prefix):]
                if rel in ICU_DROP_NON_RES or rel.startswith(("translit/", "rbnf/")):
                    dropped_files += 1
                    dropped_bytes += info.file_size
                    continue
                base = rel.split("/")[-1]
                if base.endswith(".res"):
                    stem = base[:-4]
                    if not any(stem == s or stem.startswith(s + "_") for s in ICU_KEEP_STEMS):
                        dropped_files += 1
                        dropped_bytes += info.file_size
                        continue
            kept_files += 1
            zi = zipfile.ZipInfo(fn)
            zi.compress_type = zipfile.ZIP_STORED
            zout.writestr(zi, zin.read(fn))
    return out_buf.getvalue(), {"keptFiles": kept_files, "droppedFiles": dropped_files, "droppedRawBytes": dropped_bytes}


def repack_stored(raw_bytes: bytes) -> bytes:
    out_buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw_bytes), "r") as zin, zipfile.ZipFile(out_buf, "w", compression=zipfile.ZIP_STORED) as zout:
        for info in zin.infolist():
            if info.is_dir():
                continue
            zi = zipfile.ZipInfo(info.filename)
            zi.compress_type = zipfile.ZIP_STORED
            zout.writestr(zi, zin.read(info.filename))
    return out_buf.getvalue()


def build_runtime_jar(source_jar: pathlib.Path, output_jar: pathlib.Path, full_icu: bool = False) -> dict:
    javac = default_java21_tool("javac.exe")
    java = default_java21_tool("java.exe")
    asm_jar = default_asm_jar()

    report: dict = {"sourceJar": str(source_jar), "outputJar": str(output_jar), "fullIcu": full_icu}
    with tempfile.TemporaryDirectory(dir=r"I:\temp" if pathlib.Path(r"I:\temp").exists() else None) as tmp:
        workdir = pathlib.Path(tmp)
        nested_entries: list[tuple[str, bytes]] = []
        license_bytes = b""

        with zipfile.ZipFile(source_jar, "r") as zf:
            fmj = json.loads(zf.read("fabric.mod.json").decode("utf-8"))
            jar_refs = [j["file"] for j in fmj.get("jars", [])]
            if "LICENSE" in zf.namelist():
                license_bytes = zf.read("LICENSE")
            for ref in jar_refs:
                data = zf.read(ref)
                name = pathlib.Path(ref).name
                if name.startswith("truffle-api-"):
                    data = patch_truffle_bytes(data, workdir, javac, java, asm_jar)
                elif name.startswith("fabric-language-kotlin-"):
                    data, flk_rep = trim_flk_bytes(data)
                    report["fabricLanguageKotlin"] = flk_rep
                elif name.startswith("icu4j-") and not full_icu:
                    data, icu_rep = trim_icu_bytes(data)
                    report["icu4j"] = icu_rep
                else:
                    data = repack_stored(data)
                nested_entries.append((ref, data))

        runtime_fmj = {
            "schemaVersion": 1,
            "id": "cobblemon_runtime",
            "version": "1.8.4+1.21.1",
            "name": "Cobblemon Runtime Libraries",
            "description": "Separated & slimmed Kotlin, GraalJS, Truffle (Java 25 patched), ICU4J, Regex, and MongoDB runtime libraries for Cobblemon.",
            "license": "MPL-2.0",
            "environment": "*",
            "depends": {
                "fabricloader": ">=0.17.2",
                "java": ">=21",
            },
            "jars": [{"file": ref} for ref, _ in nested_entries],
            "custom": {
                "train:variant": "runtime-libs-slim",
                "train:java25-truffle-patched": True,
            },
        }

        output_jar.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_jar, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
            zout.writestr("fabric.mod.json", (json.dumps(runtime_fmj, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
            if license_bytes:
                zout.writestr("LICENSE", license_bytes)
            for ref, data in nested_entries:
                zi = zipfile.ZipInfo(ref)
                zi.compress_type = zipfile.ZIP_DEFLATED
                zout.writestr(zi, data, compresslevel=9)

    report["outputBytes"] = output_jar.stat().st_size
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="构建精简版 Cobblemon-runtime-libs JAR")
    parser.add_argument("source", type=pathlib.Path, help="含 META-INF/jars/* 的原始 Cobblemon JAR 或旧 runtime JAR")
    parser.add_argument("output", type=pathlib.Path, help="输出的精简版 Cobblemon-runtime-libs-*.jar 路径")
    parser.add_argument("--full-icu", action="store_true", help="保留全部 ICU 语言地区资源（默认仅保留核心/英文/中文）")
    args = parser.parse_args()
    print(json.dumps(build_runtime_jar(args.source, args.output, args.full_icu), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
