import socket
import json
import time

def send_udp_telemetry():
    udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = json.dumps({"truck_id": "TRUCK-99", "latitude": -23.5505, "longitude": -46.6333, "speed_kmh": 85})
    udp_client.sendto(payload.encode('utf-8'), ('127.0.0.1', 8081))
    print("📡 [UDP Client] Telemetria de GPS enviada.")

def send_tcp_confirmation():
    tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_client.connect(('127.0.0.1', 8080))
    payload = json.dumps({"order_id": "ORD-12345", "status": "DELIVERED", "signature": "OK"})
    tcp_client.send(payload.encode('utf-8'))
    response = tcp_client.recv(1024)
    print(f"📦 [TCP Client] Resposta do Servidor: {response.decode('utf-8')}")
    tcp_client.close()

if __name__ == '__main__':
    print("🚀 Simulando envio de dados do caminhão LogiTech...")
    send_udp_telemetry()
    time.sleep(1)
    send_tcp_confirmation()
