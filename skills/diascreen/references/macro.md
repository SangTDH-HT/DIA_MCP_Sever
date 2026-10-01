# Macro (sách DOPSoft V4 chương 24, tr.1576–1833 - `1.Document\Manual_DOPSoft_V4.pdf`)

Sách DIAScreen 1.6.1 không có tập lệnh macro; DIAScreen dùng cùng bộ lệnh với DOPSoft 4.

## Loại macro (Sách)

| Loại | Chạy khi | Ở đâu trong `.dpa` |
|---|---|---|
| On / Off Macro | nút Set ON/OFF, Maintained, Momentary chuyển trạng thái **do người bấm** (một lần) | `ButtonOnMacroLen` / `ButtonOffMacroLen` |
| Before / After Execute | mọi nút và ô nhập: trước / sau hành động của phần tử | `BeforeExecMacroLen` / `AfterExecMacroLen` |
| Screen Open | mở screen; screen chưa làm gì khác cho tới khi xong | `[Screen] OpenMacroLen` |
| Screen Close | đóng / rời screen, một lần | `CloseMacroLen` |
| Screen Cycle | lặp theo **Macro Cycle Delay** (mặc định 100 ms) sau Open | `CycleMacroLen`, `CycleMacroDelayTime`, `EnableCycleMacro` |
| Submacro | 512 cái × 512 dòng, gọi `CALL n` (hoặc bí danh ≤64 ký tự), lồng ≤6 tầng, có mật khẩu | (chưa xác định section) |
| Initial | một lần khi HMI khởi động | `[Application] InitialMacroLen` |
| Background | lặp mãi, mỗi chu kỳ chạy **N dòng** (Background macro update cycle 1–512) | `BackgroundMacroLen` |
| Clock | lặp mãi, **chạy hết một lượt** mỗi Clock Macro Delay (100 ms mặc định, ≤65535), ưu tiên Low/Medium/High | `ClockMacroLen` |

Mỗi macro ≤512 dòng, ≤640 byte/word. Screen cycle macro manager bật/tắt cycle macro từng screen (tắt khi chưa có PLC).
Trạng thái nút đổi do PLC/macro khác → On/Off/Before/After **không chạy**.

## Cú pháp (Sách)
Mỗi dòng một lệnh; `#` chú thích; hậu tố kiểu **`(W)` / `(DW)` / `(Signed W)` / `(Signed DW)`** - DW chiếm 2 thanh ghi mỗi địa chỉ. Biến: bộ nhớ trong (`$`, `$M`, `*$`, recipe…), thanh ghi PLC (`{Link}st@addr`), hằng số, chuỗi `"…"`. Lệnh số thực (FADD…) luôn `(Signed DW)`.

## Tập lệnh (Sách)

