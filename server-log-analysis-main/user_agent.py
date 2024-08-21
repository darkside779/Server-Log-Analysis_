import pandas as pd
import plotly.express as px
from ua_parser import user_agent_parser
from utils import SetEnv


def parse(ua_string):
    return user_agent_parser.Parse(ua_string)


def user_agent_analysis(file_dir):
    # Set Working path
    _env = SetEnv.set_path()
    # Read the data from the CSV file
    df = pd.read_csv(f'{_env}/{file_dir}')

    # Convert the Timestamp column to datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d/%b/%Y:%H:%M:%S %z')

    # Extract User Agents
    user_agents = df['User Agent']

    # Parse each user agent string and extract device and browser information
    parsed_user_agents = [parse(ua) for ua in user_agents if pd.notnull(ua)]
    devices = [ua.get('device', {}).get('family') for ua in parsed_user_agents]
    browsers = [ua.get('user_agent', {}).get('family') for ua in parsed_user_agents]

    # Count the occurrences of each device and browser
    device_counts = pd.Series(devices).value_counts().reset_index(name='Count')
    device_counts.columns = ['Device', 'Count']

    browser_counts = pd.Series(browsers).value_counts().reset_index(name='Count')
    browser_counts.columns = ['Browser', 'Count']

    # Plot the distribution of devices
    fig = px.bar(device_counts, x='Device', y='Count', title='Distribution of Devices')
    fig.show()

    # Plot the distribution of browsers
    fig = px.bar(browser_counts, x='Browser', y='Count', title='Distribution of Browsers')
    fig.show()


def main():
    user_agent_analysis('data/csv/server_logs.csv')


if __name__ == "__main__":
    main()