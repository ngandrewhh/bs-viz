import re

from PyQt6.QtCore import QSize, Qt, QMargins
from PyQt6.QtGui import QAction
import PyQt6.QtWidgets as qt
from bs4 import BeautifulSoup

import requests

URL_RE = re.compile(r"(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?")
CONTENT_MARGINS_NARROW = QMargins(2, 0, 2, 0)
CONTENT_MARGINS_NORMAL = QMargins(2, 2, 2, 2)
LOREM_IPSUM = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent finibus tortor ut viverra pretium. Fusce ut nulla libero. Aenean mattis eget nisi non pellentesque. Aenean tempus ex eget sapien rhoncus suscipit. Fusce non lectus velit. Mauris semper nisl id sapien congue, eu mollis turpis tempor. Aenean euismod libero vitae sem dapibus convallis.

Vestibulum vel laoreet turpis. Vivamus fringilla dolor nunc. Sed varius, neque vitae gravida elementum, velit ligula aliquam augue, eu auctor arcu leo et quam. Vestibulum magna nulla, hendrerit eget ipsum quis, dictum lacinia sem. Cras suscipit ex sit amet magna laoreet vestibulum. Nam tempus quis tortor ac efficitur. Nam fermentum urna vel sem rutrum, id ultrices dolor iaculis. In massa lectus, luctus sed purus eget, aliquet imperdiet purus. Sed porttitor lectus eget tincidunt lobortis.

Phasellus porta quam eget justo efficitur, vitae convallis felis posuere. Nunc varius purus lobortis orci ultricies mollis. Ut sed felis a lectus sagittis varius. In rutrum sed enim nec suscipit. Donec purus lectus, convallis vel pulvinar in, hendrerit sit amet ex. Cras convallis suscipit augue, id tempus libero. Integer tempus laoreet interdum. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Nulla finibus magna turpis, quis malesuada ligula efficitur non. Donec faucibus nec leo sed tempus. Nunc eleifend, dolor sit amet dictum dignissim, enim nibh faucibus mi, ut molestie erat odio at elit. Pellentesque eu enim leo.

Donec ac posuere elit. Maecenas nec augue malesuada, aliquet est id, placerat neque. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Proin bibendum lorem mattis ornare consequat. Sed fermentum finibus lacinia. Curabitur vitae velit nibh. Vivamus et nisl et magna volutpat convallis et at neque. Donec mauris dolor, rhoncus sit amet urna ac, porttitor varius nibh. Proin tempus placerat leo.

