# Nhập liệu (sách tr.355–386)

## Các loại (Sách)

| Phần tử | Việc | Mã |
|---|---|---|
| **Numeric Entry** | bàn phím số → ghi địa chỉ | **6.1** |
| **Character Entry** | bàn phím ASCII → ghi chuỗi (≤ **512** ký tự) | **6.2** |
| Barcode Input | máy quét ngoài / bàn phím → chuỗi (≤512) | |
| Multi-language Input | nhập Unicode (tiếng Việt), đọc/ghi, mã hoá chọn được; **không chạy trong mô phỏng** | |
| Multi-line Text Input | xem/sửa file text/G-code, nhiều địa chỉ trigger (mở/lưu/tìm/chèn dòng…) | |

## Chung (Sách)

- Keypad: System Keypad (sửa bố cục/màu chữ) hoặc **Custom Keypad** (screen bàn phím tự làm).
- Style mặc định Raised; Standard/Raised/Sunken/**Transparent**; Border Fill style.
- **Input Mode**: Touch Popup (bấm hiện bàn phím) / Active Non-Popup (Interlock kích hoạt, ô nhấp nháy, gõ bằng bàn phím phần tử) / Touch Non-Popup.
- Interlock, **Trigger Before/After Writing** (bit không tự tắt), Invisible, Ignore Op Log, Asterisk, Security, Macro trước/sau, Coord động.

## Numeric Entry (Sách)

- Data Type Word/Double/Quad; Format BCD…Floating (Floating chỉ Double/Quad).
- **Min / Max** theo kiểu: Word Signed −32768..32767, Unsigned 0..65535; Double Signed ±2^31; Floating 0..9 999 999 (Double).
- Integer/Fractional = định dạng; **Gain/Offset** (ghi = a×nhập + b; có hộp tính thử; Gain lẻ thì phải Floating).
- Confirmation Window, Prefix Zero, **Show overrange message**, **Show #### when overrange**, Word arrangement, Unit Display, Unit conversion (như Numeric Display).

## Character Entry (Sách)
Insufficient string length zero; Reference order ByteSwap/WordSwap (ví dụ nhập ABCDEFGH → DCBAHGFE hoặc CDABGHEF).

## Thực tế `.dpa`

| Sách | Khoá |
|---|---|
| Min/Max | `MinValue`, `MaxValue` (chuỗi theo đơn vị hiển thị, vd `"30.0"`) |
| digits | `IntNum`, `DotNum` |
| kiểu | `MemFmt`, `MemLen` |
| trigger | `TriggerLink`, `TriggerVar`, `Order` |
| input mode | `Active` |
| bàn phím | `UseCustKeypad`, `KeypadScreenID`, `KeyPadLeft/Top/Right/Bottom`, `TitleHeight`, `wKPFStringLen0xx-00y`/`KPFont*`/`KPBkgndColor*` (chữ các phím hệ thống) |
| overrange | `ShowOverRange`, `NoMessage`, `RangeFontSize/Color` |
| chuỗi | `StringLen`, `ReadOnly`, `ByteSwap`, `WordSwap`, `ExtendedAscii` |

- **Bẫy đã gặp 30/09:** donor 6.1 (`scr_Discharge` #52) là `MemFmt=5` `MemLen=2` (REAL 2 word) → đè địa chỉ kế tiếp. Silo dùng `MemFmt=2`, `MemLen=1`, giá trị x10 + `DotNum=1`. Đã kiểm file; chưa kiểm nhập trên emulator.
- `Style=3` + giếng/khung vẽ trong ảnh nền để báo "nhập được". Đã kiểm hiển thị.
