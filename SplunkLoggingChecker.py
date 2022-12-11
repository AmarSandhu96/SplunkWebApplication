#!/usr/bin/python3

try: 
    import os
    from flask import Flask, render_template, request
    import urllib
    import httplib2
    import datetime
    from xml.dom import minidom
    import json
    import re
    from key import key2
    from datetime import datetime
    import logging 
    import requests

except ImportError as error:
    date = datetime.now()
    with open('log.txt', 'a') as log:
        log.write(f' {date}:   {error}\n')
        log.close()
        print (f'Error importing necessary imports. {error}')
        exit()
            

app = Flask(__name__)
logging.basicConfig(filename='demo.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

random = []
space = "------------------------------------------------------------------------------------------------"

@app.route('/', methods=['POST'])
def my_form_post():
    
    random.clear()
    baseurl = 'https://localhost:8089'
    userName = 'test'
    password = (key2)
    output = 'json' 

    try:
        hosts = request.form['hosts']
        searchQuery = 'index="data"  host='+hosts+ ' | eval time=strftime(_time,"%m/%d/%y %H:%M:%S") | stats latest(time) as _time by  host index sourcetype'
        length = (len(hosts))
        if length >= 20:
            return render_template('device_not_found.html')
        else:
            pass
    except:
        hostuf = request.form['hostuf']
        searchQuery = ' index=main sourcetype=*  host=' +hostuf+ ' | stats latest(_time) by host index sourcetype _time | dedup host index sourcetype'
        length1 = (len(hostuf))
        if length1 >= 20:
            return render_template('device_not_found.html')
        else:
            pass

    # Authenticate with server.
    # Disable SSL cert validation. Splunk certs are self-signed.
    try:
        serverContent = httplib2.Http(disable_ssl_certificate_validation=True).request(baseurl + '/services/auth/login','POST', headers={}, body=urllib.parse.urlencode({'username':userName, 'password':password}))[1]
    except:
        date = datetime.now()
        app.logger.error('Failure to disable SSL Cert Validation')
        with open('log.txt', 'a') as log:
            log.write(f' {date}:   Failure to disable SSL Cert validation'+'\n')
            log.close()
        return("error in retrieving login.")
    try:
        sessionKey = minidom.parseString(serverContent).getElementsByTagName('sessionKey')[0].childNodes[0].nodeValue
    except:
        date = datetime.now()
        app.logger.error('Failure to retrieve session key ')
        with open('log.txt', 'a') as log:
            log.write(f' {date}:   Failure to retrieve key session'+'\n')
            log.close()
        return("error in retrieving sessionKey")
        return(minidom.parseString(serverContent).toprettyxml(encoding='UTF-8'))

    # Remove leading and trailing whitespace from the search
    searchQuery = searchQuery.strip()

    # If the query doesn't already start with the 'search' operator or another 
    # generating command (e.g. "| inputcsv"), then prepend "search " to it.
    if not (searchQuery.startswith('search') or searchQuery.startswith("|")):
        searchQuery = 'search ' + searchQuery

    # Run the search.
    # Again, disable SSL cert validation. 
    searchResults = httplib2.Http(disable_ssl_certificate_validation=True).request(baseurl + '/services/search/jobs/export?output_mode='+output,'POST',headers={'Authorization': 'Splunk %s' % sessionKey},body=urllib.parse.urlencode({'search': searchQuery}))[1]

    searchResults = searchResults.decode('utf-8')

    #for result in searchResults.splitlines():
    result = searchResults.splitlines()
    result = str(result)
    if result == '  ':
        date = datetime.now()
        app.logger.error("Search results empty. Could be failure to connect to splunk")
        with open('log.txt', 'a') as log:
            log.write(f' {date}:   Search results empty. Could be failure to connect to Splunk'+'\n')
            log.close()

    try:
        json_strings = re.findall(r"\'(\{.+?\}+)\'?", result)
        # for string in json_strings:
        #     print(f"str {string}")

        for string in json_strings:
                # print(string)
                # _json = json.loads('{"example":"this"}')
            _json = json.loads(string)
                # print(_json)
            result = _json["result"]
                # print(result)
            host = result["host"]
            index = result["index"]
            sourcetype = result["sourcetype"]
            time = result["_time"]
         
            host = " [+] Host: " + host 
            index = " [+] Index: " + index 
            sourcetype = " [+] Sourcetype: " + sourcetype 
            time = " [+] Last Logged to Splunk: " + time 
            
            random.append(host)
            random.append(index)
            random.append(sourcetype)
            random.append(time)
            random.append(space)

        app.logger.info(f'User searched for {hosts} and found:\n {host}\n {index}\n {sourcetype}\n {time}\n') # NOTE: app.logger does not find all wildcards.
        return render_template("results.html", theresponse=random)
        

    except Exception as e:
        app.logger.debug(f'{hosts} not found')


@app.errorhandler(404)
def pageNotFound(error):
    return "page not found", 404

@app.errorhandler(500)
def pageNotFound(error):
    return render_template("device_not_found.html"), 500

@app.route('/', methods=['POST', 'GET'])
def home():    
    return render_template('search.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=False)

