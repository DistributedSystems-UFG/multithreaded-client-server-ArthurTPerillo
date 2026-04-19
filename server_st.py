from socket import *
from constCS import *

def apply_operation(op, value):
    try:
        value = float(value)

        if op == "c_to_f":
            return (value * 9 / 5) + 32
        elif op == "f_to_c":
            return (value - 32) * 5 / 9
        elif op == "km_to_miles":
            return value * 0.621371
        elif op == "miles_to_km":
            return value / 0.621371
        elif op == "kg_to_lb":
            return value * 2.20462
        elif op == "lb_to_kg":
            return value / 2.20462
        else:
            return "Erro: operação desconhecida"

    except Exception:
        return "Erro: valor inválido"


def process_request(data):
    try:
        if data.startswith("exit"):
            return "Encerrando conexão..."

        parts = data.split("|")
        if len(parts) < 2:
            return "Erro: formato inválido"

        ops    = parts[0].split(",")
        result = parts[1]

        for op in ops:
            result = apply_operation(op.strip(), result)
            if isinstance(result, str) and "Erro" in result:
                break

        return str(result)

    except Exception:
        return "Erro no processamento"


def run_server(host=HOST, port=PORT_ST, stop_event=None, ready_event=None):
    srv = socket(AF_INET, SOCK_STREAM)
    srv.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(5)
    srv.settimeout(1.0)

    if ready_event:
        ready_event.set()

    print(f"[ST-Server] Aguardando conexão em {host}:{port} ...")

    while True:
        if stop_event and stop_event.is_set():
            break

        try:
            conn, addr = srv.accept()
        except timeout:
            continue
        except Exception:
            break

        print(f"[ST-Server] Cliente conectado: {addr}")
        conn.settimeout(5.0)

        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break

                received = data.decode()
                if received.startswith("exit"):
                    conn.send(b"Conexao encerrada")
                    break

                response = process_request(received)
                conn.send(response.encode())
        except Exception as e:
            print(f"[ST-Server] Erro: {e}")
        finally:
            conn.close()
            print(f"[ST-Server] Conexão encerrada: {addr}")

    srv.close()
    print("[ST-Server] Servidor encerrado.")


if __name__ == "__main__":
    run_server()
