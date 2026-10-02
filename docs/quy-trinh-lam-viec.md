# Quy trình làm việc với HMI Delta

Cách dựng và sửa một dự án DIAScreen (`.dpa`) bằng bộ công cụ này, từ lúc nhận mẫu tới lúc
mở lại cho người duyệt. Phong cách (màu, lưới, thành phần) ở
[`skills/delta-hmi-style/SKILL.md`](../skills/delta-hmi-style/SKILL.md); thuộc tính từng đối
tượng theo sách ở [`skills/diascreen/`](../skills/diascreen/SKILL.md); định dạng file và các
lần vấp ở [`kien-thuc-dpa.md`](kien-thuc-dpa.md).

## Ba thứ đi cùng nhau

| Thứ | Trả lời câu hỏi | Dùng lúc nào |
|---|---|---|
| Skill `diascreen` | Delta làm được việc này không, bằng đối tượng nào, khoá `.dpa` nào | trước khi chọn đối tượng |
| Skill `delta-hmi-style` | trang trông thế nào, đặt ở đâu, script nào đã vẽ sẵn | trước khi viết script trang |
| MCP `delta-dpa` + `dpa/` | đọc, sửa, ghi file; đóng và mở DIAScreen | suốt quá trình |

Sách và thực tế lệch nhau thì tin thực tế, rồi sửa lại file `references/` của skill kèm ngày kiểm.

## Thư mục dự án

```
<dự án>\1.Document                 sách DIAScreen, tài liệu
<dự án>\2.Icon_HMI                 ảnh script sinh ra - chỉ giữ ảnh đang dùng
<dự án>\3.HMI_SILO\HMI_Silo.dpa    file dự án
<dự án>\3.HMI_SILO\1.File_Backup   bản .bak trước mỗi lần sửa
```

Không ghi gì ra gốc thư mục dự án. File `.dpa`, `.bak` và mọi hình giao diện không vào repo.

## Một vòng sửa

1. **Đọc screen trước.** `layout` / `screenshot_text` của MCP: vị trí, chữ, địa chỉ, macro đang có.
   Không dựng theo trí nhớ.
2. **Tra đối tượng.** Mở đúng file `references/` của skill `diascreen`. Mục ghi "Sách" hoặc
   "Chưa kiểm" thì thử trên emulator trước khi dùng hàng loạt.
3. **Lập bố cục từ bảng token và lưới** của skill phong cách. Chỉ thêm màu khi mẫu đòi. Mẫu mới
   chỉ lấy phần nội dung; khung chung (đầu trang, nút quay về) theo kiểu đã chốt.
4. **Xem trước.** Render cả trang ra ảnh ở thư mục tạm, tự soát: chữ bị thu nhỏ, dính nhau, lệch lề.
5. **Đóng DIAScreen** bằng `close_in_editor`. Nó hỏi lưu thì trả lời Có, để giữ phần người dùng
   vừa sửa tay. Đang có hộp thoại thuộc tính mở thì dừng lại, không đóng.
6. **So với lần dựng trước.** Phần tử nào người dùng đã sửa tay thì đưa thay đổi đó vào script,
   không đè lên.
7. **Sao lưu** vào `1.File_Backup\HMI_Silo_truoc_<việc>.dpa.bak`.
8. **Chạy script**, rồi chạy tiếp mọi bước đứng sau nó trong chuỗi bên dưới.
9. **Đọc lại file vừa ghi** và duyệt bằng ảnh thật:
   `python render_dpa.py <dpa> <thư mục> [--lang=N] [--state=N] <screen...>`.
10. **Cho DIAScreen tự lưu một vòng** (`PostMessage WM_COMMAND 0xE103`) rồi đọc lại lần nữa: editor
    nhận file và không đổi thứ mình vừa ghi.
11. **Biên dịch.** Chỉ báo "đã biên dịch" khi đọc được khung Output. F7 gửi vào cửa sổ không ở
    foreground không biên dịch.
12. **Mở lại** bằng `open_in_editor` cho người duyệt. Nói rõ phần nào đã kiểm tới mức nào: mới
    ghi file, đã qua vòng tự lưu, đã biên dịch, đã chạy emulator, đã chạy panel thật.

## Chuỗi script của HMI Silo

Script trang nào cũng xoá phần tử của mình (theo tiền tố tên) rồi vẽ lại, nên chạy lại được
nhiều lần. Nhưng nó vẽ lại nút và chữ ở dạng gốc, nên các bước phía sau phải chạy lại theo.

