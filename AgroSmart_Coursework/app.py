import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash


basedir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(basedir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'agrosecret2025'  

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Maria2007', 
    'database': 'smart_farm'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def log_action(action, details):
    user_id = session.get('user_id', None)
    username = session.get('username', 'Guest') 
    ip = request.remote_addr
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO system_logs (user_id, username, action, details, ip_address) 
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (user_id, username, action, details, ip))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Помилка запису логу: {e}")

def log_action(action, details):
    user_id = session.get('user_id', None)
    username = session.get('username', 'Guest') 
    ip = request.remote_addr
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO system_logs (user_id, username, action, details, ip_address) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (user_id, username, action, details, ip))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Помилка логування: {e}")

class Validator:
    @staticmethod
    def validate_user_data(username, password, salary):
        errors = []

        if not username or len(username) < 3:
            errors.append("Логін має бути не менше 3 символів!")
            
        if password and len(password) < 4:
            errors.append("Пароль надто простий (мінімум 4 символи)!")
            
        try:
            if float(salary) < 0:
                errors.append("Зарплата не може бути від'ємною!")
        except ValueError:
            errors.append("Зарплата має бути числом!")
            
        return errors
    
@app.route('/')
def index():
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['user_id']
                session['role'] = user['role']
                session['name'] = user['full_name']
                session['username'] = user['username']  
                session['salary'] = user['salary']
                
                log_action('LOGIN_SUCCESS', f'Користувач {username} увійшов у систему')
                
                return redirect(url_for('dashboard'))
            else:
                log_action('LOGIN_FAILED', f'Невірний пароль для логіна: {username}')
                flash('Невірний логін або пароль!', 'danger')
                
        except mysql.connector.Error as err:
            flash(f'Помилка бази даних: {err}', 'danger')
            
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT SUM(area_hectares) as total_area FROM fields")
    stats = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) as count FROM machinery WHERE status = 'busy'")
    busy_stats = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) as count FROM machinery WHERE status IN ('broken', 'repair')")
    repair_stats = cursor.fetchone()
    
    conn.close()
    
    return render_template('dashboard.html', 
                           user=session, 
                           stats=stats, 
                           busy_stats=busy_stats, 
                           repair_stats=repair_stats)


@app.route('/fields')
def fields_list():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    if session.get('role') not in ['admin', 'agronomist', 'manager']:
        flash('У вас немає доступу до земельного банку!', 'danger')
        return redirect(url_for('dashboard'))
    
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'field_name')
    
    allowed_sort = ['field_name', 'area_hectares', 'soil_type']
    if sort_by not in allowed_sort: sort_by = 'field_name'

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if search_query:
        sql = f"SELECT * FROM fields WHERE field_name LIKE %s ORDER BY {sort_by}"
        cursor.execute(sql, (f"%{search_query}%",))
    else:
        sql = f"SELECT * FROM fields ORDER BY {sort_by}"
        cursor.execute(sql)
        
    fields = cursor.fetchall()

    sql_active_machines = """
        SELECT l.field_id, m.model_name, m.machine_type, u.full_name
        FROM machinery_logs l
        JOIN machinery m ON l.machine_id = m.machine_id
        JOIN users u ON l.user_id = u.user_id
        WHERE l.return_time IS NULL
    """
    cursor.execute(sql_active_machines)
    active_machines = cursor.fetchall()

    for field in fields:
        field['machines_on_field'] = []
        for machine in active_machines:
            if machine['field_id'] == field['field_id']:
                field['machines_on_field'].append({
                    'text': f"{machine['model_name']} ({machine['full_name']})",
                    'type': machine['machine_type']
                })

    conn.close()
    
    return render_template('fields.html', fields=fields, current_sort=sort_by, search_query=search_query)

@app.route('/add_field', methods=['POST'])
def add_field():
    if 'user_id' not in session: return redirect(url_for('login'))

    name = request.form['field_name']
    area = request.form['area']
    cadastral = request.form['cadastral']
    soil = request.form['soil']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO fields (field_name, area_hectares, cadastral_number, soil_type) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (name, area, cadastral, soil))
        conn.commit()
        conn.close()
        flash('Поле успішно додано!', 'success')
    except mysql.connector.Error as err:
        flash(f'Помилка при додаванні: {err}', 'danger')
        
    return redirect(url_for('fields_list'))

