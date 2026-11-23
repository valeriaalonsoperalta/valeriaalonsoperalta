# Acta de Constitución del Proyecto

**Proyecto:** Lanzamiento App GreenStyle
**Emitida por:** Dirección de Programa – Entrega de Soluciones de Inteligencia Artificial
**Clasificación:** Documento corporativo de uso interno

## 1. Propósito y Justificación

Por medio de la presente Acta se autoriza formalmente el inicio del proyecto "Lanzamiento App GreenStyle", consistente en el diseño, desarrollo y puesta en producción de una aplicación móvil nativa para iOS y Android, junto con su correspondiente panel de administración web, destinada a la comercialización de los productos de moda sostenible de la marca GreenStyle.

La iniciativa responde a la necesidad estratégica de la organización de disponer de un canal digital propio, gobernado por datos, que permita conocer con rigor el comportamiento del cliente y sustentar decisiones de negocio basadas en información fiable, trazable y conforme a la normativa vigente.

## 2. Objetivos del Proyecto

- Poner a disposición de los clientes una aplicación que permita la navegación por el catálogo, la consulta de fichas de producto con información de materiales sostenibles, la gestión del carrito, el pago seguro mediante la pasarela Stripe y la consulta del historial de pedidos.
- Dotar a la organización de un panel de administración web para la gestión de productos, pedidos y usuarios.
- Establecer, desde la concepción del producto, un marco de gobierno del dato que garantice su calidad, seguridad y cumplimiento normativo a lo largo de todo su ciclo de vida.
- Completar el proyecto en un plazo de {duracion} días y con un presupuesto autorizado de €{coste}.

## 3. Alcance

**Dentro del alcance:**
- Autenticación de usuarios, catálogo con filtros, ficha de producto, carrito, checkout con Stripe e historial de pedidos.
- Panel de administración web.
- Publicación en Apple App Store y Google Play.
- Definición e implantación del Ciclo de Vida del Dato (DLC) para los datos de clientes, productos y transacciones.

**Fuera del alcance:**
- Modelos de recomendación o personalización basados en aprendizaje automático, que se evaluarán en una fase posterior una vez se disponga de datos de calidad suficientes.
- Integraciones con sistemas ERP o logísticos de terceros.

## 4. Ciclo de Vida del Dato (DLC)

La Dirección de Programa establece que el tratamiento de los datos del proyecto se regirá por las siguientes etapas, cuyo cumplimiento será condición necesaria para la aceptación de los entregables:

- **Captura:** se recogerán exclusivamente los datos estrictamente necesarios (principio de minimización), con consentimiento explícito e informado del usuario conforme al Reglamento General de Protección de Datos (RGPD).
- **Almacenamiento:** los datos personales se almacenarán cifrados en reposo y en tránsito. Los datos de tarjeta no se almacenarán en ningún caso en los sistemas de la organización, delegándose su custodia en Stripe mediante tokenización (cumplimiento PCI DSS).
- **Procesamiento y uso:** el acceso a los datos se regirá por el principio de mínimo privilegio, con registro de auditoría de todas las operaciones sobre datos personales.
- **Calidad del dato:** se definirán reglas de validación para el catálogo (precios, stock, atributos de sostenibilidad) y se establecerá un responsable de calidad de datos por parte de GreenStyle.
- **Compartición:** cualquier cesión de datos a terceros requerirá un acuerdo de encargo de tratamiento formalizado.
- **Retención y eliminación:** se definirán plazos de conservación por categoría de dato y se habilitará el ejercicio de los derechos de supresión y portabilidad.

## 5. Gestión y Mitigación de Riesgos

La mitigación de riesgos constituye un eje prioritario de la gobernanza del proyecto. Se identifican los siguientes riesgos principales y sus medidas de tratamiento:

- **Integración con la pasarela de pago Stripe (probabilidad alta, impacto alto):** se ejecutará una prueba de concepto técnica en la fase de Análisis y se dispondrá de una reserva de tiempo en la ruta crítica.
- **Rechazo en las tiendas de aplicaciones (probabilidad media, impacto alto):** se verificará el cumplimiento de las directrices de Apple y Google durante el Diseño y se realizará un envío preliminar con antelación suficiente.
- **Incumplimiento normativo en materia de datos (probabilidad baja, impacto muy alto):** se realizará una Evaluación de Impacto relativa a la Protección de Datos (EIPD) antes del inicio del Desarrollo y una auditoría de seguridad previa al lanzamiento.
- **Baja calidad de los datos del catálogo (probabilidad media, impacto medio):** se establecerán reglas de validación y un circuito de aprobación de contenidos.
- **Concentración de carga en el perfil de desarrollo (probabilidad media, impacto alto):** se realizará una nivelación de recursos y un seguimiento semanal de la ruta crítica.

Se constituirá un Registro de Riesgos que será revisado en cada comité de seguimiento, con propietario asignado para cada riesgo.

## 6. Presupuesto y Calendario

- **Presupuesto autorizado:** €{coste}, más una reserva de contingencia del 10 % sujeta a la aprobación del Comité de Dirección.
- **Duración estimada:** {duracion} días naturales, estructurados en las fases de Análisis, Diseño, Desarrollo, Pruebas y Lanzamiento.

## 7. Roles y Responsabilidades

- **Patrocinador del proyecto:** Dirección General de GreenStyle.
- **Director de Programa:** responsable último de la entrega, la gobernanza y la gestión de riesgos.
- **Equipo del proyecto:** {roles}.
- **Responsable de Protección de Datos (DPO):** supervisión del cumplimiento del Ciclo de Vida del Dato.

## 8. Hitos Principales

{hitos}

## 9. Criterios de Aceptación

- Funcionalidades clave operativas y validadas en las pruebas de aceptación de usuario.
- Cero incidencias críticas de seguridad abiertas en la auditoría previa al lanzamiento.
- Evaluación de Impacto relativa a la Protección de Datos aprobada por el DPO.
- Aplicación publicada en ambas tiendas.

## 10. Aprobación

El presente documento entrará en vigor a partir de su firma por las partes que se relacionan a continuación:

- Patrocinador del Proyecto: ______________________  Fecha: ________
- Director de Programa: ______________________  Fecha: ________
