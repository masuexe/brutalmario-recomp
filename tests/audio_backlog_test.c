/* Exercise queue recovery through the patched runtime and real DSP ring API. */
#include <assert.h>
#include <math.h>
#include M1_RUNTIME_SOURCE

Snes *g_snes;
static Snes machine;
static Apu apu;
static Dsp dsp;
static unsigned lock_depth;
void RtlApuLock(void) { ++lock_depth; }
void RtlApuUnlock(void) { assert(lock_depth); --lock_depth; }
void audio_trace_on_consume(uint64_t first, uint32_t count, uint32_t fill) {
    (void)first; (void)count; (void)fill;
}

void audio_trace_on_fast_forward_discard(uint32_t count, uint32_t fill) {
    (void)count; (void)fill;
}

int main(void) {
    g_snes = &machine; machine.apu = &apu; apu.dsp = &dsp;
    /* Distinct retained stereo samples make the selected time window visible. */
    for (unsigned i = 0; i < DSP_SAMPLE_RING; ++i) {
        dsp.sampleBuffer[2*i] = (int16_t)i;
        dsp.sampleBuffer[2*i+1] = -(int16_t)i;
    }
    dsp.sampleRead = 100;
    dsp.sampleWrite = 3100;
    Dsp before = dsp;
    assert(RtlAudioTrimBacklog(4096, 2136) == 0);
    assert(memcmp(&dsp, &before, sizeof(dsp)) == 0);
    assert(lock_depth == 0);

    /* A stalled callback must resume at the recent tail, with a ramp from
     * the last delivered output. DSP synthesis state and PCM stay intact. */
    dsp.sampleWrite = 7100;
    before = dsp;
    g_audio_last_output_l = 1234;
    g_audio_last_output_r = -4321;
    s_render_phase = .75;
    s_render_occ_ema = 7000;
    assert(RtlAudioTrimBacklog(4096, 2136) == 4864);
    before.sampleRead += 4864;
    assert(memcmp(&dsp, &before, sizeof(dsp)) == 0);
    assert(dsp_available(&dsp) == 2136);
    int16_t left, right;
    dsp_peek(&dsp, 0, &left, &right);
    assert(left == 4964 && right == -4964);
    assert(s_render_phase == 0 && s_render_occ_ema < 0);
    assert(g_audio_recovery_remaining == RTL_AUDIO_RECOVERY_RAMP);
    assert(g_audio_recovery_anchor_l == 1234 && g_audio_recovery_anchor_r == -4321);
    assert(!g_audio_fast_forward && g_audio_recovery_frames == 0);
    assert(lock_depth == 0);

    /* Monotonic counters may wrap; unsigned queue lengths must remain valid. */
    dsp.sampleRead = UINT32_MAX - 5000;
    dsp.sampleWrite = dsp.sampleRead + 7000;
    assert(RtlAudioTrimBacklog(4096, 2136) == 4864);
    assert(dsp_available(&dsp) == 2136);
    before = dsp;
    assert(RtlAudioTrimBacklog(1000, 2000) == 0);
    assert(memcmp(&dsp, &before, sizeof(dsp)) == 0);
    /* Negotiated device blocks must also control turbo-release cleanup. */
    RtlSetAudioBufferTarget(4104);
    assert(s_audio_target_natives == 4104);
    dsp.sampleRead = 100;
    dsp.sampleWrite = 7100;
    RtlAudioSetFastForward(true);
    RtlAudioSetFastForward(false);
    assert(dsp_available(&dsp) == 4104);
    assert(lock_depth == 0);
    RtlSetAudioBufferTarget(UINT32_MAX);
    assert(s_audio_target_natives == DSP_SAMPLE_RING - 1024u);
    RtlSetAudioBufferTarget(1);
    assert(s_audio_target_natives == RTL_AUDIO_TARGET_NATIVES);
    puts("backlog recovery: recent PCM, continuity ramp, DSP invariance, wrap passed");
    return 0;
}
