import server
import re

s = server.Server("ABCD")

s.set_style ("""
.start { background:green; color:white; }
""")

s.set_script("""

function runstart() {
    fetch("/start");
}

""")

s.set_body ("""
<button class="start" onclick="runstart()">Start</button>
""")


# --- Gestion des requêtes HTTP ---
def handle_request(server, request, conn):
    m = re.match(r"GET ([^ ]*) HTTP", request)
    if not m:
        conn.send("HTTP/1.1 400 Bad Request\r\n\r\n")
        return False
    print("my handle request=", m.group(1))
    path = m.group(1)
    if "/start" in path:
        print("START")
        # conn.send("HTTP/1.1 200 OK\r\n\r\n")
        conn.send(server.html())
        conn.close()
        
    return False

s.run(handle_request)
