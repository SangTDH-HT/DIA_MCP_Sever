# Alarm (sách tr.479–546)

## Cài đặt (Data Management > Alarm Settings) (Sách)

- Tối đa **20480** alarm. Hai kiểu địa chỉ:
  - **Liên tục**: một Address đầu (Properties), mỗi alarm là một bit kế tiếp; Trigger On/Off.
  - **Rời rạc**: mỗi alarm tự đặt Type (Bit/Word), Address, điều kiện (Bit On/Off; Word theo khoảng). Có nút *tối ưu* đọc địa chỉ rời.
- Mỗi alarm: Enable, **Message Content** (đa ngôn ngữ), **Category** 0–4095 (đặt hàng loạt), **Monitor Address** - chèn giá trị vào câu bằng `%d1`…`%d8`, `%f1`, `%s1` (≤8 địa chỉ), Text Color, **Alarm Screen** (subscreen bật lên khi alarm), Mail (cần SMTP), Notification (WeChat/WhatsApp/LINE).
- Properties: **Acknowledge all alarms** address, **Scan Time** 0.5–10 s (mặc định 3), **Max Records** 1–9999 (mặc định 500, đầy thì ghi vòng), **Non-volatile** None/HMI (SRAM)/USB/USB2/SD, **Export CSV** (cần USB/SD) + chọn cột, thoát screensaver khi có alarm, **Display alarm screen Auto/Manual**, **Alarm Moving Sign** toàn cục (trên/dưới màn hình, hướng, tốc độ, màu nền, trong suốt).
- Nhập/xuất `.xlsx` (sheet AlarmContent + AlarmSetting); đọc được `.alm/.ini` đời cũ.
- Font/size/tỉ lệ chữ alarm 33–200 %.

## Phần tử (Sách)

| Phần tử | Ghi chú | Mã |
|---|---|---|
| **Alarm History Table** | màu theo trạng thái (kích/xác nhận/phục hồi), Action Control Addr (1 xác nhận dòng chọn, 2 bật alarm screen), sắp xếp theo cột hoặc địa chỉ | **11.1** |
| Active Alarm List / Alarm Frequency Table | chọn cột, sắp xếp mặc định | |
| **Alarm Moving Sign** | chạy chữ alarm, hiện số/nhóm/giờ | **11.4** |
| Gantt Chart | chỉ DOP-300, một cái mỗi screen | |

Chung: lọc theo **Group** (0 = tất cả), **Filter control address** (ẩn đã phục hồi/đã xác nhận, theo số lần, theo category, theo số alarm), scroll control, màu hàng/lưới/chọn, cột + tiêu đề + ngày giờ, nút chức năng (25–100 px).
Chưa đặt địa chỉ đọc alarm thì compile báo lỗi.

## Tham số nội bộ liên quan
`ALARM_COUNT` - tổng số alarm (DOP-100 ghi kích + phục hồi trên một dòng). Control Block: xoá bộ đệm alarm (b3), xoá bộ đếm (b4).

## Thực tế
- **Silo mới có 8 alarm (30/09)**, dựng bằng `DeltaDpa_src/build_data_page.py`: trang Data, bảng 11.1 `dt_alarms`.
- Khoá `[Alarm]` (Đã kiểm 30/09, DIAScreen tự lưu giữ nguyên): địa chỉ rời `ContinueAddr=0`; mỗi alarm bit chỉ cần 4 khoá
  `AlarmEnableNNN=1`, `AlarmVarNNN=$900.0`, `wMessageLenNNN-000` (UTF-16LE + NUL), `AlarmColorNNN` (BGR); khoá còn lại để mặc định thì
  DIAScreen không ghi. Alarm word thêm `AlarmMemLen/TriggerFmt/TriggerOperatorNNN-001/Max/Min`. Ghi các alarm nối vào cuối section.
  `AckAllAlarmVar` = bit xác nhận tất cả, `Hold=1` giữ lịch sử khi mất điện.
- Bảng 11.1: Color Mode = trạng thái là `RowColorMode=1` + `RowActiveColor` (kích) / `RowAckColor` (đã xác nhận) / `RowNormalColor` (phục hồi).
  Cột: 1 số, 2 giờ kích, 3 nội dung, 4 giờ xác nhận, 5 giờ phục hồi, 6 số lần, 7 nhóm, 8 người thao tác; ẩn = `EnableColN=0`, `DisplayOrderN=60`.
  DIAScreen nhận các khoá này; **màu hàng theo trạng thái chưa thử trên emulator**.
- Silo mới chưa có alarm (trước 30/09). OTL-30 (Siemens) có luật riêng ở skill khác - không lẫn.
- Popup lỗi kiểu OTL-30 trên Delta: dùng **Alarm Screen** (subscreen) gắn vào alarm + Display Auto. Chưa kiểm.
