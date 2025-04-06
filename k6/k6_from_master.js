import http from 'k6/http';
import { check } from 'k6';

export let options = {
    scenarios: {
        ramp_up: {
            executor: 'ramping-arrival-rate',
            exec: 'ramp_up',
            startRate: 1,
            timeUnit: '1s',
            preAllocatedVUs: 50,
            maxVUs: 1000,
            stages: [
                { target: 15, duration: '30s' },
                { target: 20, duration: '30s' },
                { target: 30, duration: '30s' },
                { target: 35, duration: '30s' },
                { target: 5, duration: '30s' }
            ],
        }
    },
};

export function ramp_up() {
    let responses = http.get('http://<worker_node_address>:5000/test-threadpool');
    check(responses, {
        'Request to /test-threadpool succeeded': (res) => res.status === 200
    });
}

export default { ramp_up };
