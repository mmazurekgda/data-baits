FROM python:3.12
WORKDIR /code
COPY ./requirements.in /code/requirements.in
COPY ./setup.py /code/setup.py
COPY ./data_baits /code/data_baits
COPY ./examples /code/examples
RUN pip install --no-cache-dir --upgrade /code
CMD ["python", "-m", "data_baits"]
