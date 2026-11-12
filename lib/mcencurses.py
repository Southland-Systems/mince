from __future__ import annotations

import curses
import locale
import sys
import unicodedata
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


__all__ = (
    'ASCII_GLYPHS', 'UTF8_GLYPHS', 'Canvas', 'Column', 'Field',
    'Form', 'FormScreen', 'FormValue', 'Menu', 'MouseEvent', 'Rect',
    'Table', 'Terminal', 'TextView', 'animation_frame', 'fit_text',
    'init_themes', 'is_enter', 'is_key', 'item_attribute',
    'mouse_events', 'read_mouse', 'sparkline', 'text_width',
    'utf8_available', 'wrap_text',
)

UTF8_GLYPHS: Mapping[str, str] = MappingProxyType({
    'horizontal': '─',
    'vertical': '│',
    'top_left': '┌',
    'top_right': '┐',
    'bottom_left': '└',
    'bottom_right': '┘',
    'double_horizontal': '═',
    'double_vertical': '║',
    'double_top_left': '╔',
    'double_top_right': '╗',
    'double_bottom_left': '╚',
    'double_bottom_right': '╝',
    'cross': '┼',
    'tee_left': '├',
    'tee_right': '┤',
    'marker': '›',
    'bullet': '•',
    'check': '✓',
    'warning': '▲',
    'bar_full': '█',
    'bar_empty': '░',
    'left_arrow': '←',
    'right_arrow': '→',
    'up_arrow': '↑',
    'down_arrow': '↓',
    'sparkline': '▁▂▃▄▅▆▇█',
    'circle_filled': '●',
    'circle_empty': '○',
    'diamond': '◆',
    'spinner': '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏',
    'progress_head': '◆◇●○',
    'newline': '↵',
})

ASCII_GLYPHS: Mapping[str, str] = MappingProxyType({
    'horizontal': '-',
    'vertical': '|',
    'top_left': '+',
    'top_right': '+',
    'bottom_left': '+',
    'bottom_right': '+',
    'double_horizontal': '=',
    'double_vertical': '|',
    'double_top_left': '+',
    'double_top_right': '+',
    'double_bottom_left': '+',
    'double_bottom_right': '+',
    'cross': '+',
    'tee_left': '+',
    'tee_right': '+',
    'marker': '>',
    'bullet': '*',
    'check': '+',
    'warning': '!',
    'bar_full': '#',
    'bar_empty': '.',
    'left_arrow': '<',
    'right_arrow': '>',
    'up_arrow': '^',
    'down_arrow': 'v',
    'sparkline': '._:-=+*#',
    'circle_filled': '*',
    'circle_empty': 'o',
    'diamond': '*',
    'spinner': '|/-.',
    'progress_head': '*+o@',
    'newline': '\\n',
})

FormValue = Any


@dataclass(frozen=True)
class Rect:
    top: int
    left: int
    height: int
    width: int

    def __post_init__(self) -> None:
        if self.height < 0 or self.width < 0:
            raise ValueError('Rectangle dimensions must not be negative')

    def row_at(self, position: tuple[int, int] | None) -> int | None:
        if position is None:
            return None
        row, column = position
        if (
            self.top <= row < self.top + self.height
            and self.left <= column < self.left + self.width
        ):
            return row - self.top
        return None

    def inset(self, amount: int = 1) -> Rect:
        if amount < 0:
            raise ValueError('Inset must not be negative')
        return Rect(
            self.top + amount,
            self.left + amount,
            max(0, self.height - amount * 2),
            max(0, self.width - amount * 2),
        )


@dataclass(frozen=True)
class MouseEvent:
    row: int
    column: int
    state: int

    @property
    def position(self) -> tuple[int, int]:
        return self.row, self.column

    @property
    def clicked(self) -> bool:
        mask = (
            getattr(curses, 'BUTTON1_CLICKED', 0)
            | getattr(curses, 'BUTTON1_PRESSED', 0)
        )
        return bool(self.state & mask)

    @property
    def scroll(self) -> int:
        up = (
            getattr(curses, 'BUTTON4_PRESSED', 0)
            | getattr(curses, 'BUTTON4_CLICKED', 0)
        )
        down = (
            getattr(curses, 'BUTTON5_PRESSED', 0)
            | getattr(curses, 'BUTTON5_CLICKED', 0)
        )
        if self.state & up:
            return -1
        if self.state & down:
            return 1
        return 0


def read_mouse() -> MouseEvent | None:
    try:
        _, column, row, _, state = curses.getmouse()
    except (AttributeError, curses.error):
        return None
    return MouseEvent(row, column, state)


@contextmanager
def mouse_events(mask: int | None = None) -> Iterator[int]:
    if mask is None:
        mask = (
            getattr(curses, 'ALL_MOUSE_EVENTS', 0)
            | getattr(curses, 'REPORT_MOUSE_POSITION', 0)
        )
    try:
        available, previous = curses.mousemask(mask)
    except (AttributeError, curses.error):
        yield 0
        return
    try:
        yield available
    finally:
        try:
            curses.mousemask(previous)
        except (AttributeError, curses.error):
            pass


def utf8_available(encoding: str | None = None) -> bool:
    encoding = encoding or locale.getpreferredencoding(False) or ''
    return encoding.lower().replace('-', '').replace('_', '') == 'utf8'


def _character_width(character: str) -> int:
    category = unicodedata.category(character)
    if unicodedata.combining(character) or category in ('Cc', 'Cf', 'Mn', 'Me'):
        return 0
    return 2 if unicodedata.east_asian_width(character) in ('F', 'W') else 1


def text_width(text: str) -> int:
    return sum(_character_width(character) for character in text)


def fit_text(text: str, width: int) -> str:
    if width <= 0:
        return ''
    result = []
    used = 0
    for character in text:
        if unicodedata.category(character) == 'Cc':
            continue
        cells = _character_width(character)
        if used + cells > width:
            break
        result.append(character)
        used += cells
    return ''.join(result)


def wrap_text(text: str, width: int) -> list[str]:
    if width <= 0:
        return []
    lines = []
    for paragraph in text.expandtabs(4).split('\n'):
        line = []
        used = 0
        for character in paragraph:
            if unicodedata.category(character) == 'Cc':
                continue
            cells = _character_width(character)
            if line and used + cells > width:
                lines.append(''.join(line).rstrip())
                line = []
                used = 0
            if not line and character.isspace():
                continue
            line.append(character)
            used += cells
        lines.append(''.join(line).rstrip())
    return lines


def is_key(key: int | str, *characters: str) -> bool:
    return any(
        key == character or (len(character) == 1 and key == ord(character))
        for character in characters
    )


def is_enter(key: int | str) -> bool:
    return key == getattr(curses, 'KEY_ENTER', None) or is_key(key, '\n', '\r')


