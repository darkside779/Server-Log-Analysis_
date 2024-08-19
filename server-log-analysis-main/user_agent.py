import pandas as pd
import matplotlib.pyplot as plt
from user_agent import parse
from utils import SetEnv

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
    devices = [ua.device.family for ua in parsed_user_agents]
    browsers = [ua.browser.family for ua in parsed_user_agents]

    # Count the occurrences of each device and browser
    device_counts = pd.Series(devices).value_counts()
    browser_counts = pd.Series(browsers).value_counts()

    # Plot the distribution of devices
    plt.figure(figsize=(12, 6))
    device_counts.plot(kind='bar', color='skyblue')
    plt.title('Distribution of Devices')
    plt.xlabel('Device')
    plt.ylabel('Number of Requests')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y')
    plt.tight_layout()
    plt.show()

def main():
    user_agent_analysis('data/csv/server_logs.csv')

if __name__ == "__main__":
    main()
