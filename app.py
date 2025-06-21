from flask import Flask, render_template, request, redirect, session, url_for, flash
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def create_tables():
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS bank_account (
                account_number BIGINT PRIMARY KEY,
                account_holder_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                balance NUMERIC DEFAULT 0,
                password TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                account_number BIGINT REFERENCES bank_account(account_number),
                type TEXT,
                amount NUMERIC,
                timestamp TIMESTAMP DEFAULT NOW(),
                remarks TEXT
            )
        """)

        conn.commit()
        print("Tables created successfully (if not exist).")

    except Exception as e:
        print("Error while creating tables:", e)

    finally:
        if conn:
            conn.close()
# Call this once when your app starts
create_tables()

class BankAccount:
    def __init__(self, account_number, name, username, balance):
        self.account_number = account_number
        self.name = name
        self.username = username
        self.balance = balance

    @staticmethod
    def authenticate(username, password):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT account_number, account_holder_name, balance FROM bank_account WHERE username = %s AND password = %s", (username, password))
            user = cur.fetchone()
            if user:
                return BankAccount(user[0], user[1], username, float(user[2]))
            return None
        finally:
            conn.close()

    @staticmethod
    def get(account_number):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT account_holder_name, username, balance FROM bank_account WHERE account_number = %s", (account_number,))
            user = cur.fetchone()
            if user:
                return BankAccount(account_number, user[0], user[1], float(user[2]))
            return None
        finally:
            conn.close()

class Bank:
    def deposit(self, account_number, amount):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE bank_account SET balance = balance + %s WHERE account_number = %s", (amount, account_number))
        cur.execute("INSERT INTO transactions (account_number, type, amount, timestamp, remarks) VALUES (%s, %s, %s, %s, %s)",
                    (account_number, 'Deposit', amount, datetime.now(), 'User deposit'))
        conn.commit()
        conn.close()

    def withdraw(self, account_number, amount):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT balance FROM bank_account WHERE account_number = %s", (account_number,))
        balance = cur.fetchone()[0]
        if balance < amount:
            raise ValueError("Insufficient balance")
        cur.execute("UPDATE bank_account SET balance = balance - %s WHERE account_number = %s", (amount, account_number))
        cur.execute("INSERT INTO transactions (account_number, type, amount, timestamp, remarks) VALUES (%s, %s, %s, %s, %s)",
                    (account_number, 'Withdraw', amount, datetime.now(), 'User withdraw'))
        conn.commit()
        conn.close()

    def transfer(self, from_account, to_account, amount):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT balance FROM bank_account WHERE account_number = %s", (from_account,))
        balance = cur.fetchone()[0]
        if balance < amount:
            raise ValueError("Insufficient balance")
        cur.execute("UPDATE bank_account SET balance = balance - %s WHERE account_number = %s", (amount, from_account))
        cur.execute("UPDATE bank_account SET balance = balance + %s WHERE account_number = %s", (amount, to_account))
        cur.execute("INSERT INTO transactions (account_number, type, amount, timestamp, remarks) VALUES (%s, 'transfer_out', %s, %s, %s)",
                    (from_account, amount, datetime.now(), f'Transfer to {to_account}'))
        cur.execute("INSERT INTO transactions (account_number, type, amount, timestamp, remarks) VALUES (%s, 'transfer_in', %s, %s, %s)",
                    (to_account, amount, datetime.now(), f'Transfer from {from_account}'))
        conn.commit()
        conn.close()

bank = Bank()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['account_holder_name']
        username = request.form['username']
        password = request.form['password']
        deposit = float(request.form['initial_deposit'])

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT MAX(account_number) FROM bank_account")
        max_acc = cur.fetchone()[0] or 10000000000
        acc_number = max_acc + 1

        try:
            cur.execute("INSERT INTO bank_account (account_number, account_holder_name, username, balance, password) VALUES (%s, %s, %s, %s, %s)",
                        (acc_number, name, username, deposit, password))
            conn.commit()
            flash("Account created successfully! Please login.", "success")
            return redirect('/login')
        except Exception as e:
            conn.rollback()
            flash(f"Registration failed: {e}", "danger")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = BankAccount.authenticate(username, password)
        if user:
            session['account_number'] = user.account_number
            session['name'] = user.name
            session['balance'] = user.balance
            return redirect('/dashboard')
        else:
            flash("Invalid username or password", "danger")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'account_number' not in session:
        return redirect('/login')

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT timestamp, type, amount, remarks FROM transactions WHERE account_number=%s ORDER BY timestamp DESC LIMIT 5", (session['account_number'],))
    transactions = cur.fetchall()
    conn.close()

    txn_list = [{'timestamp': t[0], 'type': t[1], 'amount': t[2], 'remarks': t[3]} for t in transactions]
    return render_template('dashboard.html', 
                           name=session['name'],
                           acc_no=session['account_number'],
                           balance=session['balance'],
                           transactions=txn_list)

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'account_number' not in session:
        return redirect('/login')
    amount = float(request.form['amount'])
    bank.deposit(session['account_number'], amount)
    session['balance'] += amount
    flash("Deposit successful!", "success")
    return redirect('/dashboard')

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'account_number' not in session:
        return redirect('/login')
    amount = float(request.form['amount'])
    try:
        bank.withdraw(session['account_number'], amount)
        session['balance'] -= amount
        flash("Withdrawal successful!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect('/dashboard')

@app.route('/transfer', methods=['POST'])
def transfer():
    if 'account_number' not in session:
        return redirect('/login')
    to_account = int(request.form['to_account'])
    amount = float(request.form['amount'])
    try:
        bank.transfer(session['account_number'], to_account, amount)
        session['balance'] -= amount
        flash("Transfer completed successfully", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect('/dashboard')

@app.route('/transactions')
def transactions():
    if 'account_number' not in session:
        return redirect('/login')
    acc_no = session.get('account_number')
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT type, amount, timestamp, COALESCE(remarks, '') FROM transactions WHERE account_number = %s ORDER BY timestamp DESC", (acc_no,))
    history = cur.fetchall()
    conn.close()
    return render_template('transactions.html', history=history)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
