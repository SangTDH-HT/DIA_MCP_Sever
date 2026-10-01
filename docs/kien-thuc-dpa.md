# Kiến thức DIAScreen / .dpa

Gom từ ghi chú làm việc 22/09–30/09/2026 khi dựng HMI Silo mới. Phần tóm tắt dùng hằng ngày nằm ở
`skills/delta-hmi-style/SKILL.md`; đây là bản đầy đủ kèm lý do và các lần vấp.

## Định dạng .dpa, cách sửa, bẫy đã gặp

Delta DIAScreen 1.6 tại `C:\Program Files (x86)\Delta Industrial Automation\DIAStudio\DIAScreen 1.6`.

**Không có API** (khảo sát 28/08/2026, kiểm lại 22/09/2026): không `.tlb`, không ProgID COM, không DLL SDK, không switch dòng lệnh. App Qt5 + di sản Borland C++. Bộ cài ở `G:\File_winrar_phan_mem\PhanMemPLC_HMI\DiaStudio` chỉ là installer online, Manifest rỗng, không kèm SDK và không có DIADesigner. Máy không cài DIADesigner-AX.

**Nhưng file `.dpa` đã mở được** (22/09/2026) — kết luận cũ "chỉ còn cửa Export/Import Excel" đã sai:

```
offset 0   'BM' | offset 6 'PDAB' | offset 14 BITMAPINFOHEADER (biSizeImage ở +34)
offset 54  pixel thumbnail
tiếp theo  gzip (deflate mức 6, mtime 0, byte OS 0x0b)  → mỗi byte XOR 0x64 → text INI
```

Ghi lại bằng đúng tham số gzip đó ra file **byte-identical** với bản gốc — đã kiểm trên 14 dự án thật (DOPSoft 4.00.10 → DIAScreen 6.6.2).

Bên trong là mô hình thiết kế đầy đủ: `[Application] [Screen] [Element] [State] [SubMacro] [Alarm] [Picture]`. Element thuộc về Screen đứng trước nó; `[State]` sau Element là trạng thái của nó. Hai dạng đọc theo độ dài chứ không theo dòng: chữ UTF-16LE (`wTextLen0=28`, rồi CRLF ngăn cách) và macro (`ButtonOnMacroLen=842`, CRLF nằm trong số đếm). Macro là bản ghi có chuỗi kèm uint32 độ dài, chuỗi đầu là câu lệnh đọc được (`BITOFF $4.1`, `OPENSCREEN 5`). Địa chỉ PLC dạng `{EtherLink1}2@DB13.DBX1954.1`, nội bộ dạng `$4.0`. `PLCIP0` là int32 có dấu, octet đầu ở byte cao.

**Công cụ**: `C:\Tia_Claude\DeltaDpa_src` — MCP `delta-dpa` (đã đăng ký trong `.mcp.json`), 14 lệnh: `open_project/list_screens/layout/screenshot_text/element/find/addresses/macros/alarms/set_property/set_text/rebind/pending_changes/save`. Chưa làm được: thêm object/screen mới, ghi ngược macro, rút ảnh từ `[Picture]`.

**Why:** đây là đường tự động hoá thiết kế Delta thật sự, ngang với Openness bên Siemens — đừng quay lại lối Excel bán thủ công nữa.

**How to apply:** đóng dự án trong DIAScreen trước khi ghi đè (editor giữ bản riêng trong bộ nhớ, bấm Save là đè ngược). `save` mặc định ghi ra file khác và luôn để lại `.bak`. Dự án thật để test ở `C:\OTL\OTL_SILO\OTL_Silo6\HMI\` và `C:\OTL\OTL120_SIE_2026_Sa\`. Xem `doc-screen-truoc-khi-lam` — luật đọc screen trước khi sửa áp dụng y hệt bên Delta.

**Sửa được lúc anh đang mở file** (22/09/2026): DIAScreen đọc hết `.dpa` lúc mở rồi **buông handle** — mở được exclusive ReadWrite trong khi editor đang mở, nên ghi đè lúc nào cũng được. Nó không tự biết file đổi. Cửa sổ chính là **MFC** (`Afx:` class, không phải Qt), `GetMenu` trả 0, và `DIAScreen.exe "%1"` mở file bằng dòng lệnh. Nhờ vậy `reload_in_editor` = PostMessage WM_CLOSE cho đúng cửa sổ (khớp theo stem trong title `DIAScreen - <tên> - [1 - <screen>]`) rồi chạy lại exe với đường dẫn. **Không bao giờ trả lời hộp thoại**: thấy dialog `#32770` của pid đó là dừng, vì đó là thay đổi người dùng gõ tay. Đừng bấm Save trong editor trước khi nạp lại — bản bộ nhớ cũ hơn sẽ đè mất.

