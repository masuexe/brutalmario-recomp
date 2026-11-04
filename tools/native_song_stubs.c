/* Stubs for the trace and shadow hooks the DSP optionally calls. */
#include <stdint.h>
void audio_trace_on_sample(void) {}
void audio_trace_on_reg_write(uint8_t a, uint8_t v) { (void)a; (void)v; }
void audio_trace_on_consume(uint32_t n) { (void)n; }
void shadow_verifier_init(void) {}
void shadow_verifier_judge(void) {}
