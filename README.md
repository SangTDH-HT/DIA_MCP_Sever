<h1 align="center">DIA_MCP_Sever</h1>
<p align="center">MCP server và bộ công cụ dựng màn hình HMI Delta DIAScreen bằng code.</p>

<p align="center">
  <img alt="Python 3.12" src="https://img.shields.io/badge/python-3.12-4A84B6?style=flat-square">
  <img alt="DIAScreen 1.6 / DOPSoft" src="https://img.shields.io/badge/DIAScreen-1.6%20%7C%20DOPSoft%204-4A84B6?style=flat-square">
  <img alt="MCP server" src="https://img.shields.io/badge/MCP-delta--dpa-2BB57A?style=flat-square">
  <img alt="Claude Code skill" src="https://img.shields.io/badge/Claude%20Code-skill-5B6571?style=flat-square">
</p>

Delta DIAScreen không có API. Bộ công cụ này mở thẳng file `.dpa`, đọc và ghi lại
**đúng từng byte**, nên màn hình HMI được dựng bằng script thay vì kéo thả: mặt thẻ,
nút và sơ đồ quy trình vẽ bằng Python, phần tử động nhân bản từ dự án mẫu rồi gắn
địa chỉ PLC. Một MCP server cho Claude Code đọc/sửa thiết kế, và một skill giữ cho
mọi trang cùng một phong cách.

## Cách hoạt động

```mermaid
flowchart LR
    A["build_*.py<br/>vẽ thẻ, nút, sơ đồ bằng PIL"] --> B["kho ảnh [Picture]<br/>dpa/picbank.py"]
    D["dự án mẫu .dpa<br/>(donor)"] -- "nhân bản phần tử" --> C
    B --> C["HMI_Silo.dpa<br/>dpa/document.py ghi đúng từng byte"]
    C -- "tự đóng / mở, tự lưu kiểm" --> E["DIAScreen"]
    C --> F["render_dpa.py<br/>ảnh PNG để duyệt"]
    G["Claude Code"] -- "MCP delta-dpa" --> C
    H["skill delta-hmi-style"] -. "token, lưới, bẫy .dpa" .-> G
```

1. **Vẽ phần tĩnh thành ảnh.** Khung thẻ, tiêu đề, đơn vị, đường ống, hình silo là một ảnh; nút Delta không tô phẳng được nên mặt nút cũng là ảnh render sẵn.
2. **Nhân bản phần tử động** từ dự án mẫu (ô số, nút, van, ô chọn) rồi chỉ sửa thuộc tính đã hiểu: vị trí, phông, địa chỉ, macro.
3. **Ghi file, cho DIAScreen tự lưu một vòng** và đọc lại để chắc editor nhận, rồi mở cho người duyệt.

## Bắt đầu nhanh

```powershell
git clone https://github.com/SangTDH-HT/DIA_MCP_Sever
cd DIA_MCP_Sever
pip install -r requirements.txt
powershell -File install-skill.ps1          # skill delta-hmi-style + diascreen cho Claude Code

python render_dpa.py C:\OTL\18.SILO_Ban_Moi\3.HMI_SILO\HMI_Silo.dpa out   # vẽ mọi screen ra PNG
python build_fill_page.py C:\OTL\18.SILO_Ban_Moi\3.HMI_SILO\HMI_Silo.dpa C:\OTL\18.SILO_Ban_Moi\2.Icon_HMI
```

Đăng ký MCP trong `.mcp.json`:

```json
"delta-dpa": { "command": "python", "args": ["<repo>\\dpa_mcp.py"] }
```

> Script dựng trang cần các dự án mẫu (donor) nằm ở `C:\OTL\...` - đường dẫn ghi ở đầu mỗi
> script. File `.dpa` của khách hàng không nằm trong repo.

## Trong repo có gì

