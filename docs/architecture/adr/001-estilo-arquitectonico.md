# ADR-001: Adoptar un monolito modular para el MVP de San Camilo en Línea

- **Estado:** Aceptado
- **Fecha:** 2026-10-19
- **Decisores:** Equipo Grupo 07 (3 estudiantes de desarrollo de EPIS-UNSA)

---

## Contexto

El proyecto **San Camilo en Línea** busca digitalizar el comercio tradicional del histórico Mercado San Camilo de Arequipa, permitiendo a los clientes armar carritos con productos de diferentes puestos comerciales, pagar de forma unificada mediante Yape y despachar órdenes con confirmación inmediata a cada comerciante vía WhatsApp (**RF-01**, **RF-02**, **RF-03**, **RF-04**, **RF-05**).

Para definir la estructura arquitectónica del sistema, debemos resolver el compromiso entre el plazo de entrega, la capacidad operativa del equipo, el presupuesto y los atributos de calidad críticos definidos en [`drivers.md`](../drivers.md):
- **R-01 (Plazo estricto):** El MVP debe estar completamente desplegado y validado en producción en **1 mes** (4 semanas).
- **R-02 (Equipo limitado):** Solo **3 desarrolladores estudiantiles**, quienes dominan Python (FastAPI/Django), PostgreSQL y PWA (HTML5/Tailwind/JS).
- **R-03 (Presupuesto cero):** Infraestructura con un costo mensual de **$0 USD** (niveles gratuitos de Render/Railway o VPS básico $\le \$5/\text{mes}$), lo que impide mantener múltiples contenedores, gateways o brokers dedicados.
- **QA-01 (Usabilidad crítica en celulares de gama baja):** Los comerciantes operan smartphones con 2 GB de RAM bajo redes 3G intermitentes; la interacción para publicar o gestionar pedidos debe completarse en $\le 3$ toques con latencias mínimas.
- **QA-02 (Rendimiento picos):** Respuestas de catálogo con p95 $\le 1.5\text{ s}$ ante más de 300 usuarios concurrentes.
- **QA-03 (Fiabilidad y Consistencia):** Atomicidad en la división de pedidos multi-puesto y 0 pedidos perdidos ante fallas externas.
- **QA-04 (Modificabilidad):** Capacidad de integrar nuevas pasarelas (Plin) o servicios en $\le 3$ días-persona.

---

## Alternativas consideradas

1. **Monolito en capas tradicional (Puntaje en matriz: 3.85):**
   - *Ventajas:* Familiaridad inmediata y desarrollo veloz de los primeros prototipos.
   - *Desventajas:* Acoplamiento transversal severo. Conforme se cruzan las consultas entre el catálogo por puesto, los carritos multi-puesto y los pagos, suele degenerar en un "monolito de barro" (*big ball of mud*), dificultando el mantenimiento y las pruebas automatizadas.
2. **Microservicios (Puntaje en matriz: 2.35):**
   - *Ventajas:* Despliegue independiente por servicio y aislamiento total de fallas.
   - *Desventajas:* Requiere gestionar múltiples repositorios/despliegues, service discovery, base de datos distribuida y el patrón Saga para coordinar pedidos a múltiples puestos con un único pago Yape. Resulta inviable de construir, probar y costear en 1 mes por 3 personas con presupuesto cero.
3. **Monolito modular (Puntaje en matriz: 4.20 - Elegido):**
   - *Ventajas:* Un solo artefacto desplegable en un único servidor (costo $0/mes) con llamadas en memoria ultrarrápidas, combinado con una estricta modularización interna basada en contextos delimitados (DDD) y arquitectura hexagonal (puertos y adaptadores).

---

## Decisión

**Usaremos un Monolito Modular implementado en Python (FastAPI/Django)** estructurado en 5 módulos de dominio explícitos:
- `catalogo`: Administración y consulta de puestos y productos.
- `pedidos`: Carrito multi-puesto, división de subórdenes por puesto y control de estado (recojo/delivery).
- `pagos`: Verificación de transferencias Yape (código de operación y comprobante) desacoplado mediante una interfaz de pasarela.
- `notificaciones`: Despacho de mensajes formateados hacia WhatsApp (puerto y adaptador hacia esquema `wa.me` / webhooks).
- `usuarios`: Autenticación y perfiles de clientes, comerciantes y repartidores.

### Reglas de diseño y arquitectura:
1. **Comunicación inter-módulo:** Ningún módulo puede acceder directamente a los modelos internos ni a las tablas de la base de datos de otro módulo. La comunicación se realiza exclusivamente a través de interfaces públicas de servicio de aplicación (contratos en Python).
2. **Persistencia aislada:** Se utilizará una única instancia de **PostgreSQL**, pero organizada mediante esquemas lógicos separados para cada módulo (`catalogo.*`, `pedidos.*`, `pagos.*`, `notificaciones.*`).
3. **Puertos y adaptadores:** Las dependencias externas (Yape, WhatsApp, almacenamiento de imágenes en S3/Cloudinary/local) se aíslan detrás de interfaces (puertos) para permitir reemplazos sin impacto en el dominio.

---

## Consecuencias

### Positivas:
- **Entrega a tiempo (R-01, R-02):** Un único pipeline CI/CD, una sola base de código y un entorno de desarrollo unificado que permite a los 3 desarrolladores trabajar en paralelo por módulos.
- **Costo operativo nulo (R-03):** Se despliega como un solo contenedor en plataformas gratuitas (e.g., Render, Railway) o en un VPS económico, consumiendo $< 512\text{ MB}$ de RAM.
- **Rendimiento e interacción en gama baja (QA-01, QA-02):** La comunicación interna se produce en memoria sin latencia de serialización de red, agilizando las respuestas hacia la PWA móvil del comerciante y el cliente.
- **Consistencia transaccional ACID (QA-03):** Permite registrar la orden consolidada y sus subdivisiones por puesto de forma atómica en PostgreSQL sin la complejidad de transacciones distribuidas.
- **Evolución limpia:** Si a futuro el volumen de pedidos crece significativamente, los módulos pueden extraerse gradualmente como microservicios independientes sin necesidad de reescribir la lógica de negocio.

### Negativas / Riesgos y Mitigación:
- **Riesgo de erosión arquitectónica (acoplamiento indebido):** Existe el riesgo de que los desarrolladores importen directamente clases internas de otros módulos bajo presión de tiempo.
  - *Mitigación:* Se configurará una regla de verificación estática de arquitectura en el pipeline de CI usando `import-linter` (o `pytest-archon`), bloqueando cualquier Pull Request que viole los límites entre módulos.
- **Punto único de falla (*Single Point of Failure*):** Una caída del proceso del monolito interrumpe todo el servicio.
  - *Mitigación:* Monitoreo básico de salud (`/health`), reinicio automático mediante Docker/systemd y backups diarios automatizados de la base de datos PostgreSQL.
