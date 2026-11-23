# Revisión de Requisitos – Lanzamiento App GreenStyle

## Valoración general
La descripción expone bien el objetivo (app nativa iOS/Android de e-commerce para moda sostenible) y enumera las funcionalidades clave y las fases. Sin embargo, es una visión de alto nivel: faltan criterios de aceptación, requisitos no funcionales y definición de alcance para que el texto sea verificable y estimable con precisión.

## Hallazgos por criterio

**Claridad**
- "Aplicación móvil nativa": no se indica si significa desarrollo nativo separado (Swift/Kotlin) o multiplataforma (Flutter/React Native). Esto cambia el esfuerzo de desarrollo de forma importante.
- "Catálogo con filtros": no se especifican los filtros (talla, color, precio, categoría, material sostenible, certificaciones).

**Coherencia**
- Se pide "pago de forma segura" pero no se define el alcance de pagos: métodos (tarjeta, Apple Pay, Google Pay), monedas, impuestos ni reembolsos.

**Completitud**
- Faltan requisitos no funcionales: rendimiento (tiempo de carga), disponibilidad, versiones mínimas de iOS/Android, accesibilidad e idiomas.
- No se mencionan: registro y recuperación de contraseña, login social, notificaciones push, gestión de envíos/logística, devoluciones, stock ni integración con ERP.
- El panel de administración web no detalla funciones (productos, pedidos, usuarios, informes) ni roles.

**Ambigüedades**
- "Login de usuario": ¿es obligatorio para comprar o se admite compra como invitado?
- "Historial de pedidos": ¿incluye seguimiento del envío y facturas descargables?
- "Materiales sostenibles": ¿quién aporta y valida esta información y en qué formato?

**Testabilidad**
- Ninguna funcionalidad tiene criterios de aceptación medibles. Ejemplo recomendado: "El checkout completa un pago con 3D Secure en menos de 5 segundos en el 95 % de los casos".

**Riesgos detectados**
- Integración con Stripe y aprobación en las tiendas de aplicaciones, ambos en la ruta crítica.
- Cumplimiento RGPD y PCI DSS no mencionado.

## Recomendaciones priorizadas
1. **(Alta)** Definir el alcance de pagos con Stripe y los requisitos de seguridad y cumplimiento (PCI DSS mediante tokenización, RGPD).
2. **(Alta)** Escribir historias de usuario con criterios de aceptación para cada funcionalidad clave.
3. **(Alta)** Decidir la tecnología (nativa o multiplataforma) y la matriz de dispositivos soportados.
4. **(Media)** Añadir requisitos no funcionales: rendimiento, disponibilidad, accesibilidad (WCAG) e idiomas.
5. **(Media)** Detallar el panel de administración: módulos, roles y permisos.
6. **(Media)** Aclarar compra como invitado, envíos, devoluciones y notificaciones.
7. **(Baja)** Definir indicadores de éxito del lanzamiento (descargas, conversión, valoración en tiendas).
