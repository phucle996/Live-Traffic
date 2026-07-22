# docs/providers/provider_decision.md
# Phase HERE-0 — Provider Decision Document
# ==============================================================================
# Đây là tài liệu quyết định cuối cùng cho Phase HERE-0.
# KHÔNG bắt đầu HERE-1 trước khi tài liệu này được điền và ký off.
# ==============================================================================

# Provider Decision — HERE Traffic API

> **Trạng thái**: ⬜ PENDING — Chờ kết quả pilot và xác nhận license  
> **Phase**: HERE-0  
> **Ngày tạo**: 2026-07-22  
> **Decision maker**: [điền tên / team]  
> **Ngày quyết định**: —

---

## 1. Tóm Tắt Quyết Định

```
QUYẾT ĐỊNH: [ ] APPROVED
             [ ] APPROVED_WITH_CONSTRAINTS
             [ ] REJECTED
```

**Lý do quyết định**:
> *(Điền sau khi có đầy đủ kết quả pilot và xác nhận license)*

---

## 2. Cơ Sở Quyết Định

### 2.1 Coverage Gate

| Tiêu chí | Ngưỡng | Kết quả Thực Tế | Đạt? |
|---------|--------|----------------|------|
| Coverage ≥ 80% zones có data | 80% | —% | ⬜ |
| Data ở ≥ 2 time slots | 2 | — | ⬜ |
| Geometry trong ≥ 70% items | 70% | —% | ⬜ |
| Latency p95 ≤ 5 giây | 5000ms | —ms | ⬜ |
| Error rate < 5% | 5% | —% | ⬜ |

### 2.2 Legal Gate

| Câu hỏi | Trả lời HERE | Đạt? |
|---------|-------------|------|
| Được phép lưu raw response | — | ⬜ |
| Retention limit | — ngày | ⬜ |
| Được phép dùng để train ML | — | ⬜ |
| Được phép tạo derived prediction | — | ⬜ |
| Chi phí production có thể chấp nhận | — | ⬜ |

---

## 3. Nếu APPROVED

Tiến hành theo thứ tự:

```
HERE-1  → Provider abstraction trong Go
HERE-2  → HERE client production-grade
ROAD-1  → Road catalog TP.HCM
HERE-3  → Grid planner
...
```

**Ràng buộc**:
- Không xóa TomTom client cho đến Phase CUTOVER
- Không dùng HERE data để train cho đến khi legal gate xanh hoàn toàn
- TomTom vẫn là fallback provider

---

## 4. Nếu APPROVED_WITH_CONSTRAINTS

Ghi rõ constraints:

```
Constraint 1: [ví dụ — không được lưu quá 30 ngày]
  → Biện pháp: thêm retention job tự động xóa

Constraint 2: [ví dụ — chỉ được dùng cho internal use]
  → Biện pháp: không expose prediction API ra public

Constraint 3: [...]
  → Biện pháp: [...]
```

Tất cả constraints phải được implement trước khi bắt đầu thu thập production data.

---

## 5. Nếu REJECTED

Lý do từ chối:
```
[ ] Coverage TP.HCM không đạt ngưỡng
[ ] HERE không cho phép lưu raw data
[ ] HERE không cho phép training
[ ] Chi phí production quá cao
[ ] Latency không đáp ứng yêu cầu
[ ] Khác: [điền]
```

Hành động tiếp theo khi rejected:
- Giữ nguyên TomTom là primary provider
- Đánh giá lại HERE sau [X] tháng nếu họ cải thiện
- Hoặc đánh giá provider thay thế: [INRIX / Waze API / OpenStreetMap Overpass]
- Không có thay đổi nào trong production

---

## 6. Tài Liệu Đính Kèm

| Tài liệu | Đường dẫn | Trạng thái |
|---------|----------|-----------|
| Feasibility analysis | docs/providers/here_feasibility.md | ⬜ |
| Licensing questions | docs/providers/here_licensing_questions.md | ⬜ |
| Coverage report | docs/providers/here_coverage_report.md | ⬜ |
| Pilot raw data | artifacts/provider_pilot/raw/ | ⬜ |
| Normalized samples | artifacts/provider_pilot/normalized/ | ⬜ |
| Pilot report JSON | artifacts/provider_pilot/pilot_report.json | ⬜ |
| HERE Terms of Service | [URL hoặc file đính kèm] | ⬜ |
| HERE License confirmation | [email/văn bản từ HERE] | ⬜ |

---

## 7. Sign-off

| Vai trò | Tên | Ngày | Chữ ký |
|--------|-----|------|--------|
| Tech Lead | — | — | — |
| Data/ML Lead | — | — | — |
| Legal/Compliance | — | — | — |
| Project Owner | — | — | — |

---

## 8. Lịch Sử Thay Đổi

| Ngày | Version | Thay đổi | Người thực hiện |
|------|---------|---------|----------------|
| 2026-07-22 | 1.0 | Tạo template | Antigravity |
| — | — | Điền kết quả pilot | — |
| — | — | Điền kết quả legal | — |
| — | — | Final decision | — |

---

> **NHẮC NHỞ**: File này là Source of Truth cho việc có tiến sang HERE-1 hay không.
> Bất kỳ code nào liên quan đến HERE provider đều KHÔNG được merge vào main
> trước khi file này có quyết định `APPROVED` hoặc `APPROVED_WITH_CONSTRAINTS`.
