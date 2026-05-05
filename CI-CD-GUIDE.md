# Hướng dẫn CI/CD cho dự án Django

## 1. CI/CD là gì?

- **CI (Continuous Integration — Tích hợp liên tục):** Mỗi lần bạn push code lên GitHub, nó tự động chạy **kiểm tra** (lint + test) để đảm bảo code không bị lỗi.
- **CD (Continuous Deployment — Triển khai liên tục):** Nếu kiểm tra OK, nó tự động **deploy** lên VPS.

---

## 2. Luồng hoạt động

```
Bạn push code lên GitHub (branch main)
        │
        ▼
┌─────────────────────────────┐
│       CI — KIỂM TRA         │
│ 1. Install dependencies     │
│ 2. Chạy flake8 (lint)       │
│ 3. Chạy pytest (unit test)  │
└──────────────┬──────────────┘
        │
        ▼ Nếu fail → dừng lại, báo đỏ
        │
        ▼ Nếu pass
┌─────────────────────────────┐
│       CD — TRIỂN KHAI       │
│ SSH vào VPS                 │
│ git pull                    │
│ docker compose up -d --build│
└─────────────────────────────┘
```

## 3. Các thành phần

### a) Workflow file
File: `.github/workflows/ci-cd.yml` — định nghĩa các bước CI/CD.

### b) GitHub Secrets
Vào GitHub repo → Settings → Secrets and variables → Actions, tạo:

| Secret | Giá trị |
|--------|---------|
| `VPS_HOST` | IP VPS |
| `VPS_USER` | root |
| `VPS_SSH_KEY` | Nội dung private key |

### c) File cấu hình lint
File: `.flake8` — bỏ qua thư mục không cần kiểm tra (venv, migrations, ...)

### d) File test
File: `tasks/tests.py` — viết test cho các chức năng.

---

## 4. Tại sao phải có test?

**Không có test → không biết code có hỏng không.**

Ví dụ: Sửa view nhưng vô tình làm hỏng URL → deploy lên VPS, người dùng vào báo lỗi. Với CI/CD, test sẽ phát hiện ngay trước khi deploy.

### Nên test những gì?

- Model: tạo, sửa, xóa dữ liệu có đúng không
- View: request có trả về đúng status code, đúng template không
- API: gửi dữ liệu lên có nhận đúng response không

### Lợi ích cụ thể:

1. **Phát hiện lỗi sớm** — trước khi deploy, không phải chờ user báo
2. **Tự động** — không cần nhớ "chạy test thủ công"
3. **Yên tâm sửa code** — test pass là biết chắc không hỏng gì
4. **Tiết kiệm thời gian** — CI chạy trên GitHub, không tốn máy local

---

## 5. Lỡ dự án khác thì sao? Áp dụng thế nào?

Áp dụng cho **bất kỳ dự án Django nào**, chỉ cần:

### Bước 1: Copy workflow
Copy file `.github/workflows/ci-cd.yml` sang dự án mới.

### Bước 2: Copy .flake8
Copy file `.flake8` sang thư mục gốc dự án mới.

### Bước 3: Chỉnh tên app trong test
Sửa `python manage.py test tasks` → `python manage.py test ten_app_cua_ban`

### Bước 4: Thêm GitHub Secrets
Vào GitHub repo mới → Settings → Secrets → thêm 3 secrets như trên.

### Bước 5: Viết test cho app của bạn
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

## 6. Mẹo

- **Lint local:** Chạy `flake8` trước khi commit để khỏi fail CI
- **Test local:** Chạy `python manage.py test` trước khi commit
- **Pre-commit hook (tự động test trước commit):** file `.git/hooks/pre-commit` đã được tạo

---

## 7. Xử lý lỗi hay gặp

| Lỗi | Nguyên nhân | Cách fix |
|-----|------------|----------|
| `flake8 error` | Code sai format hoặc import không dùng | Sửa theo lỗi báo |
| `test FAILED` | Code mới làm hỏng chức năng cũ | Sửa test hoặc fix code |
| `i/o timeout` | VPS không cho SSH vào | Kiểm tra firewall VPS (port 22) |
| `unable to authenticate` | SSH key sai | Cập nhật lại GitHub secret `VPS_SSH_KEY` |
