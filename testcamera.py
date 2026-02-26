import camera
import time
import gc


# Initializing the Camera
def camera_init():
    # Disable camera initialization
    camera.deinit()
    # Enable camera initialization
    camera.init(0, d0=11, d1=9, d2=8, d3=10, d4=12, d5=18, d6=17, d7=16,
                format=camera.JPEG, framesize=camera.FRAME_VGA,
                xclk_freq=camera.XCLK_10MHz,
                href=7, vsync=6, reset=-1, pwdn=-1,
                sioc=5, siod=4, xclk=15, pclk=13, fb_location=camera.PSRAM)

    camera.framesize(camera.FRAME_VGA)  # Set the camera resolution
    # The options are the following:
    # FRAME_96X96 FRAME_QQVGA FRAME_QCIF FRAME_HQVGA FRAME_240X240
    # FRAME_QVGA FRAME_CIF FRAME_HVGA FRAME_VGA FRAME_SVGA
    # FRAME_XGA FRAME_HD FRAME_SXGA FRAME_UXGA
    # Note: The higher the resolution, the more memory is used.
    # Note: And too much memory may cause the program to fail.

    camera.flip(0)  # Flip up and down window: 0-1
    camera.mirror(0)  # Flip window left and right: 0-1
    camera.saturation(0)  # saturation: -2,2 (default 0). -2 grayscale
    camera.brightness(0)  # brightness: -2,2 (default 0). 2 brightness
    camera.contrast(0)  # contrast: -2,2 (default 0). 2 highcontrast
    camera.quality(10)  # quality: # 10-63 lower number means higher quality
    # Note: The smaller the number, the sharper the image. The larger the number, the more blurry the image

    camera.speffect(camera.EFFECT_NONE)  # special effects:
    # EFFECT_NONE (default) EFFECT_NEG EFFECT_BW EFFECT_RED EFFECT_GREEN EFFECT_BLUE EFFECT_RETRO
    camera.whitebalance(camera.WB_NONE)  # white balance
    # WB_NONE (default) WB_SUNNY WB_CLOUDY WB_OFFICE WB_HOME


camera_init()

while True:
    buf = camera.capture()
    time.sleep_ms(100)  # ~10 fps
    del buf
    gc.collect()
    print("...")
