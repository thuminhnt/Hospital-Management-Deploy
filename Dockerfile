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
    && rm -rf /var/lib/apt/lists/*

# Cài đặt dependencies Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn
COPY . .

# Tạo thư mục staticfiles nếu chưa tồn tại
RUN mkdir -p staticfiles

# In ra nội dung thư mục để debug
RUN ls -la

# Kiểm tra file manage.py
RUN test -f manage.py

# Migrate database (bỏ qua lỗi)
RUN python manage.py migrate || true

# Collectstatic (bỏ qua lỗi)
RUN python manage.py collectstatic --clear --noinput || true

# Expose port
EXPOSE 8000

# Chạy ứng dụng
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "hospital.wsgi:application"]