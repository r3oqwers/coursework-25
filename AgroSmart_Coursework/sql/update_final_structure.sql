USE smart_farm;
ALTER TABLE users ADD COLUMN salary DECIMAL(10, 2) DEFAULT 15000.00;
ALTER TABLE crops ADD COLUMN market_price_per_ton DECIMAL(10, 2) DEFAULT 5000.00;

CREATE TABLE IF NOT EXISTS finances (
    finance_id INT AUTO_INCREMENT PRIMARY KEY,
    category ENUM('income', 'expense') NOT NULL, 
    description VARCHAR(255) NOT NULL,           
    amount DECIMAL(15, 2) NOT NULL,              
    transaction_date DATE DEFAULT (CURRENT_DATE)
);

INSERT INTO finances (category, description, amount) VALUES
('expense', 'Закупівля палива', 25000.00),
('income', 'Продаж соняшника (аванс)', 150000.00),
('expense', 'Ремонт комбайна CLAAS', 12000.00);

ALTER TABLE users MODIFY COLUMN role 
ENUM('admin', 'agronomist', 'manager', 'mechanic', 'accountant') 
DEFAULT 'agronomist';