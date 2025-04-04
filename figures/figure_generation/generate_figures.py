import os
import pandas as pd
import matplotlib.pyplot as plt

file_map = {
    'Busy_Worker_Threads_export_mean_values.csv': { 'title': 'Busy Worker Threads (100 Runs)', 'ylabel': 'Threads' },
    'Request_Duration_export_mean_values.csv': { 'title': 'Request Duration (100 Runs)', 'ylabel': 'Seconds' },
    'Process_Number_of_Threads_export_mean_values.csv': { 'title': 'Process Number of Threads (100 Runs)', 'ylabel': 'Threads' },
    'System_Runtime_CPU_Usage_export_mean_values.csv': { 'title': 'System Runtime CPU (100 Runs)', 'ylabel': 'CPU Usage (%)' },
    'Total_Requests_export_mean_values.csv': { 'title': 'Total Requests (100 Runs)', 'ylabel': 'Requests Count' },
    'Worker_Node_CPU_Metrics_Over_Time_export_mean_values.csv': { 'title': 'Worker Node CPU (100 Runs)', 'ylabel': 'CPU Usage (%)' },
    'System_Runtime_ThreadPool_Queue_Length_export_mean_values.csv': { 'title': 'Thread Pool Queue Length (100 Runs)', 'ylabel': 'Items on Queue' }
}

def load_and_plot_datasets(base_path, test_duration, min_time_diff, max_time_diff):
    initial_run_path = os.path.join(base_path, 'initial')
    second_run_path = os.path.join(base_path, 'scaled')

    if not os.path.exists(initial_run_path) or not os.path.exists(second_run_path):
        print("One or both of the specified directories do not exist.")
        return

    initial_files = os.listdir(initial_run_path)
    
    for file in initial_files:
        if file.endswith('.csv'):
            initial_file_path = os.path.join(initial_run_path, file)
            second_file_path = os.path.join(second_run_path, file)
            
            if os.path.exists(second_file_path):
                df_initial = pd.read_csv(initial_file_path)
                df_second = pd.read_csv(second_file_path)

                file_info = file_map.get(file, {'title': 'Unknown Dataset', 'ylabel': 'Value'})

                plt.figure(figsize=(10, 6))
                plt.plot(df_initial['timestamp'], df_initial['value'], label='Baseline Run', marker='o', linestyle='-', color='blue')
                plt.plot(df_second['timestamp'], df_second['value'], label='Run with Scaling Mechanism', marker='o', linestyle='-', color='red')

                # Highlight the range for the scaling event
                range_start_time = test_duration + min_time_diff
                range_end_time = test_duration + max_time_diff

                plt.axvline(x=range_start_time, color='green', linestyle='--')
                plt.axvline(x=range_end_time, color='green', linestyle='--')

                plt.axvspan(range_start_time, range_end_time, color='grey', alpha=0.2, label='Scaling Event Window')

                plt.title(file_info['title'])
                plt.xlabel('Time Since Start (seconds)')
                plt.ylabel(file_info['ylabel'])
                plt.legend()
                plt.grid(True)
                
                figure_filename = f'Overlay_{file_info["title"].replace(" ", "_")}_Comparison.png'
                figure_path = os.path.join('../', figure_filename)
                plt.savefig(figure_path)
                plt.close()
                print(f"Plot saved to {figure_path}")
            else:
                print(f"No corresponding file found for {file} in second run.")

if __name__ == "__main__":
    base_path = '../../mean_datasets'
    test_duration = 150
    min_time_diff = -126
    max_time_diff = -95
    load_and_plot_datasets(base_path, test_duration, min_time_diff, max_time_diff)