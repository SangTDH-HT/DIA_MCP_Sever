# Nút (sách tr.230–261)

## Các loại (Sách)

| Nút | Hành vi | Mã `.dpa` |
|---|---|---|
| Set to ON / Set to OFF | đặt bit ON (OFF), bấm lại vẫn giữ | 1.? / **1.2** Set to Off |
| **Momentary** | nhấn đảo bit, nhả trả lại | **1.1** |
| **Maintained** | mỗi lần bấm đảo bit | **1.3 / 1.4** |
| Checkbox | như Maintained, vẽ ô tick | **1.16** |
| **Multistate** | mỗi lần bấm sang state kế (Next / Previous State); Bit 2 state, Word 1–256, LSB 16, LSB(+0) 17 | **1.5** |
| Set Value | hiện bàn phím, ghi số | |
| **Set Constant** | ghi hằng số (`SetValue`) | **1.7** |
| Increment / Decrement | cộng/trừ bước (`StepValue`), dừng ở giới hạn (`LimitValue`) | **1.8 / 1.9** (suy từ khoá, chưa kiểm) |
| **Goto Screen** | chuyển tới screen chỉ định **hoặc screen lấy từ địa chỉ**; Previous Page; Page Up (lịch sử trang) | **1.10** |
| System Date and Time, Password Table, Enter Password, Contrast Brightness, Set Low Security, System Menu, Language Change | nút hệ thống | 12.1, 12.2, –, 12.4, 12.5, 12.6, 12.12 |
| Print Output, Report List (alarm → CSV), **Template Output** (PDF), Screen Capture, Remove Storage, Import/Export Recipe, Calibration (5 điểm cảm ứng), Import/Export FileSlot, Import/Export Contact, Import/Export Account, Enable Next Installment, Timezone | chức năng | |
| **Multiple Actions** | tới **32 thao tác** cho mỗi: nhấn / nhả / nhấn giữ (thời gian giữ đặt được) | |

## Thuộc tính riêng (Sách)

- Bit button: **On Macro / Off Macro** chạy mỗi lần chuyển trạng thái.
- Multistate: Data Type, Format, State Counts, Sequence; *Batch Multistate Setting* tô hàng loạt state.
- Numeric value button: Data Type Word/Double/Quad; Format BCD…Floating; Value; **Trigger Before/After Writing** (bit trigger không tự tắt).
- Multiple Actions: thao tác gồm Set ON/OFF, Maintained, Multistate, Set Constant, Increment/Decrement, Goto Screen, Set Low Security, System Menu, Report List, Screen Capture, Remove Storage, Import/Export Recipe, Language Change, **Delay**. Luật: System Menu chỉ được là thao tác cuối; **chỉ một** thao tác đổi trang (Goto hoặc Previous) mỗi nút; **macro của nút này bị bỏ qua**.
- Report List: alarm phải lưu non-volatile + Export CSV = Yes; file ở `\HMI\HMI-000\@HMI0000\HistoryOp\CSV`.
- Template Output: Report (separate) / Reports (Batch); tên file lấy từ địa chỉ; PDF ở `\HMI\HMI-000\@HMI0000`.

## Thực tế `.dpa`

- Goto: `GoToScreenName` (chữ thường, không phải blob) + `GoToScreenID`, `CloseScreen` (=1 vẫn KHÔNG đóng popup mở bằng macro `OPENSCREEN` - thấy trên emulator 01/10: danh sách chọn bồn nằm lại trên trang Cài đặt; Screen Open/Close macro cấm `CLOSESUBSCREEN` (−83) nên phải đặt Before Execute macro `CLOSESUBSCREEN n` trên từng nút Goto: `DeltaDpa_src/close_popups_on_leave.py`, chạy CUỐI chuỗi script), `Variation` (0 = screen cố định; khác 0 = lấy từ địa chỉ - chưa kiểm), `SelectScreen`. Goto **chỉ có một state** → không có mặt "đang nhấn". Đã kiểm 30/09.
- Set Constant 1.7: `SetValue`, `WriteVar`; state **không có khoá ảnh** → thay `states[0].items` bằng bản sao state của Momentary 1.1. `AfterExecMacro` đóng popup chạy được. Đã kiểm 29/09 (DIAScreen tự lưu giữ nguyên).
- Momentary 1.1 có 2 state; `ReadVar` khác `WriteVar` được (START/DỪNG: ghi xung `$210.5`, đọc `$210.7` để đổi mặt). Chưa kiểm trên emulator việc đổi mặt theo ReadVar.
- Mặt nút = ảnh render sẵn, `Style=3`; nút không ảnh luôn ra xám `#B4B4B4` (không đổi màu được bằng khoá). Đã kiểm.
- Multiple Actions: chưa gặp trong dự án nào → chưa biết mã/khoá; muốn dùng thì tạo một cái trong DIAScreen rồi đọc bằng MCP `element`.
