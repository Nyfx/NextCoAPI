from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_mysqldb import MySQL
import MySQLdb.cursors
import jwt
from datetime import datetime, timedelta, timezone
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'your_secret_key'  # Cambia esto a un secreto seguro

# Configuración de CORS para permitir solicitudes desde cualquier origen
CORS(app, resources={r"/*": {"origins": "*"}}, 
     supports_credentials=True, 
     expose_headers=['Content-Type', 'Authorization', 'Access-Control-Allow-Credentials'],
     allow_headers=['Content-Type', 'Authorization', 'Access-Control-Allow-Credentials'])

# Configuración de MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Cambia esto a tu contraseña de MySQL
app.config['MYSQL_DB'] = 'nextco'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Cambia esto a un secreto seguro

mysql = MySQL(app)

TOKEN_EXPIRATION_MINUTES = 60  # Ajusta el tiempo de expiración del token

def get_role_id(role_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT id FROM roles WHERE name = %s', (role_name,))
    role = cursor.fetchone()
    cursor.close()
    return role['id'] if role else None

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    full_name = data.get('full_name')
    phone = data.get('phone')
    email = data.get('email')
    password = data.get('password')
    gender = data.get('gender')
    role_id = data.get('role_id', 3)  # Default to 'Usuario'

    if not all([full_name, phone, email, password, gender]):
        return jsonify({'message': 'Todos los campos son requeridos'}), 400

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM roles WHERE id = %s', (role_id,))
    role = cursor.fetchone()
    cursor.close()

    if role is None:
        return jsonify({'message': 'Rol inválido'}), 400

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id FROM usuarios WHERE email = %s', (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({'message': 'El correo electrónico ya está registrado'}), 400

        cursor.execute('INSERT INTO usuarios (full_name, phone, email, password, gender, role_id) VALUES (%s, %s, %s, %s, %s, %s)',
                       (full_name, phone, email, password, gender, role_id))
        mysql.connection.commit()
        return jsonify({'message': 'Usuario registrado exitosamente'})
    except MySQLdb.Error as err:
        return jsonify({'message': f'Error de base de datos: {str(err)}'}), 500
    finally:
        cursor.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Correo y contraseña son requeridos'}), 400

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT u.*, r.name as role_name FROM usuarios u
            JOIN roles r ON u.role_id = r.id
            WHERE u.email = %s AND u.password = %s
        ''', (email, password))
        user = cursor.fetchone()

        if user:
            token = jwt.encode({
                'user_id': user['id'],
                'role_name': user['role_name'],
                'exp': datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRATION_MINUTES)
            }, app.secret_key, algorithm='HS256')

            return jsonify({
                'message': 'Inicio de sesión exitoso',
                'role_name': user['role_name'],
                'token': token
            })
        else:
            return jsonify({'message': 'Correo electrónico o contraseña inválidos'}), 401
    except MySQLdb.Error as err:
        return jsonify({'message': f'Error de base de datos: {str(err)}'}), 500
    finally:
        cursor.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Cierre de sesión exitoso'})

@app.route('/api/user', methods=['GET'])
def get_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Token no proporcionado'}), 401

    token = auth_header.split(' ')[1]

    try:
        decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        user_id = decoded_token['user_id']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT u.id, u.full_name, u.email, r.name as role_name 
            FROM usuarios u
            JOIN roles r ON u.role_id = r.id
            WHERE u.id = %s
        ''', (user_id,))
        user = cursor.fetchone()

        if user:
            return jsonify(user)
        else:
            return jsonify({'message': 'Usuario no encontrado'}), 404
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token inválido'}), 401
    except MySQLdb.Error as err:
        return jsonify({'message': f'Error de base de datos: {str(err)}'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()

@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Token no proporcionado'}), 401

    token = auth_header.split(' ')[1]

    try:
        decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'])

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT u.id, u.full_name, u.phone, u.email, u.gender, r.name as role_name
            FROM usuarios u
            JOIN roles r ON u.role_id = r.id
        ''')
        usuarios = cursor.fetchall()

        admins = [user for user in usuarios if user['role_name'] == 'Administrador']
        soportes = [user for user in usuarios if user['role_name'] == 'Soporte']
        usuarios_regulares = [user for user in usuarios if user['role_name'] == 'Usuario']

        return jsonify({
            'admins': admins,
            'soportes': soportes,
            'usuarios': usuarios_regulares
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token inválido'}), 401
    except MySQLdb.Error as err:
        return jsonify({'message': f'Error de base de datos: {str(err)}'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()

@app.route('/api/usuarios/<int:user_id>', methods=['DELETE'])
def delete_usuario(user_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Token no proporcionado'}), 401

    token = auth_header.split(' ')[1]

    try:
        decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        if decoded_token['role_name'] != 'Administrador':
            return jsonify({'message': 'No tienes permisos para eliminar usuarios'}), 403

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            INSERT INTO usuarios_eliminados (full_name, phone, email, password, gender, role_id, deleted_at)
            SELECT full_name, phone, email, password, gender, role_id, NOW() 
            FROM usuarios WHERE id = %s
        ''', (user_id,))

        cursor.execute('DELETE FROM usuarios WHERE id = %s', (user_id,))
        
        mysql.connection.commit()
        return jsonify({'message': 'Usuario eliminado exitosamente'})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token inválido'}), 401
    except MySQLdb.Error as err:
        return jsonify({'message': f'Error de base de datos: {str(err)}'}), 500
    finally:
        cursor.close()

@app.route('/api/usuarios/<int:user_id>/role', methods=['PUT'])
def update_usuario_role(user_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Token no proporcionado'}), 401

    token = auth_header.split(' ')[1]

    try:
        decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        if decoded_token['role_name'] != 'Administrador':
            return jsonify({'message': 'No tienes permisos para editar roles'}), 403

        data = request.json
        new_role_name = data.get('role_name')
        new_role_id = get_role_id(new_role_name)

        if not new_role_id:
            return jsonify({'message': 'Rol no encontrado'}), 400

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            UPDATE usuarios SET role_id = %s WHERE id = %s
        ''', (new_role_id, user_id))
        mysql.connection.commit()

        return jsonify({'message': 'Rol de usuario actualizado exitosamente'})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token inválido'}), 401
    except MySQLdb.Error as err:
        return jsonify({'message': f'Error de base de datos: {str(err)}'}), 500
    finally:
        cursor.close()

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Token no proporcionado'}), 401

    token = auth_header.split(' ')[1]

    try:
        jwt.decode(token, app.secret_key, algorithms=['HS256'])

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Obtener total de usuarios
        cursor.execute('SELECT COUNT(*) AS count FROM usuarios')
        total_users = cursor.fetchone()['count']

        # Obtener total de usuarios eliminados
        cursor.execute('SELECT COUNT(*) AS count FROM usuarios_eliminados')
        deleted_users = cursor.fetchone()['count']

        # Obtener usuarios registrados en los últimos 30 días
        cursor.execute('''
            SELECT DATE_FORMAT(created_at, '%Y-%m') AS month, COUNT(*) AS count
            FROM usuarios
            WHERE created_at >= CURDATE() - INTERVAL 30 DAY
            GROUP BY month
        ''')
        recent_users_by_month = cursor.fetchall()

        # Obtener distribución de roles
        cursor.execute('''
            SELECT r.name as role_name, COUNT(*) as count 
            FROM usuarios u
            JOIN roles r ON u.role_id = r.id
            GROUP BY r.name
        ''')
        roles_distribution = cursor.fetchall()

        # Obtener distribución de género
        cursor.execute('''
            SELECT gender, COUNT(*) as count 
            FROM usuarios
            GROUP BY gender
        ''')
        gender_distribution = cursor.fetchall()

        return jsonify({
            'total_users': total_users,
            'deleted_users': deleted_users,
            'recent_users_by_month': recent_users_by_month,
            'roles_distribution': roles_distribution,
            'gender_distribution': gender_distribution
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token inválido'}), 401
    except MySQLdb.Error as err:
        return jsonify({'message': f'Error de base de datos: {str(err)}'}), 500
    finally:
        cursor.close()

@app.route('/api/preferences', methods=['GET'])
def get_preferences():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Token no proporcionado'}), 401

    token = auth_header.split(' ')[1]

    try:
        decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        user_id = decoded_token['user_id']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user_preferences WHERE user_id = %s', (user_id,))
        preferences = cursor.fetchone()

        if preferences:
            return jsonify(preferences)
        else:
            return jsonify({
                'usage_desc': '',
                'needs_desc': '',
                'hardware_pref': '',
                'software_pref': '',
                'budget': ''
            })
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token inválido'}), 401
    except MySQLdb.Error as err:
        return jsonify({'message': f'Error de base de datos: {str(err)}'}), 500
    finally:
        cursor.close()

@app.route('/api/preferences', methods=['POST'])
def save_preferences():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Token no proporcionado'}), 401

    token = auth_header.split(' ')[1]

    try:
        decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        user_id = decoded_token['user_id']

        data = request.json
        usage_desc = data.get('usage_desc')
        needs_desc = data.get('needs_desc')
        hardware_pref = data.get('hardware_pref')
        software_pref = data.get('software_pref')
        budget = data.get('budget')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user_preferences WHERE user_id = %s', (user_id,))
        existing_preferences = cursor.fetchone()

        if existing_preferences:
            cursor.execute('''
                UPDATE user_preferences 
                SET usage_desc = %s, needs_desc = %s, hardware_pref = %s, software_pref = %s, budget = %s 
                WHERE user_id = %s
            ''', (usage_desc, needs_desc, hardware_pref, software_pref, budget, user_id))
        else:
            cursor.execute('''
                INSERT INTO user_preferences (user_id, usage_desc, needs_desc, hardware_pref, software_pref, budget) 
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, usage_desc, needs_desc, hardware_pref, software_pref, budget))

        mysql.connection.commit()
        return jsonify({'message': 'Preferencias guardadas exitosamente'})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token inválido'}), 401
    except MySQLdb.Error as err:
        return jsonify({'message': f'Error de base de datos: {str(err)}'}), 500
    finally:
        cursor.close()

