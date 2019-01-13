import os, sys
import asyncio
import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials

class GSheet():
    def __init__(self, target, loop=None):
        self._scope = ['https://spreadsheets.google.com/feeds']

        self.credentials = ServiceAccountCredentials.from_json_keyfile_name('My Project-8455600c0643.json', self._scope)
        self.target = target
        self.load_sheet()
        self.loop = loop

    def load_sheet(self):
        self.gc = gspread.authorize(self.credentials)
        self.sheet = self.gc.open_by_url(self.target)
        self.worksheet = self.sheet.get_worksheet(0)        

    async def error(self):
        return False

    async def insert(self, columns):
        tries = 0
        while tries < 3:
            try:
                # loop until finished
                index = len(self.worksheet.col_values(1))

                ind = index + 1
                abc_list = ['A','B','C','D','E','F','G','H','I','J','K','L', 'M', 'N', 'O', 'P']

                #self.reset()
                tasks = []
                for index_of_col, col in enumerate(columns):
                    if col.startswith('='):
                        col = "'" + col
                        
                    tasks.append(self.loop.run_in_executor(None, self.worksheet.update_cell, ind, index_of_col + 1, col))

                return asyncio.gather(*tasks)
                
            except gspread.exceptions.APIError as e:
                self.load_sheet()
                tries += 1
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print('GAPI', exc_type, fname, exc_tb.tb_lineno)

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                tries += 1

        return self.error()