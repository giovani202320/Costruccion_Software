"""
despliegue.py - Vista de despliegue físico de San Camilo en Línea
Genera el diagrama de infraestructura usando la librería Python Diagrams.
Ejecución: python despliegue.py
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.generic.device import Mobile
from diagrams.onprem.network import Nginx, Internet
from diagrams.programming.framework import FastAPI
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.queue import Celery
from diagrams.onprem.monitoring import Grafana

graph_attr = {
    "fontsize": "20",
    "bgcolor": "white",
    "pad": "0.4"
}

with Diagram("San Camilo en Línea - Vista de Despliegue", filename="img/fig_despliegue", show=False,
             direction="LR", graph_attr=graph_attr, outformat="png") as diag:
    
    # Actores y dispositivos clientes
    usuarios = Users("Clientes y\nComerciantes")
    movil = Mobile("PWA Móvil en celular\n(Gama baja / Android)")
    
    # Servidor en la nube (VPS económico / Tier Gratuito)
    with Cluster("Servidor en la Nube (VPS Linux / Render)"):
        proxy = Nginx("Nginx Proxy Reverso\n(HTTPS + Gzip + Static)")
        
        with Cluster("Contenedor Monolito Modular"):
            app = FastAPI("FastAPI API REST\n(5 Módulos de Dominio)")
            worker = Celery("Worker Asíncrono\n(Reintentos WhatsApp)")
            cache = Redis("Redis\n(Caché Catálogo + Cola)")
            db = PostgreSQL("PostgreSQL\n(Esquemas Aislados)")
            mon = Grafana("Monitoreo\n(Prometheus / Grafana)")

    # Servicios externos de terceros
    yape = Internet("Billeteras Digitales\n(Yape / Plin)")
    whatsapp = Internet("Servicio WhatsApp\n(URL Scheme wa.me / API)")

    # Relaciones y flujos
    usuarios >> Edge(label="Interacción táctil ≤ 3 toques") >> movil
    movil >> Edge(label="HTTPS / JSON") >> proxy
    proxy >> Edge(label="Proxy pass :8000") >> app
    
    app >> Edge(label="Lectura/Escritura SQL") >> db
    app >> Edge(label="Caché catálogo / Encola tareas") >> cache
    cache >> Edge(label="Consume tareas pendientes") >> worker
    
    app >> Edge(label="Verificación de pago", style="dashed") >> yape
    worker >> Edge(label="Avisos a comerciantes (reintentos)", style="dashed") >> whatsapp
    
    app >> Edge(style="dotted", label="Métricas /health") >> mon

if __name__ == "__main__":
    print("Script de despliegue configurado correctamente.")
