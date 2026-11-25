FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir \
    torch==2.15.0+cpu \
    torchvision==0.29.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir timm==1.0.31 pillow==11.3.0 numpy
# Bake resnet18 weights into a world-readable cache so runs are offline,
# deterministic, and usable by any uid the harness runs the program as.
ENV HF_HOME=/opt/hf
RUN python -c "import timm; timm.create_model('resnet18.a1_in1k', pretrained=True); print('weights baked')" \
 && chmod -R a+rX /opt/hf
ENV HF_HUB_OFFLINE=1
COPY data /app/data
RUN mkdir -p /app/output
# The agent writes /app/solve.py at run time, so the image must not exec it on
# start: keep the container alive and let the harness exec into it.
CMD ["sleep", "infinity"]
