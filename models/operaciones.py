import datetime
import mysql.connector
from models.entidades import DB_CONFIG

class Sucursal:
    def __init__(self, sucursal_id, nombre_sucursal, usuario_farmacia, contrasenia_farmacia):
        self.sucursal_id = sucursal_id
        self.nombre_sucursal = nombre_sucursal
        self.usuario_farmacia = usuario_farmacia
        self.contrasenia = contrasenia_farmacia

    @staticmethod
    def iniciarSesion(usuario, contrasenia) -> bool:
        """+ iniciarSesion(): boolean"""
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM sucursal WHERE usuario_farmacia = %s AND contrasenia_farmacia = %s",
            (usuario, contrasenia)
        )
        sucursal = cursor.fetchone()
        cursor.close()
        conn.close()
        return sucursal is not None


class RecetaMedica:
    def __init__(self, receta_id, medico_matricula, validez_hasta, cliente_id):
        self.receta_id = receta_id
        self.medico_matricula = medico_matricula
        self.validez_hasta = validez_hasta
        self.cliente_id = cliente_id

    def validarVigencia(self) -> bool:
        """+ validarVigencia(): boolean"""
        if isinstance(self.validez_hasta, str):
            fecha = datetime.datetime.strptime(self.validez_hasta, "%Y-%m-%d").date()
        else:
            fecha = self.validez_hasta
        return fecha >= datetime.date.today()


class Venta:
    def __init__(self, venta_id, fecha_venta, metodo_pago, sucursal_id, cliente_id=None, obra_social_id=None):
        self.venta_id = venta_id
        self.fecha_venta = fecha_venta
        self.metodo_pago = metodo_pago
        self.sucursal_id = sucursal_id
        self.cliente_id = cliente_id
        self.obra_social_id = obra_social_id
        self.productos = [] # Lista de tuplas: (medicamento_obj, cantidad)
        self.total = 0.0

    def calcularTotal(self) -> float:
        """+ calcularTotal(): double"""
        subtotal = 0.0
        for med, cantidad in self.productos:
            subtotal += med.precio_venta * cantidad
        
        # Si aplica obra social, reducimos usando su lógica
        if self.obra_social_id:
            # Descuento base simulado o llamando a ObraSocial
            subtotal = subtotal * 0.70  # Ejemplo: 30% fijo de cobertura en mostrador
            
        self.total = round(subtotal, 2)
        return self.total

    def registrarVenta(self):
        """+ registrarVenta(): void"""
        self.calcularTotal()
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. Insertar en la tabla 'venta'
        query_venta = """
            INSERT INTO venta (venta_id, fecha_venta, total, metodo_pago, obra_social_id, cliente_id, sucursal_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query_venta, (
            self.venta_id, self.fecha_venta, self.total, self.metodo_pago, 
            self.obra_social_id, self.cliente_id, self.sucursal_id
        ))
        
        # 2. Insertar los detalles de venta y actualizar los stocks automáticamente
        query_detalle = """
            INSERT INTO detalle_venta (detalle_id, venta_id, medicamento_id, cantidad, precio_unitario, receta_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        for idx, (med, cantidad) in enumerate(self.productos):
            detalle_id = int(f"{self.venta_id}{idx}") # Generador simple de ID único para el detalle
            cursor.execute(query_detalle, (
                detalle_id, self.venta_id, med.medicamento_id, cantidad, med.precio_venta, None
            ))
            # Usamos el método de la clase Medicamento para descontar las existencias físicas
            med.actualizarStockActual(-cantidad)
            
        conn.commit()
        cursor.close()
        conn.close()