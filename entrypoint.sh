#!/bin/bash

STACK_NAME="threadpool"
CERT="<CERT>"
SSH_HOST="<SSH_HOST>"
MANAGER_IP="<MasterIP>"
SWARM_TOKEN="<swarm token>"

join_swarm() {
    ssh -i "$CERT" "$SSH_HOST" "docker swarm leave"
    ssh -i "$CERT" "$SSH_HOST" "docker swarm join --token $SWARM_TOKEN $MANAGER_IP:2377"
}

update_node_labels() {
    all_nodes=$(docker node ls --format '{{.ID}}')
    non_leader_nodes=$(echo "$all_nodes" | grep -v "$leader_node")
    for node in $non_leader_nodes; do
        docker node update --label-add role=worker $node
    done
    docker node update --label-add role=master $leader_node
}

deploy_and_cleanup() {
    echo "Deploying $STACK_NAME stack..."
    docker stack deploy -c docker-compose.yml $STACK_NAME

    # Remove the Docker service only in the first run
    if [[ $1 == "first" ]]; then
        echo "Removing threadpool_alertapi service..."
        docker service rm threadpool_alertapi
        sleep 15
    fi
    
    echo "Deployed $STACK_NAME stack"

    k6 run --env K6_PROMETHEUS_RW_SERVER_URL=http://<DNS_ADDED_TO_ROUTE53>:9090/api/v1/write --env K6_OUT=prometheus-rw --env K6_PROMETHEUS_RW_TREND_AS_NATIVE_HISTOGRAM=true -o experimental-prometheus-rw --tag testid=threadloadtest ./k6/k6_from_master.js

    echo "Running Python Export Script visualise.py"
    python3 exportmetrics.py
    echo "Sleep 2s."
    sleep 2
    echo "Export completed."

    docker stack rm $STACK_NAME
    echo "Stack Destroyed."
}

echo "Starting Baseline Run on a fresh stack."
leader_node=$(docker node ls --format '{{.ID}} {{.ManagerStatus}}' | grep "Leader" | awk '{print $1}')
update_node_labels
join_swarm
deploy_and_cleanup "first"

echo "Starting Run with Scaling Mechanism."
leader_node=$(docker node ls --format '{{.ID}} {{.ManagerStatus}}' | grep "Leader" | awk '{print $1}')
update_node_labels
join_swarm
deploy_and_cleanup "second"