@app.route('/edit_field', methods=['POST'])
def edit_field():
    if 'user_id' not in session: return redirect(url_for('login'))

    field_id = request.form['field_id']
    name = request.form['field_name']
    area = request.form['area']
    cadastral = request.form['cadastral']
    soil = request.form['soil']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """UPDATE fields 
                 SET field_name=%s, area_hectares=%s, cadastral_number=%s, soil_type=%s 
                 WHERE field_id=%s"""
        cursor.execute(sql, (name, area, cadastral, soil, field_id))
        conn.commit()
        conn.close()
        flash('Дані поля оновлено!', 'info')
    except mysql.connector.Error as err:
        flash(f'Помилка редагування: {err}', 'danger')
        
    return redirect(url_for('fields_list'))

@app.route('/delete_field/<int:id>', methods=['POST'])
def delete_field(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fields WHERE field_id = %s", (id,))
        conn.commit()
        conn.close()
        flash('Поле видалено!', 'warning')
    except mysql.connector.Error as err:
        flash(f'Не вдалося видалити: {err}', 'danger')
        
    return redirect(url_for('fields_list'))

@app.route('/users')
def users_list():
    if 'user_id' not in session: return redirect(url_for('login'))
    if session.get('role') != 'admin':
        flash('У вас немає прав доступу до цієї сторінки!', 'danger')
        return redirect(url_for('dashboard'))

    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'user_id') 

    allowed_sort = ['user_id', 'username', 'full_name', 'role', 'salary', 'created_at']
    if sort_by not in allowed_sort: sort_by = 'user_id'
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if search_query:
        sql = f"""
            SELECT * FROM users 
            WHERE username LIKE %s OR full_name LIKE %s 
            ORDER BY {sort_by}
        """
        params = (f"%{search_query}%", f"%{search_query}%")
        cursor.execute(sql, params)
    else:
        sql = f"SELECT * FROM users ORDER BY {sort_by}"
        cursor.execute(sql)

    users = cursor.fetchall()
    conn.close()
    
    return render_template('users.html', users=users, search_query=search_query, current_sort=sort_by)


@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    username = request.form['username']
    password = request.form['password']
    full_name = request.form['full_name']
    role = request.form['role']
    salary = request.form['salary'] 
    validation_errors = Validator.validate_user_data(username, password, salary)
    
    if validation_errors:
        for error in validation_errors:
            flash(error, 'danger')
        return redirect(url_for('users_list'))

    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = "INSERT INTO users (username, password_hash, full_name, role, salary) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (username, hashed_password, full_name, role, salary))
        
        conn.commit()
        conn.close()
        
        flash(f'Користувача {username} успішно створено!', 'success')
        
    except mysql.connector.Error as err:
        flash(f'Помилка створення (можливо такий логін вже є): {err}', 'danger')

    return redirect(url_for('users_list'))

