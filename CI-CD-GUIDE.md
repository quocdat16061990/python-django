# Hướng dẫn CI/CD cho dự án Django

## 1. CI/CD là gì?

- **CI (Continuous Integration — Tích hợp liên tục):** Mỗi lần push code lên GitHub, tự động chạy **kiểm tra** (lint + test) để đảm bảo code không bị lỗi.
- **CD (Continuous Deployment — Triển khai liên tục):** Nếu kiểm tra OK, tự động **deploy** lên VPS bằng Docker.

---

## 2. Sơ đồ luồng hoạt động

```
Git push (branch main)
       │
       ▼
┌──────────────────────┐
│   CI - KIỂM TRA      │
│                      │
│  ┌────────────────┐  │
│  │ flake8 (lint)   │──┼── Bắt lỗi coding convention
│  └────────────────┘  │
│  ┌────────────────┐  │
│  │ pytest (test)   │──┼── Kiểm tra chức năng
│  └────────────────┘  │
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     │           │
   FAIL        PASS
     │           │
     ▼           ▼
  Báo đỏ    ┌──────────────────────┐
  dừng lại  │  CD - TRIỂN KHAI    │
            │                      │
            │  SSH vào VPS         │
            │  git pull            │
            │  docker compose down │
            │  docker compose up   │
            │  docker image prune  │
            └──────────────────────┘
                   │
                   ▼
          Mở trình duyệt kiểm tra
          http://VPS_IP:8000
```

---

## 3. Các file quan trọng trong dự án

### a) Workflow CI/CD
**File:** `.github/workflows/ci-cd.yml`

Định nghĩa 2 job chạy tuần tự:
1. **test** — cài đặt Python, pip install, flake8, pytest
2. **deploy** — (chỉ khi test pass + push lên main) SSH vào VPS, git pull, rebuild Docker

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: flake8 . --count --statistics
      - run: python manage.py test tasks

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      - uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /root/python-django
            git pull origin main
            docker compose down
            docker compose up -d --build
            docker image prune -f
```

### b) GitHub Secrets
Vào GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret | Giá trị | Mô tả |
|--------|---------|-------|
| `VPS_HOST` | `76.13.18.183` | Địa chỉ IP VPS |
| `VPS_USER` | `root` | User SSH |
| `VPS_SSH_KEY` | (nội dung private key) | Key để SSH vào VPS |

**Cách tạo SSH key trên VPS:**
```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
cat ~/.ssh/id_ed25519   # copy nội dung này
```

### c) File cấu hình lint
**File:** `.flake8`

Bỏ qua các thư mục không cần kiểm tra:
```ini
[flake8]
max-line-length = 120
max-complexity = 10
exclude = .git, __pycache__, venv, migrations, *.pyc
```

### d) Dockerfile
**File:** `Dockerfile`

Build container cho Django app:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
```

### e) Docker Compose
**File:** `docker-compose.yml`

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
```

### f) File test
**File:** `tasks/tests.py`

Viết test cho model, view, API. Ví dụ:

```python
from django.test import TestCase, Client
from django.urls import reverse
from .models import Task

class TaskModelTest(TestCase):
    def test_task_creation(self):
        task = Task.objects.create(title="Test", priority="high")
        self.assertEqual(task.title, "Test")
        self.assertFalse(task.completed)

class TaskViewTest(TestCase):
    def test_index_view(self):
        c = Client()
        response = c.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
```

### g) Pre-commit hook (tự động test trước commit)
**File:** `.git/hooks/pre-commit`

Mỗi lần `git commit`, tự động chạy test:
```bash
#!/bin/sh
python manage.py test tasks
if [ $? -ne 0 ]; then
    exit 1
fi
```

---

## 4. Cấu hình VPS — Mở port & Firewall

### a) Port nào cần mở

| Port | Mục đích | Ghi chú |
|------|----------|---------|
| **22** | SSH | GitHub Actions deploy + anh SSH vào |
| **80** | HTTP | Nếu dùng Nginx reverse proxy |
| **443** | HTTPS | Nếu có SSL (sau này) |
| **8000** | Django app | Port mặc định của docker-compose |

### b) Mở port bằng lệnh (trên VPS)

```bash
# Kiểm tra trạng thái firewall
sudo ufw status

# Mở các port cần thiết
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000

# Bật firewall
sudo ufw --force enable

# Kiểm tra lại
sudo ufw status
```

Kết quả mong đợi:
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
8000/tcp                   ALLOW       Anywhere
22/tcp (v6)                ALLOW       Anywhere (v6)
80/tcp (v6)                ALLOW       Anywhere (v6)
443/tcp (v6)               ALLOW       Anywhere (v6)
8000/tcp (v6)              ALLOW       Anywhere (v6)
```

### c) Kiểm tra Docker container đã chạy chưa

```bash
docker ps
```

Kết quả mong đợi:
```
CONTAINER ID   IMAGE             COMMAND                  CREATED         STATUS         PORTS                                       NAMES
abc123xyz      python-django-web  "sh -c 'python mana…"   2 minutes ago   Up 2 minutes   0.0.0.0:8000->8000/tcp                      python-django-web-1
```

### d) Kiểm tra log nếu app không chạy

```bash
docker logs python-django-web-1 -f
```

### e) Nếu VPS của hãng cloud có firewall riêng
Vào web panel của nhà cung cấp VPS (Hostinger, Vultr, DigitalOcean,...):
- Tìm mục **Firewall** hoặc **Security Group**
- Thêm rules cho phép port **22**, **80**, **443**, **8000**

---

## 5. Tại sao phải có test?

**Không có test → không biết code có hỏng không.**

