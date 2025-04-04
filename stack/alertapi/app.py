from flask import Flask, jsonify, request
import subprocess
import requests

app = Flask(__name__)

def get_current_replicas(service_name):
    """Retrieve the current number of replicas of the Docker service."""
    inspect_result = subprocess.run(
        ["docker", "service", "inspect", service_name, "--format", "{{.Spec.Mode.Replicated.Replicas}}"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return int(inspect_result.stdout.strip())

def scale_service(service_name, new_replicas):
    """Scale the Docker service to the new number of replicas."""
    subprocess.run(
        ["docker", "service", "scale", f"{service_name}={new_replicas}"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def send_metric_to_pushgateway(uri, metric_name, metric_value):
    """Send metric to the Pushgateway."""
    metrics_data = f"""
    # HELP {metric_name} Indicates a call to the alert endpoint
    # TYPE {metric_name} counter
    {metric_name} {metric_value}
    """
    requests.post(uri, data=metrics_data, headers={"Content-Type": "text/plain"})

@app.route('/alert', methods=['POST'])
def handle_alert():
    service_name = 'threadpool_webserver'
    try:
        current_replicas = get_current_replicas(service_name)
        new_replicas = current_replicas + 1
        scale_service(service_name, new_replicas)
        
        pushgateway_uri = "http://<DNS_ADDED_TO_ROUTE53>:9091/metrics/job/alertapi/instance/alertapi:5001"
        send_metric_to_pushgateway(pushgateway_uri, "alert_endpoint_call", 1)

        return jsonify({"message": f"Service {service_name} scaled successfully to {new_replicas} replicas."}), 200
    except subprocess.CalledProcessError as e:
        error_message = e.stderr if e.stderr else 'Failed to execute Docker command.'
        return jsonify({"error": "Failed to scale service.", "details": error_message}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
