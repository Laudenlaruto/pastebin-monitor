# Pastebin Crawler for pro user
A simple Pastebin crawler for pastebin pro users! Which looks for interesting things and saves them to disk. 
Originally forked from [https://github.com/FabioSpampinato/Pastebin-Crawler](https://github.com/FabioSpampinato/Pastebin-Crawler)

## Dependencies
* Python 3

## How it works
The tool periodically checks for new pastes using the [scraping api](https://pastebin.com/doc_scraping_api). You will need a pro account to have your IP whitelisted. \
If the pastes match a given pattern, their URL is stored in a .txt file, and their content in a file under a predefined directory. For instance, if the paste matches a password it can be placed in 'passwords.txt' and stored under 'passwords'.
 
 The following parameters are configurable:
 
 * Refresh time (time slept between Pastebin checks, in seconds)
 * Delay (time between sequential accesses to each of Pastebin's pastes, in seconds)
 * Ban wait time (time to wait if a ban is detected, in minutes)
 * Timeout time (time to wait until a new attempt is made if connection times out due to a bad connection, in seconds)
 * Number of refreshes between flushes (number of refreshes until past Pastes are cleared from memory)
 * Limit of pastes to get per fetch
 * The regexes. See [Using your own regexes](#user-content-using-your-own-regexes)

### Recommendation
If you want to follow the guidline from [scraping api](https://pastebin.com/doc_scraping_api). An optimised continuous scrapper would have a refresh of 60 seconde, a delay of 1 seconde and a limit of 100.
```
./pastebin_crawler.py -r 60 -d 1 -l 100    
```
 
## Command line options

```
./pastebin_crawler.py -h
Usage: pastebin_crawler.py [options]

Options:
  -h, --help            show this help message and exit
  -r REFRESH_TIME, --refresh-time=REFRESH_TIME
                        Set the refresh time (default: 30)
  -d DELAY, --delay-time=DELAY
                        Set the delay time (default: 1)
  -b BAN_WAIT, --ban-wait-time=BAN_WAIT
                        Set the ban wait time (default: 5)
  -f FLUSH_AFTER_X_REFRESHES, --flush-after-x-refreshes=FLUSH_AFTER_X_REFRESHES
                        Set the number of refreshes after which memory is
                        flushed (default: 100)
  -c CONNECTION_TIMEOUT, --connection-timeout=CONNECTION_TIMEOUT
                        Set the connection timeout waiting time (default: 60)
  -l LIMIT_OF_PASTES, --limit=HOW_MANY_PASTES_YOU_WANT_TO_GET_PER_FETCH
                        Set the number of pastes to get per fetch (default: 50)
```
 
## Using your own regexes
 Regexes are stored in the _regexes.txt_ file. It is trivial to modify this file and add new patterns to match.
 
 
 The format is:
 
    regex , URL logging file path/name , directory to store pasties
      
Examples:

    (password\b|pass\b|pswd\b|passwd\b|pwd\b|pass\b), passwords.txt, passwords
    (serial\b|cd-key\b|key\b|license\b),              serials.txt,   serials

**And yes, you can use commas in the regex. Just don't do it in filename or directory. Really, _don't_!**