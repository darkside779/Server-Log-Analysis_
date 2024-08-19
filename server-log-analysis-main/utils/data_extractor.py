import pandas as pd
import re
import os
import SetEnv
import logging

# Set up logging
logging.basicConfig(filename='error.log', level=logging.ERROR)

# Set the current directory
try:
    parent_dir = SetEnv.set_path()
except Exception as e:
    logging.error(f"Error setting parent directory: {e}")
    exit(1)

# Specify the path to the log file relative to the parent directory
log_file_path = os.path.join(parent_dir, 'data/raw/server_logs.txt')

# Read the log file
try:
    with open(log_file_path, 'r') as file:
        logs = file.readlines()
except FileNotFoundError:
    logging.error(f"Log file not found: {log_file_path}")
    exit(1)
except Exception as e:
    logging.error(f"Error reading log file: {e}")
    exit(1)

# Initialize lists to store parsed data
ip_addresses = []
timestamps = []
request_methods = []
request_paths = []
status_codes = []
user_agents = []

# Regular expression pattern to match the log format
pattern = r'(?P<ip>[\d\.]+) - - \[(?P<timestamp>.*?)\] "(?P<method>.*?) (?P<path>.*?) .*?" (?P<status>\d+) .*?"(' \
          r'?P<user_agent>.*?)" '

# Iterate over each log entry and extract information
for log in logs:
    try:
        match = re.match(pattern, log)
        if match:
            ip_addresses.append(match.group('ip'))
            timestamps.append(match.group('timestamp'))
            request_methods.append(match.group('method'))
            request_paths.append(match.group('path'))
            status_codes.append(match.group('status'))
            user_agents.append(match.group('user_agent'))
    except re.error:
        logging.error("Regular expression error")
    except Exception as e:
        logging.error(f"Error parsing log entry: {e}")

# Create a DataFrame
try:
    data = {
        'IP Address': ip_addresses,
        'Timestamp': timestamps,
        'Request Method': request_methods,
        'Request Path': request_paths,
        'Status Code': status_codes,
        'User Agent': user_agents
    }
    df = pd.DataFrame(data)
except Exception as e:
    logging.error(f"Error creating DataFrame: {e}")
    exit(1)

# Specify the path to save the CSV file relative to the parent directory
data_dir = os.path.join(parent_dir, 'data/csv')
csv_file = os.path.join(data_dir, 'server_logs.csv')

# Save the DataFrame to a CSV file
try:
    df.to_csv(csv_file, index=False)
except Exception as e:
    logging.error(f"Error saving CSV file: {e}")
    exit(1)

# Display the CSV file contents
try:
    with open(csv_file,  'r') as file:
        csv_contents = file.read()
    print(csv_contents)
except Exception as e:
    logging.error(f"Error reading CSV file: {e}")