**Va chạm 22/09/2026 — lệnh đóng không rút lại được.** `reload_in_editor` bản đầu gửi WM_CLOSE *rồi mới* dò hộp thoại. Sáng đang mở hộp thoại thuộc tính Character Entry → DIAScreen bật hỏi "save?" → Sáng bấm Lưu → bản cũ trong bộ nhớ editor **đè mất** hai nút vừa ghi, rồi app đóng hẳn. Đã vá: dò dialog `#32770` **trước**, có thì từ chối không gõ cửa; và nếu vẫn bị hỏi thì câu trả lời đúng là **KHÔNG LƯU**. Luật vận hành: sau khi ghi, đừng bấm Save trong DIAScreen; đóng hết hộp thoại thuộc tính rồi mới nạp lại.

**Nút Delta tô màu bằng ảnh, không bằng số.** Mỗi State nút có `Picture Name` + `PIB Name` (vd `PicBank02`/`NewHMI00002`) — hình dáng lấy từ picture bank. Quét 14 dự án: 810/864 nút không ảnh đều giữ nguyên `BgColor=#B4B4B4` mặc định, không ai đổi được. **Clone nút sang dự án khác là ảnh treo → nút vẽ ra khoảng trắng**; phải gỡ `Picture Name`/`PIB Name`/`PictureOffset`/`UsePictureCoord` thì mới về nút xám chuẩn. Clone chéo dự án cũng kéo theo `InterLockVar`/`ReadVar` của dự án nguồn — phải set `None` không thì nút chết. Goto Screen = type `1.10`, đích nằm ở `GoToScreenName` + `GoToScreenID`.

**Chữ và ảnh trong .dpa (22/09/2026).** Cỡ/tên phông nằm trong `[State]` theo **từng ngôn ngữ**: `FontSize0`/`FontSize1`, `FontName0`/`FontName1`, `FontRatio0/1` — **không có khoá `FontSize`**. Đặt nhầm là im lặng không ăn, chữ giữ nguyên của bản clone (Arial Black 28) rồi compile cảnh báo `Text width exceeds the element width`. `FontAlign` là bit: 1 trái, 2 giữa, 4 phải, +32 giữa dọc → 33 trái, 34 giữa, 36 phải (35 = trái+giữa, panel vẽ lệch; đính chính 30/09). Bẫy parser đi kèm: quy tắc "khoá kết thúc bằng Size là độ dài blob" khiến `FontSize1=16` **nuốt 16 byte kế tiếp** (đúng bằng dòng `FontRatio1=100\r\n`); round-trip vẫn đúng byte nên test không bắt được — chỉ khoá `...Len` và `Size` đứng một mình mới là blob.

