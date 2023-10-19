FROM python:3.11
WORKDIR /app
COPY app/requirements-lock.txt /app/
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt
COPY app /app
RUN chmod +x /app/entrypoint.sh
ARG PORT=8000
ENV PORT=$PORT

EXPOSE $PORT
ENTRYPOINT ["/app/entrypoint.sh"]