# Build context is lab/. WITH_LLM_GUARD=false builds a light image (Presidio + regex only) for CI.
FROM python:3.12-slim
ARG WITH_LLM_GUARD=true
ARG SPACY_MODEL=en_core_web_lg
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/opt/hf LLM_GUARD_ENABLED=${WITH_LLM_GUARD} SPACY_MODEL=${SPACY_MODEL}
WORKDIR /app
COPY ai-gateway/requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && python -m spacy download ${SPACY_MODEL}
RUN if [ "$WITH_LLM_GUARD" = "true" ]; then \
      pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
   && pip install --no-cache-dir -r requirements-llmguard.txt ; fi
COPY apis/common/auth.py ai-gateway/guardrails.py ai-gateway/main.py ./
# Load every model once at build time so the container starts fast and needs no internet at runtime.
RUN python -c "import guardrails; guardrails.warm_up()"
RUN useradd --uid 10001 --no-create-home app && mkdir -p /var/log/ai /opt/hf && chown -R 10001 /var/log/ai /opt/hf
USER 10001
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
