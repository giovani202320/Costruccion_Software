workspace "San Camilo en Línea 2.0" "Arquitectura del sistema multi-mercado (San Camilo, Altiplano, Río Seco) con trazabilidad a atributos de calidad (Lab 08)" {

    model {
        comprador = person "Comprador" "Cliente que busca productos y realiza pedidos consolidados en los mercados." "Cliente"
        comerciante = person "Comerciante" "Vendedor de los mercados San Camilo, Altiplano o Río Seco que administra su puesto." "Comerciante"

        sistema = softwareSystem "San Camilo en Línea 2.0" "Plataforma digital para el comercio tradicional de los mercados de abastos de Arequipa." {
            pwa = container "PWA Offline-First" "Permite navegación fluida, registro de órdenes y gestión de inventario incluso sin señal móvil; sincroniza mediante IndexedDB [QA-07]." "TypeScript / React / PWA" "Web Browser"
            
            api = container "API Monolito Modular" "Servicio central en Python que expone endpoints REST, valida claims JWT 'mercado_id' y ejecuta reglas de negocio dinámicas [QA-01, QA-03]." "Python / FastAPI" "App Server"
            
            cache = container "Caché en Memoria" "Almacena temporalmente vistas de catálogo y respuestas frecuentes con TTL de 30 s para amortiguar horas pico [QA-05]." "In-Memory LRU / Redis" "Cache"
            
            db = container "Base de Datos Relacional" "PostgreSQL con esquemas modulares, índices B-tree (mercado_id, puesto_id), Row-Level Security y tabla outbox [QA-01, QA-03, QA-05, QA-06]." "PostgreSQL 16" "Database"
            
            worker = container "Worker de Conciliación" "Procesa en segundo plano los pagos diferidos en la tabla outbox ante apertura de Circuit Breaker [QA-06]." "Python Background Worker" "Worker"
        }

        pasarela = softwareSystem "Proveedor de Pagos" "Servicios externos de pago móvil (Yape, Plin y transferencias bancarias)." "External System"
        whatsapp = softwareSystem "WhatsApp Business / wa.me" "Canal de mensajería para alertas y confirmaciones directas a comerciantes." "External System"

        # Relaciones de personas
        comprador -> pwa "Consulta catálogo multi-mercado y emite pedidos [HTTPS]"
        comerciante -> pwa "Administra catálogo de puesto y confirma órdenes [HTTPS]"

        # Relaciones de contenedores
        pwa -> api "Sincroniza y envía pedidos consolidados [HTTPS/JSON]"
        api -> cache "Lee y escribe catálogos cacheados con TTL [In-Memory/TCP] [QA-05]"
        api -> db "Lee y persiste datos aplicando políticas RLS por mercado [SQL/TCP] [QA-03]"
        worker -> db "Monitorea y drena la tabla transaccional de pagos pendientes (Outbox) [SQL/TCP] [QA-06]"
        
        # Integraciones externas con resiliencia
        api -> pasarela "Valida pagos inmediatos mediante Strategy y Decorator [HTTPS]"
        worker -> pasarela "Reintenta pagos diferidos cuando el Circuit Breaker pasa a semiabierto [HTTPS] [QA-06]"
        api -> whatsapp "Despacha notificaciones de órdenes a los comerciantes [HTTPS]"
    }

    views {
        container sistema "Contenedores" {
            include *
            autoLayout lr
        }

        styles {
            element "Person" {
                shape Person
                background #1E3A8A
                color #ffffff
            }
            element "Web Browser" {
                shape WebBrowser
                background #2563EB
                color #ffffff
            }
            element "App Server" {
                shape RoundedBox
                background #1D4ED8
                color #ffffff
            }
            element "Database" {
                shape Cylinder
                background #1E40AF
                color #ffffff
            }
            element "Cache" {
                shape Cylinder
                background #0284C7
                color #ffffff
            }
            element "Worker" {
                shape Component
                background #0F766E
                color #ffffff
            }
            element "External System" {
                background #64748B
                color #ffffff
            }
        }
    }
}
