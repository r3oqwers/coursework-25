import mysql.connector
from werkzeug.security import generate_password_hash

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Maria2007', 
    'database': 'smart_farm'
}

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    new_password = "admin123"
    hashed_password = generate_password_hash(new_password)

    sql = "UPDATE users SET password_hash = %s WHERE username = %s"
    val = (hashed_password, 'admin')
    
    cursor.execute(sql, val)
    conn.commit()
    
    print(f"Успіх! Пароль для 'admin' змінено на '{new_password}' (у базі він зашифрований).")

except mysql.connector.Error as err:
    print(f"Помилка: {err}")
finally:
    if 'conn' in locals() and conn.is_connected():
        conn.close()