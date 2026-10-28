#!/usr/bin/env python3
"""Package the native product target into a self-contained Windows release bundle."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import native_sprite_gap

TARGET = 'demo11-native-product'

PACKS_MAPPING = [
    (p['variable'], p['pack_file']) for p in native_sprite_gap.packs(TARGET)
]


def create_launcher_py():
    """Return the code for play.py inside the release bundle."""
    return '''#!/usr/bin/env python3
"""Brutal Mario Native PC Launcher.

Supports original game progression, Special Zone warp cheat, and full overworld completion.
Auto-configures all native content packs and mounts the runtime.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

PACKS = [
''' + '\n'.join([f"    ('{var}', '{fn}')," for var, fn in PACKS_MAPPING]) + '''
]


def main():
    parser = argparse.ArgumentParser(description='Brutal Mario Native PC Launcher')
    parser.add_argument('-s', '--special-zone', action='store_true',
                        help='Open completion flags and warp straight to Special Zone (推荐：直达 Special Zone 选关)')
    parser.add_argument('-c', '--complete-all', action='store_true',
                        help='Open completion flags on the standard overworld map (大地图全开)')
    parser.add_argument('--scale', type=int, choices=[1, 2, 3, 4, 5],
                        help='Override window scale (1x - 5x)')
    parser.add_argument('--fullscreen', action='store_true',
                        help='Launch in fullscreen mode')
    args, unknown = parser.parse_known_args()

    # Determine binary
    exe_win = ROOT / 'bin' / 'BrutalMario.exe'
    exe_linux = ROOT / 'bin' / 'BrutalMarioDemo11NativeProductSNESRecomp'
    if exe_win.is_file() and sys.platform.startswith('win'):
        binary = exe_win
    elif exe_linux.is_file():
        binary = exe_linux
    elif exe_win.is_file():
        binary = exe_win
    else:
        raise SystemExit('Game executable not found in bin/')

    rom = ROOT / 'data' / 'rom.sfc'
    config = ROOT / 'config' / 'config.ini'
    if not rom.is_file():
        raise SystemExit('ROM not found at data/rom.sfc')

    # Environment for packs
    env = dict(os.environ)
    packs_dir = ROOT / 'data' / 'packs'
    for var, pack_file in PACKS:
        pack_path = packs_dir / pack_file
        if not pack_path.is_file():
            raise SystemExit(f'Missing pack file: {pack_file}')
        env[var] = str(pack_path.resolve())

    # Session / save directory
    saves_dir = ROOT / 'saves'
    saves_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(binary.resolve()),
        '--no-launcher',
        '--config', str(config.resolve()),
        '--rom', str(rom.resolve()),
    ]

    mode_name = '【原版游玩模式】'
    if args.special_zone:
        script = ROOT / 'scripts' / 'cheat-special-zone.script'
        if not script.is_file():
            raise SystemExit('Cheat script not found at scripts/cheat-special-zone.script')
        cmd.extend(['--script', str(script.resolve())])
        mode_name = '【关卡全开 - Special Zone 特别区直达】'
    elif args.complete_all:
        script = ROOT / 'scripts' / 'cheat-complete-all.script'
        if not script.is_file():
            raise SystemExit('Cheat script not found at scripts/cheat-complete-all.script')
        cmd.extend(['--script', str(script.resolve())])
        mode_name = '【关卡全开 - 大地图解锁】'

    if unknown:
        cmd.extend(unknown)

    print('========================================')
    print('  Brutal Mario (鬼畜马里奥) 重编译原生 PC 版')
    print(f'  启动模式: {mode_name}')
    print('========================================')
    print(f'已挂载全部 {len(PACKS)} 个原生扩展资源包。')
    print('游戏启动中，祝您游玩愉快！')

    try:
        subprocess.run(cmd, env=env, cwd=str(ROOT), check=False)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
