# Configuration (General > Configuration, sách tr.68–160)

## Main (Sách)
- Tên dự án, model; **Clock Macro Delay Time 50–65535 ms (mặc định 100)** + priority; Background macro: số dòng mỗi chu kỳ 1–512; LUA delay/priority.
- **Non-volatile data storage** cho Alarm / Recipe / History: HMI / USB / USB2 / SD; *write cache size* cho USB/SD (dữ liệu chờ trong cache, mất điện có thể mất → bật định kỳ **General Control b5** để ép ghi).
- **Global Keypad Settings** → `keypad.md`.
- System Setting: con trỏ cảm ứng, *hiện màn khởi động mỗi lần bật*, tự dò baud, giữ file LUA khi tải, **Pre-read invisible bit** (tránh nháy khi ẩn theo địa chỉ PLC, chậm chuyển trang), **Use terminator `\0`** cho chuỗi, **Watchdog** (treo tự khởi động lại), tắt cảnh báo pin yếu, **Retain historical data after screen update**, **Keep account/password table after download**, giữ dữ liệu trả góp, chế độ USB tải (Auto/Disk/CDC/None), ưu tiên chạm, gateway mặc định, độ sáng, TP Delay/Force, còi, âm phím, Animation FPS.
- Screensaver: bật sau 1–100 phút, tiết kiệm đèn nền, **trigger address** (0 tắt/1 bật), sau khi thoát về trang cũ hoặc trang chỉ định.
- Others: báo lỗi truy cập USB/SD, màn hình cảnh báo khi dung lượng còn ít, video overlay.

## Control Block (Sách) - PLC điều khiển HMI
Chọn mục nào thì địa chỉ xếp liên tục từ trên xuống (hoặc *discontinuous* tự đặt từng cái); *Auto Reset Flags*; Data Format; Sampling Cycle 100–1000 ms.

| Thanh ghi | Bit |
|---|---|
| **Screen No.** | ghi số screen → HMI chuyển trang |
| **General Control** | b0 bật/tắt truyền thông (khôi phục sau khi tự ngắt), b1 đèn nền, b2 còi, b3 xoá bộ đệm alarm, b4 xoá bộ đếm alarm, b5 ép ghi cache USB/SD, b6 khoá eRemote, **b8–b11 đặt cấp người dùng** (b11 = cao nhất) |
| Curve Control | b0–b3 lấy mẫu đường 1–4, b8–b11 xoá |
| Recipe Control / Number | b0 đổi số, b1 đọc PLC→HMI, b2 ghi HMI→PLC, b3 đổi nhóm, b8–b15 số nhóm |
| System Control | **b0–b7 ngôn ngữ** (≤32), b8 in, b9 đẩy giấy, b10–b12 xin lại IP (LAN1/LAN2/Wi-Fi) |
| Enhanced Recipe Control | như Recipe Control cho ENRCP |
| Advanced Level Access Control | b0–b3 cấp, b15 cao nhất (bật thì General b8–b11 vô hiệu) |

## Status Block (Sách) - HMI báo lại
Cần có Control Block (địa chỉ khác nhau). General Control Status (b0 **đang chuyển trang**, b3/b4/b5 đang xoá/ghi, b8–b11 cấp hiện tại), **Screen No. Status** (trang đang mở), Curve/Recipe/System/Enhanced Recipe status, cấp truy cập.

## Real Time Clock (Sách)
Đồng bộ giờ PLC ↔ HMI: link, station, hướng (PLC→HMI hoặc ngược), trigger Timer 1–1440 phút / Bit On / Bit Off, Start Address + Length 1–7 (giây, phút, giờ, ngày, tháng, năm, thứ); Delta PLC dùng D1319–D1313; *Sync time from PC* khi tải. Tham số nội bộ `TIME_YEAR…TIME_SECOND`.

## Default (Sách)
**Default Boot Screen**, định dạng số mặc định (Unsigned Decimal), màu nền mặc định, thời gian hiện lỗi hệ thống 0–5 s, **System Key Mode** (tắt / đòi mật khẩu `12345678` / không đòi), **System Default Font** (Verdana) + Fallback Font, *Faster HMI page changing*, *Reduce font size* (chỉ tải phông đang dùng), chữ tự xuống dòng, màu chữ, cỡ thanh cuộn 20–60, **chu kỳ nhấp nháy 500–5000 ms**, *thứ tự cập nhật khi chuyển trang* (hiện trước rồi đọc / đọc trước rồi hiện), kiểu tô mặc định (Gradient), **Font smoothing**, tự giãn theo chữ.
Boot Logo (ảnh từ Picture Bank, <3 MB), Boot Delay Screen 0–255 s (chờ PLC khởi động).

## Network Settings (Sách)
Tên HMI, cổng tải 12346, Modbus TCP server 502, múi giờ, **NTP**, LUA debug, eComm, One Wire; eServer/eRemote (cổng 12348, mật khẩu mạnh); **VNC** (5900; web 5800; multi ≤64; chỉ xem); Real-time Monitoring qua web `http://[IP]/RemoteMon/`; **SMTP** (mail alarm; Gmail cần app password); **FTP** (cổng 21, admin/1234 ví dụ; anonymous chỉ đổi tên); FTP File Setting (client, nhiều trigger + mã trả về); MAC Settings (khoá file màn hình theo MAC).

## Multi-language (Sách)
≤32 ngôn ngữ; dòng đầu là mặc định (không tắt được); Default Font Style theo ngôn ngữ; ngôn ngữ hệ thống (6). Đổi bằng System Control b0–b7 hoặc nút Language Change.

## Industry Application (Sách)
Electronic record: ghi thao tác / alarm / lịch sử / lỗi truyền thông vào CSV có checksum; bật *Second confirmation of account*.

## Thực tế `.dpa`
- `[Application]` có `DefaultScreen`, `CtrlScreenVar`, `StatusScreenVar`, `ScreenBkColor`, `LoginScreenID0..7`, `PwdKeypadScreenID`… (đọc từ HMI_Silo 30/09). Chưa sửa khoá nào ở đây.
- Silo đang để mặc định; chuyển trang từ PLC (Screen No.) chưa dùng.
