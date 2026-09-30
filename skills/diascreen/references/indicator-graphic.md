# Chỉ thị và đồ hoạ (sách tr.304–316, 341–354)

## Indicator (Sách)

| Phần tử | Việc | Mã |
|---|---|---|
| **Multistate Indicator** | style/chữ/ảnh theo state của địa chỉ; Bit 2, Word 1–256, LSB 16, LSB(+0) 17 | **2.1** |
| Range Indicator | state theo **khoảng giá trị** (1–256 khoảng); giới hạn hằng số hoặc lấy từ địa chỉ (liên tục hoặc từng cái) | |
| Simple Indicator | ON/OFF bằng màu XOR; *Redraw* khi đè lên phần tử động | |

LSB: lấy bit khác 0 thấp nhất (3 = 0b11 → state 1).
Chung: Style Standard/Raised/Round/Invisible, Blink, Transparency, Batch Multistate Setting, chữ/ảnh theo state, Invisible Address, Coord động.

## Graphic (Sách)

| Phần tử | Việc | Mã |
|---|---|---|
| **State Graphic** | ảnh theo state; *Auto Picture Change* (No / Yes: khác 0 thì tự lật ảnh theo chu kỳ / Variation: Read+1 điều khiển) | **7.1** |
| Animated Graphic | ảnh theo state **và di chuyển**: Read+1 = X, Read+2 = Y; *Clear Picture* | |
| Real-time Image | nhận ảnh từ PC qua `Utility\ImgTrans\TestTransfer.exe` (LAN/COM) | |
| GIF Viewer | địa chỉ trạng thái (0 dừng/1 tạm/2 chạy), control address, vòng tự động 1–200 lần | |

Chung: Read Address Word, Data Type/Format/State Counts, Foreground, Transparent, Transparency, Picture (Stretch, Transparent Color), Invisible, Coord động.

## Thực tế `.dpa`

- 7.1 State Graphic dùng cho van (Van_Off/Van_On) và dấu tick; `ReadVar`, ảnh theo state. Ảnh chừa lề **3 px hai bên, 0 trên dưới** (khác Rectangle 4/1) → `frame.picture_rect` tự bù. Đã kiểm 29/09.
- Đường kẻ có ảnh sót thì xoá hẳn khoá Picture* (DIAScreen tìm ảnh theo `PictureOffset`). Đã kiểm.
- 2.1 Multistate Indicator có `VisibleVar` → ẩn/hiện theo bit được. Chưa dùng.
- Muốn dòng "trạng thái" đổi chữ theo mã lỗi mà không cần PLC gửi chuỗi → Multistate Indicator (Word, tối đa 256 state) hoặc General Message Display (1000 state). Chưa kiểm.
