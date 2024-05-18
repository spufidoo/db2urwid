#! /usr/bin/python3

import sys
import ibm_db
import urwid as u
import logging
import configparser
from getpass import getpass

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Load configuration
config = configparser.ConfigParser()
config.read('db_config.ini')

class ListItem(u.WidgetWrap):
    def __init__(self, employee):
        self.content = employee
        EMPNO = employee["EMPNO"]
        t = u.AttrWrap(u.Text(EMPNO), "employee", "employee_selected")
        u.WidgetWrap.__init__(self, t)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key

class ListView(u.WidgetWrap):
    def __init__(self):
        u.register_signal(self.__class__, ['show_details'])
        self.walker = u.SimpleFocusListWalker([])
        lb = u.ListBox(self.walker)
        u.WidgetWrap.__init__(self, lb)

    def modified(self):
        focus_w, _ = self.walker.get_focus()
        u.emit_signal(self, 'show_details', focus_w.content)

    def set_data(self, employees):
        employee_widgets = [ListItem(e) for e in employees]
        u.disconnect_signal(self.walker, 'modified', self.modified)
        self.walker.clear()
        self.walker.extend(employee_widgets)
        u.connect_signal(self.walker, "modified", self.modified)
        self.walker.set_focus(0)

class DetailView(u.WidgetWrap):
    def __init__(self):
        t = u.Text("")
        u.WidgetWrap.__init__(self, t)

    def set_employee(self, c):
        s = f'EMPNO:      {c["EMPNO"]}\nFirst:      {c["FIRSTNME"]}\nInitial:    {c["MIDINIT"]}\nLast:       {c["LASTNAME"]}\nDept:       {c["WORKDEPT"]}\nPhone:      {c["PHONENO"]}\nHired:      {c["HIREDATE"]}\nJob:        {c["JOB"]}\nSex:        {c["SEX"]}\nBirthdate:  {c["BIRTHDATE"]}\nSalary:     {c["SALARY"]}\nBonus:      {c["BONUS"]}\nCommission: {c["COMM"]}\n'
        self._w.set_text(s)

class App(object):
    def unhandled_input(self, key):
        if key in ('esc',):
            raise u.ExitMainLoop()

    def show_details(self, employee):
        self.detail_view.set_employee(employee)

    def __init__(self):
        self.palette = [
            ("bg", "black", "white"),
            ("employee", "black", "white"),
            ("employee_selected", "black", "yellow"),
            ("footer", "white, bold", "dark red")
        ]

        self.list_view = ListView()
        self.detail_view = DetailView()

        u.connect_signal(self.list_view, 'show_details', self.show_details)
        footer = u.AttrWrap(u.Text(" ESC to exit"), "footer")
        col_rows = u.raw_display.Screen().get_cols_rows()
        h = col_rows[0] - 2

        f1 = u.Filler(self.list_view, valign='top', height=h)
        f2 = u.Filler(self.detail_view, valign='top')

        c_list = u.LineBox(f1, title="Employees")
        c_details = u.LineBox(f2, title="Employee Details")

        columns = u.Columns([('weight', 20, c_list), ('weight', 80, c_details)])

        frame = u.AttrMap(u.Frame(body=columns, footer=footer), 'bg')

        self.loop = u.MainLoop(frame, self.palette, unhandled_input=self.unhandled_input)

    def connect_to_db(self):
        max_attempts = 3
        attempts = 0
        database = config['database']['name']
        hostname = config['database']['hostname']
        port = config['database']['port']
        userid = config['database']['userid']

        while attempts < max_attempts:
            password = getpass("Enter password:")

            try:
                conn_str = f"DATABASE={database};HOSTNAME={hostname};PORT={port};PROTOCOL=TCPIP;UID={userid};PWD={password};"
                conn = ibm_db.connect(conn_str, '', '')
                return conn
            except Exception as e:
                attempts += 1
                if ibm_db.conn_error() == "08001":
                    logger.error(f"Nope. Try again. You have {max_attempts - attempts} attempts left.")
                else:
                    logger.error(f"Connection failed: {e}")
        logger.critical(f"You tried {attempts} invalid passwords. Bye bye.")
        sys.exit()

    def update_data(self, search_term=''):
        employees = []
        conn = self.connect_to_db()

        sql = "SELECT * FROM DB2INST1.EMP"
        if search_term:
            sql += f" WHERE LASTNAME LIKE '{search_term}%'"

        stmt = ibm_db.exec_immediate(conn, sql)

        while True:
            data_record = ibm_db.fetch_assoc(stmt)
            if not data_record:
                break
            employees.append(data_record)

        ibm_db.close(conn)
        self.list_view.set_data(employees)

    def start(self, search_term=''):
        self.update_data(search_term)
        self.loop.run()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Employee Viewer')
    parser.add_argument('--search', type=str, help='Search term for employee last name', default='')

    args = parser.parse_args()
    app = App()
    app.start(args.search)
