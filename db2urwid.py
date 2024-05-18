#! /usr/bin/python3

import sys
import ibm_db
import urwid as u

# Define And Initialize The Appropriate Variables
resultSet = False
dataRecord = False

class ListItem(u.WidgetWrap):
    def __init__ (self, employee):
        self.content = employee
        EMPNO = employee["EMPNO"]
        t = u.AttrWrap(u.Text(EMPNO), "employee", "employee_selected")
        u.WidgetWrap.__init__(self, t)

    def selectable (self):
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

    def set_data(self, countries):
        countries_widgets = [ListItem(c) for c in countries]
        u.disconnect_signal(self.walker, 'modified', self.modified)
        while len(self.walker) > 0:
            self.walker.pop()
        self.walker.extend(countries_widgets)
        u.connect_signal(self.walker, "modified", self.modified)
        self.walker.set_focus(0)

class DetailView(u.WidgetWrap):
    def __init__ (self):
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
        self.palette = {
            ("bg",               "black",       "white"),
            ("employee",          "black",       "white"),
            ("employee_selected", "black",       "yellow"),
            ("footer",           "white, bold", "dark red")
        }

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
        database = 'SAMPLE'
        hostname = 'odin.local'
        port = '25000'
        userid = 'db2inst1'

        from getpass import getpass

        while attempts < max_attempts:
            password = getpass("Enter password:")

            try:
                conn_str= f"DATABASE={database};HOSTNAME={hostname};PORT={port};PROTOCOL=TCPIP;UID={userid};PWD={password};"
                conn = ibm_db.connect(conn_str,'','')
            except Exception as e:
                attempts += 1
                if ibm_db.conn_error() == "08001":
                    print (f"Nope. Try again. You have {max_attempts-attempts} attempts left.")
                else:
                    print(e)
            else:
                break

        if attempts == max_attempts:
            print(f"You tried {attempts} invalid passwords. Bye bye.")
            exit()
        return conn

    def update_data(self):
        l = ([])
        conn = self.connect_to_db()

        #sql = "SELECT * FROM DB2INST1.EMP WHERE LASTNAME LIKE 'H%'"
        sql = "SELECT * FROM DB2INST1.EMP"
        stmt = ibm_db.exec_immediate(conn, sql)
        # As Long As There Are Records
        noData = False
        loopCounter = 1
        while noData is False:

            # Retrieve A Record And Store It In A Python Dictionary
            try:
                dataRecord = ibm_db.fetch_assoc(stmt)
            except:
                dataRecord = False

            # If The Data Could Not Be Retrieved Or If There Was No Data To Retrieve, Set The
            # "No Data" Flag And Exit The Loop
            if dataRecord is False:
                noData = True

            # Otherwise, Display The Information Retrieved
            else:
                l.append(dataRecord)
                loopCounter += 1

        # Close The Database Connection That Was Opened Earlier
        ibm_db.close(conn)

        self.list_view.set_data(l)

    def start(self):
        self.update_data()
        self.loop.run()

if __name__ == '__main__':

    app = App()
    app.start()
