import os
import pandas as pd
import matplotlib.pyplot as plt

def load_and_plot_combined_datasets(base_path, test_duration, min_time_diff, max_time_diff):
    first_run_path, second_run_path = os.path.join(base_path, 'initial'), os.path.join(base_path, 'scaled')
    threadpool_file, response_time_file, cpu_file = 'System_Runtime_ThreadPool_Queue_Length_export_mean_values.csv', 'Request_Duration_export_mean_values.csv', 'System_Runtime_CPU_Usage_export_mean_values.csv'
    fig, axs = plt.subplots(2, 1, figsize=(6.5, 5.5), dpi=400, sharex=True)
    
    def load_and_plot(ax, path, title):
        df_threadpool, df_response, df_cpu = pd.read_csv(os.path.join(path, threadpool_file)), pd.read_csv(os.path.join(path, response_time_file)), pd.read_csv(os.path.join(path, cpu_file))
        ax.plot(df_threadpool['timestamp'], df_threadpool['value'], label='Threadpool Queue Length', color='blue', marker='o', linestyle='-', linewidth=1.2, markersize=4)
        ax.plot(df_response['timestamp'], df_response['value'], label='Response Time (s)', color='red', marker='o', linestyle='-', linewidth=1.2, markersize=4)
        ax.plot(df_cpu['timestamp'], df_cpu['value'], label='Container CPU Usage (%)', color='orange', marker='o', linestyle='-', linewidth=1.2, markersize=4)
        ax.set_title(title, fontsize=12)
        ax.grid(True, linewidth=0.5, alpha=0.6)
        return df_response, df_threadpool
    
    load_and_plot(axs[0], first_run_path, 'Baseline Run')
    axs[0].legend(loc='upper left', fontsize=9, frameon=False)
    
    df_response_second, df_threadpool_second = load_and_plot(axs[1], second_run_path, 'Run with Scaling Mechanism')
    range_start_time, range_end_time = test_duration + min_time_diff, test_duration + max_time_diff
    axs[1].axvline(x=range_start_time, color='green', linestyle='--', linewidth=1)
    axs[1].axvline(x=range_end_time, color='green', linestyle='--', linewidth=1)
    axs[1].fill_betweenx(y=[0, max(df_response_second['value'].max(), df_threadpool_second['value'].max())], x1=range_start_time, x2=range_end_time, color='grey', alpha=0.3, label='Scaling Event Window')
    
    axs[-1].set_xlabel('Time (s)', fontsize=10)
    axs[1].legend(loc='upper left', fontsize=9, frameon=False)
    
    plt.tight_layout(pad=0.8)
    plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1)
    plt.savefig(os.path.join('../', 'issc_figures', 'Thread_Response_CPU.png'), bbox_inches='tight')
    plt.close()
    print(f"Combined plots saved to {os.path.join(base_path, 'issc_figures', 'Thread_Response_CPU.png')}")

if __name__ == "__main__":
    load_and_plot_combined_datasets('../../mean_datasets', 150, -126, -95)
