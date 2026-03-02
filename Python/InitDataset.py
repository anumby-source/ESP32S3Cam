
import network
import socket
import time
import gc
import machine
import camera
import camera_init

# =====================
# INIT CAMERA (EXTERNE)
# =====================

camera_init.camera_init()

# =====================
# CONFIG WIFI
# =====================

SSID = "ESP32-CAM"
PASSWORD = "12345678"
PORT = 80

# =====================
# COMPTEUR GLOBAL PHOTO SIMPLE
# =====================

COUNTER_FILE = "photo_counter.txt"

def load_counter():
    try:
        with open(COUNTER_FILE, "r") as f:
            return int(f.read())
    except:
        return 0

def save_counter(n):
    with open(COUNTER_FILE, "w") as f:
        f.write(str(n))

photo_n = load_counter()

# =====================
# WIFI AP
# =====================

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID, password=PASSWORD)

while not ap.active():
    time.sleep(0.2)

print("IP:", ap.ifconfig()[0])

# =====================
# HTML
# =====================

def html():
    return """HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>ESP32-S3 Camera</title>

<style>
body { background:#111; color:white; text-align:center; font-family:Arial; }
img { width:320px; border-radius:10px; margin-top:10px; }
button { padding:10px 20px; margin:5px; font-size:15px; border:none; border-radius:8px; }
.start { background:green; color:white; }
.stop { background:red; color:white; }
.serie { background:orange; color:white; }
.photo { background:blue; color:white; }
.exit { background:#900; color:white; }
.card { background:#222; padding:20px; border-radius:15px; display:inline-block; }
input { padding:5px; font-size:16px; width:80px; }

.complete { color:lime; font-weight:bold; }
.running { color:orange; font-weight:bold; }
</style>

<script>
let runningVideo = false;
let runningSerie = false;
let frames = 0;
let startTime = 0;
let serieIndex = 0;
let Ns = 10;
let dtSerie = 2000;

function disableButtons(state) {
    document.querySelectorAll("button").forEach(b => b.disabled = state);
}

function startVideo() {
    if (runningVideo) return;
    runningVideo = true;
    frames = 0;
    startTime = Date.now();
    update();
}

function stopVideo() {
    runningVideo = false;
}

function update() {
    if (!runningVideo) return;

    let img = document.getElementById("cam");
    img.src = "/frame?t=" + new Date().getTime();

    frames++;
    let now = Date.now();
    let fps = (frames / ((now - startTime)/1000)).toFixed(1);
    document.getElementById("fps").innerHTML = fps + " FPS";

    setTimeout(update, 200);
}

function takePhoto() {
    if (runningSerie) return;
    let label = document.getElementById("label").value;
    fetch("/photo?label=" + encodeURIComponent(label));
}

function startSerie() {
    if (runningSerie) return;

    Ns = parseInt(document.getElementById("Ns").value);
    dtSerie = parseInt(document.getElementById("dt").value);

    if (isNaN(Ns) || Ns <= 0) Ns = 10;
    if (isNaN(dtSerie) || dtSerie < 200) dtSerie = 2000;

    serieIndex = 0;
    document.getElementById("serieNum").innerHTML = "0 / " + Ns;

    let status = document.getElementById("serieStatus");
    status.classList.remove("complete");
    status.classList.add("running");

    runningSerie = true;
    disableButtons(true);

    // 🔹 DÉMARRAGE AUTOMATIQUE DE LA VIDÉO
    runningVideo = true;
    frames = 0;
    startTime = Date.now();
    update();

    takeSeriePhoto();
}

function takeSeriePhoto() {
    if (!runningSerie) return;

    let label = document.getElementById("label").value;

    fetch("/serieshot?label=" + encodeURIComponent(label) +
          "&idx=" + serieIndex)
    .then(r => r.text())
    .then(resp => {

        serieIndex++;
        document.getElementById("serieNum").innerHTML =
            serieIndex + " / " + Ns;

        if (serieIndex >= Ns) {

            runningSerie = false;
            runningVideo = false;
            disableButtons(false);

            let status = document.getElementById("serieStatus");
            status.classList.remove("running");
            status.classList.add("complete");

        } else {
            setTimeout(takeSeriePhoto, dtSerie);
        }
    });
}

function exitServer() {
    fetch("/exit");
}
</script>
</head>

<body>
<div class="card">

<h2>ESP32-S3 OV2640</h2>

<img id="cam" src="/frame">
<p id="fps">0 FPS</p>

<button class="start" onclick="startVideo()">Start</button>
<button class="serie" onclick="startSerie()">StartSerie</button>
<button class="stop" onclick="stopVideo()">Stop</button>

<br><br>

<label>Label :</label>
<input type="text" id="label" value="test">

<label>Ns :</label>
<input type="number" id="Ns" value="10">

<label>dt (ms) :</label>
<input type="number" id="dt" value="2000">

<br><br>

<button class="photo" onclick="takePhoto()">Photo</button>

<p id="serieStatus">Série : <span id="serieNum">0 / 0</span></p>

<br>
<button class="exit" onclick="exitServer()">Exit</button>

</div>
</body>
</html>
"""

# =====================
# SERVER
# =====================

def create_server():
    s = socket.socket()
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except:
        pass
    s.bind(("0.0.0.0", PORT))
    s.listen(5)
    s.settimeout(2)
    return s

server = create_server()
running = True

while running:
    try:
        conn, addr = server.accept()
    except OSError:
        continue

    try:
        request = conn.recv(1024).decode()

        if "GET / " in request:
            conn.send(html())

        elif "GET /frame" in request:
            gc.collect()
            buf = camera.capture()
            conn.send("HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\n\r\n")
            conn.send(buf)

        elif "GET /photo" in request:
            label = "default"
            if "label=" in request:
                start = request.find("label=") + 6
                end = request.find(" ", start)
                label = request[start:end]
                label = label.replace("%20", "_")

            photo_n += 1
            save_counter(photo_n)

            filename = "photo_{}_{}.jpg".format(label, photo_n)

            gc.collect()
            img = camera.capture()
            with open(filename, "wb") as f:
                f.write(img)

            conn.send("HTTP/1.1 200 OK\r\n\r\nOK")

        elif "GET /serieshot" in request:
            label = "default"
            idx = 0

            if "label=" in request:
                start = request.find("label=") + 6
                mid = request.find("&idx=")
                label = request[start:mid]
                label = label.replace("%20", "_")
                idx = int(request[mid+5:request.find(" ", mid)])

            filename = "photo_{}_{:02d}.jpg".format(label, idx+1)

            gc.collect()
            img = camera.capture()
            with open(filename, "wb") as f:
                f.write(img)

            conn.send("HTTP/1.1 200 OK\r\n\r\nOK")

        elif "GET /exit" in request:
            conn.send("HTTP/1.1 200 OK\r\n\r\nBYE")
            running = False

        else:
            conn.send("HTTP/1.1 404 Not Found\r\n\r\n")

    except Exception as e:
        print("Erreur:", e)

    finally:
        try:
            conn.close()
        except:
            pass

server.close()
ap.active(False)
camera.deinit()
gc.collect()
time.sleep(1)
machine.reset()


