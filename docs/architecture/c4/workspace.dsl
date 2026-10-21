workspace "San Camilo en Línea - Modelo C4" "Modelo C4 del MVP de comercio multi-puesto del Mercado San Camilo de Arequipa." {

    !identifiers hierarchical

    model {
        cliente = person "Cliente" "Explora catálogos, consolida compras de varios puestos, registra su transferencia y consulta pedidos."
        comerciante = person "Comerciante" "Publica productos, actualiza disponibilidad y prepara las subórdenes de su puesto."
        repartidor = person "Repartidor" "Gestiona la entrega consolidada de pedidos con modalidad delivery."
        administrador = person "Administrador" "Verifica comprobantes de pago y supervisa la operación de la plataforma."

        yapePlin = softwareSystem "Yape / Plin" "Billeteras externas usadas por el cliente para realizar transferencias; el MVP registra y concilia comprobantes de forma manual." "Externo"
        whatsapp = softwareSystem "WhatsApp Business API / wa.me" "Canal externo usado mediante enlaces wa.me para entregar al comerciante el detalle de su suborden; el MVP no contrata la API Cloud de pago." "Externo"

        sanCamilo = softwareSystem "San Camilo en Línea" "Plataforma que digitaliza catálogos por puesto, pedidos multi-puesto, pagos y coordinación de entregas del Mercado San Camilo." {
            pwa = container "PWA móvil" "Interfaz instalable y responsiva para clientes, comerciantes, repartidores y administradores; tolera conectividad intermitente." "HTML5, TailwindCSS, JavaScript, Service Worker" "Web Browser"

            api = container "API San Camilo" "Monolito modular que expone los casos de uso mediante una API REST y mantiene fronteras de dominio explícitas." "Python, FastAPI o Django, REST/JSON" {
                catalogo = component "Módulo Catálogo" "Administra puestos, productos, precios, disponibilidad y reserva de stock mediante su interfaz pública." "Módulo Python"
                pedidos = component "Módulo Pedidos" "Orquesta el carrito multi-puesto, el pedido consolidado, las subórdenes y su ciclo de vida." "Módulo Python"
                pagos = component "Módulo Pagos" "Registra comprobantes y encapsula la validación mediante un puerto de pasarela de pago." "Módulo Python; puertos y adaptadores"
                notificaciones = component "Módulo Notificaciones" "Formatea avisos por puesto y los encola para despacho asíncrono." "Módulo Python; puertos y adaptadores"
                usuarios = component "Módulo Usuarios" "Gestiona autenticación y perfiles de clientes, comerciantes, repartidores y administradores." "Módulo Python"
            }

            worker = container "Worker de notificaciones" "Consume avisos pendientes y aplica reintentos sin bloquear la confirmación del pedido." "Celery" "Worker"
            postgres = container "PostgreSQL" "Persistencia ACID con esquemas lógicos aislados: catalogo, pedidos, pagos, notificaciones y usuarios." "PostgreSQL 15+" "Database"
            redis = container "Redis" "Caché del catálogo y cola de tareas de notificación." "Redis" "Queue"
        }

        cliente -> sanCamilo "Compra productos de varios puestos y consulta sus pedidos"
        comerciante -> sanCamilo "Gestiona catálogo y atiende subórdenes"
        repartidor -> sanCamilo "Consulta y confirma entregas delivery"
        administrador -> sanCamilo "Verifica comprobantes y supervisa pedidos"
        cliente -> yapePlin "Realiza la transferencia del pedido"

        cliente -> sanCamilo.pwa "Usa la aplicación" "HTTPS"
        comerciante -> sanCamilo.pwa "Usa la aplicación" "HTTPS"
        repartidor -> sanCamilo.pwa "Usa la aplicación" "HTTPS"
        administrador -> sanCamilo.pwa "Usa la aplicación" "HTTPS"
        sanCamilo.pwa -> yapePlin "Guía la transferencia y recibe el comprobante" "Deep link / HTTPS"
        sanCamilo.pwa -> sanCamilo.api "Invoca casos de uso" "HTTPS/JSON"

        sanCamilo.api.catalogo -> sanCamilo.postgres "Lee y escribe su esquema catalogo" "SQL/TCP"
        sanCamilo.api.pedidos -> sanCamilo.postgres "Lee y escribe su esquema pedidos" "SQL/TCP"
        sanCamilo.api.pagos -> sanCamilo.postgres "Lee y escribe su esquema pagos" "SQL/TCP"
        sanCamilo.api.notificaciones -> sanCamilo.postgres "Lee y escribe su esquema notificaciones" "SQL/TCP"
        sanCamilo.api.usuarios -> sanCamilo.postgres "Lee y escribe su esquema usuarios" "SQL/TCP"
        sanCamilo.api.catalogo -> sanCamilo.redis "Lee y actualiza caché de catálogo" "Redis protocol"
        sanCamilo.api.notificaciones -> sanCamilo.redis "Encola avisos y reintentos" "Redis protocol"
        sanCamilo.worker -> sanCamilo.redis "Consume avisos pendientes" "Redis protocol"
        sanCamilo.worker -> whatsapp "Entrega avisos por puesto" "HTTPS (wa.me)"

        sanCamilo.pwa -> sanCamilo.api.catalogo "Consulta y administra productos" "HTTPS/JSON"
        sanCamilo.pwa -> sanCamilo.api.pedidos "Gestiona carrito y pedidos" "HTTPS/JSON"
        sanCamilo.pwa -> sanCamilo.api.pagos "Registra código y comprobante" "HTTPS/JSON"
        sanCamilo.pwa -> sanCamilo.api.usuarios "Autentica y administra perfiles" "HTTPS/JSON"
        sanCamilo.api.pedidos -> sanCamilo.api.catalogo "Solicita reservar o liberar stock" "Interfaz de servicio en memoria"
        sanCamilo.api.pedidos -> sanCamilo.api.pagos "Solicita registrar y validar el pago" "Interfaz de servicio en memoria"
        sanCamilo.api.pedidos -> sanCamilo.api.notificaciones "Solicita avisar a comerciantes" "Interfaz de servicio en memoria"
        sanCamilo.api.pedidos -> sanCamilo.api.usuarios "Consulta perfil y modalidad de entrega" "Interfaz de servicio en memoria"
        sanCamilo.api.pedidos -> sanCamilo.pwa "Devuelve el estado actualizado del pedido" "HTTPS/JSON"

        produccion = deploymentEnvironment "Producción" {
            dispositivo = deploymentNode "Dispositivo del usuario" "Celular Android básico o PC con navegador." "Android / navegador web" {
                containerInstance sanCamilo.pwa
            }

            vps = deploymentNode "VPS de bajo costo" "Servidor único compatible con el presupuesto del MVP." "Ubuntu 24.04, 2 vCPU, 4 GB RAM" {
                dockerCompose = deploymentNode "Docker Compose" "Orquesta los servicios desplegados en el VPS." "Docker Compose" {
                    containerInstance sanCamilo.api
                    containerInstance sanCamilo.worker
                    containerInstance sanCamilo.postgres
                    containerInstance sanCamilo.redis
                }
            }
        }
    }

    views {
        systemContext sanCamilo "systemContext" "Nivel 1 - Contexto de San Camilo en Línea y sus actores externos." {
            include *
            autolayout lr
        }

        container sanCamilo "container" "Nivel 2 - Contenedores desplegables del monolito modular." {
            include *
            autolayout lr
        }

        component sanCamilo.api "componentApi" "Nivel 3 - Componentes del contenedor API San Camilo." {
            include sanCamilo.api.catalogo
            include sanCamilo.api.pedidos
            include sanCamilo.api.pagos
            include sanCamilo.api.notificaciones
            include sanCamilo.api.usuarios
            include sanCamilo.postgres
            include sanCamilo.redis
            autolayout lr
        }

        dynamic sanCamilo.api "confirmarYape" "Flujo crítico - Confirmar y pagar un pedido consolidado con Yape." {
            sanCamilo.pwa -> sanCamilo.api.pedidos "1. Envía pedido, modalidad, código de operación y comprobante" "HTTPS/JSON"
            sanCamilo.api.pedidos -> sanCamilo.api.catalogo "2. Reserva stock de cada línea" "Interfaz de servicio en memoria"
            sanCamilo.api.pedidos -> sanCamilo.api.pagos "3. Registra y valida el comprobante" "Interfaz de servicio en memoria"
            sanCamilo.api.pagos -> sanCamilo.postgres "4. Persiste el pago y su estado" "SQL/TCP"
            sanCamilo.api.pedidos -> sanCamilo.postgres "5. Guarda atómicamente pedido y subórdenes" "SQL/TCP"
            sanCamilo.api.pedidos -> sanCamilo.api.notificaciones "6. Solicita avisos por comerciante" "Interfaz de servicio en memoria"
            sanCamilo.api.notificaciones -> sanCamilo.redis "7. Encola avisos y reintentos" "Redis protocol"
            sanCamilo.worker -> sanCamilo.redis "8. Consume el aviso pendiente" "Redis protocol"
            sanCamilo.worker -> whatsapp "9. Entrega la comanda al comerciante" "HTTPS (wa.me)"
            sanCamilo.api.pedidos -> sanCamilo.pwa "10. Devuelve pedido confirmado y pagado" "HTTPS/JSON"
            autolayout lr
        }

        deployment sanCamilo "Producción" "deploymentProduccion" "Despliegue del MVP en un VPS con Docker Compose." {
            include *
            autolayout lr
        }

        styles {
            element "Person" {
                shape Person
                background "#08427B"
                color "#FFFFFF"
            }
            element "Software System" {
                background "#1168BD"
                color "#FFFFFF"
            }
            element "Container" {
                background "#438DD5"
                color "#FFFFFF"
            }
            element "Component" {
                background "#85BBF0"
                color "#000000"
            }
            element "Database" {
                shape Cylinder
                background "#438DD5"
                color "#FFFFFF"
            }
            element "Queue" {
                shape Pipe
                background "#438DD5"
                color "#FFFFFF"
            }
            element "Web Browser" {
                shape WebBrowser
                background "#438DD5"
                color "#FFFFFF"
            }
            element "Worker" {
                shape Hexagon
                background "#438DD5"
                color "#FFFFFF"
            }
            element "Externo" {
                background "#999999"
                color "#FFFFFF"
            }
            relationship "Relationship" {
                color "#707070"
                thickness 2
            }
        }
    }
}
