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
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt dependencies Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt Pillow

# Copy toàn bộ mã nguồn
COPY . .

# Tạo thư mục staticfiles nếu chưa tồn tại
RUN mkdir -p staticfiles

# In ra thông tin debug
RUN pwd
RUN ls -la
RUN python --version
RUN pip list

# Migrate database với verbose
RUN python manage.py migrate --verbosity 2

# Collectstatic
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Chạy ứng dụng
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "hospital.wsgi:application"]