@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Token no proporcionado'}), 401

    token = auth_header.split(' ')[1]

    try:
        decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        user_id = decoded_token['user_id']
        role_name = decoded_token['role_name']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if role_name == 'Soporte':
            cursor.execute('''
                SELECT us.id, us.title, us.suggestion, us.created_at, u.full_name
                FROM user_suggestions us
                JOIN usuarios u ON us.user_id = u.id
            ''')
        else:
            cursor.execute('''
                SELECT us.id, us.title, us.suggestion, us.created_at
                FROM user_suggestions us
                WHERE us.user_id = %s
            ''', (user_id,))
        
        suggestions = cursor.fetchall()
        
        if not suggestions:
            return jsonify({'message': 'Sin sugerencias hechas.'}), 404
        
        return jsonify(suggestions)
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token inválido'}), 401
    except MySQLdb.Error as err:
        return jsonify({'message': f'Error de base de datos: {str(err)}'}), 500
    finally:
        cursor.close()

@app.route('/api/suggestions', methods=['POST'])
def save_suggestions():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Token no proporcionado'}), 401

    token = auth_header.split(' ')[1]

    try:
        decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        user_id = decoded_token['user_id']

        data = request.json
        title = data.get('title')
        suggestion = data.get('suggestion')

        if not suggestion or not title:
            return jsonify({'message': 'El título y la sugerencia no pueden estar vacíos'}), 400

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            INSERT INTO user_suggestions (user_id, title, suggestion, created_at)
            VALUES (%s, %s, %s, NOW())
        ''', (user_id, title, suggestion))

        mysql.connection.commit()
        return jsonify({'message': 'Sugerencia enviada exitosamente'})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token inválido'}), 401
    except MySQLdb.Error as err:
        return jsonify({'message': f'Error de base de datos: {str(err)}'}), 500
    finally:
        cursor.close()

@app.route('/api/suggestions/<int:suggestion_id>', methods=['PUT'])
def update_suggestion(suggestion_id):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Token no proporcionado'}), 401

    token = auth_header.split(' ')[1]

    try:
        decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        user_id = decoded_token['user_id']

        data = request.json
        title = data.get('title')
        new_suggestion = data.get('suggestion')

        if not new_suggestion or not title:
            return jsonify({'message': 'El título y la sugerencia no pueden estar vacíos'}), 400

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            UPDATE user_suggestions 
            SET title = %s, suggestion = %s 
            WHERE id = %s AND user_id = %s
        ''', (title, new_suggestion, suggestion_id, user_id))

        mysql.connection.commit()
        return jsonify({'message': 'Sugerencia actualizada exitosamente'})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token inválido'}), 401
    except MySQLdb.Error as err:
        return jsonify({'message': f'Error de base de datos: {str(err)}'}), 500
    finally:
        cursor.close()