'''


def create_bat_scripts():
    """Return content of 启动游戏.bat, 关卡全开版(SpecialZone).bat, 关卡全开版(普通大地图).bat."""
    lines_normal = [
        '@echo off',
        'chcp 65001 >nul',
        'cd /d "%~dp0"',
        'title Brutal Mario Native PC - 启动游戏',
        'where python >nul 2>nul',
        'if %ERRORLEVEL% equ 0 (',
        '    python play.py %*',
        ') else (',
        '    where py >nul 2>nul',
        '    if %ERRORLEVEL% equ 0 (',
        '        py play.py %*',
        '    ) else (',
        '        echo [提示] 未检测到 Python，使用原生批处理直接加载运行...',
        '        set "BM_DIR=%~dp0data\\packs"',
    ]
    for var, fn in PACKS_MAPPING:
        lines_normal.append(f'        set "{var}=%BM_DIR%\\{fn}"')
    lines_normal.extend([
        '        start "" "%~dp0bin\\BrutalMario.exe" --no-launcher --config "%~dp0config\\config.ini" --rom "%~dp0data\\rom.sfc" %*',
        '    )',
        ')',
    ])

    lines_special = [
        '@echo off',
        'chcp 65001 >nul',
        'cd /d "%~dp0"',
        'title Brutal Mario Native PC - 关卡全开版 (Special Zone 直达)',
        'where python >nul 2>nul',
        'if %ERRORLEVEL% equ 0 (',
        '    python play.py --special-zone %*',
        ') else (',
        '    where py >nul 2>nul',
        '    if %ERRORLEVEL% equ 0 (',
        '        py play.py --special-zone %*',
        '    ) else (',
        '        echo [提示] 未检测到 Python，使用原生批处理直接加载运行...',
        '        set "BM_DIR=%~dp0data\\packs"',
    ]
    for var, fn in PACKS_MAPPING:
        lines_special.append(f'        set "{var}=%BM_DIR%\\{fn}"')
    lines_special.extend([
        '        start "" "%~dp0bin\\BrutalMario.exe" --no-launcher --config "%~dp0config\\config.ini" --rom "%~dp0data\\rom.sfc" --script "%~dp0scripts\\cheat-special-zone.script" %*',
        '    )',
        ')',
    ])

    lines_complete = [
        '@echo off',
        'chcp 65001 >nul',
        'cd /d "%~dp0"',
        'title Brutal Mario Native PC - 关卡全开版 (大地图)',
        'where python >nul 2>nul',
        'if %ERRORLEVEL% equ 0 (',
        '    python play.py --complete-all %*',
        ') else (',
        '    where py >nul 2>nul',
        '    if %ERRORLEVEL% equ 0 (',
        '        py play.py --complete-all %*',
        '    ) else (',
        '        echo [提示] 未检测到 Python，使用原生批处理直接加载运行...',
        '        set "BM_DIR=%~dp0data\\packs"',
    ]
    for var, fn in PACKS_MAPPING:
        lines_complete.append(f'        set "{var}=%BM_DIR%\\{fn}"')
    lines_complete.extend([
        '        start "" "%~dp0bin\\BrutalMario.exe" --no-launcher --config "%~dp0config\\config.ini" --rom "%~dp0data\\rom.sfc" --script "%~dp0scripts\\cheat-complete-all.script" %*',
        '    )',
        ')',
    ])

    return (
        '\r\n'.join(lines_normal) + '\r\n',
        '\r\n'.join(lines_special) + '\r\n',
        '\r\n'.join(lines_complete) + '\r\n',
    )


def create_readme():
    return '''======================================================================
  Brutal Mario (鬼畜马里奥 / 鬼畜玛利欧) - 原生 PC 重编译完整版
======================================================================

【版本说明】
  本版本为 Brutal Mario 的 PC 原生重编译最终完整版（Native PC Port）。
  突破了原版 SFC 卡带的物理容量限制，采用 Native 扩展架构完整集成了：
  - 经典的 Demo 1-1 / demoOnly1 主线关卡与音画
  - 完整的 Star World（星星世界）隐藏路线与全新 Boss 机制
  - 七个库巴小子（Seven Koopalings）全新战斗机制与专属音乐
  - 完整的 Mazo 走廊与定制怪物代码（9B, 9C, B0 等全部就绪，精准还原 Donor 行为）
  - 全新 SDL3 现代音频与图形渲染后端，支持超低输入延迟。

