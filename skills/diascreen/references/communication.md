# Truyền thông (sách tr.161–169, 208–218, phụ lục mã lỗi)

## COM Port (Sách)
Connection + Link Name + thiết bị; HMI Station 1–255; Interface: **COM1 chỉ RS232**, COM2/COM3 RS232/422/485; data/stop bits, baud, parity.

## Ethernet (Sách)
Mỗi cổng: ≤4 loại controller, ≤16 link mỗi controller; Controller IP cùng dải; COM Port (cổng TCP) tuỳ controller. Localhost: **Overwrite IP** (tải xuống thì ghi đè IP HMI), DHCP, IP/Mask.

## Tham số chung (Sách)
PLC Station 0–255, Password (mặc định 12345678), **Comm. Delay 0–255**, **Connection Timeout 10–2000 ms (1000)**, **Connect Retries 0–15 (2)**, **Optimize** (gộp đọc), COMMGR simulation (mô phỏng offline với PLC giả), **Disconnect after communication interrupt** + retries 0–255 (khôi phục bằng Control Block General b0). Thiết bị nhập (barcode): Read length 10–1024, terminator, timeout.

## Mã lỗi (Sách, phụ lục)

| Mã | Tên | Nguyên nhân / xử lý |
|---|---|---|
| 0x02 | Unknown | nhiễu - chống nhiễu, bọc cáp |
| **0x03** | NoResponse | timeout; sai dây, station, baud/parity/bits |
| 0x04 / 0x05 | CheckSum | nhiễu / PLC bật checksum |
| **0x06 / 0x07** | Command / Address Error | địa chỉ vượt vùng PLC hoặc không ghi được |
| 0x08 | ValueError | giá trị ghi ngoài phạm vi PLC |
| 0x09 | Controller busy | thử lại |
| 0x0A | NoCTS | chân CTS/RTS |
| 0x0B / 0x0C | NoResource / NoService | PLC quá tải |
| 0x0D | MustRetry | chờ gửi lại |
| 0x0E / 0x0F | Station Error | trùng/sai station |
| 0x10 | UARTCommunicateFail | cổng COM mở sai / HMI quá tải (bớt alarm, macro) |
| 0x1A | RTCSYNCError | PLC không hỗ trợ đồng bộ giờ |
| 0x1B | Receive Error | dữ liệu PLC sai định dạng |
| **0x20** | LinkBroken | mất TCP - kiểm cáp, PLC có nhận kết nối |
| 0x21 | TransIDError | lệch thứ tự gói - khởi động lại HMI |
| 0x22 | NoConnection | cắm lại cáp |
| 0x23 | GatewayPathUnavailable | gateway |
| **0x24** | LinksFull | >16 kết nối |
| 0x2F / 0x3F | ExceptionCode / OtherError | mã ngoài chuẩn Modbus / địa chỉ không hợp lệ |

**Khi ghi**: mã OR 0x40 (vd ValueError 0x08 → 0x48).
Siemens MPI/S7-200/300: 0x11 MPI_IDLE, 0x12 trùng station, 0x14 hết chỗ kết nối, 0x18 không phản hồi, 0x3F Read Error (địa chỉ vượt). Omron C/CPM: 0x1F (PLC ở Run, HMI tự chuyển Monitor). Delta CNC: 0x25–0x28.

## HMI làm Modbus Slave (Sách)
Project > Other Settings > Modbus TCP/COM Mapping Table: TCP coils/registers 0..65535; COM coils 1..2048, registers 40001..60000. Ví dụ `$4000.0` ↔ coil 0x0000, `$5000` ↔ register 0x0000.

## EIP Data Exchange (Sách)
Chỉ DOP-300; ≤6 bảng; nhập EDS hoặc CIP tay; RPI 5–1000 ms; ≤200 byte đọc/ghi.

## Thực tế
- Silo: `EtherLink1: S7 1200 (ISO TCP) @192.168.0.1` (đọc bằng MCP `open_project`).
- S7 qua Delta: địa chỉ dạng `{EtherLink1}2@DB13.DBD2456` (DB phải **không tối ưu**). Chuỗi S7 STRING có 2 byte đầu - xem `display.md`.
