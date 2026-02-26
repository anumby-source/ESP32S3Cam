import network
import socket
import camera
import time
import gc

# ---------------- CONFIG ----------------
SSID = "Capture"
PASSWORD = "12345678"

# ---------------- CAMERA ----------------
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

# ---------------- WIFI ----------------
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

    # Attendre qu'une IP soit assignÃ©e
    time.sleep(2)

    print("3")

    print("Config:", ap.ifconfig())

    print("Connecté :", ap.ifconfig()[0])
    return ap.ifconfig()[0]

# ---------------- PAGE WEB ----------------
html = """\
<!DOCTYPE html>
<html>
<head>
<title>ESP32 S3 Dataset Builder</title>
</head>
<body>
<h2>ESP32-S3 Dataset Builder</h2>

<label>Label :</label>
<input id="label" value="default"><br>
<button onclick="capture()">Capture</button><br>
<button onclick="serie()">Serie</button><br>
<span id="counter">0</span> images<br>

<br><br>
<img src="/stream" width="320">

<script>
let counter = 0;

function capture() {
    let label = document.getElementById("label").value || "default";
    let url = "/capture?label=" + label + "&n=" + counter;
    counter++;
    document.getElementById("counter").innerText = counter;

    // Téléchargement automatique
    var a = document.createElement("a");
    a.href = url;
    a.download = "";
    a.click();
}

function serie() {
    let label = document.getElementById("label").value || "default";
    let url = "/capture?label=" + label + "&n=" + counter;
    counter++;
    document.getElementById("counter").innerText = counter;

    // Téléchargement automatique
    var a = document.createElement("a");
    a.href = url;
    a.download = "";
    a.click();
}

</script>

</body>
</html>
"""

# ---------------- SERVEUR ----------------
boundary = "frame"
photo_counter = {}

def get_param(request, name):
    try:
        start = request.index(name + "=") + len(name) + 1
        end = request.find("&", start)
        if end == -1:
            end = request.find(" ", start)
        return request[start:end]
    except:
        return ""

def start_server(ip):
    addr = socket.getaddrinfo(ip, 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print("Ouvre : http://%s" % ip)

    while True:
        cl, addr = s.accept()
        req = cl.recv(1024).decode()

        # -------- STREAM MJPEG --------
        if "GET /stream" in req:
            cl.send("HTTP/1.1 200 OK\r\n")
            cl.send("Content-Type: multipart/x-mixed-replace; boundary=%s\r\n\r\n" % boundary)
            try:
                while True:
                    gc.collect()
                    buf = camera.capture()
                    cl.send("--%s\r\n" % boundary)
                    cl.send("Content-Type: image/jpeg\r\n")
                    cl.send("Content-Length: %d\r\n\r\n" % len(buf))
                    cl.send(buf)
                    cl.send("\r\n")
                    time.sleep_ms(100)  # ~10 fps
            except:
                cl.close()

        # -------- CAPTURE --------
        elif "GET /capture" in req:
            label = get_param(req, "label")
            if label == "":
                label = "default"

            # compteur par label
            if label not in photo_counter:
                photo_counter[label] = 0
            photo_counter[label] += 1
            num = photo_counter[label]

            filename = "photo_%s_%04d.jpg" % (label, num)

            gc.collect()
            buf = camera.capture()  # Capture haute qualité possible

            cl.send("HTTP/1.1 200 OK\r\n")
            cl.send("Content-Type: image/jpeg\r\n")
            cl.send("Content-Disposition: attachment; filename=%s\r\n" % filename)
            cl.send("Content-Length: %d\r\n\r\n" % len(buf))
            cl.send(buf)
            cl.close()

            print("Capture:", filename)

        # -------- SERIE --------
        elif "GET /serie" in req:
            label = get_param(req, "label")
            if label == "":
                label = "default"

            # compteur par label
            if label not in photo_counter:
                photo_counter[label] = 0
            photo_counter[label] += 1
            num = photo_counter[label]

            filename = "photo_%s_%04d.jpg" % (label, num)

            gc.collect()
            buf = camera.capture()  # Capture haute qualité possible

            cl.send("HTTP/1.1 200 OK\r\n")
            cl.send("Content-Type: image/jpeg\r\n")
            cl.send("Content-Disposition: attachment; filename=%s\r\n" % filename)
            cl.send("Content-Length: %d\r\n\r\n" % len(buf))
            cl.send(buf)
            cl.close()

            print("Serie:", filename)

        # -------- PAGE WEB --------
        else:
            cl.send("HTTP/1.1 200 OK\r\n")
            cl.send("Content-Type: text/html\r\n\r\n")
            cl.send(html)
            cl.close()

# ---------------- MAIN ----------------
camera_init()
ip = connect_wifi()
start_server(ip)

