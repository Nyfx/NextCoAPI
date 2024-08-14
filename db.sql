CREATE DATABASE nextco;

USE nextco;

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password VARCHAR(100) NOT NULL,
    gender ENUM('Masculino', 'Femenino', 'Otro') NOT NULL,
    role_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE usuarios_eliminados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password VARCHAR(100) NOT NULL,
    gender ENUM('Masculino', 'Femenino', 'Otro') NOT NULL,
    role_id INT NOT NULL,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_preferences (
    user_id INT NOT NULL,
    usage_desc VARCHAR(255),
    needs_desc VARCHAR(255),
    hardware_pref VARCHAR(255),
    software_pref VARCHAR(255),
    budget VARCHAR(255),
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES usuarios(id)
);

CREATE TABLE user_suggestions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    suggestion TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES usuarios(id)
);

-- Insertar datos predefinidos en roles
INSERT INTO roles (name) VALUES ('Administrador'), ('Soporte'), ('Usuario');

-- Insertar usuarios predefinidos
INSERT INTO usuarios (full_name, phone, email, password, gender, role_id) VALUES
('Guillermo Angarita Parra', '3136019045', 'gangaritap@unibarranquilla.edu.co', 'Gp3136019045.', 'Masculino', 1),
('Jesus David Altamar Varilla', '3043334976', 'jesusdavidaltamar@unibarranquilla.edu.co', 'Jd3043334976.', 'Masculino', 1),
('Lourde Maria De Avila Gutierrez', '3000000001', 'ldeavila@unibarranquilla.edu.co', 'LDavila1.', 'Femenino', 1),
('Pepito Juarez Alcachofa', '3013451234', 'pepitoalcachofa@correo.com', 'Pepe1234.', 'Masculino', 3),
('Soporte Tecnico', '3001122334', 'soporte@correo.com', 'Soporte1234.', 'Masculino', 2),
('Mariana Rodriguez Lopez', '3156789023', 'marianarodriguez@correo.com', 'MRL1234.', 'Femenino', 3),
('Carlos Alberto Mendoza', '3112345678', 'carlosmendoza@correo.com', 'CAM1234.', 'Masculino', 3),
('Valentina Perez Jimenez', '3209876543', 'valentinaperez@correo.com', 'VPJ1234.', 'Femenino', 3),
('David Andres Salgado', '3223456789', 'davidsalgado@correo.com', 'DAS1234.', 'Masculino', 3),
('Andrea Sofia Gutierrez', '3101122334', 'andreasofia@correo.com', 'ASG1234.', 'Femenino', 3),
('Luis Fernando Ruiz', '3167890123', 'luisruiz@correo.com', 'LFR1234.', 'Masculino', 3),
('Ana Maria Martinez', '3194567890', 'anamaria@correo.com', 'AMM1234.', 'Femenino', 3),
('Jorge Luis Rivera', '3145678901', 'jorgerivera@correo.com', 'JLR1234.', 'Masculino', 2),
('Diana Patricia Suarez', '3009988776', 'dianasuarez@correo.com', 'DPS1234.', 'Femenino', 3),
('Camilo Andres Garcia', '3123456780', 'camilogarcia@correo.com', 'CAG1234.', 'Masculino', 2),
('Tatiana Marcela Pardo', '3139876543', 'tatianapardo@correo.com', 'TMP1234.', 'Femenino', 3),
('Julian Esteban Lopez', '3187654321', 'julianlopez@correo.com', 'JEL1234.', 'Masculino', 3),
('Laura Vanessa Prieto', '3212345678', 'lauraprieto@correo.com', 'LVP1234.', 'Femenino', 3),
('Santiago Torres Mejia', '3234567891', 'santiagotorres@correo.com', 'STM1234.', 'Masculino', 3),
('Paola Andrea Ramirez', '3245678902', 'paolaramirez@correo.com', 'PAR1234.', 'Femenino', 3);

-- Insertar sugerencias de usuarios
INSERT INTO user_suggestions (user_id, title, suggestion) VALUES
(4, 'Mejorar la interfaz de usuario', 'La interfaz es un poco confusa. Sería genial si fuera más intuitiva.'),
(5, 'Agregar más opciones de personalización', 'Sería útil tener más opciones para personalizar la página principal.'),
(6, 'Soporte para idiomas adicionales', 'Por favor, agreguen soporte para más idiomas, especialmente portugués y francés.'),
(7, 'Implementar tema oscuro', 'El tema oscuro ayudaría a reducir la fatiga visual.'),
(8, 'Mejorar la velocidad de carga', 'La página es un poco lenta en dispositivos móviles.'),
(9, 'Añadir más gráficos de análisis', 'Me gustaría ver más gráficos en la sección de estadísticas.'),
(10, 'Función de recuperación de cuenta', 'Sería útil tener una función de recuperación de cuenta en caso de olvidar la contraseña.'),
(11, 'Agregar notificaciones push', 'Las notificaciones push serían útiles para mantenerse actualizado.'),
(12, 'Compatibilidad con navegadores antiguos', 'Asegúrense de que la página funcione bien en navegadores más antiguos.'),
(13, 'Mejorar la seguridad', 'Consideren añadir autenticación de dos factores.'),
(14, 'Mejorar la accesibilidad', 'Asegúrense de que la página sea completamente accesible para personas con discapacidades.'),
(15, 'Agregar tutoriales interactivos', 'Los tutoriales interactivos ayudarían a los nuevos usuarios.'),
(16, 'Reducir la cantidad de pop-ups', 'Los pop-ups son un poco molestos, sería bueno reducirlos.'),
(17, 'Optimizar el uso de memoria', 'En algunos casos, la aplicación usa mucha memoria, lo que ralentiza otros programas.'),
(18, 'Incluir un foro de usuarios', 'Un foro de usuarios permitiría a los usuarios compartir experiencias y ayudarse entre ellos.'),
(19, 'Agregar más temas de color', 'Sería bueno poder elegir entre más temas de color.'),
(20, 'Mejorar el soporte técnico', 'El soporte técnico podría ser más rápido en responder las solicitudes.');
