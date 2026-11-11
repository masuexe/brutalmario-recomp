#!/usr/bin/env python3
"""Build, cross-platform qualify, and package ROM-free Public Beta bundles (Linux & Windows).

Each generated archive contains:
  - Native executable + zero-Python-dependency bm_launcher[.exe]
  - BMPT v1 delta patch container (patch/brutalmario.bmpatch) against unmodified
    US Super Mario World (U) [!] (524,288 B headerless or 524,800 B headered)
  - Pack manifest (config/packs.manifest) naming data/rom.sfc and all 65 BM_* packs
  - Desktop config.ini, keybinds.ini, optional Special Zone / Complete-All scripts,
    and bilingual README

No .sfc/.smc ROM image or extracted data/packs/*.bin payload is shipped inside
the archive; players drop their own US Super Mario World (U) [!] ROM into the
folder and launch once to synthesize and SHA-256-verify all 66 runtime files.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_smw_delta as delta
from qualify_console_performance import qualify
from restoration_targets import RESTORATIONS

VCVARS_BAT = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
VC_REDIST_GLOB = "/mnt/c/Program Files/Microsoft Visual Studio/2022/Community/VC/Redist/MSVC/*/x64/Microsoft.VC143.CRT"
CMD_EXE = "/mnt/c/WINDOWS/system32/cmd.exe"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wsl_unc_root() -> str:
    return subprocess.check_output(["wslpath", "-w", str(ROOT)], text=True).strip()


def host_path(path: Path, platform: str) -> str:
    if platform == "windows" and sys.platform != "win32":
        return subprocess.check_output(["wslpath", "-w", str(path)], text=True).strip()
    return str(path)


def run_cmd_bat(bat_path: Path, log_path: Path, timeout: int = 600) -> None:
    bat_win = host_path(bat_path, "windows")
    with open(os.devnull, "rb") as devnull, log_path.open("w", encoding="utf-8") as logf:
        proc = subprocess.run(
            [CMD_EXE, "/c", bat_win],
            stdin=devnull,
            stdout=logf,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    if proc.returncode != 0:
        tail = "\n".join(log_path.read_text(errors="replace").splitlines()[-40:])
        raise RuntimeError(f"Windows command failed (rc={proc.returncode}, log={log_path}):\n{tail}")


def parse_linux_ninja_sources(target: str) -> tuple[list[str], list[str], str]:
    ninja_path = ROOT / "local/build" / target / "build.ninja"
    if not ninja_path.is_file():
        raise FileNotFoundError(f"Linux build.ninja missing at {ninja_path}; build Linux target first")
    text = ninja_path.read_text()
    matches = re.findall(r"^build (\S+\.o): (C_COMPILER|CXX_COMPILER)\S* (\S+)", text, re.M)
    if not matches:
        raise ValueError(f"no object rules parsed from {ninja_path}")
    c_rels: list[str] = []
    cxx_rels: list[str] = []
    for _, kind, abs_src in matches:
        rel = str(Path(abs_src).resolve().relative_to(ROOT)).replace("/", "\\")
        if kind == "C_COMPILER":
            c_rels.append(rel)
        else:
            cxx_rels.append(rel)
    title_match = re.search(r'-DSNES_GAME_TITLE="\\"(.*?)\\""', text)
    title = title_match.group(1) if title_match else f"Brutal Mario {target}"
    return c_rels, cxx_rels, title


def build_windows_game_binary(target: str, force: bool = False) -> Path:
    win_dir = ROOT / "local/build-windows" / target
    exe_name = RESTORATIONS[target]["binary"] + ".exe"
    exe_path = win_dir / exe_name
    receipt_path = win_dir / "m1-build-windows.json"
    cfg = json.loads((ROOT / "config/restorations" / f"{target}.json").read_text())
    expected_rom_sha = cfg["output"]["sha256"]

    if exe_path.is_file() and receipt_path.is_file() and not force:
        rec = json.loads(receipt_path.read_text())
        data = exe_path.read_bytes()
        if (
            rec.get("rom_sha256") == expected_rom_sha
            and rec.get("binary_sha256") == hashlib.sha256(data).hexdigest()
            and expected_rom_sha.encode() in data
        ):
            print(f"[Windows Build] Reusing verified {exe_path}")
            return exe_path

    sdl3_lib = ROOT / "local/build-windows/demo11-native-product/_deps/sdl3-build/SDL3-static.lib"
    if not sdl3_lib.is_file():
        raise FileNotFoundError(f"Prebuilt SDL3-static.lib missing at {sdl3_lib}")

    c_rels, cxx_rels, title = parse_linux_ninja_sources(target)
    exp_dir_name = [p for p in c_rels if p.endswith("\\src\\main.c")][0].split("\\")[2]

    objs_dir = win_dir / "objs"
    if objs_dir.exists():
        shutil.rmtree(objs_dir)
    objs_dir.mkdir(parents=True, exist_ok=True)

    includes = [
        f"local\\build\\{target}\\snesrecomp_rom_identity",
        "local\\upstream\\snesrecomp\\runner\\src",
        "local\\upstream\\snesrecomp\\runner\\src\\snes",
        "local\\upstream\\snesrecomp\\runner\\src\\desktop",
        f"local\\experiments\\{exp_dir_name}\\src",
        f"local\\experiments\\{exp_dir_name}\\recomp",
        "local\\upstream\\snesrecomp\\third_party\\gl_core",
        "local\\upstream\\snesrecomp\\third_party",
        f"local\\native-content-runtime\\{target}",
        "recomp",
        "local\\build-windows\\demo11-native-product\\_deps\\sdl3-build\\include-revision",
        "local\\build-windows\\demo11-native-product\\_deps\\sdl3-src\\include",
    ]
    inc_flags = " ".join(f'/I"{inc}"' for inc in includes)
    defines = (
        f'/DLNG_SDL3=1 /DM1_SEPARATE_ECHO_DEFAULT=1 /DSDL_MAIN_HANDLED '
        f'/DSNESRECOMP_ENABLE_MODS=1 /DSNESRECOMP_EXECUTION_DEFAULT_MODE=SNESRECOMP_EXECUTION_MODE_OFF '
        f'/DSNESRECOMP_EXPOSE_COVERAGE_MOD=0 /DSNESRECOMP_HAS_GENERATED_CODE=1 /DSNESRECOMP_SDL3=1 '
        f'/DSNES_GAME_TITLE="\\"{title}\\"" /DSNES_GAME_VERSION="\\"0.1.0\\"" '
        f'/DSNESRECOMP_BOOT_WATCHDOG_DIAGNOSTICS=0 /DSNESRECOMP_FUNC_SNAPSHOT=0 '
        f'/DSNESRECOMP_STACK_BALANCE_DIAGNOSTICS=0 /DWIN32 /D_WINDOWS /DNDEBUG'
    )

    rel_win_dir = f"local\\build-windows\\{target}"
    c_rsp = win_dir / "compile_c.rsp"
    cxx_rsp = win_dir / "compile_cxx.rsp"
    link_rsp = win_dir / "link.rsp"

    c_rsp.write_text(
        f"/nologo /MP /O2 /Ob2 /std:c11 /MD {defines} {inc_flags} /Fo\"{rel_win_dir}\\objs\\\\\" /c\n"
        + "\n".join(f'"{src}"' for src in c_rels)
        + "\n",
        encoding="utf-8",
    )
    cxx_rsp.write_text(
        f"/nologo /MP /EHsc /O2 /Ob2 /std:c++17 /MD {defines} {inc_flags} /Fo\"{rel_win_dir}\\objs\\\\\" /c\n"
        + "\n".join(f'"{src}"' for src in cxx_rels)
        + "\n",
        encoding="utf-8",
    )
    all_objs = [f'"{rel_win_dir}\\objs\\{Path(p.replace(chr(92), "/")).stem}.obj"' for p in (c_rels + cxx_rels)]
    sys_libs = (
        '"local\\build-windows\\demo11-native-product\\_deps\\sdl3-build\\SDL3-static.lib" '
        "dbghelp.lib opengl32.lib kernel32.lib user32.lib gdi32.lib winmm.lib imm32.lib "
        "ole32.lib oleaut32.lib version.lib uuid.lib advapi32.lib setupapi.lib shell32.lib "
        "dinput8.lib winspool.lib comdlg32.lib"
    )
    link_rsp.write_text("\n".join(all_objs) + "\n" + sys_libs + "\n", encoding="utf-8")

    bat = win_dir / "build_windows.bat"
    unc = wsl_unc_root()
    bat.write_text(
        "@echo off\r\n"
        f'pushd "{unc}" || exit /b 1\r\n'
        f'call "{VCVARS_BAT}" >nul || exit /b 1\r\n'
        f'cl @"{rel_win_dir}\\compile_c.rsp" || exit /b 1\r\n'
        f'cl @"{rel_win_dir}\\compile_cxx.rsp" || exit /b 1\r\n'
        f'link /nologo @"{rel_win_dir}\\link.rsp" /out:"{rel_win_dir}\\{exe_name}" /machine:x64 /INCREMENTAL:NO /subsystem:console || exit /b 1\r\n'
        "popd\r\n",
        encoding="utf-8",
    )

    print(f"[Windows Build] Compiling {len(c_rels)} C + {len(cxx_rels)} C++ files for {target} via MSVC...")
    run_cmd_bat(bat, win_dir / "build.log", timeout=900)

    data = exe_path.read_bytes()
    if not data.startswith(b"MZ") or expected_rom_sha.encode() not in data:
        raise RuntimeError("Built Windows executable failed PE or ROM SHA-256 check")
    if b"PRACTICE CHEAT CONSOLE" not in data:
        raise RuntimeError("Built Windows executable is missing PRACTICE CHEAT CONSOLE")

    receipt = {
        "target": target,
        "binary": exe_name,
        "binary_sha256": hashlib.sha256(data).hexdigest(),
        "rom_sha256": expected_rom_sha,
        "c_sources": len(c_rels),
        "cxx_sources": len(cxx_rels),
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"[Windows Build] Built {exe_path} ({len(data) // 1024} KB, sha256={receipt['binary_sha256'][:16]}...)")
    return exe_path


def build_launchers(cache_dir: Path) -> tuple[Path, Path]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    linux_out = cache_dir / "bm_launcher"
    win_out = cache_dir / "bm_launcher.exe"

    subprocess.run(
        [
            "gcc", "-O2", "-Wall", "-Wextra", "-Werror", "-std=c11",
            f"-I{ROOT / 'local/upstream/snesrecomp/runner/src'}",
            str(ROOT / "recomp/bm_release_launcher.c"),
            str(ROOT / "local/upstream/snesrecomp/runner/src/sha256.c"),
            "-o", str(linux_out),
        ],
        check=True,
    )
    linux_out.chmod(0o755)

    rel_cache = str(cache_dir.resolve().relative_to(ROOT)).replace("/", "\\")
    bat = cache_dir / "build_launcher_win.bat"
    bat.write_text(
        "@echo off\r\n"
        f'pushd "{wsl_unc_root()}" || exit /b 1\r\n'
        f'call "{VCVARS_BAT}" >nul || exit /b 1\r\n'
        f'cl /nologo /O2 /W4 /WX /MT /std:c11 /utf-8 /DWIN32 /D_CRT_SECURE_NO_WARNINGS '
        f'/I"local\\upstream\\snesrecomp\\runner\\src" '
        f'"recomp\\bm_release_launcher.c" "local\\upstream\\snesrecomp\\runner\\src\\sha256.c" '
        f'/Fo"{rel_cache}\\\\" /Fe"{rel_cache}\\bm_launcher.exe" '
        f'/link /INCREMENTAL:NO /subsystem:console kernel32.lib user32.lib shell32.lib || exit /b 1\r\n'
        "popd\r\n",
        encoding="utf-8",
    )
    run_cmd_bat(bat, cache_dir / "build_launcher_win.log", timeout=120)
    if not win_out.is_file() or not win_out.read_bytes().startswith(b"MZ"):
        raise RuntimeError("Failed to compile Windows bm_launcher.exe")
    return linux_out, win_out


def verify_platform_binary(target: str, platform: str, binary: Path, out_dir: Path, frames: int = 60) -> dict:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    rest_dir = ROOT / "local/restoration" / target
    packs = delta.collect_target_packs(target)
    script = out_dir / "probe.script"
    script.write_text(f"turbo on\nwait {frames}\ndump probe\nquit\n")

    exe_to_run = binary
    if platform == "windows" and sys.platform != "win32":
        exe_to_run = out_dir / "probe.exe"
        shutil.copy2(binary, exe_to_run)
        exe_to_run.chmod(0o755)

    for mode in ("closed", "console"):
        cap = out_dir / mode
        cap.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith(("BM_", "SNESRECOMP_", "M1_"))}
        env.update(
            SDL_VIDEODRIVER="dummy",
            SDL_AUDIODRIVER="dummy",
            SNESRECOMP_HOST_PROFILE="1",
            SNESRECOMP_APU_MASTER_CLOCK="1",
            SNESRECOMP_REWIND="0",
            SNESRECOMP_DUMP_DIR=host_path(cap, platform),
        )
        for p in packs:
            env[p["variable"]] = host_path(p["source_path"], platform)
        if mode == "console":
            env.update(SNESRECOMP_CHEAT_CONSOLE="1", SNESRECOMP_CHEAT_CONSOLE_COMMANDS="help;close")
        if platform == "windows" and sys.platform != "win32":
            forwarded = [k for k in env if k.startswith(("BM_", "SNESRECOMP_", "SDL_"))]
            env["WSLENV"] = ":".join(forwarded)

        cmd = [
            str(exe_to_run),
            "--no-launcher",
            "--config", host_path(ROOT / "recomp/m1-config.ini", platform),
            "--rom", host_path(rest_dir / "rom.sfc", platform),
            "--script", host_path(script, platform),
        ]
        (cap / "receipt.json").write_text(
            json.dumps(
                {
                    "target": target,
                    "platform": platform,
                    "mode": mode,
                    "rom_sha256": sha256_file(rest_dir / "rom.sfc"),
                    "binary_sha256": sha256_file(binary),
                    "script_sha256": sha256_file(script),
                    "command": cmd,
                },
                indent=2,
            )
            + "\n"
        )
        with open(os.devnull, "rb") as devnull, (cap / "run.log").open("w") as logf:
            subprocess.run(cmd, stdin=devnull, stdout=logf, stderr=subprocess.STDOUT, cwd=cap, env=env, check=True, timeout=90)

        info = json.loads((cap / "probe.info.json").read_text())
        if info["frame"] != frames:
            raise ValueError(f"{platform}/{mode} frame mismatch: {info['frame']} != {frames}")

    comp = qualify(out_dir / "closed", out_dir / "console")
    console_log = (out_dir / "console/run.log").read_text(errors="replace")
    if "practice cheat console OPEN" not in console_log or "practice cheat console CLOSED" not in console_log:
        raise ValueError(f"{platform} console lifecycle missing")
    for side in ("before", "after"):
        if comp[side]["guest_mean_ms"] > 16.667:
            raise ValueError(f"{platform} performance gate failed: {comp[side]['guest_mean_ms']} ms")
    return comp


def format_manifest_text(target: str) -> str:
    cfg = json.loads((ROOT / "config/restorations" / f"{target}.json").read_text())
    lines = [
        "# Brutal Mario Native PC Content Manifest",
        f"ROM\tdata/rom.sfc\t{cfg['output']['size']}\t{cfg['output']['sha256']}",
    ]
    for p in delta.collect_target_packs(target):
        lines.append(f"{p['variable']}\t{p['rel_path']}\t{p['size']}\t{p['sha256']}")
    return "\n".join(lines) + "\n"


def format_config_ini(platform: str) -> str:
    method = "Direct3D11" if platform == "windows" else "SDL-Software"
    return (
        "[Graphics]\n"
        f"OutputMethod={method}\n"
        "VSync=1\n"
        "NewRenderer=0\n"
        "WindowScale=3\n"
        "NoSpriteLimits=0\n"
        "Widescreen=0\n\n"
        "[Sound]\n"
        "EnableAudio=1\n\n"
        "[General]\n"
        "RunAhead=0\n"
    )


def format_readme(target: str) -> str:
    return f"""========================================================================
  Brutal Mario (鬼畜马里奥 / Super Kitiku Mario) - 原生 PC 重编译公测版
  Public Beta ({target}) — Windows x64 & Linux x86_64