----------------------------------------------------------------------
【快速启动指南】
----------------------------------------------------------------------
本整合包提供方便的游玩方式，解压即玩：

1. 【直接双击运行】（推荐，无需任何复杂操作）：
   - 双击【启动游戏.bat】
     -> 进入【原版模式】（从 1-1 耀西岛正常闯关）
   - 双击【关卡全开版(SpecialZone).bat】（推荐作弊入口）
     -> 进入【关卡全开版】，直接传送至 Special Zone 特别区，自由挑战高难度与隐藏关卡！
   - 双击【关卡全开版(普通大地图).bat】
     -> 进入【关卡全开版】，在普通大地图上解锁全部星星路线与关卡。

2. 【通过 Python 启动】（如果您习惯命令行）：
   - 原版模式：python play.py
   - Special Zone 全开：python play.py --special-zone
   - 大地图全开：python play.py --complete-all

----------------------------------------------------------------------
【操作按键说明】
----------------------------------------------------------------------
【键盘默认键位】
  - 方向键 (↑ ↓ ← →) : 移动 / 蹲下 / 抬头
  - Z                : 跳跃 (对应 SNES B 键)
  - X                : 旋转跳 / 加速 (对应 SNES A 键)
  - A                : 冲刺 / 吞食 (对应 SNES Y 键)
  - S                : 备用按键 (对应 SNES X 键)
  - C / V            : L / R 键
  - 回车 (Enter)     : Start 键 (暂停 / 确定)
  - 右 Shift         : Select 键 (释放储备道具 / 取消)

【手柄支持】
  - 支持常见 Xbox、PlayStation、Nintendo Switch 手柄，即插即用自动识别！

【自定义键位】
  - 如果需要修改键盘按键，可使用记事本打开 `config/keybinds.ini` 自行调整后保存。

----------------------------------------------------------------------
【画面与高级设置】
----------------------------------------------------------------------
  使用记事本打开 `config/config.ini` 可以调整：
  - WindowScale: 窗口缩放倍率（默认为 3，即 3 倍窗口尺寸，适合 1080P/2K 显示器）
  - VSync: 垂直同步（1 开启，0 关闭）
  - EnableAudio: 音效开关（1 开启，0 关闭）

----------------------------------------------------------------------
【存档说明】
----------------------------------------------------------------------
  - 游戏进度会自动保存在 `saves/save.srm`。
  - 【关卡全开版】启动时会在内存中直接激活通关数据，不会破坏您的原版正常存档。

祝您游玩愉快！
======================================================================
'''


def create_config_ini():
    return '''[Graphics]
OutputMethod=Direct3D11
VSync=1
NewRenderer=0
WindowScale=3
NoSpriteLimits=0
Widescreen=0

[Sound]
EnableAudio=1

