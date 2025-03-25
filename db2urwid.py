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
        s = (f'EMPNO:      {c["EMPNO"]}\n'
             f'First:      {c["FIRSTNME"]}\n'
             f'Initial:    {c["MIDINIT"]}\n'
             f'Last:       {c["LASTNAME"]}\n'
             f'Dept:       {c["WORKDEPT"]}\n'
             f'Phone:      {c["PHONENO"]}\n'
             f'Hired:      {c["HIREDATE"]}\n'
             f'Job:        {c["JOB"]}\n'
             f'Sex:        {c["SEX"]}\n'
             f'Birthdate:  {c["BIRTHDATE"]}\n'
             f'Salary:     {c["SALARY"]}\n'
             f'Bonus:      {c["BONUS"]}\n'
             f'Commission: {c["COMM"]}\n'
             f'Edlevel:    {c["EDLEVEL"]}\n')

        self._w.set_text(s)

class App(object):
    def unhandled_input(self, key):
        if key in ('esc',):
            raise u.ExitMainLoop()

    def show_details(self, employee):
        self.detail_view.set_employee(employee)

    def __init__(self):
        self.palette = {
            ("bg",                "black",       "white"),
            ("employee",          "black",       "white"),
            ("employee_selected", "black",       "yellow"),
            ("footer",            "white, bold", "dark red")
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
        """Attempt to establish a connection to the DB2 database with retry logic."""
        from getpass import getpass

        max_attempts = 3
        attempts = 0

        database = 'SAMPLE'
        hostname = 'odin.local'
        port = '25000'
        userid = 'db2inst1'

        while attempts < max_attempts:
            password = getpass("Enter password: ")

            conn_str = (
                f"DATABASE={database};"
                f"HOSTNAME={hostname};"
                f"PORT={port};"
                f"PROTOCOL=TCPIP;"
                f"UID={userid};"
                f"PWD={password};"
            )

            try:
                conn = ibm_db.connect(conn_str, '', '')
                print("Connected successfully!")
                return conn  # Return the connection on success

            except Exception as e:
                error_message = ibm_db.conn_errormsg()
                error_code = ibm_db.conn_error()
                sqlcode = self.get_sqlcode_from_error(error_message)

                print(f"\nConnection failed with error code = {error_code} SQLCODE = {sqlcode}:\n{error_message}\nException: {e}\n")

                if error_code == "08001":
                    attempts += 1
                    if attempts < max_attempts:
                        print(f"Invalid credentials. You have {max_attempts - attempts} attempts left.\n")
                    else:
                        print("Too many failed attempts. Exiting.")
                        exit(1)
                else:
                    print(f"\nConnection failed with error code = {error_code} SQLCODE = {sqlcode}:\n{error_message}\nException: {e}\n")
                    exit(1)

        return None  # If the function reaches this point, connection failed.

    def get_sqlcode_from_error(self, error_msg):
        import re
        """Extract SQLCODE from ibm_db connection error message."""
        if not error_msg:
            return None  # No error message means no SQLCODE

        # Regex to match SQLCODE patterns (e.g., SQL30082N)
        match = re.search(r"SQL(\d{5})N", error_msg)

        if match:
            return int(match.group(1))  # Convert to integer for easy handling
        return None

    def connect_to_db_old(self):
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
                print(f" Borked with: {e}\n Deets: {ibm_db.activeconn_error()}")
                if ibm_db.conn_error() == "08001":
                    attempts += 1
                    if attempts < max_attempts:
                        print (f"Nope. Try again. You have {max_attempts-attempts} attempts left.")
                else:
                    print(f" Borked with: {e} {conn_error()}")
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
