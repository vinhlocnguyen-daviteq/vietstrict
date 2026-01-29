# Governance — VietStrict (VS1D)

## 1. Phạm vi dự án
VietStrict (VS1D) là một **đặc tả (specification)** cho biểu diễn tiếng Việt dạng 1D strict, phục vụ xử lý kỹ thuật (NLP, IME, compiler, AI, tooling).

Repository này chứa:
- SPEC (chuẩn chính thức)
- Test vectors
- Tài liệu tham chiếu
- Các implementation và benchmark (nếu có)

---

## 2. Vai trò và trách nhiệm

### Originator / Spec Maintainer
- **Người khởi xướng và maintainer hiện tại:** Nguyen Vinh Loc
- Có **quyền chốt cuối cùng** đối với mọi thay đổi SPEC chính thức.

Trong giai đoạn hiện tại, dự án áp dụng mô hình:
> **BDFL (Benevolent Dictator For Life)** cho phần SPEC.

Điều này nhằm:
- đảm bảo tính nhất quán
- tránh phân mảnh chuẩn
- giữ logic thiết kế xuyên suốt

---

## 3. Các loại đóng góp được chấp nhận

### 3.1. Đóng góp an toàn (không làm thay đổi chuẩn)
- Bổ sung **test vectors**
- Cải thiện tài liệu (README, FAQ, ví dụ)
- Viết benchmark / báo cáo đo lường
- Reference implementation (encode/decode)
- Tooling (CLI, demo, editor support)

👉 Các đóng góp này có thể được duyệt nhanh.

---

### 3.2. Đóng góp ảnh hưởng SPEC (thay đổi chuẩn)
Bao gồm:
- thay đổi mapping
- thay đổi quy tắc parse/decode
- thêm/bỏ cụm nguyên âm, thanh điệu, marker

👉 **BẮT BUỘC** đi theo quy trình ở Mục 4.

---

## 4. Quy trình thay đổi SPEC (bắt buộc)

Mọi thay đổi SPEC phải tuân theo **đầy đủ các bước sau**:

1. **Mở Issue trước**
   - mô tả vấn đề / mục tiêu
   - nêu rõ đề xuất cụ thể
   - có ví dụ pass / fail

2. Thảo luận trong Issue
   - làm rõ tác động
   - xác định breaking hay non-breaking

3. Khi hướng thay đổi được chấp nhận:
   - Contributor mở Pull Request (PR)

4. PR phải đồng thời cập nhật:
   - `SPEC.md`
   - `CHANGELOG.md`
   - `tests/` (test chứng minh thay đổi)

5. Spec Maintainer review và quyết định merge.

6. Sau khi merge:
   - phát hành **spec-vX.Y** (release mới)

> **Nguyên tắc bắt buộc:**  
> *Không có test → không có spec change.*

---

## 5. Versioning
- VietStrict sử dụng **Semantic Versioning** cho SPEC:
  - `vX.Y`
- Mọi thay đổi làm thay đổi cách encode/decode đều là **breaking** → tăng `Y`.

---

## 6. Fork và biến thể
- Mọi người được tự do fork và thử nghiệm.
- Tuy nhiên, chỉ nhánh `main` của repo này đại diện cho:
  > **VietStrict (VS1D) official specification**

---

## 7. Nguyên tắc chung
- Ưu tiên tính **strict, deterministic, reversible**
- Không suy đoán khi parse/decode
- Tránh thay đổi vì lý do thẩm mỹ thuần tuý
- Tôn trọng phản hồi kỹ thuật, tránh tranh luận cảm tính
