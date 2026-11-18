FROM python:3.11-slim
WORKDIR /edge
RUN pip install --no-cache-dir redis numpy
COPY detector /edge/detector
CMD ["python", "-m", "detector.publisher", "--source", "synthetic", "--camera-id", "cam-01"]
