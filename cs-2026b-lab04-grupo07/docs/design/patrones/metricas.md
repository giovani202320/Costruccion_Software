# Métricas de Refactorización y Análisis de Trade-Off — San Camilo en Línea

Este documento corresponde al entregable **E6** del Laboratorio 07 (Patrones de Diseño GoF, EPIS-UNSA). Se comparan cuantitativamente mediante la herramienta `radon` (complejidad ciclomática, líneas de código e índice de mantenibilidad) la versión inicial (`antes`) y la versión refactorizada (`después`), complementado con una evaluación crítica del compromiso arquitectónico (trade-off).

---

## 1. Tabla Comparativa de Métricas (Radon 6.0.1)

| Métrica / Elemento | Versión Inicial (`antes`) | Versión con Patrones (`después`) | Variación / Impacto |
|:---|:---:|:---:|:---|
| **Complejidad ciclomática de `confirmar_y_pagar`** | **15 (Rango C)** | **2 (Rango A)** | **−86.7%** (De método riesgoso a flujo lineal simple) |
| **Complejidad promedio del código** | **5.50 (Rango B)** | **1.84 (Rango A)** | **−66.5%** (Alta simplificación por delegación) |
| **Complejidad máxima del módulo** | 15 (`confirmar_y_pagar`) | 5 (`SinPrecios._aplicar` / `__init__`) | Ningún método supera el umbral crítico de 10 |
| **Líneas de código fuente (SLOC)** | 85 SLOC | 314 SLOC (total 5 archivos) | +269.4% (Costo de abstracciones e interfaces) |
| **SLOC del orquestador (`servicio.py`)** | 85 SLOC | 42 SLOC | **−50.6%** (El servicio se redujo a la mitad) |
| **Número de archivos de dominio** | 1 archivo | 5 archivos | Mayor modularidad y separación de responsabilidades |
| **Índice de Mantenibilidad (MI)** | 52.75 (Rango A) | **81.46 (Rango A)** | **+28.71 puntos** en el servicio de aplicación |
| **Archivos a modificar para nuevo medio de pago** | 1 (`servicio.py`) | **0** (solo registrar en `FabricaPasarelas`) | Cumplimiento estricto de **OCP** |
| **Cobertura de pruebas automatizadas** | 26 pruebas | 44 pruebas (100% pasando, 1 xfail documentado) | Red de seguridad completa y reproducible |

---

## 2. Análisis del Trade-Off (Compromiso Arquitectónico)

> Con la refactorización ganamos una reducción drástica de la complejidad ciclomática (de C a A) y cumplimiento estricto del principio abierto/cerrado (OCP), permitiendo agregar nuevos medios de pago o pasarelas sin tocar el servicio principal. A su vez, se logró aislar componentes externos y no deterministas (SDKs heterogéneos y LLMs) detrás de adaptadores, decoradores con caché y guardrails de seguridad. El costo principal fue el incremento de líneas de código (de 85 a 314 SLOC) y la dispersión en múltiples archivos con mayor nivel de indirección cognitiva para el equipo. La versión "antes" habría sido perfectamente suficiente si el sistema de San Camilo en Línea se mantuviera estático, con un único medio de pago fijo y sin previsiones de crecimiento o integración con IA.

---

## 3. Patrones Rechazados con Justificación Técnica (Anti-Patternitis)

En concordancia con Fowler (2018) y Kerievsky (2004), cada patrón debe justificar su costo frente a un problema real. En este proyecto se rechazaron explícitamente:

### 1. Rechazo de `Singleton` para `FabricaPasarelas`
* **Propuesta inicial de la IA:** Instanciar la fábrica como un Singleton global accesible desde cualquier módulo.
* **Motivo del rechazo:** Introduce estado global mutable oculto en la aplicación, acopla los componentes en tiempo de ejecución y dificulta la ejecución paralela y la inyección de dobles de prueba (`YapeSDK(fallas=2)`) en `pytest`.
* **Solución adoptada:** Inyección de dependencias a través del constructor de `ServicioPedidos`.

### 2. Rechazo de `Abstract Factory` para familias de pasarelas
* **Propuesta inicial de la IA:** Crear una fábrica abstracta con familias de productos dependientes (`FactoriaYape`, `FactoriaPlin` creando conectores, validadores y serializadores individuales).
* **Motivo del rechazo:** "Patternitis" (sobreingeniería). En San Camilo en Línea no existen familias dependientes de objetos que deban instanciarse en conjunto; cada pasarela es independiente.
* **Solución adoptada:** Simple `FabricaPasarelas` basada en registro (`Factory Method`), que reduce la jerarquía a un único diccionario de creadores sin clases intermedias innecesarias.

### 3. Rechazo de `LLM-as-a-judge` para los Guardrails
* **Propuesta inicial de la IA:** Usar un segundo modelo de lenguaje para evaluar y arbitrar si la respuesta del primer LLM cumplía con las políticas.
* **Motivo del rechazo:** Inviable bajo las restricciones de **R-01** (MVP en 1 mes) y **R-03** (presupuesto $0). Agregaría latencia de red inaceptable (QA-01, QA-02) y no garantiza determinismo en la verificación.
* **Solución adoptada:** Cadena de Responsabilidad (`Chain of Responsibility`) con guardrails deterministas en memoria basados en reglas concretas (`SinPrecios`, `LongitudMaxima`, `SinAfirmacionesProhibidas`).
