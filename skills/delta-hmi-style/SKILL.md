---
name: delta-hmi-style
description: Phong cách và cách dựng màn hình HMI Delta (DIAScreen/DOPSoft .dpa) của Sáng - bảng màu, lưới 1024x600, thẻ, nút START/DỪNG, công tắc chế độ, ô chọn có tên đổi được, popup - bằng script Python vẽ ảnh + MCP delta-dpa. Dùng khi dựng mới, sửa, "làm đẹp", "căn chỉnh", "phong cách tương tự" cho bất kỳ trang HMI Delta nào (Silo, OTL...). Không dùng cho WinCC Unified.
---

# Phong cách HMI Delta

Thuộc tính / giới hạn / cách dùng từng đối tượng theo sách DIAScreen → skill `diascreen` (tra theo đối tượng trước khi làm). Skill này chỉ lo phong cách và cách dựng bằng script.

Mẫu chuẩn: dự án `C:\OTL\18.SILO_Ban_Moi\3.HMI_SILO\HMI_Silo.dpa`. Thư mục dự án (Sáng đặt 30/09):

| Thư mục | Chứa |
|---|---|
| `1.Document` | sách hướng dẫn DIAScreen 1.6.1 (PDF) - tra thuộc tính phần tử ở đây trước khi đoán |
| `2.Icon_HMI` | ảnh script sinh ra (tham số thứ hai của mọi `build_*.py`) |
| `3.HMI_SILO\HMI_Silo.dpa` | file dự án |
| `3.HMI_SILO\1.File_Backup` | bản `.bak` trước mỗi lần sửa |

Không ghi gì ra gốc `SILO_Ban_Moi`.
Code mẫu ở `C:\Tia_Claude\DeltaDpa_src`:

