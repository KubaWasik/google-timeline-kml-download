import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import os
import re
import winshell
from urllib.parse import quote
from tkinter import Frame, PhotoImage, Label, Entry, Button, messagebox, E, Tk


class GoogleSession:
    '''Class for Google session'''
    def __init__(self, url_login, url_auth, login, password):
        # create request for google auth service
        self.session = requests.session()
        login_html = self.session.get(url_login)
        # search for inputs in login page
        soup_login = BeautifulSoup(login_html.content)\
            .find('form').find_all('input')
        # inject credentials into form
        credentials = {}
        for form_input in soup_login:
            if form_input.has_attr('value'):
                credentials[form_input['name']] = form_input['value']
        credentials['Login'] = login
        credentials['Password'] = password
        # send injected form to google auth service => create session
        self.session.post(url_auth, data=credentials)

    def get(self, url):
        # get response in text format in utf-8 encoding
        response = self.session.get(url)
        response.encoding = 'utf-8'
        response = response.text
        return response


def get_session(login, password):
    # urls for google auth service
    url_login = "https://accounts.google.com/ServiceLogin"
    url_auth = "https://accounts.google.com/ServiceLoginAuth"
    # create session
    session = GoogleSession(url_login, url_auth, login, password)
    # return session object
    return session


def download_kml(year, month, day, period, session):
    start = date(year, month, day)
    end = start + timedelta(days=period)
    number_of_days = end - start
    number_of_days = number_of_days.days
    # download and save kml file for every day in period
    for day in range(0, number_of_days + 1):
        day_date = start + timedelta(days=day)
        kml = session.get('https://www.google.com/maps/timeline/kml?authuser=0\
                          &pb=!1m8!1m3!1i' + str(day_date.year) + '!2i' +
                          str((day_date.month - 1)) + '!3i' +
                          str(day_date.day) + '!2m3!1i' + str(day_date.year)
                          + '!2i' + str((day_date.month-1)) + '!3i' +
                          str((day_date.day) + 1))
        try:
            kml_file = open('location-history-' + str(day_date.year) + '-' +
                            str(day_date.month) + '-' + str(day_date.day) +
                            '.kml', 'w', encoding="utf-8")
            kml_file.write(kml)
        finally:
            kml_file.close()


def read_from_file(year, month, day, period):
    visited = {}
    start = date(year, month, day)
    end = start + timedelta(days=period)
    number_of_days = end - start
    number_of_days = number_of_days.days
    count = 0
    # for every file search with regular expressions for addresses
    for day in range(0, number_of_days + 1):
        day_date = start + timedelta(days=day)
        try:
            kml = open('location-history-' + str(day_date.year) + '-' +
                       str(day_date.month) + '-' + str(day_date.day) + '.kml',
                       'r', encoding="utf-8")
            kml_file = kml.read()
            addresses = re.findall(r'<address>[^<>]+</address>', kml_file)
            # count the addresses
            for address in addresses:
                regex = re.findall(r'(?<=<address>).*(?=</address>)', address)
                regex_count = visited.get(str(regex), 0)
                visited[str(regex)] = regex_count + 1
                count = count + 1
        finally:
            kml.close()
    # if number of addressed found is less than 6 return -1 as error code
    if count < 6:
        return -1
    # else return dict of all visited addresses
    else:
        return visited


def find_max(visited):
    # find and return top 5 visited addresses
    top = {}
    visited_copy = visited.copy()
    for i in range(0, 5):
        keys = list(visited_copy.items())
        max_item = keys[0][0]
        for key in visited_copy:
            if visited_copy[key] > visited_copy[max_item]:
                max_item = key
        top[max_item] = visited[max_item]
        visited_copy.pop(max_item)
    top = list(top.items())
    return top


def create_shotcuts(top_list):
    # create shortcuts on desktop, it will work only on Windows
    desktop = winshell.desktop()
    i = 1
    for elemnt in top_list:
        path = os.path.join(desktop, "Google maps shortcut ("+str(i)+").url")
        shortcut = open(path, 'w')
        shortcut.write('[InternetShortcut]\n')
        address = quote(elemnt[0])
        shortcut.write('URL=http://www.google.com/maps/dir/?api=1&destination='
                       + str(address))
        shortcut.close()
        i = i + 1