### Ví dụ thực tế:
1. Sửa một dòng trong view → vô tình làm hỏng URL
2. Nếu có test: CI sẽ **phát hiện ngay**, báo đỏ, **không deploy**
3. Nếu không có test: code vẫn deploy lên VPS → **người dùng báo lỗi**

### Nên test những gì?

| Loại | Kiểm tra | Ví dụ |
|------|----------|-------|
| Model | Tạo/sửa/xóa dữ liệu | `assertEqual(task.priority, "high")` |
| View | Status code, template | `assertContains(response, "DevOverflow")` |
| API | POST/GET response | `assertTrue(data["success"])` |
| Dashboard | Thống kê, biểu đồ | `assertContains(response, "Tổng số")` |

### Lợi ích:
1. **Phát hiện lỗi sớm** — trước khi deploy, không cần chờ user báo
2. **Tự động** — không cần nhớ "chạy test thủ công"
3. **Yên tâm sửa code** — test pass là biết chắc không hỏng gì
4. **Tiết kiệm thời gian** — CI chạy trên GitHub, không tốn máy local

---

## 6. Áp dụng cho dự án Django khác

Áp dụng cho **bất kỳ dự án Django nào**, chỉ cần:

### Bước 1: Copy workflow
Copy file `.github/workflows/ci-cd.yml` sang dự án mới.

### Bước 2: Copy cấu hình
Copy file `.flake8` và `.git/hooks/pre-commit` sang dự án mới.

### Bước 3: Sửa tên app trong workflow
Sửa `python manage.py test tasks` → `python manage.py test ten_app_cua_ban`

### Bước 4: Thêm GitHub Secrets
Vào GitHub repo mới → **Settings** → **Secrets and variables** → **Actions** → thêm 3 secrets:
- `VPS_HOST` — IP VPS
- `VPS_USER` — root
- `VPS_SSH_KEY` — private key

### Bước 5: Sửa đường dẫn deploy nếu cần
Trong `.github/workflows/ci-cd.yml`, sửa:
```yaml
script: |
  cd /root/python-django    # ← đổi thành thư mục chứa project trên VPS
  git pull origin main
  docker compose down
  docker compose up -d --build
```

### Bước 6: Viết test cho app mới
Tạo file `tests.py` trong app:
```python
from django.test import TestCase, Client
from django.urls import reverse

class MyTest(TestCase):
    def test_homepage(self):
        c = Client()
        response = c.get('/')
        self.assertEqual(response.status_code, 200)
```

---

## 7. Cách dùng Git hook (tự động test khi commit)

File `.git/hooks/pre-commit` đã được tạo sẵn. Khi chạy `git commit`, nó sẽ tự động:

1. Chạy `python manage.py test`
2. Nếu test **fail** → commit bị **chặn** (không được tạo commit)
3. Nếu test **pass** → commit thành công

### Cài đặt hook cho dự án khác:
```bash
cp .git/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## 8. Quy trình làm việc hàng ngày

```
1. Sửa code ở local (thêm tính năng, fix bug...)
       │
2. Chạy test local:
   python manage.py test
       │
3. Nếu fail → fix code, quay lại bước 2
       │
4. Nếu pass:
   git add .
   git commit -m "mô tả"
       │ (hook tự động chạy test lại)
5. git push
       │
6. GitHub Actions CI/CD tự động:
   - flake8 (lint) → nếu fail: dừng, báo đỏ
   - pytest (test) → nếu fail: dừng, báo đỏ
   - deploy (CD) → nếu pass hết: deploy lên VPS
       │
7. Mở trình duyệt kiểm tra kết quả
   http://VPS_IP:8000
```

**Lưu ý:** Anh chỉ cần code + test + push. **Không cần động vào file .yml** khi thêm tính năng mới.

---

## 9. Các lệnh thường dùng

| Mục đích | Lệnh |
|----------|------|
| Chạy test | `python manage.py test` |
| Chạy lint | `flake8 . --count --statistics` |
| Chạy server local | `python manage.py runserver` |
| Build Docker | `docker compose up -d --build` |
| Xem container | `docker ps` |
| Xem log Docker | `docker logs python-django-web-1 -f` |
| Kiểm tra firewall | `sudo ufw status` |
| Mở port | `sudo ufw allow 8000` |

---

## 10. Xử lý lỗi hay gặp

| Lỗi | Nguyên nhân | Cách fix |
|-----|------------|----------|
| `flake8 error` | Code sai format, import không dùng | Sửa theo lỗi báo |
| `test FAILED` | Code mới làm hỏng chức năng cũ | Sửa test hoặc fix code |
| `i/o timeout` | VPS không cho SSH vào port 22 | Mở port 22: `sudo ufw allow 22` |
| `unable to authenticate` | SSH key sai hoặc hết hạn | Tạo lại key, cập nhật GitHub secret |
| `No such file or directory` | Đường dẫn deploy sai | Sửa `cd /root/python-django` trong workflow |
| `docker: command not found` | VPS chưa cài Docker | `curl -fsSL https://get.docker.com \| sh` |
| `port already allocated` | Port 8000 đã có app chạy | `docker compose down` rồi chạy lại |
| `Connection refused` | App chưa chạy / sai port | Kiểm tra `docker ps` và `docker logs` |
| `ssh: connect to host port 22: No route to host` | VPS firewall chặn SSH | Vào web panel hãng cloud mở port 22 |

---

## 11. File tham khảo trong dự án này

| File | Vai trò |
|------|---------|
| `.github/workflows/ci-cd.yml` | Workflow GitHub Actions |
| `.flake8` | Cấu hình flake8 |
| `Dockerfile` | Build Docker image |
| `docker-compose.yml` | Docker Compose config |
| `requirements.txt` | Python dependencies |
| `tasks/tests.py` | Unit test |
| `CI-CD-GUIDE.md` | File này — tài liệu hướng dẫn |
