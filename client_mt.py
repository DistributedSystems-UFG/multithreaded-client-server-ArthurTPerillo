import threading
import random
import time
from socket import *
from constCS import *

OPERATIONS = [
    "c_to_f", "f_to_c",
    "km_to_miles", "miles_to_km",
    "kg_to_lb", "lb_to_kg",
]

def generate_request():
    """Gera uma requisição aleatória no formato  op|valor."""
    op    = random.choice(OPERATIONS)
    value = round(random.uniform(-100, 1000), 4)
    return f"{op}|{value}"


def send_request(req_id, msg, host, port, results, lock):
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((host, port))
        s.send(msg.encode())
        data = s.recv(1024)
        response = data.decode()
        s.send(b"exit|")
        s.close()

        with lock:
            results[req_id] = ("ok", msg, response)

    except Exception as e:
        with lock:
            results[req_id] = ("erro", msg, str(e))



def run_client_mt(n_requests=100, host=HOST, port=PORT, verbose=False):
    results = {}
    lock    = threading.Lock()
    threads = []

    print(f"[MT-Client] Enviando {n_requests} requisições em paralelo para {host}:{port} ...")
    t0 = time.perf_counter()

    for i in range(n_requests):
        msg = generate_request()
        t   = threading.Thread(
                  target=send_request,
                  args=(i, msg, host, port, results, lock),
                  daemon=True)
        threads.append(t)

    
    for t in threads:
        t.start()

    
    for t in threads:
        t.join()

    elapsed = time.perf_counter() - t0

    errors = sum(1 for v in results.values() if v[0] == "erro")
    print(f"[MT-Client] Concluído em {elapsed:.4f}s | "
          f"OK: {n_requests - errors} | Erros: {errors}")

    if verbose:
        for req_id, (status, req, resp) in sorted(results.items()):
            print(f"  [{req_id:04d}] {status.upper()} | {req} => {resp}")

    return elapsed, results



if __name__ == "__main__":
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    run_client_mt(n_requests=n, verbose=(n <= 20))
