import server

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
    print("my handle request=", request)
    return False

s.run(handle_request)