```
dpa/                    thư viện .dpa: document, model, edit, picbank, macro, editor
dpa_mcp.py              MCP server delta-dpa
render_dpa.py           vẽ screen ra PNG từ kho ảnh của chính dự án, theo ngôn ngữ và trạng thái
                        (ảnh chỉ để duyệt ở máy, không commit)

skills/delta-hmi-style/ skill phong cách: token, lưới 1024x600, thành phần, bẫy .dpa, chuỗi script
skills/diascreen/       skill tra sách DIAScreen 1.6.1 theo từng đối tượng + khoá .dpa thật
docs/quy-trinh-lam-viec.md  quy trình: một vòng sửa, chuỗi script, nối PLC, luật với DIAScreen
docs/kien-thuc-dpa.md   định dạng .dpa và mọi lần vấp, kèm lý do

build_silo_frame.py     khung chung: logo, user, thanh bên, token màu, icon Lucide
silo_tabs.py            hàng 5 tab của các trang Home
build_overview_page.py  Tổng quan 6 bồn: tên, kg, % đầy, đèn van
build_fill_page.py      Nạp liệu + mặt dùng chung (START/DỪNG, công tắc, ô chọn + popup)
build_home_pages.py     Xả liệu + Phối trộn
build_clean_page.py     Làm sạch đường ống
build_setting_page.py   Settings: lưới 8 ô + đầu trang của mọi trang con
build_system_tiles.py   ô Settings dùng chức năng của panel (ngày giờ, độ sáng), trang Ngôn ngữ
build_calibration_page.py  Hiệu chỉnh bồn cân
build_info_pages.py     About + Cài đặt bồn cân (18 thông số có giới hạn nhập)
build_io_page.py        bảng điều khiển tay: từng van, từng động cơ, có khoá liên động
build_recipe_page.py    công thức phối trộn trong Enhanced Recipe của panel
build_account_pages.py  Login + Quản lý tài khoản bằng tham số nội bộ của panel
build_data_page.py      Cảnh báo: Alarm History Table + danh sách alarm

silo_i18n.py            ba ngôn ngữ Anh / Việt / Pháp, chữ tự co cho vừa ô
translate_silo.py       đưa các trang đã vẽ sang ba ngôn ngữ
bind_plc.py             địa chỉ giữ chỗ $ → DB của PLC theo hmi_map.json
rebind_hmi_map.py       dời địa chỉ theo tên thành viên khi DB xếp lại
apply_security.py       bật máy vào Login, nút cần cấp 8, popup "Không đủ quyền"
close_popups_on_leave.py  đóng popup khi rời trang (chạy cuối chuỗi)

assets/lucide/          icon Lucide (ISC)
tests/                  round-trip byte-identical trên 14 dự án thật
```

Thứ tự chạy các script và lý do của nó: [`docs/quy-trinh-lam-viec.md`](docs/quy-trinh-lam-viec.md).

## Phong cách

