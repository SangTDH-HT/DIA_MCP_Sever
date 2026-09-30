# Bảo mật, tài khoản, nhật ký thao tác (sách tr.606–612, 687–693, 705–707)

## Account and Password (Sách)
- Cấp **0–9** (nhiều tài khoản mỗi cấp, đăng nhập đồng thời được), **cấp 10** = mật khẩu cao nhất (mặc định `12345678`), dùng cho upload/download, format, mã hoá file.
- Tên ≤24 ký tự (không trùng), mật khẩu ≤128, mô tả chỉ chữ Latin/số; tổng ≤1000 tài khoản.
- Simple Password: 7 cấp, mật khẩu 8 ký tự hex 0–F.
- RFID login; nhập/xuất `accounts.csv` (nút Import/Export Account; xuất phải mã hoá, mật khẩu mạnh).
- **User Login Screen** theo từng cấp (screen Login/Logout tự làm).

## Security (Sách)
Mật khẩu cao nhất bắt buộc mạnh (≥8, hoa, thường, số, ký hiệu `!$#%`), **cấp khởi động mặc định** 0–10, *Check password when downloading*, *Screen upload prohibited*, báo thiếu cấp (biểu tượng), không hiện hộp đăng nhập khi thiếu cấp, giấu tài khoản cấp thấp, bảng mật khẩu bắt buộc mạnh, xác nhận khi Restore, giới hạn số lần cập nhật qua USB; **Logout khi hết thời gian** (phút), khoá tài khoản sau N lần sai, lần bấm đầu chỉ đăng nhập (bấm lại mới làm), đổi mật khẩu lần đầu, thời gian tối thiểu giữa hai lần đổi, không dùng lại mật khẩu, bàn phím mật khẩu.

## Đăng nhập bằng tham số nội bộ (Sách, tr.705–707)
`ACCOUNT` (tài khoản đang đăng nhập, Character Display), `SetUserAccount` / `SetUserPassword` (Character Entry, hiện ***) / `SetUserLevel` (0–10), `Login` / `Logout` (ghi 1 để kích, về 0 khi xong), `LoginResult` / `LogoutResult` (Success/Fail), `AddUserAccount` + `AddUserAccountResult`, `DeleteUserAccount` + Result, `ChangeUserPassword` + `ChangePasswordResult`, `CurrentUserLevel`, `AdminLogin`, `AccountStatus` (Unexpired/Unlocked/Expired/Locked), `UserDescription`, `RFIDSerialNumber`, `SetRFIDSerialNumber`, `SetUserDescription`. Chỉ dùng khi tài khoản **không** phải Simple Password.
→ Trang đăng nhập tự vẽ trên Delta làm theo đường này (Silo có `build_login.py` - kiểm lại theo danh sách trên).

Control Block: b8–b11 General Control đặt cấp người dùng (hoặc Advanced Level Access Control b0–b3, b15 cấp cao nhất); Status Block đọc lại.

## Operation Log (Sách)
Data Management > Operation Log Setting: Enable, **Trigger Address** (bit bật mới ghi), lưu CSV (mặc định 10 000 dòng; HMI tối đa 10 000; USB/SD: đầy thì ghi đè hoặc dừng; giới hạn số file/cỡ file), cột + định dạng ngày giờ, *Ignore operation Log* từng phần tử (`IgnoreHistOP`). Phần tử **Operation Log Table** (`.dpa` 9.5): màu, cột, tiêu đề, ngày giờ, nút.
Electronic record (Configuration > Industry Application) ép ghi CSV có checksum, xem bằng `Utility\eRecordViewer`.

## Thực tế
- Nút Password Table = 12.2, Set Low Security = 12.5 (có trong HMI_AThanh).
- Trang Account Management của Silo đang trống - làm bằng tham số nội bộ ở trên + Character Entry. Chưa kiểm.