| Nhóm | Lệnh |
|---|---|
| Số học | `V1 = V2 + V3` (`- * / %`), `V1 = biểu thức` (vd `$1 = $2 + $3 - 57 * $4`), `MUL64`, `ADDSUMW(start, len)`, `FADD FSUB FMUL FDIV FMOD`, `SIN COS TAN COT SEC CSC` (góc số nguyên, kết quả Floating) |
| Logic | `\|` OR, `&&` AND, `^` XOR, `NOT`, `<<`, `>>` |
| Chuyển dữ liệu | `V1 = V2` (MOV), **`BMOV(dst, src, len)`**, `V1 = ArrayCopy(dst, dstOff, src, srcOff, len)`, `FILL(dst, value, len)`, **`FILLASC(dst, "chuỗi")`**, **`V1 = STRCAT(dst, src, maxLen)`**, `V1 = FMOV(V2)` |
| Chuyển đổi | `BCD`, `BIN`, `TODWORD`, `TOWORD(src, lenByte)`, `TOBYTE`, `SWAP(dst, src, len)` (đảo byte), `XCHG`, `MAX`, `MIN`, `TOHEX`, `TOASC`, `FCNV` (int→float), `ICNV` (float→int), **`V1 = SPRINTF(dst, "%d %u %c %x", v1..v20)`** |
| So sánh | `IF a == b THEN GOTO LABEL n` (`!= > >= < <=`, `(a && b) == 0/!= 0`, `== ON/OFF`, `IFB`), `IF … THEN CALL n`, **`IF … / ELSEIF … / ELSE / ENDIF`** (lồng ≤7; lỗi biên dịch cho ≤6), `V1 = FCMP(a, b)` (0 bằng, 1 lớn, 2 nhỏ) |
| Luồng | `GOTO LABEL n`, `LABEL n` (không trùng trong một macro), `CALL n` (số hoặc địa chỉ chứa số), `RET` (cuối submacro), `FOR n … NEXT` (lồng ≤10), `END` |
| Bit | `BITON b`, `BITOFF b`, `BITNOT b`, `b1 = GETB b2` |
| Truyền thông | `INITCOM(com, if, data, parity, stop, baud, flow)` (mã: COM1..3 = 0..2; RS232/422/485 = 0/1/2; baud 9600 = 6, 19200 = 8, 38400 = 10, 115200 = 12), `SELECTCOM`, `PUTCHARS/GETCHARS(buf, lenByte, timeoutMs)`, `CLEARCOMBUFFER`, `ADDSUM`, `XORSUM`, `CHRCHKSUM`, `LOCKCOM/UNLOCKCOM` (phải cặp trong **cùng** macro), `CLOSECOM`, `STATIONCHK/ON/OFF`, `IPON/IPOFF/IPCHANGE(link, ip1..4, port)`, **`COMLINKSTATUS(com)` / `NETLINKSTATUS(link)`** (trả mã lỗi truyền thông, 0 = tốt) |
| Vẽ | `RECTANGLE/LINE/POINT/CIRCLE(start)` - tham số ở các word liên tiếp |
| File | `FileSlotRead/Write/Remove/GetLength/Export/Import/GetName/SetName/GetID` |
| Khác | `TIMETICK` (ms từ khi bật), `GETLASTERROR`, `Delay(ms)` (**dừng mọi thứ** trong lúc chờ), `GETSYSTEMTIME/SETSYSTEMTIME(start)` (năm, tháng, ngày, thứ, giờ, phút, giây), `GETHISTORY`, `EXPORT`, `EXRCP16/32`, `IMRCP16/32`, `EXENRCP/IMENRCP`, `EXHISTORY(id, tên, 2=USB/3=SD)`, `EXALARM`, `EXALARMGROUP`, `DISKFORMAT`, `BMPCAPTURE`, `PLCDOWNLOAD`, **`OPENSCREEN(n)`**, **`CLOSESUBSCREEN(n)`** (n hằng hoặc địa chỉ; **không dùng được trong Screen Open/Close/Cycle** - lỗi −83), `GetCircleCenter`, `VAR tên` |

## Mã lỗi (Sách)
Biên dịch: −91 biến cục bộ trong tham số liên tục, −93 submacro không có, −97 IF lồng quá, −98 thiếu ENDIF, −100 thiếu LABEL, −101 đệ quy, −102 FOR lồng >10, −104/−105 FOR/NEXT lệch, −106 LABEL trùng, −107 RET ngoài submacro, −109 sai định dạng địa chỉ, −110/−111 địa chỉ recipe, −112..−114 cấu hình COM.
Trên HMI (`GETLASTERROR`): −10 GOTO, −11 tràn stack submacro, −12 submacro rỗng, −13/−14 lỗi đọc/ghi (thường là PLC), −15 chia 0, −23 INITCOM, −25 COM, −28 IF/ELSE, −32 lỗi ổ đĩa, −70..−72 sai biến 1..3, **−83 lệnh bị cấm ở chỗ này** (vd OPENSCREEN trong Cycle), −40..−64/−84..−87 lỗi file/FileSlot.

