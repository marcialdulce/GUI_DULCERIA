USE db_dulceria;

-- Columnas que usa el código y que no estaban en la BD (ejecutar UNA sola vez)
ALTER TABLE detalles_pedidos_proveedores
    ADD COLUMN descuento_promocion DECIMAL(10,2) UNSIGNED NOT NULL DEFAULT 0.00 AFTER costo_unitario;

ALTER TABLE movimientos_inventario
    ADD COLUMN observaciones VARCHAR(255) NULL AFTER stock_resultante;

-- Reporte mensual de ventas, costos y ganancias (nombres de tabla en minúsculas: en Linux/Aiven importan)
CREATE OR REPLACE VIEW vw_analisis_financiero_mensual AS
SELECT
    MONTHNAME(v.fecha_hora) AS mes,
    YEAR(v.fecha_hora) AS anio,
    SUM(dv.subtotal) AS ingresos_totales,
    SUM(dv.cantidad * COALESCE((SELECT dpp.costo_unitario FROM detalles_pedidos_proveedores dpp
        WHERE dpp.id_producto = dv.id_producto ORDER BY dpp.id_detalle_pedido_proveedor DESC LIMIT 1), 0)) AS costo_inversion,
    SUM(dv.cantidad * COALESCE((SELECT dpp.descuento_promocion FROM detalles_pedidos_proveedores dpp
        WHERE dpp.id_producto = dv.id_producto ORDER BY dpp.id_detalle_pedido_proveedor DESC LIMIT 1), 0)) AS ahorro_promociones,
    (SUM(dv.subtotal)
     - SUM(dv.cantidad * COALESCE((SELECT dpp.costo_unitario FROM detalles_pedidos_proveedores dpp
            WHERE dpp.id_producto = dv.id_producto ORDER BY dpp.id_detalle_pedido_proveedor DESC LIMIT 1), 0))
     + SUM(dv.cantidad * COALESCE((SELECT dpp.descuento_promocion FROM detalles_pedidos_proveedores dpp
            WHERE dpp.id_producto = dv.id_producto ORDER BY dpp.id_detalle_pedido_proveedor DESC LIMIT 1), 0))
    ) AS ganancia_neta_real
FROM ventas v
JOIN detalles_ventas dv ON v.id_venta = dv.id_venta
GROUP BY YEAR(v.fecha_hora), MONTH(v.fecha_hora), MONTHNAME(v.fecha_hora);



