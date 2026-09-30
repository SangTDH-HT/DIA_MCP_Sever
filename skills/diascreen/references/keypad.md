# Bàn phím (sách tr.49–56, 418–423, Configuration – Global Keypad)

## Keypad element (Sách)
- Keypad(1) thập phân, (2) hex, (3) ASCII. Là **phần tử nhóm**: nhấp đúp để sửa; *UnGroup* để dời từng phím.
- Mode mỗi phím: `[ESC]` (huỷ; nếu nằm trên subscreen thì **đóng luôn subscreen**), `[ENT]`, `[CLR]`, `[DEL]`, `[BKSP]`, `[Home]`, `[End]`, `[Left]`, `[Right]`, `[ASCII]` (mã ký tự).
- Style Standard/Raised, màu, Transparency, smooth animation, chữ/ảnh theo state.

## Keypad Screen (Sách)
Tạo screen loại Keypad, kéo mẫu từ Element Bank (`Keypad-Template`, vd `KP(1)_01_Big`, `KP_Swedish_Big`) hoặc dựng Keypad element. Ô nhập chọn *Custom Keypad* = screen đó. Xoá screen đang được dùng → hộp *Keypad Lists* để đổi hàng loạt (No Action / System / Custom).

## Global Keypad Settings (Configuration) (Sách)
Bàn phím hệ thống cho Decimal / Binary / Hex / ASCII: sửa bố cục/màu/chữ, hoặc trỏ tới Custom Keypad screen; áp dụng Not apply / Apply to all / Apply to new.

## Password keypad (Security) (Sách)
Default / Simple / Customized (Simple không dùng được với mật khẩu mạnh).

## Thực tế `.dpa`
- Ô nhập: `UseCustKeypad`, `KeypadScreenID`, vị trí `KeyPadLeft/Top/Right/Bottom`, `TitleHeight`, chữ các phím hệ thống `wKPFStringLen000..006-00x` (vd "Numeric Keypad", "CLR", "DEL", "Enter"), `KPFontSize/Name/Color`, `KPBkgndColor`. Screen: `IsKeypadScreen`.
- Chưa làm bàn phím riêng cho Silo; muốn bàn phím cùng phong cách thì dựng Keypad Screen với nút mặt ảnh - cần donor Keypad element (mã chưa biết; tạo một cái trong DIAScreen rồi đọc).
