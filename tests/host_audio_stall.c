/* Test-only SDL2 device shim: delay callbacks to model a blocked RDP sink. */
#define _POSIX_C_SOURCE 200809L
#include <dlfcn.h>
#include <time.h>
#include <SDL.h>

static SDL_AudioCallback original_callback;
static void *original_userdata;
static unsigned callback_count;
static void delayed_callback(void *unused, Uint8 *stream, int length) {
  (void)unused;
  /* A brief warm-up, then a half-second device stall about once a second. */
  if (++callback_count > 60 && callback_count % 30 == 0) {
    struct timespec delay = {0, 500000000};
    nanosleep(&delay, 0);
  }
  original_callback(original_userdata, stream, length);
}

SDL_AudioDeviceID SDL_OpenAudioDevice(const char *device, int capture,
    const SDL_AudioSpec *want, SDL_AudioSpec *have, int changes) {
  typedef SDL_AudioDeviceID (*OpenDevice)(const char *, int,
      const SDL_AudioSpec *, SDL_AudioSpec *, int);
  static OpenDevice open_device;
  if (!open_device) *(void **)(&open_device) = dlsym(RTLD_NEXT, "SDL_OpenAudioDevice");
  SDL_AudioSpec delayed = *want;
  original_callback = want->callback;
  original_userdata = want->userdata;
  delayed.callback = delayed_callback;
  delayed.userdata = 0;
  return open_device(device, capture, &delayed, have, changes);
}
