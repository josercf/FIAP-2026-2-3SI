import socket
import threading
import json
import time

def handle_tcp():
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind(('0.0.0.0', 8080))
    tcp_server.listen(5)
    print("🟢 [TCP Server] Aguardando conexões de frete/contratos na porta 8080...")

    while True:
        client, addr = tcp_server.accept()
        data = client.recv(1024)
        if data:
            print(f"📦 [TCP Received from {addr}]: {data.decode('utf-8')}")
            response = json.dumps({"status": "SUCCESS", "message": "Telemetry Logged (TCP)", "timestamp": time.time()})
            client.send(response.encode('utf-8'))
        client.close()

def handle_udp():
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_server.bind(('0.0.0.0', 8081))
    print("⚡ [UDP Server] Aguardando datagramas de GPS/temperatura na porta 8081...")

    while True:
        data, addr = udp_server.recvfrom(1024)
        print(f"📡 [UDP Received from {addr}]: {data.decode('utf-8')}")

if __name__ == '__main__':
    print("🚛 === LogiTech Enterprise - Telemetry Service (L4 OSI Layer) ===")
    tcp_thread = threading.Thread(target=handle_tcp, daemon=True)
    udp_thread = threading.Thread(target=handle_udp, daemon=True)

    tcp_thread.start()
    udp_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🔴 Servidor finalizado.")
