FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

<<<<<<< HEAD
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
=======
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
>>>>>>> 85f0827548ad523fd83f3215aa0c30a5cc1db382
