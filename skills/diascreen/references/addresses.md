# Địa chỉ (sách tr.673–730)

## Bộ nhớ trong (Sách)

| Loại | Phạm vi | Giữ khi mất điện |
|---|---|---|
| `$n`, `$n.b` | `$0..$199999`, bit `.0..15` | **Không** |
| **`$Mn`**, `$Mn.b` | `$M0..$M4999` | **Có** |
| `*$n` / `*D$n` gián tiếp | lấy giá trị `$n` làm địa chỉ (`$10=101`, `$101=55` → `*$10=55`); >65535 dùng `*D$` | Không |
| `EM0..EM15` | mỗi EM là một file `.emi` trên USB/USB2/SD, ≤512 MB, word tới 268435455 | Có (trên thẻ) |
| Recipe: `RCP RCPNO RCPG *RCP ENRCP ENRCPNO ENRCPG ENRCPGNAME *ENRCP` | xem `recipe.md` | tuỳ loại |

EM đặt tên file ở Project > Other Settings > Extended Memory Settings; LUA đọc/ghi bằng `mem.em.Read/Write/ReadDW/…/ReadASCII/WriteASCII`. Trạng thái `StatusEM0..15` (0 xong, 1 đang ghi, 2 không có ổ, 3/4 lỗi ghi/đọc).

## Tham số nội bộ (Internal Parameter, chỉ phần tử Word) (Sách)

| Nhóm | Tham số |
|---|---|
| Hệ thống | `BATTER_VOLTAGE`, `LANG_OF_SYSMSG` (0 Anh…6 Thổ), `SP_BRIGHT`, `SYS_BUZZER_VOLUME`, `BTN_BUZZER_VOLUME`, `BOOT_BUZZER_VOLUME`, `FW_VERSION1/2` (Hex), `HardwareID` (Character Display 32) |
| Tài khoản | xem `security-oplog.md` |
| Alarm | `ALARM_COUNT` |
| Truyền thông | `NET_STATUS1..4` (Binary: mỗi bit = một kết nối của controller 1..4) |
| Giờ | `TIME_YEAR/MONTH/DAY/HOUR/MINUTE/SECOND` |
| Ethernet | `NET1_IP1..4`, `NET2_IP…`, `SUBMASK…`, `GWAY…`, `DNS…`, `NET_MAC1..3` |
| Ứng dụng mạng | `SMTP_STATUS/INFO`, `REMO_COUNT`, `VNC_ENABLE`, `VNC_STATUS_ENABLE`, `VNC_NOPASSWORD`, `VNC_VIEWONLY`, `VNC_MULTI_CONNECT`, `VNC_PASSWORD`, `VNC_PORT`, `InternetConnStatus` |
| Thiết bị nhập | `InputDevID`, `InputDevConnStatus`, `InputDevData(Len)`, `InputDevClear`, `InputDevInProgress`, `InputDevStatus` |
| Trả góp | `NEXT_INST_REMAIN_TIME` (chuỗi 23), `INST_LOCK_STATUS` |
| IoT (DOP-300) | `IoTNotify`, `IoTDeviceStatus`, `IoTEnable`, `IoTPairingKey`, … |
| Bàn phím | `KEY_CHAR` |
| LUA | `PROGRAM_STATUS`, `PROGRAM_INFO` |
| MQTT | `MQTTClientID`, `BrokerNumber`, `BrokerInfo` |
| Lưu trữ | `SD_STATUS`, `USB_STATUS`, `USB2_STATUS` (0 không có / 1 có) |
| Cảm ứng | `TP_STATUS`, `TP_X`, `TP_Y`, `TP_FORCE`, `TP_DELAY` |
| Wi-Fi | `WiFi.*` |

## Địa chỉ PLC (Sách)
Device Communication đặt Link Name → trong hộp địa chỉ chọn Link, bỏ Default để đặt Station. Controller có nhập biến (AB, Beckhoff, **Siemens**, Omron, CODESYS…) thì chọn **Tag**; tìm theo từ khoá, cấp dưới bằng dấu cách, mảng chọn chỉ số, bit chọn trong danh sách.

## Tag / UDT (Sách)
≤6000 tag; tên ≤220 byte, không bắt đầu bằng số, không dùng `. [ ] @`, cùng ngôn ngữ hệ điều hành; kiểu BOOL, INT, DINT, LINT, WORD, DWORD, LWORD, REAL, LREAL, UINT, UDINT, ULINT, **STRING ≤128 byte**, WSTRING ≤256; UDT Structure/Array (tên ≤32, không ký tự đặc biệt). Nhập/xuất xlsx/csv. DIA Tag đồng bộ từ DIADesigner / DIADesigner-AX.

## Thực tế `.dpa`
- Dạng chuỗi: `$205`, `$210.1`, `{EtherLink1}2@DB13.DBX1954.1` (link, station, địa chỉ S7). Silo nối `EtherLink1: S7 1200 (ISO TCP) @192.168.0.1`.
- Mọi địa chỉ tạm của Silo đang ở `$` (mất khi tắt nguồn) - đủ cho thử; **tên bồn/tên công thức nếu HMI tự giữ thì phải chuyển sang `$M`**.
- Đổi hàng loạt địa chỉ: MCP `rebind(old, new)` (mặc định chạy thử) hoặc Tools > Address Conversion.
