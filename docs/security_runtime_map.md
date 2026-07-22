# Security Runtime Map (docs/security_runtime_map.md)

Tài liệu ánh xạ và phân tích hiện trạng bảo mật (Authentication, Authorization, Rate Limiter, Secrets) của hệ thống sau khi chuyển đổi serving sang Go và Rust.

---

## 1. Hiện trạng imports của `src/security`

Qua rà soát toàn bộ codebase, dưới đây là chi tiết các import của các module trong thư mục `src/security`:

| Module Python | Vị trí import | Mục đích sử dụng | Đánh giá hiện trạng |
| :--- | :--- | :--- | :--- |
| `src/security/secret_provider.py` | `src/observability/structured_logging.py`<br>`src/streaming/kafka_producer.py` | Lấy các cấu hình bí mật từ environment variables hoặc Docker secrets. | **ĐANG SỬ DỤNG** (Phục vụ logging & streaming). Giữ lại, không được xóa. |
| `src/security/authentication.py` | `tests/unit/test_security_modules.py` | Xác thực token, hash password. | **DEAD CODE** ở runtime (chỉ còn test sử dụng). Sẽ xóa sau khi chuyển giao hoàn toàn. |
| `src/security/authorization.py` | `tests/unit/test_security_modules.py` | Phân quyền RBAC. | **DEAD CODE** ở runtime. Sẽ xóa sau khi chuyển giao hoàn toàn. |
| `src/security/rate_limiter.py` | `tests/unit/test_security_modules.py` | Rate limiter dựa trên sliding window. | **DEAD CODE** ở runtime. Sẽ xóa sau khi chuyển giao hoàn toàn. |

---

## 2. Điểm kiểm tra (Endpoints sử dụng Auth)

Trước đây, khi còn sử dụng FastAPI API layer trong Python, các endpoint sau sử dụng authentication:
- `/v1/predictions` (Yêu cầu scope `prediction:execute`)
- `/v1/traffic/live` (Yêu cầu scope `traffic:read`)
- `/v1/model` (Yêu cầu scope `model:read`)
- `/v1/model/reload` (Yêu cầu scope `model:reload` hoặc `admin`)

Hiện tại:
- Các endpoint này đã chuyển dịch hoàn toàn sang **Rust Inference API** (Port 8090) và **Go Live Traffic API** (Port 8084).
- Các API Gateway (Nginx) định tuyến trực tiếp đến hai service này mà không đi qua Python API.
- Do đó, **Go và Rust cần tự chịu trách nhiệm thực thi Authentication/Authorization trên các request nhận được**.

---

## 3. Hoạt động của Rate Limiter

File `src/security/rate_limiter.py` triển khai thuật toán **Sliding Window** sử dụng bộ nhớ trong (`local-memory` thông qua `defaultdict(list)`).
- **Hạn chế**: Không đồng bộ trạng thái khi scale nhiều instance (không HA).
- **Đề xuất chuyển giao**:
  - Đối với Go Live Traffic API: Triển khai rate limiter bằng thuật toán Token Bucket / Leaky Bucket (sử dụng thư viện standard `x/time/rate` của Go) hoặc Redis-based rate limiter cho môi trường HA thực tế.
  - Đối với Rust Inference API: Sử dụng middleware `tower-limit` hoặc tự viết sliding window memory-efficient rate limiter cho Axum.

---

## 4. Mô hình bảo mật đích (Target Security Architecture)

```
                            [ Client JWT Token ]
                                      │
                                      ▼
                             [ Ingress Gateway ]
                        (HTTPS Termination & TLS)
                                      │
              ┌───────────────────────┴───────────────────────┐
              │                                               │
              ▼                                               ▼
     [ Go Live Traffic API ]                         [ Rust Inference API ]
   - Validate JWT Signature                        - Validate JWT Signature
   - Verify scope: "traffic:read"                  - Verify scope: "prediction:execute"
   - Rate limit per IP/Token                       - Scope: "model:read" / "model:reload"
```
