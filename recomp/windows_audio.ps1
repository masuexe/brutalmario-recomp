# Project-local PCM output helper. No service or system audio settings change.
param([int]$Rate = 44100, [int]$Frames = 512)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;

public static class BrutalMarioAudio {
    [StructLayout(LayoutKind.Sequential, Pack=2)]
    struct Format {
        public ushort tag, channels;
        public uint rate, bytesPerSecond;
        public ushort alignment, bits, extra;
    }
    [StructLayout(LayoutKind.Sequential)]
    struct Header {
        public IntPtr data;
        public uint length, recorded;
        public UIntPtr user;
        public uint flags, loops;
        public IntPtr next;
        public UIntPtr reserved;
    }
    [StructLayout(LayoutKind.Explicit, Size=12)]
    struct Position {
        [FieldOffset(0)] public uint type;
        [FieldOffset(4)] public uint samples;
    }
    [DllImport("winmm.dll")] static extern uint waveOutOpen(out IntPtr device, uint id, ref Format format, IntPtr callback, IntPtr instance, uint flags);
    [DllImport("winmm.dll")] static extern uint waveOutPrepareHeader(IntPtr device, IntPtr header, uint size);
    [DllImport("winmm.dll")] static extern uint waveOutUnprepareHeader(IntPtr device, IntPtr header, uint size);
    [DllImport("winmm.dll")] static extern uint waveOutWrite(IntPtr device, IntPtr header, uint size);
    [DllImport("winmm.dll")] static extern uint waveOutGetPosition(IntPtr device, ref Position position, uint size);
    [DllImport("winmm.dll")] static extern uint waveOutReset(IntPtr device);
    [DllImport("winmm.dll")] static extern uint waveOutClose(IntPtr device);

    static void Check(uint code, string operation) {
        if (code != 0) throw new IOException(operation + " failed: " + code);
    }
    static bool Done(IntPtr header) {
        return (((Header)Marshal.PtrToStructure(header, typeof(Header))).flags & 1) != 0;
    }
    static AutoResetEvent completed;
    static void Wait(IntPtr header) {
        Stopwatch timeout = Stopwatch.StartNew();
        while (!Done(header)) {
            int remaining = 5000 - (int)timeout.ElapsedMilliseconds;
            if (remaining <= 0 || !completed.WaitOne(remaining))
                throw new IOException("Windows audio device stopped completing buffers");
        }
    }
    public static void Play(int rate, int frames) {
        if (rate < 11025 || rate > 48000 || frames < 128 || frames > 4096)
            throw new ArgumentOutOfRangeException("audio format");
        Format format = new Format { tag=1, channels=2, rate=(uint)rate,
            bytesPerSecond=(uint)(rate*4), alignment=4, bits=16, extra=0 };
        IntPtr device;
        completed = new AutoResetEvent(false);
        Check(waveOutOpen(out device, UInt32.MaxValue, ref format, completed.SafeWaitHandle.DangerousGetHandle(), IntPtr.Zero, 0x50000), "waveOutOpen");
        const int count = 3;
        IntPtr[] headers = new IntPtr[count], data = new IntPtr[count];
        bool[] prepared = new bool[count], submitted = new bool[count];
        uint headerSize = (uint)Marshal.SizeOf(typeof(Header));
        byte[] buffer = new byte[frames*4];
        long total = 0, nextReport = 0;
        Stopwatch clock = Stopwatch.StartNew();
        Stream input = Console.OpenStandardInput();
        try {
            for (int i=0; i<count; ++i) {
                data[i] = Marshal.AllocHGlobal(buffer.Length);
                headers[i] = Marshal.AllocHGlobal((int)headerSize);
                Header header = new Header { data=data[i], length=(uint)buffer.Length };
                Marshal.StructureToPtr(header, headers[i], false);
                Check(waveOutPrepareHeader(device, headers[i], headerSize), "prepare");
                prepared[i] = true;
            }
            Console.Error.WriteLine("[windows-audio] ready rate={0} frames={1} buffers={2}", rate, frames, count);
            Console.Out.WriteLine("READY 1 {0} {1} {2}", rate, frames, count);
            Console.Out.Flush();
            for (int slot=0;;slot=(slot+1)%count) {
                if (submitted[slot]) {
                    Wait(headers[slot]);
                    Console.Out.WriteLine("CREDIT");
                    Console.Out.Flush();
                }
                int bytes=0;
                while (bytes < buffer.Length) {
                    int got=input.Read(buffer, bytes, buffer.Length-bytes);
                    if (got==0) break;
                    bytes+=got;
                }
                if (bytes==0) break;
                if (bytes%4!=0) throw new IOException("truncated stereo PCM frame");
                Marshal.Copy(buffer, 0, data[slot], bytes);
                Header header = (Header)Marshal.PtrToStructure(headers[slot], typeof(Header));
                header.length=(uint)bytes;
                header.flags &= ~1u;
                Marshal.StructureToPtr(header, headers[slot], false);
                Check(waveOutWrite(device, headers[slot], headerSize), "write");
                submitted[slot]=true;
                total+=bytes/4;
                if (clock.ElapsedMilliseconds >= nextReport) {
                    Position position = new Position { type=2 };
                    Check(waveOutGetPosition(device, ref position, 12), "position");
                    Console.Error.WriteLine("[windows-audio] ms={0} submitted={1} position={2} type={3}", clock.ElapsedMilliseconds, total, position.samples, position.type);
                    nextReport=clock.ElapsedMilliseconds+1000;
                }
            }
            for (int i=0; i<count; ++i) if (submitted[i]) Wait(headers[i]);
            Console.Error.WriteLine("[windows-audio] complete frames={0} ms={1}", total, clock.ElapsedMilliseconds);
        } finally {
            waveOutReset(device);
            for (int i=0; i<count; ++i) {
                if (prepared[i]) waveOutUnprepareHeader(device, headers[i], headerSize);
                if (headers[i]!=IntPtr.Zero) Marshal.FreeHGlobal(headers[i]);
                if (data[i]!=IntPtr.Zero) Marshal.FreeHGlobal(data[i]);
            }
            waveOutClose(device);
            completed.Dispose();
        }
    }
}
'@
try { [BrutalMarioAudio]::Play($Rate, $Frames) }
catch { [Console]::Error.WriteLine('[windows-audio] ERROR: ' + $_.Exception.ToString()); exit 1 }
