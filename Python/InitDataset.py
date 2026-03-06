
import network
import socket
import time
import gc
import machine
import camera
import camera_init
import server

# =====================
# INIT CAMERA (EXTERNE)
# =====================

camera_init.camera_init()

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
# HTML
# =====================

def handle_request(server, request, conn):
    global photo_n

    if "GET /frame" in request:
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

        conn.send("HTTP/1.1 200 OK\r\n\r\n")

    elif "GET /serieshot" in request:
        label = "default"
        idx = 0

        if "label=" in request:
            start = request.find("label=") + 6
            mid = request.find("&idx=")
            label = request[start:mid]
            label = label.replace("%20", "_")
            idx = int(request[mid + 5:request.find(" ", mid)])

        filename = "photo_{}_{:02d}.jpg".format(label, idx + 1)

        gc.collect()
        img = camera.capture()
        with open(filename, "wb") as f:
            f.write(img)

        conn.send("HTTP/1.1 200 OK\r\n\r\n")

    else:
        conn.send(server.html())
        
    conn.close()
    return False

style = """
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
"""

script = """
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

    if (runningSerie) setTimeout(update, dtSerie);
    else setTimeout(update, 500);
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
    if (isNaN(dtSerie) || dtSerie < 200) dtSerie = 1000;

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
"""

body = """
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
<input type="number" id="dt" value="1000">

<br><br>

<button class="photo" onclick="takePhoto()">Photo</button>

<p id="serieStatus">Série : <span id="serieNum">0 / 0</span></p>

<br>
"""


serv = server.Server(title="ESP32-S3 Camera")
serv.set_style(style)
serv.set_script(script)
serv.set_body(body)

serv.run(handle_request)

serv.stop_server()
camera.deinit()
gc.collect()