def item_attribute(
    style: int,
    selected: bool,
    hovered: bool,
    default: int = curses.A_NORMAL,
) -> int:
    attribute = style | curses.A_BOLD if selected or hovered else default
    if selected:
        attribute |= curses.A_REVERSE
    if hovered:
        attribute |= curses.A_UNDERLINE
    return attribute


def animation_frame(
    sequence: str,
    elapsed: float,
    frames_per_second: float = 8.0,
) -> str:
    if frames_per_second <= 0:
        raise ValueError('Frame rate must be positive')
    if not sequence:
        return ''
    return sequence[int(elapsed * frames_per_second) % len(sequence)]


def sparkline(
    values: Iterable[float],
    symbols: str = UTF8_GLYPHS['sparkline'],
) -> str:
    data = tuple(values)
    if not data or not symbols:
        return ''
    minimum = min(data)
    span = max(data) - minimum
    if span == 0:
        return symbols[0] * len(data)
    scale = len(symbols) - 1
    return ''.join(
        symbols[min(scale, max(0, int((value - minimum) * scale / span)))]
        for value in data
    )


def init_themes(
    palette: Iterable[tuple[str, int | Sequence[int]]],
    *,
    background: int | None = None,
    first_pair: int = 1,
) -> tuple[tuple[str, int], ...]:
    if first_pair < 1:
        raise ValueError('The first color pair must be positive')
    try:
        if not curses.has_colors():
            return ()
        curses.start_color()
        if background is None:
            try:
                curses.use_default_colors()
                background = -1
            except (AttributeError, curses.error):
                background = curses.COLOR_BLACK
        themes = []
        for pair, (name, foreground) in enumerate(palette, first_pair):
            if pair >= curses.COLOR_PAIRS:
                break
            colors = (foreground,) if isinstance(foreground, int) else foreground
            for color in colors:
                if not 0 <= color < curses.COLORS:
                    continue
                try:
                    curses.init_pair(pair, color, background)
                    attribute = curses.color_pair(pair)
                except curses.error:
                    continue
                themes.append((name, attribute))
                break
        return tuple(themes)
    except curses.error:
        return ()


def _pad(text: str, width: int, right_align: bool = False) -> str:
    fitted = fit_text(text, width)
    padding = ' ' * max(0, width - text_width(fitted))
    return padding + fitted if right_align else fitted + padding


def _viewport(
    selected: int,
    scroll: int,
    count: int,
    height: int,
) -> tuple[int, int]:
    if count <= 0:
        return 0, 0
    selected = min(max(0, selected), count - 1)
    visible = max(1, height)
    scroll = min(max(0, scroll), max(0, count - visible))
    scroll = min(scroll, selected)
    if selected >= scroll + visible:
        scroll = selected - visible + 1
    return selected, scroll


def _selection_key(
    key: int | str,
    selected: int,
    count: int,
    page_size: int,
) -> int | None:
    last = max(0, count - 1)
    selected = min(max(0, selected), last)
    if key == curses.KEY_UP or is_key(key, 'k', 'K'):
        return (selected - 1) % count if count else 0
    if key == curses.KEY_DOWN or is_key(key, 'j', 'J'):
        return (selected + 1) % count if count else 0
    if key == getattr(curses, 'KEY_HOME', None):
        return 0
    if key == getattr(curses, 'KEY_END', None):
        return last
    if key == getattr(curses, 'KEY_PPAGE', None):
        return max(0, selected - max(1, page_size))
    if key == getattr(curses, 'KEY_NPAGE', None):
        return min(last, selected + max(1, page_size))
    return None


def _input_text(
    value: Sequence[str],
    width: int,
    cursor: int | None,
) -> tuple[str, int]:
    if width <= 0:
        return '', 0
    start = 0
    column = 0
    if cursor is not None:
        start = min(max(0, cursor), len(value))
        while start:
            cells = text_width(value[start - 1])
            if column + cells >= width:
                break
            start -= 1
            column += cells
    return _pad(''.join(value[start:]), width), column


def _number_input(value: str) -> bool:
    digits = value[1:] if value.startswith(('+', '-')) else value
    return not digits or (digits.isascii() and digits.isdecimal())


