import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
THREE_PATH = os.path.join(BASE_DIR, "three.min.js")
THREE_URL = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"


def ensure_three():
    """Download three.js once (needs internet); afterwards it works offline."""
    if os.path.exists(THREE_PATH) and os.path.getsize(THREE_PATH) > 100000:
        print("three.min.js found - offline mode ready.")
        return
    print("three.min.js not found, downloading (needs internet)...")
    try:
        urllib.request.urlretrieve(THREE_URL, THREE_PATH)
        print("Downloaded three.min.js. You can now run this offline.")
    except Exception as e:
        print(f"WARNING: could not download three.min.js ({e}).")
        print("Connect to the internet and run again, or save it manually next to this file.")


# Shared flight state
telemetry = {"pitch": 0.0, "roll": 0.0}


# Listen for UDP packets from ESP8266 on port 4210
def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 4210))
    print("Listening for ESP8266 Flight Controller on UDP port 4210...")
    while True:
        try:
            data, _ = sock.recvfrom(1024)
            parts = data.decode().strip().split(",")
            if len(parts) == 2:
                telemetry["pitch"] = float(parts[0])
                telemetry["roll"] = float(parts[1])
        except Exception:
            pass


HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
  <title>ESP8266 3D Flight Simulator</title>
  <style>
    body { margin: 0; overflow: hidden; background: #87CEEB; font-family: sans-serif; }
    #hud {
      position: absolute; top: 15px; left: 15px; color: #00ff00;
      background: rgba(0, 20, 0, 0.75); padding: 15px; border-radius: 8px;
      font-family: monospace; font-size: 16px; border: 1px solid #00ff00;
    }
  </style>
  <script src="/three.min.js"></script>
</head>
<body>
  <div id="hud">
    <div><strong>ESP8266 FLIGHT SIM</strong></div>
    <div id="pitch">PITCH: 0.0°</div>
    <div id="roll">ROLL:  0.0°</div>
    <div id="alt">ALT:   200 m</div>
  </div>
  <script>
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x87CEEB);
    scene.fog = new THREE.Fog(0x87CEEB, 100, 1200);

    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);

    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });

    // Lighting
    const sun = new THREE.DirectionalLight(0xffffff, 1.2);
    sun.position.set(100, 300, 100);
    scene.add(sun);
    scene.add(new THREE.AmbientLight(0x606060));

    // Ground Grid
    const grid = new THREE.GridHelper(4000, 100, 0x228B22, 0x2E8B57);
    scene.add(grid);

    // Build Simple Airplane
    const plane = new THREE.Group();
    const bodyMat = new THREE.MeshPhongMaterial({ color: 0xdc2626 });
    const wingMat = new THREE.MeshPhongMaterial({ color: 0xf8fafc });

    const fuselage = new THREE.Mesh(new THREE.BoxGeometry(1.2, 1.2, 7), bodyMat);
    const wings = new THREE.Mesh(new THREE.BoxGeometry(11, 0.2, 1.8), wingMat);
    const tail = new THREE.Mesh(new THREE.BoxGeometry(3.5, 0.2, 1), wingMat);
    tail.position.set(0, 0.2, 3);
    const rudder = new THREE.Mesh(new THREE.BoxGeometry(0.2, 1.5, 1), bodyMat);
    rudder.position.set(0, 0.8, 3);

    plane.add(fuselage, wings, tail, rudder);
    plane.position.set(0, 200, 0);
    scene.add(plane);

    let pitch = 0, roll = 0, yaw = 0;

    // Fetch live tilt from Python server
    setInterval(async () => {
      try {
        const res = await fetch('/data');
        const d = await res.json();
        pitch = d.pitch;
        roll = d.roll;
        document.getElementById('pitch').innerText = `PITCH: ${pitch.toFixed(1)}°`;
        document.getElementById('roll').innerText  = `ROLL:  ${roll.toFixed(1)}°`;
      } catch (e) {}
    }, 30);

    function animate() {
      requestAnimationFrame(animate);

      // Apply controller tilt to aircraft orientation
      const pitchRad = THREE.MathUtils.degToRad(-pitch);
      const rollRad  = THREE.MathUtils.degToRad(-roll);
      yaw += rollRad * 0.025; // Banking turns the aircraft

      plane.rotation.order = 'YXZ';
      plane.rotation.y = yaw;
      plane.rotation.x = pitchRad;
      plane.rotation.z = rollRad;

      // Move forward
      plane.translateZ(-1.2);
      if (plane.position.y < 2) plane.position.y = 2; // Ground floor

      document.getElementById('alt').innerText = `ALT:   ${Math.round(plane.position.y)} m`;

      // Chase camera behind the airplane
      plane.updateMatrixWorld();
      const camOffset = new THREE.Vector3(0, 4, 16).applyMatrix4(plane.matrixWorld);
      camera.position.lerp(camOffset, 0.15);
      camera.lookAt(plane.position);

      renderer.render(scene, camera);
    }
    animate();
  </script>
</body>
</html>
"""


class SimHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Keep terminal clean

    def do_GET(self):
        if self.path == "/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(json.dumps(telemetry).encode())
        elif self.path == "/three.min.js":
            try:
                with open(THREE_PATH, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript")
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))


class QuietServer(HTTPServer):
    def handle_error(self, request, client_address):
        import sys
        # Ignore errors caused by the browser closing/reloading mid-request
        if isinstance(sys.exc_info()[1], ConnectionError):
            return
        super().handle_error(request, client_address)


if __name__ == "__main__":
    ensure_three()
    threading.Thread(target=udp_listener, daemon=True).start()
    print("Flight Simulator running! Open http://localhost:8000 in your browser.")
    QuietServer(("0.0.0.0", 8000), SimHandler).serve_forever()