========================================================================

【公测版说明 / Public Beta Notice】
  本版本为 Brutal Mario 原生 PC 重编译公开测试版（Public Beta），突破了
  原版 SFC 4MB 卡带容量限制，采用外部扩展包架构集成了 Demo 1-1、demoOnly1、
  Star World 九星路线、Mazo 走廊与中 Boss、库巴七子、威利胶囊多阶段图块，
  并恢复了原版 SMW 缺失曲目、采样组与全 256 槽位自定义精灵时序版本。
  注：本版本定位为公开测试版（Public Beta），欢迎反馈关卡、音乐或演出问题；
  原作者在历史补丁中未制作通关出口的隐藏内容（如 Star World Center Boss）按原貌保留。

------------------------------------------------------------------------
【第一步：首次运行准备（仅需一次，耗时不到 1 秒）】
【Step 1: First-Time ROM Setup (One-time, < 1 second)】
------------------------------------------------------------------------
  本发布包【不包含】任何任天堂原版 ROM 文件，也【不需要】安装 Python。
  1. 请自备一份未修改的【美版】原版《Super Mario World (U) [!]》ROM 文件：
     - 文件后缀：.sfc 或 .smc 均可（文件名任意，无需改名）
     - 文件大小：524,288 字节（无头）或 524,800 字节（带 512 字节头自动剥离）
     - 无头 SHA-256：0838e531fe22c077528febe14cb3ff7c492f1f5fa8de354192bdff7137c27f5b
  2. 将该 ROM 直接放入本压缩包解压后的【根目录】（与启动脚本同一层目录）。
  3. 正常启动游戏即可！启动器会自动校验原版 ROM，离线合成 data/rom.sfc 与
     全部 65 个原生扩展资源包（data/packs/*.bin）并进行 SHA-256 完整性校验，
     合成完成后立即进入游戏。之后每次启动将直接秒开游戏。

  (English: Place an unmodified US 'Super Mario World (U) [!]' .sfc or .smc
   ROM into this root folder and launch the game. On first run, the built-in
   native launcher automatically synthesizes and SHA-256-verifies data/rom.sfc
   and all 65 native content packs in under 1 second. No Python required.)

------------------------------------------------------------------------
【第二步：启动游戏 / Launching the Game】
------------------------------------------------------------------------
  [Windows 用户]
  • 双击【启动游戏.bat】
      -> 默认纯净原版闯关模式（推荐正式游玩，进度保存在 saves/save.srm）
  • 双击【关卡全开版(SpecialZone).bat】
      -> 解锁全地图并直达 Special Zone 特别区（自动备份原存档至 save.srm.before-cheat）
  • 双击【关卡全开版(普通大地图).bat】
      -> 在普通大地图解锁全部路线与隐藏关（自动备份原存档）

  [Linux 用户 (x86_64)]
  • 依赖说明：仅需系统安装 SDL2 运行库（Ubuntu/Debian: sudo apt install libsdl2-2.0-0；
    Arch: sudo pacman -S sdl2；Fedora: sudo dnf install SDL2）。
  • 原版闯关模式：./play.sh
  • Special Zone 直达：./play-special-zone.sh
  • 普通大地图全开：./play-complete-all.sh

------------------------------------------------------------------------
【操作按键与设置 / Controls & Settings】
------------------------------------------------------------------------
  [默认键盘键位]（可在 bin/keybinds.ini 中自由修改）
  • 方向键 (↑ ↓ ← →) : 移动 / 蹲下 / 进水管
  • Z                : 普通跳跃 (SNES B)
  • X                : 旋转跳 / 确认 (SNES A)
  • A                : 加速跑 / 拿壳 / 吞食 (SNES Y)
  • S                : 备用键 (SNES X)
  • C / V            : L / R 切屏键
  • Enter (回车)     : Start (暂停 / 确认)
  • Right Shift      : Select (释放储备道具 / 地图退出已通关关卡)
  • 手柄支持         : Xbox / PlayStation / Switch 手柄即插即用自动识别

  [内置公测练习控制台 / Built-in Practice Console]
  • 游戏中按键盘左上角反引号键【 ` 】（波浪号 ~ 键）可随时呼出/关闭内置控制台：
    - help           : 查看命令列表
    - invincible     : 切换无敌星状态
    - swim           : 切换全屏空中游泳
    - lives 99       : 设置生命数
    - teleport 0x151 : 传送至指定房间号（0x000 - 0x1FF）
    - xy X Y         : 关卡内坐标瞬移
    - Esc            : 关闭控制台

  [画面与音量调整]
  • 编辑 config/config.ini 可修改窗口倍率（WindowScale=3 默认 3 倍大小）、
    垂直同步（VSync=1）与音频开关（EnableAudio=1）。
========================================================================
"""


def write_zip_preserving_modes(src_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # Include empty directories (like saves/) explicitly
        for path in sorted(src_dir.rglob("*")):
            rel = Path(src_dir.name) / path.relative_to(src_dir)
            if path.is_dir():
                if not any(path.iterdir()):
                    zi = zipfile.ZipInfo(rel.as_posix() + "/")
                    zi.external_attr = (stat.S_IFDIR | 0o755) << 16
                    zf.writestr(zi, b"")
            else:
                mode = stat.S_IMODE(path.stat().st_mode)
                zi = zipfile.ZipInfo.from_file(path, arcname=rel.as_posix())
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = (stat.S_IFREG | mode) << 16
                zf.writestr(zi, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)


def stage_platform_bundle(
    target: str,
    platform: str,
    game_binary: Path,
    launcher_binary: Path,
    patch_bytes: bytes,
    bundle_dir: Path,
) -> Path:
    zip_path = bundle_dir.with_name(bundle_dir.name + ".zip")
    if bundle_dir.exists() or zip_path.exists():
        raise FileExistsError(f"Destination already exists: {bundle_dir} or {zip_path}")

    for sub in ("bin/mods/preloaded/packages", "config", "patch", "scripts", "saves"):
        (bundle_dir / sub).mkdir(parents=True, exist_ok=True)

    # 1. Binaries + keybinds + mod state
    if platform == "windows":
        dest_game = bundle_dir / "bin/BrutalMario.exe"
        dest_launcher = bundle_dir / "bin/bm_launcher.exe"
        shutil.copy2(game_binary, dest_game)
        shutil.copy2(launcher_binary, dest_launcher)
        # Bundle official Microsoft VC143 app-local CRT DLLs so bare Windows PCs need no VC++ installer
        import glob
        redist_dirs = sorted(glob.glob(VC_REDIST_GLOB))
        if not redist_dirs:
            raise FileNotFoundError(f"VC++ Redist folder not found matching {VC_REDIST_GLOB}")
        redist_dir = Path(redist_dirs[-1])
        for dll_name in ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"):
            shutil.copy2(redist_dir / dll_name, bundle_dir / "bin" / dll_name)
    else:
        dest_game = bundle_dir / "bin/BrutalMario"
        dest_launcher = bundle_dir / "bin/bm_launcher"
        shutil.copy2(game_binary, dest_game)
        shutil.copy2(launcher_binary, dest_launcher)
        dest_game.chmod(0o755)
        dest_launcher.chmod(0o755)

    keybinds_src = ROOT / "local/build" / target / "keybinds.ini"
    if not keybinds_src.is_file():
        keybinds_src = ROOT / "local/build-windows/demo11-native-product/keybinds.ini"
    shutil.copy2(keybinds_src, bundle_dir / "bin/keybinds.ini")

    state_toml = ROOT / "local/build" / target / "mods/preloaded/state.toml"
    if state_toml.is_file():
        shutil.copy2(state_toml, bundle_dir / "bin/mods/preloaded/state.toml")

    # 2. Config & manifest
    (bundle_dir / "config/config.ini").write_text(format_config_ini(platform), encoding="utf-8")
    (bundle_dir / "config/packs.manifest").write_text(format_manifest_text(target), encoding="utf-8")

    # 3. Delta patch (NO ROM or data/packs/*.bin inside the release!)
    (bundle_dir / "patch/brutalmario.bmpatch").write_bytes(patch_bytes)

    # 4. Practice / unlock scripts
    for sname in ("cheat-special-zone.script", "cheat-complete-all.script"):
        shutil.copy2(ROOT / "recomp/inputs" / sname, bundle_dir / "scripts" / sname)

    # 5. Zero-Python entry scripts + README
    if platform == "windows":
        # Pure ASCII batch body avoids GBK/UTF-8 cmd.exe codepage pitfalls on Windows
        (bundle_dir / "启动游戏.bat").write_bytes(
            b'@echo off\r\n"%~dp0bin\\bm_launcher.exe" %*\r\n'
        )
        (bundle_dir / "关卡全开版(SpecialZone).bat").write_bytes(
            b'@echo off\r\n"%~dp0bin\\bm_launcher.exe" --special-zone %*\r\n'
        )
        (bundle_dir / "关卡全开版(普通大地图).bat").write_bytes(
            b'@echo off\r\n"%~dp0bin\\bm_launcher.exe" --complete-all %*\r\n'
        )
        readme_bytes = format_readme(target).replace("\n", "\r\n").encode("utf-8")
        (bundle_dir / "说明文档-README.txt").write_bytes(readme_bytes)
    else:
        sh_header = '#!/bin/sh\nDIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
        for fname, flag in (
            ("play.sh", ""),
            ("play-special-zone.sh", " --special-zone"),
            ("play-complete-all.sh", " --complete-all"),
        ):
            p = bundle_dir / fname
            p.write_text(sh_header + f'exec "$DIR/bin/bm_launcher"{flag} "$@"\n', encoding="utf-8")
            p.chmod(0o755)
        (bundle_dir / "说明文档-README.txt").write_text(format_readme(target), encoding="utf-8")

    files_manifest = {
        str(p.relative_to(bundle_dir)).replace("\\", "/"): sha256_file(p)
        for p in sorted(bundle_dir.rglob("*"))
        if p.is_file()
    }
    (bundle_dir / "files.json").write_text(json.dumps(files_manifest, indent=2) + "\n", encoding="utf-8")

    write_zip_preserving_modes(bundle_dir, zip_path)

    # Strict audit: verify zero .sfc/.smc or data/packs/*.bin inside the ZIP!
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        forbidden = [
            n for n in names
            if n.lower().endswith((".sfc", ".smc")) or "/data/packs/" in n or n.endswith(".bin")
        ]
        if forbidden:
            raise AssertionError(f"Forbidden ROM/pack files leaked into {zip_path}: {forbidden}")
        if not any(n.endswith("/saves/") for n in names):
            raise AssertionError(f"Empty saves/ directory missing in {zip_path}")

    return zip_path


def run_end_to_end_smoke_test(
    linux_zip: Path,
    windows_zip: Path,
    base_rom_path: Path,
    smoke_root: Path,
) -> dict:
    """Simulate real players extracting into Unicode-named folders and launching with their SMW ROM."""
    if smoke_root.exists():
        shutil.rmtree(smoke_root)
    smoke_root.mkdir(parents=True)

    base_bytes = delta.normalize_base_rom(base_rom_path.read_bytes())

    # 1. Linux clean-room simulation ( inside Chinese + space directory! )
    lin_extract = smoke_root / "鬼畜马里奥 公测 Linux"
    lin_extract.mkdir(parents=True)
    subprocess.run(["unzip", "-q", str(linux_zip), "-d", str(lin_extract)], check=True)
    lin_pkg = next(p for p in lin_extract.iterdir() if p.is_dir())

    # 1a. Missing ROM must return exit code 2 cleanly
    res_missing = subprocess.run(
        [str(lin_pkg / "play.sh"), "--setup-only"],
        capture_output=True, text=True, check=False,
    )
    if res_missing.returncode != 2:
        raise RuntimeError(f"Expected rc=2 when SMW ROM missing on Linux, got {res_missing.returncode}")

    # 1b. Place headerless .sfc and boot 60 frames directly through play.sh!
    (lin_pkg / "Super Mario World (U) [!].sfc").write_bytes(base_bytes)
    lin_dump = smoke_root / "lin_dump"
    lin_dump.mkdir()
    probe = smoke_root / "smoke60.script"
    probe.write_text("turbo on\nwait 60\ndump smoke\nquit\n")
    lin_env = {k: v for k, v in os.environ.items() if not k.startswith(("BM_", "SNESRECOMP_", "M1_"))}
    lin_env.update(
        SDL_VIDEODRIVER="dummy",
        SDL_AUDIODRIVER="dummy",
        SNESRECOMP_DUMP_DIR=str(lin_dump),
    )
    subprocess.run(
        [str(lin_pkg / "play.sh"), "--script", str(probe)],
        env=lin_env, check=True, timeout=60,
    )
    subprocess.run([str(lin_pkg / "bin/bm_launcher"), "--verify"], check=True)

    # 2. Windows clean-room simulation ( inside Chinese + space directory, with 512B SMC header! )
    win_extract = smoke_root / "鬼畜马里奥 公测 Windows"
    win_extract.mkdir(parents=True)
    subprocess.run(["unzip", "-q", str(windows_zip), "-d", str(win_extract)], check=True)
    win_pkg = next(p for p in win_extract.iterdir() if p.is_dir())

    # 2a. Missing ROM must return exit code 2 cleanly (with BM_NO_MSGBOX=1)
    miss_bat = smoke_root / "test_win_missing.bat"
    miss_bat.write_text(
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        "set BM_NO_MSGBOX=1\r\n"
        f'call "{host_path(win_pkg / "启动游戏.bat", "windows")}" --setup-only\r\n'
        "if %ERRORLEVEL% equ 2 exit /b 0\r\n"
        "exit /b 1\r\n",
        encoding="utf-8",
    )
    run_cmd_bat(miss_bat, smoke_root / "win_missing.log", timeout=60)

    # 2b. Place 524,800-byte SMC-headered ROM and boot 60 frames through 启动游戏.bat!
    (win_pkg / "my_smw_usa_headered.smc").write_bytes(b"\x00" * 512 + base_bytes)
    win_dump = smoke_root / "win_dump"
    win_dump.mkdir()
    boot_bat = smoke_root / "test_win_boot.bat"
    boot_bat.write_text(
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        "set BM_NO_MSGBOX=1\r\n"
        "set SDL_VIDEODRIVER=dummy\r\n"
        "set SDL_AUDIODRIVER=dummy\r\n"
        f'set "SNESRECOMP_DUMP_DIR={host_path(win_dump, "windows")}"\r\n'
        f'call "{host_path(win_pkg / "启动游戏.bat", "windows")}" --script "{host_path(probe, "windows")}" || exit /b 1\r\n'
        f'"{host_path(win_pkg / "bin/bm_launcher.exe", "windows")}" --verify || exit /b 1\r\n',
        encoding="utf-8",
    )
    run_cmd_bat(boot_bat, smoke_root / "win_boot.log", timeout=120)

    # 3. Assert 100% binary state parity between unpacked Linux ZIP and unpacked Windows ZIP!
    parity = {}
    for suffix in ("wram.bin", "vram.bin", "cgram.bin", "oam.bin", "sram.bin", "fb.bgrx", "fb.bmp"):
        lb = (lin_dump / f"smoke.{suffix}").read_bytes()
        wb = (win_dump / f"smoke.{suffix}").read_bytes()
        if lb != wb:
            raise AssertionError(f"Cross-platform ZIP smoke mismatch on smoke.{suffix}")
        parity[suffix] = hashlib.sha256(lb).hexdigest()

    return {
        "linux_zip": str(linux_zip),
        "linux_zip_sha256": sha256_file(linux_zip),
        "linux_zip_size_bytes": linux_zip.stat().st_size,
        "windows_zip": str(windows_zip),
        "windows_zip_sha256": sha256_file(windows_zip),
        "windows_zip_size_bytes": windows_zip.stat().st_size,
        "frame60_binary_parity_sha256": parity,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="demo11-native-product-r43")
    parser.add_argument("--base-rom", type=Path, default=ROOT.parent / "roms/Super Mario World (U) [!].smc")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "dist/public-beta-r43")
    parser.add_argument("--diag-dir", type=Path, default=ROOT / "local/diagnostics/public-beta-r43")
    parser.add_argument("--force-rebuild-windows", action="store_true")
    args = parser.parse_args()

    target = args.target
    out_dir = args.out_dir.resolve()
    diag_dir = args.diag_dir.resolve()
    if out_dir.exists():
        raise SystemExit(f"Output directory already exists: {out_dir} (choose a fresh --out-dir)")

    linux_game_bin = ROOT / "local/build" / target / RESTORATIONS[target]["binary"]
    if not linux_game_bin.is_file():
        raise SystemExit(f"Linux binary missing at {linux_game_bin}; run tools/m1.py build first")

    # 1. Build Windows game binary + cross-platform bm_launcher
    windows_game_bin = build_windows_game_binary(target, force=args.force_rebuild_windows)
    linux_launcher, windows_launcher = build_launchers(diag_dir / "cache")

    # 2. Run 60-frame performance + cheat-console qualification on both platforms
    print("[Qualify] Verifying Linux binary (closed + console + guest_mean_ms)...")
    lin_qual = verify_platform_binary(target, "linux", linux_game_bin, diag_dir / "qualify-linux")
    print(f"  Linux guest_mean_ms: closed={lin_qual['before']['guest_mean_ms']:.3f} ms, console={lin_qual['after']['guest_mean_ms']:.3f} ms")

    print("[Qualify] Verifying Windows binary (closed + console + guest_mean_ms)...")
    win_qual = verify_platform_binary(target, "windows", windows_game_bin, diag_dir / "qualify-windows")
    print(f"  Windows guest_mean_ms: closed={win_qual['before']['guest_mean_ms']:.3f} ms, console={win_qual['after']['guest_mean_ms']:.3f} ms")
    l_closed = diag_dir / "qualify-linux/closed"
    w_closed = diag_dir / "qualify-windows/closed"
    for suffix in ("wram.bin", "vram.bin", "sram.bin", "cgram.bin", "oam.bin", "fb.bgrx", "fb.bmp"):
        if (l_closed / f"probe.{suffix}").read_bytes() != (w_closed / f"probe.{suffix}").read_bytes():
            raise RuntimeError(f"Cross-platform binary dump mismatch: probe.{suffix}")
    for suffix in ("info.json", "regs.json", "apu.tsv", "ppuw.tsv"):
        lb = (l_closed / f"probe.{suffix}").read_bytes().replace(b"\r\n", b"\n")
        wb = (w_closed / f"probe.{suffix}").read_bytes().replace(b"\r\n", b"\n")
        if lb != wb:
            raise RuntimeError(f"Cross-platform text dump mismatch: probe.{suffix}")
    print("  Cross-platform state & framebuffer parity (Linux vs Windows): PASSED")

    # 3. Build BMPT v1 delta patch against US Super Mario World (U) [!]
    print("[Delta] Building BMPT v1 delta patch container...")
    patch_bytes, patch_stats = delta.build_patch_bytes(target, args.base_rom)

    # 4. Stage Linux & Windows Public Beta ZIPs
    out_dir.mkdir(parents=True, exist_ok=False)
    lin_name = "BrutalMario-PublicBeta-r43-Linux"
    win_name = "BrutalMario-PublicBeta-r43-Windows"
    linux_zip = stage_platform_bundle(
        target, "linux", linux_game_bin, linux_launcher, patch_bytes, out_dir / lin_name
    )
    windows_zip = stage_platform_bundle(
        target, "windows", windows_game_bin, windows_launcher, patch_bytes, out_dir / win_name
    )

    # 5. Clean-room end-to-end smoke test (Unicode folder names, missing ROM check, SMC header strip, 60f parity)
    print("[Smoke] Running clean-room player simulation on unpacked Linux & Windows ZIPs...")
    smoke_report = run_end_to_end_smoke_test(linux_zip, windows_zip, args.base_rom, diag_dir / "smoke")

    receipt = {
        "target": target,
        "linux_binary_sha256": sha256_file(linux_game_bin),
        "windows_binary_sha256": sha256_file(windows_game_bin),
        "linux_launcher_sha256": sha256_file(linux_launcher),
        "windows_launcher_sha256": sha256_file(windows_launcher),
        "patch": patch_stats,
        "qualification": {
            "linux_closed_guest_mean_ms": lin_qual["before"]["guest_mean_ms"],
            "linux_console_guest_mean_ms": lin_qual["after"]["guest_mean_ms"],
            "windows_closed_guest_mean_ms": win_qual["before"]["guest_mean_ms"],
            "windows_console_guest_mean_ms": win_qual["after"]["guest_mean_ms"],
        },
        "archives": smoke_report,
    }
    receipt_path = out_dir / "release-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\n[SUCCESS] Public Beta packages built and verified:")
    print(f"  Linux ZIP  : {linux_zip} ({linux_zip.stat().st_size // 1024} KB)")
    print(f"  Windows ZIP: {windows_zip} ({windows_zip.stat().st_size // 1024} KB)")
    print(f"  Receipt    : {receipt_path}")


if __name__ == "__main__":
    main()
