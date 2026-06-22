from flask import Flask, jsonify
from flask_cors import CORS
from flask import request
import mysql.connector
from mysql.connector import Error
import os  # <--- Fundamental para leer las variables de entorno de Railway
from dotenv import load_dotenv

load_dotenv()  # Carga las variables desde un archivo .env local si existe.
               # En Railway no hace nada (no hay .env ahí), las variables ya están seteadas en el dashboard.

app = Flask(__name__)
# Permitimos que React acceda a los datos
CORS(app, resources={r"/api/*": {"origins": "*"}}) # Al usar "*" permitimos que lea tanto local como desde Vercel/Netlify en producción

def obtener_conexion_db():
    """Establece y devuelve la conexión a la base de datos de forma dinámica."""
    try:
        # Lee host/usuario/base/puerto de las variables de entorno (.env local o Railway),
        # con valores por defecto solo para los datos NO sensibles.
        # La contraseña ya no tiene un valor por defecto: si falta, falla explícitamente
        # en vez de exponer una clave real en el código fuente.
        conexion = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD'),
            database=os.environ.get('DB_NAME', 'hygeia_nexus_fund'),
            port=int(os.environ.get('DB_PORT', 3306))
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

@app.route('/api/medicamentos', methods=['GET'])
def listar_medicamentos():
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT m.medicamento_id, m.nombre_comercial, m.precio_venta, 
                   m.requiere_receta, m.stock_actual, l.nombre_laboratorio as laboratorio
            FROM medicamento m
            INNER JOIN laboratorio l ON m.laboratorio_id = l.laboratorio_id
        """
        cursor.execute(query)
        medicamentos = cursor.fetchall()
        return jsonify(medicamentos), 200
    except Error as e:
        return jsonify({'error': f'Error al ejecutar la consulta: {e}'}), 500
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

@app.route('/api/lotes', methods=['POST'])
def agregar_lote():
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    
    try:
        datos = request.json
        codigo_lote = datos.get('codigo_lote')
        medicamento_id = datos.get('medicamento_id')
        fecha_vencimiento = datos.get('fecha_vencimiento')
        cantidad_stock = datos.get('cantidad_stock')
        
        if not codigo_lote or not medicamento_id or not fecha_vencimiento or cantidad_stock is None:
            return jsonify({'error': 'Todos los campos son obligatorios'}), 400
            
        cursor = conexion.cursor()
        query_lote = """
            INSERT INTO lote (codigo_lote, medicamento_id, fecha_vencimiento, cantidad_stock, estado_lote)
            VALUES (%s, %s, %s, %s, 'OK')
        """
        cursor.execute(query_lote, (codigo_lote, medicamento_id, fecha_vencimiento, cantidad_stock))
        
        query_update_stock = """
            UPDATE medicamento 
            SET stock_actual = stock_actual + %s 
            WHERE medicamento_id = %s
        """
        cursor.execute(query_update_stock, (cantidad_stock, medicamento_id))
        
        conexion.commit()
        cursor.close()
        return jsonify({'status': 'success', 'message': 'Lote registrado e inventario actualizado'}), 201
    except Error as e:
        return jsonify({'error': f'Error en la consistencia de datos: {e}'}), 500
    finally:
        if conexion.is_connected():
            conexion.close()

@app.route('/api/proveedores', methods=['GET'])
def listar_proveedores():
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    
    try:
        cursor = conexion.cursor(dictionary=True)
        query = "SELECT proveedor_id, nombre_proveedor, mail_proveedor, tel_proveedor FROM proveedor"
        cursor.execute(query)
        proveedores = cursor.fetchall()
        return jsonify(proveedores), 200
    except Error as e:
        return jsonify({'error': f'Error al ejecutar la consulta: {e}'}), 500
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

@app.route('/api/proveedores', methods=['POST'])
def agregar_proveedor():
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    
    try:
        datos = request.json
        id_prov = datos.get('proveedor_id')
        nombre = datos.get('nombre_proveedor')
        mail = datos.get('mail_proveedor')
        tel = datos.get('tel_proveedor')
        
        if not id_prov or not nombre or not mail or not tel:
            return jsonify({'error': 'Todos los campos son obligatorios'}), 400
            
        cursor = conexion.cursor()
        query = """
            INSERT INTO proveedor (proveedor_id, nombre_proveedor, mail_proveedor, tel_proveedor)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (id_prov, nombre, mail, tel))
        conexion.commit()
        cursor.close()
        return jsonify({'status': 'success', 'message': 'Proveedor registrado con éxito'}), 201
    except Error as e:
        return jsonify({'error': f'Error en la base de datos: {e}'}), 500
    finally:
        if conexion.is_connected():
            conexion.close()

@app.route('/api/proveedores/<int:id_prov>', methods=['DELETE'])
def eliminar_proveedor(id_prov):
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    
    try:
        cursor = conexion.cursor()
        query = "DELETE FROM proveedor WHERE proveedor_id = %s"
        cursor.execute(query, (id_prov,))
        conexion.commit()
        cursor.close()
        return jsonify({'status': 'success', 'message': f'Proveedor #{id_prov} eliminado'}), 200
    except Error as e:
        return jsonify({'error': f'No se puede eliminar el proveedor: {e}'}), 400
    finally:
        if conexion.is_connected():
            conexion.close()

