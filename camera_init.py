import time
import camera
import gc

def camera_init():
    camera.deinit()
    gc.collect()

    camera.init(0,
        d0=11, d1=9, d2=8, d3=10,
        d4=12, d5=18, d6=17, d7=16,
        format=camera.JPEG,
        framesize=camera.FRAME_QVGA,  # Flux fluide
        xclk_freq=camera.XCLK_10MHz,
        href=7, vsync=6, reset=-1, pwdn=-1,
        sioc=5, siod=4, xclk=15, pclk=13,
        fb_location=camera.PSRAM
    )
    camera.quality(15)
    time.sleep_ms(500)