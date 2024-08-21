import pandas as pd
import plotly.express as px

def path_analysis(file_dir: str) -> None:
    """
    Analyze server logs and display a bar chart of request paths.

    Args:
        file_dir (str): The directory of the server log file.
    """
    try:
        # Read the data from the CSV file
        df = pd.read_csv(file_dir)
        print("File read successfully")
    except FileNotFoundError:
        print(f"Error: File not found at {file_dir}")
        return
    except pd.errors.EmptyDataError:
        print(f"Error: File at {file_dir} is empty")
        return
    except pd.errors.ParserError as e:
        print(f"Error: Unable to parse file at {file_dir}: {e}")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    try:
        # Extract request paths
        request_paths = df['Request Path']

        # Count the occurrences of each request path
        path_counts = request_paths.value_counts()

        # Create a DataFrame for paths and their counts
        path_df = pd.DataFrame({'Path': path_counts.index, 'Count': path_counts.values})

        # Plot the distribution of request paths using Plotly
        fig = px.bar(path_df, x='Path', y='Count', title='Distribution of Request Paths')
        fig.update_layout(xaxis_title='Path Reference Number', yaxis_title='Number of Requests')

        # Show the plot
        fig.show()
    except Exception as e:
        print(f"Error generating plot: {e}")

def main() -> None:
    """
    Main entry point of the script.
    """
    path_analysis('data/csv/server_logs.csv')

if __name__ == "__main__":
    main()