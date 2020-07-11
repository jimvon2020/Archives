# !/usr/bin/python
# _*_ coding:utf-8 _*_

import re
import sys
from io import StringIO


class FontColor:
    BLACK = '\033[0;30m'
    DARK_GRAY = '\033[1;30m'
    LIGHT_GRAY = '\033[0;37m'
    BLUE = '\033[0;34m'
    LIGHT_BLUE = '\033[1;34m'
    GREEN = '\033[0;32m'
    LIGHT_GREEN = '\033[1;32m'
    CYAN = '\033[0;36m'
    LIGHT_CYAN = '\033[1;36m'
    RED = '\033[0;31m'
    LIGHT_RED = '\033[1;31m'
    PURPLE = '\033[0;35m'
    LIGHT_PURPLE = '\033[1;35m'
    BROWN = '\033[0;33m'
    YELLOW = '\033[1;33m'
    WHITE = '\033[1;37m'
    DEFAULT_COLOR = '\033[00m'
    RED_BOLD = '\033[01;31m'
    ENDC = '\033[0m'


def str_contains(container, keyword):
    if container.find(keyword) != -1:
        return True
    else:
        return False


class Crash(object):
    reg_ip_exp = r'''\d{3,5}'''
    ip_pattern = re.compile(reg_ip_exp)
    actual_log_start = len("11-05 17:34:51.704  3544  3544 E ")

    def __init__(self, line_num, crash_line):
        self.__line_num = line_num
        self.__crash_line = crash_line
        self.__stack_string = StringIO()
        self.__ip_pattern = re.compile(Crash.reg_ip_exp)

    def get_crash_line_content(self):
        return self.__crash_line

    def get_stack_string(self):
        return self.__stack_string.getvalue()

    def save_stack_string(self, line):
        self.__stack_string.write(line)

    def get_crash_line(self):
        return self.__line_num

    def get_crash_pid(self):
        pid_pos = Crash.actual_log_start
        return Crash.ip_pattern.findall(self.__crash_line[pid_pos:])[0]

    def __str__(self) -> str:
        return super().__str__()


class CrashParser(object):
    time_stamp_len = len("10-26 10:06:26.623 ")
    log_tag_len = len("10-26 10:06:26.698 30494 30494 D WindowControl2: [VivoBrowser-eea40ff]:")

    def __init__(self, file_path) -> None:
        self.open_file = open(file_path, "rb+")
        self.all_lines = []
        self.dump_process_pid = 0
        self.__read_all_lines()
        self.all_crash = []
        self.calc_all_crash_line()

    def __read_all_lines(self):
        index = 1
        failed_count = 0
        while 1:
            try:
                line_bytes = self.open_file.readline()
                if not line_bytes:
                    break

                line = line_bytes.decode("utf-8")
                index += 1

                if line.find("crash_dump32") != -1:
                    self.dump_process_pid = CrashParser.get_line_process(line)

                self.all_lines.append(line)
            except UnicodeDecodeError:
                failed_count += 1
                continue

        print("正确读取到日志文件总行数：", len(self.all_lines), "处理失败日志行数", failed_count)

    def calc_all_crash_line(self):
        crash_line = 0
        self.all_crash.clear()
        for line_content in self.all_lines:
            crash_line += 1
            if str_contains(line_content, "Process com.vivo.browser ") and str_contains(line_content, "has died"):
                self.all_crash.append(Crash(crash_line, line_content))
            if str_contains(line_content, "AndroidRuntime: Process: com.vivo.browser, PID"):
                self.all_crash.append(Crash(crash_line, line_content))

    def print_crash_stack(self):
        for crash in self.all_crash:
            print(crash.get_stack_string())
            print("####" * 32)


    @staticmethod
    def get_line_process(line):
        actual_line = line[0:CrashParser.log_tag_len]
        keywords = actual_line.split()
        return keywords[2]

    @staticmethod
    def get_line_log_tag(line):
        actual_line = line[0:CrashParser.log_tag_len]
        keywords = actual_line.split()
        return keywords[4]

    def get_browser_pid(self):
        crash_pids = []
        start_line = 0
        for crash in self.all_crash:
            crash_pid = crash.get_crash_pid()
            crash_pids.append(crash_pid)
            has_native = False
            end_line = crash.get_crash_line()
            # print("Crash", crash_pid, "发生在", end_line, "行")
            # print("在", start_line, "和", end_line, "之间搜索堆栈")

            for line_content in self.all_lines[start_line: end_line + 200]:
                contains_native = line_content.find("libwebviewchromium_vivo.so") != -1
                if contains_native:
                    has_native = True

                if CrashParser.get_line_process(line_content) == crash_pid and CrashParser.get_line_log_tag(
                        line_content) == "F":
                    crash.save_stack_string(line_content)

                if CrashParser.get_line_process(line_content) == self.dump_process_pid or contains_native:
                    crash.save_stack_string(line_content)

                if CrashParser.get_line_process(line_content) == crash_pid and CrashParser.get_line_log_tag(
                        line_content) == "E" and line_content.find("AndroidRuntime:") != -1:
                    crash.save_stack_string(line_content)

                if has_native and not contains_native:
                    break

            start_line = end_line

            crash.save_stack_string(crash.get_crash_line_content())

        return crash_pids


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("crash_stack.py crash_log")
        exit(0)

    parser = CrashParser(sys.argv[1])
    all_crash_pids = parser.get_browser_pid()
    print("检测到" + str(len(all_crash_pids)) + "次Crash， Crash进程号为 " + " ".join(all_crash_pids))
    print("####" * 32)
    parser.print_crash_stack()
