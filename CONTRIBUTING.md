# Đóng góp cho VietStrict

Repo ưu tiên theo thứ tự:
1) Spec rõ ràng, kiểm chứng được
2) Test vectors phong phú (càng nhiều edge cases càng tốt)
3) Reference implementation (Python/JS)
4) Tooling (CLI, web demo, keyboard/IME-less helpers)

## Cách đóng góp nhanh
- Thêm test cases vào `tests/words.tsv` (Quốc ngữ<TAB>VietStrict)
- Thêm đoạn văn mẫu vào `tests/*.tsv`
- Mở issue nếu phát hiện mơ hồ spec

## Quy ước
- Không thêm “shorthand” vào v1.0 strict.
- Nếu đề xuất rút gọn, tạo nhánh `shorthand/` hoặc bản spec v2.
