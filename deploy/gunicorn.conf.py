# gunicorn configuration of the SQL judge (see deploy/lsql.service.example)
import os

# Local address where the reverse proxy forwards /sql/ (GUNICORN_BIND in the env file)
bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8000")

# Threads: a submission waits for Oracle (and DES) and keeps a thread busy, not a whole
# process, so the rest of the pages keep answering. Each process has its own Oracle pool of
# ORACLE_MAX_GESTOR_CONNECTIONS connections, so Oracle sees up to workers * that number.
worker_class = "gthread"
workers = 2
threads = 8

# A submission may wait for a free Oracle connection (ORACLE_GESTOR_POOL_TIMEOUT_MS) and then
# run several statements and the DES analysis (DES_TIMEOUT)
timeout = 120

# Logs to stdout/stderr: they end up in the systemd journal
accesslog = "-"
errorlog = "-"
capture_output = True
loglevel = "info"