**Ghi ảnh vào picture bank.** `[Picture]` = `Size=N` + N byte: 15 byte `DOP-100IMAGE1.0` rồi lặp `uint32 độ dài + BITMAPINFOHEADER 40 byte + pixel BGRA 32-bit lật ngược`. Không có tên trong kho; `Picture Name` = tiền tố (tên HMI) + số thứ tự 5 chữ số 1-based, `PIB Name`: 3 dự án cũ đều `PicBank02`, nhưng dự án mới ghi PicBank02 thì **DIAScreen lưu lại đổi hết sang `PicBank01` và dựng lại kho** (29/09) — cả hai đều hiện được. Khi lưu, DIAScreen **dựng lại cả kho ảnh**: đổi thứ tự, đánh lại số, và **tìm ảnh theo `PictureOffset`, không theo tên** (đường kẻ còn sót offset bị gắn nhầm logo). Nó cũng thu ảnh vào trong thân: Goto `Style=0` và Rectangle có lề **4 px hai bên, 1 px trên dưới** (giữ tỉ lệ), rồi lưu ảnh đã thu → kéo lại là nhòe. **Đã kiểm 29/09 bằng vòng DIAScreen tự lưu:** Goto `Style=3` giữ nguyên cỡ ảnh, không viền; Rectangle nới khung thêm lề đó thì ảnh vừa khít, **nhưng Rectangle vẫn vẽ nét nổi sáng 1 px (#F8F9FA) mép trên/trái, Style 0 hay 32768 như nhau** → ảnh tĩnh (logo, cụm user) cũng dùng Goto `Style=3`; nét sáng đó = pha 50% với `TransColor` (#FCFCFC) → đặt `TransColor` = màu tô là giả thuyết đang thử cho ảnh nền trang Fill (29/09, chưa xác nhận). **State Graphic 7.1 chừa lề 3 px hai bên, 0 trên dưới** (khác Rectangle 4/1); đường kẻ phải xoá hẳn các khoá Picture*. Tự lưu để kiểm: `PostMessage(hwnd, WM_COMMAND, 0xE103, 0)` (ID_FILE_SAVE của MFC). Mẫu: `restyle_silo_frame.py`. **Viền Rectangle không lấy `BorderColor`**: màu viền nằm ở `BDRStartColor/BDRMidColor/BDREndColor` (donor = 0, đen), còn `FgFillEndColor` là điểm dừng xám #808080 — đặt cả mấy khoá này vẫn **đen đậm trên emulator** (29/09) → panel vẽ viền Rectangle màu đen bất kể khoá màu. Tắt viền thì hình chữ nhật 1 px **biến mất** (emulator 29/09). **Đường kẻ phải là Line 10.1**: **màu ở state `FontColor`** (không phải FgColor — emulator ra #565656 đúng FontColor), `LineStyle` 0 = nét thường / 1 = mũi tên, `Style` 769 = ngang, 1025 = dọc; mẫu donor HMI_AThanh `scr_Overview#1` / `scr_I/O#0` (29/09, chờ Sáng xác nhận). **`PictureOffset` = vị trí byte của bản ghi ảnh (tính từ đầu blob, gồm 15 byte magic, trỏ vào uint32 độ dài)** — khớp đúng ảnh 2 và 9 của HMI_AThanh; ảnh mới phải đặt đúng số này. Kho rỗng ghi là `Size=0` + một dòng trống (Raw) — khi đổ ảnh vào phải gỡ dòng trống đó, donor chạy thẳng sang `[Background]`. Panel không trộn alpha nên PNG trong suốt phải bẹt xuống màu nền trước. Module `dpa/picbank.py`; mẫu dựng đầy đủ: `build_silo_frame.py` (29/09, khung HMI_Silo mới ở `C:\OTL\18.SILO_Ban_Moi`, base screen `Khung_Chung` qua `BaseScreenID`, nút = một Goto Screen mặt ảnh render sẵn).

**Trend clone sang dự án khác là lỗi compile** `Element buffer is undefined` — nó cần `[History]` khai bộ đệm (`HistoryCount`, `ReadVar01`…), dự án mới có `HistoryCount=0`.

**Chưa chốt được:** khoá nào tô nền phẳng cho Rectangle. Đời mới (VER 16, Silo) có `GradFillStartColor/EndColor`; đời cũ (OTL-120) **không có khoá đó**. Đặt `GradFillStartColor` + state `BgColor/FgColor` vẫn ra xám chuyển sắc. Đang chờ Sáng xem dải thử `F# S# G#` trong `C:\OTL\8.TestMCPHMIDelta\Roast2.dpa` Screen_1.

**Combo + macro + popup (30/09/2026).** ComboBox 19.1 chỉ lấy mục từ `DataSourceType` = gõ tay / tài khoản / instance / lịch sử — **không đọc chữ từ địa chỉ** → tên do người vận hành đặt phải dựng popup riêng (mẫu `pop_Silo` trong `build_fill_page.py`: nút mở `OPENSCREEN n`, dòng = Set Constant + `AfterExecMacro CLOSESUBSCREEN n`, Character Display 5.2 đè lên). **Ghi macro được rồi**: `dpa/macro.screen_statement()` sinh `OPENSCREEN`(0x84)/`CLOSESUBSCREEN`(0x85) đúng byte donor; độ dài gồm cả CRLF (`blob_eol=False`). Set Constant 1.7 không có khoá ảnh ở bất kỳ dự án nào → thay `states[0].items` bằng bản sao state của Momentary 1.1 (cùng bố cục, thêm Picture*) — DIAScreen tự lưu vẫn giữ. Popup: toạ độ phần tử tính từ góc popup; khung screen lấy từ donor OVERVIEW + AuxKeyElement.

## Quy trình đóng/mở DIAScreen khi sửa

Sáng 29/09/2026: "em tự đóng rồi làm xong tự mở cho anh xem". Đừng dừng lại nhờ anh đóng DIAScreen.

**Why:** nhờ đóng/mở là thêm một vòng chờ; lần trước cách "ghi rồi mới reload" làm bật hộp thoại lưu, anh bấm Có và bản sửa bị đè mất.

**How to apply:** thứ tự luôn là `close_in_editor` (MCP delta-dpa; hộp thoại lưu → tự bấm Yes để giữ phần anh sửa tay) → `open_project` / sửa / `save` → `open_in_editor`. Chỉ dừng khi đang có hộp thoại thuộc tính mở (anh đang sửa dở). Code ở `DeltaDpa_src/dpa/editor.py` (`close_document`, `open_document`); MCP phải khởi động lại mới thấy hai lệnh mới. Xem `diascreen-khong-co-api`.

## Phông chữ

Sáng 29/09/2026: "font chữ mặc định arial nhé" — khi dựng HMI Silo mới (C:\OTL\18.SILO_Ban_Moi), mọi chữ dùng Arial
(`arial.ttf`, chữ đậm `arialbd.ttf`), kể cả chữ em render sẵn vào ảnh mặt nút. Không dùng Segoe UI.

**Why:** trước đó em render mặt nút bằng Segoe UI cho giống hình mẫu; Sáng muốn đồng bộ với phông mặc định của panel.

**How to apply:** `build_silo_frame.py` đã đổi sang Arial; phần tử chữ Delta đặt `FontName0/1 = Arial`.
Xem `diascreen-khong-co-api`.