@app.route('/api/ventas', methods=['GET'])
def listar_ventas():
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT v.venta_id as factura, 
                   DATE_FORMAT(v.fecha_venta, '%d/%m/%Y') as fecha, 
                   v.total, 
                   v.metodo_pago, 
                   IFNULL(o.nombre_obra_social, '-') as obraSocial,
                   IFNULL(c.nombre, 'Consumidor Final') as cliente
            FROM venta v
            LEFT JOIN cliente c ON v.cliente_id = c.cliente_id
            LEFT JOIN obra_social o ON v.obra_social_id = o.obra_social_id
            ORDER BY v.fecha_venta DESC
        """
        cursor.execute(query)
        ventas = cursor.fetchall()
        return jsonify(ventas), 200
    except Error as e:
        return jsonify({'error': f'Error al ejecutar la consulta: {e}'}), 500
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

@app.route('/api/clientes', methods=['GET'])
def listar_clientes():
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT c.cliente_id, c.nombre, c.dni, c.cliente_frecuente, 
                   IFNULL(o.nombre_obra_social, 'Particular') as obra_social,
                   c.obra_social_id
            FROM cliente c
            LEFT JOIN obra_social o ON c.obra_social_id = o.obra_social_id
        """
        cursor.execute(query)
        clientes = cursor.fetchall()
        return jsonify(clientes), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

@app.route('/api/ventas', methods=['POST'])
def registrar_nueva_venta():
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    
    try:
        datos = request.json
        venta_id = datos.get('venta_id')
        cliente_id = datos.get('cliente_id')
        obra_social_id = datos.get('obra_social_id')
        metodo_pago = datos.get('metodo_pago')
        total = datos.get('total')
        carrito = datos.get('carrito')
        
        if not venta_id or not metodo_pago or not carrito:
            return jsonify({'error': 'Faltan datos críticos para procesar la transacción'}), 400
            
        cursor = conexion.cursor()
        query_venta = """
            INSERT INTO venta (venta_id, fecha_venta, total, metodo_pago, obra_social_id, cliente_id, sucursal_id)
            VALUES (%s, CURDATE(), %s, %s, %s, %s, 1)
        """
        cursor.execute(query_venta, (venta_id, total, metodo_pago, obra_social_id, cliente_id))
        
        query_detalle = """
            INSERT INTO detalle_venta (detalle_id, venta_id, medicamento_id, cantidad, precio_unitario, receta_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        query_descontar_stock = """
            UPDATE medicamento 
            SET stock_actual = stock_actual - %s 
            WHERE medicamento_id = %s
        """
        
        for idx, item in enumerate(carrito):
            detalle_id = int(f"{venta_id}{idx}")
            med_id = item.get('medicamento_id')
            cant = item.get('cantidad')
            precio = item.get('precio_unitario')
            receta_id = item.get('receta_id') if item.get('receta_id') != "" else None
            
            cursor.execute(query_detalle, (detalle_id, venta_id, med_id, cant, precio, receta_id))
            cursor.execute(query_descontar_stock, (cant, med_id))
            
        conexion.commit()
        cursor.close()
        return jsonify({'status': 'success', 'message': 'Factura emitida e inventario actualizado con éxito'}), 201
    except Error as e:
        return jsonify({'error': f'Fallo transaccional en MySQL: {e}'}), 500
    finally:
        if conexion.is_connected():
            conexion.close()

@app.route('/api/obras-sociales', methods=['GET'])
def listar_obras_sociales():
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT obra_social_id, nombre_obra_social FROM obra_social")
        os = cursor.fetchall()
        return jsonify(os), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

@app.route('/api/clientes', methods=['POST'])
def agregar_cliente():
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    
    try:
        datos = request.json
        cliente_id = datos.get('cliente_id')
        nombre = datos.get('nombre')
        dni = datos.get('dni')
        cliente_frecuente = datos.get('cliente_frecuente', False)
        obra_social_id = datos.get('obra_social_id')
        
        if not cliente_id or not nombre or not dni:
            return jsonify({'error': 'ID, Nombre y DNI son campos obligatorios'}), 400
            
        cursor = conexion.cursor()
        query = """
            INSERT INTO cliente (cliente_id, nombre, dni, cliente_frecuente, obra_social_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (cliente_id, nombre, dni, cliente_frecuente, obra_social_id))
        conexion.commit()
        cursor.close()
        return jsonify({'status': 'success', 'message': 'Cliente registrado de forma reglamentaria'}), 201
    except Error as e:
        return jsonify({'error': f'Error de duplicación o clave en MySQL: {e}'}), 500
    finally:
        if conexion.is_connected():
            conexion.close()

