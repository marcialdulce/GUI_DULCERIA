USE db_dulceria;

-- Agregamos la columna para registrar los descuentos directos de proveedores
ALTER TABLE DETALLES_PEDIDOS_PROVEEDORES 
ADD COLUMN descuento_promocion DECIMAL(10,2) UNSIGNED NOT NULL DEFAULT 0.00 AFTER costo_unitario;

-- Vista para sacar el reporte mensual de ventas, costos y ganancias
CREATE OR REPLACE VIEW vw_analisis_financiero_mensual AS
SELECT 
    MONTHNAME(v.fecha_hora) AS mes,
    YEAR(v.fecha_hora) AS anio,
    SUM(dv.subtotal) AS ingresos_totales,
    
    -- Calculamos el costo de inversión tomando el último precio de compra del producto
    SUM(dv.cantidad * COALESCE(
        (SELECT costo_unitario 
         FROM DETALLES_PEDIDOS_PROVEEDORES dpp 
         WHERE dpp.id_producto = dv.id_producto 
         ORDER BY id_detalle_pedido_proveedor DESC LIMIT 1), 0)
    ) AS costo_inversion,
    
    -- Calculamos cuánto nos ahorramos por promociones
    SUM(dv.cantidad * COALESCE(
        (SELECT descuento_promocion 
         FROM DETALLES_PEDIDOS_PROVEEDORES dpp 
         WHERE dpp.id_producto = dv.id_producto 
         ORDER BY id_detalle_pedido_proveedor DESC LIMIT 1), 0)
    ) AS ahorro_promociones,
    
    -- Restamos costos y sumamos descuentos a los ingresos para sacar la ganancia real
    (SUM(dv.subtotal) - 
     SUM(dv.cantidad * COALESCE((SELECT costo_unitario FROM DETALLES_PEDIDOS_PROVEEDORES dpp WHERE dpp.id_producto = dv.id_producto ORDER BY id_detalle_pedido_proveedor DESC LIMIT 1), 0)) +
     SUM(dv.cantidad * COALESCE((SELECT descuento_promocion FROM DETALLES_PEDIDOS_PROVEEDORES dpp WHERE dpp.id_producto = dv.id_producto ORDER BY id_detalle_pedido_proveedor DESC LIMIT 1), 0))
    ) AS ganancia_neta_real
FROM VENTAS v
JOIN DETALLES_VENTAS dv ON v.id_venta = dv.id_venta
GROUP BY YEAR(v.fecha_hora), MONTH(v.fecha_hora), MONTHNAME(v.fecha_hora);

-- Trigger para descontar del inventario automáticamente en cada venta
DELIMITER //
CREATE TRIGGER trg_descontar_stock_venta
AFTER INSERT ON DETALLES_VENTAS
FOR EACH ROW
BEGIN
    DECLARE stock_previo INT;
    
    -- Sacamos el stock actual haciendo el balance de entradas y salidas
    SELECT COALESCE(SUM(CASE WHEN tipo IN ('entrada', 'ajuste') THEN cantidad ELSE -cantidad END), 0)
    INTO stock_previo
    FROM MOVIMIENTOS_INVENTARIO 
    WHERE id_producto = NEW.id_producto;

    -- Registramos la salida con el stock actualizado
    INSERT INTO MOVIMIENTOS_INVENTARIO 
    (tipo, cantidad, observaciones, stock_resultante, fecha_hora_movimiento, id_producto, id_detalle_venta)
    VALUES 
    ('salida', NEW.cantidad, 'Venta en mostrador', (stock_previo - NEW.cantidad), NOW(), NEW.id_producto, NEW.id_detalle_venta);
END; //
DELIMITER ;