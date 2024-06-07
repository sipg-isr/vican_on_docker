FROM python:3.12.3

RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx

WORKDIR /vican

ADD src /vican/src
ADD requirements.txt /vican

RUN pip install -r requirements.txt && \
    rm requirements.txt

CMD ["python", "src/main.py"]
