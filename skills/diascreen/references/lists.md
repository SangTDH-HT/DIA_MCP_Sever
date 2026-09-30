# Danh sách (sách tr.424–475)

## ComboBox / Drop-down / ListBox (Sách)

- Chọn một mục → ghi **giá trị state** của mục đó vào Write Address. Data Type Bit/Word/LSB; State Counts (Word 1–256); **State Index** = giá trị ghi cho state đó (0–65535). Chữ mỗi mục = chữ state (đa ngôn ngữ, Text Bank).
- ComboBox: Number of Rows 5–15 (mặc định 5), màu nền/màu chọn menu, chiều cao mục (mặc định 40, ≤ cao màn hình).
- Drop-down Menu: phải bấm nút xác nhận sau khi chọn; menu Glass/Solid/Gradient, cao/rộng, số mục mỗi trang.
- ListBox: mục hiện sẵn trên phần tử.
- Chung: Interlock, **Trigger Before/After Writing**, Invisible, Confirmation, Ignore Op Log, Security, Macro, Coord.

## GridBox (Sách)

Bảng dữ liệu tự định nghĩa đọc từ địa chỉ:
- Column Count ≤32, Initial Item Count ≤1000, Items per Page ≤100, **Start Address**, **Item Addr. Offset** (khoảng cách địa chỉ giữa hai dòng, ≤10000; nhỏ hơn số cột thì báo chồng).
- Kiểu cột: **State** (ảnh/chữ theo state), **String** (chữ từ địa chỉ), **Numeric**; rộng cột, căn, ẩn dòng (địa chỉ Hide Item ≠ 0 thì ẩn), ẩn giá trị theo bit, gộp ô, ẩn vạch dọc.
- Địa chỉ trả về: **Selected Item** (dòng đang chọn), Actual/Visible Item Count, Current/Total Page; Auto Update hoặc Update Data; trigger Page Up/Down, Previous/Next Item, Copy/Paste/Replace/Insert/Cut, Touch Protect, Select Item + Trigger, vùng đệm Buffer Start + Insert/Add/Add to last/Read/Write.
- Style: đánh số tự động, màu lưới/nền/chọn.

→ Đây là cách **chính hãng** hiện danh sách tên do người vận hành đặt (cột String) và biết dòng nào được chọn. Chưa kiểm trên `.dpa` (chưa có donor).

## Khác (Sách)

| Phần tử | Ghi chú |
|---|---|
| PDF Viewer / Text Viewer | xem PDF/TXT/CSV trên USB/SD; chỉ **một** viewer mỗi screen; Text Viewer chỉ UTF-8; zoom PDF 0–6 = full/50/75/100/125/150/200 % |
| FTP file list | chỉ DOP-300 |
| Text List | chỉ DOP-107H cầm tay; sửa nội dung FileSlot |
| File Browser | duyệt/xoá/đổi tên file; Control Address 1 xoá / 2 đổi tên / 3 ghi đường dẫn / 4 lên trang; mã trả về −1..−8 |
| Picture Viewer | xem ảnh trên USB (2) / USB2 (6) / SD (3); chỉ một cái, chỉ trên screen thường |

## Thực tế `.dpa`

- **ComboBox 19.1**: `DataSourceType` 0 = gõ tay; các nguồn khác là tài khoản (`AccountOrder`, `ShowUserLevel`), instance (`InstOrder`, `ShowInstName`), lịch sử (`MaxDisplayDaysOfData`, `DisplayDataFormat`, `BufferID`) - **không** có nguồn "chữ từ địa chỉ" (đọc chuỗi trong HMIApp.exe 30/09). Viền do panel vẽ đen dù đặt `BorderColor`. Khoá: `PageLines`, `OptionsBKColor`, `OptionsSelectColor`, `OptionsHeight`, `OptionsSetHeight`.
- Drop-down 19.9 có trong OTL-120 (`Burner_keypad`); ENRCP Viewer 19.10 trong OTL-120 (`PROFILE LIST`).
- Ô chọn tên đổi được đang dùng ở Silo: nút mở popup + Character Display + popup các Set Constant (xem `delta-hmi-style`). Đã kiểm file; chưa kiểm chạm xuyên chữ trên emulator.
