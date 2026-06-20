import datetime
import mysql.connector

# Configuración compartida (Asegúrate de cambiar 'tu_contraseña')
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'tu_contraseña',
    'database': 'hygeia_nexus_fund'
}

class Medicamento:
    def __init__(self, medicamento_id, nombre_comercial, precio_venta, requiere_receta, stock_actual):
        self.medicamento_id = medicamento_id
        self.nombre_comercial = nombre_comercial
        self.precio_venta = float(precio_venta)
        self.requiere_receta = bool(requiere_receta)
        self.stock_actual = int(stock_actual)

    def verificarDisponibilidad(self, cantidad: int) -> bool:
        """+ verificarDisponibilidad(cantidad: int): boolean"""
        return self.stock_actual >= cantidad

    def actualizarStockActual(self, cantidad: int):
        """+ actualizarStockActual(cantidad: int): void"""
        # Cambia el stock local y lo impacta directamente en MySQL
        nuevo_stock = self.stock_actual + cantidad # Puede ser negativo si es una venta
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE medicamento SET stock_actual = %s WHERE medicamento_id = %s",
            (nuevo_stock, self.medicamento_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        self.stock_actual = nuevo_stock


class Lote:
    def __init__(self, codigo_lote, fecha_vencimiento, cantidad_stock, estado_lote):
        self.codigo_lote = codigo_lote
        self.fecha_vencimiento = fecha_vencimiento  # Espera un objeto date o string
        self.cantidad_stock = cantidad_stock
        self.estado_lote = estado_lote

    def verificarExpiracion(self) -> bool:
        """+ verificarExpiracion(): boolean"""
        if isinstance(self.fecha_vencimiento, str):
            fecha = datetime.datetime.strptime(self.fecha_vencimiento, "%Y-%m-%d").date()
        else:
            fecha = self.fecha_vencimiento
        # Retorna True si está vencido respecto al día de hoy
        return fecha < datetime.date.today()

    def actualizarEstado(self):
        """+ actualizarEstado(): void"""
        nuevo_estado = "VENCIDO" if self.verificarExpiracion() else "OK"
        if nuevo_estado != self.estado_lote:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE lote SET estado_lote = %s WHERE codigo_lote = %s",
                (nuevo_estado, self.codigo_lote)
            )
            conn.commit()
            cursor.close()
            conn.close()
            self.estado_lote = nuevo_estado


class Cliente:
    def __init__(self, cliente_id, nombre, dni, cliente_frecuente, obra_social_id=None):
        self.cliente_id = cliente_id
        self.nombre = nombre
        self.dni = dni
        self.cliente_frecuente = bool(cliente_frecuente)
        self.obra_social_id = obra_social_id

    @staticmethod
    def buscarPorDNI(dni: str):
        """+ buscarPorDNI(): Cliente"""
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cliente WHERE dni = %s", (dni,))
        res = cursor.fetchone()
        cursor.close()
        conn.close()
        if res:
            return Cliente(res['cliente_id'], res['nombre'], res['dni'], res['cliente_frecuente'], res['obra_social_id'])
        return None

    def evaluarCobertura(self) -> bool:
        """+ evaluarCobertura(): boolean"""
        # Retorna True si el cliente tiene una obra social asociada en la BD
        return self.obra_social_id is not None


# === MODELOS DE SOPORTE / CATÁLOGOS ===

class ObraSocial:
    def __init__(self, obra_social_id, nombre_obra_social):
        self.obra_social_id = obra_social_id
        self.nombre_obra_social = nombre_obra_social

    def obtenerPorcentajeDescuento(self) -> float:
        """+ obtenerPorcentajeDescuento(): double"""
        # Lógica simulada de negocio: PAMI da 40%, OSDE 30%, otras 20%
        if "PAMI" in self.nombre_obra_social.upper():
            return 0.40
        elif "OSDE" in self.nombre_obra_social.upper():
            return 0.30
        return 0.20


class Monodroga:
    def __init__(self, monodroga_id, nombre_monodroga):
        self.monodroga_id = monodroga_id
        self.nombre_monodroga = nombre_monodroga

    def obtenerPrincipioActivo(self) -> str:
        """+ obtenerPrincipioActivo(): String"""
        return self.nombre_monodroga


class CategoriaMedicamento:
    def __init__(self, categoria_id, nombre_categoria, requiere_refrigeracion):
        self.categoria_id = categoria_id
        self.nombre_categoria = nombre_categoria
        self.requiere_refrigeracion = bool(requiere_refrigeracion)

    def verificarCadenaFrio(self) -> bool:
        """+ verificarCadenaFrio(): boolean"""
        return self.requiere_refrigeracion


class Laboratorio:
    def __init__(self, laboratorio_id, nombre_laboratorio):
        self.laboratorio_id = laboratorio_id
        self.nombre_laboratorio = nombre_laboratorio

    def obtenerNombreLaboratorio(self) -> str:
        """+ obtenerNombreLaboratorio(): String"""
        return self.nombre_laboratorio