@app.route('/api/recetas', methods=['GET'])
def listar_recetas():
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT r.receta_id as id,
                   r.medico_matricula,
                   DATE_FORMAT(r.validez_hasta, '%d/%m/%Y') as fecha_limite,
                   c.nombre as paciente,
                   IFNULL(o.nombre_obra_social, 'Particular') as obra_social,
                   MAX(m.requiere_receta) as exige_receta,
                   IFNULL(GROUP_CONCAT(m.nombre_comercial SEPARATOR ', '), 'Ninguno (No dispensado aún)') as medicamentos_asociados
            FROM receta_medica r
            INNER JOIN cliente c ON r.cliente_id = c.cliente_id
            LEFT JOIN obra_social o ON r.obra_social_id = o.obra_social_id
            LEFT JOIN detalle_venta dv ON r.receta_id = dv.receta_id
            LEFT JOIN medicamento m ON dv.medicamento_id = m.medicamento_id
            GROUP BY r.receta_id
            ORDER BY r.validez_hasta DESC
        """
        cursor.execute(query)
        recetas_bd = cursor.fetchall()
        
        recetas_formateadas = []
        for r in recetas_bd:
            medico_simulado = "Dr. Carlos Martínez" if int(r['id']) % 2 == 0 else "Dra. Laura Sosa"
            especialidad_simulada = "Psiquiatría" if int(r['id']) % 2 == 0 else "Medicina General"
            
            recetas_formateadas.append({
                'id': str(r['id']),
                'medico': medico_simulado,
                'especialidad': especialidad_simulada,
                'matricula': r['medico_matricula'],
                'paciente': r['paciente'],
                'fecha': r['fecha_limite'],
                'obra_social': r['obra_social'],
                'psicotropico': bool(r['exige_receta']), 
                'medicamentos': r['medicamentos_asociados'].split(', ')
            })
            
        return jsonify(recetas_formateadas), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

@app.route('/api/recetas', methods=['POST'])
def agregar_receta():
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    
    try:
        datos = request.json
        receta_id = datos.get('receta_id')
        medico_matricula = datos.get('medico_matricula')
        validez_hasta = datos.get('validez_hasta')
        cliente_id = datos.get('cliente_id')
        obra_social_id = datos.get('obra_social_id')
        
        if not receta_id or not medico_matricula or not validez_hasta or not cliente_id:
            return jsonify({'error': 'Faltan campos obligatorios para registrar la receta'}), 400
            
        cursor = conexion.cursor()
        query = """
            INSERT INTO receta_medica (receta_id, medico_matricula, validez_hasta, cliente_id, obra_social_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (receta_id, medico_matricula, validez_hasta, cliente_id, obra_social_id))
        conexion.commit()
        cursor.close()
        return jsonify({'status': 'success', 'message': 'Receta archivada en el sistema'}), 201
    except Error as e:
        return jsonify({'error': f'Error de duplicación o integridad en MySQL: {e}'}), 500
    finally:
        if conexion.is_connected():
            conexion.close()

@app.route('/api/reportes/mas-vendidos', methods=['GET'])
def reporte_mas_vendidos():
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT m.nombre_comercial as producto, 
                   cat.nombre_categoria as categoria, 
                   SUM(dv.cantidad) as cantidad, 
                   m.stock_actual as stock, 
                   SUM(dv.cantidad * dv.precio_unitario) as ingresos
            FROM detalle_venta dv
            INNER JOIN medicamento m ON dv.medicamento_id = m.medicamento_id
            INNER JOIN categoria_medicamento cat ON m.categoria_id = cat.categoria_id
            GROUP BY m.medicamento_id
            ORDER BY cantidad DESC
            LIMIT 5
        """
        cursor.execute(query)
        resultados = cursor.fetchall()
        return jsonify(resultados), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

@app.route('/api/reportes/categorias', methods=['GET'])
def reporte_categorias():
    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
    
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT cat.nombre_categoria as categoria, 
                   SUM(dv.cantidad) as total_vendido
            FROM detalle_venta dv
            INNER JOIN medicamento m ON dv.medicamento_id = m.medicamento_id
            INNER JOIN categoria_medicamento cat ON m.categoria_id = cat.categoria_id
            GROUP BY cat.categoria_id
            ORDER BY total_vendido DESC
        """
        cursor.execute(query)
        resultados = cursor.fetchall()
        return jsonify(resultados), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

@app.route('/api/login', methods=['POST'])
def login():
    datos = request.get_json()
    username = datos.get('username')
    password = datos.get('password')

    if not username or not password:
        return jsonify({'error': 'Por favor, complete todos los campos'}), 400

    conexion = obtener_conexion_db()
    if conexion is None:
        return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

    cursor = conexion.cursor(dictionary=True)
    try:
        query = "SELECT * FROM usuario WHERE username = %s AND password = %s AND activo = TRUE"
        cursor.execute(query, (username, password))
        usuario = cursor.fetchone()

        if usuario:
            return jsonify({
                'mensaje': 'Autenticación exitosa',
                'usuario': {
                    'username': usuario['username'],
                    'nombre': usuario['nombre_completo']
                }
            }), 200
        else:
            return jsonify({'error': 'Credenciales incorrectas o usuario inactivo'}), 401

    except mysql.connector.Error as err:
        print(f"Error SQL: {err}")
        return jsonify({'error': 'Error interno del servidor de base de datos'}), 500
    finally:
        cursor.close()
        conexion.close()


if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)