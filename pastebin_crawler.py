#!/usr/bin/env python3
from math import ceil
from optparse import OptionParser
import os
import re
import time
import sys
import urllib
import urllib.request
import json
from bs4 import BeautifulSoup


def get_timestamp():
    return time.strftime('%Y/%m/%d %H:%M:%S')

class Logger:

    shell_mod = {
        '':'',
       'PURPLE' : '\033[95m',
       'CYAN' : '\033[96m',
       'DARKCYAN' : '\033[36m',
       'BLUE' : '\033[94m',
       'GREEN' : '\033[92m',
       'YELLOW' : '\033[93m',
       'RED' : '\033[91m',
       'BOLD' : '\033[1m',
       'UNDERLINE' : '\033[4m',
       'RESET' : '\033[0m'
    }

    def log ( self, message, is_bold=False, color='', log_time=True):
        prefix = ''
        suffix = ''

        if log_time:
            prefix += '[{:s}] '.format(get_timestamp())

        if os.name == 'posix':
            if is_bold:
                prefix += self.shell_mod['BOLD']
            prefix += self.shell_mod[color.upper()]

            suffix = self.shell_mod['RESET']

        message = prefix + message + suffix
        print ( message )
        sys.stdout.flush()

    def error(self, err):
        self.log(err, True, 'RED')

    def fatal_error(self, err):
        self.error(err)
        exit()

