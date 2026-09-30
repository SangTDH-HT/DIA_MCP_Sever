# Hiển thị dữ liệu (sách tr.317–340)

## Các loại (Sách)

| Phần tử | Việc | Mã |
|---|---|---|
| **Numeric Display** | hiện số ở Read Address | **5.1** |
| **Character Display** | hiện chữ ASCII từ word (tối đa **256 ký tự**) | **5.2** |
| Date / Time / Week Display | giờ hệ thống; hoặc **timestamp giây từ 1970** ở Read Address (nên Quad Word) | **5.3 / 5.4** |
| General Message Display | chữ theo state của địa chỉ (Word tới **1000** state) | |
| Moving Sign | chữ chạy theo state (256 state), hướng, bước 1–50 px, chu kỳ | |
| QR Code Display | chuỗi → QR (≤256 ký tự, mức sửa lỗi L/M/Q/H) | |
| Barcode | EAN13 (≤12) / CODE128 (≤48) | |

## Numeric Display (Sách)

- Data Type, Format (Floating chỉ Double/Quad), **Integer / Fractional digits** (số lẻ là **định dạng**, không phải số thực, trừ khi Floating).
- **Gain / Offset**: hiển thị = Gain × giá trị + Offset; *Round off*.
- Prefix Zero, **Word arrangement** (đảo word cao/thấp), Unit Display (chữ đơn vị gắn vào ô), Mark as Asterisk.
- **Unit conversion**: Disable / Custom formula (A×x+B, ra Floating) / đơn vị cố định / % (đặt 0% và 100%) / **theo mã** từ địa chỉ: tốc độ 101 mm/s 102 inch/s; áp suất 201 kg/cm² 202 bar 203 MPa 204 psi; vị trí 301 mm 302 inch; nhiệt 401 °F 402 °C; khối lượng 501 T 502 kN 503 g 504 oz; thể tích 601 L 602 ml 603 kL; 700 = %.

## Character Display (Sách)

- 1 word = 2 byte, **byte thấp trước**: `$0 = 0x4241` hiện "AB".
- Insufficient string length zero, **Reference order**: ByteSwap (LowHigh) và/hoặc WordSwap (HighLow) - dùng khi PLC xếp byte khác.
- Invisible Address chỉ có ở Numeric / Character / General Message Display.

## Thực tế `.dpa`

| Sách | Khoá |
|---|---|
| Integer/Fractional | `IntNum`, `DotNum` |
| Prefix zero | `LeadingZero` |
| Gain/Offset/Round | `GainValue`, `OffsetValue`, `Roundoff` |
| Word order | `HiWordFirst` |
| Unit conversion | `UnitType`, `UnitSrc(Var)`, `UnitDisplay(Var)`, `UnitPercent…`, `UnitCustom…` |
| Chuỗi | `StringLen`, `StringLeadingZero`, `ByteSwap`, `WordSwap`, `ExtendedAscii` |
| Date/Time format | `DataFmt`; `ReadVar` rỗng = giờ hệ thống |

- Ô số/chữ không nền: `Style=3`, căn phải `FontAlign=36`. Đã kiểm 30/09.
- Chuỗi từ **S7 STRING** có 2 byte đầu (max/len) → lệch 1 word; dùng `Array of Char` hoặc bỏ 2 byte đầu. Chưa kiểm trên PLC thật.
- `IntNum` quá nhỏ thì số bị cắt/hiện ####; DIAScreen tự tính lại chuỗi mẫu `wTextLen0` (`#####.#`) khi lưu - không phải sửa tay.
