"""一键构建列车服务端空壳版（使用中间注册层 RegistryReplayEngine）。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import zipfile

from distribution_env import API, CLASSPATH, MINECRAFT, MAPPINGS, MAPROOT, NAMED_CP, ROOT, SOURCE_DIR, TINY, MAPIO, argfile, compile_mod, prepare_server, server_args
from verify_distribution_pair import compare

ADDON_BASE_ID = "mega_showdown"
ADDON_VERSION = "1.3.3+1.8.4+1.21.1-release"
ADDON_PROVIDES = ["cobblenav", "cobblemon_spawn_notification"]
COBBLEMON_JAR_NAME = "Cobblemon-fabric-1.8.4+1.21.1.jar"
ADDON_JAR_NAME = f"mega_showdown-fabric-{ADDON_VERSION}.jar"
COBBLEMON_MINECRAFT_IDS = {"minecraft:cooking_pot_menu", "minecraft:tm_machine_menu"}


def sha256(path: pathlib.Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def split_snapshot_namespaces(full_snapshot: dict) -> tuple[dict, dict]:
    cobblemon_regs: dict[str, list] = {}
    addon_regs: dict[str, list] = {}
    for reg_key, entries in full_snapshot.items():
        for entry in entries:
            entry_id = entry["id"] if isinstance(entry, dict) else entry
            ns = entry_id.split(":", 1)[0]
            if ns == "cobblemon" or entry_id in COBBLEMON_MINECRAFT_IDS:
                cobblemon_regs.setdefault(reg_key, []).append(entry)
            elif ns != "minecraft":
                addon_regs.setdefault(reg_key, []).append(entry)
    return cobblemon_regs, addon_regs


def refresh_snapshots(cobblemon_jar: pathlib.Path, extra_mods: list[pathlib.Path], out_cobblemon: pathlib.Path, out_addons: pathlib.Path) -> None:
    probe_jar = ROOT / "distribution-probe.jar"
    if not probe_jar.is_file():
        probe_jar = compile_mod(
            "distribution-probe",
            [SOURCE_DIR / "DistributionProbe.java"],
            {
                "schemaVersion": 1,
                "id": "train_distribution_probe",
                "version": "1.0.0",
                "environment": "*",
                "entrypoints": {"main": ["train.cobblemon.probe.DistributionProbe"]},
                "depends": {"fabric-api": "*"},
            },
        )
    work_dir = ROOT / "shell-refresh-server"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    game = prepare_server("shell-refresh-server", cobblemon_jar, probe_jar)
    for mod in extra_mods:
        shutil.copy2(mod, game / "mods" / mod.name)
    dump_path = ROOT / "shell-refresh-snapshot.json"
    log_path = ROOT / "shell-refresh.log"
    args = server_args(game, [f"-Dtrain.registry.output={dump_path.as_posix()}", "-Dtrain.probe.stop=true"])
    with log_path.open("wb") as logf:
        res = subprocess.run(["java", argfile("shell-refresh.args", args)], cwd=game, stdout=logf, stderr=subprocess.STDOUT, timeout=300)
    text = log_path.read_text(encoding="utf-8", errors="replace")
    assert res.returncode == 0 and "TRAIN_REGISTRY_DUMP_PASS" in text, (res.returncode, log_path)

    full_snapshot = json.loads(dump_path.read_text(encoding="utf-8"))
    cobble_regs, addon_regs = split_snapshot_namespaces(full_snapshot)
    out_cobblemon.write_text(json.dumps(cobble_regs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_addons.write_text(json.dumps(addon_regs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Refreshed snapshots -> {out_cobblemon.name}, {out_addons.name}")


def compile_addon_against_shell(name: str, sources: list[pathlib.Path], extra_cp: pathlib.Path, metadata: dict, resources: dict[str, bytes]) -> pathlib.Path:
    out = ROOT / f"{name}-classes"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    cp = f"{NAMED_CP};{extra_cp.as_posix()}"
    args = ["--release", "21", "-proc:none", "-encoding", "UTF-8", "-cp", cp, "-d", out.as_posix(), *[s.as_posix() for s in sources]]
    subprocess.run(["javac", "-J-Duser.language=en", argfile(f"{name}-javac.args", args)], check=True)

    named = ROOT / f"{name}-named.jar"
    target = ROOT / f"{name}.jar"
    with zipfile.ZipFile(named, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("fabric.mod.json", json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
        z.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nFabric-Mapping-Namespace: named\n\n")
        for p in sorted(out.rglob("*.class")):
            z.write(p, p.relative_to(out).as_posix())
        for key, value in resources.items():
            z.writestr(key, value)

    # Remap named -> intermediary (include extra_cp in tiny-remapper library classpath)
    remap_cp = ";".join([TINY.as_posix(), MAPIO.as_posix(), *[p for p in NAMED_CP.split(";") if p]])
    remap_args = ["-Xmx2G", "-cp", remap_cp, "net.fabricmc.tinyremapper.Main", named.as_posix(), target.as_posix(), MAPPINGS.as_posix(), "named", "intermediary", extra_cp.as_posix()]
    remap_args.extend(p for p in NAMED_CP.split(";") if p.endswith(".jar") and pathlib.Path(p).is_file())
    subprocess.run(["java", argfile(f"{name}-remap.args", remap_args)], check=True)
    return target


def verify_shells(cobble_shell: pathlib.Path, addon_shell: pathlib.Path, snapshot: pathlib.Path) -> None:
    probe_jar = ROOT / "distribution-probe.jar"
    if not probe_jar.is_file():
        probe_jar = compile_mod(
            "distribution-probe",
            [SOURCE_DIR / "DistributionProbe.java"],
            {
                "schemaVersion": 1,
                "id": "train_distribution_probe",
                "version": "1.0.0",
                "environment": "*",
                "entrypoints": {"main": ["train.cobblemon.probe.DistributionProbe"]},
                "depends": {"fabric-api": "*"},
            },
        )
    verify_dir = ROOT / "shell-layer-verify"
    if verify_dir.exists():
        shutil.rmtree(verify_dir)
    game = prepare_server("shell-layer-verify", cobble_shell, probe_jar)
    shutil.copy2(addon_shell, game / "mods" / addon_shell.name)
    dump_path = ROOT / "shell-layer-registries.json"
    log_path = ROOT / "shell-layer-verify.log"
    args = server_args(game, [f"-Dtrain.registry.output={dump_path.as_posix()}", "-Dtrain.probe.stop=true"])
    args[0] = "-Xmx512M"
    with log_path.open("wb") as logf:
        res = subprocess.run(["java", argfile("shell-layer-verify.args", args)], cwd=game, stdout=logf, stderr=subprocess.STDOUT, timeout=180)
    txt = log_path.read_text(encoding="utf-8", errors="replace")
    assert res.returncode == 0 and "TRAIN_REGISTRY_DUMP_PASS" in txt, (res.returncode, log_path, "\n".join(txt.splitlines()[-25:]))
    assert "COBBLEMON_REGISTRY_SHELL_READY" in txt and "MEGA_SHOWDOWN_REGISTRY_SHELL_READY" in txt, "Missing shell ready markers"
    cmp = compare(snapshot, dump_path)
    print("VERIFY_SHELL_PASS:", json.dumps(cmp, ensure_ascii=False))


def build_shells(
    output_dir: pathlib.Path,
    cobble_snapshot_path: pathlib.Path,
    addon_snapshot_path: pathlib.Path,
    verify: bool = False,
    full_snapshot_for_verify: pathlib.Path | None = None,
) -> tuple[pathlib.Path, pathlib.Path]:
    # 1. Build Cobblemon intermediate registration layer + shell JAR
    cobble_meta = {
        "schemaVersion": 1,
        "id": "cobblemon",
        "version": "1.8.4+1.21.1",
        "name": "Cobblemon Registry Shell (Train Server Only)",
        "description": "Shared intermediate registration layer & Cobblemon registry-only shell; no Pokemon gameplay, Showdown or Kotlin runtime.",
        "license": "MPL-2.0",
        "environment": "server",
        "entrypoints": {"main": ["train.cobblemon.shell.RegistryShell"]},
        "depends": {"fabricloader": ">=0.17.2", "fabric-api": ">=0.116.6+1.21.1", "minecraft": "1.21.1", "java": ">=21"},
        "custom": {"train:variant": "registry-only-shell", "train:intermediateLayer": "train.cobblemon.shell.RegistryReplayEngine"},
    }
    cobble_res = {
        "train-shell-registries.json": cobble_snapshot_path.read_bytes(),
        "LICENSE": (SOURCE_DIR.parent / "LICENSE").read_bytes(),
    }
    cobble_built = compile_mod(
        "Cobblemon-fabric-1.8.4+1.21.1-server-shell",
        [SOURCE_DIR / "RegistryReplayEngine.java", SOURCE_DIR / "RegistryShell.java"],
        cobble_meta,
        cobble_res,
    )
    cobble_named = ROOT / "Cobblemon-fabric-1.8.4+1.21.1-server-shell-named.jar"

    # 2. Extract addon-only namespaces from addon_snapshot_path (works whether passed full runtime snapshot or addon-only snapshot)
    raw_addon = json.loads(addon_snapshot_path.read_text(encoding="utf-8"))
    _, addon_only = split_snapshot_namespaces(raw_addon)
    addon_meta = {
        "schemaVersion": 1,
        "id": ADDON_BASE_ID,
        "version": ADDON_VERSION,
        "name": "Cobblemon: Mega Showdown + Addons Registry Shell",
        "provides": ADDON_PROVIDES,
        "environment": "server",
        "license": "MEGA SHOWDOWN LICENSE v2.1",
        "entrypoints": {"main": ["train.addons.shell.mega_showdown.AddonRegistryShell"]},
        "depends": {"fabricloader": ">=0.17.2", "minecraft": "1.21.1", "java": ">=21", "fabric-api": "*", "cobblemon": "1.8.4+1.21.1"},
        "custom": {"train:variant": "registry-only-shell", "train:gameplay": False, "train:mergedAddons": [ADDON_BASE_ID, *ADDON_PROVIDES]},
    }
    addon_res = {
        "train-shell-mega_showdown-registries.json": (json.dumps(addon_only, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    }
    addon_built = compile_addon_against_shell(
        "mega_showdown-server-shell",
        [SOURCE_DIR / "AddonRegistryShell.java"],
        cobble_named,
        addon_meta,
        addon_res,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    cobble_out = output_dir / COBBLEMON_JAR_NAME
    addon_out = output_dir / ADDON_JAR_NAME
    shutil.copy2(cobble_built, cobble_out)
    shutil.copy2(addon_built, addon_out)
    print(f"BUILT {cobble_out} ({cobble_out.stat().st_size:,} bytes, sha256={sha256(cobble_out)[:12]})")
    print(f"BUILT {addon_out} ({addon_out.stat().st_size:,} bytes, sha256={sha256(addon_out)[:12]})")

    if verify:
        snap = full_snapshot_for_verify or addon_snapshot_path
        verify_shells(cobble_out, addon_out, snap)
    return cobble_out, addon_out


def main() -> None:
    parser = argparse.ArgumentParser(description="一键构建列车服务端空壳版（基于 RegistryReplayEngine 中间注册层）")
    parser.add_argument("--out", type=pathlib.Path, default=ROOT / "train-shell-out", help="输出目录")
    parser.add_argument("--refresh-from", type=pathlib.Path, help="从完整服务端模组目录重新采样注册表快照后再构建空壳")
    parser.add_argument("--cobblemon-snapshot", type=pathlib.Path, default=SOURCE_DIR / "cobblemon-1.8.4-registries.json")
    parser.add_argument("--addon-snapshot", type=pathlib.Path, default=SOURCE_DIR / "registry-addons-reference.json")
    parser.add_argument("--verify", action="store_true", help="启动 -Xmx512M 实机空壳服务端验证注册表与完整快照一致")
    parser.add_argument("--deliver", type=pathlib.Path, action="append", default=[], help="额外交付目录（如 其余列车服务器更新mod）")
    args = parser.parse_args()

    cobble_snap = args.cobblemon_snapshot
    addon_snap = args.addon_snapshot
    verify_snap = addon_snap

    if args.refresh_from:
        mods = sorted(args.refresh_from.glob("*.jar"))
        cobble_jar = next(m for m in mods if m.name.startswith("Cobblemon-fabric-"))
        others = [m for m in mods if m != cobble_jar]
        cobble_snap = ROOT / "refreshed-cobblemon-registries.json"
        addon_snap = ROOT / "refreshed-addon-registries.json"
        refresh_snapshots(cobble_jar, others, cobble_snap, addon_snap)
        verify_snap = ROOT / "shell-refresh-snapshot.json"

    cobble_out, addon_out = build_shells(args.out, cobble_snap, addon_snap, verify=args.verify, full_snapshot_for_verify=verify_snap)
    for dst in args.deliver:
        dst.mkdir(parents=True, exist_ok=True)
        for obsolete in ["cobblenav-fabric-2.4.2.jar", "cobblemon_spawn_notification-fabric-1.5-fabric-1.2.1.jar", "Cobblemon-runtime-libs-1.8.4+1.21.1.jar"]:
            p = dst / obsolete
            if p.exists():
                p.unlink()
        shutil.copy2(cobble_out, dst / cobble_out.name)
        shutil.copy2(addon_out, dst / addon_out.name)
        print(f"DELIVERED -> {dst}")


if __name__ == "__main__":
    main()
