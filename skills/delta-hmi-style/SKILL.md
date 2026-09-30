---
name: delta-hmi-style
description: Phong cách và cách dựng màn hình HMI Delta (DIAScreen/DOPSoft .dpa) của Sáng - bảng màu, lưới 1024x600, thẻ, nút START/DỪNG, công tắc chế độ, ô chọn có tên đổi được, popup - bằng script Python vẽ ảnh + MCP delta-dpa. Dùng khi dựng mới, sửa, "làm đẹp", "căn chỉnh", "phong cách tương tự" cho bất kỳ trang HMI Delta nào (Silo, OTL...). Không dùng cho WinCC Unified.
---

# Phong cách HMI Delta

Mẫu chuẩn: dự án `C:\OTL\SILO_Ban_Moi\HMI_Silo.dpa` (trang Home_Fill, Home_Discharge, Home_Blend).
Code mẫu ở `C:\Tia_Claude\DeltaDpa_src`:

| Script | Dựng gì |
|---|---|
| `build_silo_frame.py` | khung chung: logo, user, thanh bên Home/Setting/Data, tab Fill/Discharge/Blend, token màu gốc, `icon()` Lucide |
| `build_fill_page.py` | trang Fill (tiếng Anh) + các mặt dùng chung: `start_face`, `mode_face`, `field_face`, `row_face`, `silo_popup` |
| `build_home_pages.py` | Xả liệu + Công thức (tiếng Việt), một bố cục hai biến thể qua `PAGES` |
| `build_setting_page.py` | trang menu: tiêu đề 34 đậm + vạch xanh `#4A84B6` 44x4, lưới ô 202x176 cách 14 (icon Lucide 56 + nhãn 18), trang con khung trống có "‹ Settings" |
| `build_calibration_page.py` | trang biểu mẫu (Set_Calibration): các khối thẻ xếp dọc, nhãn 14 trên ô cao 36, giếng `TILE` cho số đọc, ô nhập viền `FIELD_LINE`, nút chính tối `#5A6068` (nhấn `#43484F`) / nút phụ trắng, bảng 4 kênh (hàng tiêu đề `#E9EEF3`), ô chọn kích thước bất kỳ; ô ở đáy trang mở danh sách **lên trên** (`UP`) |

Trang mới: sao chép cách làm của `build_home_pages.py`, import mặt dùng chung từ `build_fill_page`, **đừng vẽ lại theo thói quen**.

## Nguyên tắc

- **Ảnh tĩnh + phần tử động.** Mọi thứ không đổi theo PLC (khung thẻ, tiêu đề, đơn vị, đường ống, hình silo) vẽ bằng PIL thành một ảnh. Chỉ số, nút, van, tên là phần tử Delta đè lên. Nút Delta không tô màu phẳng được → mặt nút là ảnh render sẵn (Lucide icon + chữ).
- **Phông Arial** (`arial.ttf`, đậm `arialbd.ttf`), kể cả chữ trong ảnh. Ngôn ngữ theo mẫu Sáng đưa (Fill tiếng Anh, Xả/Trộn tiếng Việt) - hỏi nếu chưa rõ.
- **Ô số hiển thị luôn in đậm**, căn phải sát trước đơn vị. Cỡ theo cặp: STATUS 18 · giá trị thẻ quy trình 24 · cặp áp suất/thời gian 20 · cặp thẻ nhỏ 16 · khối lượng lớn 64 màu `#2B3644`.
- **Tiêu đề** thẻ lớn: đậm 15, ô icon 34x34 nền `TILE` bên trái. Tiêu đề thẻ quy trình: thường 12, gạch mảnh + chấm dưới (`card_title`), quá dài thì thu tới 11 - không nhỏ hơn; hết chỗ thì nới thẻ.
- Bỏ trang trí thừa: không dấu tick trên nút đang chọn, không dòng "Press to begin", không khung lồng khung - dùng đường kẻ mảnh.
- Nhãn ALL-CAPS chỉ cho tiêu đề thẻ (theo mẫu Sáng); nút dùng chữ thường/hoa theo mẫu.

## Token

| Tên | Hex | Vai trò |
|---|---|---|
| PAGE | `#F3F5F8` | nền trang, header, thanh bên |
| WHITE | `#FFFFFF` | thẻ |
| CARD_LINE | `#E1E6EC` | viền thẻ, đường kẻ trong thẻ |
| FIELD_LINE | `#C9D0D8` | viền ô chọn, tag van (SFV/GHFV/SDV) |
| TILE | `#EEF1F4` | ô icon, rãnh công tắc, giếng ô nhập |
| INK | `#1E2630` | chữ chính |
| MUTED | `#5B6571` | nhãn phụ, mã thiết bị, chữ nấc không chọn |
| NAV_INK | `#2F3A45` | icon, nét hình vẽ (silo, bơm) |
| MATERIAL | `#2E9E48` | đường liệu |
| VACUUM | `#35C2C8` | đường chân không |
| LEADER | `#8C95A0` | đường đứt nối thẻ ↔ thiết bị |
| START xanh | `#DDF5EC` / `#C3EEDB` / `#2BB57A` | vòng ngoài / vòng trong / icon |
| DỪNG đỏ | `#FDE4E8` / `#FBCDD5` / `#F0405A` | như trên |
| Đĩa nút | `#FFFFFF`→`#E4E8ED`, viền `#D9DEE4`, chữ `#4A5563` | |

