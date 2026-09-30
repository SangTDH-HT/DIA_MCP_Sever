# Screen (sách tr.45–67)

## Loại screen (Sách)

| Loại | Dùng làm gì | Ghi chú |
|---|---|---|
| **Screen** | màn hình chính, cỡ cố định theo model | có thể gắn **Base Screen** (Single/Multiple): kéo screen vào vùng Base; phần tử của base không sửa được từ screen con |
| **Subscreen** | cửa sổ nổi trên screen; gọi bằng macro hoặc alarm; hoặc nhúng bằng phần tử *Embedded Subscreen* (DOPSoft tr.1331: số subscreen, X, Y lấy từ **word bộ nhớ trong** → đổi nội dung một vùng trên màn hình theo địa chỉ; có Invisible Address; không đặt trên subscreen) | **không** đặt được Embedded Subscreen, Picture Viewer, Gantt Chart trên subscreen |
| Keypad Screen | bàn phím tự làm (kéo Keypad-Template từ Element Bank, vd `KP(1)_01_Big`) | không làm màn hình khởi động; thuộc tính như Subscreen |
| Print Screen | trang in (chỉ HMI có máy in) | Goto Screen không được trỏ tới |
| Template Screen | mẫu PDF (header trên vạch đỏ, footer đánh số trang) cho nút Template Output | kiểu này không đổi được |
| Confirmation Window Screen | hộp xác nhận tự thiết kế; phần tử chọn *Confirmation Window = Custom* | thuộc tính như Subscreen |
| Login / Logout Screen | màn đăng nhập tự thiết kế khi cấp bảo mật không đủ, hoặc gọi bằng Goto | có thể gán theo từng cấp ở Security Setting; cái đặt trên phần tử thắng |
| Add/Delete User Account, Change Password Screen | quản lý tài khoản trên HMI | thêm/xoá chỉ cho cấp **thấp hơn** cấp đang đăng nhập |
| Bind Cloud Service Screen | gắn DIACloud (DOP-300) | |

## Thuộc tính screen (Sách)

- Screen No. (không trùng), Screen type, **Macro Cycle Delay** (chu kỳ Clock/Cycle macro), **Screen Lock Bit** (ON = khoá không chuyển trang được).
- Subscreen: Width/Height (≤ cỡ screen), **Position** (giữa màn hình hoặc X,Y góc trên trái), Show Border, **tự đóng sau N giây** (0 = không), Title Bar (chữ đa ngôn ngữ).
- Quản lý: New / Edit / Cut-Copy-Paste (Shift chọn nhiều), *Paste the specified screen* (số trùng thì tự lùi số), Delete (không hoàn tác), Export/Import ảnh nền (.bmp/.png/.svg…) hoặc dữ liệu screen `.dpi` (chỉ Screen/Subscreen; kéo theo base screen; Goto trỏ screen khác sẽ báo lỗi compile), Rename (đa ngôn ngữ), **Set as Default screen**, Password protection (8 ký tự 0-9/A-F), Screensaver.

## Thực tế `.dpa`

| Thuộc tính | Khoá section `[Screen]` | Ghi chú |
|---|---|---|
| số / tên | `ID`, `wTextLen` (+ `wScreenDESCTextLen000/001`) | |
| loại | `ScreenType` 0 = Screen, 1 = Subscreen; `IsSubScreen`, `IsKeypadScreen`, `IsConfirmScreen`, `IsTemplateScreen`, `IsPrintTypeScreen`, `IsExternalScreen` | Đã kiểm 29/09 (0/1) |
| base screen | `BaseScreenID` (0 = không) | Đã kiểm: Silo dùng `Khung_Chung` làm base của mọi trang |
| cỡ popup | `Width`, `Height`, `DocSizeX/Y` | đặt cả hai cặp |
| vị trí popup | `CenterSubScreen` (0/1), `SubScreenX`, `SubScreenY` | Đã kiểm 29–30/09: popup đè đúng toạ độ |
| tự đóng | `AutoCloseTime` | |
| khung / tiêu đề | `IsUseFrame`, `IsUseTitleBar`, `wTitleTextLen000/001`, `TitleTextFont*` | |
| nền | `BgColor` (BGR) | |
| macro | `OpenMacroLen`, `CloseMacroLen`, `CycleMacroLen`, `EnableCycleMacro`, `CycleMacroDelayTime` | |
| khoá màn hình | `ScreenLockVar` | |
| mật khẩu screen | `ScreenProtect`, `ScreenPassword` | |

- Toạ độ phần tử trong subscreen tính **từ góc subscreen**. Đã kiểm.
- Mở/đóng popup: macro `OPENSCREEN n` / `CLOSESUBSCREEN n` (`dpa/macro.screen_statement`). Đã kiểm 29/09 (byte giống DIAScreen).
- Screen mới: nhân bản `[Screen]` + `[AuxKeyElement]` đi kèm của screen có sẵn (`edit.clone_screen` cùng dự án; khác dự án thì copy tay như `fill.silo_popup`). DIAScreen tự lưu vẫn giữ. Đã kiểm.
- Popup mở ở đáy màn hình: tính `SubScreenY` để không tràn 600 (mở lên trên). Đã kiểm 30/09.
