# Recipe (sách tr.580–605; Control Block tr.84–109)

## Ba loại (Sách)

| Loại | Kích thước | Định dạng | Thanh ghi |
|---|---|---|---|
| 16-Bit | Length × Groups, mỗi cái 1–65535, tổng ≤50 MB | word | `RCP`, `RCPNO` |
| 32-Bit | như trên | Signed/Unsigned/Floating (integer+fraction ≤7 chữ số) | `RCP`, `RCPNO`, `RCPG` (≤255 nhóm) |
| **Enhanced** | **Field 1–2048**, **Group 1–65535**, có **Name** (Unicode, mọi thứ tiếng) | từng field: BCD / Signed / Unsigned / Hex / Floating / **Char (≤32 word = 64 ký tự, Unicode)**; Length 1/2/4 | `ENRCP`, `ENRCPNO`, `ENRCPG`, **`ENRCPGNAME`**, `*ENRCP` |

- Recipe Storage: HMI (ROM, giữ khi tắt), USB, USB2, SD. Liên tục hoặc rời (mỗi field một địa chỉ đọc). Nhập/xuất `.rcp` (16-bit), `.csv`, `.xlsx` (Enhanced).
- **Bộ đệm**: RCP0…RCP(L−1) là recipe đang chọn; dữ liệu thật bắt đầu từ RCP(L). Tổng thanh ghi L × (G+1). `RCPNO`/`RCPG` **không giữ khi mất điện**.
- `ENRCPGNAME`: tên nhóm công thức, nhập/hiện bằng **Multi-language Input**; nhập tên để gọi công thức.
- `*RCP` / `*ENRCP`: gián tiếp trong vùng recipe.

## Đọc/ghi PLC (Sách)
Control Block → *Recipe Control* / *Enhanced Recipe Control*: b0 đổi số recipe, **b1 đọc PLC→HMI**, **b2 ghi HMI→PLC**, b3 đổi nhóm, b8–b15 số nhóm; Status Block trả trạng thái tương ứng. Ví dụ sách: nút Momentary `$50.1` đọc, `$50.2` ghi.

## Recipe Viewer (Sách) - `.dpa` **19.10** "ENRCP Viewer"
ENRCPG Read Address (hằng/địa chỉ), RCPNO write address (dòng chọn → địa chỉ), Recipe Type 1/2/3, nhảy tới hàng/cột bằng trigger, Read Only, Show all / chọn cột, độ rộng cột, bảo mật, nút chức năng.

## Áp dụng cho Silo (gợi ý, chưa kiểm)
Trang **Công thức**: thay vì PLC giữ tên + popup tự dựng, có thể dùng Enhanced Recipe - mỗi công thức một group, tên ở `ENRCPGNAME`, các field là khối lượng từng bồn; Recipe Viewer để chọn/sửa; Control Block b2 để đẩy xuống PLC. Cần Sáng quyết vì đổi cách PLC nhận dữ liệu.

## Thực tế
- OTL-120 có ENRCP Viewer (`PROFILE LIST`) và ô nhập `ENRCP1..6` trong HMI_AThanh `scr_Blend` - donor sẵn.
