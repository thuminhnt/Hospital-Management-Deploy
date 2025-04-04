# Sử dụng Python official image
FROM python:3.9-slim

# Thiết lập môi trường
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Tạo và chuyển đến thư mục làm việc
WORKDIR /app

# Cài đặt dependencies hệ thống
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt dependencies Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn
COPY . .

# Collectstatic
RUN python manage.py collectstatic --noinput

# Migrate database
RUN python manage.py migrate

# Expose port
EXPOSE 8000

# Chạy ứng dụng
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "hospital.wsgi:application"]