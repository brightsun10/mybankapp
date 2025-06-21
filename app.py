from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from datetime import datetime
import os

DATABASE_URL = os.environ.get('DATABASE_URL')

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection parameters
hostname = 'localhost'
dbname = 'postgres'
port = 5432
usr = 'postgres'
pwd = 'Nithinp@10'

# Database connection helper
def get_connection():
    return psycopg2.connect(DATABASE_URL)

# Classes for Bank and BankAccount
class BankAccount:
    def __init__(self, account_number, name, username, password, balance=0):
        self.account_number = account_number
        self.name = name
        self.username = username
        self.password = password
        self.balance = balance

    def save_to_db(self):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO bank_account (account_number, account_holder_name, username, balance, password)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.account_number, self.name, self.username, self.balance, self.password))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def authenticate(username, password):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT account_number FROM bank_account WHERE username = %s AND password = %s", (username, password))
            user = cur.fetchone()
            return user[0] if user else None
        finally:
            conn.close()

    @staticmethod
    def get_by_account_number(account_number):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT account_holder_name, balance FROM bank_account WHERE account_number = %s", (account_number,))
            user = cur.fetchone()
            if user:
                return {'name': user[0], 'balance': user[1]}
            return None
        finally:
            conn.close()

class Bank:
    def __init__(self, name):
        self.name = name

    def deposit(self, account_number, amount):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE bank_account SET balance = balance + %s WHERE account_number = %s", (amount, account_number))
            cur.execute("INSERT INTO transactions (account_number, type, amount, timestamp) VALUES (%s, %s, %s, %s)",
                        (account_number, 'deposit', amount, datetime.now()))
            conn.commit()
        finally:
            conn.close()

    def withdraw(self, account_number, amount):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT balance FROM bank_account WHERE account_number = %s", (account_number,))
            balance = cur.fetchone()[0]
            if balance >= amount:
                cur.execute("UPDATE bank_account SET balance = balance - %s WHERE account_number = %s", (amount, account_number))
                cur.execute("INSERT INTO transactions (account_number, type, amount, timestamp) VALUES (%s, %s, %s, %s)",
                            (account_number, 'withdraw', amount, datetime.now()))
                conn.commit()
            else:
                raise ValueError("Insufficient funds")
        finally:
            conn.close()

    def transfer(self, from_account, to_account, amount):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT balance FROM bank_account WHERE account_number = %s", (from_account,))
            balance = cur.fetchone()[0]
            if balance >= amount:
                cur.execute("UPDATE bank_account SET balance = balance - %s WHERE account_number = %s", (amount, from_account))
                cur.execute("UPDATE bank_account SET balance = balance + %s WHERE account_number = %s", (amount, to_account))
                cur.execute("INSERT INTO transactions (account_number, type, amount, timestamp, remarks) VALUES (%s, 'transfer_out', %s, %s, %s)", (from_account, amount, datetime.now(), f'To {to_account}'))
                cur.execute("INSERT INTO transactions (account_number, type, amount, timestamp, remarks) VALUES (%s, 'transfer_in', %s, %s, %s)", (to_account, amount, datetime.now(), f'From {from_account}'))
                conn.commit()
            else:
                raise ValueError("Insufficient funds")
        finally:
            conn.close()

bank = Bank("SBI")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        account_number = 10000000000 + hash(username) % 100000

        account = BankAccount(account_number, name, username, password)
        account.save_to_db()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        account_number = BankAccount.authenticate(username, password)
        if account_number:
            session['account_number'] = account_number
            return redirect(url_for('dashboard'))
        else:
            return "Login failed. Invalid credentials."
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    acc_no = session.get('account_number')
    if not acc_no:
        return redirect(url_for('login'))
    user = BankAccount.get_by_account_number(acc_no)
    return render_template('dashboard.html', name=user['name'], balance=user['balance'], acc_no=acc_no)

@app.route('/deposit', methods=['POST'])
def deposit():
    amount = float(request.form['amount'])
    bank.deposit(session['account_number'], amount)
    return redirect(url_for('dashboard'))

@app.route('/withdraw', methods=['POST'])
def withdraw():
    amount = float(request.form['amount'])
    try:
        bank.withdraw(session['account_number'], amount)
    except ValueError as e:
        return str(e)
    return redirect(url_for('dashboard'))

@app.route('/transfer', methods=['POST'])
def transfer():
    to_account = int(request.form['to_account'])
    amount = float(request.form['amount'])
    try:
        bank.transfer(session['account_number'], to_account, amount)
    except ValueError as e:
        return str(e)
    return redirect(url_for('dashboard'))

@app.route('/transactions')
def transactions():
    acc_no = session.get('account_number')
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT type, amount, timestamp, COALESCE(remarks, '') FROM transactions WHERE account_number = %s ORDER BY timestamp DESC", (acc_no,))
    history = cur.fetchall()
    conn.close()
    return render_template('transactions.html', history=history)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
