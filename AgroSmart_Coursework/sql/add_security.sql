USE smart_farm;

CREATE TABLE system_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,                 
    username VARCHAR(50),         
    action VARCHAR(50) NOT NULL,  
    details TEXT,               
    ip_address VARCHAR(45),       
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);