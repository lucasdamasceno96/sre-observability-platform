import requests
import time
import threading

def send_requests():
    while True:
        try:
            # Bate no endpoint que criamos com delay e erro
            requests.get("http://localhost:8000/orders")
            # Bate no endpoint saudável
            requests.get("http://localhost:8000/health")
        except:
            pass
        time.sleep(0.1)

# Simula 5 usuários simultâneos
for i in range(5):
    threading.Thread(target=send_requests, daemon=True).start()

print("🔥 Gerador de carga iniciado. Olhe seu Grafana!")
while True:
    time.sleep(1)