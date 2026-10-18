/* Test-only device metadata: retain SDL dummy playback but advertise RDP. */
#include <SDL.h>
const char *SDL_GetCurrentAudioDriver(void) { return "pulseaudio"; }
int SDL_GetDefaultAudioInfo(char **name, SDL_AudioSpec *spec, int capture) {
  if (capture) return -1;
  if (name) *name = SDL_strdup("RDP Sink");
  SDL_zero(*spec);
  spec->freq = 44100;
  spec->format = AUDIO_S16;
  spec->channels = 2;
  return 0;
}
