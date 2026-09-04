#!/usr/bin/env python3
"""
send_kakao.py - KakaoTalk Windows 자동 메시지 전송 (Win32 SendInput)

Inspired by kmsg (https://github.com/channprj/kmsg)
Windows/WSL port using Win32 SendInput API

사용법:
  python send_kakao.py -r "홍길동" -m "메시지"
  python send_kakao.py -r "홍길동" -f note.md --convert-md
  python send_kakao.py --list

WSL에서 실행:
  powershell.exe -Command "python '<UNC path>' -r '홍길동' -m '테스트'"
"""

import time
import sys
import argparse
import re
import io

# Windows 콘솔 UTF-8 출력 강제
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

IS_WINDOWS = sys.platform == 'win32'

if IS_WINDOWS:
    import ctypes
    import ctypes.wintypes as wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # ─── SendInput 구조체 ───
    INPUT_KEYBOARD = 1
    INPUT_MOUSE = 0
    KEYEVENTF_UNICODE = 0x0004
    KEYEVENTF_KEYUP = 0x0002
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    VK_RETURN = 0x0D
    VK_ESCAPE = 0x1B
    VK_CONTROL = 0x11
    VK_DELETE = 0x2E
    SW_RESTORE = 9
    WM_SETTEXT = 0x000C
    WM_GETTEXTLENGTH = 0x000E
    WM_GETTEXT = 0x000D
    WM_CHAR = 0x0102

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                     ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                     ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                     ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                     ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]
        _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]

    class RECT(ctypes.Structure):
        _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                     ("right", wintypes.LONG), ("bottom", wintypes.LONG)]

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    # ─── 저수준 입력 함수 ───

    def _click_at(x, y):
        """절대 좌표에서 마우스 클릭"""
        user32.SetCursorPos(x, y)
        time.sleep(0.05)
        inp = (INPUT * 2)()
        inp[0].type = INPUT_MOUSE
        inp[0]._input.mi.dwFlags = MOUSEEVENTF_LEFTDOWN
        inp[1].type = INPUT_MOUSE
        inp[1]._input.mi.dwFlags = MOUSEEVENTF_LEFTUP
        user32.SendInput(2, ctypes.pointer(inp[0]), ctypes.sizeof(INPUT))

    def _dblclick_at(x, y):
        """절대 좌표에서 더블클릭"""
        _click_at(x, y)
        time.sleep(0.08)
        _click_at(x, y)

    def _click_center(hwnd):
        """윈도우 중앙 클릭"""
        rect = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        _click_at((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2)

    def _press_key(vk):
        """가상 키 전송 (SendInput)"""
        inp = (INPUT * 2)()
        inp[0].type = INPUT_KEYBOARD
        inp[0]._input.ki.wVk = vk
        inp[1].type = INPUT_KEYBOARD
        inp[1]._input.ki.wVk = vk
        inp[1]._input.ki.dwFlags = KEYEVENTF_KEYUP
        user32.SendInput(2, ctypes.pointer(inp[0]), ctypes.sizeof(INPUT))

    VK_SHIFT = 0x10

    def _type_unicode(text):
        """SendInput UNICODE로 타이핑 (줄바꿈 = Shift+Enter)"""
        for char in text:
            if char == '\n':
                # Shift+Enter = 카카오톡 줄바꿈
                inp = (INPUT * 4)()
                inp[0].type = INPUT_KEYBOARD
                inp[0]._input.ki.wVk = VK_SHIFT
                inp[1].type = INPUT_KEYBOARD
                inp[1]._input.ki.wVk = VK_RETURN
                inp[2].type = INPUT_KEYBOARD
                inp[2]._input.ki.wVk = VK_RETURN
                inp[2]._input.ki.dwFlags = KEYEVENTF_KEYUP
                inp[3].type = INPUT_KEYBOARD
                inp[3]._input.ki.wVk = VK_SHIFT
                inp[3]._input.ki.dwFlags = KEYEVENTF_KEYUP
                user32.SendInput(4, ctypes.pointer(inp[0]), ctypes.sizeof(INPUT))
                time.sleep(0.01)
                continue
            code = ord(char)
            inp = (INPUT * 2)()
            inp[0].type = INPUT_KEYBOARD
            inp[0]._input.ki.wScan = code
            inp[0]._input.ki.dwFlags = KEYEVENTF_UNICODE
            inp[1].type = INPUT_KEYBOARD
            inp[1]._input.ki.wScan = code
            inp[1]._input.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
            user32.SendInput(2, ctypes.pointer(inp[0]), ctypes.sizeof(INPUT))
            time.sleep(0.005)

    def _select_all_delete():
        """Ctrl+A → Delete (입력 필드 초기화)"""
        inp = (INPUT * 4)()
        inp[0].type = INPUT_KEYBOARD; inp[0]._input.ki.wVk = VK_CONTROL
        inp[1].type = INPUT_KEYBOARD; inp[1]._input.ki.wVk = 0x41  # 'A'
        inp[2].type = INPUT_KEYBOARD; inp[2]._input.ki.wVk = 0x41; inp[2]._input.ki.dwFlags = KEYEVENTF_KEYUP
        inp[3].type = INPUT_KEYBOARD; inp[3]._input.ki.wVk = VK_CONTROL; inp[3]._input.ki.dwFlags = KEYEVENTF_KEYUP
        user32.SendInput(4, ctypes.pointer(inp[0]), ctypes.sizeof(INPUT))
        time.sleep(0.05)
        _press_key(VK_DELETE)
        time.sleep(0.1)


# ─── 윈도우 탐색 ───

def _get_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value

def _get_title(hwnd):
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value

def _find_children(parent, cls):
    results = []
    def cb(hwnd, lp):
        if _get_class(hwnd) == cls:
            results.append(hwnd)
        return True
    user32.EnumChildWindows(parent, WNDENUMPROC(cb), 0)
    return results

def find_kakao_main():
    """카카오톡 메인 윈도우 찾기"""
    results = []
    def cb(hwnd, lp):
        if _get_class(hwnd) == "EVA_Window_Dblclk" and _get_title(hwnd) == "카카오톡":
            results.append(hwnd)
        return True
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return results[0] if results else None

def find_chat_window(recipient):
    """채팅방 윈도우 찾기 (정확한 이름 매칭만 — 그룹 채팅 제외)"""
    results = []
    def cb(hwnd, lp):
        cls = _get_class(hwnd)
        title = _get_title(hwnd)
        if cls == "EVA_Window_Dblclk" and title and title != "카카오톡":
            results.append((hwnd, title))
        return True
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    if not results:
        return None
    # 1순위: 정확한 이름 매칭
    for hwnd, title in results:
        if title == recipient:
            return hwnd
    # 2순위: "이름 (N)" 형식 (동명이인 카운터)
    for hwnd, title in results:
        if re.match(rf'^{re.escape(recipient)}\s*\(\d+\)$', title):
            return hwnd
    # 그룹 채팅("이름1, 이름2") 등 부분 매칭은 반환하지 않음
    return None

def list_chat_windows():
    """열려 있는 모든 채팅방 목록"""
    results = []
    def cb(hwnd, lp):
        cls = _get_class(hwnd)
        title = _get_title(hwnd)
        if cls == "EVA_Window_Dblclk" and title and title != "카카오톡":
            results.append((hwnd, title))
        return True
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return results


# ─── 채팅방 열기 / 메시지 전송 ───

def _is_chat_tab_active(main_hwnd):
    """ChatRoomListView가 활성(visible) 상태인지 확인"""
    results = []
    def cb(hwnd, lp):
        title = _get_title(hwnd)
        if "ChatRoomListView" in title or "ChatRoomListCtrl" in title:
            results.append(user32.IsWindowVisible(hwnd))
        return True
    user32.EnumChildWindows(main_hwnd, WNDENUMPROC(cb), 0)
    return any(results)


def _switch_to_chat_tab(main_hwnd):
    """사이드바 채팅 탭 클릭으로 전환"""
    if _is_chat_tab_active(main_hwnd):
        return True

    rect = RECT()
    user32.GetWindowRect(main_hwnd, ctypes.byref(rect))
    sidebar_cx = rect.left + 33

    # 사이드바 상단(OnlineMainView)에서 아래로 탐색하며 채팅 탭 찾기
    sidebar_top = rect.top + 31
    for offset in range(55, 220, 15):
        _click_at(sidebar_cx, sidebar_top + offset)
        time.sleep(0.3)
        if _is_chat_tab_active(main_hwnd):
            print(f"채팅 탭 전환 완료 (offset={offset})", file=sys.stderr)
            return True

    print("WARNING: 채팅 탭 전환 실패", file=sys.stderr)
    return False


def open_chat_room(main_hwnd, recipient):
    """채팅 탭 전환 → WM_CHAR 검색 → SearchListCtrl 더블클릭으로 채팅방 열기"""
    user32.ShowWindow(main_hwnd, SW_RESTORE)
    user32.SetForegroundWindow(main_hwnd)
    time.sleep(0.5)

    # 채팅 탭으로 전환
    _switch_to_chat_tab(main_hwnd)
    time.sleep(0.3)

    edits = _find_children(main_hwnd, "Edit")
    if not edits:
        return None

    search_edit = edits[1] if len(edits) > 1 else edits[0]
    _click_center(search_edit)
    time.sleep(0.3)

    # WM_CHAR로 검색어 입력 (검색 트리거 필수)
    user32.SendMessageW(search_edit, WM_SETTEXT, 0, "")
    for ch in recipient:
        user32.SendMessageW(search_edit, WM_CHAR, ord(ch), 0)
        time.sleep(0.05)
    time.sleep(1.0)

    # SearchListCtrl에서 결과 순회 — 정확한 채팅방이 열릴 때까지
    all_children = []
    def cb(hwnd, lp):
        all_children.append(hwnd)
        return True
    user32.EnumChildWindows(main_hwnd, WNDENUMPROC(cb), 0)

    search_ctrl = None
    for hwnd in all_children:
        title = _get_title(hwnd)
        if "SearchListCtrl" in title and user32.IsWindowVisible(hwnd):
            search_ctrl = hwnd
            break

    if search_ctrl:
        rect = RECT()
        user32.GetWindowRect(search_ctrl, ctypes.byref(rect))
        cx = (rect.left + rect.right) // 2
        item_height = 60  # 검색 결과 항목 높이 (카카오톡 기본)

        for attempt in range(5):  # 최대 5개 결과 순회
            cy = rect.top + 35 + (attempt * item_height)
            if cy > rect.bottom - 10:
                break
            _dblclick_at(cx, cy)
            time.sleep(1.5)

            chat = find_chat_window(recipient)
            if chat:
                _clear_search_field(main_hwnd)
                return chat

            # 잘못된 채팅방이 열렸으면 닫기
            wrong = _find_wrong_chat(recipient)
            if wrong:
                print(f"잘못된 채팅방 닫기: {_get_title(wrong)}", file=sys.stderr)
                user32.PostMessageW(wrong, 0x0010, 0, 0)  # WM_CLOSE
                time.sleep(0.5)
                # 메인 윈도우 다시 활성화
                user32.SetForegroundWindow(main_hwnd)
                time.sleep(0.3)

    _clear_search_field(main_hwnd)
    return None


def _find_wrong_chat(recipient):
    """recipient과 정확히 일치하지 않는 열린 채팅방 찾기 (잘못 열린 그룹 채팅 등)"""
    results = []
    def cb(hwnd, lp):
        cls = _get_class(hwnd)
        title = _get_title(hwnd)
        if cls == "EVA_Window_Dblclk" and title and title != "카카오톡":
            if recipient in title and title != recipient:
                results.append(hwnd)
        return True
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return results[0] if results else None


def _clear_search_field(main_hwnd):
    """검색 필드 텍스트 초기화 — 채팅방 목록 필터 해제"""
    user32.SetForegroundWindow(main_hwnd)
    time.sleep(0.2)
    edits = _find_children(main_hwnd, "Edit")
    if not edits:
        return
    search_edit = edits[1] if len(edits) > 1 else edits[0]
    _click_center(search_edit)
    time.sleep(0.2)
    _select_all_delete()
    _press_key(VK_ESCAPE)
    time.sleep(0.3)


def send_text(edit_hwnd, text):
    """마우스 클릭 포커스 → SendInput 타이핑 → Enter 전송"""
    _click_center(edit_hwnd)
    time.sleep(0.3)
    _select_all_delete()
    _type_unicode(text)
    time.sleep(0.5)
    _press_key(VK_RETURN)
    time.sleep(0.8)


def split_message(text, max_length=4500):
    """긴 메시지를 줄바꿈 기준 분할"""
    if len(text) <= max_length:
        return [text]

    chunks = []
    lines = text.split('\n')
    current = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1
        if current_len + line_len > max_length and current:
            chunks.append('\n'.join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len

    if current:
        chunks.append('\n'.join(current))

    return chunks


# ─── Markdown → 플레인 텍스트 변환 ───

def convert_markdown_to_plain(md_text):
    """마크다운을 카카오톡용 읽기 좋은 플레인 텍스트로 변환"""
    lines = md_text.split('\n')
    result = []
    in_code_block = False
    in_table = False
    in_frontmatter = False
    table_rows = []

    for idx, line in enumerate(lines):
        if idx == 0 and line.strip() == '---':
            in_frontmatter = True
            continue
        if in_frontmatter:
            if line.strip() == '---':
                in_frontmatter = False
            continue

        if line.strip().startswith('```'):
            if in_code_block:
                in_code_block = False
                result.append('  ─ ─ ─')
            else:
                in_code_block = True
                lang = line.strip().lstrip('`').strip()
                result.append(f'  ─ {lang} ─' if lang else '  ─ ─ ─')
            continue

        if in_code_block:
            result.append(f'  {line}')
            continue

        if '|' in line and line.strip().startswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if all(set(c.strip()) <= {'-', ':', ' '} for c in cells):
                continue
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cells)
            continue
        elif in_table:
            result.extend(_format_table(table_rows))
            table_rows = []
            in_table = False

        if re.match(r'^-{3,}$', line.strip()):
            result.append('────────')
            continue

        if line.startswith('#### '):
            result.append(f'  {line[5:].strip()}'); continue
        if line.startswith('### '):
            result.append(f'▹ {line[4:].strip()}'); continue
        if line.startswith('## '):
            result.append(f'▸ {line[3:].strip()}'); continue
        if line.startswith('# '):
            result.append(f'◆ {line[2:].strip()}'); continue

        result.append(_convert_inline(line))

    if in_table and table_rows:
        result.extend(_format_table(table_rows))

    cleaned = []
    prev_empty = False
    for line in result:
        if line.strip() == '':
            if not prev_empty:
                cleaned.append('')
            prev_empty = True
        else:
            cleaned.append(line)
            prev_empty = False

    return '\n'.join(cleaned).strip()


def _convert_inline(line):
    line = re.sub(r'\*\*\*(.*?)\*\*\*', r'\1', line)
    line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
    line = re.sub(r'\*(.*?)\*', r'\1', line)
    line = re.sub(r'~~(.*?)~~', r'\1', line)
    line = re.sub(r'`(.*?)`', r'\1', line)
    line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', line)
    line = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'[\1]', line)
    line = re.sub(r'^(\s*)- \[x\]', r'\1[v]', line)
    line = re.sub(r'^(\s*)- \[ \]', r'\1[ ]', line)
    line = re.sub(r'^(\s*)[-*+] ', r'\g<1>. ', line)
    if re.match(r'^-{3,}$', line.strip()):
        line = '────────'
    if line.startswith('> '):
        line = '│ ' + line[2:]
    elif line.startswith('>'):
        line = '│ ' + line[1:]
    return line


