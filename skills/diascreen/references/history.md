# History Buffer (sách tr.547–579)

## Bộ đệm (Data Management > History Buffer) (Sách)

- Tối đa **40** buffer. Mỗi buffer: Address, **Read Length ≤256 word**, **Sample Number ≤9 999 999**, Enable active bit (bật mới lấy mẫu), Stamp Time/Date.
- Trigger: **Timer** (Sampling Cycle 100–86 400 000 ms hoặc Custom Cycle từ địa chỉ, ≤32767 / DWORD ≤2 147 483 647) hoặc **Memory Address** (bit ON thì lấy mẫu).
- Data Clearing bit, Status Block bit, **Non-volatile** HMI/USB/SD, **Auto Stop** (đủ mẫu thì dừng, không thì ghi vòng), **Export CSV** (tiêu đề ≤20 cột × 10 dòng, định dạng từng cột; Length 1 hoặc 2 word; Char), **File storage** một file (tên ≤8 ký tự) hoặc nhiều file `Tên_Ngày_Giờ` (không đi cùng Auto Stop).
- *Continuous historical buffer control command address*: một vùng bit liên tục điều khiển lấy mẫu/xoá của mọi buffer (Data Sampling, Data Clearing, trạng thái, Auto Reset Flags, chu kỳ 100–1000 ms).
- CSV mặc định: `HMI\HMI-000\History\CSV\H0001.csv`.

## Phần tử (Sách)

| Phần tử | Ghi chú | Mã |
|---|---|---|
| **Historical Trend Graph** | ≤60 đường; global range hoặc từng đường (Enable có thể là bit, Length, Start Position, format, màu, dày 1–8, min/max hằng/địa chỉ, **Write Address** giá trị tại vạch dò), đường cao/thấp, lưới ≤50, fill dưới đường, monitoring line, trục thời gian + zoom | **9.1 / 12.15** |
| Historical Data Table | ≤60 cột, định dạng từng cột (>2 word chỉ Char), tiêu đề, số thứ tự, sắp xếp | **9.2** |
| Historical Event Table | giá trị → chữ theo state (Word 256 / LSB 16) | |
| Historical Overview Table | duyệt file `.dat` trên USB/SD + đồ thị | |
| Circular Trend | đồ thị tròn 1–24 h/vòng, ≤8 đường, một cái mỗi screen | |

Nút chức năng: Zoom In/Out/Reset, cuộn, khoảng thời gian.

## Thực tế
- Trend clone chéo dự án cần `[History]` khai buffer (`HistoryCount`, `ReadVar01`…), không thì compile lỗi `Element buffer is undefined`. Đã gặp 29/09.
- Configuration > *Retain historical data after screen update*: giữ dữ liệu khi tải lại màn hình, nhưng đổi Read Length/Sample Number/Stamp/Non-volatile/CSV/kiểu file thì vẫn mất.
- **Trend chạy không cần PLC (Đã kiểm emulator 30/09)**, mẫu `DeltaDpa_src/build_test_trend.py`: đổi mọi địa chỉ PLC của trend sang `$` nội bộ, macro chu kỳ 1 s của screen tự sinh số liệu.
  - Chạy/dừng = **Enable active bit** của buffer: ON lấy mẫu, OFF dừng tại chỗ, đường đã vẽ giữ nguyên.
  - Xoá = **Data Clearing bit**: xoá theo **sườn lên**, HMI **không tự hạ cờ** → macro phải hạ về 0, không thì bấm lần hai chỉ ghi 0. Hạ ngay trong cùng lượt macro thì HMI có lúc hụt sườn (bấm 2 lần mới xoá 1) → giữ cờ trọn một lượt (1 s) rồi mới hạ.
  - Nút ghi **địa chỉ bit** phải `MemLen=0`; để 1 như nút word là compile lỗi `Element address input error`.
