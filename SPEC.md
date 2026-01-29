# SPEC — VietStrict (VS1D) v1.1

## 1. Định nghĩa
VietStrict là encoding 1D, ASCII-only cho tiếng Việt, với mục tiêu:
- không dùng dấu phụ Unicode,
- không suy đoán ngữ cảnh,
- biểu diễn đầy đủ nguyên âm đặc biệt và thanh điệu,
- giải mã 1–1 về Quốc ngữ.

Âm tiết được biểu diễn theo cấu trúc: Onset + VowelCluster + Coda + Tone

Trong đó:
- `Onset`: phụ âm đầu
- `VowelCluster`: cụm nguyên âm (có marker)
- `Coda`: phụ âm cuối (nếu có)
- `Tone`: hậu tố thanh (nếu có)

---

## 2. Bảng ký hiệu bắt buộc

### 2.1 Phụ âm đặc biệt
- `đ` → `dd` (bắt buộc)

### 2.2 Nguyên âm đặc biệt (bắt buộc)
| Quốc ngữ | VietStrict |
|---|---|
| ă | `av` |
| â | `az` |
| ê | `ez` |
| ô | `oz` |
| ơ | `ow` |
| ư | `uw` |

Nguyên âm thường giữ nguyên: `a e i o u y`.

### 2.3 Cụm nguyên âm đặc biệt
| Quốc ngữ | VietStrict |
|---|---|
| iê | `iez` |
| yê | `yez` |
| uyê | `uyez` |
| uê | `uez` |
| uô | `uoz` |
| ươ | `uow` |
| ưa | `uwa` |

---

## 3. Thanh điệu (tone suffix)
Thanh điệu được biểu diễn bằng hậu tố ở CUỐI âm tiết:

| Thanh | Hậu tố |
|---|---|
| ngang | (rỗng) |
| sắc | `s` |
| huyền | `f` |
| hỏi | `r` |
| ngã | `x` |
| nặng | `j` |

**Quy tắc:** Tone suffix (nếu có) luôn là ký tự cuối cùng của âm tiết.

---

## 4. Phụ âm cuối (coda)
Coda hợp lệ: `p t c m n ng nh` hoặc rỗng.

---

## 5. Quy tắc strict (không suy đoán)
- Không có “ngầm hiểu” kiểu: `o` sau `qu` là `ô`.
- Nếu nguyên âm là `ô` thì luôn phải có `oz`.
- Nếu nguyên âm là `ă` thì luôn phải có `av`, v.v.

---

## 6. Quy tắc parse (đọc chuỗi VietStrict)

Giải mã một âm tiết VietStrict theo thứ tự **xác định, không suy đoán**, như sau:

### Bước 1. Tách thanh điệu (tone)
Nếu ký tự cuối cùng thuộc tập `{s, f, r, x, j}` thì:
- tách ký tự đó ra làm **tone suffix**
- phần còn lại tiếp tục được parse

Nếu không có, thanh điệu là **ngang**.

---

### Bước 2. Xác định phụ âm đầu đặc biệt theo chính tả (onset đặc biệt)
Nếu chuỗi (sau khi tách tone) **bắt đầu bằng** một trong các chuỗi sau thì coi đó là **onset đặc biệt**:
- `qu`
- `gi`

Lưu ý: không có onset đặc biệt `uy`. Các âm tiết bắt đầu bằng `uy...` (ví dụ: *Uyên*) được xử lý như trường hợp onset rỗng + VowelCluster bắt đầu bằng `uy...`.

---
### Bước 3. Nhận diện cụm nguyên âm (VowelCluster) bằng longest-match
Sau khi xác định onset đặc biệt (nếu có), ta tìm **VowelCluster** trong phần còn lại bằng nguyên tắc **longest-match**.

- Ưu tiên các cụm nguyên âm dài nhất, ví dụ:
  - `uyez` (uyê)
  - `uow` (ươ)
  - `uoz` (uô)
  - `uwa` (ưa)
  - `uez` (uê)
  - `iez` (iê)
  - `yez` (yê)

- Sau đó mới xét tới các marker nguyên âm ngắn:
  - `av`, `az`, `ez`, `oz`, `ow`, `uw`

Mỗi âm tiết phải có **đúng một** VowelCluster hợp lệ.

---

### Bước 4. Nhận diện phụ âm cuối (coda)
Nếu sau khi tách onset (nếu có) và VowelCluster vẫn còn ký tự, thì phần còn lại (nếu tồn tại) phải là **một coda hợp lệ**, thuộc tập:
- `ng`, `nh`
- `p`, `t`, `c`, `m`, `n`

Nếu không khớp, chuỗi được coi là **không hợp lệ** theo VietStrict.

---

### Bước 5. Phần còn lại là onset (và phải hợp lệ)
Trong trường hợp **không có onset đặc biệt** (`qu`, `gi`), onset (nếu có) là phần nằm trước VowelCluster.

Onset phải là **chuỗi phụ âm hợp lệ của tiếng Việt** (ví dụ: `b, c/k, ch, d, dd, g, gh, h, kh, l, m, n, ng, ngh, nh, p, ph, r, s, t, th, tr, v, x`).
Nếu onset không hợp lệ, chuỗi được coi là **không hợp lệ**.

---

### Ghi chú về tính strict
- Không có bước nào trong quá trình parse được phép suy đoán dựa trên từ điển hoặc ngữ cảnh.
- Một chuỗi VietStrict hợp lệ phải có **duy nhất một cách parse** theo các quy tắc trên.

---

## 7. Quy tắc `qu` và `gi` khi GẮN DẤU (decode ra Quốc ngữ)
Khi hiển thị Quốc ngữ, việc đặt dấu theo chính tả cần xử lý riêng:
- `qu` và `gi` có ký tự `u/i` thuộc phụ âm đầu (không thuộc nguyên âm hạt nhân).
- Vì vậy dấu thanh phải đặt lên nguyên âm hạt nhân của vần (theo quy tắc chính tả Việt).

Lưu ý: đây là bước hiển thị, không ảnh hưởng tới encode.

---

## 8. Ví dụ chuẩn
- tối → `tozis`
- cõi → `coix`
- đánh → `ddanhs`
- quyền → `quyeznf`
- nghiêm → `nghiezm`
- trước → `truowcs`

---

## 9. Nguyên tắc kiểm thử
Mọi implementation phải:
- encode(decode(x)) = x  (với x là chuỗi VietStrict hợp lệ)
- decode(encode(y)) = y  (với y là Quốc ngữ hợp lệ trong phạm vi spec)
- pass toàn bộ test vectors trong `tests/`.