| Bước | Script | Tham số | Việc |
|---|---|---|---|
| 1 | `build_silo_frame.py` | `<dpa> <donor> <icon>` | khung chung: logo, user, thanh bên |
| 2 | `build_fill_page.py` | `<dpa> <icon>` | trang Nạp + các mặt dùng chung |
| 3 | `build_home_pages.py` | `<dpa> <icon>` | trang Xả và Phối trộn |
| 4 | `build_setting_page.py` | `<dpa> <icon>` | lưới Settings + đầu trang của mọi trang con |
| 5 | `build_calibration_page.py`, `build_info_pages.py`, `build_data_page.py` | `<dpa> <icon>` | Hiệu chỉnh, About, Thông số, Cảnh báo |
| 6 | `build_clean_page.py` | `<dpa> <icon> <hmi_map.json>` | trang Làm sạch đường ống, hàng tab Home |
| 7 | `build_system_tiles.py` | `<dpa> <icon>` | ô Settings dùng chức năng của panel, trang Ngôn ngữ |
| 8 | `translate_silo.py` | `<dpa> <icon>` | mọi chữ sang Anh / Việt / Pháp |
| 9 | `bind_plc.py` | `<dpa> <hmi_map.json>` | địa chỉ `$` sang DB của PLC, viết lại alarm |
| 10 | `build_account_pages.py` | `<dpa> <icon>` | Login, Quản lý tài khoản |
| 11 | `build_io_page.py` | `<dpa> <icon> <hmi_map.json>` | bảng điều khiển tay có khoá liên động |
| 12 | `build_overview_page.py` | `<dpa> <icon> <hmi_map.json>` | Tổng quan 6 bồn |
| 13 | `build_recipe_page.py` | `<dpa> <icon> <hmi_map.json>` | công thức trong Enhanced Recipe của panel |
| 14 | `apply_security.py` | `<dpa> <icon>` | trang khởi động = Login, nút cần cấp 8 |
| 15 | `close_popups_on_leave.py` | `<dpa>` | đóng popup khi rời trang |

Hai bước cuối luôn chạy sau cùng, đúng thứ tự đó: mọi script trang vẽ lại nút Goto không kèm
macro và không kèm quyền.

`<donor>` và đường dẫn dự án mẫu ghi ở đầu mỗi script (hằng `DONOR`, `OLD`, `SETUP_DONOR`).
Chạy ở máy khác thì sửa các hằng đó trước.

## Nối PLC

- Trang dựng trước trên bộ nhớ trong của panel (`$2xx..$7xx`), chạy được trên emulator khi chưa có PLC.
- PLC giữ một DB trao đổi riêng cho panel (truy cập chuẩn, số nguyên x10, chuỗi 20 ký tự).
  `hmi_map.json` là bảng thành viên → địa chỉ, sinh từ nguồn DB phía PLC; nó thuộc dự án PLC nên
  không nằm trong repo này.
- `bind_plc.py` đổi `$` sang địa chỉ DB theo bảng `BIND`. Chạy lại sau mỗi lần chạy script trang.
- Thêm thành viên DB thì thêm ở **cuối**. Buộc phải xếp lại DB thì
  `rebind_hmi_map.py <dpa> <map cũ> <map mới>` dời theo tên thành viên, và dừng không lưu nếu
  dự án còn dùng thành viên đã bị xoá.
- HMI đã giữ dữ liệu nào (công thức trong Enhanced Recipe) thì PLC chỉ cần một cấu trúc khớp
  đúng một dòng của nó, không dựng lại cả kho.

## Luật khi đụng tới DIAScreen

- DIAScreen không khoá file và không tự biết file đổi. Sau khi ghi, đừng bấm Save trong editor:
  bản trong bộ nhớ nó cũ hơn và sẽ đè mất phần vừa ghi.
- Kiểm hộp thoại **trước** khi gửi lệnh đóng. Lệnh đóng không rút lại được.
- DIAScreen chỉ giữ một dự án: mở file thử là đóng file người dùng đang mở. File thử đặt tên
  khác hẳn file thật, vì cửa sổ được tìm theo tên file.
- Khi lưu, DIAScreen dựng lại cả kho ảnh và tìm ảnh theo `PictureOffset`. Đừng vá ảnh tại chỗ
  trên file nó đã lưu; render lại rồi dựng kho mới (`frame.prune_bank`).
- Emulator có thể đang chạy một bản sao cũ. Kiểm dòng lệnh của tiến trình trước khi kết luận
  lỗi nằm ở file nào.

## Thêm một trang mới

1. Chép cách làm của `build_home_pages.py`; lấy mặt nút, ô chọn, popup từ `build_fill_page.py`.
2. Đặt tiền tố riêng cho tên phần tử (`ov_`, `io_`, `rc_`…) và xoá theo tiền tố ở đầu `main`.
3. Phần tĩnh Delta không vẽ được thì render thành ảnh qua `frame.static`; chữ tĩnh là phần tử
   Text, đường kẻ là Line.
4. Mọi chữ qua `silo_i18n.words(element, (en, vi, fr), size)`.
5. Trang Home thì gọi `silo_tabs.clear()` → `faces()` → `place()`. Trang con Settings thì để
   `build_setting_page.py` vẽ đầu trang, nội dung bắt đầu từ `CONTENT_TOP`.
6. Trang cần quyền thì thêm nút mở nó vào `GUARDS` của `apply_security.py`; trang có nhiều đường
   vào thì liệt kê đủ mọi nút.
7. Thêm script vào bảng chuỗi ở trên và vào bảng script của skill phong cách.

## Sau khi sửa skill

Skill dùng hằng ngày nằm ở `~/.claude/skills`. Sửa ở đó xong thì chép lại vào `skills/` của repo
rồi commit; máy khác cài bằng `powershell -File install-skill.ps1`.
