USE smart_farm;

ALTER TABLE machinery MODIFY COLUMN status 
ENUM('active', 'broken', 'repair', 'busy') 
DEFAULT 'active';

CREATE TABLE machinery_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    machine_id INT,
    user_id INT,        
    field_id INT,      
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP, 
    expected_end_time DATETIME, 
    return_time DATETIME,      
    FOREIGN KEY (machine_id) REFERENCES machinery(machine_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (field_id) REFERENCES fields(field_id)
);