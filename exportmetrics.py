import os
import requests
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.dates import DateFormatter

end_time = datetime.utcnow()
start_time = end_time - timedelta(minutes=5)

folder_name = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
export_folder = os.path.join("metric_exports", folder_name)
os.makedirs(export_folder, exist_ok=True)

def fetch_and_save_prometheus_data(metric_query, readable_name):
    prometheus_url = "http://<DNS_ADDED_TO_ROUTE53>:9090/api/v1/query_range"

    params = {
        'query': metric_query,
        'start': start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'end': end_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'step': '5s'
    }

    response = requests.get(prometheus_url, params=params)
    if response.status_code == 200:
        print(f"Successfully fetched the metrics for {readable_name}")
        data = response.json()
        
        # Conditionally save the data if it's not the 'Scale event' or if it is and has content
        if readable_name != "Scale event" or (readable_name == "Scale event" and data['data']['result']):
            file_path = os.path.join(export_folder, f"{readable_name.replace(' ', '_')}_export.json")
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=6)
            print(f"Data written to {file_path}")
        else:
            print(f"Scale event data is empty, not saved.")

        return data
    else:
        print(f"Failed to fetch metrics for {readable_name}, status code: {response.status_code}")
        return None

metrics_map = {
    "sum by(testid) (k6_http_reqs_total{testid=~'threadloadtest'})":"Total Requests",
    "sum by(testid) (k6_http_reqs_total{testid=~'threadloadtest', expected_response='false'})":"Failed Requests",
    "sum by(testid) (k6_http_reqs_total{testid=~'threadloadtest', expected_response='true'})":"Successful Requests",
    "process_num_threads": "Process Number of Threads",
    "system_runtime_cpu_usage": "System Runtime CPU Usage",
    "busy_worker_threads": "Busy Worker Threads",
    "system_runtime_threadpool_queue_length": "System Runtime ThreadPool Queue Length",
    "100 * sum(irate(node_cpu_seconds_total{instance='node-exporter:9100',job='node',mode='user'}[15s])) / scalar(count(count(node_cpu_seconds_total{instance='node-exporter:9100',job='node'}) by (cpu)))": "VM CPU Metrics Over Time",
    "histogram_quantile(0.99, sum by(testid) (rate(k6_http_req_duration_seconds{testid=~'threadloadtest'}[15s])))": "Request Duration",
    "(histogram_sum(rate(k6_http_req_duration_seconds{testid=~'threadloadtest'}[15s]))/histogram_count(rate(k6_http_req_duration_seconds{testid=~'threadloadtest'}[15s]))) ": "Average HTTP Request Duration",
    "alert_endpoint_call": "Scale event",
    "(histogram_sum(rate(k6_http_req_duration_seconds{testid=~'threadloadtest'}[10s])))": "Request Duration"
    }

for metric_query, readable_name in metrics_map.items():
    data = fetch_and_save_prometheus_data(metric_query, readable_name)