[General]
RunAhead=0
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=ROOT / 'dist' / 'BrutalMario-Native-Windows',
                        help='Destination folder for the unpacked release bundle')
    parser.add_argument('--zip', action='store_true', default=True,
                        help='Create a zip archive of the release bundle')
    args = parser.parse_args()

    out_dir = args.out_dir.resolve()
    print(f'[*] Staging Windows release bundle at: {out_dir}')

    if out_dir.exists():
        shutil.rmtree(out_dir)

    bin_dir = out_dir / 'bin'
    data_dir = out_dir / 'data'
    packs_dir = data_dir / 'packs'
    config_dir = out_dir / 'config'
    scripts_dir = out_dir / 'scripts'
    saves_dir = out_dir / 'saves'

    for d in [bin_dir, packs_dir, config_dir, scripts_dir, saves_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Copy Windows binary
    win_bin = ROOT / 'local/build-windows/demo11-native-product/BrutalMarioDemo11NativeProductSNESRecomp.exe'
    if not win_bin.is_file():
        raise SystemExit(f'Windows binary missing at: {win_bin}')
    dest_bin = bin_dir / 'BrutalMario.exe'
    shutil.copy2(win_bin, dest_bin)
    print(f'[+] Copied Windows executable: {dest_bin.name} ({dest_bin.stat().st_size // 1024} KB)')

    # Also place rom.cfg beside the exe so double-clicking exe directly works!
    (bin_dir / 'rom.cfg').write_text('../data/rom.sfc\n', encoding='utf-8')

    # 2. Copy ROM
    rom_src = ROOT / 'local/restoration' / TARGET / 'rom.sfc'
    if not rom_src.is_file():
        raise SystemExit(f'ROM missing at: {rom_src}')
    dest_rom = data_dir / 'rom.sfc'
    shutil.copy2(rom_src, dest_rom)
    print(f'[+] Copied ROM: {dest_rom.name} ({dest_rom.stat().st_size // 1024} KB)')

    # 3. Copy 45 content packs
    packs_src_dir = ROOT / 'local/restoration' / TARGET
    for var, pack_file in PACKS_MAPPING:
        src = packs_src_dir / pack_file
        if not src.is_file():
            raise SystemExit(f'Missing pack file: {src}')
        shutil.copy2(src, packs_dir / pack_file)
    print(f'[+] Copied all {len(PACKS_MAPPING)} content pack files into data/packs/')

    # 4. Copy scripts
    cheat_complete = ROOT / 'recomp/inputs/cheat-complete-all.script'
    if cheat_complete.is_file():
        shutil.copy2(cheat_complete, scripts_dir / 'cheat-complete-all.script')
    cheat_special = ROOT / 'recomp/inputs/cheat-special-zone.script'
    if cheat_special.is_file():
        shutil.copy2(cheat_special, scripts_dir / 'cheat-special-zone.script')
    print('[+] Copied cheat scripts (cheat-complete-all.script, cheat-special-zone.script)')

    # 5. Configs
    (config_dir / 'config.ini').write_text(create_config_ini(), encoding='utf-8')
    keybinds_src = ROOT / 'local/build/demo11-native-product/keybinds.ini'
    if keybinds_src.is_file():
        shutil.copy2(keybinds_src, config_dir / 'keybinds.ini')
    print('[+] Created configuration files (config.ini, keybinds.ini)')

    # 6. Launchers
    (out_dir / 'play.py').write_text(create_launcher_py(), encoding='utf-8')
    os.chmod(out_dir / 'play.py', 0o755)

    bat_normal, bat_special, bat_complete = create_bat_scripts()
    (out_dir / '启动游戏.bat').write_text(bat_normal, encoding='utf-8')
    (out_dir / '关卡全开版(SpecialZone).bat').write_text(bat_special, encoding='utf-8')
    (out_dir / '关卡全开版(普通大地图).bat').write_text(bat_complete, encoding='utf-8')
    (out_dir / '说明文档.txt').write_text(create_readme(), encoding='utf-8')
    print('[+] Created launchers: play.py, 启动游戏.bat, 关卡全开版(SpecialZone).bat, 关卡全开版(普通大地图).bat, 说明文档.txt')

    # 7. Create ZIP archive
    if args.zip:
        zip_path = out_dir.parent / f'{out_dir.name}.zip'
        print(f'[*] Creating release ZIP: {zip_path} ...')
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for root, dirs, files in os.walk(out_dir):
                for f in files:
                    full_p = Path(root) / f
                    rel_p = full_p.relative_to(out_dir.parent)
                    zf.write(full_p, arcname=str(rel_p))
        print(f'[+] Successfully generated ZIP archive: {zip_path} ({zip_path.stat().st_size // 1024} KB)')

    print('\n======================================================')
    print(f' Windows 分发包制作完成！')
    print(f' 便携文件夹路径: {out_dir}')
    if args.zip:
        print(f' 压缩包文件路径: {zip_path}')
    print('======================================================')


if __name__ == '__main__':
    main()
