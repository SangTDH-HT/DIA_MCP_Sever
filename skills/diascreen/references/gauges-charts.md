# Đồng hồ, thanh, ống, biểu đồ (sách tr.262–303, 387–417)

## Meter (Sách)
Read Address Word; Data Type/Format; Min/Max (hằng hoặc **từ địa chỉ**); **Target** (màu riêng) và **Range Low/High** (hằng hoặc địa chỉ); digits. Style Standard/Raised/Sunken/Transparent; màu kim/vạch/viền/vùng thấp/cao; Numeric Display; mark 1–10, subscale 0–99; ảnh Picture Bank Mode hoặc Template Wizard; smooth animation, anti-aliasing; Invisible; Coord.

## Bar (Sách)
- **Normal Bar**: min→max, màu vùng thấp/cao, target; hiện Value hoặc Percentage.
- **Differential Bar**: độ lệch so với target (Deviation), trong ngưỡng thì màu deviation.
- Word/Double Word; BCD…Hex (không Floating); scale vị trí/mark 1–99. Mã `.dpa` **3.1** "Normal" (khoá `MinValue MaxValue LRegionColor HRegionColor ShowRange Variation LLimitValue HLimitValue ShowTarget TargetValue TargetColor BarStyle MinMaxVariation TargetStyle`).

## Pipe (Sách)

| Phần tử | Việc |
|---|---|
| Pipe(1)/(2) | ống/bồn có mực theo giá trị (Water Level Color, Cylinder Color, vùng thấp/cao, target) - hợp **mức silo** |
| Pipe(3)/(4)/(5) | đoạn nối, chỉ đường kính và góc |
| Pipe(6)/(7) | ống nước có **hướng chảy theo địa chỉ** (1 = phải/xuống, 2 = trái/lên); con trỏ Conveyer/Bubble/Arrow; màu đổi theo địa chỉ |
| **Flow Block** | vẽ đường gấp khúc (góc ≥90°), khối chạy theo hướng vẽ; **tốc độ −10..10** (âm = ngược), kiểu khối 1 chữ nhật/2 mũi tên/3 tròn/4 bình hành/5 ảnh, rộng/dài/khe khối, màu ống/viền/khối - **mọi thứ lấy được từ địa chỉ** |

→ Đường liệu / đường hút trên trang Fill/Xả có thể thành Flow Block chạy khi đang nạp. Chưa kiểm (chưa có donor).

## Pie (Sách)
Pie(1)… theo giá trị, vùng thấp/cao, target, Interval display 0–100; Pie Chart: góc đầu/cuối, số vùng 2–15, lỗ giữa.

## Curve (Sách)

| Phần tử | Việc |
|---|---|
| Trend Graph | ≤12 đường; lấy mẫu khi bit **Curve Control** (Control Block) bật; Sample Number ≤ rộng phần tử |
| X-Y Chart | ≤8 đường, X/Y riêng, trượt xem giá trị, giới hạn trên/dưới, ≤10 nhóm |
| X-Y Distribution | chấm điểm X,Y (≤4 mẫu), màu/nối từ địa chỉ, chạy nền |
| Curve Input | vẽ đường từ mảng địa chỉ (gấp khúc/cột) |
| Mold Thickness Control | chỉ AX/IMP |

Chung: min/max hằng hoặc địa chỉ, màu/độ dày, projection axis, lưới ≤50, Style, smooth, anti-aliasing.
Đồ thị lịch sử (theo History Buffer) → `history.md`.

## Thực tế `.dpa`
- Trend 9.1 / 12.15 clone sang dự án khác bị lỗi compile `Element buffer is undefined` - cần `[History]` khai bộ đệm (`HistoryCount`, `ReadVar01`…). Đã gặp 29/09.
- Silo hiện vẽ silo/đường ống bằng ảnh tĩnh; muốn động (mức, dòng chảy) thì thay bằng Pipe(1)/(2) và Flow Block - cần tạo donor trong DIAScreen trước.