| | Token | |
|---|---|---|
| ![](https://img.shields.io/badge/-%20-F3F5F8?style=flat-square) | `#F3F5F8` | nền trang |
| ![](https://img.shields.io/badge/-%20-1E2630?style=flat-square) | `#1E2630` | chữ chính |
| ![](https://img.shields.io/badge/-%20-4A84B6?style=flat-square) | `#4A84B6` | mục đang chọn, vạch tiêu đề |
| ![](https://img.shields.io/badge/-%20-2BB57A?style=flat-square) | `#2BB57A` | START |
| ![](https://img.shields.io/badge/-%20-F0405A?style=flat-square) | `#F0405A` | DỪNG |
| ![](https://img.shields.io/badge/-%20-2E9E48?style=flat-square) | `#2E9E48` | đường liệu |
| ![](https://img.shields.io/badge/-%20-35C2C8?style=flat-square) | `#35C2C8` | đường chân không |

Phông Arial, thẻ bo 6 px viền 1 px không bóng, ô số luôn in đậm. Đầy đủ trong
[`skills/delta-hmi-style/SKILL.md`](skills/delta-hmi-style/SKILL.md).

Năm nguyên tắc giữ cho mọi trang cùng một kiểu:

- **Hạn chế hình ảnh.** Thứ gì phần tử Delta làm được thì dùng phần tử, để sửa được ngay trong
  DIAScreen: chữ tĩnh là Text, đường kẻ là Line. Ảnh chỉ cho mặt nút, icon, hình thiết bị, khung thẻ.
- **Ảnh tĩnh, phần tử động.** Số, nút, van, tên là phần tử Delta đè lên ảnh nền.
- **Một hướng cho mọi trang cùng loại.** Đầu trang và nút quay về do một script duy nhất vẽ;
  mẫu mới chỉ lấy phần nội dung.
- **Ba ngôn ngữ.** Chữ là text của phần tử, không nằm trong ảnh; mỗi ngôn ngữ tự co cỡ cho vừa ô.
- **Bỏ trang trí thừa.** Không khung lồng khung, không dấu tick trên nút đang chọn.

---

# Tài liệu kỹ thuật

## MCP `delta-dpa`

Truy cập thiết kế `.dpa` bằng code, giống cách `Tia.exe` làm với TIA Portal —
đọc screen, đối tượng, địa chỉ PLC, macro nút bấm; sửa và ghi lại.

DIAScreen **không có API** (không COM, không typelib, không dòng lệnh). Nên
server này làm việc thẳng với file dự án.

## Cấu trúc file `.dpa`

```
offset 0    'BM'                    ảnh thumbnail Windows bitmap
offset 2    uint32 = 14             bfSize giả
offset 6    'PDAB'                  dấu nhận dạng của Delta
offset 14   BITMAPINFOHEADER        biSizeImage ở +34 cho biết ảnh dài bao nhiêu
offset 54   pixel ảnh
tiếp theo   luồng gzip              deflate mức 6, mtime 0, byte OS = 0x0b
bên trong   mỗi byte XOR 0x64       ra phần text của dự án
```

Phần text là dạng INI: `[Application] [Screen] [Element] [State] [SubMacro]
[Alarm] [Picture]`… Đối tượng thuộc về screen đứng ngay trước nó, `[State]`
đứng sau đối tượng là các trạng thái của nó.

Hai chỗ không phải text thuần, đọc theo **độ dài** chứ không theo dòng:

| Dạng | Ví dụ | Khung |
|---|---|---|
| Chữ UTF-16LE | `wTextLen0=28` | 28 byte, rồi một CRLF ngăn cách |
| Macro | `ButtonOnMacroLen=842` | 842 byte, CRLF nằm trong số đếm |
| Ảnh | `Size=2689151` | cả ngân hàng ảnh |

## Vì sao ghi lại được an toàn

Parser giữ nguyên từng byte: mọi thứ nó không hiểu được cất lại nguyên xi.
Test `test_round_trip_is_byte_identical` đọc rồi ghi lại **14 dự án thật**
(DOPSoft 4.00.10 → DIAScreen 6.6.2) và đòi file ra phải giống hệt file vào,
tính cả luồng gzip. Nhờ vậy một lệnh sửa chỉ đổi đúng chỗ cần đổi.

## Các lệnh

| Lệnh | Việc |
|---|---|
| `open_project(path)` | nạp `.dpa`, trả về panel, độ phân giải, PLC đang nối |
| `list_screens()` | mọi screen: id, tên, kích thước, số đối tượng |
| `layout(screen, kind)` | đổ đối tượng một screen: vị trí, kích thước, chữ, địa chỉ |
| `screenshot_text(screen)` | sơ đồ mặt bằng dạng chữ, xếp theo toạ độ |
| `element(screen, index)` | toàn bộ thuộc tính + trạng thái + macro của một đối tượng |
| `find(query)` | tìm khắp dự án theo địa chỉ PLC, chữ hiện, hay tên |
| `addresses()` | mọi địa chỉ thiết kế đụng tới, kèm chỗ dùng |
| `macros(screen)` | logic nút bấm dạng câu lệnh đọc được; bỏ trống thì trả sub-macro |
| `alarms()` | bảng cảnh báo |
| `set_property(...)` | đổi một thuộc tính: `X`, `Width`, `BgColor`, `ReadVar`… |
| `set_text(...)` | đổi chữ hiện trên đối tượng |
| `set_state_text(...)` | đổi chữ cả hai ngôn ngữ cùng lúc (Việt trước, Anh sau) |
| `clone_element(...)` | nhân bản một đối tượng sang screen khác — cách tạo mới |
| `clone_screen(...)` | thêm screen rỗng, chép thiết lập từ screen có sẵn |
| `delete_element(...)` | xoá một đối tượng và các trạng thái của nó |
| `rebind(old, new)` | dời hàng loạt địa chỉ PLC; mặc định chạy thử |
| `pending_changes()` | những gì đã sửa trong bộ nhớ, chưa ghi |
| `save(out_path, reload_editor)` | ghi ra file, tuỳ chọn nạp lại luôn trong editor |
| `editor_windows()` | DIAScreen đang mở những dự án nào |
| `close_in_editor(path)` | đóng dự án trong DIAScreen trước khi sửa, giữ phần người dùng sửa tay |
| `open_in_editor(path)` | mở lại file trong DIAScreen sau khi ghi |
| `reload_in_editor(path)` | đóng cửa sổ cũ và mở lại file vừa ghi |

## Luật an toàn

- `open_project` chỉ đọc, không khoá, không đụng file trên đĩa.
- Sửa nằm trong bộ nhớ cho tới khi `save`.
- `save` mặc định ghi ra file khác. Muốn đè file gốc phải
  `overwrite_source=True`, và luôn để lại bản `.bak`.
- **DIAScreen không khoá file** — ghi đè được ngay lúc nó đang mở. Nhưng nó
  không tự biết, nên sau khi ghi phải `reload_in_editor`, hoặc
  `save(..., reload_editor=True)`. Đừng bấm Save trong editor trước khi nạp
  lại: bản trong bộ nhớ nó cũ hơn, bấm Save là đè mất phần vừa ghi.
- `reload_in_editor` **không bao giờ trả lời hộp thoại**, và **kiểm hộp thoại
  TRƯỚC khi gửi lệnh đóng**. Lệnh đóng không rút lại được: gửi rồi mới phát
  hiện hộp thoại thì người dùng bị hỏi "có lưu không" một cách vô cớ, và bấm
  Lưu là bản cũ trong bộ nhớ editor đè mất file vừa ghi. Đang có hộp thoại mở
  thì nó từ chối, không gõ cửa.
- Nếu DIAScreen vẫn hỏi lưu sau đó: trả lời **KHÔNG**. Bản của nó cũ hơn file
  trên đĩa.
- `rebind` mặc định `dry_run=True`: xem danh sách trúng rồi mới chạy thật.

## Chạy

```
python dpa_mcp.py          # stdio MCP server
python -m pytest tests -q  # 38 test trên dự án thật
```

Đăng ký trong `.mcp.json` với tên `delta-dpa`.

## Tạo mới bằng cách nhân bản

Không dựng `[Element]` từ số không: một đối tượng thật mang vài chục thuộc tính
mà mình chưa hiểu hết, nên đối tượng mới luôn là bản sao sâu của một cái đang
chạy, rồi chỉ sửa những thuộc tính mình hiểu. `nPartsID` đánh số lại theo
screen đích, thứ tự section là thứ tự vẽ nên chèn sau cùng là nằm trên cùng.

`build_login.py` là ví dụ đầy đủ: dựng trang đăng nhập theo tông HOME của
OTL-30 vào một dự án Delta bất kỳ.

## Đã làm thêm (29–30/09/2026)

- **Macro mở/đóng popup**: `dpa/macro.screen_statement()` sinh `OPENSCREEN n` /
  `CLOSESUBSCREEN n` đúng từng byte như DIAScreen; `set_macro()` gán vào nút.
- **Kho ảnh** `[Picture]`: `dpa/picbank.py` đọc/ghi, `build_silo_frame.Bank` thêm ảnh,
  `prune_bank` dọn ảnh không còn dùng.

## Đã làm thêm (01/10/2026)

- **Macro có điều kiện và phép gán**: `dpa/macro.py` thêm `if_statement` / `else_statement` /
  `endif_statement`, `assign_statement`, `arith_statement`, `fmov_statement`,
  `fillasc_statement`; `program()` ghép nhiều câu thành một macro. Khung byte đối chiếu với
  macro thật do DIAScreen ghi.
- **Xoá screen**: `dpa/edit.delete_screen()`.
- **Ba ngôn ngữ**: `silo_i18n.py` thêm ô ngôn ngữ cho cả dự án, `render_dpa.py --lang=N --state=N`
  vẽ theo ngôn ngữ và trạng thái để soát.
- **Đóng / mở DIAScreen**: `close_in_editor`, `open_in_editor` trong MCP.

## Chưa làm

- **Ẩn/hiện theo bit cho Text**: cần thêm khoá `VisibleLink` + `VisibleVar`;
  thêm khoá mới vào section là cơ chế **chưa kiểm chứng** (`Section.set` chỉ sửa khoá có sẵn).
- **Macro**: chưa ghi được lệnh bit (`BITON`, `BITOFF`…) và vòng lặp.
- **Kiểm trên máy thật**: các trang Tổng quan, I/O, Công thức, Tài khoản và phần phân quyền mới
  qua biên dịch DIAScreen hoặc mới ghi file; chưa chạy trên panel thật với PLC.
