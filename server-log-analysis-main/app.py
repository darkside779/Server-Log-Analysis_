from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
import plotly.io as pio
import plotly.express as px
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key
db = SQLAlchemy(app)

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if not logged in

# Define the User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Define the LogEntry model
class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    request_method = db.Column(db.String(10), nullable=False)
    request_path = db.Column(db.String(2083), nullable=False)
    response_code = db.Column(db.Integer, nullable=False)
    user_agent = db.Column(db.String(255))
    referrer = db.Column(db.String(2083))

# Load data from CSV and populate the database (run this once to populate the database)
def populate_db():
    df = pd.read_csv('data/csv/server_logs.csv')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d/%b/%Y:%H:%M:%S %z')

    print("CSV loaded. Number of rows:", len(df))

    for index, row in df.iterrows():
        print(f"Processing row {index + 1}/{len(df)}")
        log_entry = LogEntry(
            timestamp=row['Timestamp'],
            ip_address=row['IP Address'],
            request_method=row['Request Method'],
            request_path=row['Request Path'],
            response_code=row['Status Code'],
            user_agent=row.get('User Agent'),
            referrer=row.get('Referrer')
        )
        db.session.add(log_entry)
    db.session.commit()
    print("Database populated.")

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Protected route for the dashboard
@app.route('/')
@login_required
def index():
    # Query the top 10 most frequent IP addresses
    ip_counts = db.session.query(
        LogEntry.ip_address, db.func.count(LogEntry.ip_address).label('Count')
    ).group_by(LogEntry.ip_address).order_by(db.func.count(LogEntry.ip_address).desc()).limit(10).all()
    ip_counts_df = pd.DataFrame(ip_counts, columns=['IP Address', 'Count'])
    fig1 = px.bar(ip_counts_df, x='IP Address', y='Count', title='Top 10 Most Frequent IP Addresses')
    plot1_html = pio.to_html(fig1, full_html=False)

    # Query the number of requests over time
    requests_over_time = db.session.query(
        db.func.date(LogEntry.timestamp).label('Date'), db.func.count(LogEntry.id).label('Number of Requests')
    ).group_by(db.func.date(LogEntry.timestamp)).all()
    requests_df = pd.DataFrame(requests_over_time, columns=['Date', 'Number of Requests'])
    fig2 = px.line(requests_df, x='Date', y='Number of Requests', title='Requests Over Time')
    plot2_html = pio.to_html(fig2, full_html=False)

    # Query the number of successful requests for different paths
    request_counts = db.session.query(
        LogEntry.request_path, db.func.count(LogEntry.request_path).label('Count')
    ).filter(LogEntry.response_code == 200).group_by(LogEntry.request_path).all()
    request_counts_df = pd.DataFrame(request_counts, columns=['Request Path', 'Count'])
    fig3 = px.bar(request_counts_df, x='Request Path', y='Count', title='Number of Successful Requests for Different Paths/Resources')
    plot3_html = pio.to_html(fig3, full_html=False)

    return render_template('index.html', plot1=plot1_html, plot2=plot2_html, plot3=plot3_html)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Uncomment the following line if you need to populate the database
        # populate_db()
        # Create an admin user if it doesn't exist
        if User.query.filter_by(username='admin').first() is None:
            admin_user = User(username='admin')
            admin_user.set_password('password123')  # Change the password for production use
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)

# Handle any exceptions during commit
try:
    db.session.commit()
except Exception as e:
    db.session.rollback()
    print(f"Error occurred during commit: {e}")
