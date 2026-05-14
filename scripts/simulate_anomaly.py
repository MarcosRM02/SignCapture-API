import asyncio
import httpx
import time
import multiprocessing

API_URL = "http://127.0.0.1:8000"

def stress_cpu():
    """Genera carga de CPU intensiva con cálculos inútiles."""
    print("Estresando CPU...")
    start_time = time.time()
    while time.time() - start_time < 20: # 20 segundos de carga
        _ = [x**2 for x in range(10000)]

async def simulate_model_drift():
    """Envía repetidos feedbacks negativos para simular deriva de datos y disparar la alerta de modelo."""
    print("Enviando feedback negativo para disparar alerta de Modelo...")
    async with httpx.AsyncClient() as client:
        for _ in range(6):
            try:
                response = await client.post(
                    f"{API_URL}/api/v1/inference/feedback",
                    json={"is_correct": False}
                )
                print(f"Feedback enviado. Status: {response.status_code}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error conectando a la API: {e}")

async def main():
    print("Iniciando Simulador de Anomalías...")
    print("Para probar la alerta de Modelo, asegúrate de que el servidor esté corriendo.")
    
    # 1. Simular Deriva de Modelo
    await simulate_model_drift()
    
    # 2. Simular carga de CPU
    print("Lanzando procesos para estresar la CPU local...")
    processes = []
    # Lanzar tantos procesos como cores para asegurar el 100%
    for _ in range(multiprocessing.cpu_count()):
        p = multiprocessing.Process(target=stress_cpu)
        p.start()
        processes.append(p)
        
    for p in processes:
        p.join()
        
    print("Simulación completada. Revisa tu grupo de Telegram.")

if __name__ == "__main__":
    asyncio.run(main())
