---
name: diascreen
description: Tra cứu chuẩn Delta DIAScreen 1.6.1 (sách hướng dẫn 767 trang, đọc hết 30/09/2026) theo từng đối tượng - screen/popup, nút, hiển thị, nhập, chỉ thị/ảnh, danh sách/ComboBox/GridBox, đồng hồ/thanh/ống/biểu đồ, bàn phím, alarm, history buffer, recipe, bảo mật/tài khoản, cấu hình/Control Block, địa chỉ bộ nhớ ($, $M, *$, EM, tham số nội bộ), truyền thông/mã lỗi, biên dịch/mô phỏng/tải - kèm khoá .dpa thật và các bẫy đã kiểm. Dùng trước khi thiết kế hoặc lập trình bất kỳ đối tượng nào trên HMI Delta (DOP-100/300, DIAScreen/DOPSoft), khi hỏi "Delta làm được X không", "thuộc tính này ở đâu", "địa chỉ nào giữ khi mất điện". Phong cách giao diện xem skill delta-hmi-style.
---

# DIAScreen - tra theo đối tượng

Nguồn: `C:\OTL\SILO_Ban_Moi\1.Document\DELTA_IA_OSW_DIAScreen_V1.6.1_UM_ENG_20250929.pdf`
(767 trang). Mỗi file `references/` = phần sách về một nhóm đối tượng, viết lại gọn bằng
tiếng Việt, **cộng** phần "Thực tế" - khoá `.dpa` tương ứng và những gì đã kiểm trên dự án
thật / emulator.

## Cách dùng (đi song song với thực tế)

1. Làm đối tượng nào → mở đúng file trong bảng dưới **trước khi** chọn phần tử / đặt thuộc tính.
2. Mỗi mục có nhãn:
   - **Sách** - Delta nói vậy, chưa chắc bản `.dpa`/panel làm đúng y vậy.
   - **Đã kiểm** (kèm ngày) - đã chạy trên file thật / DIAScreen tự lưu / emulator.
   - **Chưa kiểm** - định dùng thì thử trên emulator (DOP-110WS Emulator) trước, rồi báo Sáng.
3. Sách và thực tế lệch nhau → **tin thực tế**, sửa file tham khảo: ghi rõ sách nói gì, thực tế ra sao, ngày.
4. Thử xong một mục "Chưa kiểm" → đổi nhãn thành "Đã kiểm dd/mm" trong file đó (skill này là tài liệu sống).
5. Phong cách (màu, lưới, thẻ, nút mặt ảnh) → skill `delta-hmi-style`. Định dạng file và cách ghi → `DeltaDpa_src/docs/kien-thuc-dpa.md`.

## Bảng tra

