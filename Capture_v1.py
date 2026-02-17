import network
import socket
import camera
import time
import gc

SSID = "Capture"
PASSWORD = "12345678"

def connect_wifi():
    # AP
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=SSID, password=PASSWORD, authmode=3)

    print("1")
    # Attendre que l'AP soit actif
    while ap.active() == False:
        time.sleep(0.5)

    print("2")

    # Attendre qu'une IP soit assignée
    time.sleep(2)

    print("3")

    print("Config:", ap.ifconfig())

    print("Connecté :", ap.ifconfig()[0])
    return ap.ifconfig()[0]

def camera_init():
    # Disable camera initialization
    camera.deinit()
    gc.collect()
    # Enable camera initialization
    camera.init(0, d0=11, d1=9, d2=8, d3=10, d4=12, d5=18, d6=17, d7=16,
                format=camera.JPEG, framesize=camera.FRAME_VGA, 
                xclk_freq=camera.XCLK_10MHz,
                href=7, vsync=6, reset=-1, pwdn=-1,
                sioc=5, siod=4, xclk=15, pclk=13, fb_location=camera.PSRAM)

    camera.framesize(camera.FRAME_VGA) # Set the camera resolution
    # The options are the following:
    # FRAME_96X96 FRAME_QQVGA FRAME_QCIF FRAME_HQVGA FRAME_240X240
    # FRAME_QVGA FRAME_CIF FRAME_HVGA FRAME_VGA FRAME_SVGA
    # FRAME_XGA FRAME_HD FRAME_SXGA FRAME_UXGA
    # Note: The higher the resolution, the more memory is used.
    # Note: And too much memory may cause the program to fail.
    
    camera.flip(0)                       # Flip up and down window: 0-1
    camera.mirror(0)                     # Flip window left and right: 0-1
    camera.saturation(0)                 # saturation: -2,2 (default 0). -2 grayscale 
    camera.brightness(0)                 # brightness: -2,2 (default 0). 2 brightness
    camera.contrast(0)                   # contrast: -2,2 (default 0). 2 highcontrast
    camera.quality(10)                   # quality: # 10-63 lower number means higher quality
    # Note: The smaller the number, the sharper the image. The larger the number, the more blurry the image
    
    camera.speffect(camera.EFFECT_NONE)  # special effects:
    # EFFECT_NONE (default) EFFECT_NEG EFFECT_BW EFFECT_RED EFFECT_GREEN EFFECT_BLUE EFFECT_RETRO
    camera.whitebalance(camera.WB_NONE)  # white balance
    # WB_NONE (default) WB_SUNNY WB_CLOUDY WB_OFFICE WB_HOME



# --------- PAGE WEB ---------
html = """\
<!DOCTYPE html>
<html>
<head>
<title>ESP32 Cam</title>
</head>
<body>
<h2>ESP32-S3 Camera</h2>
<button onclick="capture()">Capturer</button>
<br><br>
<img id="img" width="640"/>

<script>
function capture() {
    var url = "/capture?t=" + new Date().getTime();
    document.getElementById("img").src = url;

    // Téléchargement automatique
    var a = document.createElement("a");
    a.href = url;
    a.download = "photo.jpg";
    a.click();
}
</script>
</body>
</html>
"""

# --------- SERVEUR ---------
def start_server(ip):
    addr = socket.getaddrinfo(ip, 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(20)

    print("Serveur prêt : http://%s" % ip)

    while True:
        cl, addr = s.accept()
        print("Client:", addr)

        request = cl.recv(1024)
        request = request.decode()

        if "GET /capture" in request:
            gc.collect()
            buf = camera.capture()

            cl.send("HTTP/1.1 200 OK\r\n")
            cl.send("Content-Type: image/jpeg\r\n")
            cl.send("Content-Length: %d\r\n\r\n" % len(buf))
            cl.send(buf)

        else:
            cl.send("HTTP/1.1 200 OK\r\n")
            cl.send("Content-Type: text/html\r\n\r\n")
            cl.send(html)

        cl.close()

# --------- MAIN ---------
camera_init()
ip = connect_wifi()
start_server(ip)

time.sleep(2)


"""
print("Capture...")

buf = camera.capture()

# Sauvegarde dans la flash
filename = "photo.jpg"

with open(filename, "wb") as f:
    f.write(buf)

print("Photo sauvegardée :", filename)
print("Taille :", len(buf), "bytes")

camera.deinit()
"""

