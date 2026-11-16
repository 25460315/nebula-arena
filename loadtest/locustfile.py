import json, os, random, time, uuid
import requests
import urllib3
from gevent.lock import Semaphore
from locust import User, HttpUser, task, constant, constant_pacing, events
from websocket import create_connection  # pip install websocket-client

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ALLOCATOR = f"https://{os.environ.get('ALLOCATOR_IP', '')}/gameserverallocation"
PEDIDO = {
    "namespace": "default",
    "gameServerSelectors": [{"matchLabels": {"agones.dev/fleet": "nebula-fleet"}}],
}
VERIFY_TLS = False if os.environ.get("ALLOCATOR_INSECURE", "1") == "1" else "ca.crt"
CERTS = {"cert": ("client.crt", "client.key"), "verify": VERIFY_TLS}


def medir(nombre, inicio, error=None):
    events.request.fire(
        request_type="WS",
        name=nombre,
        response_time=(time.perf_counter() - inicio) * 1000,
        response_length=0,
        exception=error,
    )


class Jugador(User):
    wait_time = constant(0.05)            # 20 mensajes por segundo
    sala = {"addr": None, "cupo": 0}      # mini-matchmaker compartido
    candado = Semaphore()

    def pedir_servidor(self):
        with Jugador.candado:             # un solo pedido a la vez
            if Jugador.sala["cupo"] == 0:  # sala llena: pide otro servidor
                t0 = time.perf_counter()
                r = requests.post(ALLOCATOR, json=PEDIDO, timeout=10, **CERTS)
                r.raise_for_status()
                gs = r.json()
                medir("asignacion", t0)
                Jugador.sala = {
                    "addr": f"{gs['address']}:{gs['ports'][0]['port']}",
                    "cupo": 10,
                }
            Jugador.sala["cupo"] -= 1
            return Jugador.sala["addr"]

    def on_start(self):
        self.id, self.n = uuid.uuid4().hex[:8], 0
        self.x, self.y = random.uniform(0, 100), random.uniform(0, 100)
        self.ws = create_connection(f"ws://{self.pedir_servidor()}", timeout=5)

    @task
    def jugar(self):
        self.x += random.uniform(-1, 1); self.y += random.uniform(-1, 1)
        self.ws.send(json.dumps({
            "id": self.id, "x": self.x, "y": self.y,
            "dispara": random.random() < 0.1,
        }))
        self.n += 1
        if self.n % 20 == 0:              # un ping por segundo
            t0 = time.perf_counter()
            try:
                self.ws.send(json.dumps({"ping": t0}))
                while json.loads(self.ws.recv()).get("pong") != t0:
                    pass                  # descarta los snapshots acumulados
                medir("rtt", t0)
            except Exception as e:
                medir("rtt", t0, e)

    def on_stop(self):
        if hasattr(self, "ws") and self.ws:
            self.ws.close()


class Espectador(HttpUser):
    wait_time = constant_pacing(2)        # un segmento cada 2 s, como el reproductor

    def on_start(self):
        self.i = random.randint(0, 100)   # cada espectador empieza en otro punto

    @task
    def ver_stream(self):
        m = self.client.get("/live/nebula/360p.m3u8", name="manifiesto")
        segmentos = [l for l in m.text.splitlines() if l.endswith(".ts")]
        if not segmentos:
            return
        seg = segmentos[self.i % len(segmentos)]; self.i += 1
        with self.client.get(f"/live/nebula/{seg}", name="segmento", catch_response=True) as r:
            if r.elapsed.total_seconds() > 2:
                r.failure("rebuffering: el segmento tardó más de lo que dura")
