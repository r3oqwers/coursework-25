USE smart_farm;

DELETE FROM harvest_logs;
DELETE FROM finances;

INSERT INTO finances (category, description, amount, transaction_date) VALUES
('income', 'Продаж пшениці (партія 1)', 150000.00, '2023-08-10'),
('income', 'Продаж соняшника', 320000.00, '2023-09-15'),
('income', 'Послуги елеватора', 45000.00, '2023-10-01'),
('expense', 'Закупівля палива (ДП)', 85000.00, '2023-03-20'),
('expense', 'Добрива (Селітра)', 120000.00, '2023-04-05'),
('expense', 'Ремонт трактора John Deere', 35000.00, '2023-06-12'),
('expense', 'Зарплати за серпень', 60000.00, '2023-08-30');

INSERT INTO harvest_logs (crop_id, amount_tons, responsible_user_id) VALUES
(1, 150.50, 1), 
(1, 200.00, 2), 
(2, 500.00, 2), 
(2, 120.00, 1), 
(3, 850.00, 2), 
(4, 50.00, 1);  -