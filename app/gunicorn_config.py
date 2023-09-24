import os

bind = f"0.0.0.0:{os.environ['PORT']}"
workers = 3
timeout = 120