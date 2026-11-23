import os

# Server socket
# Render injects PORT (default 10000). Local/container defaults to 5000.
port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"

# Worker processes (PR-07 Remediation)
# Sized dynamically to prevent micro-pool thread starvation and orchestrator healthcheck timeouts.
# Defaults: 2 workers x 4 threads = 8 concurrent request slots minimum.
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
worker_class = "gthread"

# Timeouts (PR-07 Remediation)
# Set timeout = 60s and keepalive = 5s to release saturated threads and clean up zombie workers cleanly.
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))

# Logging
loglevel = os.environ.get("LOG_LEVEL", "info")
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)ss'

# Process management
preload_app = False  # Avoid TensorFlow fork safety issues by loading model per worker

# Server & Worker Lifecycle Hooks for robust error handling and timeout logging
def on_starting(server):
    """Log server initialization details and concurrency capacity."""
    server.log.info(
        f"Gunicorn starting: workers={workers}, threads={threads} "
        f"(total capacity={workers * threads} concurrent threads), "
        f"timeout={timeout}s, keepalive={keepalive}s"
    )

def worker_abort(worker):
    """Handle worker timeout/abort cleanly with clear diagnostic logging."""
    worker.log.warning(
        f"Worker PID {worker.pid} received abort signal (SIGABRT/timeout exceeded {timeout}s). "
        "Terminating worker cleanly to prevent zombie request hanging."
    )

def worker_int(worker):
    """Handle graceful worker termination on INT/QUIT signal."""
    worker.log.info(f"Worker PID {worker.pid} received interrupt signal; terminating gracefully.")
