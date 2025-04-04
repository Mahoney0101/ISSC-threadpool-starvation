using System.Diagnostics.Tracing;
using MongoDB.Bson;
using MongoDB.Driver;
using Prometheus;
using System.Text;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient();
var app = builder.Build();

var mongoClient = new MongoClient("REMOVED");
var database = mongoClient.GetDatabase("ThreadPoolTestDb");
var collection = database.GetCollection<BsonDocument>("TestData");
var runtimeMetricsListener = new RuntimeMetricsListener();

var maxWorkerThreadsGauge = Metrics.CreateGauge("max_worker_threads", "Maximum number of worker threads");
var availableWorkerThreadsGauge = Metrics.CreateGauge("available_worker_threads", "Available worker threads");
var busyWorkerThreadsGauge = Metrics.CreateGauge("busy_worker_threads", "Busy worker threads");
var maxCompletionPortThreadsGauge = Metrics.CreateGauge("max_completion_port_threads", "Maximum number of completion port threads");
var availableCompletionPortThreadsGauge = Metrics.CreateGauge("available_completion_port_threads", "Available completion port threads");
var busyCompletionPortThreadsGauge = Metrics.CreateGauge("busy_completion_port_threads", "Busy completion port threads");
var processThreadCountGauge = Metrics.CreateGauge("process_number_of_threads", "Number of threads in the process");
// Expose metrics on /metrics endpoint
app.UseMetricServer();

// SUT endpoint
app.MapGet("/test-threadpool", async (IHttpClientFactory httpClientFactory) =>
{
    var task = Task.Run(() =>
    {
        Thread.Sleep(2000);
        return new BsonDocument
        {
            { "Timestamp", DateTime.UtcNow },
            { "Note", "Simulated long-running task" }
        };
    });

    task.Wait();

    var doc = task.Result;
    await collection.InsertOneAsync(doc);

    var metricsData = GetMetricData();
    var httpClient = httpClientFactory.CreateClient();
    var requestContent = new StringContent(metricsData, Encoding.UTF8, "text/plain");
    var pushgatewayUri = "http://threads.mahoney0101.com:9091/metrics/job/webserver/instance/webserver:5000";
    var response = await httpClient.PostAsync(pushgatewayUri, requestContent);

    if (!response.IsSuccessStatusCode)
    {
        var responseContent = await response.Content.ReadAsStringAsync();
        return Results.Problem($"Failed to push metrics to Pushgateway. Status code: {response.StatusCode}, Response: {responseContent}");
    }

    return Results.Ok();
});

//Run applictaion
app.Run();

string GetMetricData(){
    ThreadPool.GetMaxThreads(out int maxWorkerThreads, out int maxCompletionPortThreads);
    ThreadPool.GetAvailableThreads(out int availableWorkerThreads, out int availableCompletionPortThreads);

    int busyWorkerThreads = maxWorkerThreads - availableWorkerThreads;
    int busyCompletionPortThreads = maxCompletionPortThreads - availableCompletionPortThreads;

    maxWorkerThreadsGauge.Set(maxWorkerThreads);
    availableWorkerThreadsGauge.Set(availableWorkerThreads);
    busyWorkerThreadsGauge.Set(busyWorkerThreads);
    maxCompletionPortThreadsGauge.Set(maxCompletionPortThreads);
    availableCompletionPortThreadsGauge.Set(availableCompletionPortThreads);
    busyCompletionPortThreadsGauge.Set(busyCompletionPortThreads);

    // Manually build custom metrics to push
    var stringBuilder = new StringBuilder();
    stringBuilder.AppendLine($"# HELP max_worker_threads Maximum number of worker threads");
    stringBuilder.AppendLine($"# TYPE max_worker_threads gauge");
    stringBuilder.AppendLine($"max_worker_threads {maxWorkerThreads}");
    stringBuilder.AppendLine($"# HELP available_worker_threads Available worker threads");
    stringBuilder.AppendLine($"# TYPE available_worker_threads gauge");
    stringBuilder.AppendLine($"available_worker_threads {availableWorkerThreads}");

    stringBuilder.AppendLine($"# HELP busy_worker_threads ");
    stringBuilder.AppendLine($"# TYPE busy_worker_threads gauge");
    stringBuilder.AppendLine($"busy_worker_threads {busyWorkerThreads}");
    stringBuilder.AppendLine($"# HELP max_completion_port_threads Available worker threads");
    stringBuilder.AppendLine($"# TYPE max_completion_port_threads gauge");
    stringBuilder.AppendLine($"max_completion_port_threads {maxCompletionPortThreads}");

    stringBuilder.AppendLine($"# HELP available_completion_port_threads Maximum number of worker threads");
    stringBuilder.AppendLine($"# TYPE available_completion_port_threads gauge");
    stringBuilder.AppendLine($"available_completion_port_threads {availableCompletionPortThreads}");
    stringBuilder.AppendLine($"# HELP busy_completion_port_threads Available worker threads");
    stringBuilder.AppendLine($"# TYPE busy_completion_port_threads gauge");
    stringBuilder.AppendLine($"busy_completion_port_threads {busyCompletionPortThreads}");
    stringBuilder.AppendLine($"# HELP system_runtime_threadpool_queue_length The length of the thread pool queue.");
    stringBuilder.AppendLine($"# TYPE system_runtime_threadpool_queue_length gauge");
    stringBuilder.AppendLine($"system_runtime_threadpool_queue_length {runtimeMetricsListener.ThreadPoolQueueLength}");
// Add CPU usage metric to the manual metrics string
    stringBuilder.AppendLine($"# HELP system_runtime_cpu_usage CPU usage");
    stringBuilder.AppendLine($"# TYPE system_runtime_cpu_usage gauge");
    stringBuilder.AppendLine($"system_runtime_cpu_usage {runtimeMetricsListener.CpuUsage}");
//   
    stringBuilder.AppendLine($"# HELP process_number_of_threads Total number of threads in the process");
    stringBuilder.AppendLine($"# TYPE process_number_of_threads gauge");
    stringBuilder.AppendLine($"process_number_of_threads {runtimeMetricsListener.ProcessNumberOfThreads}");

    return stringBuilder.ToString();
}

public class RuntimeMetricsListener : EventListener
{
    public int ThreadPoolQueueLength { get; private set; } = -1;
    public int ProcessNumberOfThreads { get; private set; } = -1;
    public double CpuUsage { get; private set; } = -1;

    protected override void OnEventSourceCreated(EventSource eventSource)
    {
        if (eventSource.Name.Equals("System.Runtime"))
        {
            EnableEvents(eventSource, EventLevel.LogAlways, EventKeywords.All, new Dictionary<string, string>()
            {
                {"EventCounterIntervalSec", "1"}
            });
        }
    }

    protected override void OnEventWritten(EventWrittenEventArgs eventData)
    {
        if (eventData.EventName.Equals("EventCounters"))
        {
            foreach (var payload in eventData.Payload)
            {
                if (payload is IDictionary<string, object> eventPayload)
                {
                    switch (eventPayload["Name"])
                    {
                        case "threadpool-queue-length":
                            ThreadPoolQueueLength = Convert.ToInt32(eventPayload["Mean"]);
                            break;
                        case "process-number-of-threads":
                            ProcessNumberOfThreads = Convert.ToInt32(eventPayload["Mean"]);
                            break;
                        case "cpu-usage":
                            CpuUsage = Convert.ToDouble(eventPayload["Mean"]);
                            break;
                    }
                }
            }
        }
    }
}
