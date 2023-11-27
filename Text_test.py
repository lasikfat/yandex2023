import sys
import random
import sqlite3
from PyQt5.QtCore import Qt, QTime, QEvent
from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, QTextEdit, QApplication, QLabel, QHBoxLayout\



class MyLineEdit(QLineEdit):

    def __init__(self):
        super().__init__()
        self.backspace_flag = False
        self.con = sqlite3.connect("result.sqlite")

    def event(self, event):
        if event.type() == QEvent.KeyPress and event.key() != Qt.Key_Backspace:
            self.backspace_flag = False
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Backspace:
            self.backspace_flag = True
        return QLineEdit.event(self, event)


class Example(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.random_line = ""
        self.line_number = 0

        self.time = QTime()
        self.time.start()
        grid = QGridLayout()
        grid.setContentsMargins(1, 1, 1, 1)
        grid.setSpacing(1)
        self.setLayout(grid)
        self.entry_widget = MyLineEdit()
        grid.addWidget(self.entry_widget, 0, 0, 1, 5, Qt.AlignTop)
        grid.setRowStretch(0, 0)
        self.text_widget = QTextEdit(self)
        self.text_widget.setReadOnly(True)
        grid.addWidget(self.text_widget, 1, 0, 1, 5, Qt.AlignTop)
        grid.setRowStretch(1, 10)

        hbox = QHBoxLayout()
        grid.addLayout(hbox, 2, 0, 1, 5)
        self.wpm_current_label = QLabel(self)
        self.wpm_current_label.setMaximumWidth(140)
        hbox.addWidget(self.wpm_current_label)
        self.wpm_average_label = QLabel(self)
        hbox.addWidget(self.wpm_average_label)
        self.errors_label = QLabel(self)
        hbox.addWidget(self.errors_label)

        self.initialize_all()

        self.background_right = "background-color: white;"
        self.background_wrong = "background-color: pink;"
        self.font = "font-size: 12pt; font-family: Verdana;font-weight: bold;"
        self.next_char = """<p1 style="background-color:lightblue;">"""

        self.wpm_current_label.setStyleSheet(self.font)
        self.wpm_average_label.setStyleSheet(self.font)
        self.errors_label.setStyleSheet(self.font)

        self.entry_widget.setStyleSheet(self.background_right + self.font)
        self.text_widget.setStyleSheet("QTextEdit{{{} {}}}".format(self.background_right, self.font))

        self.load_random_line()

        self.entry_widget.textChanged.connect(lambda changed: self.text_widget_handler(changed, self.random_line))

        self.setGeometry(580, 0, 515, 115)
        self.setWindowTitle('Тест скорости печати')
        self.show()

    def initialize_all(self, clear_text_widget=False):
        self.test_end = False
        self.test_start = False
        self.entry_widget.setReadOnly(False)
        self.match_end_index = 0
        self.wpm_value = 0
        self.error_counter = 0
        self.time.restart()
        self.average_value = self.get_average_speed("speed_records.txt")
        self.wpm_current_label.setText("Скорость : {:.2f}".format(self.wpm_value))
        self.wpm_average_label.setText("Средняя : {:.2f}".format(self.average_value))
        self.errors_label.setText("Ошибки : {:d}".format(self.error_counter))
        if clear_text_widget:
            self.text_widget.setHtml(self.next_char + self.random_line[0] + "</p1>" + self.random_line[1:])

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Tab:
            self.entry_widget.clear()
            self.entry_widget.setFocus()
            self.initialize_all(True)
        if event.key() == Qt.Key_Escape:
            self.entry_widget.clear()
            self.load_random_line()
            self.initialize_all()

    def get_random_line(self, filename):
        with open(filename, "rt", encoding="utf-8") as text_file:
            random_line = next(text_file)
            line_number = 0
            for num, line in enumerate(text_file):
                if random.randrange(num + 2):
                    continue
                random_line = line
                line_number = num
        return line_number, random_line

    def load_random_line(self):
        self.text_widget.clear()
        self.line_number, self.random_line = self.get_random_line("text.txt")
        self.text_widget.setHtml(self.next_char + self.random_line[0] + "</p1>" + self.random_line[1:])

    def matcher(self, string_a, string_b):
        """
        string_a : input string
        string_b : full string to match to
        return len(not_matched_chars, matched_chars)
        """

        if string_a == string_b[0:len(string_a)]:
            matched = len(string_a)
        else:
            matched = self.match_end_index
            for i, char in enumerate(string_a[self.match_end_index + 1:len(string_a)]):
                if string_a[0:self.match_end_index + 1 + i] == string_b[0:self.match_end_index + 1 + i]:
                    matched += 1

        not_matched = len(string_a) - matched
        self.match_end_index = matched

        return not_matched, matched

    def text_widget_handler(self, string_a, string_b):

        if self.test_end:
            return None

        not_matched, matched = self.matcher(string_a, string_b)

        if not_matched >= 1:
            if not self.entry_widget.backspace_flag:
                self.error_counter += 1
                self.errors_label.setText("#Error : {:d}".format(self.error_counter))

            self.text_widget.setStyleSheet("QTextEdit{{{} {}}}".format(self.background_wrong, self.font))
            self.text_widget.setHtml(
                "<font color=\"Gray\">" + string_b[:matched] + "</font>" + "<font color=\"Red\">" + string_b[matched:matched + not_matched] + "</font>" + string_b[matched + not_matched:])

        else:
            if (not self.test_start) and (matched > 0):
                self.time.restart()
                self.wpm_value = 0
                self.test_start = True

            self.text_widget.setStyleSheet("QTextEdit{{{} {}}}".format(self.background_right, self.font))
            self.text_widget.setHtml("<font color=\"Gray\">" + string_b[:matched] + "</font>" + self.next_char + string_b[matched] + "</p1>" + string_b[matched + 1 + not_matched:])

            if self.test_start:
                if not self.time.elapsed():
                    self.wpm_value = 999
                else:
                    self.wpm_value = round((matched) / (5 * (self.time.elapsed()) / (1000 * 60)), 2)
                if self.wpm_value > 999:
                    self.wpm_value = 999
        self.wpm_current_label.setText("WMP : {:.2f}".format(self.wpm_value))

        if matched == (len(self.random_line) - 1):
            self.write_record("speed_records.txt", self.wpm_value)
            #self.pushButton.clicked.connect(self.update_result)
            self.average_value = self.get_average_speed("speed_records.txt")
            self.wpm_average_label.setText("Average : {:.2f}".format(self.average_value))
            self.test_end = True
            self.entry_widget.setReadOnly(True)

    def write_record(self, filename, wpm_value):
        with open(filename, "a") as record_file:
            record_file.write(str(wpm_value) + "\n")

    def get_average_speed(self, filename):
        average = 0
        count = 0
        with open(filename, "rt") as record_file:
            for value in record_file:
                average += float(value)
                count += 1
            average = average / count
        return round(average, 2)

    def closeEvent(self, event):
        self.con.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