@app.route('/edit_user', methods=['POST'])
def edit_user():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    user_id = request.form['user_id']
    username = request.form['username']
    full_name = request.form['full_name']
    role = request.form['role']
    salary = request.form['salary'] if request.form['salary'] else 0
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if password:
            hashed_password = generate_password_hash(password)
            sql = """UPDATE users 
                     SET username=%s, full_name=%s, role=%s, salary=%s, password_hash=%s 
                     WHERE user_id=%s"""
            cursor.execute(sql, (username, full_name, role, salary, hashed_password, user_id))
        else:
            sql = """UPDATE users 
                     SET username=%s, full_name=%s, role=%s, salary=%s 
                     WHERE user_id=%s"""
            cursor.execute(sql, (username, full_name, role, salary, user_id))
        
        conn.commit()
        flash('Дані працівника успішно оновлено!', 'info')
    except mysql.connector.Error as err:
        flash(f'Помилка редагування: {err}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('users_list'))

@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    if id == session['user_id']:
        flash('Ви не можете видалити власний акаунт!', 'danger')
        return redirect(url_for('users_list'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = %s", (id,))
        conn.commit()
        conn.close()
        log_action('USER_DELETE', f'Адмін видалив користувача ID {id}')
        
        flash('Працівника звільнено (видалено)!', 'warning')
    except mysql.connector.Error as err:
        flash(f'Помилка: {err}', 'danger')
        
    return redirect(url_for('users_list'))


@app.route('/machinery')
def machinery_list():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    allowed_roles = ['admin', 'manager', 'mechanic', 'agronomist'] 
    if session.get('role') not in allowed_roles:
        flash('Доступ заборонено!', 'danger')
        return redirect(url_for('dashboard'))

    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'status')
    
    allowed_sort = ['status', 'model_name', 'machine_type']
    if sort_by not in allowed_sort: sort_by = 'status'

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
  
    
    base_sql = """
        SELECT m.*, 
               u.full_name as driver_name, 
               f.field_name as current_field,
               l.start_time,
               l.expected_end_time
        FROM machinery m
        LEFT JOIN machinery_logs l ON m.machine_id = l.machine_id AND l.return_time IS NULL
        LEFT JOIN users u ON l.user_id = u.user_id
        LEFT JOIN fields f ON l.field_id = f.field_id
        WHERE 1=1
    """
    params = []

    if search_query:
        base_sql += " AND (m.model_name LIKE %s OR m.machine_type LIKE %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    
    if sort_by == 'status':
        base_sql += " ORDER BY FIELD(m.status, 'busy', 'broken', 'repair', 'active'), m.model_name"
    else:
        base_sql += f" ORDER BY m.{sort_by}"

    cursor.execute(base_sql, tuple(params))
    machines = cursor.fetchall()

    cursor.execute("SELECT field_id, field_name FROM fields")
    fields = cursor.fetchall()
    
    cursor.execute("SELECT user_id, full_name FROM users") 
    users = cursor.fetchall()

    conn.close()
    
    return render_template('machinery.html', 
                           machines=machines, 
                           fields=fields, 
                           users=users,
                           search_query=search_query, 
                           current_sort=sort_by)


@app.route('/assign_machine', methods=['POST'])
def assign_machine():
    if session.get('role') not in ['admin', 'manager', 'mechanic']: return redirect(url_for('machinery_list'))

    m_id = request.form['machine_id']
    driver = request.form['user_id']
    field = request.form['field_id']
    end_time = request.form['end_time'] 

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT status FROM machinery WHERE machine_id = %s", (m_id,))
        status = cursor.fetchone()[0]
        
        if status != 'active':
            flash('Цю техніку не можна видати! Вона зламана або вже зайнята.', 'danger')
        else:
            cursor.execute("UPDATE machinery SET status = 'busy' WHERE machine_id = %s", (m_id,))

            sql_log = """INSERT INTO machinery_logs (machine_id, user_id, field_id, expected_end_time) 
                         VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql_log, (m_id, driver, field, end_time))
            
            conn.commit()
            flash('Техніка успішно виїхала на поле!', 'success')
            
        conn.close()
    except Exception as e:
        flash(f'Помилка: {e}', 'danger')

    return redirect(url_for('machinery_list'))

@app.route('/return_machine/<int:id>', methods=['POST'])
def return_machine(id):
    if session.get('role') not in ['admin', 'manager', 'mechanic']: return redirect(url_for('machinery_list'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
 
        cursor.execute("UPDATE machinery SET status = 'active' WHERE machine_id = %s", (id,))
        cursor.execute("""UPDATE machinery_logs 
                          SET return_time = NOW() 
                          WHERE machine_id = %s AND return_time IS NULL""", (id,))
        
        conn.commit()
        conn.close()
        flash('Техніка повернулася в гараж!', 'success')
    except Exception as e:
        flash(f'Помилка: {e}', 'danger')
        
    return redirect(url_for('machinery_list'))

@app.route('/add_machine', methods=['POST'])
def add_machine():
    if session.get('role') not in ['admin', 'manager']: return redirect(url_for('machinery_list'))
    model = request.form['model']
    m_type = request.form['type']
    year = request.form['year']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO machinery (model_name, machine_type, purchase_year, status) VALUES (%s, %s, %s, 'active')", (model, m_type, year))
        conn.commit()
        conn.close()
        flash('Техніка додана!', 'success')
    except Exception as e: flash(f'Помилка: {e}', 'danger')
    return redirect(url_for('machinery_list'))

@app.route('/edit_machine', methods=['POST'])
def edit_machine():
    if 'user_id' not in session: return redirect(url_for('login'))
    m_id = request.form['machine_id']
    model = request.form['model']
    m_type = request.form['type']
    year = request.form['year']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE machinery SET model_name=%s, machine_type=%s, purchase_year=%s WHERE machine_id=%s", (model, m_type, year, m_id))
        conn.commit()
        conn.close()
        flash('Дані оновлено!', 'info')
    except Exception as e: flash(f'Помилка: {e}', 'danger')
    return redirect(url_for('machinery_list'))

@app.route('/delete_machine/<int:id>', methods=['POST'])
def delete_machine(id):
    if session.get('role') != 'admin': return redirect(url_for('machinery_list'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM machinery WHERE machine_id = %s", (id,))
        conn.commit()
        conn.close()
        flash('Техніку списано!', 'warning')
    except Exception as e: flash(f'Помилка: {e}', 'danger')
    return redirect(url_for('machinery_list'))

@app.route('/set_broken/<int:id>', methods=['POST'])
def set_broken(id):
    if session.get('role') not in ['admin', 'mechanic']: return redirect(url_for('machinery_list'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE machinery SET status = 'broken' WHERE machine_id = %s", (id,))
        conn.commit()
        conn.close()
        flash('Статус змінено на ЗЛАМАНИЙ!', 'danger')
    except Exception as e: flash(f'Помилка: {e}', 'danger')
    return redirect(url_for('machinery_list'))

@app.route('/set_repair/<int:id>', methods=['POST'])
def set_repair(id):
    if session.get('role') not in ['admin', 'mechanic']: return redirect(url_for('machinery_list'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE machinery SET status = 'repair' WHERE machine_id = %s", (id,))
        conn.commit()
        conn.close()
        flash('Техніка відправлена в ремонт.', 'warning')
    except Exception as e: flash(f'Помилка: {e}', 'danger')
    return redirect(url_for('machinery_list'))

@app.route('/finances')
def finances_list():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    if session.get('role') not in ['admin', 'accountant', 'manager']:
        flash('Доступ до фінансів обмежено!', 'danger')
        return redirect(url_for('dashboard'))

    search_query = request.args.get('search', '') 
    filter_date = request.args.get('date', '')    
    sort_by = request.args.get('sort', 'newest') 

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    sql = "SELECT * FROM finances WHERE 1=1"
    params = []

    if search_query:
        sql += " AND description LIKE %s"
        params.append(f"%{search_query}%")

    if filter_date:
        sql += " AND transaction_date = %s"
        params.append(filter_date)

    if sort_by == 'amount_desc':     
        sql += " ORDER BY amount DESC"
    elif sort_by == 'amount_asc':   
        sql += " ORDER BY amount ASC"
    elif sort_by == 'oldest':        
        sql += " ORDER BY transaction_date ASC, finance_id ASC"
    else:                           
        sql += " ORDER BY transaction_date DESC, finance_id DESC"

    cursor.execute(sql, tuple(params))
    transactions = cursor.fetchall()
    cursor.execute("SELECT SUM(amount) as income FROM finances WHERE category = 'income'")
    total_income = cursor.fetchone()['income'] or 0
    
    cursor.execute("SELECT SUM(amount) as expense FROM finances WHERE category = 'expense'")
    total_expense = cursor.fetchone()['expense'] or 0
    
    balance = total_income - total_expense
    
    conn.close()
    
    return render_template('finances.html', 
                           transactions=transactions, 
                           balance=balance, 
                           income=total_income, 
                           expense=total_expense,
                           search_query=search_query, 
                           filter_date=filter_date,
                           current_sort=sort_by)


@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if session.get('role') not in ['admin', 'accountant']:
        flash('Тільки бухгалтер може вносити транзакції!', 'danger')
        return redirect(url_for('finances_list'))

    category = request.form['category'] 
    description = request.form['description']
    amount = request.form['amount']
    date = request.form['date']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO finances (category, description, amount, transaction_date) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (category, description, amount, date))
        conn.commit()
        log_action('FINANCE_ADD', f'Проведено операцію: {description} ({amount} грн)')  
        
        conn.close()
        flash('Транзакцію успішно проведено!', 'success')
    except mysql.connector.Error as err:
        flash(f'Помилка: {err}', 'danger')

    return redirect(url_for('finances_list'))

@app.route('/delete_transaction/<int:id>', methods=['POST'])
def delete_transaction(id):
    if session.get('role') != 'admin':
        flash('Видаляти фінансові записи може тільки Адмін!', 'danger')
        return redirect(url_for('finances_list'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM finances WHERE finance_id = %s", (id,))
        conn.commit()
        conn.close()
        flash('Запис видалено!', 'warning')
    except mysql.connector.Error as err:
        flash(f'Помилка: {err}', 'danger')
        
    return redirect(url_for('finances_list'))


@app.route('/crops')
def crops_list():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    allowed = ['admin', 'agronomist', 'manager']
    if session.get('role') not in allowed:
        flash('Це розділ для агрономів!', 'danger')
        return redirect(url_for('dashboard'))

    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'newest')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql_crops = """
        SELECT c.*, f.field_name 
        FROM crops c
        JOIN fields f ON c.field_id = f.field_id
        WHERE 1=1
    """
    params = []

    if search_query:
        sql_crops += " AND (c.crop_name LIKE %s OR f.field_name LIKE %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])

    if sort_by == 'name_asc':
        sql_crops += " ORDER BY c.crop_name ASC"
    elif sort_by == 'field':
        sql_crops += " ORDER BY f.field_name ASC"
    elif sort_by == 'harvest_date':
        sql_crops += " ORDER BY c.expected_harvest_date ASC"
    else: 
        sql_crops += " ORDER BY c.planting_date DESC"

    cursor.execute(sql_crops, tuple(params))
    crops = cursor.fetchall()

    sql_harvest = """
        SELECT h.*, c.crop_name, u.full_name
        FROM harvest_logs h
        JOIN crops c ON h.crop_id = c.crop_id
        LEFT JOIN users u ON h.responsible_user_id = u.user_id
        ORDER BY h.harvest_date DESC
    """
    cursor.execute(sql_harvest)
    harvest_logs = cursor.fetchall()

    cursor.execute("SELECT field_id, field_name FROM fields")
    fields = cursor.fetchall()
    
    conn.close()
    
    return render_template('crops.html', 
                           crops=crops, 
                           harvest_logs=harvest_logs, 
                           fields=fields,
                           search_query=search_query,
                           current_sort=sort_by)

@app.route('/add_crop', methods=['POST'])
def add_crop():
    if session.get('role') not in ['admin', 'agronomist']: return redirect(url_for('crops_list'))

    name = request.form['crop_name']
    field = request.form['field_id']
    p_date = request.form['planting_date']
    h_date = request.form['harvest_date']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO crops (crop_name, field_id, planting_date, expected_harvest_date) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (name, field, p_date, h_date))
        conn.commit()
        conn.close()
        flash('Посівну кампанію зареєстровано!', 'success')
    except mysql.connector.Error as err:
        flash(f'Помилка: {err}', 'danger')

    return redirect(url_for('crops_list'))

@app.route('/edit_crop', methods=['POST'])
def edit_crop():
    if session.get('role') not in ['admin', 'agronomist']: return redirect(url_for('crops_list'))

    crop_id = request.form['crop_id']
    name = request.form['crop_name']
    field = request.form['field_id']
    p_date = request.form['planting_date']
    h_date = request.form['harvest_date']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """UPDATE crops 
                 SET crop_name=%s, field_id=%s, planting_date=%s, expected_harvest_date=%s 
                 WHERE crop_id=%s"""
        cursor.execute(sql, (name, field, p_date, h_date, crop_id))
        conn.commit()
        conn.close()
        flash('Дані про культуру оновлено!', 'info')
    except mysql.connector.Error as err:
        flash(f'Помилка редагування: {err}', 'danger')

    return redirect(url_for('crops_list'))

@app.route('/delete_crop/<int:id>', methods=['POST'])
def delete_crop(id):
    if session.get('role') not in ['admin', 'agronomist']: return redirect(url_for('crops_list'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM crops WHERE crop_id = %s", (id,))
        conn.commit()
        conn.close()
        flash('Культуру видалено (списано)!', 'warning')
    except mysql.connector.Error as err:
        flash(f'Помилка: {err}', 'danger')
        
    return redirect(url_for('crops_list'))

@app.route('/add_harvest', methods=['POST'])
def add_harvest():
    if session.get('role') not in ['admin', 'agronomist']: return redirect(url_for('crops_list'))

    crop_id = request.form['crop_id']
    amount = request.form['amount']
    date = request.form['date']
    user_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO harvest_logs (crop_id, amount_tons, harvest_date, responsible_user_id) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (crop_id, amount, date, user_id))
    conn.commit()
    conn.close()
    flash('Врожай успішно обліковано!', 'success')
    return redirect(url_for('crops_list'))


@app.route('/logs')
def view_logs():
    if session.get('role') != 'admin':
        flash('Доступ заборонено!', 'danger')
        return redirect(url_for('dashboard'))
    
    filter_date = request.args.get('date', '')
    show_attacks = request.args.get('attacks', '') 

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM system_logs WHERE 1=1"
    params = []

    if filter_date:
        sql += " AND DATE(created_at) = %s"
        params.append(filter_date)

    if show_attacks:
        sql += " AND action = 'LOGIN_FAILED'"

    sql += " ORDER BY created_at DESC LIMIT 100"

    cursor.execute(sql, tuple(params))
    logs = cursor.fetchall()
    conn.close()
    
    return render_template('logs.html', logs=logs, filter_date=filter_date, show_attacks=show_attacks)

if __name__ == '__main__':
    app.run(debug=True)