def delete_files(year, month, day, period):
    # delete downloaded kml files
    start = date(year, month, day)
    end = start + timedelta(days=period)
    number_of_days = end - start
    number_of_days = number_of_days.days
    for day in range(0, number_of_days + 1):
        day_date = start + timedelta(days=day)
        os.remove('location-history-' + str(day_date.year) + '-' +
                  str(day_date.month) + '-' + str(day_date.day) + '.kml')


class GuiLogin(Frame):
    '''Class for TkInt window for login'''
    def __init__(self, master):
        super().__init__(master)
        # Source: https://pl.wikipedia.org/wiki/Plik:Google_2015_logo.svg
        self.photo = PhotoImage(file="Google_2015_logo.png")
        self.label_0 = Label(image=self.photo)
        self.label_0.image = self.photo
        self.label_0.pack(pady=(100, 50))

        self.label_1 = Label(self, text="Login")
        self.label_2 = Label(self, text="Password")

        self.entry_1 = Entry(self, width=30)
        self.entry_2 = Entry(self, show="*", width=30)

        self.label_1.grid(row=0, sticky=E, padx=(10, 10), pady=(10, 10))
        self.label_2.grid(row=1, sticky=E, padx=(10, 10), pady=(10, 10))
        self.entry_1.grid(row=0, column=1, padx=(10, 10), pady=(10, 10))
        self.entry_2.grid(row=1, column=1, padx=(10, 10), pady=(10, 10))

        self.logbtn = Button(self, text="Login", command=self._login)
        self.logbtn.grid(columnspan=2)

        self.entry_1.focus()
        self.pack()

    def _login(self):
        global username
        username = self.entry_1.get()
        global password
        password = self.entry_2.get()
        global session
        session = get_session(username, password)
        GuiResults(root)
        self.destroy()
        messagebox.showinfo(message='Logged in, choose period of time')


class GuiResults(Frame):
    '''Class for TkInt window for choosing period of time
        and downloading result'''
    def __init__(self, master):
        super().__init__(master)

        self.label_1 = Label(self, text="Start date in format rrrr-mm-dd")
        self.label_2 = Label(self, text="Number of days (min. 5)")
        self.label_1_1 = Label(self, text=" - ")
        self.label_1_2 = Label(self, text=" - ")

        self.entry_1_1 = Entry(self, width=4)
        self.entry_1_2 = Entry(self, width=2)
        self.entry_1_3 = Entry(self, width=2)
        self.entry_2 = Entry(self, width=4)

        self.label_1.grid(row=0, sticky=E, pady=(10, 10))
        self.label_2.grid(row=1, sticky=E, pady=(10, 10))
        self.label_1_1.grid(row=0, column=2)
        self.label_1_2.grid(row=0, column=4)
        self.entry_1_1.grid(row=0, column=1, padx=(10, 0), pady=(10, 10))
        self.entry_1_2.grid(row=0, column=3, pady=(10, 10))
        self.entry_1_3.grid(row=0, column=5, pady=(10, 10))
        self.entry_2.grid(row=1, column=1, padx=(10, 0), pady=(10, 10))

        self.dlbtn = Button(self, text="Download and create shortcuts",
                            command=self._download)
        self.dlbtn.grid(columnspan=6)

        self.entry_1_1.focus()
        self.pack()

    def _download(self):
        global date_year
        global date_month
        global date_day
        date_year = self.entry_1_1.get()
        date_month = self.entry_1_2.get()
        date_day = self.entry_1_3.get()
        global number_of_days
        number_of_days = self.entry_2.get()
        # create kml folder if it not exist
        if (os.path.isdir("kml")):
            os.chdir('kml/')
        else:
            os.mkdir("kml")
            os.chdir("kml/")
        download_kml(int(date_year), int(date_month), int(date_day),
                     int(number_of_days), session)
        visited = read_from_file(int(date_year), int(date_month),
                                 int(date_day), int(number_of_days))
        if visited == -1:
            messagebox.showinfo(message='Error: No account activity!')
            root.destroy()
            delete_files(int(date_year), int(date_month), int(date_day),
                         int(number_of_days))
            return
        top_5 = find_max(visited)
        create_shotcuts(top_5)
        delete_files(int(date_year), int(date_month), int(date_day),
                     int(number_of_days))
        messagebox.showinfo(message='Shortcuts have been created on desktop')
        root.destroy()


def _gui():
    global root
    root = Tk()
    root.title("Google timeline download")
    root.geometry('600x500')
    GuiLogin(root)
    root.mainloop()


if __name__ == "__main__":
    _gui()
