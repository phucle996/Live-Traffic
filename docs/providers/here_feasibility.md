# docs/providers/here_feasibility.md
# Phase HERE-0 — HERE Traffic API Feasibility Analysis for TP.HCM
# ==============================================================================

# HERE Traffic API — Feasibility Analysis

> **Trạng thái**: Đang thực hiện pilot  
> **Phase**: HERE-0  
> **Ngày tạo**: 2026-07-22  
> **Người thực hiện**: [điền tên]  
> **Phiên bản**: 1.0

---

## 1. Mục tiêu

Xác nhận HERE Traffic API v7 đáp ứng các yêu cầu tối thiểu để thay thế TomTom làm provider chính cho hệ thống giao thông TP.HCM trước khi bắt đầu Phase HERE-1 (refactor provider abstraction).

**Tiêu chí ngừng sớm**: Nếu phase này thất bại ở bất kỳ hard gate nào, dừng toàn bộ quá trình tích hợp HERE và giữ nguyên TomTom.

---

## 2. Hard Gates (phải đạt tất cả)

| # | Gate | Yêu cầu | Kết quả |
|---|------|---------|---------|
| G1 | Coverage TP.HCM | ≥ 80% số đường mục tiêu có flow data | ⬜ Chưa đánh giá |
| G2 | Multi-time coverage | Có data ở ít nhất 3 trong 4 time slot | ⬜ Chưa đánh giá |
| G3 | Geometry available | ≥ 70% flow item có road geometry | ⬜ Chưa đánh giá |
| G4 | License — lưu trữ | Được phép lưu raw response | ⬜ Chưa xác nhận |
| G5 | License — training | Được phép dùng data để train model | ⬜ Chưa xác nhận |
| G6 | License — derived | Được phép tạo prediction từ HERE data | ⬜ Chưa xác nhận |
| G7 | Latency | p95 latency ≤ 5 giây cho bbox query | ⬜ Chưa đánh giá |
| G8 | Error rate | Error rate < 5% trong pilot period | ⬜ Chưa đánh giá |

---

## 3. Bốn Vùng Pilot TP.HCM

| Zone | Tên | BBox | Lý do chọn |
|------|-----|------|------------|
| `quan1` | Quận 1 — Trung tâm | 10.760,106.692 → 10.790,106.710 | Đường lớn, mật độ cao nhất |
| `binh_thanh` | Bình Thạnh | 10.795,106.700 → 10.820,106.730 | Cầu Sài Gòn, Hàng Xanh |
| `thu_duc` | TP. Thủ Đức | 10.845,106.770 → 10.890,106.820 | Xa lộ Hà Nội, cửa ngõ đông |
| `tan_son_nhat` | Sân bay Tân Sơn Nhất | 10.800,106.655 → 10.830,106.685 | Điểm kẹt xe kinh niên |

---

## 4. Time Slots Thu Thập

| Slot | Giờ | Mục đích |
|------|-----|---------|
| `peak_morning` | 07:00–09:00 | Cao điểm sáng |
| `off_peak` | 10:00–16:00 | Thấp điểm |
| `peak_evening` | 16:00–19:00 | Cao điểm chiều |
| `weekend` | Thứ 7–CN | Mẫu cuối tuần |

---

## 5. Metrics Thu Thập

### 5.1 Volume & Coverage
- Số flow item / zone / time slot
- Số item có geometry
- Geometry coverage rate (%)
- Tổng số đoạn đường độc lập

### 5.2 Data Quality
- Speed range (min, max, mean, median, stdev)
- Free-flow speed distribution
- Jam factor distribution (0–10)
- Road closed flags
- Khoảng tốc độ bất thường (speed < 0 hoặc > free_flow * 2)

### 5.3 Technical Performance
- HTTP latency per request
- Response size (bytes)
- HTTP error codes
- Timeout rate
- Quota consumption (nếu có header)

### 5.4 Coverage vs OSM
- Đường `motorway`, `trunk`, `primary`, `secondary`, `tertiary` trong mỗi zone
- Số đường OSM có flow item tương ứng từ HERE
- Coverage percentage theo road class

---

## 6. Kết Quả Pilot (Điền Sau Khi Chạy)

### 6.1 Quận 1

| Time Slot | Flow Items | Geometry | Speed (mean) | Jam (mean) | Latency |
|-----------|-----------|---------|-------------|-----------|---------|
| peak_morning | — | — | — | — | — |
| off_peak | — | — | — | — | — |
| peak_evening | — | — | — | — | — |
| weekend | — | — | — | — | — |

### 6.2 Bình Thạnh

| Time Slot | Flow Items | Geometry | Speed (mean) | Jam (mean) | Latency |
|-----------|-----------|---------|-------------|-----------|---------|
| peak_morning | — | — | — | — | — |
| off_peak | — | — | — | — | — |
| peak_evening | — | — | — | — | — |
| weekend | — | — | — | — | — |

### 6.3 Thủ Đức

| Time Slot | Flow Items | Geometry | Speed (mean) | Jam (mean) | Latency |
|-----------|-----------|---------|-------------|-----------|---------|
| peak_morning | — | — | — | — | — |
| off_peak | — | — | — | — | — |
| peak_evening | — | — | — | — | — |
| weekend | — | — | — | — | — |

### 6.4 Tân Sơn Nhất

| Time Slot | Flow Items | Geometry | Speed (mean) | Jam (mean) | Latency |
|-----------|-----------|---------|-------------|-----------|---------|
| peak_morning | — | — | — | — | — |
| off_peak | — | — | — | — | — |
| peak_evening | — | — | — | — | — |
| weekend | — | — | — | — | — |

---

## 7. So Sánh HERE vs TomTom (Sau Khi Có Dữ Liệu)

| Tiêu chí | TomTom (hiện tại) | HERE (pilot) |
|---------|------------------|-------------|
| Coverage Quận 1 | [đo từ data cũ] | — |
| Coverage Bình Thạnh | — | — |
| Speed accuracy | — | — |
| Update frequency | 5 phút | — |
| Latency (p95) | — | — |
| Geometry support | Điểm tọa độ | BBox flow |
| Pricing/quota | [ghi ở đây] | — |

---

## 8. Rủi Ro Nhận Diện

| Rủi ro | Mức độ | Biện pháp |
|--------|--------|-----------|
| HERE coverage thấp ở đường nhỏ | Trung bình | Giữ TomTom fallback |
| License không cho phép lưu/train | Cao | Đây là hard gate — dừng nếu không đạt |
| Quota production không đủ | Trung bình | Đánh giá chi phí trước cutover |
| HERE API thay đổi schema | Thấp | Contract + decoder test |
| Lag dữ liệu > 5 phút | Trung bình | Đo thực tế trong pilot |

---

## 9. Kết Luận

> *(Điền sau khi hoàn thành pilot và nhận kết quả từ `summarize_here_pilot.py`)*

**Quyết định**: [ ] approved | [ ] approved_with_constraints | [ ] rejected

**Lý do**:

**Bước tiếp theo**:
- [ ] Điền `provider_decision.md`
- [ ] Nếu approved → bắt đầu HERE-1
- [ ] Nếu rejected → tài liệu hóa lý do và duy trì TomTom

---

*File này là đầu vào cho `docs/providers/provider_decision.md`.*
*Không sửa production routing trước khi `provider_decision.md` được ký off.*
