USE smart_farm;
ALTER TABLE users MODIFY COLUMN role 
ENUM('admin', 'agronomist', 'manager', 'mechanic', 'accountant') 
DEFAULT 'agronomist';