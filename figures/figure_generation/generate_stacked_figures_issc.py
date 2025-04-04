import os
import pandas as pd
import matplotlib.pyplot as plt

file_map = {
    'Busy_Worker_Threads_export_mean_values.csv': {'title': 'Busy Worker Threads', 'ylabel': 'Threads'},
    'p99_Request_Duration_export_mean_values.csv': {'title': 'Request Duration', 'ylabel': 'Seconds'},
    'Process_Number_of_Threads_export_mean_values.csv': {'title': 'Process Threads', 'ylabel': 'Threads'},
    'System_Runtime_CPU_Usage_export_mean_values.csv': {'title': 'System CPU Usage', 'ylabel': 'CPU Usage (%)'},
    'Worker_Node_CPU_Metrics_Over_Time_export_mean_values.csv': {'title': 'Worker Node CPU', 'ylabel': 'CPU Usage (%)'},
    'System_Runtime_ThreadPool_Queue_Length_export_mean_values.csv': {'title': 'Thread Pool Queue', 'ylabel': 'Items'}
}

def load_and_plot_datasets(base_path, test_duration, min_time_diff, max_time_diff):
    initial_run_path = os.path.join(base_path, 'initial')
    second_run_path = os.path.join(base_path, 'scaled')

    if not os.path.exists(initial_run_path) or not os.path.exists(second_run_path):
        print("One or both of the specified directories do not exist.")
        return

    initial_files = [file for file in os.listdir(initial_run_path) if file.endswith('.csv') and file in file_map]

    fig, axes = plt.subplots(nrows=len(initial_files), figsize=(3.5, len(initial_files) * 1.2), dpi=400, sharex=True)

    if len(initial_files) == 1:
        axes = [axes]

    for ax, file in zip(axes, initial_files):
        initial_file_path = os.path.join(initial_run_path, file)
        second_file_path = os.path.join(second_run_path, file)

        if os.path.exists(second_file_path):
            df_initial = pd.read_csv(initial_file_path)
            df_second = pd.read_csv(second_file_path)
            file_info = file_map.get(file, {'title': 'Unknown Dataset', 'ylabel': 'Value'})

            ax.plot(df_initial['timestamp'], df_initial['value'], label='Baseline', 
                    marker='o', linestyle='-', color='blue', linewidth=0.9, markersize=2.5)
            ax.plot(df_second['timestamp'], df_second['value'], label='Scaled Run', 
                    marker='s', linestyle='-', color='red', linewidth=0.9, markersize=2.5)

            range_start_time = test_duration + min_time_diff
            range_end_time = test_duration + max_time_diff
            ax.axvline(x=range_start_time, color='green', linestyle='--', linewidth=0.7)
            ax.axvline(x=range_end_time, color='green', linestyle='--', linewidth=0.7)
            ax.axvspan(range_start_time, range_end_time, color='grey', alpha=0.2, label='Scaling Event')

            ax.set_title(file_info['title'], fontsize=7, pad=1)
            ax.set_ylabel(file_info['ylabel'], fontsize=7)
            ax.grid(True, linewidth=0.4, alpha=0.6)
            ax.margins(x=0, y=0.02)

            if ax == axes[-1]:
                ax.set_xlabel("Time (s)", fontsize=7)
            else:
                ax.set_xticklabels([])

            ax.legend(fontsize=6, loc='upper right', frameon=False)

    plt.subplots_adjust(hspace=0.2)
    plt.tight_layout(pad=0.5)

    figure_path = os.path.join('../', "issc_figures", "Stacked_Figures.png")
    plt.savefig(figure_path, bbox_inches='tight', dpi=400)
    plt.close()
    print(f"Stacked plot saved to {figure_path}")

if __name__ == "__main__":
    base_path = '../../mean_datasets'
    test_duration = 150
    min_time_diff = -126
    max_time_diff = -95
    load_and_plot_datasets(base_path, test_duration, min_time_diff, max_time_diff)
