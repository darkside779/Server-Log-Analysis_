from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import plotly.io as pio
import plotly.graph_objects as go
import plotly.express as px
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
from ua_parser import user_agent_parser  
from utils import SetEnv  

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'our_secret_key'
db = SQLAlchemy(app)

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper function for parsing user agents
def parse_user_agent(ua_string):
    return user_agent_parser.Parse(ua_string)

# User agent analysis function
def user_agent_analysis():
    _env = SetEnv.set_path()
    file_path = f'{_env}/data/csv/server_logs.csv'

    # Read the data from the CSV file
    df = pd.read_csv(file_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d/%b/%Y:%H:%M:%S %z')

    # Extract User Agents
    user_agents = df['User Agent']

    # Parse each user agent string and extract device and browser information
    parsed_user_agents = [parse_user_agent(ua) for ua in user_agents if pd.notnull(ua)]
    devices = [ua.get('device', {}).get('family') for ua in parsed_user_agents]
    browsers = [ua.get('user_agent', {}).get('family') for ua in parsed_user_agents]

    # Count the occurrences of each device and browser
    device_counts = pd.Series(devices).value_counts().reset_index(name='Count')
    device_counts.columns = ['Device', 'Count']

    browser_counts = pd.Series(browsers).value_counts().reset_index(name='Count')
    browser_counts.columns = ['Browser', 'Count']

    return device_counts, browser_counts


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user is not None and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

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

@app.route('/')
@login_required
def index():
    ip_counts = db.session.query(
        LogEntry.ip_address, db.func.count(LogEntry.ip_address).label('Count')
    ).group_by(LogEntry.ip_address).order_by(db.func.count(LogEntry.ip_address).desc()).limit(10).all()

    ip_counts_df = pd.DataFrame(ip_counts, columns=['IP Address', 'Count'])
    fig1 = px.bar(ip_counts_df, x='IP Address', y='Count', title='Top 10 Most Frequent IP Addresses')
    plot1_html = pio.to_html(fig1, full_html=False)

    requests_over_time = db.session.query(LogEntry.timestamp.label('Timestamp')).all()
    requests_df = pd.DataFrame(requests_over_time, columns=['Timestamp'])
    requests_over_time_grouped = requests_df.groupby('Timestamp').size().reset_index(name='Number of Requests')
    fig2 = px.line(requests_over_time_grouped, x='Timestamp', y='Number of Requests', title='Requests Over Time')
    plot2_html = pio.to_html(fig2, full_html=False)

    request_counts = db.session.query(
        LogEntry.request_path, db.func.count(LogEntry.request_path).label('Count')
    ).filter(LogEntry.response_code == 200).group_by(LogEntry.request_path).all()

    request_counts_df = pd.DataFrame(request_counts, columns=['Request Path', 'Count'])
    fig3 = go.Figure(
        data=[go.Bar(
            x=request_counts_df['Request Path'].apply(lambda x: x.split('/')[-2]),
            y=request_counts_df['Count'],
            marker=dict(color=request_counts_df['Count']),
            hovertext=request_counts_df['Request Path'],
            hoverinfo="text+y"
        )],
        layout=go.Layout(
            title="Number of Successful Requests for Different Paths/Resources",
            xaxis=dict(title='Request Path'),
            yaxis=dict(title='Count')
        )
    )
    plot3_html = pio.to_html(fig3, full_html=False)

    # Perform user agent analysis and create visualizations
    device_counts, browser_counts = user_agent_analysis()

    fig4 = px.bar(device_counts, x='Device', y='Count', title='Distribution of Devices')
    plot4_html = pio.to_html(fig4, full_html=False)

    # Query the status code counts from the database
    status_code_counts = db.session.query(
        LogEntry.response_code, db.func.count(LogEntry.response_code).label('Count')
    ).group_by(LogEntry.response_code).order_by(db.func.count(LogEntry.response_code).desc()).all()

    # Convert query results to a DataFrame
    status_code_df = pd.DataFrame(status_code_counts, columns=['Status Code', 'Count'])

    # Create a Plotly bar chart similar to the IP addresses example
    fig5 = px.bar(
        status_code_df, 
        x='Status Code', 
        y='Count', 
        title='Distribution of Status Codes',
        labels={'Status Code': 'Status Code', 'Count': 'Frequency'},
        color='Status Code',
        category_orders={'Status Code': status_code_df['Status Code'].unique()}
    )
    # Convert Plotly figure to HTML
    plot5_html = pio.to_html(fig5, full_html=False)


    return render_template('index.html', plot1=plot1_html, plot2=plot2_html, plot3=plot3_html, plot4=plot4_html, plot5=plot5_html)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    populate_db()

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