| Script | Dựng gì |
|---|---|
| `build_silo_frame.py` | khung chung: logo, user, thanh bên Home/Setting/Data, tab Fill/Discharge/Blend, token màu gốc, `icon()` Lucide |
| `build_fill_page.py` | trang Fill (tiếng Anh) + các mặt dùng chung: `start_face`, `mode_face`, `field_face`, `row_face`, `silo_popup` |
| `build_home_pages.py` | Xả liệu + Công thức (tiếng Việt), một bố cục hai biến thể qua `PAGES` |
| `build_setting_page.py` | trang menu: tiêu đề 34 đậm + vạch xanh `#4A84B6` 44x4, lưới ô 202x176 cách 14 (icon Lucide 56 + nhãn 18), trang con khung trống có "‹ Settings" |
| `build_calibration_page.py` | trang biểu mẫu (Set_Calibration): các khối thẻ xếp dọc, nhãn 14 trên ô cao 36, giếng `TILE` cho số đọc, ô nhập viền `FIELD_LINE`, nút chính tối `#5A6068` (nhấn `#43484F`) / nút phụ trắng, bảng 4 kênh (hàng tiêu đề `#E9EEF3`), ô chọn kích thước bất kỳ; ô ở đáy trang mở danh sách **lên trên** (`UP`) |
| `build_data_page.py` | trang Data = Cảnh báo: tiêu đề kiểu Settings, nút "XÁC NHẬN TẤT CẢ" cùng hàng bên phải, Alarm History Table 11.1 x 133..983 (cột Giờ xảy ra / Nội dung / Giờ hết / Số lần, hàng đỏ nhạt `#FDE4E8` khi kích, vàng nhạt `#FFF3D9` khi đã xác nhận); ghi luôn danh sách alarm vào `[Alarm]` |
| `build_info_pages.py` | About (cả trang là một ảnh tĩnh + nút ✕ về Settings, logo lấy phần biểu tượng của `OTL-logo-square-01.png`) và Cài đặt bồn cân (3 thẻ × 6 dòng: nhãn 14/13 một dòng hoặc ngắt ở "–", khoảng giới hạn 12 xám, ô nhập 80x40 có `MinValue/MaxValue`) |
| `build_io_page.py` | trang I/O (Set_IO) = bảng điều khiển tay như Overview_Silo OTL-30: nút SFV1..6 / SDV1..6 quanh hình silo, VACUUM / HOPPER / GHFV / GHDV, công tắc AUTO \| MANUAL, Xoá lỗi, thanh mã liên động; nút là Momentary (mặt xanh khi chân %Q thật bật) có **Interlock** (`interlock()` chèn `InterLockLink/InterLockVar`): thiết bị khoá khi chưa vào tay, MANUAL khoá khi đường ống đang bận; nhận `<dpa> <icon> <hmi_map.json>` |
| `build_overview_page.py` | trang Tổng quan (Home_Overview, tab đầu, trang HOME mở và trang khởi động): thẻ TỔNG trên cùng + 6 thẻ bồn 3x2 (hình silo, số bồn, tên, kg, % đầy, đèn van nạp/xả) qua `"HMI".Ov`; nhận `<dpa> <icon> <hmi_map.json>` |
| `build_recipe_page.py` | công thức phối trộn trong Enhanced Recipe của panel: trang `Set_Recipe` (danh sách 6 dòng + vạch chọn, ô tên, 6 ô kg, tổng, Xoá có hỏi lại), popup công thức và bánh răng trang Phối trộn, cycle macro đẩy công thức đang chọn xuống `"HMI".Rc`; chạy sau `build_overview_page.py`, trước `close_popups_on_leave.py` |
| `build_clean_page.py` | trang Làm sạch đường ống (Home_Clean, tab thứ 5) qua `"HMI".Cl`: thanh trạng thái, chọn đường, 6 chip bồn, điều kiện / thông số, tiến độ %, nút tròn START/DỪNG; nhận `<dpa> <icon> <hmi_map.json>` |
| `build_system_tiles.py` | ô Settings ba ngôn ngữ; Date and time (12.1) và Screen Brightness (12.4) mở hộp thoại của chính panel, Language mở `Set_Language` có 3 nút cờ (12.12, `LangValue` 0/1/2) |
| `build_account_pages.py` | trang Login (cả trang, ô nhập ở nửa trên vì bàn phím che nửa dưới) + Quản lý tài khoản (Set_Account) bằng tham số nội bộ `SetUserAccount` / `Login` / `AddUserAccount`…; nút trên tham số nội bộ phải là Set Constant 1.7 ghi 1 |
| `silo_i18n.py` | ba ngôn ngữ, thứ tự cố định 0 English · 1 Tiếng Việt · 2 Français: `ensure_languages()` thêm ô ngôn ngữ, `words(element, (en, vi, fr), size)` ghi chữ và tự co cỡ chẵn cho vừa ô |
| `translate_silo.py` | đưa các trang vẽ trước 01/10 sang ba ngôn ngữ: tra `WORDS` theo chữ đang có, vẽ lại mặt nút không chữ, chữ thành text của nút; chữ Sáng tự sửa mà `WORDS` không biết thì để nguyên và liệt kê |
| `bind_plc.py` / `rebind_hmi_map.py` | đổi địa chỉ giữ chỗ `$` sang DB "HMI" theo `hmi_map.json` (bảng `BIND`) và viết lại alarm; DB xếp lại thì `rebind_hmi_map.py <dpa> <map cũ> <map mới>` dời theo tên thành viên |
| `silo_tabs.py` | hàng 5 tab Home (TỔNG QUAN / NẠP / XẢ / PHỐI TRỘN / LÀM SẠCH), x 196, rộng 119 cách 4 - nơi DUY NHẤT vẽ tab; script trang Home gọi `clear()` → `faces()` → `place()` |
| `close_popups_on_leave.py` | chạy CUỐI chuỗi: gắn `CLOSESUBSCREEN` vào mọi nút Goto để popup không nằm lại khi chuyển trang |
| `apply_security.py` | chạy CUỐI chuỗi, trước `close_popups_on_leave.py`: trang khởi động = Login, đăng nhập đúng tự vào trang chủ, đăng xuất về Login; nút mở Công thức / Quản lý tài khoản / Thông số cần cấp 8 - bảng `GUARDS`: nút Goto thay bằng Momentary có macro so `CurrentUserLevel`, thiếu cấp mở popup `pop_NoRight`; nhận `<dpa> <icon>` |

Trang mới: sao chép cách làm của `build_home_pages.py`, import mặt dùng chung từ `build_fill_page`, **đừng vẽ lại theo thói quen**.

## Nguyên tắc

