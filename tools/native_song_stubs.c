/* Stubs for the trace hooks the APU and DSP optionally call. */
#include <stdint.h>
void audio_trace_on_sample(void) {}
void audio_trace_on_reg_write(uint8_t a, uint8_t v) { (void)a; (void)v; }
void audio_trace_on_consume(uint32_t n) { (void)n; }
void shadow_verifier_init(void) {}
void shadow_verifier_judge(void) {}
void audio_trace_on_cpu_port_apply(uint8_t p, uint8_t v, uint64_t c)
{ (void)p; (void)v; (void)c; }
void audio_trace_on_spc_port_read(uint8_t p, uint8_t v) { (void)p; (void)v; }
void audio_trace_on_spc_port_write(uint8_t p, uint8_t v) { (void)p; (void)v; }
void audio_trace_on_spc_cycle(uint32_t n) { (void)n; }
uint64_t g_apu_timer0_total_ticks = 0;