class Crawler:

    PASTEBIN_URL = 'https://scrape.pastebin.com/api_scrape_item.php?i='
    PASTES_URL = 'https://scrape.pastebin.com/api_scraping.php'
    REGEXES_FILE = 'regexes.txt'
    OK = 1
    ACCESS_DENIED = -1
    CONNECTION_FAIL = -2
    OTHER_ERROR = -3

    prev_checked_ids = []
    new_checked_ids = []

    def read_regexes(self):
        try:
            with open ( self.REGEXES_FILE, 'r') as f:
                try:
                    self.regexes = [ [ field.strip() for field in line.split(',')] for line in f.readlines() if line.strip() != '' and not line.startswith('#')]
                    # In case commas exist in the regexes...merge everything.
                    for i in range(len(self.regexes)):
                        self.regexes[i] = [','.join(self.regexes[i][:-2])] + self.regexes[i][-2:]
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    Logger().error(str(e))
                    Logger().fatal_error('Malformed regexes file. Format: regex_pattern,URL logging file, directory logging file.')
        except KeyboardInterrupt:
            raise
        except Exception as e:
            Logger().error(str(e))
            Logger().fatal_error('{:s} not found or not acessible.'.format(self.REGEXES_FILE))


    def __init__(self):
        self.read_regexes()



    def get_pastes ( self, limit ):
        Logger ().log ( 'Getting pastes', True , 'PURPLE')
        try:
            with urllib.request.urlopen(self.PASTES_URL+'?limit='+str(limit)) as response:
                html = response.read().decode('utf-8')
                if 'DOES NOT HAVE ACCESS' in html:
                    Logger().fatal_error("Your public IP is not whitelisted. Go to https://pastebin.com/doc_scraping_api")
                    return self.CONNECTION_FAIL,None               
                else:
                    pastes = json.loads(html)
                    return self.OK,pastes
        except KeyboardInterrupt:
            raise
        except Exception as e:
            Logger().error("Error getting pastes: " + str(e))
            return self.CONNECTION_FAIL,None

    def check_paste ( self, paste_id ):
        paste_url = self.PASTEBIN_URL + paste_id
        try:
            Logger ().log ( 'Checking paste ' + str(paste_id), True, 'CYAN' )
            with urllib.request.urlopen(paste_url) as response:
                paste_txt = str(BeautifulSoup(response, "lxml"))
                #TODO Check all regex, not only stop at first match
                for regex,file,directory in self.regexes:
                    if re.match ( regex, paste_txt, re.IGNORECASE ):
                        Logger ().log ( 'Found a matching paste: ' + paste_url + ' (' + file + ')', True, 'CYAN' )
                        self.save_result ( paste_txt, paste_url, paste_id, file, directory )
                        return True
        except KeyboardInterrupt:
            raise
        except Exception as e:
            Logger().error("Error on check paste: " + str(e))
            # Logger ().log ( 'Error reading paste (probably a 404 or encoding issue).', True, 'YELLOW')
        return False

    def save_result ( self, paste_txt, paste_url, paste_id, file, directory ):
        timestamp = get_timestamp()
        with open ( file, 'a' ) as matching:
            matching.write ( timestamp + ' - ' + paste_url + '\n' )
        try:
            os.mkdir(directory)
        except KeyboardInterrupt:
            raise
        except:
            pass
        try:
            with open( directory + '/' + timestamp.replace('/','_').replace(':','_').replace(' ','__') + '_' + paste_id.replace('/','') + '.txt', mode='w' ) as paste:
                paste.write(paste_txt + '\n')
        except Exception as e:
            Logger().fatal_error(str(e))



    def start ( self, refresh_time = 30, delay = 1, ban_wait = 0, flush_after_x_refreshes=100, connection_timeout=60, limit=50 ):
        count = 0
        while True:
            status,pastes = self.get_pastes (limit)
            start_time = time.time()
            if status == self.OK:
                Logger ().log ( 'Got '+ str(len(pastes)) +' pastes', True , 'PURPLE')
                read_count=0
                for paste in pastes:
                    paste_id = paste['key']
                    self.new_checked_ids.append ( paste_id )
                    if paste_id not in self.prev_checked_ids:
                        self.check_paste ( paste_id )
                        read_count +=1
                        time.sleep ( delay )
                    count += 1

                if count == flush_after_x_refreshes:
                    self.prev_checked_ids = self.new_checked_ids
                    count = 0
                else:
                    self.prev_checked_ids += self.new_checked_ids
                self.new_checked_ids = []
                Logger ().log ( 'Read ' + str(read_count)    +' pastes', True , 'PURPLE')
                elapsed_time = time.time() - start_time
                Logger().log('Elapsed time: '+ str(elapsed_time), True, 'BLUE')
                sleep_time = ceil(max(0,(refresh_time - elapsed_time)))
                if sleep_time > 0:
                    Logger().log('Waiting {:d} seconds to refresh...'.format(sleep_time), True , 'BLUE')
                    time.sleep ( sleep_time )
            elif status == self.ACCESS_DENIED:
                Logger ().log ( 'Damn! It looks like you have been banned (probably temporarily)', True, 'YELLOW' )
                for n in range ( 0, ban_wait ):
                    Logger ().log ( 'Please wait ' + str ( ban_wait - n ) + ' minute' + ( 's' if ( ban_wait - n ) > 1 else '' ) )
                    time.sleep ( 60 )
            elif status == self.CONNECTION_FAIL:
                Logger().log ( 'Connection down. Waiting {:d} seconds and trying again'.format(connection_timeout), True, 'RED')
                time.sleep(connection_timeout)
            elif status == self.OTHER_ERROR:
                Logger().log( 'Unknown error. Maybe an encoding problem? Trying again.', True,'RED')
                time.sleep(1)

def parse_input():
    parser = OptionParser()
    parser.add_option('-r', '--refresh-time', help='Set the refresh time (default: 30)', dest='refresh_time', type='int', default=30)
    parser.add_option('-d', '--delay-time', help='Set the delay time (default: 1)', dest='delay', type='float', default=1)
    parser.add_option('-b', '--ban-wait-time', help='Set the ban wait time (default: 5)', dest='ban_wait', type='int', default=5)
    parser.add_option('-f', '--flush-after-x-refreshes', help='Set the number of refreshes after which memory is flushed (default: 100)', dest='flush_after_x_refreshes', type='int', default=100)
    parser.add_option('-c', '--connection-timeout', help='Set the connection timeout waiting time (default: 60)', dest='connection_timeout', type='float', default=60)
    parser.add_option('-l','--limit',help='Set the limit of results by fetch (default: 50)',dest='limit' ,type='int',default=50)
    (options, args) = parser.parse_args()
    return options.refresh_time, options.delay, options.ban_wait, options.flush_after_x_refreshes, options.connection_timeout, options.limit


try:
    Crawler ().start (*parse_input())
except KeyboardInterrupt:
    Logger ().log ( 'Bye! Hope you found what you were looking for :)', True )
