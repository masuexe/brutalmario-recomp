#ifndef BM_NATIVE_WIDESCREEN_H
#define BM_NATIVE_WIDESCREEN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Desktop host hooks wired into SnesDesktopHostGame for r52+. */
void BmWidescreenAfterConfig(void);
void BmWidescreenOnReset(void);
void BmWidescreenPrepareFrame(int drawable_w, int drawable_h,
                              int *frame_w, int *frame_h);

/* Called inside GameDrawPpuFrame() immediately before and after
 * snes_beam_frame_driver_draw_ppu_frame(). */
void BmWidescreenApplyFramePolicy(void);
void BmWidescreenAfterDraw(void);

#ifdef __cplusplus
}
#endif

#endif /* BM_NATIVE_WIDESCREEN_H */
