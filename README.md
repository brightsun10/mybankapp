# 🏦 Flask Bank Management Web Application

A full-featured Flask-based banking application where users can register, log in, deposit, withdraw, and transfer funds between accounts. The application uses **PostgreSQL** for data storage and is ready to be deployed on **Render**.

---

## 🚀 Features

- ✅ User registration with unique username
- ✅ Secure login and session management
- ✅ Account dashboard with balance display
- ✅ Deposit and withdraw money
- ✅ Transfer funds to other accounts
- ✅ Transaction history log
- ✅ PostgreSQL backend with schema auto-creation

---

## 🛠️ Tech Stack

- **Backend:** Flask, Gunicorn
- **Database:** PostgreSQL
- **ORM:** Raw SQL using `psycopg2`
- **Deployment:** Render
- **Frontend:** Jinja2 Templates (HTML)

---

## 📦 Folder Structure

├── app.py # Main Flask application
├── templates/ # HTML templates
├── static/ # Static files (CSS, images, etc.)
├── requirements.txt # Python dependencies
├── render.yaml # Render deployment config
└── README.md # Project documentation


---

## ⚙️ Getting Started

### 1. 🔧 Setup Locally

#### Clone the repo:

```bash
git clone https://github.com/your-username/flask-bank-app.git
cd flask-bank-app

Install dependencies:
bash
Copy
Edit
pip install -r requirements.txt
Set up environment variable:
bash
Copy
Edit
export DATABASE_URL="postgresql://<user>:<password>@<host>:<port>/<dbname>"
Replace with your local or cloud PostgreSQL connection string.

Run the app:
bash
Copy
Edit
python app.py
Open your browser at: http://localhost:5000

2. 🚀 Deploy on Render
This project is ready to deploy on Render.

Steps:
Push your code to GitHub.

Create a new Web Service on Render.

Link your GitHub repository.

Set the Build Command:

nginx
Copy
Edit
pip install -r requirements.txt
Set the Start Command:

nginx
Copy
Edit
gunicorn app:app
Add a PostgreSQL Database on Render and attach its connectionString as the DATABASE_URL environment variable in render.yaml.

The database tables will be created automatically on the first run.

🧪 Test Accounts
You can register a new account via the UI at /register. All actions like deposit, withdraw, transfer, and transaction history can be tested from the dashboard after login.

✅ TODO / Improvements
🔒 Password hashing with werkzeug.security

📧 Email verification / password reset

📱 Responsive UI with Bootstrap

📊 Transaction charts or analytics

📃 License
This project is licensed under the MIT License.

🙋‍♂️ Author
Nithin P
📫 nithinpsea10@gmail.com
🔗 LinkedIn