@app.route('/api/chatbot', methods=['POST'])
def chatbot_reply():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'reply': 'Token no proporcionado'}), 401

    token = auth_header.split(' ')[1]

    try:
        jwt.decode(token, app.secret_key, algorithms=['HS256'])

        data = request.json
        message = data.get('message')

        if message == '¿Cuáles son las especificaciones de hardware recomendadas?':
            reply = 'Para un rendimiento óptimo, te recomiendo un procesador Intel i7 o AMD Ryzen 7, 16GB de RAM y una tarjeta gráfica NVIDIA GTX 1660 o mejor.'
        elif message == '¿Qué software me recomiendas?':
            reply = 'Dependiendo de tus necesidades, recomiendo software como Microsoft Office para productividad, Adobe Creative Cloud para diseño, y VSCode para desarrollo.'
        elif message == '¿Cómo optimizar mi sistema para rendimiento?':
            reply = 'Para optimizar tu sistema, asegúrate de desactivar programas innecesarios al inicio, mantener el software actualizado, y realizar limpiezas de disco regularmente.'
        else:
            reply = 'Lo siento, no entiendo la pregunta. ¿Podrías reformularla?'

        return jsonify({'reply': reply})
    except jwt.ExpiredSignatureError:
        return jsonify({'reply': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'reply': 'Token inválido'}), 401

# Ruta para verificar el token
@app.route('/api/verify-token', methods=['POST'])
def verify_token():
    data = request.json
    token = data.get('token')

    try:
        decoded = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return jsonify({'valid': True, 'role': decoded['role_name']})
    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'message': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'message': 'Token inválido'}), 401

# Ruta para extender la sesión
@app.route('/api/extend-session', methods=['POST'])
def extend_session():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'message': 'Token no proporcionado'}), 401

    token = auth_header.split(' ')[1]

    try:
        decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'], options={"verify_exp": False})
        user_id = decoded_token['user_id']
        role_name = decoded_token['role_name']

        new_token = jwt.encode({
            'user_id': user_id,
            'role_name': role_name,
            'exp': datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRATION_MINUTES)
        }, app.secret_key, algorithm='HS256')

        return jsonify({'token': new_token})
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token inválido'}), 401

if __name__ == '__main__':
    app.run()

