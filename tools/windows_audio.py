"""Bounded Windows waveform output for WSL, without WSLg's RDP sink."""
import configparser
import os
from pathlib import Path
import selectors
import subprocess
import sys
import threading

POWERSHELL = Path('/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')


def available(root, env=None):
    env = os.environ if env is None else env
    requested = env.get('SNESRECOMP_WINDOWS_AUDIO')
    if requested == '0' or (env.get('SDL_AUDIODRIVER') and requested != '1'):
        return False
    return (sys.platform == 'linux' and bool(env.get('WSL_INTEROP')) and
            (requested == '1' or '/mnt/wslg/' in env.get('PULSE_SERVER', '')) and
            POWERSHELL.is_file() and (root / 'recomp/windows_audio.ps1').is_file())


def enabled(config):
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        parser.read(config)
        return parser.getboolean('Sound', 'EnableAudio', fallback=True)
    except (configparser.Error, ValueError):
        return True  # The game's own config parser remains authoritative.


def run(command, directory, root, env=None):
    """Return the game exit code, or None if native output could not start."""
    env = dict(os.environ if env is None else env)
    log_path = directory / 'windows-audio.log'
    helper = game = None
    ack_read = ack_write = None
    relay = None
    try:
        script = subprocess.check_output(['wslpath', '-w', str(root / 'recomp/windows_audio.ps1')],
                                         text=True, timeout=5).strip()
        with log_path.open('w') as log:
            helper = subprocess.Popen([str(POWERSHELL), '-NoProfile', '-NonInteractive',
                                       '-ExecutionPolicy', 'Bypass', '-File', script],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=log, env=env)
            with selectors.DefaultSelector() as selector:
                selector.register(helper.stdout, selectors.EVENT_READ)
                if not selector.select(15) or helper.stdout.readline().strip() != b'READY 1 44100 512 3':
                    raise RuntimeError('Windows audio did not become ready')
            # Device-completion credits bound queued audio even if Windows'
            # interop layer buffers stdin ahead of the waveform device.
            ack_read, ack_write = os.pipe()
            os.write(ack_write, b'1' * 3)
            def relay_credits():
                try:
                    for line in helper.stdout:
                        if line.strip() != b'CREDIT':
                            break
                        os.write(ack_write, b'1')
                except OSError:
                    pass
                finally:
                    os.close(ack_write)
            relay = threading.Thread(target=relay_credits, daemon=True)
            write_fd = helper.stdin.fileno()
            try:
                import fcntl
                fcntl.fcntl(write_fd, fcntl.F_SETPIPE_SZ, 4096)
            except OSError:
                pass  # The pipe is still bounded by the kernel's default.
            env.update(SDL_AUDIODRIVER='dummy', SNESRECOMP_WINDOWS_AUDIO_FD=str(write_fd),
                       SNESRECOMP_WINDOWS_AUDIO_ACK_FD=str(ack_read),
                       SNESRECOMP_WINDOWS_AUDIO='1')
            print('[Audio] Windows native output ready (44100 Hz); ' + str(log_path), flush=True)
            game = subprocess.Popen(command, cwd=directory, env=env,
                                    pass_fds=(write_fd, ack_read), restore_signals=False)
            os.close(ack_read)
            ack_read = None
            helper.stdin.close()
            relay.start()
            warned = False
            while game.poll() is None:
                if helper.poll() is not None and not warned:
                    print('[Audio] Windows output stopped; game continues without sound. See ' + str(log_path),
                          file=sys.stderr, flush=True)
                    warned = True
                try:
                    game.wait(timeout=.5)
                except subprocess.TimeoutExpired:
                    pass
            return game.returncode
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        if game is not None:
            raise
        print('[Audio] Windows output unavailable: ' + str(error) + '; using SDL audio. See ' + str(log_path),
              file=sys.stderr, flush=True)
        return None
    finally:
        if game is not None and game.poll() is None:
            game.terminate()
            try:
                game.wait(timeout=3)
            except subprocess.TimeoutExpired:
                game.kill()
                game.wait()
        if ack_read is not None:
            os.close(ack_read)
        if helper is not None:
            if helper.stdin and not helper.stdin.closed:
                helper.stdin.close()
            try:
                helper.wait(timeout=5)
            except subprocess.TimeoutExpired:
                helper.kill()
                helper.wait()
            if relay is not None and relay.ident is not None:
                relay.join(timeout=2)
            elif ack_write is not None:
                os.close(ack_write)
            if helper.stdout and not helper.stdout.closed:
                helper.stdout.close()
