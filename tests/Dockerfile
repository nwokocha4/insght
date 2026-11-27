FROM python:3.12-slim
WORKDIR /tests
COPY . /tests/
# Verifier needs torch CPU + timm (with baked resnet18 weights) plus pytest.
# Weights are fetched at build time into a world-readable cache so the graded
# run (which drops to an unprivileged uid) is offline and deterministic.
ENV HF_HOME=/opt/hf
RUN pip install --no-cache-dir \
    torch==2.15.0+cpu \
    torchvision==0.29.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir \
    timm==1.0.31 pillow==11.3.0 numpy==2.1.3 \
 && pip install --no-cache-dir -r /tests/requirements.txt \
 && python -c "import timm; timm.create_model('resnet18.a1_in1k', pretrained=True); print('weights baked')" \
 && chmod -R a+rX /opt/hf
ENV HF_HUB_OFFLINE=1
RUN mkdir -p /app && chmod -R go-rwx /tests
CMD ["sh", "/tests/test.sh"]