class Canvas:
    def __init__(
        self,
        window: curses.window,
        *,
        glyphs: Mapping[str, str] | None = None,
        attribute: int = curses.A_NORMAL,
    ) -> None:
        self.window = window
        self.attribute = attribute
        self.encoding = (
            getattr(window, 'encoding', None)
            or locale.getpreferredencoding(False)
            or 'ascii'
        )
        self.utf8_supported = utf8_available(self.encoding)
        self.utf8_enabled = self.utf8_supported
        self._glyph_overrides = dict(glyphs or {})
        self.glyphs = dict(UTF8_GLYPHS if self.utf8_enabled else ASCII_GLYPHS)
        self.glyphs.update(self._glyph_overrides)

    def set_utf8(self, enabled: bool) -> bool:
        if enabled and not self.utf8_supported:
            return False
        self.utf8_enabled = enabled
        self.glyphs.clear()
        self.glyphs.update(UTF8_GLYPHS if enabled else ASCII_GLYPHS)
        self.glyphs.update(self._glyph_overrides)
        return True

    def display_text(self, text: str) -> str:
        result = ''.join(
            self.glyphs['newline'] if character == '\n'
            else '\\t' if character == '\t'
            else '\\r' if character == '\r'
            else character if character.isprintable()
            else '?'
            for character in text
        )
        if not self.utf8_supported:
            result = result.encode(
                self.encoding, errors='replace',
            ).decode(self.encoding)
        return result

    def text_view(
        self,
        value: str,
        width: int,
        cursor: int | None = None,
        secret: bool = False,
    ) -> tuple[str, int]:
        characters = [
            self.glyphs['bullet'] if secret else self.display_text(character)
            for character in value
        ]
        return _input_text(characters, width, cursor)

    def write(
        self,
        row: int,
        column: int,
        text: str,
        attribute: int | None = None,
        width: int | None = None,
    ) -> None:
        height, columns = self.window.getmaxyx()
        if row < 0 or row >= height or column < 0 or column >= columns:
            return
        available = columns - column
        if width is not None:
            available = min(available, width)
        clipped = fit_text(self.display_text(text), available)
        if not clipped:
            return
        if attribute is None:
            attribute = self.attribute
        try:
            self.window.addstr(row, column, clipped, attribute)
        except (curses.error, UnicodeError):
            pass

    def centered(
        self,
        row: int,
        text: str,
        attribute: int | None = None,
        *,
        left: int = 0,
        width: int | None = None,
    ) -> None:
        if width is None:
            width = max(0, self.window.getmaxyx()[1] - left)
        text = fit_text(self.display_text(text), width)
        column = left + max(0, (width - text_width(text)) // 2)
        self.write(row, column, text, attribute, width)

    def clear(self, rect: Rect, attribute: int | None = None) -> None:
        height, width = self.window.getmaxyx()
        left = max(0, rect.left)
        right = min(width, rect.left + rect.width)
        if right <= left:
            return
        blank = ' ' * (right - left)
        for row in range(max(0, rect.top), min(height, rect.top + rect.height)):
            self.write(row, left, blank, attribute)

    def shade(self, rect: Rect, attribute: int = curses.A_DIM) -> None:
        height, width = self.window.getmaxyx()
        left = max(0, rect.left)
        right = min(width, rect.left + rect.width)
        if right <= left:
            return
        for row in range(max(0, rect.top), min(height, rect.top + rect.height)):
            try:
                self.window.chgat(row, left, right - left, attribute)
            except curses.error:
                pass

    def rule(
        self,
        row: int,
        column: int,
        width: int,
        *,
        character: str | None = None,
        elapsed: float | None = None,
        attribute: int | None = None,
    ) -> None:
        if width <= 0:
            return
        if character is None:
            character = self.glyphs['horizontal']
        if attribute is None:
            attribute = self.attribute
        if elapsed is None:
            self.write(row, column, character * width, attribute)
            return
        self.write(row, column, character * width, curses.A_DIM)
        glow_width = min(8, max(1, width // 6))
        travel = width - glow_width
        phase = int(elapsed * 14) % max(1, travel * 2)
        offset = travel - abs(travel - phase)
        self.write(
            row, column + offset, character * glow_width,
            attribute | curses.A_BOLD,
        )

    def box(
        self,
        rect: Rect,
        title: str = '',
        *,
        attribute: int | None = None,
        shadow: bool = False,
    ) -> None:
        if rect.height < 2 or rect.width < 2:
            return
        if attribute is None:
            attribute = self.attribute
        glyphs = self.glyphs
        right = rect.left + rect.width - 1
        bottom = rect.top + rect.height - 1
        if shadow:
            self.write(
                bottom + 1, rect.left + 2,
                glyphs['bar_empty'] * rect.width, curses.A_DIM,
            )
            for row in range(rect.top + 1, bottom + 1):
                self.write(row, right + 1, glyphs['bar_empty'] * 2, curses.A_DIM)
        self.clear(rect.inset())
        self.write(
            rect.top, rect.left,
            glyphs['top_left']
            + glyphs['horizontal'] * (rect.width - 2)
            + glyphs['top_right'],
            attribute | curses.A_BOLD,
        )
        for row in range(rect.top + 1, bottom):
            self.write(row, rect.left, glyphs['vertical'], attribute)
            self.write(row, right, glyphs['vertical'], attribute)
        self.write(
            bottom, rect.left,
            glyphs['bottom_left']
            + glyphs['horizontal'] * (rect.width - 2)
            + glyphs['bottom_right'],
            attribute | curses.A_BOLD,
        )
        if title and rect.width > 4:
            self.write(
                rect.top, rect.left + 2,
                fit_text(' ' + title + ' ', rect.width - 4),
                attribute | curses.A_BOLD,
            )

    def meter(
        self,
        row: int,
        column: int,
        bar_width: int,
        percent: float,
        *,
        attribute: int | None = None,
        elapsed: float | None = None,
        show_value: bool = True,
    ) -> None:
        if bar_width <= 0:
            return
        if attribute is None:
            attribute = self.attribute
        percent = min(100.0, max(0.0, percent))
        filled = int(bar_width * percent / 100)
        full = self.glyphs['bar_full']
        empty = self.glyphs['bar_empty']
        bar = full * filled + empty * (bar_width - filled)
        self.write(row, column, '[' + bar + ']', curses.A_DIM)
        if filled:
            self.write(row, column + 1, full * filled, attribute | curses.A_BOLD)
        if elapsed is not None and percent < 100:
            head = animation_frame(self.glyphs['progress_head'], elapsed, 12.0)
            self.write(
                row, column + 1 + min(bar_width - 1, filled), head,
                attribute | curses.A_BOLD | curses.A_REVERSE,
            )
        if show_value:
            self.write(row, column + bar_width + 3, f'{percent:3.0f}%')

    def scrollbar(self, rect: Rect, total: int, offset: int) -> None:
        if rect.height <= 0 or rect.width <= 0 or total <= rect.height:
            return
        maximum = total - rect.height
        offset = min(max(0, offset), maximum)
        thumb_height = max(1, rect.height * rect.height // total)
        thumb_start = (rect.height - thumb_height) * offset // maximum
        for row in range(rect.height):
            in_thumb = thumb_start <= row < thumb_start + thumb_height
            character = self.glyphs['bar_full' if in_thumb else 'vertical']
            attribute = self.attribute if in_thumb else curses.A_DIM
            self.write(rect.top + row, rect.left, character, attribute)

    def refresh(self, cursor: tuple[int, int] | None = None) -> None:
        try:
            curses.curs_set(1 if cursor is not None else 0)
        except curses.error:
            pass
        try:
            if cursor is not None:
                self.window.move(*cursor)
            self.window.refresh()
        except curses.error:
            pass


class Terminal(Canvas):
    @classmethod
    def run(cls, screen: Callable[[Terminal], Any], **options: Any) -> Any:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise ValueError('interactive terminal input and output are required')
        try:
            locale.setlocale(locale.LC_CTYPE, '')
        except locale.Error:
            pass

        def invoke(window: curses.window) -> Any:
            terminal = cls(window, **options)
            with mouse_events(getattr(curses, 'ALL_MOUSE_EVENTS', 0)) as available:
                terminal.mouse_enabled = bool(available)
                return screen(terminal)

        try:
            return curses.wrapper(invoke)
        except curses.error as exc:
            raise ValueError(f'terminal interface failed: {exc}') from exc

    def __init__(
        self,
        window: curses.window,
        *,
        palette: Iterable[tuple[str, int | Sequence[int]]] = (),
        glyphs: Mapping[str, str] | None = None,
        timeout: int = 250,
    ) -> None:
        themes = init_themes(palette)
        super().__init__(
            window, glyphs=glyphs,
            attribute=themes[0][1] if themes else curses.A_BOLD,
        )
        self.input_timeout = timeout
        self.mouse_enabled = False
        window.keypad(True)
        window.timeout(timeout)
        try:
            curses.set_escdelay(25)
        except (AttributeError, curses.error):
            pass

    def read_key(self) -> int | str | None:
        try:
            return self.window.get_wch()
        except curses.error:
            return None

    def suspend(self, operation: Callable[[], Any]) -> Any:
        curses.def_prog_mode()
        curses.endwin()
        try:
            return operation()
        finally:
            curses.reset_prog_mode()
            self.window.keypad(True)
            self.window.timeout(self.input_timeout)
            self.window.clear()

    def dialog(
        self,
        title: str,
        lines: Sequence[str],
        buttons: Sequence[str] = ('Close',),
        default: int = 0,
    ) -> str | None:
        if not buttons:
            raise ValueError('Dialogs require at least one button')
        selection = default % len(buttons)
        content = TextView(
            tuple(
                self.display_text(line)
                for paragraph in lines
                for line in paragraph.splitlines() or ['']
            ) or ('',),
            show_scrollbar=False,
        )
        button_width = sum(text_width(button) + 4 for button in buttons)
        button_width += 2 * (len(buttons) - 1)
        while True:
            height, width = self.window.getmaxyx()
            ready = height >= 8 and width >= max(30, button_width + 8)
            self.window.erase()
            positions = []
            if ready:
                inner_width = max(button_width, min(76, width - 8))
                available = Rect(0, 0, height - 6, inner_width)
                visible_rows = max(1, min(len(content._lines(available)), available.height))
                frame = Rect(
                    (height - visible_rows - 4) // 2,
                    (width - inner_width - 4) // 2,
                    visible_rows + 4, inner_width + 4,
                )
                self.box(frame, title)
                body = Rect(frame.top + 1, frame.left + 2, visible_rows, inner_width)
                content.draw(self, body)
                column = frame.left + 2
                for index, button in enumerate(buttons):
                    text = '[ ' + button + ' ]'
                    position = Rect(frame.top + visible_rows + 2, column, 1, text_width(text))
                    positions.append(position)
                    attribute = item_attribute(self.attribute, index == selection, False)
                    self.write(position.top, position.left, text, attribute)
                    column += position.width + 2
                self.write(
                    height - 1, 2,
                    'Up/Down: scroll  Tab: choose  Enter: accept  Esc: back',
                    curses.A_DIM, width - 4,
                )
            else:
                self.centered(height // 2, 'Resize the terminal to continue', curses.A_BOLD)
            self.refresh()
            key = self.read_key()
            if key is None or key == getattr(curses, 'KEY_RESIZE', None):
                continue
            if is_key(key, '\x1b', 'q', 'Q'):
                return None
            if key == getattr(curses, 'KEY_MOUSE', None):
                event = read_mouse()
                if not ready or event is None:
                    continue
                if event.scroll:
                    content.scroll_by(event.scroll * 3, body)
                elif event.clicked:
                    for index, position in enumerate(positions):
                        if position.row_at(event.position) is not None:
                            return buttons[index]
                continue
            if not ready:
                continue
            if is_enter(key):
                return buttons[selection]
            if key in (curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_BTAB) or is_key(key, '\t'):
                step = -1 if key in (curses.KEY_LEFT, curses.KEY_BTAB) else 1
                selection = (selection + step) % len(buttons)
            else:
                content.handle_key(key, body)


@dataclass
class Menu:
    items: Sequence[str]
    selected: int = 0
    scroll: int = 0

    @property
    def selected_item(self) -> str | None:
        if not self.items:
            return None
        return self.items[min(max(0, self.selected), len(self.items) - 1)]

    def handle_key(self, key: int | str, page_size: int = 1) -> bool:
        selected = _selection_key(key, self.selected, len(self.items), page_size)
        if selected is None:
            return False
        self.selected = selected
        return True

    def click(self, rect: Rect, position: tuple[int, int]) -> int | None:
        self.selected, self.scroll = _viewport(
            self.selected, self.scroll, len(self.items), rect.height,
        )
        row = rect.row_at(position)
        if row is None or self.scroll + row >= len(self.items):
            return None
        self.selected = self.scroll + row
        return self.selected

    def draw(
        self,
        canvas: Canvas,
        rect: Rect,
        mouse_position: tuple[int, int] | None = None,
    ) -> None:
        canvas.clear(rect)
        self.selected, self.scroll = _viewport(
            self.selected, self.scroll, len(self.items), rect.height,
        )
        hovered = rect.row_at(mouse_position)
        for row, label in enumerate(self.items[self.scroll:self.scroll + rect.height]):
            index = self.scroll + row
            prefix = canvas.glyphs['marker'] + ' ' if index == self.selected else '  '
            attribute = item_attribute(
                canvas.attribute, index == self.selected, row == hovered,
                canvas.attribute,
            )
            canvas.write(rect.top + row, rect.left, _pad(prefix + label, rect.width), attribute)


@dataclass
class TextView:
    text: str | Sequence[str] = ''
    scroll: int = 0
    show_scrollbar: bool = True

    def _lines(self, rect: Rect) -> list[str]:
        width = rect.width - int(self.show_scrollbar and rect.width > 1)
        source = self.text.split('\n') if isinstance(self.text, str) else self.text
        return [wrapped for line in source for wrapped in wrap_text(line, width)]

    def scroll_by(self, amount: int, rect: Rect) -> None:
        maximum = max(0, len(self._lines(rect)) - rect.height)
        self.scroll = min(maximum, max(0, self.scroll + amount))

    def handle_key(self, key: int | str, rect: Rect) -> bool:
        maximum = max(0, len(self._lines(rect)) - rect.height)
        if key == curses.KEY_UP or is_key(key, 'k', 'K'):
            self.scroll -= 1
        elif key == curses.KEY_DOWN or is_key(key, 'j', 'J'):
            self.scroll += 1
        elif key == getattr(curses, 'KEY_PPAGE', None) or is_key(key, 'b', 'B'):
            self.scroll -= max(1, rect.height)
        elif key == getattr(curses, 'KEY_NPAGE', None) or is_key(key, ' ', 'f', 'F'):
            self.scroll += max(1, rect.height)
        elif key == getattr(curses, 'KEY_HOME', None):
            self.scroll = 0
        elif key == getattr(curses, 'KEY_END', None):
            self.scroll = maximum
        else:
            return False
        self.scroll = min(maximum, max(0, self.scroll))
        return True

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        canvas.clear(rect)
        lines = self._lines(rect)
        self.scroll = min(max(0, self.scroll), max(0, len(lines) - rect.height))
        width = rect.width - int(self.show_scrollbar and rect.width > 1)
        for row, line in enumerate(lines[self.scroll:self.scroll + rect.height]):
            canvas.write(rect.top + row, rect.left, fit_text(line, width))
        if self.show_scrollbar and rect.width > 1:
            canvas.scrollbar(
                Rect(rect.top, rect.left + rect.width - 1, rect.height, 1),
                len(lines), self.scroll,
            )


@dataclass(frozen=True)
class Column:
    label: str
    value: Callable[[Any], Any]
    width: int | None = None
    right_align: bool = False
    format_value: Callable[[Any], str] = str

    def __post_init__(self) -> None:
        if self.width is not None and self.width < 0:
            raise ValueError('Column width must not be negative')


class Table:
    def __init__(
        self,
        columns: Iterable[Column],
        rows: Iterable[Any] = (),
        *,
        header: bool = True,
    ) -> None:
        self.columns = tuple(columns)
        self.rows = tuple(rows)
        self.header = header
        self.selected = 0
        self.scroll = 0
        self.sort_index: int | None = None
        self.reverse = False
        self.row_filter: Callable[[Any], bool] | None = None

    def visible_rows(self) -> tuple[Any, ...]:
        rows = [
            row for row in self.rows
            if self.row_filter is None or self.row_filter(row)
        ]
        if self.sort_index is not None:
            rows.sort(key=self.columns[self.sort_index].value, reverse=self.reverse)
        return tuple(rows)

    @property
    def selected_row(self) -> Any | None:
        rows = self.visible_rows()
        if not rows:
            return None
        return rows[min(max(0, self.selected), len(rows) - 1)]

    def sort(self, index: int | None, reverse: bool = False) -> None:
        if index is not None and not 0 <= index < len(self.columns):
            raise ValueError('Sort column is out of range')
        self.sort_index = index
        self.reverse = reverse
        self.selected = 0
        self.scroll = 0

    def handle_key(self, key: int | str, page_size: int = 1) -> bool:
        selected = _selection_key(
            key, self.selected, len(self.visible_rows()), page_size,
        )
        if selected is None:
            return False
        self.selected = selected
        return True

    def _body(self, rect: Rect) -> Rect:
        header_height = min(2, rect.height) if self.header else 0
        return Rect(
            rect.top + header_height, rect.left,
            rect.height - header_height, rect.width,
        )

    def _widths(self, width: int) -> tuple[int, ...]:
        fixed = sum(column.width for column in self.columns if column.width is not None)
        flexible = sum(column.width is None for column in self.columns)
        remaining = max(0, width - max(0, len(self.columns) - 1) - fixed)
        base, extra = divmod(remaining, flexible) if flexible else (0, 0)
        widths = []
        for column in self.columns:
            if column.width is None:
                widths.append(base + int(extra > 0))
                extra = max(0, extra - 1)
            else:
                widths.append(column.width)
        return tuple(widths)

    def click(self, rect: Rect, position: tuple[int, int]) -> int | None:
        rows = self.visible_rows()
        body = self._body(rect)
        self.selected, self.scroll = _viewport(
            self.selected, self.scroll, len(rows), body.height,
        )
        row = body.row_at(position)
        if row is None or self.scroll + row >= len(rows):
            return None
        self.selected = self.scroll + row
        return self.selected

    def draw(
        self,
        canvas: Canvas,
        rect: Rect,
        mouse_position: tuple[int, int] | None = None,
    ) -> None:
        canvas.clear(rect)
        widths = self._widths(rect.width)
        if self.header and rect.height:
            heading = ' '.join(
                _pad(column.label, width, column.right_align)
                for column, width in zip(self.columns, widths)
            )
            canvas.write(
                rect.top, rect.left, fit_text(heading, rect.width),
                canvas.attribute | curses.A_BOLD,
            )
            if rect.height > 1:
                canvas.rule(rect.top + 1, rect.left, rect.width)
        body = self._body(rect)
        rows = self.visible_rows()
        self.selected, self.scroll = _viewport(
            self.selected, self.scroll, len(rows), body.height,
        )
        hovered = body.row_at(mouse_position)
        for offset, row in enumerate(rows[self.scroll:self.scroll + body.height]):
            text = ' '.join(
                _pad(str(column.format_value(column.value(row))), width, column.right_align)
                for column, width in zip(self.columns, widths)
            )
            attribute = item_attribute(
                canvas.attribute, self.scroll + offset == self.selected,
                offset == hovered, canvas.attribute,
            )
            canvas.write(body.top + offset, body.left, _pad(text, body.width), attribute)


@dataclass(frozen=True)
class Field:
    name: str
    label: str
    kind: str = 'text'
    default: FormValue = ''
    choices: tuple[str, ...] = ()
    max_length: int | None = None
    validator: Callable[[FormValue], str | None] | None = None
    description: str = ''
    secret: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError('Field names must not be empty')
        if self.kind not in ('text', 'number', 'bool', 'enum'):
            raise ValueError('Unsupported field kind: ' + self.kind)
        if self.max_length is not None and self.max_length < 0:
            raise ValueError('Maximum length must not be negative')
        object.__setattr__(self, 'choices', tuple(self.choices))
        if self.kind == 'enum' and (
            not self.choices or len(set(self.choices)) != len(self.choices)
        ):
            raise ValueError('Enumeration choices must be nonempty and unique')
        self.normalize(self.default)

    def normalize(self, value: FormValue) -> FormValue:
        if self.kind == 'bool':
            if not isinstance(value, bool):
                raise ValueError(f'{self.label} must be a boolean')
            return value
        text = str(value)
        if self.max_length is not None and len(text) > self.max_length:
            raise ValueError(f'{self.label} exceeds its maximum length')
        if self.kind == 'number':
            text = text.strip()
            if isinstance(value, bool) or text in ('', '+', '-') or not _number_input(text):
                raise ValueError(f'{self.label} must be an integer')
            return int(text)
        if self.kind == 'enum' and text not in self.choices:
            raise ValueError(f'{self.label} must be one of the configured choices')
        return text


class Form:
    def __init__(
        self,
        fields: Iterable[Field],
        *,
        values: Mapping[str, FormValue] | None = None,
        defaults: Mapping[str, FormValue] | None = None,
        validator: Callable[[Mapping[str, FormValue]], str | None] | None = None,
    ) -> None:
        self.fields = tuple(fields)
        if len({field.name for field in self.fields}) != len(self.fields):
            raise ValueError('Field names must be unique')
        self.validator = validator
        self.defaults = {
            field.name: field.normalize(field.default)
            for field in self.fields
        }
        if defaults is not None:
            self.defaults.update(defaults)
        self.values = self.defaults.copy()
        if values is not None:
            self.values.update(values)
        self._applied = self.values.copy()
        self.focus = 0
        self.scroll = 0
        self.editing = False
        self.cursor = 0
        self.buffer = ''

    @property
    def applied(self) -> dict[str, FormValue]:
        return self._applied.copy()

    @property
    def modified(self) -> bool:
        if self.values != self._applied:
            return True
        if not self.editing:
            return False
        field = self.fields[self.focus]
        return self.buffer != self.format_value(field, self.values[field.name])

    @property
    def control_count(self) -> int:
        return len(self.fields)

    def boolean_value(self, value: FormValue) -> bool:
        return bool(value)

    def field_label(self, field: Field) -> str:
        return field.label

    def format_value(self, field: Field, value: FormValue) -> str:
        if field.kind == 'bool':
            return 'on' if self.boolean_value(value) else 'off'
        return '' if value is None else str(value)

    def parse_value(self, field: Field, value: str) -> FormValue:
        if field.kind == 'bool':
            text = value.strip().lower()
            if text not in ('on', 'off', 'true', 'false', 'yes', 'no', '1', '0'):
                raise ValueError(f'{field.label} must be a boolean')
            return field.normalize(text in ('on', 'true', 'yes', '1'))
        return field.normalize(value)

    def validate_value(self, field: Field, value: FormValue) -> FormValue:
        return field.normalize(value)

    def _validated_value(self, field: Field, value: FormValue) -> FormValue:
        value = self.validate_value(field, value)
        if field.validator is not None:
            message = field.validator(value)
            if message:
                raise ValueError(message)
        return value

    def set_value(self, field: Field, text: str) -> None:
        self.values[field.name] = self._validated_value(
            field, self.parse_value(field, text),
        )

    def activate(self) -> None:
        if not 0 <= self.focus < len(self.fields):
            return
        field = self.fields[self.focus]
        if field.kind == 'bool':
            self.set_value(
                field, 'off' if self.boolean_value(self.values[field.name]) else 'on',
            )
            return
        self.buffer = self.format_value(field, self.values[field.name])
        self.cursor = len(self.buffer)
        self.editing = True

    def finish_edit(self, cancel: bool = False) -> None:
        if self.editing and not cancel:
            self.set_value(self.fields[self.focus], self.buffer)
        self.editing = False

    def apply(
        self,
        on_save: Callable[[dict[str, FormValue]], None] | None = None,
    ) -> dict[str, FormValue]:
        self.finish_edit()
        values = self.values.copy()
        for index, field in enumerate(self.fields):
            try:
                values[field.name] = self._validated_value(field, values[field.name])
            except (TypeError, ValueError):
                self.focus = index
                raise
        if self.validator is not None:
            message = self.validator(MappingProxyType(values))
            if message:
                raise ValueError(message)
        if on_save is not None:
            on_save(values.copy())
        self.values = values
        self._applied = values.copy()
        return values.copy()

    def reset(self) -> None:
        self.finish_edit(cancel=True)
        self.values = self._applied.copy()
        self.cursor = 0

    def _choice_index(self, field: Field) -> int:
        current = self.buffer if self.editing else self.format_value(field, self.values[field.name])
        try:
            return field.choices.index(current)
        except ValueError:
            return 0

    def _cycle(self, step: int, editing: bool = False) -> None:
        field = self.fields[self.focus]
        selected = self._choice_index(field)
        value = field.choices[(selected + step) % len(field.choices)]
        if editing:
            self.buffer = value
        else:
            self.set_value(field, value)

    def _edit_text(self, field: Field, key: int | str) -> None:
        value = self.buffer
        cursor = min(max(0, self.cursor), len(value))
        self.cursor = cursor
        if key == curses.KEY_LEFT:
            self.cursor = max(0, cursor - 1)
        elif key == curses.KEY_RIGHT:
            self.cursor = min(len(value), cursor + 1)
        elif key == getattr(curses, 'KEY_HOME', None) or is_key(key, '\x01'):
            self.cursor = 0
        elif key == getattr(curses, 'KEY_END', None) or is_key(key, '\x05'):
            self.cursor = len(value)
        elif key == getattr(curses, 'KEY_BACKSPACE', None) or is_key(key, '\b', '\x7f'):
            if cursor:
                self.buffer = value[:cursor - 1] + value[cursor:]
                self.cursor -= 1
        elif key == getattr(curses, 'KEY_DC', None):
            self.buffer = value[:cursor] + value[cursor + 1:]
        elif is_key(key, '\x15'):
            self.buffer = ''
            self.cursor = 0
        elif is_key(key, '\x0b'):
            self.buffer = value[:cursor]
        else:
            character = key if isinstance(key, str) else chr(key) if 0 <= key < 128 else ''
            if not character or not character.isprintable():
                return
            candidate = value[:cursor] + character + value[cursor:]
            if field.max_length is not None and len(candidate) > field.max_length:
                return
            self.buffer = candidate
            self.cursor += len(character)

    def handle_key(self, key: int | str, page_size: int = 1) -> bool:
        if not self.control_count or key == getattr(curses, 'KEY_RESIZE', None):
            return False
        self.focus %= self.control_count
        backtab = key == getattr(curses, 'KEY_BTAB', None)
        tab = is_key(key, '\t') or backtab
        if self.editing:
            field = self.fields[self.focus]
            if is_key(key, '\x1b'):
                self.finish_edit(cancel=True)
            elif is_enter(key):
                self.finish_edit()
            elif tab:
                self.finish_edit()
                self.focus = (self.focus + (-1 if backtab else 1)) % self.control_count
            elif field.kind == 'enum':
                if key in (curses.KEY_UP, curses.KEY_LEFT) or is_key(key, 'k', 'K'):
                    self._cycle(-1, editing=True)
                elif key in (curses.KEY_DOWN, curses.KEY_RIGHT) or is_key(key, 'j', 'J'):
                    self._cycle(1, editing=True)
                elif key == getattr(curses, 'KEY_HOME', None):
                    self.buffer = field.choices[0]
                elif key == getattr(curses, 'KEY_END', None):
                    self.buffer = field.choices[-1]
            else:
                self._edit_text(field, key)
            return True
        if tab:
            self.focus = (self.focus + (-1 if backtab else 1)) % self.control_count
            return True
        selected = _selection_key(key, self.focus, self.control_count, page_size)
        if selected is not None:
            self.focus = selected
            return True
        if self.focus >= len(self.fields):
            return False
        field = self.fields[self.focus]
        if is_enter(key) or is_key(key, ' '):
            self.activate()
            return True
        if key in (curses.KEY_LEFT, curses.KEY_RIGHT):
            if field.kind == 'enum':
                self._cycle(-1 if key == curses.KEY_LEFT else 1)
                return True
            if field.kind == 'bool':
                self.activate()
                return True
        return False

    def _sync_view(self, rect: Rect) -> None:
        self.focus = min(max(0, self.focus), max(0, self.control_count - 1))
        if self.focus < len(self.fields):
            self.focus, self.scroll = _viewport(
                self.focus, self.scroll, len(self.fields), rect.height,
            )
        else:
            self.scroll = min(max(0, self.scroll), max(0, len(self.fields) - rect.height))

    def _layout(self, rect: Rect) -> tuple[int, int, int]:
        longest = max((text_width(self.field_label(field)) + 3 for field in self.fields), default=0)
        label_width = min(longest, rect.width // 2)
        left = rect.left + min(rect.width, label_width + 2)
        return label_width, left, max(0, rect.left + rect.width - left)

    def _choice_rect(self, rect: Rect) -> Rect | None:
        if not self.editing or not self.fields:
            return None
        field = self.fields[self.focus]
        if field.kind != 'enum':
            return None
        _, left, control_width = self._layout(rect)
        height = min(len(field.choices) + 2, rect.height)
        width = min(control_width, max(text_width(choice) for choice in field.choices) + 4)
        if height < 3 or width < 3:
            return None
        row = rect.top + self.focus - self.scroll
        top = max(rect.top, min(row + 1, rect.top + rect.height - height))
        return Rect(top, left, height, width)

    def click(self, rect: Rect, position: tuple[int, int]) -> bool:
        self._sync_view(rect)
        menu = self._choice_rect(rect)
        if menu is not None:
            if menu.row_at(position) is not None:
                row = menu.inset().row_at(position)
                if row is not None:
                    field = self.fields[self.focus]
                    _, scroll = _viewport(
                        self._choice_index(field), 0, len(field.choices), menu.height - 2,
                    )
                    index = scroll + row
                    if index < len(field.choices):
                        self.buffer = field.choices[index]
                        self.finish_edit()
                return True
            self.finish_edit(cancel=True)
        row = rect.row_at(position)
        if row is None or self.scroll + row >= len(self.fields):
            return False
        index = self.scroll + row
        if self.editing and index == self.focus:
            return True
        self.finish_edit()
        self.focus = index
        self.activate()
        return True

    def draw(
        self,
        canvas: Canvas,
        rect: Rect,
        mouse_position: tuple[int, int] | None = None,
    ) -> tuple[int, int] | None:
        canvas.clear(rect)
        self._sync_view(rect)
        label_width, left, control_width = self._layout(rect)
        hovered = rect.row_at(mouse_position)
        cursor_position = None
        for offset, field in enumerate(self.fields[self.scroll:self.scroll + rect.height]):
            index = self.scroll + offset
            row = rect.top + offset
            selected = index == self.focus
            attribute = item_attribute(
                canvas.attribute, selected, offset == hovered, canvas.attribute,
            )
            value = self.values[field.name]
            label = (canvas.glyphs['marker'] if selected else ' ') + ' '
            label += ('*' if value != self._applied[field.name] else ' ') + self.field_label(field)
            canvas.write(
                row, rect.left, _pad(label, label_width),
                canvas.attribute | curses.A_BOLD,
            )
            editing = selected and self.editing
            if field.kind in ('text', 'number'):
                cursor = self.cursor if editing else None
                framed = control_width >= 5
                inner_width = control_width - 4 if framed else control_width
                visible, cursor_column = canvas.text_view(
                    self.buffer if editing else self.format_value(field, value),
                    inner_width, cursor, field.secret,
                )
                text = '[ ' + visible + ' ]' if framed else visible
                if cursor is not None and inner_width > 0:
                    cursor_position = row, left + (2 if framed else 0) + cursor_column
            elif field.kind == 'bool':
                enabled = self.boolean_value(value)
                text = '[' + (canvas.glyphs['check'] if enabled else ' ') + '] '
                text += 'On' if enabled else 'Off'
            else:
                text = self.buffer if editing else self.format_value(field, value)
                text = '[ ' + text + ' ' + canvas.glyphs['down_arrow'] + ' ]'
            canvas.write(row, left, _pad(text, control_width), attribute)
        menu = self._choice_rect(rect)
        if menu is not None:
            canvas.shade(rect)
            canvas.box(menu)
            field = self.fields[self.focus]
            Menu(field.choices, self._choice_index(field)).draw(
                canvas, menu.inset(), mouse_position,
            )
        return cursor_position


class FormScreen(Form):
    ACTIONS = ('Save', 'Revert', 'Cancel')
    HELP_LINES = (
        'Tab/Shift-Tab or Up/Down (j/k): next/previous control.',
        'PageUp/PageDown: move a page; Home/End: first/last field.',
        'Enter/Space: edit, toggle a checkbox, or activate a button.',
        'Left/Right: cycle choices or toggle a checkbox.',
        'While editing, Enter accepts and Esc cancels the edit.',
        'Tab accepts an edit and moves to the next control.',
        'Ctrl+A/E: start/end; Ctrl+U: clear; Ctrl+K: erase to end.',
        'F4 or e: open the selected text field in the external editor.',
        "d: restore a field's default; r: revert all unsaved changes.",
        'F2, Ctrl+S, or s: save and close; Esc/q: close.',
        'u: toggle UTF-8 styling; ?: show help.',
        'Mouse: click controls, select choices, or scroll with the wheel.',
    )

    def __init__(
        self,
        title: str,
        subtitle: str,
        fields: Iterable[Field],
        values: Mapping[str, FormValue],
        defaults: Mapping[str, FormValue],
        on_save: Callable[[dict[str, FormValue]], None],
        editor: Callable[[str], str] | None = None,
    ) -> None:
        super().__init__(fields, values=values, defaults=defaults)
        self.title = title
        self.subtitle = subtitle
        self.default_label = 'Default'
        self.on_save = on_save
        self.editor = editor
        self.notice = ''

    @property
    def control_count(self) -> int:
        return len(self.fields) + len(self.ACTIONS)

    def default_note(self, field: Field) -> str:
        value = self.format_value(field, self.defaults[field.name])
        if field.secret and value:
            value = '(hidden)'
        return f"{self.default_label}: {value or '(empty)'}"

    def save(self) -> bool:
        try:
            self.apply(self.on_save)
        except Exception as exc:
            self.notice = f'Save failed: {exc}'
            return False
        return True

    def close(self, terminal: Terminal) -> bool | None:
        if not self.modified:
            return False
        choice = terminal.dialog(
            'Unsaved changes', ('Save changes before closing?',),
            ('Save', 'Discard', 'Cancel'), default=2,
        )
        if choice == 'Discard':
            return False
        if choice == 'Save' and self.save():
            return True
        return None

    def activate_control(self, terminal: Terminal) -> bool | None:
        if self.focus < len(self.fields):
            self.activate()
            self.notice = ''
            return None
        action = self.ACTIONS[self.focus - len(self.fields)]
        if action == 'Save':
            return True if self.save() else None
        if action == 'Revert':
            self.reset()
            self.notice = 'Restored the initial values'
            return None
        return self.close(terminal)

    def edit_external(self, terminal: Terminal) -> None:
        if self.focus >= len(self.fields):
            return
        field = self.fields[self.focus]
        if self.editor is None or field.kind not in ('text', 'number') or field.secret:
            self.notice = 'External editing is unavailable for this field'
            return
        text = self.buffer if self.editing else self.format_value(field, self.values[field.name])
        try:
            edited = terminal.suspend(lambda: self.editor(text))
        except Exception as exc:
            self.notice = f'Editor failed: {exc}'
            return
        if not self.editing:
            self.activate()
        self.buffer = edited
        self.cursor = len(edited)
        self.finish_edit()
        self.notice = ''

    def help(self, terminal: Terminal) -> None:
        lines = list(self.HELP_LINES)
        if self.focus < len(self.fields):
            field = self.fields[self.focus]
            lines.extend((
                '', self.field_label(field), field.description, self.default_note(field),
            ))
        if self.notice:
            lines[0:0] = [self.notice, '']
        terminal.dialog(self.title + ' help', tuple(lines))

    def _action_positions(self, rect: Rect) -> tuple[Rect, ...]:
        column = rect.left + 1
        positions = []
        for action in self.ACTIONS:
            size = text_width(action) + 4
            positions.append(Rect(rect.top + rect.height + 1, column, 1, size))
            column += size + 2
        return tuple(positions)

    def draw(self, terminal: Terminal) -> Rect | None:
        height, columns = terminal.window.getmaxyx()
        terminal.window.erase()
        if height < 12 or columns < 50:
            terminal.centered(max(0, height // 2 - 1), 'Terminal too small', curses.A_BOLD)
            terminal.centered(height // 2, 'Resize to at least 50 columns x 12 rows')
            terminal.centered(height // 2 + 1, 'Esc: cancel edit; q: close; Ctrl+C: quit', curses.A_DIM)
            terminal.refresh()
            return None
        frame = Rect(3, 2, height - 8, columns - 4)
        body = Rect(frame.top + 1, frame.left + 1, frame.height - 2, frame.width - 3)
        terminal.centered(0, self.title.upper(), terminal.attribute | curses.A_BOLD)
        terminal.write(1, frame.left, self.subtitle, curses.A_DIM, frame.width)
        terminal.rule(2, frame.left, frame.width)
        terminal.box(frame, 'VALUES' + (' *' if self.modified else ''))
        cursor = super().draw(terminal, body)
        terminal.scrollbar(
            Rect(body.top, frame.left + frame.width - 1, body.height, 1),
            len(self.fields), self.scroll,
        )
        count = len(self.fields)
        for offset, position in enumerate(self._action_positions(body)):
            terminal.write(
                position.top, position.left, '[ ' + self.ACTIONS[offset] + ' ]',
                item_attribute(terminal.attribute, self.focus == count + offset, False),
            )
        if self.focus < count:
            field = self.fields[self.focus]
            terminal.write(height - 4, frame.left, field.description, curses.A_DIM, frame.width)
            terminal.write(height - 3, frame.left, self.default_note(field), curses.A_DIM, frame.width)
        else:
            notes = (
                'Validate and save all changes, then close.',
                'Restore the values from when this screen opened.',
                'Close; ask about any unsaved changes.',
            )
            terminal.write(height - 4, frame.left, notes[self.focus - count], curses.A_DIM, frame.width)
        state = 'modified' if self.modified else 'unchanged'
        mode = 'UTF-8' if terminal.utf8_enabled else 'ASCII'
        input_mode = 'mouse' if terminal.mouse_enabled else 'keyboard'
        position = f'{min(count, self.scroll + 1)}-{min(count, self.scroll + body.height)}/{count}'
        status = self.notice or f'{state} | {mode} | {input_mode} | {position}'
        attribute = terminal.attribute | curses.A_REVERSE
        if self.notice:
            attribute |= curses.A_BOLD
        terminal.write(height - 2, frame.left, ' ' * frame.width, attribute)
        terminal.write(height - 2, frame.left, status, attribute, frame.width)
        if self.editing:
            shortcuts = 'Enter accept  Esc cancel  Tab next  Ctrl+U clear'
            if self.fields[self.focus].kind == 'enum':
                shortcuts = 'Up/Down choose  Enter accept  Esc cancel  Tab next'
        else:
            arrows = terminal.glyphs['up_arrow'] + terminal.glyphs['down_arrow']
            shortcuts = f'Tab/{arrows} move  Enter edit  s save  q close  ? help'
        terminal.write(height - 1, frame.left, shortcuts, curses.A_DIM, frame.width)
        terminal.refresh(cursor)
        return body

    def click_control(
        self,
        terminal: Terminal,
        rect: Rect,
        event: MouseEvent,
    ) -> bool | None:
        if event.scroll:
            if self.editing and self.fields[self.focus].kind == 'enum':
                self._cycle(event.scroll, editing=True)
            elif self.fields:
                self.finish_edit()
                self.focus = min(len(self.fields) - 1, max(0, self.focus + event.scroll * 3))
            return None
        if not event.clicked:
            return None
        if super().click(rect, event.position):
            return None
        for offset, position in enumerate(self._action_positions(rect)):
            if position.row_at(event.position) is not None:
                self.finish_edit()
                self.focus = len(self.fields) + offset
                return self.activate_control(terminal)
        return None

    def handle_event(
        self,
        terminal: Terminal,
        key: int | str,
        rect: Rect | None,
    ) -> bool | None:
        if key == curses.KEY_F1 or (not self.editing and is_key(key, '?')):
            self.help(terminal)
            return None
        if key == getattr(curses, 'KEY_MOUSE', None):
            event = read_mouse()
            if rect is not None and event is not None:
                self.notice = ''
                return self.click_control(terminal, rect, event)
            return None
        if rect is None:
            if is_key(key, '\x1b') and self.editing:
                self.finish_edit(cancel=True)
                self.notice = ''
            elif not self.editing and is_key(key, '\x1b', 'q', 'Q'):
                return self.close(terminal)
            return None
        if key == curses.KEY_F2 or is_key(key, '\x13'):
            return True if self.save() else None
        if key == curses.KEY_F4 or (not self.editing and is_key(key, 'e', 'E')):
            self.edit_external(terminal)
            return None
        if self.editing:
            if self.handle_key(key, rect.height):
                self.notice = ''
            return None
        if is_key(key, '\x1b', 'q', 'Q'):
            return self.close(terminal)
        if is_key(key, 's', 'S'):
            return True if self.save() else None
        if is_key(key, 'r', 'R'):
            self.reset()
            self.notice = 'Restored the initial values'
        elif is_key(key, 'u', 'U'):
            if terminal.set_utf8(not terminal.utf8_enabled):
                self.notice = ''
            else:
                self.notice = 'UTF-8 styling is unavailable in this locale'
        elif is_key(key, 'd', 'D') and self.focus < len(self.fields):
            field = self.fields[self.focus]
            self.values[field.name] = self.defaults[field.name]
            self.notice = 'Restored ' + self.default_label.lower()
        elif key == getattr(curses, 'KEY_END', None):
            self.focus = max(0, len(self.fields) - 1)
            self.notice = ''
        elif is_enter(key) or is_key(key, ' '):
            return self.activate_control(terminal)
        elif self.focus >= len(self.fields) and key in (curses.KEY_LEFT, curses.KEY_RIGHT):
            offset = self.focus - len(self.fields)
            step = -1 if key == curses.KEY_LEFT else 1
            self.focus = len(self.fields) + (offset + step) % len(self.ACTIONS)
            self.notice = ''
        elif self.handle_key(key, rect.height):
            self.notice = ''
        return None

    def run(self, terminal: Terminal) -> bool:
        while True:
            rect = self.draw(terminal)
            key = terminal.read_key()
            if key is None or key == getattr(curses, 'KEY_RESIZE', None):
                continue
            try:
                result = self.handle_event(terminal, key, rect)
            except (TypeError, ValueError) as exc:
                self.notice = str(exc)
                continue
            if result is not None:
                return result