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
    op    = random.choice(OPERATIONS)
    value = round(random.uniform(-100, 1000), 4)
    return f"{op}|{value}"


def run_client_st(n_requests=100, host=HOST, port=PORT_ST, verbose=False):
    """
    Envia n_requests requisições sequencialmente por uma única conexão.
    Retorna o tempo total decorrido e os resultados.
    """
    results = {}
    errors  = 0

    print(f"[ST-Client] Enviando {n_requests} requisições sequencialmente para {host}:{port} ...")
    t0 = time.perf_counter()

    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((host, port))

        for i in range(n_requests):
            msg = generate_request()
            try:
                s.send(msg.encode())
                data     = s.recv(1024)
                response = data.decode()
                results[i] = ("ok", msg, response)
            except Exception as e:
                results[i] = ("erro", msg, str(e))
                errors += 1

        s.send(b"exit|")
        s.close()

    except Exception as e:
        print(f"[ST-Client] Erro de conexão: {e}")

    elapsed = time.perf_counter() - t0
    print(f"[ST-Client] Concluído em {elapsed:.4f}s | "
          f"OK: {n_requests - errors} | Erros: {errors}")

    if verbose:
        for req_id, (status, req, resp) in sorted(results.items()):
            print(f"  [{req_id:04d}] {status.upper()} | {req} => {resp}")

    return elapsed, results


if __name__ == "__main__":
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    run_client_st(n_requests=n, verbose=(n <= 20))
