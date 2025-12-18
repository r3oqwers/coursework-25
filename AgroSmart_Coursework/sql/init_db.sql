CREATE DATABASE smart_farm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_farm;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, 
    full_name VARCHAR(100) NOT NULL,
    role ENUM('admin', 'agronomist', 'manager') DEFAULT 'agronomist',
    phone VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fields (
    field_id INT AUTO_INCREMENT PRIMARY KEY,
    field_name VARCHAR(100) NOT NULL,
    area_hectares DECIMAL(10, 2) NOT NULL, 
    cadastral_number VARCHAR(50) UNIQUE,   
    soil_type ENUM('Чорнозем', 'Глинистий', 'Піщаний', 'Суглинки') NOT NULL,
    irrigation_status BOOLEAN DEFAULT FALSE 
);

CREATE TABLE machinery (
    machine_id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,      
    machine_type VARCHAR(50) NOT NULL,     
    purchase_year YEAR,
    last_service_date DATE,                
    status ENUM('active', 'repair', 'broken') DEFAULT 'active'
);

CREATE TABLE crops (
    crop_id INT AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(50) NOT NULL,        
    planting_date DATE NOT NULL,
    expected_harvest_date DATE,
    field_id INT,                        
    
    FOREIGN KEY (field_id) REFERENCES fields(field_id) ON DELETE SET NULL
);

CREATE TABLE harvest_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    crop_id INT NOT NULL,
    amount_tons DECIMAL(10, 2) NOT NULL,
    harvest_date DATE DEFAULT (CURRENT_DATE),
    responsible_user_id INT,               
    notes TEXT,                            
    
    FOREIGN KEY (crop_id) REFERENCES crops(crop_id) ON DELETE CASCADE,
    FOREIGN KEY (responsible_user_id) REFERENCES users(user_id) ON DELETE SET NULL
);


INSERT INTO fields (field_name, area_hectares, cadastral_number, soil_type, irrigation_status) VALUES
('Північний Схил', 120.50, 'UA-321-001', 'Чорнозем', 1),
('Долина річки', 45.00, 'UA-321-002', 'Піщаний', 1),
('Старий сад', 15.30, 'UA-321-003', 'Глинистий', 0),
('Західний сектор', 200.00, 'UA-321-004', 'Чорнозем', 0),
('Експериментальне поле', 10.00, 'UA-321-005', 'Суглинки', 1);

INSERT INTO machinery (model_name, machine_type, purchase_year, status) VALUES
('John Deere 8R', 'Трактор', 2020, 'active'),
('CLAAS Lexion 760', 'Комбайн', 2019, 'repair'),
('New Holland T7', 'Трактор', 2021, 'active'),
('Bourgault 3720', 'Сівалка', 2022, 'active'),
('MTZ 82', 'Трактор', 2010, 'broken');

INSERT INTO crops (crop_name, planting_date, expected_harvest_date, field_id) VALUES
('Озима Пшениця', '2023-09-15', '2024-07-20', 1),
('Соняшник', '2024-04-10', '2024-09-01', 2),
('Кукурудза', '2024-04-20', '2024-10-15', 4),
('Соя', '2024-05-05', '2024-09-20', 5);

INSERT INTO users (username, password_hash, full_name, role) VALUES
('admin', 'pbkdf2:sha256:600000$Z7...', 'Головний Адміністратор', 'admin'),
('ivan_agro', 'pbkdf2:sha256:600000$X2...', 'Іван Петренко', 'agronomist');

SHOW TABLES;