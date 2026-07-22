# docs/providers/here_licensing_questions.md
# Phase HERE-0 — Checklist câu hỏi pháp lý cần xác nhận với HERE
# ==============================================================================

# HERE Traffic API — Licensing Questions Checklist

> **Trạng thái**: Chờ xác nhận  
> **Phase**: HERE-0  
> **Ngày tạo**: 2026-07-22  
> **Người phụ trách**: [điền tên]  
> **Kênh liên lạc HERE**: developer.here.com / sales contact

---

> **QUAN TRỌNG**: Không sử dụng bất kỳ raw response nào từ HERE để training,
> lưu trữ lâu dài, hoặc tạo derived product cho đến khi tất cả câu hỏi bên
> dưới được xác nhận rõ ràng bằng văn bản từ HERE.

---

## Nhóm A — Quyền Lưu Trữ (Storage Rights)

| # | Câu hỏi | Nguồn kiểm tra | Trả lời | Người xác nhận | Ngày |
|---|---------|---------------|---------|---------------|------|
| A1 | Có được phép lưu raw API response (full JSON) xuống disk/HDFS không? | HERE ToS §[điền] | ⬜ Chưa | — | — |
| A2 | Retention tối đa được phép là bao lâu (ngày/tháng/năm)? | HERE ToS §[điền] | ⬜ Chưa | — | — |
| A3 | Có khác biệt retention giữa development key và production key không? | HERE Pricing page | ⬜ Chưa | — | — |
| A4 | Có cần xóa data định kỳ theo license không? Nếu có, chu kỳ là bao nhiêu? | HERE ToS | ⬜ Chưa | — | — |
| A5 | Có được phép cache response trong Redis/bộ nhớ ngắn hạn (< 24h) không? | HERE ToS | ⬜ Chưa | — | — |

---

## Nhóm B — Quyền Dùng Để Training (Training Rights)

| # | Câu hỏi | Nguồn kiểm tra | Trả lời | Người xác nhận | Ngày |
|---|---------|---------------|---------|---------------|------|
| B1 | Có được phép dùng HERE data (speed, jam factor, geometry) để train ML model không? | HERE ToS | ⬜ Chưa | — | — |
| B2 | Nếu được phép, có giới hạn loại model hoặc mục đích sử dụng model không? | HERE ToS | ⬜ Chưa | — | — |
| B3 | Model được train từ HERE data có thể deploy để serve prediction cho end-user không? | HERE ToS | ⬜ Chưa | — | — |
| B4 | HERE data có thể mix với dữ liệu từ nguồn khác (TomTom, OSM) để train không? | HERE ToS | ⬜ Chưa | — | — |
| B5 | Khi không còn subscribe HERE, model đã train có thể tiếp tục sử dụng không? | HERE ToS | ⬜ Chưa | — | — |

---

## Nhóm C — Quyền Tạo Derived Product (Derived Data Rights)

| # | Câu hỏi | Nguồn kiểm tra | Trả lời | Người xác nhận | Ngày |
|---|---------|---------------|---------|---------------|------|
| C1 | Có được phép tạo prediction (congestion status, speed forecast) từ model đã train với HERE data không? | HERE ToS | ⬜ Chưa | — | — |
| C2 | Có phải ghi nguồn attribution "Powered by HERE" trong sản phẩm không? | HERE ToS | ⬜ Chưa | — | — |
| C3 | Có thể hiển thị prediction (derived data) trên custom map (MapLibre/Google Maps) không? | HERE ToS | ⬜ Chưa | — | — |
| C4 | Có giới hạn về redistribution prediction ra bên ngoài org không? | HERE ToS | ⬜ Chưa | — | — |

---

## Nhóm D — Quota & Chi Phí Production

| # | Câu hỏi | Nguồn kiểm tra | Trả lời | Người xác nhận | Ngày |
|---|---------|---------------|---------|---------------|------|
| D1 | Freemium/development quota là bao nhiêu request/ngày? | HERE Pricing | ⬜ Chưa | — | — |
| D2 | Chi phí production ước tính khi crawl 4 zones × 5 phút/lần × 24h? | HERE Pricing | ⬜ Chưa | — | — |
| D3 | Có gói flat-rate hoặc enterprise không? | HERE Sales | ⬜ Chưa | — | — |
| D4 | Rate limit per second và per day là bao nhiêu? | HERE Docs | ⬜ Chưa | — | — |
| D5 | Có header trả về quota remaining không? (dùng để kiểm soát budget trong code) | HERE API Docs | ⬜ Chưa | — | — |
| D6 | Cơ chế throttling khi vượt quota: soft block hay hard block? | HERE Docs | ⬜ Chưa | — | — |

---

## Nhóm E — Data Freshness & SLA

| # | Câu hỏi | Nguồn kiểm tra | Trả lời | Người xác nhận | Ngày |
|---|---------|---------------|---------|---------------|------|
| E1 | HERE Traffic v7 update frequency tại TP.HCM là bao lâu? | HERE Docs | ⬜ Chưa | — | — |
| E2 | Có SLA uptime cho Traffic API không? | HERE SLA | ⬜ Chưa | — | — |
| E3 | Nếu API down, có alternative endpoint hoặc degraded mode không? | HERE Docs | ⬜ Chưa | — | — |

---

## Nhóm F — Compliance & Security

| # | Câu hỏi | Nguồn kiểm tra | Trả lời | Người xác nhận | Ngày |
|---|---------|---------------|---------|---------------|------|
| F1 | HERE data có chứa PII không? (cần xác nhận cho GDPR/PDPA compliance) | HERE Privacy | ⬜ Chưa | — | — |
| F2 | API key rotation — HERE có hỗ trợ không? Chu kỳ bao lâu? | HERE Console | ⬜ Chưa | — | — |
| F3 | Có thể restrict API key theo domain/IP không? | HERE Console | ⬜ Chưa | — | — |

---

## Tóm Tắt Gate

Tất cả nhóm sau phải được xác nhận **trước khi** đưa HERE data vào bất kỳ pipeline nào:

```
[HARD GATE — KHÔNG bỏ qua]
A1  — Có thể lưu raw response
A2  — Biết retention limit
B1  — Có thể dùng để train
C1  — Có thể tạo prediction từ model
```

```
[SOFT — Cần biết trước production]
D1–D6 — Quota và chi phí
E1    — Update frequency
F1    — PII check
```

---

## Kết Quả Cuối Cùng

> *(Điền sau khi xác nhận từ HERE)*

| Nhóm | Kết quả |
|------|---------|
| A — Lưu trữ | ⬜ Chưa xác nhận |
| B — Training | ⬜ Chưa xác nhận |
| C — Derived | ⬜ Chưa xác nhận |
| D — Quota | ⬜ Chưa xác nhận |
| E — SLA | ⬜ Chưa xác nhận |
| F — Compliance | ⬜ Chưa xác nhận |

**Ngày xác nhận cuối**: —  
**Tài liệu xác nhận đính kèm**: —  
**Kết luận**: [ ] approved | [ ] approved_with_constraints | [ ] rejected

---

*Xem quyết định chính thức tại: `docs/providers/provider_decision.md`*