def _format_table(rows):
    """카드형 테이블 변환 — 비례 폰트(카카오톡)에서도 가독성 유지"""
    if not rows:
        return []
    if len(rows) < 2:
        return ['  '.join(rows[0])] if rows else []

    headers = rows[0]
    result = []

    for data_row in rows[1:]:
        # 첫 번째 열을 카드 제목으로 사용
        title = data_row[0] if data_row else ''
        result.append(f'┌ {title}')
        # 나머지 열을 header: value 형식으로
        for i in range(1, len(headers)):
            val = data_row[i] if i < len(data_row) else ''
            if val:
                result.append(f'│ {headers[i]}: {val}')
        result.append('└')
    return result


# ─── 메인 ───

def main():
    parser = argparse.ArgumentParser(description='카카오톡 메시지 자동 전송')
    parser.add_argument('--recipient', '-r', default=None, help='수신자 채팅방 이름')
    parser.add_argument('--message', '-m', default=None, help='메시지 텍스트')
    parser.add_argument('--message-file', '-f', default=None, help='메시지 파일 경로')
    parser.add_argument('--convert-md', action='store_true', help='마크다운 → 플레인 텍스트 변환')
    parser.add_argument('--max-length', type=int, default=4500, help='분할 기준 길이')
    parser.add_argument('--dry-run', action='store_true', help='변환 결과만 출력')
    parser.add_argument('--restore-focus', action='store_true', default=True, help='포커스 복원')
    parser.add_argument('--list', action='store_true', help='열린 채팅방 목록')

    args = parser.parse_args()

    if not IS_WINDOWS:
        print("ERROR: Windows 전용. WSL에서는 powershell.exe로 호출하세요.", file=sys.stderr)
        sys.exit(99)

    if args.list:
        windows = list_chat_windows()
        if not windows:
            print("열려 있는 채팅방 없음")
        else:
            for hwnd, title in windows:
                print(f"  {hwnd} | {title}")
        sys.exit(0)

    if not args.recipient:
        parser.error('--recipient/-r 필수')

    # 메시지 소스
    if args.message:
        text = args.message
    elif args.message_file:
        fp = args.message_file
        if fp.startswith('/mnt/'):
            fp = f'{fp[5].upper()}:\\{fp[7:].replace("/", chr(92))}'
        elif fp.startswith('/home/'):
            fp = f'\\\\wsl.localhost\\Ubuntu{fp}'.replace('/', '\\')
        with open(fp, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("ERROR: 빈 메시지", file=sys.stderr)
        sys.exit(1)

    if args.convert_md:
        text = convert_markdown_to_plain(text)

    if args.dry_run:
        print(text)
        print(f"\n({len(text)}자)", file=sys.stderr)
        sys.exit(0)

    chunks = split_message(text, args.max_length)

    # 포커스 저장
    prev = user32.GetForegroundWindow() if args.restore_focus else None

    # 채팅방 찾기/열기
    chat_hwnd = find_chat_window(args.recipient)
    if chat_hwnd:
        print(f"채팅방 발견: {args.recipient}", file=sys.stderr)
    else:
        main_hwnd = find_kakao_main()
        if not main_hwnd:
            print("ERROR: 카카오톡 미실행", file=sys.stderr)
            sys.exit(2)
        print(f"채팅방 검색: '{args.recipient}'...", file=sys.stderr)
        chat_hwnd = open_chat_room(main_hwnd, args.recipient)
        if not chat_hwnd:
            print(f"ERROR: '{args.recipient}' 못 찾음", file=sys.stderr)
            sys.exit(3)
        print(f"채팅방 열림: {args.recipient}", file=sys.stderr)

    # 입력 필드 찾기
    edits = _find_children(chat_hwnd, "RICHEDIT50W")
    if not edits:
        print("ERROR: 입력 필드 없음", file=sys.stderr)
        sys.exit(4)
    edit_hwnd = edits[0]

    # 채팅방 활성화
    user32.ShowWindow(chat_hwnd, SW_RESTORE)
    user32.SetForegroundWindow(chat_hwnd)
    time.sleep(0.5)

    # 전송
    for i, chunk in enumerate(chunks):
        if i > 0:
            time.sleep(0.5)
        send_text(edit_hwnd, chunk)
        print(f"전송 ({i+1}/{len(chunks)}): {len(chunk)}자", file=sys.stderr)

    # 포커스 복원
    if prev and args.restore_focus:
        time.sleep(0.3)
        user32.SetForegroundWindow(prev)

    print(f"OK: {args.recipient}에게 {len(chunks)}건 전송", file=sys.stderr)
    print("OK")


if __name__ == '__main__':
    main()