## Thực tế `.dpa`

- Blob macro: mỗi dòng một bản ghi, CRLF ngăn; đầu bản ghi `02 'REV%' 02 01 <opcode>`, rồi câu lệnh dạng chữ (đọc được) + toán hạng đã tách + `Var2..Var4`, cờ, 8 byte 0. `dpa/macro.statements()` đọc ra chữ.
- Opcode đã biết: **0x84 OPENSCREEN**, **0x85 CLOSESUBSCREEN** (ghi được, byte giống DIAScreen - Đã kiểm 29/09), 0x1E gán `=`, 0x41 FMOV (chỉ thấy khi đọc). Lệnh khác: chưa ghi được → muốn dùng thì gõ trong DIAScreen, hoặc tạo mẫu trong DIAScreen rồi chép blob.
- **Ghi được thêm (Đã kiểm 30/09, DIAScreen compile "OK", 0 lỗi, trên dự án DOPSoft 4.00):** blob = `02 'REV'` rồi từng bản ghi + CRLF; bản ghi = 4 byte khung + 5 chuỗi (uint32 độ dài + chữ) + `01 01 01 01` + 8 byte 0. Khung: gán `$a = b` → `25 07 03 1E`, chuỗi (câu, a, b, Var3, Var4); trừ/nhân `$a = x - y` / `x * y` → `04 0F 07 01` / `04 0F 07 02`, chuỗi (câu, a, x, y, Var4), x hoặc y là hằng hay địa chỉ đều cùng khung; `IF a == b` / `IF a > b` → `14 0E 03 48` / `14 0E 03 4A`, câu có 2 dấu cách cuối, chuỗi (câu, a, b, Var3, Var4); `ENDIF` → `00 00 00 5D`, chuỗi (ENDIF, Var1..Var4). Ngoài ra đọc được: `ELSE` 0x5C, `IF >=` 0x4B, `IF <=` 0x4D, `BITON`/`BITOFF` khung `0A 00 01 1B/1C`. Cộng hai số hạng chưa có mẫu - dùng `x - y` hoặc `hằng - $a` thay. Mẫu dựng: `DeltaDpa_src/build_test_trend.py`.
- Biên dịch DIAScreen bằng **phím F7** gửi vào cửa sổ chính (PostMessage WM_KEYDOWN) - bấm ngầm vào nút ribbon Compile không ăn. Biên dịch cũng tự lưu file. Xem lỗi: khung Output, lọc Error (khung tự vẽ, không đọc chữ được → chụp PrintWindow).
- Viết dạng `OPENSCREEN 24` hay `OPENSCREEN(24)` đều gặp trong dự án thật.
- Cách dùng thật đã gặp (quét 30/09): nhiều nhất là gán `=`, `BITON/BITOFF`, `IF/ELSEIF/ELSE/ENDIF`, `OPENSCREEN/CLOSESUBSCREEN`, `CALL`, `FILLASC($5500, "Default user")`, `BMOV($M970, $M520, 30)`, `FADD/FDIV/FMUL(ENRCP…)` (Signed DW), `DELAY (500)`, `LABEL/END`, `FILL`, một ít `INITCOM/SELECTCOM/GETCHARS` (đầu cân serial).
- Chỗ chứa: phần tử 588 After / 332 On / 267 Off / 101 Before; screen 24 Cycle / 6 Open / 6 Close; `[Application]` 15 Background / 13 Initial / 13 Clock.

## Mẹo áp dụng
- Hiện tên bồn đang chọn không cần PLC: After macro của dòng chọn `BMOV($300, $310, 10)`… hoặc một Clock macro `IF $205 == 0 / BMOV($300, $310, 10) / ELSEIF …`. Hoặc dùng Read Offset (xem `element-common.md`). Chưa kiểm.
- Không đặt `Delay` dài trong Clock/Cycle macro (treo cả HMI).
