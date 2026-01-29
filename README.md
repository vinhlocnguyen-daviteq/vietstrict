# VietStrict (VS1D) — Chữ Việt tuyến tính (STRICT 1D)

VietStrict (Vietnamese Strict 1D, viết tắt **VS1D**) là một **lớp biểu diễn 1 chiều (1D), thuần ASCII, xác định (deterministic)** cho tiếng Việt: không dùng dấu phụ Unicode, không cần IME, không suy đoán ngữ cảnh, và **mã hoá/giải mã 1–1** với Quốc ngữ.

> VietStrict không phải “bộ gõ”, không phải Telex/VNI, và không phải lời kêu gọi thay thế Quốc ngữ hiển thị.  
> Đây là **encoding kỹ thuật** để gõ/xử lý tiếng Việt hiệu quả trong môi trường số.

---

## Mục tiêu

- **1D**: mọi thông tin nằm trên một dòng ký tự.
- **ASCII-only**: dùng ký tự Latin chuẩn, không dấu treo.
- **Strict**: không mơ hồ, không đoán, không tự sửa.
- **Reversible**: VietStrict ⇄ Quốc ngữ là ánh xạ 1–1.
- **Machine-first**: phù hợp NLP/AI, search/indexing, log, terminal, lập trình.

---

## Ví dụ nhanh

| Quốc ngữ | VietStrict |
|---|---|
| tối | `tozis` |
| cõi | `coix` |
| đánh | `ddanhs` |
| “Trăm năm trong cõi người ta” | `travm navm trong coix nguowif ta` |

---

## Tài liệu

- Đặc tả chuẩn: [SPEC.md](./SPEC.md)
- Bộ test: [tests/words.tsv](./tests/words.tsv), [tests/kieu_10_lines.tsv](./tests/kieu_10_lines.tsv)
- Ví dụ: [examples/quickstart.md](./examples/quickstart.md)

---

## Trạng thái

- Spec: **v1.0 (ổn định)**
- Bộ test: đang mở rộng
- Reference implementation: chưa có (mời cộng đồng đóng góp)

---

## Đóng góp

Repo này ưu tiên:
1) làm spec rõ ràng,  
2) làm test vectors đầy đủ,  
3) rồi mới viết reference implementation.

Xem [CONTRIBUTING.md](./CONTRIBUTING.md).

---

## Giấy phép

MIT (dự kiến). Có thể điều chỉnh nếu cần cho chuẩn hoá/tiêu chuẩn.
