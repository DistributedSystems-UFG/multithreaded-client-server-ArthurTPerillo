import sys
import time
import statistics
import socket
from datetime import datetime

from constCS import HOST, PORT, PORT_ST
from client_mt import run_client_mt
from client_st import run_client_st


SERVER_IP   = HOST
N_REQUESTS  = int(sys.argv[1]) if len(sys.argv) > 1 else 200
N_RUNS      = int(sys.argv[2]) if len(sys.argv) > 2 else 5
WARMUP      = 1
RESULT_FILE = "result.txt"



def run_scenario(label, client_fn, host, port, n_requests, n_runs, warmup, out):
    header = (f"\n{'='*60}\n"
              f"CENÁRIO: {label}\n"
              f"Servidor: {host}:{port}  |  Requisições/rodada: {n_requests}  |  Rodadas: {n_runs}\n"
              f"{'='*60}")
    print(header)
    out.write(header + "\n")

    times = []

    for run in range(warmup + n_runs):
        is_warmup = run < warmup
        tag = "WARMUP" if is_warmup else f"RUN {run - warmup + 1}/{n_runs}"
        print(f"\n  [{tag}]")

        elapsed, results = client_fn(
            n_requests=n_requests,
            host=host,
            port=port
        )

        if not is_warmup:
            times.append(elapsed)

            out.write(f"\n  [{tag}]  tempo: {elapsed:.4f}s\n")
            out.write(f"  {'ID':>4}  {'STATUS':<5}  {'OPERAÇÃO':<15}  {'ENTRADA':>12}  {'RESULTADO':>20}\n")
            out.write(f"  {'-'*62}\n")

            for req_id, (status, req, resp) in sorted(results.items()):
                parts = req.split("|")
                op  = parts[0] if len(parts) > 0 else "?"
                val = parts[1] if len(parts) > 1 else "?"
                try:
                    val_fmt = f"{float(val):>12.4f}"
                except ValueError:
                    val_fmt = f"{val:>12}"
                out.write(f"  {req_id:>4}  {status.upper():<5}  {op:<15}  {val_fmt}  {resp:>20}\n")

            out.flush()

        time.sleep(0.2)

    return times


def write_summary(label, times, n_requests, out):
    mean  = statistics.mean(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0.0
    minv  = min(times)
    maxv  = max(times)
    tput  = n_requests / mean

    lines = [
        f"\n  ┌─ {label}",
        f"  │  Média   : {mean:.4f}s  ±  {stdev:.4f}s",
        f"  │  Mín/Máx : {minv:.4f}s  /  {maxv:.4f}s",
        f"  └─ Throughput: {tput:.1f} req/s",
    ]
    for ln in lines:
        print(ln)
        out.write(ln + "\n")

    return mean, stdev, tput


def wait_for_server_swap(from_server, to_server, host, port):
    print(f"\n{'!'*60}")
    print(f"  AÇÃO NECESSÁRIA NA VM DO SERVIDOR ({host})")
    print(f"  1. Encerre o {from_server} (Ctrl+C)")
    print(f"  2. Inicie o {to_server}:")
    print(f"       python {to_server}")
    print(f"  Depois pressione ENTER aqui para continuar...")
    print(f"{'!'*60}")
    input()

    for attempt in range(10):
        try:
            s = socket.create_connection((host, port), timeout=2)
            s.close()
            print(f"  Servidor detectado em {host}:{port}. Continuando...\n")
            return
        except Exception:
            print(f"  Aguardando servidor... (tentativa {attempt + 1}/10)")
            time.sleep(1)

    print("  AVISO: não foi possível confirmar o servidor. Prosseguindo assim mesmo.")



if __name__ == "__main__":

    with open(RESULT_FILE, "w", encoding="utf-8") as out:

        header = (
            f"{'#'*60}\n"
            f"  EXPERIMENTO DE DESEMPENHO – Cliente/Servidor (AWS)\n"
            f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"  SERVIDOR: {SERVER_IP}\n"
            f"  N_REQUESTS={N_REQUESTS}  N_RUNS={N_RUNS}  WARMUP={WARMUP}\n"
            f"{'#'*60}"
        )
        print("\n" + header)
        out.write(header + "\n")

        print(f"\n  O IP do servidor foi lido de constCS.py: HOST = '{SERVER_IP}'")
        print(f"  Certifique-se de que o server_mt.py está rodando na VM do servidor.")
        input("  Pressione ENTER para começar...\n")

        times_a = run_scenario(
            label      = "A) Cliente MT → Servidor MT",
            client_fn  = run_client_mt,
            host       = SERVER_IP,
            port       = PORT,
            n_requests = N_REQUESTS,
            n_runs     = N_RUNS,
            warmup     = WARMUP,
            out        = out,
        )

        times_b = run_scenario(
            label      = "B) Cliente ST → Servidor MT",
            client_fn  = run_client_st,
            host       = SERVER_IP,
            port       = PORT,
            n_requests = N_REQUESTS,
            n_runs     = N_RUNS,
            warmup     = WARMUP,
            out        = out,
        )

        wait_for_server_swap("server_mt.py", "server_st.py", SERVER_IP, PORT_ST)

        times_c = run_scenario(
            label      = "C) Cliente ST → Servidor ST",
            client_fn  = run_client_st,
            host       = SERVER_IP,
            port       = PORT_ST,
            n_requests = N_REQUESTS,
            n_runs     = N_RUNS,
            warmup     = WARMUP,
            out        = out,
        )

        sep = "\n\n" + "="*60 + "\n  RESULTADOS FINAIS\n" + "="*60
        print(sep)
        out.write(sep + "\n")

        mean_a, _, tput_a = write_summary("A) MT + MT", times_a, N_REQUESTS, out)
        mean_b, _, tput_b = write_summary("B) MT + ST", times_b, N_REQUESTS, out)
        mean_c, _, tput_c = write_summary("C) ST + ST", times_c, N_REQUESTS, out)

        def speedup(base, target):
            return base / target if target > 0 else float("inf")

        comparison = (
            f"\n  ── Speedup (referência = ST+ST) ──────────────────────\n"
            f"  A vs C (MT+MT vs ST+ST) : {speedup(mean_c, mean_a):.2f}x\n"
            f"  B vs C (MT+ST vs ST+ST) : {speedup(mean_c, mean_b):.2f}x\n"
            f"  A vs B (MT+MT vs MT+ST) : {speedup(mean_b, mean_a):.2f}x\n"
            f"\n  ── Throughput ────────────────────────────────────────\n"
            f"  A) MT+MT : {tput_a:.1f} req/s\n"
            f"  B) MT+ST : {tput_b:.1f} req/s\n"
            f"  C) ST+ST : {tput_c:.1f} req/s\n"
        )
        print(comparison)
        out.write(comparison)

    print(f"\n  Resultados salvos em '{RESULT_FILE}'\n")
