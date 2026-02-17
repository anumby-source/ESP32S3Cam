import socket
import time
import gc
import network
import camera
import os

SSID = "TON_WIFI"
PASSWORD = "TON_MOTDEPASSE"
PORT = 80

camera_busy = False
counters = {}


# =============================
# WIFI INIT AP
# =============================
def init_wifi_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=SSID, password=PASSWORD)
    print("AP actif")
    ip = ap.ifconfig()[0]
    print("IP:", ip)
    return ip


def init_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connexion WiFi...")
        wlan.connect(SSID, PASSWORD)

        for _ in range(10):
            if wlan.isconnected():
                break
            time.sleep(1)

    print("IP:", wlan.ifconfig()[0])

def init_camera():
    camera.deinit()

    camera.init(0,
        d0=11, d1=9, d2=8, d3=10, d4=12, d5=18, d6=17, d7=16,
        format=camera.JPEG,
        framesize=camera.FRAME_QVGA,   # stable
        xclk_freq=camera.XCLK_10MHz,
        href=7, vsync=6,
        reset=-1, pwdn=-1,
        sioc=5, siod=4,
        xclk=15, pclk=13,
        fb_location=camera.PSRAM)

    camera.quality(12)
    print("Camera OK")


def safe_capture():
    global camera_busy
    if camera_busy:
        return None

    camera_busy = True
    gc.collect()

    buf = camera.capture()

    camera_busy = False
    return buf

def save_image(label, buf):
    if label not in counters:
        counters[label] = 0

    counters[label] += 1
    num = counters[label]

    filename = "photo_%s_%04d.jpg" % (label, num)

    with open(filename, "wb") as f:
        f.write(buf)

    return filename, num

def capture_series(label, total):
    results = []

    for i in range(total):
        buf = safe_capture()
        if not buf:
            results.append("fail")
            continue

        filename, num = save_image(label, buf)
        results.append(filename)

        gc.collect()
        time.sleep(1)

    return results

def web_page():
    return """<!DOCTYPE html>
<html>
<body>
<h2>ESP32-S3 Dataset</h2>

Label: <input id="label" value="test"><br>
Nombre: <input id="count" value="10"><br><br>

<button onclick="capture()">Capture</button>
<button onclick="series()">Serie</button><br><br>

<img src="/stream" width="320"><br>
<div id="status"></div>
<div id="progress"></div>

<script>
function capture(){
 let label = document.getElementById("label").value;
 fetch("/capture?label="+label)
 .then(r=>r.text())
 .then(t=>document.getElementById("status").innerHTML=t);
}

function series(){
 let label = document.getElementById("label").value;
 let count = document.getElementById("count").value;
 fetch("/series?label="+label+"&n="+count)
 .then(r=>r.text())
 .then(t=>document.getElementById("status").innerHTML=t);
}

setInterval(()=>{
 fetch("/progress")
 .then(r=>r.text())
 .then(t=>document.getElementById("progress").innerHTML=t);
},500);
</script>

</body>
</html>
"""

progress_current = 0
progress_total = 0
progress_label = ""

def start_server():
    global progress_current, progress_total, progress_label

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', PORT))
    s.listen(5)

    print("Serveur prêt")

    while True:
        cl, addr = s.accept()
        req = cl.recv(1024).decode()

        # PAGE
        if "GET / " in req:
            cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            cl.send(web_page())
            cl.close()

        # STREAM MJPEG
        elif "GET /stream" in req:
            cl.send("HTTP/1.1 200 OK\r\n")
            cl.send("Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n")

            try:
                while True:
                    if camera_busy:
                        time.sleep(0.05)
                        continue

                    buf = safe_capture()
                    if not buf:
                        continue

                    cl.send("--frame\r\n")
                    cl.send("Content-Type: image/jpeg\r\n\r\n")
                    cl.send(buf)
                    cl.send("\r\n")
            except:
                cl.close()

        # CAPTURE UNIQUE
        elif "GET /capture" in req:
            label = req.split("label=")[1].split(" ")[0]

            buf = safe_capture()
            if buf:
                filename, num = save_image(label, buf)
                cl.send("HTTP/1.1 200 OK\r\n\r\nSaved: %s" % filename)
            else:
                cl.send("HTTP/1.1 200 OK\r\n\r\nCapture failed")

            cl.close()

        # CAPTURE SERIE
        elif "GET /series" in req:
            parts = req.split("label=")[1]
            label = parts.split("&")[0]
            n = int(parts.split("n=")[1].split(" ")[0])

            progress_current = 0
            progress_total = n
            progress_label = label

            for i in range(n):
                buf = safe_capture()
                if buf:
                    save_image(label, buf)

                progress_current = i + 1
                gc.collect()
                time.sleep(1)

            cl.send("HTTP/1.1 200 OK\r\n\r\nSerie terminee")
            cl.close()

        # PROGRESSION
        elif "GET /progress" in req:
            txt = "Classe: %s | %d / %d" % (progress_label, progress_current, progress_total)
            cl.send("HTTP/1.1 200 OK\r\n\r\n"+txt)
            cl.close()

        else:
            cl.close()


def main():
    # init_wifi()
    init_wifi_ap()
    init_camera()
    start_server()

main()
