# Menu hệ thống trên panel (sách tr.731–765)

Vào: **giữ chỗ trống trên màn hình >3 giây** → thanh bên trái: Settings, Monitor, Capture (ảnh `screen_capture\hhmmss.png`), Export (gói debug vào `HMIData`), Close.

| Mục | Nội dung |
|---|---|
| MISC | ngôn ngữ hệ thống, con trỏ, thời gian screensaver, boot delay, **ngôn ngữ mặc định** (ID − 1 = index), hiện màn khởi động, chế độ USB (CDC/DISK/NONE), gateway, bật/tắt ổ USB |
| File Manager | **Format** (HMI cần mật khẩu cao nhất - xoá màn hình), **File Copy** (chép màn hình ra/vào USB/SD), **Firmware Update**, **File Encryption** (giới hạn số lần copy) |
| Display / Date-Time | độ sáng; giờ (cũng mở được bằng nút 12.4 / 12.1) |
| Touch Panel | Delay, Force, **Calibration 5 điểm** (dùng bút) |
| Network | LAN: DHCP / Static / BOOTP, mask, gateway, DNS, MAC; Wi-Fi (khi có dongle) |
| Network App | VNC (không mật khẩu / multi / view only / cổng / TLS), eServer, SMTP, FTP |
| COM Port | multi-link, chế độ, delay, timeout, retry |
| Audio | còi, âm phím, âm khởi động |
| Password | bảng tài khoản (≤1000 mỗi cấp), Restore Default Security Level |
| Up/Download | Standard (COM), **Bypass** (COM1↔COM2 chuyển tiếp), **Transfer**: nạp chương trình PLC Delta (.isp) hoặc CODESYS (.app) từ USB |
| System Info | firmware, model, pin, Flash, CPU, giờ, PLC driver |
| HMI Doctor | test màu LCD, vẽ đường (lệch → hiệu chỉnh cảm ứng), còi, ADC (lực nhấn, X/Y, điện áp, pin, nhiệt), mạng |

Chế độ phím hệ thống (tắt / đòi mật khẩu) đặt ở Configuration > Default > System Key Mode.