Ut facilisis facilisis purus non tincidunt. Cras vel sem placerat, congue mauris quis, aliquam lectus. Ut at fringilla sapien, at bibendum leo. Nulla egestas volutpat nisi hendrerit rutrum. Curabitur vel erat fermentum, sagittis nisl suscipit, fermentum nibh. Nunc ut metus ac sapien ornare tincidunt. Nullam augue magna, rhoncus ac neque eu, maximus suscipit lorem. In vel diam placerat velit maximus ullamcorper nec quis mi. Morbi viverra tellus eget ante consectetur lacinia. Vivamus tristique risus vel consequat porttitor. Phasellus malesuada in lectus at sodales. Aliquam tincidunt blandit est. Aliquam pretium dictum justo, ut luctus lacus aliquet sed. Fusce in risus arcu. Fusce id magna nec nisi condimentum aliquam nec at dui. Sed metus orci, laoreet ut ligula vitae, lobortis consectetur diam.
"""


class ScrollDisplay(qt.QScrollArea):
    # constructor
    def __init__(self):
        super().__init__()
        self.is_output_raw = 0

        # making widget resizable
        self.setWidgetResizable(True)
        self.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Expanding)

        # creating text field
        self.label = qt.QTextEdit(self)
        self.label.setLineWrapMode(self.label.LineWrapMode.NoWrap)
        self.label.setReadOnly(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.label.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Expanding)

        self.setWidget(self.label)

    def set_text(self, text):
        if self.is_output_raw == 0:
            self.label.setText(text)
        elif self.is_output_raw == 1:
            self.label.setPlainText(text)
        elif self.is_output_raw == 2:
            plain_soup = BeautifulSoup(text, 'lxml')
            self.label.setPlainText(re.sub('\n+', '\n', plain_soup.text))


class FormRadioButtons:
    def new(*button_names):
        rdo_gbox = qt.QGroupBox()
        rdo_hbox = qt.QHBoxLayout()

        lst_btn = []
        for button_name in button_names:
            btn = qt.QRadioButton(button_name)
            lst_btn.append(btn)
            rdo_hbox.addWidget(btn)

        lst_btn[0].setChecked(True)
        rdo_gbox.setLayout(rdo_hbox)

        rdo_hbox.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        rdo_hbox.setContentsMargins(CONTENT_MARGINS_NARROW)
        rdo_gbox.setSizePolicy(qt.QSizePolicy.Policy.Expanding, qt.QSizePolicy.Policy.Minimum)
        return rdo_gbox, *lst_btn


class EntityBox(qt.QWidget):
    TAG_EXCLUDE = ['script', 'meta', 'head', 'noscript', 'svg', 'html', 'body', 'div', 'aside', 'main']

    def __init__(self, parent):

        # parent
        super().__init__()
        self.parent = parent

        # data
        self.status_code = -1
        self.data = None
        self.soup = None
        self.str_html = LOREM_IPSUM
        self.str_text = LOREM_IPSUM
        self.is_with_css = True

        # widgets
        self.display = ScrollDisplay()
        self.input_url = qt.QLineEdit()
        self.input_filter = qt.QLineEdit()

        self.rdo_gbox_with, self.rdo_with_css, self.rdo_with_text = FormRadioButtons.new("CSS", "Text")
        self.rdo_gbox_disp, self.rdo_raw, self.rdo_plain, self.rdo_clean = FormRadioButtons.new("HTML", "Raw", "Clean")

        self.btn_fetch = qt.QPushButton("Fetch")
        self.btn_read = qt.QPushButton("Freeze")

        self.btn_read.setCheckable(True)
        self.input_filter.setEnabled(False)

        # layout
        layout_l1 = qt.QGridLayout()
        layout_l2_left = qt.QVBoxLayout()
        layout_l3_form = qt.QFormLayout()
        layout_l3_btn = qt.QHBoxLayout()
        layout_l3_form.setFieldGrowthPolicy(qt.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Form
        layout_l3_form.addRow("URL", self.input_url)
        layout_l3_form.addRow("Filter", self.input_filter)
        layout_l3_form.addRow("With", self.rdo_gbox_with)
        layout_l3_form.addRow("Display", self.rdo_gbox_disp)

        # Form Button
        layout_l3_btn.addWidget(self.btn_fetch)
        layout_l3_btn.addWidget(self.btn_read)

        layout_l2_left.addLayout(layout_l3_form)
        layout_l2_left.addLayout(layout_l3_btn)
        layout_l1.addLayout(layout_l2_left, 0, 0)
        layout_l1.addWidget(self.display, 0, 1)
        layout_l1.setColumnStretch(0, 1)
        layout_l1.setColumnStretch(1, 2)

        layout_l3_form.setContentsMargins(CONTENT_MARGINS_NARROW)

        self.setMinimumSize(720, 180)

        # collect
        self.setLayout(layout_l1)
        self.input_url.setText("https://")

        # reaction
        self.btn_fetch.clicked.connect(self.requests_get)
        self.input_filter.textChanged.connect(self.requests_extract)
        # self.btn_read.clicked.connect(self.requests_read)
        self.rdo_raw.clicked.connect(self.output_raw)
        self.rdo_plain.clicked.connect(self.output_plain)
        self.rdo_clean.clicked.connect(self.output_clean)
        self.rdo_with_css.clicked.connect(self.with_css)
        self.rdo_with_text.clicked.connect(self.with_text)

    def requests_get(self, _):
        if not self.data:
            if not bool(URL_RE.match(self.input_url.text())):
                self.parent.set_status_bar("The provided URL is invalid. It must starts with [ http(s):// ].")
                return

            try:
                resp = requests.get(self.input_url.text())
            except BaseException as e:
                self.parent.set_status_bar(repr(e))
                return

            if resp.status_code == 200:
                self.status_code = resp.status_code
                self.data = resp.text
                self.soup = BeautifulSoup(self.data, 'lxml')
                self.str_html = self.soup.prettify()
                self.btn_fetch.setEnabled(False)
                # self.btn_fetch.setText(str(resp))
                self.input_filter.setEnabled(True)
                self.requests_extract(_)
                self.parent.set_status_bar("URL Fetch succeeded.")
            else:
                self.parent.set_status_bar(repr(resp))

    def requests_extract(self, _):
        if self.status_code != 200:
            return

        if not len(self.input_filter.text()):
            self.str_html = self.soup.prettify()
            self.display.set_text(self.str_html)
            return

        try:
            if self.is_with_css:
                repo_html, repo_text = [], []
                for tag in list(self.soup.find_all(class_=re.compile(self.input_filter.text()))):
                    if tag.name not in EntityBox.TAG_EXCLUDE:
                        if str(tag) not in repo_html:
                            repo_html.append(str(tag))
                self.str_html = '<br>\n'.join(repo_html)

            else:
                repo_html = []
                for tag in list(self.soup.find_all()):
                    if (tag.name not in EntityBox.TAG_EXCLUDE) and (self.input_filter.text() in tag.text):
                        if str(tag) not in repo_html:
                            repo_html.append(str(tag))
                self.str_html = '<br>\n'.join(repo_html)

        except BaseException as e:
            self.str_html = repr(e)

        self.display.set_text(self.str_html)

    def output_raw(self, _):
        self.display.is_output_raw = 0
        if self.status_code != 200:
            return

        self.display.set_text(self.str_html)

    def output_plain(self, _):
        self.display.is_output_raw = 1
        if self.status_code != 200:
            return

        self.display.set_text(self.str_html)

    def output_clean(self, _):
        self.display.is_output_raw = 2
        if self.status_code != 200:
            return

        self.display.set_text(self.str_html)

    def with_css(self, _):
        self.is_with_css = True
        if self.status_code != 200:
            return

        self.display.set_text(self.str_html)

    def with_text(self, _):
        self.is_with_css = False
        if self.status_code != 200:
            return

        self.display.set_text(self.str_html)


# Subclass QMainWindow to customize your application's main window
class MainWindow(qt.QMainWindow):
    def __init__(self):
        super().__init__()

        # window parameters
        self.setWindowTitle(f"BeautifulSoup GUI v0.1")
        self.setMinimumSize(QSize(840, 360))
        self.setMaximumSize(QSize(840, 1080))

        self.statusBar = qt.QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self.set_status_bar("Normal")

        self.lst_display = list()

        # self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # self.customContextMenuRequested.connect(lambda: print("calling context menu"))

        # widgets init
        self.btn_add_display = qt.QPushButton("Add Display")
        self.btn_rmv_display = qt.QPushButton("Remove Display")
        self.btn_add_display.setMaximumWidth(160)
        self.btn_rmv_display.setMaximumWidth(160)

        # 1/
        widget_main = qt.QWidget()
        layout_main = qt.QVBoxLayout()
        self.layout_main_fixed_btn = qt.QHBoxLayout()
        self.layout_main_fixed_btn.addWidget(self.btn_add_display, alignment=Qt.AlignmentFlag.AlignLeft)
        self.layout_main_fixed_btn.addWidget(self.btn_rmv_display, alignment=Qt.AlignmentFlag.AlignLeft)

        self.layout_main_display = qt.QScrollArea()
        self.layout_main_display_widget = qt.QWidget()
        self.layout_main_display_widget_layout = qt.QVBoxLayout()

        self.layout_main_display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.layout_main_display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.layout_main_display.setWidgetResizable(True)

        self.layout_main_display.setWidget(self.layout_main_display_widget)
        self.layout_main_display_widget.setLayout(self.layout_main_display_widget_layout)

        layout_main.addLayout(self.layout_main_fixed_btn)
        layout_main.addWidget(self.layout_main_display)
        widget_main.setLayout(layout_main)
        self.layout_main_fixed_btn.setAlignment(Qt.AlignmentFlag.AlignLeft)

        widget_main.setContentsMargins(CONTENT_MARGINS_NORMAL)
        layout_main.setContentsMargins(CONTENT_MARGINS_NORMAL)

        # connect
        self.btn_add_display.clicked.connect(self.add_display)
        self.btn_rmv_display.clicked.connect(self.rmv_display)

        self.setCentralWidget(widget_main)

    def add_display(self):
        eb = EntityBox(self)
        self.lst_display.append(eb)
        self.layout_main_display_widget_layout.addWidget(eb)
        self.set_status_bar('Added new widget')

    def rmv_display(self):
        if len(self.lst_display):
            eb: EntityBox = self.lst_display.pop()
            self.layout_main_display_widget_layout.removeWidget(eb)
            self.set_status_bar('Removed bottom most widget')

        else:
            self.set_status_bar('Cannot remove widget')

    def set_status_bar(self, e):
        self.statusBar.showMessage(e)

    def contextMenuEvent(self, e):
        context = qt.QMenu(self)
        context.addAction(QAction("test 1", self))
        context.addAction(QAction("test 2", self))
        context.addAction(QAction("test 3", self))
        # context.hovered.connect(lambda x: print("hovered over", x.text()))
        context.triggered.connect(lambda x: print("pressed", x.str_html()))
        context.exec(e.globalPos())

    def on_trigger(self, *args, **kwargs):
        print(args, kwargs)

    def _mousePressEvent(self, e):
        pass
        # if e.button() == Qt.MouseButton.LeftButton:
        #     # handle the left-button press in here
        #     self.display.set_text("mousePressEvent LEFT")
        #
        # elif e.button() == Qt.MouseButton.MiddleButton:
        #     # handle the middle-button press in here.
        #     self.display.set_text("mousePressEvent MIDDLE")
        #
        # elif e.button() == Qt.MouseButton.RightButton:
        #     # handle the right-button press in here.
        #     self.display.set_text("mousePressEvent RIGHT")

    def _mouseReleaseEvent(self, e):
        pass
        # if e.button() == Qt.MouseButton.LeftButton:
        #     self.display.set_text("mouseReleaseEvent LEFT")
        #
        # elif e.button() == Qt.MouseButton.MiddleButton:
        #     self.display.set_text("mouseReleaseEvent MIDDLE")
        #
        # elif e.button() == Qt.MouseButton.RightButton:
        #     self.display.set_text("mouseReleaseEvent RIGHT")

    def _mouseDoubleClickEvent(self, e):
        pass
        # if e.button() == Qt.MouseButton.LeftButton:
        #     self.display.set_text("mouseDoubleClickEvent LEFT")
        #
        # elif e.button() == Qt.MouseButton.MiddleButton:
        #     self.display.set_text("mouseDoubleClickEvent MIDDLE")
        #
        # elif e.button() == Qt.MouseButton.RightButton:
        #     self.display.set_text("mouseDoubleClickEvent RIGHT")


def main():
    app = qt.QApplication([])

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == '__main__':
    main()