- **Hạn chế hình ảnh** (Sáng 30/09: "sau này thiết kế hạn chế hình ảnh lại nha"). Cái gì phần tử Delta làm được thì dùng phần tử để Sáng tự sửa trong DIAScreen: chữ tĩnh = Text 10.6, đường kẻ thẳng = Line 10.1, số/chữ động = 5.x/6.x. Ảnh chỉ cho thứ Delta không làm được: mặt nút, icon Lucide, hình vẽ thiết bị/đường ống, khung thẻ bo góc. Trước khi render gì thành ảnh, hỏi "phần tử Delta làm được không?".
- **Ảnh tĩnh + phần tử động.** Mọi thứ không đổi theo PLC mà Delta không vẽ được (khung thẻ, đường ống, hình silo, icon) vẽ bằng PIL thành một ảnh. Chỉ số, nút, van, tên là phần tử Delta đè lên. Nút Delta không tô màu phẳng được → mặt nút là ảnh render sẵn (Lucide icon + chữ).
- **Chữ tĩnh là phần tử Text 10.6, không nằm trong ảnh** (Sáng 30/09: "toàn hình vậy sao anh sửa?"). Ảnh nền nào cũng render qua `frame.static(key, hàm, *args)`: chữ `t.text(...)` trong hàm không vẽ mà được ghi lại; `picture()` gọi `frame.labels(project, screen, key, x, y)` để đặt từng chữ thành Text (`<key>_txtN`, donor HMI_AThanh `pop_Setting`#2, `AutoResizeByText=0`, cỡ lẻ làm tròn xuống chẵn; Text cỡ 34 DIAScreen lưu thành 36 - kiểm 30/09, các cỡ 10–28 chẵn giữ nguyên). Đầu `main` gọi `frame.remember_labels(project)` → chữ Sáng đã sửa trong DIAScreen được **giữ nguyên** khi chạy lại; muốn script vẽ lại chữ nào thì xoá phần tử đó. Chữ trên mặt nút vẫn trong ảnh. Gạch chân + chấm của `card_title` vẫn trong ảnh, dài theo chữ gốc.
- **Phông Arial** (`arial.ttf`, đậm `arialbd.ttf`), kể cả chữ trong ảnh.
- **Ba ngôn ngữ** (Sáng 01/10): chữ mới luôn đủ Anh / Việt / Pháp qua `silo_i18n.words`. Chữ trên nút là text của chính nút, mặt ảnh vẽ **không chữ**; chữ dưới icon thì thêm dòng trống phía trước (`"\n\n\nHOME"`). Soát từng ngôn ngữ bằng `render_dpa.py --lang=N`.
- **Chữ đổi theo ngôn ngữ thì không nằm trong ảnh**; hộp thoại có sẵn của panel (ngày giờ, độ sáng) dùng luôn, không vẽ lại.
- **Phân quyền** nằm ở nút mở trang (bảng `GUARDS` trong `apply_security.py`): thiếu cấp thì hiện popup "Không đủ quyền", không dùng khoá `Level` (nó bật hộp Login của Delta).
- **Ô số hiển thị luôn in đậm**, căn phải sát trước đơn vị. Cỡ theo cặp: STATUS 18 · giá trị thẻ quy trình 24 · cặp áp suất/thời gian 20 · cặp thẻ nhỏ 16 · khối lượng lớn 64 màu `#2B3644`.
- **Tiêu đề** thẻ lớn: đậm 15, ô icon 34x34 nền `TILE` bên trái. Tiêu đề thẻ quy trình: thường 12, gạch mảnh + chấm dưới (`card_title`), quá dài thì thu tới 11 - không nhỏ hơn; hết chỗ thì nới thẻ.
- **Một hướng cho mọi trang cùng loại** (Sáng 30/09: "đừng làm khác nhau, nó sẽ không đồng bộ"). Trang con của Settings: link "‹ Settings" (127, 70) về Settings, vạch mảnh `FIELD_LINE`, tên trang đậm 18 (250, 66), nội dung từ `CONTENT_TOP` = 104 - kiểu trang Hiệu chỉnh, Sáng chốt 30/09 (em từng hiểu nhầm "hướng đầu tiên" là kiểu About có ✕). Phần đầu này **chỉ** `build_setting_page.py` vẽ (phần tử `st_head_*`, `st_back`), script nội dung không tự vẽ tiêu đề/nút quay về và không xoá `st_`. Mẫu mới có kiểu đầu trang khác thì vẫn theo kiểu chung, hỏi Sáng nếu muốn đổi cả loạt.
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
header 0..58 (logo | 5 tab Home từ x 196 | user)
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

Icon: Lucide ở `DeltaDpa_src/assets/lucide`; thiếu thì tải `https://unpkg.com/lucide-static@latest/icons/<tên>.svg` vào đó. Hình vẽ tay của Sáng ở `DeltaDpa_src/assets/drawings` (chỉ trên máy, không đẩy GitHub; Silo_3 vẽ đỏ → `inked()` đổi về NAV_INK). Ảnh sinh ra ghi vào `2.Icon_HMI`; đừng tạo lại `Icon_HMI`.

## Bẫy .dpa (đã kiểm)

- `FontAlign` là bit: 1 trái, 2 giữa, 4 phải, +32 giữa dọc → **33 trái, 34 giữa, 36 phải**. 35 = trái+giữa, panel vẽ lệch.
- `Style=3` = Transparent (không nền, không viền) cho ô số/ô chữ và nút mặt ảnh.
- Cỡ phông theo từng ngôn ngữ `FontSize0/1`, không có `FontSize`. **Phần tử dùng cỡ chẵn**: DIAScreen lưu là đổi 15 → 14 (chữ trong ảnh thì cỡ nào cũng được). Dự án một ngôn ngữ: DIAScreen xoá các khoá `...1` khi lưu - so bản trước/sau thì bỏ qua chúng.
- **Ô nhập 6.1 donor là REAL 2 word** (`MemFmt=5, MemLen=2`) → đặt `MemFmt=2, MemLen=1` (1 word, giá trị x10 như ô hiển thị) nếu không sẽ chồng lên địa chỉ kế tiếp. Giới hạn nhập: `MinValue`/`MaxValue` theo đơn vị hiển thị ("30.0").
- Goto 1.10 chỉ có một trạng thái → ô menu không có mặt "đang nhấn".
- `Section.set()` không thêm khoá mới. Set Constant 1.7 không có khoá ảnh → thay `states[0].items` bằng bản sao state của Momentary 1.1.
- Macro: `dpa/macro.screen_statement()` sinh `OPENSCREEN`/`CLOSESUBSCREEN` đúng byte; `set_macro()` gán, độ dài gồm CRLF.
- Rectangle chừa lề ảnh 4/1 px (`frame.picture_rect`), State Graphic 3/0; Goto/nút Style 3 giữ nguyên.
- Chi tiết thêm: memory `diascreen-khong-co-api`.

## Quy trình

1. Đọc screen trước (`layout`/script dump) - mẫu, vị trí, chữ.
2. Lập token/bố cục từ bảng trên; chỉ thêm màu mới khi mẫu đòi.
3. Render ảnh xem trước cả trang vào scratchpad, tự soát (chữ bị thu nhỏ? dính? lệch lề?) rồi mới nạp.
4. `close_in_editor` (tự lưu phần Sáng sửa tay) → **so phần tử với lần dựng trước**: Sáng có sửa tay thì đưa vào script, không đè → sao lưu vào `3.HMI_SILO\1.File_Backup\HMI_Silo_truoc_<việc>.dpa.bak` → chạy script → đọc lại file.
5. Duyệt bằng ảnh thật của file: `python render_dpa.py <dpa> <thư mục> <screen...>` (vẽ từ kho ảnh + phông/căn lề phần tử, không cần DIAScreen).
6. Cho DIAScreen tự lưu một vòng (`PostMessage WM_COMMAND 0xE103`) và đọc lại để chắc nó nhận → `open_in_editor` cho Sáng xem.
7. Địa chỉ chưa có PLC thì trỏ bộ nhớ trong `$2xx/$3xx`, liệt kê trong `ADDRESSES` để gán lại sau.

## Thứ tự chuỗi script (HMI Silo)

Script trang vẽ lại nút và chữ của nó, nên chạy lại một script ở giữa là phải chạy lại mọi bước phía sau:

```
build_silo_frame → build_fill_page → build_home_pages → build_setting_page
→ build_calibration_page → build_info_pages → build_data_page        (trang gốc, địa chỉ $)
→ build_clean_page → build_system_tiles → translate_silo              (ba ngôn ngữ)
→ bind_plc                                                            ($ → DB "HMI")
→ build_account_pages → build_io_page → build_overview_page → build_recipe_page
→ apply_security → close_popups_on_leave                              (LUÔN chạy cuối)
```

Bản đầy đủ kèm lý do: `DeltaDpa_src/docs/quy-trinh-lam-viec.md`.
