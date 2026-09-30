# Thuộc tính chung của phần tử (sách tr.236–248 và phần Common của từng chương)

## Main - địa chỉ (Sách)

- **Write / Read Address**: bộ nhớ trong hoặc thanh ghi PLC; loại nhập chỉ là Word (bit dùng `$n.b`). Chỉ đặt Write thì Read = Write.
- **Write / Read Offset Address**: địa chỉ thật = Địa chỉ + (giá trị ô Offset) × cỡ [Data Type]. Offset Length chỉ chọn được trên Numeric Display/Entry.
  Sách DOPSoft phụ lục D (tr.2076–2083): giá trị offset **không dấu 0–65535**; chỉ đặt Write Offset thì Read Offset = Write Offset; nút không có Data Type thì đơn vị là **bit** (`$3000.0` + 3 → `$3000.3`); Double Word nhảy 2 word; **Character Display/Entry tính theo Word, KHÔNG theo String Length** → muốn hiện chuỗi thứ n (mỗi chuỗi 10 word) thì ô offset phải = n × 10. Có Offset: nút bit/Multistate/Set Value/Constant/Tăng-Giảm, Meter, Bar, Pipe(1)(2)(6)(7), Pie, mọi Indicator, Numeric/Character/Message Display, Moving Sign, State/Animated Graphic, mọi ô nhập, Slider, ComboBox, ListBox, Line/Rectangle/Circle/Text. Địa chỉ PLC dài Double Word (vd DVP C200–C255) không hỗ trợ.
- Data Type Word / Double Word / Quad Word; Data Format BCD, Signed BCD, Signed/Unsigned Decimal, Hex, Binary, **Floating chỉ với Double/Quad Word**.

## Style (Sách)

- Style: nút/chỉ thị Standard / Raised / Round / **Invisible**; hiển thị/nhập Standard / Raised / Sunken / **Transparent**.
- Foreground/Background: Gradient (≤5 điểm dừng, góc/tâm có thể lấy từ địa chỉ), Solid, Fill Pattern.
- Blink (màu đảo), Use Text Pic (tương thích DOP-B), **Transparency 50–255**, Shadow (chỉ Numeric/Character Display: offset −100..100, blur 0..100).
- Automatically resized based on text (chỉ phóng to, không thu).

## Text (Sách)
Chữ theo từng **state × ngôn ngữ**; Process text of all states, Uniform text size, Text Bank, Import Font Template.

## Picture (Sách)
Picture Name (kéo ảnh từ Picture Bank vào từng state), Alignment, Stretch (Stretch All / 1:1 / Actual Size), Process pictures of all states, **Transparent Color** (một màu trong ảnh thành trong suốt).

## Operating conds. (Sách)

| Thuộc tính | Ý nghĩa |
|---|---|
| **Interlock Address + State** | chỉ cho thao tác khi bit = State; Display Mode: hiện bình thường hoặc hiện biển cấm |
| **Invisible Address + State** | State On: bit ON thì ẩn; State Off: bit OFF thì ẩn. Có ở mọi nhóm (nút, hiển thị, nhập, chỉ thị, đồ hoạ, list, đồng hồ, ống…) |
| Min. Press Time | 0–10 s giữ mới tác động (chống bấm nhầm) |
| Confirmation Window | Disable / Confirmation / Second confirmation of account / Custom (screen xác nhận tự làm) |
| Modifier + Hot Key | phím tắt khi có bàn phím ngoài |
| Ignore Operation Log | không ghi vào nhật ký thao tác |
| Trigger Mode / Addr. (nhập, set value, list) | bật bit trước khi ghi hoặc sau khi ghi; **không tự tắt** - phải tự OFF |

## User Security Level (Sách)
Cấp 0 = không cần đăng nhập. Không đủ cấp → hộp đăng nhập (hoặc Login screen riêng). *Set Low Security*: làm xong tự hạ về cấp 0.

## Macro (Sách)
**Before Execute Macro → hành động → After Execute Macro**. Nút bit còn có **On Macro / Off Macro** (mỗi lần chuyển trạng thái chạy một lần). Trạng thái đổi do PLC/macro khác thì **không** chạy macro. Tập lệnh macro nằm ở tài liệu macro riêng, không có trong sách này.

## Coord. (Sách)
X, Y, W, H là hằng số **hoặc địa chỉ** → dời/đổi cỡ phần tử lúc chạy.

## Thực tế `.dpa`

| Sách | Khoá | Ghi chú |
|---|---|---|
| Read/Write Address | `ReadVar` / `WriteVar` (+`ReadLink/WriteLink`, `ReadMemType/WriteMemType`) | `$205`, `$210.1`, `{EtherLink1}2@DB13.DBX1954.1` |
| Offset Address | `OffsetReadVar`, `OffsetWriteVar`, `OffsetMemLen`, `OffsetMemFmt` | chỉ có ở phần tử đời mới (xem dpa-khoa-theo-loai); chưa kiểm trên panel |
| Data Type / Format | `MemLen` (1 = Word, 2 = Double), `MemFmt` (2 = Signed Decimal 16-bit như ô hiển thị Silo; 5 = Floating) | Đã kiểm 30/09: donor 6.1 là REAL 2 word, chồng địa chỉ kế |
| Style | `Style`: **3 = Transparent** (ô số/chữ); nút Style 3 = không thân, chỉ ảnh | Đã kiểm |
| Transparency | `opacity` | chưa dùng |
| Invisible | `VisibleLink`, `VisibleVar`, `VisibleCondition` | nhiều phần tử đời cũ (Text 10.6, một số nút) **không có** `VisibleVar` → không thêm được bằng `Section.set` |
| Interlock | `InterLockLink`, `InterLockVar`, `InterLockLevel`, `InterLockViewMode` | clone chéo dự án phải set `InterLockVar=None` không thì nút chết. Đã kiểm |
| Min press | `PushTime` | |
| Confirmation | `ConFirmWindow`, `ConfirmScreenName/ID` | |
| Security | `Level`, `SetLowSecurity` | |
| Ignore op log | `IgnoreHistOP` | |
| Macro | `BeforeExecMacroLen`, `AfterExecMacroLen`, `ButtonOnMacroLen`, `ButtonOffMacroLen` (blob, độ dài gồm CRLF) | ghi được lệnh mở/đóng screen. Đã kiểm |
| Chữ | state: `wTextLen0/1`, `FontName0/1`, `FontSize0/1`, `FontRatio0/1`, `FontColor` (BGR), `FontBold/Italic/Underline`, `FontAlign` (bit: 1 trái 2 giữa 4 phải +32 giữa dọc → **33/34/36**) | cỡ **chẵn** (15 bị lưu thành 14). Đã kiểm |
| Ảnh | state: `PIB Name`, `Picture Name`, `PictureOffset` (DIAScreen tìm ảnh theo offset), `PictureCoordX/Y/Width/Height`, `PictureStretch`, `StretchMode`, `UsePictureCoord`, `TransEffect`, `TransColor` | Đã kiểm |
| Blink | state `Twinkles` | |
