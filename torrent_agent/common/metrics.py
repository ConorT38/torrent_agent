from prometheus_client import start_http_server, Counter, Histogram

class MetricEmitter:
    """
    This class is responsible for defining and managing Prometheus metrics.
    It includes counters and histograms for various events and durations.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Ensure only one instance of the class is created.
        """
        if cls._instance is None:
            cls._instance = super(MetricEmitter, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """
        Initialize the metrics.
        """
        if not hasattr(self, '_initialized'):  # Prevent reinitialization
            self._initialized = True
            self.files_processed = Counter('files_processed_total', 'Total number of files processed')
            self.db_inserts = Counter('db_inserts_total', 'Total number of database inserts')
            self.file_conversion_duration = Histogram('file_conversion_duration_seconds', 'Duration of file conversions in seconds')
            self.db_connection_failures = Counter('db_connection_failures_total', 'Total number of database connection failures')
            self.files_converted = Counter('files_converted_total', 'Total number of files converted')
            self.agent_runs_cycles = Counter('agent_run_cycles', 'Total number of run cycles the agent performed')
            self.agent_runs_cycles_failed = Counter('agent_run_cycles_failed', 'Total number of run cycles the agent performed that failed')
            self.agent_runs_cycles_duration = Histogram('agent_run_cycles_duration_seconds', 'Duration of agent run cycles in seconds')
            start_http_server(8002)  # Start the Prometheus HTTP server on port 8002