| Đang làm | Mở |
|---|---|
| Screen thường / base screen / sub-screen (popup) / keypad screen / xác nhận / đăng nhập / tài khoản / template / in | `references/screens.md` |
| Thuộc tính chung mọi phần tử: đọc/ghi, offset, style, chữ, ảnh, interlock, **ẩn theo bit**, xác nhận, bảo mật, macro trước/sau, toạ độ động | `references/element-common.md` |
| Nút: Set ON/OFF, Momentary, Maintained, Checkbox, Multistate, Set Value/Constant, Tăng/Giảm, Goto Screen, **Multiple Actions**, nút hệ thống | `references/buttons.md` |
| Ô số, ô chữ, ngày/giờ/thứ, Message Display, Moving Sign, QR, Barcode; Gain/Offset, đổi đơn vị | `references/display.md` |
| Numeric/Character Entry, Barcode, Multi-language Input, Multi-line Text; giới hạn, trigger, chế độ nhập | `references/input.md` |
| Multistate/Range/Simple Indicator; State Graphic, Animated Graphic, GIF, Real-time Image | `references/indicator-graphic.md` |
| ComboBox, Drop-down, ListBox, **GridBox**, PDF/Text Viewer, File Browser, Picture Viewer, Text List, FTP list | `references/lists.md` |
| Meter, Bar, Pipe, **Flow Block**, Pie, Trend Graph, X-Y Chart/Distribution, Curve Input | `references/gauges-charts.md` |
| Keypad element, bàn phím chung, bàn phím tự làm | `references/keypad.md` |
| Alarm: cài đặt, địa chỉ liên tục/rời, tin nhắn động %d/%f/%s, màn hình alarm, bảng/moving sign, gửi mail/LINE | `references/alarm.md` |
| History Buffer, Historical Trend/Data/Event/Overview/Circular, xuất CSV | `references/history.md` |
| Recipe 16/32-bit, **Enhanced Recipe (tên công thức Unicode)**, RCP/ENRCP…, Recipe Viewer | `references/recipe.md` |
| Tài khoản/cấp bảo mật 0–10, mật khẩu cao nhất, đăng nhập bằng tham số nội bộ, Operation Log | `references/security-oplog.md` |
| Configuration: macro chu kỳ, lưu khi mất điện, screensaver, **Control/Status Block** (PLC chuyển màn hình…), RTC, mặc định, boot, mạng/VNC/FTP/SMTP, đa ngôn ngữ, electronic record | `references/configuration.md` |
| Địa chỉ: `$`, `$M` (giữ khi mất điện), `*$` gián tiếp, EM, **tham số nội bộ** (tài khoản, USB, mạng, giờ, VNC…), địa chỉ PLC, Tag/UDT | `references/addresses.md` |
| COM/Ethernet, tham số chung, **mã lỗi truyền thông** (cả S7), Modbus slave mapping, EIP | `references/communication.md` |
| Biên dịch, mô phỏng online/offline, Monitor IO, tải/xuất file màn hình, firmware, kho ảnh/chữ/phông, đa ngôn ngữ, Duplicate, Scheduler, Address Conversion, Change Model, Environment, trả góp, in, OPC UA/MQTT/Cloud | `references/project-tools.md` |
| Menu hệ thống trên panel, HMI Doctor | `references/system-menu.md` |
| Khoá `.dpa` thật theo từng loại (mã 1.1…19.10) | `references/dpa-khoa-theo-loai.md` |

## Mười điều hay cần nhất (tóm tắt, chi tiết trong file)

1. `$` mất khi tắt nguồn; **`$M0..$M4999` giữ** khi mất điện → tên bồn / tên công thức HMI tự giữ thì để ở `$M`. (addresses)
2. Mọi phần tử có **Invisible Address + Invisible State** (ẩn/hiện theo bit) và nhiều loại có **Interlock** (khoá thao tác, hiện biển cấm). (element-common)
3. **Read/Write Offset Address**: địa chỉ thật = địa chỉ + giá trị ô offset × cỡ kiểu dữ liệu → hiện phần tử thứ n của mảng mà không cần PLC chép. Chưa kiểm với Character Display. (element-common)
4. **Multiple Actions** button: tới 32 thao tác cho nhấn / nhả / nhấn giữ (Set, Constant, Goto, Delay…); macro của nút bị bỏ qua. (buttons)
5. Goto Screen lấy số màn hình **từ địa chỉ** được; PLC đổi màn hình qua **Control Block – Screen No.**; Status Block trả màn hình đang mở. (buttons, configuration)
6. ComboBox chỉ lấy mục gõ sẵn (mỗi state một chữ); danh sách chữ lấy từ địa chỉ → **GridBox** cột String hoặc popup tự dựng. (lists)
7. **Enhanced Recipe** có tên nhóm Unicode (`ENRCPGNAME`), đổi được trên HMI qua Multi-language Input. (recipe)
8. Ô nhập có Min/Max theo kiểu dữ liệu; Word signed −32768..32767; "số lẻ" chỉ là định dạng trừ khi Floating (Double Word). (input)
9. Macro trước/sau chạy khi **người bấm**; nút bị PLC/ macro khác đổi trạng thái thì macro không chạy. Tập lệnh macro **không có trong sách này** (tài liệu macro riêng của Delta). (element-common)
10. Mã lỗi truyền thông 0x03 NoResponse, 0x06/0x07 sai lệnh/địa chỉ, 0x20 LinkBroken, 0x24 >16 kết nối; khi ghi thì OR 0x40. (communication)
