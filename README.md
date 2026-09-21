## Sistema de Gestión para Dulcería

Aplicación de escritorio desarrollada en Python para la administración del punto de venta y control de inventario de una dulcería. Este proyecto está estructurado bajo el patrón de arquitectura **Modelo-Vista-Controlador (MVC)**, garantizando un código fácil de mantener y estructurado.

## Características Principales

* **Panel de Control (Dashboard):** Visualización rápida de indicadores de negocio, total de productos activos y alertas de stock bajo.
* **Punto de Venta Dinámico:** Interfaz de cobro ("Nueva Venta") con cálculo automático de subtotales, validación de inventario en tiempo real y cálculo de cambio.
* **Gestión de Inventario:** Catálogo visual con indicadores de estado de stock (Medio, Bajo, Agotado).
* **Búsqueda y Filtrado en Tiempo Real:** Filtros interactivos por marca y categoría que actualizan la vista sin necesidad de recargar la pantalla.
* **Manejo Seguro de Sesiones:** Autenticación básica y cierre de sesión seguro que limpia la memoria volátil de transacciones en curso.

## Tecnologías Utilizadas

* **Lenguaje:** Python 
* **Interfaz Gráfica:** Tkinter / ttk
* **Arquitectura:** MVC (Modelo-Vista-Controlador)
* **Almacenamiento actual:** Estructuras de datos en memoria (fase de prototipado GUI).

## Arquitectura del Proyecto

El código fuente está dividido lógicamente para separar la interfaz visual de las reglas de negocio:

* `main`: Punto de entrada de la aplicación. Inicializa el ciclo principal y arranca el controlador.
* `controlador`: Puente de comunicación. Gestiona los eventos del usuario, valida la lógica de negocio y coordina las actualizaciones entre la vista y el modelo.
* `vista`: Contiene exclusivamente la parte de la interfaz gráfica usando Tkinter. Dibuja las ventanas, tablas y botones.
* `modelo`: Administra los datos y la lógica matemática. Gestiona el catálogo de dulces, el carrito de compras temporal y los cálculos de cobro.
