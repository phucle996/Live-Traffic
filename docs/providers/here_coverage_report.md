# docs/providers/here_coverage_report.md
# Phase HERE-0 — HERE Traffic API Coverage Report TP.HCM
# ==============================================================================

# HERE Traffic API — Coverage Report

> **Trạng thái**: Chờ dữ liệu pilot  
> **Phase**: HERE-0  
> **Ngày tạo**: 2026-07-22  
> **Người thực hiện**: [điền tên]  
> **Dữ liệu nguồn**: `artifacts/provider_pilot/raw/`

---

## 1. Phương Pháp Đánh Giá

Coverage được đánh giá bằng cách so sánh:
1. **Đường mục tiêu từ OSM** trong mỗi vùng pilot (road class: motorway → tertiary)
2. **Flow item từ HERE** trả về cho cùng bounding box

Metric chính: **tổng số đường mục tiêu có ít nhất 1 flow item match** / **tổng số đường mục tiêu**

---

## 2. Đường Mục Tiêu Theo Road Class

Road class được tính (theo spec model-v2.md):

| Road Class OSM | Ưu tiên |
|---------------|--------|
| motorway | Bắt buộc |
| motorway_link | Bắt buộc |
| trunk | Bắt buộc |
| trunk_link | Bắt buộc |
| primary | Bắt buộc |
| primary_link | Bắt buộc |
| secondary | Bắt buộc |
| secondary_link | Bắt buộc |
| tertiary | Bắt buộc |
| tertiary_link | Bắt buộc |
| unclassified (có tên) | Có điều kiện |
| residential (đủ điều kiện) | Có điều kiện |

---

## 3. Kết Quả Coverage Theo Vùng

### 3.1 Quận 1 (`quan1`)

**BBox**: 10.760,106.692 → 10.790,106.710

| Road Class | Số đường OSM | HERE flow items | Coverage % | Ghi chú |
|-----------|-------------|----------------|-----------|---------|
| motorway | — | — | — | — |
| trunk | — | — | — | — |
| primary | — | — | — | — |
| secondary | — | — | — | — |
| tertiary | — | — | — | — |
| **Tổng** | **—** | **—** | **—** | — |

**HERE items có geometry**: —/— (—%)

---

### 3.2 Bình Thạnh (`binh_thanh`)

**BBox**: 10.795,106.700 → 10.820,106.730

| Road Class | Số đường OSM | HERE flow items | Coverage % | Ghi chú |
|-----------|-------------|----------------|-----------|---------|
| motorway | — | — | — | — |
| trunk | — | — | — | — |
| primary | — | — | — | — |
| secondary | — | — | — | — |
| tertiary | — | — | — | — |
| **Tổng** | **—** | **—** | **—** | — |

**HERE items có geometry**: —/— (—%)

---

### 3.3 Thủ Đức (`thu_duc`)

**BBox**: 10.845,106.770 → 10.890,106.820

| Road Class | Số đường OSM | HERE flow items | Coverage % | Ghi chú |
|-----------|-------------|----------------|-----------|---------|
| motorway | — | — | — | — |
| trunk | — | — | — | — |
| primary | — | — | — | — |
| secondary | — | — | — | — |
| tertiary | — | — | — | — |
| **Tổng** | **—** | **—** | **—** | — |

**HERE items có geometry**: —/— (—%)

---

### 3.4 Tân Sơn Nhất (`tan_son_nhat`)

**BBox**: 10.800,106.655 → 10.830,106.685

| Road Class | Số đường OSM | HERE flow items | Coverage % | Ghi chú |
|-----------|-------------|----------------|-----------|---------|
| motorway | — | — | — | — |
| trunk | — | — | — | — |
| primary | — | — | — | — |
| secondary | — | — | — | — |
| tertiary | — | — | — | — |
| **Tổng** | **—** | **—** | **—** | — |

**HERE items có geometry**: —/— (—%)

---

## 4. Tổng Hợp 4 Vùng

| Vùng | OSM roads | HERE items | Coverage | Status |
|------|----------|-----------|---------|--------|
| Quận 1 | — | — | —% | ⬜ |
| Bình Thạnh | — | — | —% | ⬜ |
| Thủ Đức | — | — | —% | ⬜ |
| Tân Sơn Nhất | — | — | —% | ⬜ |
| **Trung bình** | **—** | **—** | **—%** | ⬜ |

**Ngưỡng tối thiểu (spec HERE-0)**: ≥ 80%

---

## 5. Phân Tích Đường Không Được Phủ

*(Điền sau khi chạy spatial matching với OSM)*

Danh sách đường mục tiêu không có flow item từ HERE:

| Tên đường | Road Class | Quận | Lý do nghi ngờ |
|----------|-----------|------|---------------|
| [điền] | primary | [điền] | bbox không đủ rộng / HERE không support |
| ... | ... | ... | ... |

---

## 6. Nhận Xét Về Chất Lượng Data

### 6.1 Speed Distribution
*(Điền từ kết quả `summarize_here_pilot.py`)*

```
Giờ cao điểm:
  mean speed   : —
  median speed : —
  jam factor   : —

Thấp điểm:
  mean speed   : —
  median speed : —
  jam factor   : —
```

### 6.2 So Sánh Sơ Bộ Với TomTom

| Metric | TomTom | HERE | Chênh lệch |
|--------|--------|------|-----------|
| Flow items / zone | — | — | — |
| Geometry coverage | — | — | — |
| Speed granularity | Điểm đơn | Đoạn đường | HERE tốt hơn |
| Update lag | ~5 phút | — | — |

---

## 7. Kết Luận Coverage

> *(Điền sau khi hoàn thành phân tích)*

**Kết quả tổng thể**: ⬜ Đạt / ⬜ Không đạt ngưỡng 80%

**Các đường lớn có coverage tốt**:
- [điền]

**Các khu vực có coverage yếu**:
- [điền]

**Khuyến nghị**:
- [điền]

---

*File này là input cho `docs/providers/provider_decision.md`.*
*Dữ liệu raw: `artifacts/provider_pilot/raw/`*
*Dữ liệu normalized: `artifacts/provider_pilot/normalized/`*
