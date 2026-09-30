# Công cụ dự án (sách tr.20–44, 170–228, 613–672)

## Tạo dự án (Sách)
Project Wizard: Series → HMI → tên dự án/tên + số screen đầu + **mật khẩu cao nhất** (mạnh) → Next (truyền thông) / Finish. Mẫu: Full-featured, Industry, CODESYS, **Small kit (StartUp/Template - chép screen sang dự án khác bằng Ctrl+C/V trong Screen Management)**. Đường dẫn mẫu `C:\ProgramData\Delta Industrial Automation\HMI\DIAScreen (version)\ScrEditApp\Example\`.

## Biên dịch / tải (Sách)
- **Compile** (Ctrl+F7, chỉ screen đang sửa), **Compile All** (lỗi hiện ở Output, bấm để nhảy tới phần tử).
- **Download All Data** (Ctrl+F8: màn hình + recipe), **Download Screen** (Ctrl+F9), Upload All Data (cần mật khẩu cao nhất; *Include picture data when uploading* ở Environment, không thì mất ảnh).
- **On-line Simulation** (Ctrl+F4): PC làm HMI nói chuyện PLC qua COM; chuột phải → **Monitor IO** (xem/sửa giá trị địa chỉ lúc chạy).
- **Off-line Simulation** (Ctrl+F5): kiểm màn hình, địa chỉ, macro không cần PLC. Emulator: `ScrEditApp\Emulator\100_Series\...\HMIApp.exe`.
- Transmission: Upload/Download Recipe (.rcp/.csv), Download Boot Screen, Update Firmware, Get Firmware Info, **Reset HMI** (xoá hết), Reset Default Boot Screen.

## File màn hình (Sách)
Create Screen Data File / Auto Update (`HMI_AutoUP` trên USB/SD, cắm vào là hỏi cập nhật cả firmware), mật khẩu copy, khoá MAC; **Create Download Screen Executable** (`DownloadScreen.exe`, không cần DIAScreen); Create Screen Auto Execution File (`HMIEmulator.exe` chạy màn hình trên PC).

## Kho và phông (Sách)
- **Picture Bank**: thêm kho, mở kho dự án khác, nhập bmp/jpg/gif/ico/png/emf/svg, xuất bmp, đảo màu, xám 256, lật, bão hoà. Kho người dùng ở `C:\ProgramData\Delta Industrial Automation\HMI\Common\Pic`.
- **Text Bank**: chữ dùng chung (nhiều state, đa ngôn ngữ), nhập/xuất .tbk/.txt/.xlsx; phần tử dùng Text Bank thì *Replace* không đụng.
- **Font Management**: đổi phông hàng loạt; **Font Template** ≤100 mẫu (lưu trên máy, dùng chung mọi dự án; `Common\FontTemplate.xlsx`), Text Bitmap/Font.

## Ngôn ngữ (Sách)
Language Management: xuất/nhập chữ đa ngôn ngữ (có/không kèm phông) ra Excel, **Copy Multi-Language Font** từ ngôn ngữ nguồn sang đích.

## Sửa hàng loạt (Sách)
- **Duplicate**: nhân X×Y, khoảng cách, **tăng/giảm địa chỉ theo offset** (Word hoặc bit), chỉ số mảng tag, tự đánh số chữ.
- **Address Conversion**: xem/sửa mọi địa chỉ của phần tử chọn, tìm-thay, tự dời theo offset.
- **Change Model**: đổi model/xoay màn hình; mở được dự án DOP-B/W/H và chuyển sang DOP-100.
- **Scheduler**: ≤3 lịch ghi giá trị định kỳ / giờ cố định.

## Environment (Sách)
Thư mục output (CIN), ngôn ngữ giao diện, kiểu tải USB (Auto / Disk / CDC / None) hoặc Ethernet (cùng dải IP) hoặc COM, **AutoSave 3–120 phút**, mở lại dự án cuối, kèm ảnh khi upload, tự đổi địa chỉ thành tên tag, tự khởi động lại sau cập nhật firmware, giữ mạng khi reset, cài lại driver USB/NIC ảo, **dấu phân cách CSV**.

## Trả góp (Installment) (Sách)
Khoá HMI theo kỳ trả tiền: màn hình mở khoá (Drop-down nguồn *Installment Period*), mật khẩu tĩnh/biến, ≤10 khách, ≤32 kỳ, nhắc trước 0–15 ngày; khi bật thì **khoá mọi cách chỉnh giờ**; pin hỏng về 1970 là khoá máy. Bảo vệ dự án bằng *Check password when downloading* + *Screen upload prohibited*.

## In (Sách)
Máy in Honeywell/HP/EPSON/ZEBRA/GoDEX/Micro/PDF Writer/**ePrinter** (PC chạy `PrnServer.exe`, cổng 85); Print Screen riêng; mã lỗi in −2..−14; Template Screen xuất PDF.

## IIoT (Sách)
- **OPC UA Client** (nhập tag từ file XML/CSV hoặc từ server), **OPC UA Server** (cổng 4840; DOP-110WS có hỗ trợ), bảo mật chính sách/tài khoản (DOP-300).
- **MQTT**: ≤5 broker, publisher/subscriber ≤100 topic, topic có biến `%0` HWID `%2` random, JSON thường/nâng cao (DOP-300), Will Message, địa chỉ trạng thái/điều khiển, Azure IoT Hub / Aliyun / AWS.
- DIACloud (DOP-300).

## Thực tế
- Tự động hoá không qua GUI: `DeltaDpa_src` (thư viện `.dpa` + MCP `delta-dpa`) - DIAScreen **không có API/dòng lệnh** ngoài mở file. Tự lưu trong editor: `PostMessage WM_COMMAND 0xE103`.
- Compile/mô phỏng vẫn phải bấm trong DIAScreen (chưa tự động được).