Thẻ bo 6 px, viền 1 px, không bóng. Vẽ ở 4x rồi thu (`s = 4`) cho nét mịn.

## Lưới 1024x600

```
header 0..58 (logo | tab Fill/Discharge/Blend | user)
┌sidebar 0..92┬ STATUS 100,66 674x46 ─────────────────┬ thẻ khối lượng 784,66 232x144 ┐
│ Home        │ vùng quy trình 100,120 674x472         ├ thẻ chọn 784,222 232x370      │
│ Setting     │  thẻ số + đường ống + hình thiết bị    │  ô chọn 800,276 200x42        │
│ Data        │                                        │  nút tròn 835,329 130x130     │
│             │                                        │  kẻ 470 · CHẾ ĐỘ · công tắc   │
│             │                                        │  800,520 200x50               │
```
Lề trong thẻ 16 px. Mọi phần tử trong cột phải thẳng lề x 800..1000.

## Thành phần có sẵn

- **Nút tròn START/DỪNG** `start_face(running, go, stop, size)`: 1.1 Momentary, `WriteVar` = xung lệnh, `ReadVar` = bit đang chạy (đổi mặt). PLC tự lật chạy/dừng.
- **Công tắc chế độ** `mode_face(auto, labels, size)`: 1.5 Multistate hai trạng thái, nấc chọn trắng nổi chữ đậm.
- **Ô chọn có tên đổi được** (`field_face` + `row_face` + `silo_popup`): ComboBox Delta **không đọc chữ từ địa chỉ**, nên ô = nút 1.1 macro `OPENSCREEN n` + Character Display 5.2 tên đang chọn; popup sub-screen đặt đè đúng ô, header bấm `CLOSESUBSCREEN n`, 6 dòng = Set Constant 1.7 (`SetValue` i, `AfterExecMacro` đóng popup) + Character Display tên. PLC giữ mảng tên và chép tên đang chọn ra một chuỗi.
- **Van** State Graphic 7.1 hai ảnh `Van_Off/Van_On.png`; **dấu xong** 7.1 `circle` xám / `circle-check` xanh.
- **Nút thiết bị trong thẻ** `valve_button_face`: ô 62x70 icon + nhãn, xám khi nghỉ, trắng viền đậm khi bật.
- Ô nhập số: 6.1 donor `scr_Discharge` #52, vẽ giếng `TILE` phía sau để báo nhập được.

Icon: Lucide ở `C:\Users\Admin\.tia-openness\state\lucide`; thiếu thì tải `https://unpkg.com/lucide-static@latest/icons/<tên>.svg`. Hình vẽ tay của Sáng ở `C:\OTL\SILO_Ban_Moi\Icon_HMI` (Silo_3 vẽ đỏ → `inked()` đổi về NAV_INK).

## Bẫy .dpa (đã kiểm)

- `FontAlign` là bit: 1 trái, 2 giữa, 4 phải, +32 giữa dọc → **33 trái, 34 giữa, 36 phải**. 35 = trái+giữa, panel vẽ lệch.
- `Style=3` = Transparent (không nền, không viền) cho ô số/ô chữ và nút mặt ảnh.
- Cỡ phông theo từng ngôn ngữ `FontSize0/1`, không có `FontSize`. **Phần tử dùng cỡ chẵn**: DIAScreen lưu là đổi 15 → 14 (chữ trong ảnh thì cỡ nào cũng được). Dự án một ngôn ngữ: DIAScreen xoá các khoá `...1` khi lưu - so bản trước/sau thì bỏ qua chúng.
- Goto 1.10 chỉ có một trạng thái → ô menu không có mặt "đang nhấn".
- `Section.set()` không thêm khoá mới. Set Constant 1.7 không có khoá ảnh → thay `states[0].items` bằng bản sao state của Momentary 1.1.
- Macro: `dpa/macro.screen_statement()` sinh `OPENSCREEN`/`CLOSESUBSCREEN` đúng byte; `set_macro()` gán, độ dài gồm CRLF.
- Rectangle chừa lề ảnh 4/1 px (`frame.picture_rect`), State Graphic 3/0; Goto/nút Style 3 giữ nguyên.
- Chi tiết thêm: memory `diascreen-khong-co-api`.

## Quy trình

1. Đọc screen trước (`layout`/script dump) - mẫu, vị trí, chữ.
2. Lập token/bố cục từ bảng trên; chỉ thêm màu mới khi mẫu đòi.
3. Render ảnh xem trước cả trang vào scratchpad, tự soát (chữ bị thu nhỏ? dính? lệch lề?) rồi mới nạp.
4. `close_in_editor` (tự lưu phần Sáng sửa tay) → **so phần tử với lần dựng trước**: Sáng có sửa tay thì đưa vào script, không đè → sao lưu `.bak` → chạy script → đọc lại file.
5. Duyệt bằng ảnh thật của file: `python render_dpa.py <dpa> <thư mục> <screen...>` (vẽ từ kho ảnh + phông/căn lề phần tử, không cần DIAScreen).
6. Cho DIAScreen tự lưu một vòng (`PostMessage WM_COMMAND 0xE103`) và đọc lại để chắc nó nhận → `open_in_editor` cho Sáng xem.
7. Địa chỉ chưa có PLC thì trỏ bộ nhớ trong `$2xx/$3xx`, liệt kê trong `ADDRESSES` để gán lại sau.
