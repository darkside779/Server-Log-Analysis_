import pandas as pd

def performance_monitoring(file_path):
    df = pd.read_csv(file_path)
    
    # Example processing; adjust according to your needs
    summary = df.groupby('Request Path').size().reset_index(name='Number of Requests')
    
    return summary
