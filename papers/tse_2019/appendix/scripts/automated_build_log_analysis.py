#==================================
import csv
import sys
import os
import re
import time
import tqdm
from os import listdir, path

#==============================================================================================================
def extended_message_search(pattern, text):
    pattern = pattern.lower()
    text = text.lower()
    strings = pattern.split('(.*)')
    return text.find(strings[1],text.find(strings[0])) >= 0

#==============================================================================================================
def eliminate_unwanted_characters(text):
	return (text.replace("(B","").replace("[m","").replace("[90m","").replace("[40m","").replace("[1A","")
            .replace("[1m","").replace("[0K","").replace("[K","").replace("[34m","").replace("[9C","").replace("[1;39m","")
            .replace("[35m","").replace("[36m","").replace("[39m","").replace("[m","").replace("[5C","").replace("[4;31m","")
            .replace("[33m","").replace("[37m","").replace("[32m","").replace("[32D","").replace("[0m","").replace("[1;33m","")
            .replace("[31m","").replace("[K","").replace("[31;1m","").replace("[22m","").replace("[9D",""))

#==============================================================================================================
def automated_log_analysis():
    global error_msgs_with_last_lines      
    global error_msgs_with_frequency       
    global error_msgs_per_project_frequency
    global error_unknown_patterns_per_project
    global error_msgs_with_log_ids         
    global csvfile_msgs                    
    global csvfile_unknown_patterns_per_project                   
    global csvwriter_msgs                  
    global csvfile_msgs_per_project        
    global csvwriter_msgs_per_project      
    global csvfile_unknown_patterns_per_project                   
    global csvwriter_unknown_patterns_per_project      
    global csvfile_valid_logs_per_project      
    global csvwriter_valid_logs_per_project      
    global csvwriter_jobs_labeling      
    global csvfile_jobs_labeling
    global valid_files
    global developer_breakages
    global developer_breakages_found_patterns
    global finished_projects

    error_msgs_with_last_lines             = dict()
    error_msgs_with_frequency              = dict()
    error_msgs_per_project_frequency       = dict()
    error_unknown_patterns_per_project     = dict()
    error_msgs_with_log_ids                = dict()
    csvfile_msgs                           = open('results/log_messages_all--.csv', 'a', newline='', encoding="utf8")
    csvfile_msgs_per_project               = open('results/log_messages_per_project--.csv', 'a', newline='', encoding="utf8")
    csvfile_unknown_patterns_per_project   = open('results/log_unknown_error_messages--.csv', 'a', newline='', encoding="utf8")
    csvfile_valid_logs_per_project         = open('results/valid_files_per_project--.csv', 'a', newline='', encoding="utf8")
    csvfile_jobs_labeling                  = open('results/build_jobs_breakage_categories_and_labels--.csv', 'a', newline='', encoding="utf8")
    csvwriter_msgs                         = csv.writer(csvfile_msgs)
    csvwriter_msgs_per_project             = csv.writer(csvfile_msgs_per_project)
    csvwriter_unknown_patterns_per_project = csv.writer(csvfile_unknown_patterns_per_project)
    csvwriter_valid_logs_per_project       = csv.writer(csvfile_valid_logs_per_project)
    csvwriter_jobs_labeling                = csv.writer(csvfile_jobs_labeling)
    valid_files                            = 0
    developer_breakages                    = 0
    developer_breakages_found_patterns     = 0
    finished_projects                      = 0

    csvwriter_msgs.writerow(["breakage_message", "frequency", "sample_log_files", "sample_last_10_lines"])
    csvwriter_msgs_per_project.writerow(["gh_project_name", "breakage_message", "frequency"])
    csvwriter_jobs_labeling.writerow(["gh_project_name", "build_id", "job_num", "job_label", 
                                      "no_of_developer_error_msgs", "breakage_messages", 
                                      "category", "sub_category", "examples"])

    csvwriter_valid_logs_per_project.writerow(["gh_project_name", "valid_logs", "developer_breakages", 
                                               "developer_breakage_found_patterns", "pattern_identification_ratio",
                                               "environmental_breakages", "suspicious_breakages", "unknown_breakages", 
                                               "environmental%", "environmental+suspicious%"])
    csvfile_msgs.flush()
    csvfile_msgs_per_project.flush()
    csvfile_jobs_labeling.flush()
    csvfile_valid_logs_per_project.flush()
    projects_names = []
    logs_dir = "dataset/build_logs"
    dir_lis = listdir(logs_dir)
    i = 0
    for project_name in dir_lis:
        if path.isdir(logs_dir + "/" + project_name):
            i += 1
            identify_breakage_causes(logs_dir, project_name, i)

    print("---------------------------")
    csvfile_msgs.close()
    csvfile_msgs_per_project.close()
    csvfile_valid_logs_per_project.close()
    csvfile_jobs_labeling.close()
    csvfile_unknown_patterns_per_project.close()

#==============================================================================================================
def identify_breakage_causes(logs_dir, project_name, i):
    global error_msgs_with_last_lines
    global error_msgs_with_frequency
    global error_msgs_per_project_frequency
    global error_unknown_patterns_per_project
    global error_msgs_with_log_ids
    global csvfile_msgs
    global csvfile_unknown_patterns_per_project
    global csvwriter_msgs
    global csvfile_msgs_per_project
    global csvwriter_msgs_per_project
    global csvwriter_unknown_patterns_per_project
    global csvfile_valid_logs_per_project
    global csvwriter_valid_logs_per_project
    global csvwriter_jobs_labeling
    global csvfile_jobs_labeling
    global developer_breakages
    global developer_breakages_found_patterns
    global finished_projects
    global valid_files

    project_path = logs_dir  + "/" + project_name
    valid_logs_per_project = 0
    developer_breakages_per_project = 0
    developer_breakages_found_patterns_per_project = 0
    developer_breakages_unknown_patterns_per_project = 0
    environmental_breakages_per_project = 0
    suspicious_breakages_per_project = 0
    unknown_breakages_per_project = 0
    project_display_name = (str(i)+":"+project_name)

    for build_id in tqdm.tqdm(listdir(project_path), ascii=False, ncols=100, 
                              desc=("["+'{0: <40}'.format(project_display_name)+"]")):
        build_path = project_path + "/" + build_id
        log_files = listdir(build_path)
        build_total_num_broken_jobs = len(log_files)
        build_num_truly_broken_jobs = 0
        build_num_environmental_breakage_jobs = 0
        build_num_suspiciously_broken_jobs = 0
        build_num_unknown_breakage_jobs = 0
        build_label = ""
        
        for log_name in log_files:
            job_num      = log_name[(log_name.index('-')+1):(log_name.index('.txt'))]
            log_path     = build_path + "/" + log_name

            key          = ""
            key2         = ""
            category     = ""
            sub_category = ""
            examples     = []
            value        = ""
            job_label    = ""
            valid_files += 1
            no_of_error_msgs = 0
            error_messages = ""
            valid_logs_per_project += 1
            if os.stat(log_path).st_size == 0:
                key = "[SUSPICIOUS BREAKAGE] Empty log."
                category = "01-Internal CI issues"
                sub_category = "01.12-Empty log"
                examples = []
            else:
                logfile = open(log_path, 'r', encoding="utf8")
                loglines = logfile.readlines()
                logfile.seek(0)
                log_content = logfile.read()
                log_content = eliminate_unwanted_characters(log_content)
                log_content = re.sub('travis_time:end(.*)','', log_content)
                log_content = re.sub('travis_time:start(.*)','', log_content)
                logfile.close()
                loglines.reverse()
                all_lines = '\r\n'.join(loglines)
                all_lines = eliminate_unwanted_characters(all_lines)
                all_lines = re.sub('travis_time:end(.*)','', all_lines)
                all_lines = re.sub('travis_time:start(.*)','', all_lines)
                replaced_all_lines = all_lines.replace('[','').replace(']','').replace('(','').replace(')','')
                if len(loglines) > 0:
                    i                   = 0
                    found_msg           = 0
                    before_last_line    = ""
                    before_last_2_lines = ""
                    last_line           = ""
                    last_lines           = ""
                    breaking_msg1       = ""
                    breaking_msg2       = ""
                    is_before_2_lasts   = True
                    is_before_last      = True
                    is_last             = True
                    for line in loglines:
                        line = line.strip()
                        line = eliminate_unwanted_characters(line)
                        original_line = line
                        line = re.sub(r'"(.*)"',        '(.*)', line)
                        line = re.sub(r'\[(.*)\]',      '(.*)', line)
                        line = re.sub(r'\((.*)\)',      '(.*)', line)
                        line = re.sub(r'/(.*):in',      '(.*)', line)
                        line = re.sub(r'/home(.*):',    '(.*)', line)
                        line = re.sub(r'http://.*\s+',  '(.*)', line)
                        line = re.sub(r'https://.*\s+', '(.*)', line)

                        if line and not line.startswith("https://travis-ci.org/"):
                            if ("ERROR".lower()      in line.lower() or 
                                "FATAL".lower()      in line.lower() or 
                                "FAILED".lower()     in line.lower() or 
                                "FAILURE".lower()    in line.lower() or 
                                "CRASH".lower()      in line.lower() or 
                                "EXCEPTION".lower()  in line.lower() or 
                                "ABORTED".lower()    in line.lower() or 
                                "KILLED".lower()     in line.lower() or 
                                "FAULT".lower()      in line.lower() or
                                "NOT FOUND".lower()  in line.lower()
                                ):
                                found_msg += 1
                                if found_msg == 1:
                                    breaking_msg1 = line.encode('ascii', 'ignore').decode(sys.stdout.encoding)
                                elif found_msg == 2:
                                    breaking_msg2 = line.encode('ascii', 'ignore').decode(sys.stdout.encoding)

                            if is_last:
                                last_line = original_line
                                is_last = False
                            elif is_before_last:
                                before_last_line = original_line
                                is_before_last = False
                            elif is_before_2_lasts:
                                before_last_2_lines = original_line
                                is_before_2_lasts = False
                            
                            if i < 30:
                                i += 1
                                last_lines = original_line + last_lines                            
                            else:
                                break
                    
                    value = last_lines.encode('ascii', 'ignore').decode(sys.stdout.encoding)

                    if "No output has been received in the last" in all_lines: 
                        key = "[ENVIRONMENTAL BREAKAGE] No output has been received in the last"
                        category = "02-Exceeding limits"
                        sub_category = "02.01-Stalled build (not response)"
                        examples = ["No output has been received in the last"]
                    elif ("job exceeded the maxmimum time limit for jobs" in all_lines 
                       or "job exceeded the maximum time limit for jobs" in all_lines 
                       or extended_message_search("specified wait_for timeout(.*)was exceeded", all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] The job exceeded the maximum time limit for jobs"
                        category = "02-Exceeding limits"
                        sub_category = "02.06-Job runtime limit"
                        examples = ["job exceeded the maxmimum time limit for jobs", 
                                    "job exceeded the maximum time limit for jobs", 
                                    "specified wait_for timeout was exceeded"]
                    elif "Timed out waiting for response" in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] Timed out waiting for response"
                        category = "02-Exceeding limits"
                        sub_category = "02.05-Time limit waiting for response"
                        examples = ["Timed out waiting for response"]
                    elif ((extended_message_search('The command(.*)exited with 127', all_lines)
                           or "Command failed with status (127)" in all_lines)
                        and  ("The program 'bundle' is currently not installed" in all_lines 
                           or "ERROR: Gem bundler is not installed" in all_lines
                           or "bundle: command not found" in all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] The command(.*)exited with 127"
                        category = "04-Ruby & bundler issues"
                        sub_category = "04.06-Bundler not installed"
                        examples = ["The command xyz exited with 127",
                                    "Command failed with status (127)"]
                    elif extended_message_search('The command(.*)exited with 6', value):
                        key = "[ENVIRONMENTAL BREAKAGE] The command(.*)exited with 6"
                        category = "04-Ruby & bundler issues"
                        sub_category = "04.01-No compatible gem versions"
                        examples = ["The command xyz exited with 6"]
                    elif extended_message_search('Trying to register Bundler::(.*)is already registered', all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] Trying to register Bundler::(.*)is already registered" 
                        category = "04-Ruby & bundler issues"
                        sub_category = "04.07-Registration problems"
                        examples = ["Trying to register Bundler::(.*)is already registered"]
                    elif (extended_message_search('ERROR:  While executing gem(.*)(Errno::ENOENT)', all_lines) 
                      or ('Errno::ENOENT: No such file or directory' in all_lines 
					      and 'an unexpected error occurred, and Bundler cannot continue' in all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] Errno::ENOENT: No such file or directory"
                        category = "04-Ruby & bundler issues" 
                        sub_category = "04.02-Cannot find, parse, execute gems"
                        examples = ["ERROR:  While executing gem(.*)(Errno::ENOENT)", 
                                    "Errno::ENOENT: No such file or directory",
                                    "an unexpected error occurred, and Bundler cannot continue"]
                    elif ('Bundler::GemfileError: There was an error in your Gemfile' in value
                      or extended_message_search('There was an error in your Gemfile(.*)(Bundler::GemfileError)', value)
                      or extended_message_search('There was an error parsing(.*)Bundler cannot continue', value)):
                        key = "[ENVIRONMENTAL BREAKAGE] ERROR:  While executing gem -or- error parsing" 
                        category = "04-Ruby & bundler issues"
                        sub_category = "04.02-Cannot find, parse, execute gems"
                        examples = ["Bundler::GemfileError: There was an error in your Gemfile", 
                                    "There was an error parsing(.*)Bundler cannot continue"]
                    elif (extended_message_search('The command(.*)exited with 7', value)
                      or extended_message_search("Could not find a valid gem(.*), here is why", all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] The command(.*)exited with 7"
                        category = "04-Ruby & bundler issues"
                        sub_category = "04.02-Cannot find, parse, execute gems"
                        examples = ["The command xyz exited with 7",
                                    "Could not find a valid gem(.*), here is why"]
                    elif ("Error Bundler::HTTPError during request to dependency API" in all_lines
                      or  'Bundler could not find compatible versions for' in value):
                        key = "[ENVIRONMENTAL BREAKAGE] Error Bundler::HTTPError during request to dependency API"
                        category = "04-Ruby & bundler issues"
                        sub_category = "04.05-Dependency request error"
                        examples = ["Error Bundler::HTTPError during request to dependency API",
                                    "Bundler could not find compatible versions for gem"]
                    elif 'bundle: not found' in value:
                        key = "[ENVIRONMENTAL BREAKAGE] bundler: not found"
                        category = "04-Ruby & bundler issues"
                        sub_category = "04.06-Bundler not installed"
                        examples = ["bundle: not found"]
                    elif ('LoadError: cannot load such file -- bundler/dep_proxy' in all_lines
                      or 'bundler: failed to load command: rake' in all_lines
                      or extended_message_search(': cannot load such file(.*)(LoadError)', all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] bundler: failed to load command"
                        category = "04-Ruby & bundler issues"
                        sub_category = "04.03-Command loading failure"
                        examples = ["bundler: failed to load command -- bundler/dep_proxy",
                                    "bundler: failed to load command: rake",
                                    "cannot load such file(.*)(LoadError)"]
                    elif (extended_message_search('The command(.*)exited with 8', all_lines)
                      or 'ERROR 404: Not Found' in all_lines
                      or 'Received status code 500 from server: Internal Server Error' in all_lines
                      or 'Received status code 502 from server: Proxy Error' in all_lines
                      or 'Received status code 503 from server: Service Temporarily Unavailable' in all_lines
                      or 'Received status code 503 from server: backend read error' in all_lines
                      or 'ERROR: 404 Not Found'.lower() in all_lines.lower()
                      or 'Error: 404 Client Error' in all_lines
                      or 'ERROR 503: Service Unavailable' in all_lines
                      or 'ERROR: 503 Service Unavailable'.lower() in all_lines.lower()
                      or 'Error: 503 Server Error' in all_lines
                      or "Return code is: 503 , ReasonPhrase:Service Unavailable" in all_lines
                      or "Return code is: 503 , ReasonPhrase:Service Temporarily Unavailable" in all_lines
                      or extended_message_search('The TCP/IP connection to the host (.*) failed', all_lines)
                      or "bad response Service Unavailable 503" in all_lines
                      or ("ERROR:  While executing gem" in all_lines
                          and "Errno::EHOSTUNREACH: No route to host - connect(2)" in all_lines)
                      or extended_message_search(" Server not available (.*) (response code 404)", all_lines)
                      or "ERROR: #<Net::HTTPBadRequest 400 Bad Request readbody=false>" in value
                      or "Error: (Response code was not 200 , but 404.)" in all_lines
                      or re.search("Could not download(.*)Got error code (520|522|524|400) from the server", all_lines)
                      or ("Gem::RemoteFetcher::FetchError" in all_lines
                          and "bad response Not Found 404" in all_lines)
                      or ("bad response Service Unavailable: Back-end server is at capacity 503" in all_lines
                          and (all_lines.rfind("bad response Service Unavailable: Back-end server is at capacity 503")
                                  > all_lines.rfind("failed. Retrying, 3 of 3")))
                      or 'error: The requested URL returned error: 403' in all_lines
                      or 'Server returned HTTP response code: 403' in all_lines
                      or 'Server returned HTTP response code: 403' in all_lines
                      or 'Server returned HTTP response code: 503' in all_lines
                      or 'error: The requested URL returned error: 504' in all_lines
                      or '(22) The requested URL returned error: 410' in all_lines
                      or "(22) The requested URL returned error: 404" in all_lines
                      or "Received status code 403 from server: Forbidden" in all_lines
                      or "HTTPError: 403 Forbidden" in all_lines
                      or "HTTP Error 403: Forbidden" in all_lines
                      or "SERVER ERROR: Backend is unhealthy url" in all_lines
                      or extended_message_search('The command(.*)exited with 135', all_lines)
                      or re.search('\[ERROR\] (.*) Cannot access(.*)in offline mode', all_lines)
                      or "': Failed to open TCP connection to localhost" in all_lines
                      or "ConnectionError: Failed to establish connection for" in all_lines
                      or re.search('The command(.*)exited with 100', all_lines)
                      or (all_lines.find('Service Temporarily Unavailable') == all_lines.find('503')+5)
                      or (all_lines.find('Service Temporarily Unavailable') == all_lines.find('503')+4)):
                        key = "[ENVIRONMENTAL BREAKAGE] The command(.*)exited with 8 -- 404 Not Found"
                        category = "03-Connection issues"
                        sub_category = "03.04-Server or service unavailable"
                        examples = ["The command xyz exited with 8",
                                    "ERROR 404: Not Found", "Error: 404 Client Error",
                                    "Return code is: 503", "ERROR 503: Service Unavailable",
                                    "Error: 503 Server Error",
                                    "Received status code 503 from server: Service Temporarily Unavailable",
                                    "Received status code 502 from server: Proxy Error",
                                    "Received status code 500 from server: Internal Server Error",
                                    "Received status code 503 from server: backend read error",
                                    "bad response Not Found 404",
                                    "No route to host",
                                    "HTTPError: 403 Forbidden",
                                    "HTTP Error 403: Forbidden",
                                    "SERVER ERROR: Backend is unhealthy",
                                    "Back-end server is at capacity 503",
                                    "not download xyz Got error code (520|522|524|400) from the server",
                                    "The TCP/IP connection to the host (.*) failed",
                                    "Failed to open TCP connection to localhost",
                                    "ConnectionError: Failed to establish connection for URL",
                                    "The command(.*)exited with 100"]
                    elif ("bad response Connection refused 503" in all_lines
                      or extended_message_search('The authenticity of host (.*) can\'t be established', all_lines)
                      or ('Could not resolve all dependencies for configuration' in all_lines
                           and (extended_message_search('Connection to(.*)refused', all_lines) or 'Could not download artifact' in all_lines or 'The target server failed to respond' in all_lines))
                      or 'failed: Connection refused' in all_lines
                      or 'ConnectException: Connection refused' in all_lines
                      or 'Error running command: Server refused connection' in all_lines
                      or 'Errno::ECONNREFUSED: Connection refused' in all_lines
                      or "psql: could not connect to server: Connection refused" in all_lines
                      or extended_message_search('Error connecting to (.*) (ECONNREFUSED)', all_lines)
                      or re.search('ERROR(.*)Error reading from url(.*)Connection refused', all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] Connection refused"
                        category = "03-Connection issues"
                        sub_category = "03.05-Connection refused, reset, closed"
                        examples = ["bad response Connection refused 503",
                                    "failed: Connection refused",
                                    "Error reading from url (.*) Connection refused",
                                    "ConnectException: Connection refused",
                                    "The authenticity of host (.*) can\'t be established",
                                    "Error connecting to (.*) (ECONNREFUSED)",
                                    "Connection to URL refused"]
                    elif extended_message_search('The command(.*)exited with 22', all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] The command(.*)exited with 22"
                        category = "01-Internal CI issues"
                        sub_category = "01.13-Caching problems"
                        examples = ["The command xyz exited with 22"]
                    elif (("Gem::RemoteFetcher::FetchError" in all_lines
                           and "bad response Connection timed out 503" in all_lines)
                      or "Specs timed out" in value
                      or "gpg: keyserver timed out" in value
                      or extended_message_search('Failed connect to github.com:(.*); Operation timed out', all_lines)
                      or re.search('RestClient::GatewayTimeout\n504 Gateway Timeout', log_content) or re.search('RestClient::GatewayTimeout\n\n504 Gateway Timeout', log_content)
                      or "failed: Connection timed out" in value
                      or 'fatal: unable to connect a socket (Connection timed out)' in all_lines
                      or "Errno::ETIMEDOUT: Connection timed out" in all_lines
                      or "Connection timed out (Errno::ETIMEDOUT)" in all_lines
                      or ("ERROR: Connection timed out - connect(2)" in all_lines
                           and (all_lines.rfind("ERROR: Connection timed out - connect(2)") 
						          > all_lines.rfind("failed. Retrying, 3 of 3")))
                      or (": Connection timed out - connect(2) (Errno::ETIMEDOUT)" in all_lines
                           and (all_lines.rfind(": Connection timed out - connect(2) (Errno::ETIMEDOUT)") 
						          > all_lines.rfind("failed. Retrying, 3 of 3")))
                      or "Timeout::Error: execution expired" in all_lines
                      or "execution expired (Timeout::Error)" in all_lines
                      or "Timeout::Error (Timeout::Error)" in all_lines
                      or "seconds past (Timeout::Error)" in all_lines
                      or ("RestClient::RequestTimeout" in all_lines
                           and "Request Timeout")):
                        key = "[ENVIRONMENTAL BREAKAGE] Connection timeout"
                        category = "03-Connection issues"
                        sub_category = "03.01-Connection timeout"
                        examples = ["bad response Connection timed out 503",
                                    "keyserver timed out", "failed: Connection timed out",
                                    "fatal: unable to connect a socket (Connection timed out)",
                                    "Errno::ETIMEDOUT: Connection timed out",
                                    "Connection timed out (Errno::ETIMEDOUT)",
                                    "ERROR: Connection timed out - connect(2)",
                                    "RestClient::RequestTimeout",
                                    "Timeout::Error: execution expired",
                                    "execution expired (Timeout::Error)"]
                    elif "The remote end hung up unexpectedly" in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] The remote end hung up unexpectedly"
                        category = "03-Connection issues"
                        sub_category = "03.07-Remote end hung up unexpectedly"
                        examples = ["The remote end hung up unexpectedly"]
                    elif (extended_message_search('request of(.*)failed: Connection reset', all_lines)
                      or ('Could not resolve all dependencies for configuration' in all_lines
                           and 'Connection reset' in all_lines)
                      or extended_message_search('too many connection resets(.*)(Gem::RemoteFetcher::FetchError)', all_lines)
                      or 'Gem::RemoteFetcher::FetchError: too many connection resets' in all_lines
                      or '(Gem::RemoteFetcher::FetchError)(.*)too many connection resets' in all_lines
                      or "Errno::ECONNRESET: Connection reset by peer" in all_lines
                      or "Connection reset by peer (Errno::ECONNRESET)" in all_lines
                      or "[Errno 104] Connection reset by peer" in all_lines
                      or "IOError: Connection reset by peer" in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] request of(.*) failed: Connection reset"
                        category = "03-Connection issues"
                        sub_category = "03.05-Connection refused, reset, closed"
                        examples = ["request of URL failed: Connection reset",
                                    "too many connection resets",
                                    "IOError: Connection reset by peer",
                                    "Connection reset by peer (Errno::ECONNRESET)",
                                    "Errno::ECONNRESET: Connection reset by peer"]
                    elif ("Errno::EPIPE: Broken pipe" in all_lines
                      or  "Broken pipe (Errno::EPIPE)" in all_lines
                      or  "Error: Broken pipe" in all_lines
                      or  "IOError: Broken pipe" in all_lines
                      or  "Connection broken: IncompleteRead(0 bytes read)" in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] Errno::EPIPE: Broken pipe"
                        category = "03-Connection issues"
                        sub_category = "03.02-Broken connection/pipes"
                        examples = ["Errno::EPIPE: Broken pipe",
                                    "Error: Broken pipe",
                                    "IOError: Broken pipe",
                                    "Broken pipe (Errno::EPIPE)",
                                    "Connection broken: IncompleteRead(0 bytes read)"]
                    elif ("Read error: #<IOError: closed stream>" in all_lines
                      or  "....IOError: closed stream" in all_lines
                      or  "PG::Error: connection not open" in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] connection closed or not open"
                        category = "03-Connection issues"
                        sub_category = "03.05-Connection refused, reset, closed"
                        examples = ["IOError: closed stream",
                                    "PG::Error: connection not open"]
                    elif 'fatal: fsync error' in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] fatal: fsync error"
                        category = "03-Connection issues"
                        sub_category = "03.09-Connection, proxy, & sync errors"
                        examples = ["fatal: fsync error"]
                    elif 'Network error while fetching' in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] Network error while fetching"
                        category = "03-Connection issues"
                        sub_category = "03.08-Network transmission error"
                        examples = ["Network error while fetching"]
                    elif ': Unknown host nexus.codehaus.org' in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] Unknown host nexus.codehaus.org"
                        category = "03-Connection issues"
                        sub_category = "03.03-Unknown host"
                        examples = ["Unknown host nexus.codehaus.org"]
                    elif (extended_message_search('FatalError:(.*)Proxy Error', all_lines)
                      or "Errors::ConnectionFailure" in all_lines
                      or extended_message_search('Failed to connect to a master node(.*)ConnectionFailure', all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] Errors::ConnectionFailure"
                        category = "03-Connection issues"
                        sub_category = "03.09-Connection, proxy, & sync errors"
                        examples = ["FatalError: Proxy Error",
                                    "Errors::ConnectionFailure",
                                    "Failed to connect to a master node: ConnectionFailure"]
                    elif (extended_message_search('SSL_connect(.*)(OpenSSL::SSL::SSLError)', all_lines)
                      or re.search('Connecting to(.*)(\r)?\nUnable to establish SSL connection', log_content)
                      or ("ERROR:  While executing gem" in all_lines
                          and "Received fatal alert: bad_record_mac" in all_lines)
                      or "OpenSSL::SSL::SSLError: Received fatal alert: bad_record_mac" in all_lines
                      or re.search('\(OpenSSL::SSL::SSLError\)(\r)?\n(.*)decryption failed or bad record mac', log_content, re.IGNORECASE)):
                        key = "[ENVIRONMENTAL BREAKAGE] SSL_connect(.*)(OpenSSL::SSL::SSLError)"
                        category = "03-Connection issues"
                        sub_category = "03.10-SSL connection error"
                        examples = ["TSSL_connect(.*)(OpenSSL::SSL::SSLError)",
                                    "Connecting to URL Unable to establish SSL connection",
                                    "OpenSSL::SSL::SSLError:",
                                    "Received fatal alert: bad_record_mac",
                                    "decryption failed or bad record mac"]
                    elif extended_message_search('The command(.*)exited with 17', all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] The command(.*)exited with 17 - SSL Certificate"
                        category = "03-Connection issues"
                        sub_category = "03.11-SSL certificate error"
                        examples = ["The command xyz exited with 17"]
                    elif (extended_message_search('OpenSSL::(.*)CipherError:', all_lines)
                      or extended_message_search('Unable to fetch credentuals:(.*)404 Not Found', all_lines)
                      or extended_message_search('Unable to fetch credentials:(.*)404 Not Found', all_lines)
                      or extended_message_search('signatures couldn(.*)t be verified because the public key is not available:', all_lines)):
                        key =  '[ENVIRONMENTAL BREAKAGE] signatures couldn\'t be verified because the public key is not available:'
                        category = "03-Connection issues"
                        sub_category = "03.06-Connection credentials error"
                        examples = ["OpenSSL::(.*)CipherError",
                                    "Unable to fetch credentuals:(.*)404 Not Found",
                                    "signatures couldn(.*)t be verified because the public key is not available"]
                    elif ('fatal: unable to connect to github.com' in all_lines
                      or 'Cannot clone' in all_lines
                      or 'error: Failed connect to github.com' in all_lines
                      or re.search('fatal: unable to access(.*)Could not resolve host: github.com', all_lines)
                      or 'fatal: Unable to look up github.com' in all_lines
                      or 'fatal: Could not read from remote repository' in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] fatal: unable to connect to github.com"
                        category = "01-Internal CI issues"
                        sub_category = "01.11-Cannot access GitHub"
                        examples = ["fatal: unable to connect to github.com",
                                    "Cannot clone",
                                    "error: Failed connect to github.com",
                                    "fatal: Could not read from remote repository"]
                    elif (("Failed to execute git clone" in all_lines
                            and "[RuntimeException]" in all_lines)
                      or extended_message_search('Git error: command(.*)failed', all_lines)
                      or "Git error: command `git clone" in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] Cannot execute git command"
                        category = "01-Internal CI issues"
                        sub_category = "01.07-Cannot execute git command"
                        examples = ["Failed to execute git clone",
                                    "Git error: command(.*)failed",
                                    "Git error: command `git clone"]
                    elif (extended_message_search('The command(.*)exited with 128', all_lines)
                      or 'fatal: reference is not a tree' in all_lines
                      or 'fatal: Remote branch not found in upstream origin' in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] The command exited with 128"
                        category = "01-Internal CI issues"
                        sub_category = "01.01-Unidentified branch/tree/commit"
                        examples = ["The command xyz exited with 128",
                                    "fatal: reference is not a tree",
                                    "fatal: Remote branch not found in upstream origin"]
                    elif 'remote: aborting due to possible repository corruption' in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] remote: aborting due to possible repository corruption"
                        category = "01-Internal CI issues"
                        sub_category = "01.15-Remote repository corruption"
                        examples = ["remote: aborting due to possible repository corruption"]
                    elif (extended_message_search('The command(.*)exited with 134', all_lines)
                      or "Command failed with status (134)" in all_lines
                      or extended_message_search("make[1]: (.*) Error 134", all_lines)
                      or 'Invalid handle usage detected' in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] The command(.*)exited with 134 - core dump"
                        category = "05-Memory & disk issues"
                        sub_category = "05.02-Core dump problems"
                        examples = ["The command xyz exited with 134",
                                    "Command failed with status (134)",
                                    "make[1]: xyz Error 134",
                                    "Invalid handle usage detected"]
                    elif (extended_message_search('The command(.*)exited with 137', all_lines)
                      or extended_message_search('Process(.*)finished with non-zero exit value 137', all_lines)
                      or 'Command failed with status (137)' in all_lines
                      or "java.lang.OutOfMemoryError: unable to create new native thread" in all_lines
                      or extended_message_search("internal implementation error(.*)OutOfMemoryError GC overhead limit exceeded", all_lines)
                      or "java.lang.OutOfMemoryError: Java heap space" in all_lines
                      or extended_message_search("Error: Your application exhausted (.*) area of the heap", all_lines)
                      or extended_message_search("Cannot run program(.*)Cannot allocate memory",all_lines)
                      or '# There is insufficient memory for the Java Runtime Environment to continue' in all_lines
                      or "Error: Your application used more memory than the safety cap of" in all_lines
                      or "java.lang.OutOfMemoryError: GC overhead limit exceeded" in all_lines
                      or (extended_message_search("ERROR:  While executing gem(.*):BufError",all_lines) and 'buffer error' in all_lines)
                      or "Java::JavaLang::OutOfMemoryError: GC overhead limit exceeded" in all_lines
                      or ("[heap]" in all_lines
                          and "Command failed with status ()" in all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] The command(.*)exited with 137"
                        category = "05-Memory & disk issues"
                        sub_category = "05.01-Out of memory/disk space"
                        examples = ["The command xyz exited with 137",
                                    "Process(.*)finished with non-zero exit value 137",
                                    "Command failed with status (137)",
                                    "Command failed with status ()",
                                    "Java::JavaLang::OutOfMemoryError: GC overhead limit exceeded",
                                    "java.lang.OutOfMemoryError: Java heap space",
                                    "Java::JavaLang::OutOfMemoryError: Java heap space",
                                    "Error: Your application exhausted xyz area of the heap",
                                    "Cannot run program xyz Cannot allocate memory",
                                    "ERROR:  While executing gem BufError - buffer error",
                                    "There is insufficient memory for the Java Runtime Environment to continue",
                                    "Error: Your application used more memory than the safety cap"]
                    elif ("java.io.IOException: No space left on device" in all_lines
                      or extended_message_search(": Problem creating(.*): No space left on device", all_lines)
                      or extended_message_search("fatal: could not create(.*)No space left on device", all_lines)
                      or "due to No space left on device" in all_lines
                      or re.search('rake aborted!((\r)?\n)*No space left on device - write', log_content)):
                        key = "[ENVIRONMENTAL BREAKAGE] No space left on device"
                        category = "05-Memory & disk issues"
                        sub_category = "05.01-Out of memory/disk space"
                        examples = ["java.io.IOException: No space left on device",
                                    "Problem creating (.*): No space left on device",
                                    "due to No space left on device",
                                    "fatal: could not create xyz: No space left on device",
                                    "rake aborted! No space left on device - write"]
                    elif (extended_message_search('The command(.*)exited with 139', value)
                      or ("[BUG] Segmentation fault" in all_lines
                          and ("rake aborted!" in all_lines
                                 or "Aborted" in all_lines
                                 or extended_message_search('Thread (.*) crashed', all_lines)))
                      or ("[coverage] Segmentation fault: 11" in all_lines)
                      or ("[coverage] Abort trap: 6" in all_lines)
                      or ("Exception Type:  EXC_CRASH (SIGABRT)" in all_lines)
                      or ("Segmentation fault" in all_lines
                          and "Failed to write core dump" in all_lines)
                      or ("Segmentation fault" in all_lines
                          and "Internal Error" in all_lines)
                      or ("fatal error has been detected" in all_lines
                          and "Failed to write core dump" in all_lines)
                      or ('Error: signal SIGSEGV' in all_lines)
                      or ('fatal error has been detected' in all_lines
                          and 'SIGSEGV' in all_lines)
                      or "Command failed with status (139)" in all_lines
                      or "Segmentation fault" in value):
                        key = "[ENVIRONMENTAL BREAKAGE] The command(.*)exited with 139 - Segmentation fault"
                        category = "05-Memory & disk issues"
                        sub_category = "05.03-Segmentation fault"
                        examples = ["The command xyz exited with 139",
                                    "[BUG] Segmentation fault",
                                    "Error: signal SIGSEGV",
                                    "SIGSEGV",
                                    "Segmentation fault: 11",
                                    "Abort trap: 6",
                                    "Exception Type:  EXC_CRASH (SIGABRT)",
                                    "Segmentation fault -- Internal Error",
                                    "Command failed with status (139)"]
                    elif (extended_message_search('glibc detected(.*)double free or corruption (out)', all_lines)
                      or extended_message_search('glibc detected(.*)corrupted double-linked list', all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] glibc detected(.*)double free or corruption (out)"
                        category = "05-Memory & disk issues"
                        sub_category = "05.05-Corrupted memory references"
                        examples = ["glibc detected(.*)corrupted double-linked list",
                                    "glibc detected(.*)double free or corruption (out)"]
                    elif (extended_message_search('stack level too deep (SystemStackError)(.*)rake aborted!', all_lines)
                      or extended_message_search('rake aborted!(.*)stack level too deep', all_lines)
                      or extended_message_search('SystemStackError: stack level too deep(.*)rake aborted!', all_lines)
                      or extended_message_search('rake aborted!(.*)stack level too deep', all_lines)
                      or re.search('An exception occurred running(.*)(\r)?\n\s*SystemStackError \(SystemStackError\)', log_content)):
                        key = "[ENVIRONMENTAL BREAKAGE] stack level too deep"
                        category = "05-Memory & disk issues"
                        sub_category = "05.04-Memory stack error"
                        examples = ["stack level too deep (SystemStackError)",
                                    "An exception occurred running eyx SystemStackError"]
                    elif extended_message_search('[BUG](.*)called for broken object', all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] [BUG](.*)called for broken object"
                        category = "11-External bugs"
                        sub_category = "11.01-E.g., interpreter bugs"
                        examples = ["[BUG] xyz called for broken object"]
                    elif ("[BUG: Control flow error in interpreter]" in all_lines
                         and "rake aborted!" in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] [BUG: Control flow error in interpreter]"
                        category = "11-External bugs"
                        sub_category = "11.01-E.g., interpreter bugs"
                        examples = ["[BUG: Control flow error in interpreter]"]
                    elif extended_message_search('make: (.*) Abort trap: 6', all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] make: (.*) Abort trap: 6"
                        category = "11-External bugs"
                        sub_category = "11.01-E.g., interpreter bugs"
                        examples = ["make: xyz Abort trap: 6"]
                    elif "[BUG] Uncaught C++ internal exception" in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] [BUG]Uncaught C++ internal exception"
                        category = "11-External bugs"
                        sub_category = "11.01-E.g., interpreter bugs"
                        examples = ["[BUG] Uncaught C++ internal exception"]
                    elif extended_message_search('[BUG](.*)unknown data type', all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] [BUG](.*)unknown data type"
                        category = "11-External bugs"
                        sub_category = "11.01-E.g., interpreter bugs"
                        examples = ["[BUG](.*)unknown data type"]
                    elif (extended_message_search('test run exceeded(.*)minutes', all_lines)
                      or extended_message_search('test run exceeded(.*)seconds', all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] test run exceeded [0-9]+ time"
                        category = "02-Exceeding limits"
                        sub_category = "02.04-Test running limit"
                        examples = ["test run exceeded [0-9]+ minutes", "test run exceeded [0-9]+ seconds"]
                    elif (extended_message_search('running(.*)took longer than', all_lines)
                      or extended_message_search('took longer than(.*)minutes and was terminated', all_lines)
                      or extended_message_search('took longer than(.*)seconds and was terminated', all_lines)
                      or "timed out and was terminated" in all_lines
                      or extended_message_search('xecuting your(.*)took longer than', all_lines)
                      or extended_message_search('timeout of(.*)exceeded', all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] command took longer than"
                        category = "02-Exceeding limits"
                        sub_category = "02.03-Command execution time limit"
                        examples = ["running xyz took longer than",
                                    "xyz took longer than [0-9]+ minutes and was terminated",
                                    "xyz took longer than [0-9]+ seconds and was terminated",
                                    "xyz timed out and was terminated",
                                    "Executing your xyz took longer than",
                                    "timeout of xyz exceeded"]
                    elif "The log length has exceeded the limit" in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] The log length has exceeded the limit"
                        category = "02-Exceeding limits"
                        sub_category = "02.02-Log size limit"
                        examples = ["The log length has exceeded the limit"]
                    elif "error with the connection to the VM" in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] error with the connection to the VM"
                        category = "07-Virtual Machine issues"
                        sub_category = "07.03-VM connection problem"
                        examples = ["error with the connection to the VM"]
                    elif ("ERROR: the VM is exiting improperly" in all_lines
                      or  "failed: The forked VM terminated without properly saying goodbye" in all_lines
                      or  "failed: The forked VM terminated without saying properly goodbye" in all_lines
                      or  "java.lang.RuntimeException: The forked VM terminated without saying properly goodbye" in all_lines
                      or  'VmFatalError: The VM had trouble shutting down and has now been told off' in all_lines
                      or  'Cannot power down a saved virtual machine' in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] ERROR: the VM is exiting improperly"
                        category = "07-Virtual Machine issues"
                        sub_category = "07.01-Improper VM shut down"
                        examples = ["ERROR: the VM is exiting improperly",
                                    "failed: The forked VM terminated without properly saying goodbye"]
                    elif ('Invalid machine state: RestoringSnapshot (must be Running, Paused or Stuck)' in all_lines
                      or  'Invalid machine state: Restoring (must be Running, Paused or Stuck)' in all_lines
                      or extended_message_search('The machine(.*)already locked for a session (or being unlocked)', all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] Invalid machine state: RestoringSnapshot (must be Running, Paused or Stuck)"
                        category = "07-Virtual Machine issues"
                        sub_category = "07.04-Invalid VM state"
                        examples = ["Invalid machine state: RestoringSnapshot (must be Running, Paused or Stuck)",
                                    "Invalid machine state: Restoring (must be Running, Paused or Stuck)",
                                    "The machine(.*)already locked for a session (or being unlocked)"]
                    elif 'the VM stalled during your build and was not recoverable' in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] the VM stalled during your build and was not recoverable"
                        category = "07-Virtual Machine issues"
                        sub_category = "07.05-Stalled VM"
                        examples = ["the VM stalled during your build and was not recoverable"]
                    elif 'Error: Could not create the Java Virtual Machine' in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] Error: Could not create the Java Virtual Machine"
                        category = "07-Virtual Machine issues"
                        sub_category = "07.02-VM creation error"
                        examples = ["Error: Could not create the Java Virtual Machine"]
                    elif 'rate limit exceeded for' in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] rate limit exceeded for (.*)"
                        category = "02-Exceeding limits"
                        sub_category = "02.07-API rate limit"
                        examples = ["rate limit exceeded for xyz"]
                    elif ("killing dying sleeping thread wakes up thread" in all_lines
                      or "fatal: deadlock detected" in value
                      or extended_message_search("ThreadError:(.*)wakeup primitive failed, thread may be dead", all_lines)
                      or extended_message_search('Transaction(.*)deadlocked on lock resources with another process', all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] dying sleeping or deadlock thread"
                        category = "01-Internal CI issues"
                        sub_category = "01.08-Multithreading issues"
                        examples = ["killing dying sleeping thread wakes up thread",
                                    "fatal: deadlock detected",
                                    "ThreadError: xyz wakeup primitive failed, thread may be dead",
                                    "Transaction xyz deadlocked on lock resources with another process"]
                    elif ('error occured while compiling the build script' in all_lines
                      or  'error occurred while compiling the build script' in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] error occurred while compiling the build script"                        
                        category = "01-Internal CI issues"
                        sub_category = "01.10-Script compilation error"
                        examples = ["error occurred while compiling the build script"]
                    elif ('Could not fetch .travis.yml from GitHub' in all_lines
                      or  'Could not find .travis.yml, using standard configuration' in all_lines
                      or  'We were unable to find a .travis.yml file' in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] Could not fetch .travis.yml from GitHub"
                        category = "01-Internal CI issues"
                        sub_category = "01.05-Error fetching CI configuration"
                        examples = ["Could not fetch .travis.yml from GitHub",
                                    "Could not find .travis.yml, using standard configuration",
                                    "We were unable to find a .travis.yml file"]
                    elif ("Errno::EBADF: Bad file descriptor" in all_lines
                      or  "Bad file descriptor (Errno::EBADF)" in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] Errno::EBADF: Bad file descriptor"
                        category = "04-Ruby & bundler issues"
                        sub_category = "04.04-Bad file descriptor"
                        examples = ["Errno::EBADF: Bad file descriptor",
                                    "Bad file descriptor (Errno::EBADF)"]
                    elif ("can't create Thread: Resource temporarily unavailable" in all_lines
                      or "[Errno 11] Resource temporarily unavailable" in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] Resource temporarily unavailable"
                        category = "01-Internal CI issues"
                        sub_category = "01.16-Cannot allocate resources"
                        examples = ["can't create Thread: Resource temporarily unavailable",
                                    "[Errno 11] Resource temporarily unavailable"]
                    elif (re.search("write error:(\s*(\r)?\n\s*)?Resource temporarily unavailable", log_content)
                      or  "make: write error" in all_lines
                      or  "tar: write error" in all_lines
                      or  re.search('make\[[0-9]+\]: write error', all_lines)
                      or  'fatal: Cannot update the ref \'HEAD\'' in all_lines
                      or  extended_message_search("make: write error(.*)was exceeded", all_lines)
                      or  "log writing failed. execution expired" in all_lines
                      or  "log writing failed. deadlock; recursive locking" in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] write error"
                        category = "01-Internal CI issues"
                        sub_category = "01.14-Writing errors"
                        examples = ["write error: Resource temporarily unavailable",
                                    "can't create Thread: Resource temporarily unavailable",
                                    "tar: write error",
                                    "make: write error",
                                    "fatal: Cannot update the ref HEAD",
                                    "make: write error(.*)was exceeded",
                                    "log writing failed. execution expired",
                                    "log writing failed. deadlock; recursive locking"]
                    elif re.search('fatal: remote error:(.*)((\r)?\n)?\s*Storage server temporarily offline', log_content):
                        key = "[ENVIRONMENTAL BREAKAGE] fatal: remote error:(.*)Storage server temporarily offline"
                        category = "01-Internal CI issues"
                        sub_category = "01.17-Storage server offline"
                        examples = ["fatal: remote error:(.*)Storage server temporarily offline"]
                    elif ('The system is going down for halt NOW' in all_lines
                      or re.search('Internal Server Error [0-9]+', all_lines)
                      or 'an error occured within Travis while running your build' in all_lines
                      or 'an error occurred within Travis while running your build' in all_lines
                      or extended_message_search('Communication with Travis(.*)failed', all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] an error occurred within Travis while running your build"
                        category = "01-Internal CI issues"
                        sub_category = "01.09-Unknown Travis CI error"
                        examples = ["The system is going down for halt NOW",
                                    "Internal Server Error [0-9]+",
                                    "an error occurred within Travis while running your build",
                                    "Communication with Travis(.*)failed"]
                    elif extended_message_search('fatal: destination path(.*)already exists and is not an empty directory', value):
                        key = "[ENVIRONMENTAL BREAKAGE] fatal: destination path(.*)already exists and is not an empty directory"
                        category = "01-Internal CI issues"
                        sub_category = "01.18-Path issues"
                        examples = ["fatal: destination path(.*)already exists and is not an empty directory"]
                    elif ("ERROR: Failed to build gem native extension" in all_lines
                      or  "(Gem::Installer::ExtensionBuildError)" in all_lines):
                        key = "[ENVIRONMENTAL BREAKAGE] ERROR: Failed to build gem native extension"
                        category = "01-Internal CI issues"
                        sub_category = "01.02-Error building gems"
                        examples = ["ERROR: Failed to build gem native extension",
                                    "(Gem::Installer::ExtensionBuildError)"]
                    elif (re.search('\[ERROR\]\s+The build could not read [1-9][0-9]* project(s)?', all_lines)
                      or ('E: Some index files failed to download' in all_lines
                      or 'E: Unable to fetch some archives' in all_lines
                      or extended_message_search('E: Failed to fetch(.*)Connection failed'.lower(), all_lines.lower())
                      or extended_message_search('W: Failed to fetch(.*)Could not connect to'.lower(), all_lines.lower())
                      or extended_message_search('W: Failed to fetch(.*)Unable to connect to'.lower(), all_lines.lower())
                      or extended_message_search('W: Failed to fetch(.*)Failed to connect to'.lower(), all_lines.lower())
                      or extended_message_search('W: Failed to fetch(.*)404 Not Found', all_lines))
                     and not ('W: Some index files failed to download. They have been ignored, or old ones used instead' in all_lines
                      or 'E: Some index files failed to download. They have been ignored, or old ones used instead' in all_lines)
                      or re.search('The command(.*)exited with 5', value)
                      or extended_message_search('W: Failed to fetch(.*)404  Not Found', value)
                      or 'An error occured while installing' in value
                      or 'An error occurred while installing' in value):
                        key = "[ENVIRONMENTAL BREAKAGE] Worker fails to fetch resources"
                        category = "01-Internal CI issues"
                        sub_category = "01.03-Failure to fetch resources"
                        examples = ["[ERROR] The build could not read project",
                                    "E: Some index files failed to download",
                                    "E: Unable to fetch some archives",
                                    "E: Failed to fetch(.*)Connection failed",
                                    "W: Failed to fetch(.*)Failed to connect to",
                                    "W: Failed to fetch(.*)404 Not Found",
                                    "The command(.*)exited with 5",
                                    "An error occured while installing"]
                    elif (re.search('Could not find gem(.*)in the gems available on this((\r)?\n)?\s*machine', value)
                      or re.search('Could not find(.*)in any of the (gem )?sources', value)):
                        key = "[ENVIRONMENTAL BREAKAGE] Could not find gems"
                        category = "01-Internal CI issues"
                        sub_category = "01.06-Error finding gems"
                        examples = ["Could not find gem(.*)in the gems available on this machine",
                                    "Could not find(.*)in any of the sources"]
                    elif ('Mysql::Error: query: not connected:' in all_lines
                      or extended_message_search('SQLSTATE[HY000](.*)No such file or directory', all_lines)
                      or extended_message_search('SQLSTATE[HY000](.*)MySQL server has gone away', all_lines)):
                        key = "[ENVIRONMENTAL BREAKAGE] SQLSTATE[HY000]"
                        category = "09-Database (DB) issues"
                        sub_category = "09.02-DB connection error"
                        examples = ["Mysql::Error: query: not connected",
                                    "SQLSTATE[HY000](.*)No such file or directory",
                                    "SQLSTATE[HY000] MySQL server has gone away"]
                    elif "Database creation would exceed quota" in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] Database creation would exceed quota"
                        category = "09-Database (DB) issues"
                        sub_category = "09.01-DB creation quota"
                        examples = ["Database creation would exceed quota"]
                    elif "The server quit without updating PID file" in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] The server quit without updating PID file -- Database-related"
                        category = "09-Database (DB) issues"
                        sub_category = "09.02-DB connection error"
                        examples = ["The server quit without updating PID file"]
                    elif ("has crashed. Please read the crash report" in all_lines
                      or before_last_2_lines.lower().endswith("killed")
                      or before_last_line.lower().endswith("killed")
                      or last_line.lower().endswith("killed")
                      or "Killed" in value
                      or 'Unfortunately, a fatal error has occurred' in all_lines
                         and extended_message_search('install:(.*)returned false', all_lines)
                      or "CRASH: A fatal error has occurred" in all_lines
                      or extended_message_search('The command(.*)exited with 130', value)
                      or extended_message_search('Installing(.*)with native extensions Killed', value)):
                        key = "[ENVIRONMENTAL BREAKAGE] Build crashed"
                        category = "08-Accidental abruption"
                        sub_category = "08.01-Build crashes unexpectedly"
                        examples = ["has crashed. Please read the crash report",
                                    "killed",
                                    "Unfortunately, a fatal error has occurred",
                                    "CRASH: A fatal error has occurred",
                                    "The command xyz exited with 130",
                                    "Installing xyz with native extensions Killed"]
                    elif ('BUILD SUCCESSFUL' in value
                      or  'Build script exited with 0' in value
                      or  'Your build exited with 0' in value
                      or  "build finished successfully" in value):
                        key = "[ENVIRONMENTAL BREAKAGE] BUILD SUCCESSFUL -or- Build exited with 0"
                        category = "10-Buggy build status"
                        sub_category = "10.02-Build exited successfully"
                        examples = ["BUILD SUCCESSFUL",
                                    "Build script exited with 0",
                                    "Your build exited with 0",
                                    "build finished successfully"]
                    elif (extended_message_search('ruby(.*)is not installed', value)
                      or "Mounting remote ruby failed with status 10, stopping installation." in value
                      or "Requested binary installation but no rubies are available to download" in value):
                        key = "[ENVIRONMENTAL BREAKAGE] ruby(.*)is not installed"
                        category = "06-Platform issues"
                        sub_category = "06.01-Language installation issues"
                        examples = ["ruby(.*)is not installed",
                                    "Mounting remote ruby failed with status 10, stopping installation",
                                    "Requested binary installation but no rubies are available to download"]
                    elif 'is not a valid platform. The available options are' in all_lines:
                        key = "[ENVIRONMENTAL BREAKAGE] is not a valid platform. The available options are"
                        category = "06-Platform issues"
                        sub_category = "06.02-Invalid platform"
                        examples = ["is not a valid platform"]
                    elif (re.search('\'ant\' failed in the(.*)repo at', value)
                      and re.search('and(.*)is not properly built', value)):
                        key = "[ENVIRONMENTAL BREAKAGE] is not a valid platform. The available options are"
                        category = "06-Platform issues"
                        sub_category = "06.03-Unexpected failure"
                        examples = ["ant failed in the xyz repo at"]
                    elif i <= 3 or not ('build ' in last_line.lower()):
                        key = "[SUSPICIOUS BREAKAGE] Using worker and/or Build exited without any further progress"
                        category = "01-Internal CI issues"
                        sub_category = "01.04-Logging stopped progressing"
                        examples = ["Trimmed build log", "Using worker and/or Build exited without any further progress"]
                    else:
                        error_messages = identify_developer_breakages(log_content)
                        no_of_error_msgs = len(error_messages)
                        if no_of_error_msgs > 0:
                            developer_breakages += 1
                            build_num_truly_broken_jobs += 1
                            developer_breakages_per_project += 1
                            job_label = "developer_breakage"
                            developer_breakages_found_patterns += 1
                            developer_breakages_found_patterns_per_project += 1
                        else:
                            ## Again, check for the 127 breakage pattern
                            if (extended_message_search('The command(.*)exited with 127', all_lines)
                              or "Command failed with status (127)" in all_lines
                              or "Could not find a valid gem 'bundler' (>= 0)" in value):
                                key = "[ENVIRONMENTAL BREAKAGE] The command(.*)exited with 127"
                                category = "04-Ruby & bundler issues"
                                sub_category = "04.06-Bundler not installed"
                                examples = ["The command xyz exited with 127",
                                            "Command failed with status (127)",
                                            "Could not find a valid gem 'bundler' (>= 0)"]
                            else:
                                if project_name in error_unknown_patterns_per_project:
                                    error_unknown_patterns_per_project[project_name] += " " + log_name
                                else:
                                    error_unknown_patterns_per_project[project_name] = log_name

                                if not (re.search(r'\bERROR\b', all_lines, re.IGNORECASE)
                                   or re.search(r'\bFAILED\b', all_lines, re.IGNORECASE)
                                   or re.search(r'\bFAILURE\b', all_lines, re.IGNORECASE)
                                   or re.search(r'\bCRASH\b', all_lines, re.IGNORECASE)
                                   or re.search(r'\bFATAL\b', all_lines, re.IGNORECASE)
                                   or re.search(r'\bABORTED\b', all_lines, re.IGNORECASE)
                                   or re.search(r'\bKILLED\b', all_lines, re.IGNORECASE)
                                   or re.search(r'\bEXCEPTION\b', all_lines, re.IGNORECASE)
                                   or re.search(r'\bNOT FOUND\b', all_lines, re.IGNORECASE)
                                   or re.search(r'\bFAULT\b', all_lines, re.IGNORECASE)):
                                    key = "[SUSPICIOUS BREAKAGE] No presense of error or failing messages."
                                    category = "01-Internal CI issues"
                                    sub_category = "01.04-Logging stopped progressing"
                                    developer_breakages_unknown_patterns_per_project += 1
                                else:
                                    key  = "[UNKNOWN ERROR] " #+ breaking_msg1
                                    key2 = "" #+ breaking_msg2
                                    build_num_unknown_breakage_jobs += 1
                                    job_label = "unknown_breakage"
                                    unknown_breakages_per_project += 1
                                    no_of_error_msgs = 0
            if key:
                error_msgs_with_last_lines[key] = value
                if key in error_msgs_with_frequency:
                    error_msgs_with_frequency[key] += 1
                    if error_msgs_with_frequency[key] < 30:
                        error_msgs_with_log_ids[key] += (log_name + " ")
                else:
                    error_msgs_with_frequency[key] = 1
                    error_msgs_with_log_ids[key] = log_name + " "

                if (key.startswith("[ENVIRONMENTAL BREAKAGE]")
                 or key.startswith("[SUSPICIOUS BREAKAGE]")):
                    no_of_error_msgs = 1
                    if key.startswith("[ENVIRONMENTAL BREAKAGE]"):
                        build_num_environmental_breakage_jobs += 1
                        environmental_breakages_per_project += 1
                        job_label = "environmental_breakage"
                    else:
                        build_num_suspiciously_broken_jobs += 1
                        suspicious_breakages_per_project += 1
                        job_label = "suspicious_breakage"

                    if (project_name,key) in error_msgs_per_project_frequency:
                        error_msgs_per_project_frequency[(project_name, key)] += 1
                    else:
                        error_msgs_per_project_frequency[(project_name, key)] = 1

            if key2:
                error_msgs_with_last_lines[key2] = value
                if key2 in error_msgs_with_frequency:
                    error_msgs_with_frequency[key2] += 1
                    if error_msgs_with_frequency[key2] < 30:
                        error_msgs_with_log_ids[key2] += (log_name + " ")
                else:
                    error_msgs_with_frequency[key2] = 1
                    error_msgs_with_log_ids[key2] = log_name + " "
            
            whole_msg = key
            if job_label == "developer_breakage":
                whole_msg  = error_messages

            if key2:
                whole_msg += ("\r\n" + key2)
            csvwriter_jobs_labeling.writerow([project_name,
                                              build_id,
                                               ("~"+job_num),
                                               job_label,
                                               no_of_error_msgs,
                                               whole_msg,
                                               category,
                                               sub_category,
                                               examples])
            csvfile_jobs_labeling.flush()
    finished_projects += 1
    
    if valid_logs_per_project > 0:
        environmental_breakages_per_project_ratio = environmental_breakages_per_project/valid_logs_per_project
        environmental_suspicious_ratio = (environmental_breakages_per_project+suspicious_breakages_per_project)/valid_logs_per_project

    else:
        environmental_breakages_per_project_ratio = 0
        environmental_suspicious_ratio = 0

    if developer_breakages_per_project > 0:
        developer_breakages_found_patterns_per_project_ratio =  developer_breakages_found_patterns_per_project/developer_breakages_per_project
    else:
        developer_breakages_found_patterns_per_project_ratio = 0
        
    csvwriter_valid_logs_per_project.writerow([project_name,
                                               valid_logs_per_project,
                                               developer_breakages_per_project,
                                               developer_breakages_found_patterns_per_project,
                                               developer_breakages_found_patterns_per_project_ratio,
                                               environmental_breakages_per_project,
                                               suspicious_breakages_per_project,
                                               unknown_breakages_per_project,
                                               environmental_breakages_per_project_ratio,
                                               environmental_suspicious_ratio])
    csvfile_valid_logs_per_project.flush()
    for key, value in error_unknown_patterns_per_project.items():
        csvwriter_unknown_patterns_per_project.writerow([key, value])
        csvfile_unknown_patterns_per_project.flush()

    for key, value in error_msgs_per_project_frequency.items():
        csvwriter_msgs_per_project.writerow([key[0], key[1], value])
        csvfile_msgs_per_project.flush()

    error_msgs_per_project_frequency.clear()
    error_unknown_patterns_per_project.clear()
    csvfile_msgs_per_project.flush()
    csvfile_valid_logs_per_project.flush()
    csvfile_unknown_patterns_per_project.flush()

#==============================================================================================================
def identify_developer_breakages(log):
    msgs = []
    pattern = ""

    ##======= No. of errors or failures =======##
    if "[ERROR] COMPILATION ERROR :".upper() in log.upper():
        pattern =   '\[INFO\] [1-9][0-9]* error(s)?'
        result = re.search(pattern, log, re.IGNORECASE)
        if result:
            msgs.append(result[0])

        if len(msgs) > 0:
            return msgs

    pattern  = '('
    pattern +=   '([0-9]+ tests completed, [1-9][0-9]* failed)'
    pattern +=   '|([0-9]+ example(s)?(, [1-9][0-9]* failure(s)?)(, [0-9]+ error(s)?)?(, [0-9]+ pending)?)'
    pattern +=   '|([0-9]+ example(s)?(, [0-9]+ failure(s)?)?(, [1-9][0-9]* error(s)?)(, [0-9]+ pending)?)'
    pattern +=   '|([0-9]+ example(s)?(, [0-9]+ expectations(s)?)?(, [1-9][0-9]* failure(s)?)(, [0-9]+ error(s)?)?(, [0-9]+ pending)?)'
    pattern +=   '|([0-9]+ example(s)?(, [0-9]+ expectations(s)?)?(, [0-9]+ failure(s)?)?(, [1-9][0-9]* error(s)?)(, [0-9]+ pending)?)'
    pattern +=   '|([0-9]+ specification(s)?( \([0-9]+ requirement(s)?\))?, [1-9][0-9]* failure(s)?, [0-9]+ error(s)?)'
    pattern +=   '|([0-9]+ specification(s)?( \([0-9]+ requirement(s)?\))?, [0-9]+ failure(s)?, [1-9][0-9]* error(s)?)'
    pattern +=   '|([0-9]+ example(s)?(, [0-9]+ failure(s)?)?(, [1-9][0-9]* error(s)?)(, [0-9]+ pending)?)'
    pattern +=   '|(([0-9]+ run(s)?, )?[0-9]+ assertion(s)?, [1-9][0-9]* failure(s)?, [0-9]+ error(s)?(, [0-9]+ skips)?)'
    pattern +=   '|(([0-9]+ run(s)?, )?[0-9]+ assertion(s)?, [0-9]+ failure(s)?, [1-9][0-9]* error(s)?(, [0-9]+ skips)?)'
    pattern +=   '|(([0-9]+ test(s)?, )?[0-9]+ assertion(s)?, [1-9][0-9]* failure(s)?, [0-9]+ error(s)?(, [0-9]+ skips)?)'
    pattern +=   '|(([0-9]+ test(s)?, )?[0-9]+ assertion(s)?, [0-9]+ failure(s)?, [1-9][0-9]* error(s)?(, [0-9]+ skips)?)'
    pattern +=   '|(Tests run: [0-9]+, Failures: [1-9][0-9]*, Errors: [0-9]+(, Skipped: [0-9]+)?)'
    pattern +=   '|(Tests run: [0-9]+, Failures: [0-9]+, Errors: [1-9][0-9]*(, Skipped: [0-9]+)?)'
    pattern +=   '|(Passed: [0-9]+, Failed: [1-9][0-9]*, Errors: [0-9]+(, Skipped: [0-9]+)?)'
    pattern +=   '|(Passed: [0-9]+, Failed: [0-9]+, Errors: [1-9][0-9]*(, Skipped: [0-9]+)?)'
    pattern +=   '|(pass: [0-9]+,\s+fail: [0-9]+,\s+error: [1-9][0-9]*)'
    pattern +=   '|([1-9][0-9]* failed, [0-9]+ passed)'
    pattern +=   '|(Total tests run: [0-9]+, Failures: [1-9][0-9]*)'
    pattern +=   '|([0-9]+ validation(s)? valid\s+[1-9][0-9]* failed)'
    pattern +=   '|([1-9][0-9]* failed, [0-9]+ succeeded)'
    pattern +=   '|(default - Hits: [0-9]+ Misses: [1-9][0-9]*)'
    pattern +=   '|(pass: [0-9]+,\s+fail: [1-9][0-9]*,\s+error: [0-9]+)'
    pattern +=   '|(FAIL(.*)Passed(.*)Skipped\s+[1-9][0-9]*\s+Failed(.*))'
    pattern +=   '|([1-9][0-9]* error(s)?(\r)?\n\s*FAILED(\r)?\n((\r)?\n)?\s*FAILURE: Build failed with an exception)'
    pattern +=   '|([1-9][0-9]* scenarios \([1-9][0-9]* failed(, [0-9]+ skipped)?(, [0-9]+ undefined)?(, [0-9]+ pending)?(, [0-9]+ passed)?\))'
    pattern +=   '|([1-9][0-9]* steps \([1-9][0-9]* failed(, [0-9]+ skipped)?(, [0-9]+ undefined)?(, [0-9]+ pending)?(, [0-9]+ passed)?\))'
    pattern +=   '|([1-9][0-9]* steps \(([0-9]+ skipped, )?[1-9][0-9]* undefined(, [0-9]+ pending)?(, [0-9]+ passed)?\))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?ERROR: (.*) failed to build [1-9][0-9]* times)'
    pattern +=   '|(BUILD FAILED(\r)?\n(.*): Stopping build (.*) found [1-9][0-9]* rule violations in the code)'
    pattern +=   '|([1-9][0-9]* error(s)?(\r)?\n([0-9]+ warnings)?(\r)?\nrake aborted!)'
    pattern +=   '|(\[apt\] [1-9][0-9]* error(s)?)'
    pattern +=   '|(\[javac\] [1-9][0-9]* error(s)?)'
    pattern +=   '|(\[build-ext\](.*)Error [1-9][0-9]*)'
    pattern +=   '|([0-9]+ specs, [1-9][0-9]* (failure(s)?|error(s)?))'
    pattern +=   '|(\[(.*)\] ([1-9][0-9]*|one|two|three|four|five|six|seven|eight|nine|ten) error(s)?( found)?)'
    pattern +=   '|(TOTAL: [1-9][0-9]* FAILED, [0-9]+ SUCCESS)'
    pattern +=   '|(\s*[0-9]+ passing(.*)(\r)?\n\s*[0-9]+ pending(\r)?\n\s*[1-9][0-9]* failing)'
    pattern +=   '|(Compilation produced [1-9][0-9]* syntax errors)'
    pattern +=   '|(Summary: [0-9]+ exe.(.*)[0-9]+ warn.; [1-9][0-9]* failed)'
    pattern +=   '|([1-9][0-9]* error(s)? generated(.*))'
    pattern +=   '|([1-9][0-9]* error(s)?(\s*(\r)?\n\s*)*:compileDebugJavaWithJavac FAILED)'
    pattern +=   '|(Execution failed for task [\':a-zA-Z0-9\.]*\s*> invalid source release: [0-9\.]*)'
    pattern +=   '|(Completed [0-9]* (unit|integration) test(s)?, [1-9][0-9]* failed)'
    pattern +=   '|(Error: [1-9][0-9]* problem(s)?(.*))'
    pattern +=   '|(#(\s)*Error(\s)*\|(\s)*[1-9][0-9]*(\s)*\|)'
    pattern +=   '|([1-9][0-9]* file(s)? inspected, [1-9][0-9]* offen(s|c)e(s)? detected(\r)?\n((\r)?\n)?((\r)?\n)?The command (.*) exited with 1)'
    pattern += ')'
    
    for result in re.findall(pattern, log, re.IGNORECASE):
        if result[0]:
            msg = re.sub('0[xX][0-9a-fA-F]+', '0X', result[0])
            if re.search('|(#(\s)*Error(\s)*\|(\s)*[1-9][0-9]*(\s)*\|)', log):
                msg = msg.replace(" ", "")
            msgs.append(msg)

    if len(msgs) > 0:
        return msgs
    
    ##======= Failed to execute goal errors =======##
    pattern = '('
    pattern +=   '(\[ERROR\] Failed to execute goal (.*)There (was|were) [1-9][0-9]* error(s)?)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Compilation failure(.*)(\r)?\n(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)initialize failed: Java returned:(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Fatal error compiling(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)failed: unknown result)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)does not match)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Couldn\'t find the release(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Error detected parsing the header)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)No such compiler(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Properties file not found(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Code generating failed(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Invalid SDK(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Checkstyle violations)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)already exists)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Unable to find(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Error while creating archive)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Error provisioning assembly(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)does not exist)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)No (.*) could be found)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)The packaging for this project did not assign a file to the build artifact)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Error\(s\) found in bundle configuration)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Check for forbidden API calls failed)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)NullPointerException)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)java.nio.file.FileAlreadyExistsException(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Unable to calculate distance between(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Error adding file to archive(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Exception was thrown while processing(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Could not extract archive(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Failed to run task(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Error parsing(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Coverage check failed)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)failed: An API incompatibility was encountered(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)There was a timeout or other error(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)failed with [0-9]* bugs and [0-9]* errors(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)An error has occurred in(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Command execution failed(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)failed(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)There are test failures(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Failed to run the report(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Error occurred in starting fork(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Error executing ant task(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)An Ant BuildException has occured(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Too many (files with )?unapproved license(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Some files do not have the expected license(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Can\'t find any war dependency(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Failed to retrieve(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Failed to refresh project dependencies(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Dependency problems found(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Failed to resolve(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Error setting up or running(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)\(No such file or directory\))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Cannot analyze dependencies(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)You have(.*)violation(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Found dependency version conflicts(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)\(sign-artifacts\)(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Could not find artifact(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Execution(.*)failed: found(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)\(InstallError\) invalid gem:(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)java\.lang\.ClassCastException:(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)\(LoadError\) library(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Error while generating Javadoc)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Signature errors found(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)Some Enforcer rules have failed(.*))'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)1 build failed)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)The artifact information is incomplete or not valid)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)failed to start)'
    pattern +=   '|(\[ERROR\] Failed to execute goal (.*)failed: A required class was missing(.*))'
    pattern +=   '|(\[ERROR\] (Failed to execute goal|Plugin) (.*)Could not transfer artifact(.*))'
    pattern +=   '|(\[ERROR\] (Failed to execute goal|Plugin) (.*)No versions available for(.*))'
    pattern +=   '|(\[ERROR\] (Failed to execute goal|Plugin) (.*)Failed to read artifact(.*))'
    pattern +=   '|(\[ERROR\] Failed to parse plugin (.*)invalid LOC header(.*))'
    pattern +=   '|(\[ERROR\] Failed to parse plugin (.*)No plugin descriptor found(.*))'
    pattern +=   '|(\[ERROR\] Unable to read model at (.*)Unknown category(.*))'
    pattern += ')'

    result = re.search(pattern, log, re.IGNORECASE)
    if(result):
        msg = re.sub('0[xX][0-9a-fA-F]+', '0X', result[0])
        msgs.append(msg)

    if len(msgs) > 0:
        if ('Errno::ENOENT: No such file or directory' in log
          or 'Errno::ENOEXEC: Exec format error' in log):
            result = re.search('((Errno::ENOENT: No such file or directory(.*))|(Errno::ENOEXEC: Exec format error(.*)))', log, re.IGNORECASE)
            if(result):
                msg = re.sub('0[xX][0-9a-fA-F]+', '0X', result[0])
                msgs.append(msg)
        return msgs

    if re.search('rake aborted!(\r)?\nError compiling', log):
        pattern  = '('
        pattern +=   '((.*)error: no matching function for call to(.*))'
        pattern +=   '|((.*)error: using typedef-name(.*))'
        pattern +=   '|((.*)error: could not convert(.*))'
        pattern +=   '|((.*)error: (.*) is not a member of(.*))'
        pattern +=   '|((.*)error: invalid value-initialization(.*))'
        pattern +=   '|((.*)error: (.*) was not declared(.*))'
        pattern +=   '|((.*)error: control reaches end of non-void func(.*))'
        pattern +=   '|((.*)error: (.*) may be used uninitialized(.*))'
        pattern +=   '|((.*)variable(.*)is uninitialized when used)'
        pattern +=   '|((.*)error: (.*) expects argument of type(.*))'
        pattern +=   '|((.*)error: invalid operands of types(.*))'
        pattern +=   '|((.*)error: left shift(.*))'
        pattern +=   '|((.*)could not read symbols: Bad value)'
        pattern +=   '|((.*)error: (.*) has not been declared)'
        pattern +=   '|((.*)error: ignoring return value(.*))'
        pattern +=   '|((.*)error: private field(.*)is not used)'
        pattern +=   '|((.*)error: (.*) called on(.*))'
        pattern +=   '|((.*)error: unused variable(.*))'
        pattern +=   '|((.*)error: variable source_str set but not used(.*))'
        pattern +=   '|((.*)error: no matching function for call(.*))'
        pattern +=   '|((.*)error: (.*) no member named(.*))'
        pattern +=   '|((.*)error: suggest parentheses around(.*))'
        pattern +=   '|((.*)error: variable or field (.*) declared(.*))'
        pattern +=   '|((.*)error: expected declaration specifiers(.*))'
        pattern +=   '|((.*)error: dereferencing type-punned pointer(.*))'
        pattern +=   '|((.*)error: comparison between signed and unsigned integer expressions(.*))'
        pattern +=   '|(WARNING: (.*) is missing on your system)'
        pattern += ')'

        for result in re.findall(pattern, log, re.IGNORECASE):
            if result[0]:
                msg = re.sub('0[xX][0-9a-fA-F]+', '0X', result[0])
                if msg not in msgs:
                    msgs.append(msg)
        if len(msgs) > 0:
            return msgs

    ##======= Compiler related errors =======##
    pattern  = '('
    pattern +=   '(((SyntaxError:(.*): syntax error)|syntax error(.*)\(SyntaxError\)))'
    pattern +=   '|(syntax error, unexpected(.*)expecting(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?syntax error on line [0-9]+, col (-)?[0-9]+:)'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?(.*)syntax error, unexpected(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?tests do not work with(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?bad value for range)'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?An error has occurred, this and all later migrations canceled:)'
    pattern +=   '|(The driver encountered an unknown error: cannot load Java(.*))'
    pattern +=   '|(Exception in (.*) \(NoMethodError\)(.*))'
    pattern +=   '|(W: Failed to fetch(.*)Hash Sum mismatch)'
    pattern +=   '|(Lexing error on line(.*))'
    pattern +=   '|(.py:(.*)line too long(.*))'
    pattern +=   '|([a-zA-Z0-9_]+.py:(.*) too many blank lines(.*))'
    pattern +=   '|([a-zA-Z0-9_]+(.c|.cpp)(.*)error: (.*) undeclared \(first use in this function\))'
    pattern +=   '|(Global handler has fired: PRECONDITION_FAILED(.*))'
    pattern +=   '|(Simulator session started with error: (.*)Unable to run app in Simulator)'
    pattern +=   '|(Thread deadlock in (.*)(\r)?\n((\r)?\n)?Aborted)'
    pattern +=   '|(undefined method (.*) (for|on) (.*) \(NoMethodError\))'
    pattern +=   '|(NoMethodError: undefined method (.*) (for|on) (.*))'
    pattern +=   '|(rake aborted!(\r)?\n((.*)(\r)?\n)?((\r)?\n)?undefined method(.*)(for|on)(.*))'
    pattern +=   '|(A syntax error has occurred:(\r)?\n\s+expecting(.*))'
    pattern +=   '|(syntax error(.*)\(ArgumentError\))'    
    pattern +=   '|(SyntaxError:(.*)invalid (multibyte)? char(.*))'
    pattern +=   '|(SyntaxError:(.*)unknown type of(.*))'
    pattern +=   '|(`syntax_error\'(.*)\(SyntaxError\))'
    pattern +=   '|(`assert_index\'(.*)\(RuntimeError\))'
    pattern +=   '|(`initialize\'(.*)Error\))'
    pattern +=   '|(Error:(.*)not present or broken)'
    pattern +=   '|(Main Manifest missing from(.*))'
    pattern +=   '|(Converge failed on instance(.*))'
    pattern +=   '|(RSpec::Expectations::ExpectationNotMetError)'
    pattern +=   '|(cannot open shared object file: No such file or directory(.*))'
    pattern +=   '|(Gem::RemoteFetcher::UnknownHostError: no such name(.*))'
    pattern +=   '|(ERROR:\s+While executing gem(.*)\(Gem::DependencyError\))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?(.*)expecting(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?RABBITMQ MUST BE RUNNING)'
    pattern +=   '|(Error:(.*)failed((\r)?\n)*(.*)expected but was((\r)?\n)*(.*))'
    pattern +=   '|(An exception occurred running (.*)((\r)?\n)+(.*)\(SyntaxError\))'
    pattern +=   '|(An exception occurred running (.*)((\r)?\n)+\s*file not found:(.*))'
    pattern +=   '|(An exception occurred running (.*)((\r)?\n)+\s*Could not find(.*))'
    pattern +=   '|(An exception occurred running (.*)((\r)?\n)+\s*method not initialized properly(.*))'
    pattern +=   '|(The SDK Build Tools (.*) is too low for project)'
    pattern +=   '|([a-zA-Z]+:(.*)bad variable name)'
    pattern +=   '|(Caused by:(.*)(\r)?\n(.*))'
    pattern +=   '|(ERR! not ok code 0)'
    pattern +=   '|(Exception message: Could not satisfy all requirements(.*))'
    pattern +=   '|(ERROR(.*)404 page not found)'
    pattern +=   '|(tar: Error is not recoverable: exiting now)'
    pattern +=   '|(Error: tried to access method(.*)from class(.*))'
    pattern +=   '|(Error: (.*)did not build)'
    pattern +=   '|(error: Could not compile (.*) test program)'
    pattern +=   '|(Error: Failed to download resource(.*))'
    pattern +=   '|(Error: No such file or directory(.*))'
    pattern +=   '|(bin/rake: No such file or directory(.*))'
    pattern +=   '|(ruby: Is a directory - spec \(Errno::EISDIR\))'
    pattern +=   '|(Error: An unsatisfied requirement(.*))'
    pattern +=   '|(Error: No available formula (with|for)(.*))'
    pattern +=   '|(\[ERROR\] npm WARN(.*)No repository field)'
    pattern +=   '|(\[ERROR\] Could not build new ruby extent. This means(.*))'
    pattern +=   '|(\[WARNING\] Could not transfer(.*)unknown error)'
    pattern +=   '|(Unable to parse command line options: Unrecognized option:(.*))'
    pattern +=   '|(: Missing helper file(.*)\(LoadError\))'
    pattern +=   '|(Running (.*) failed. Please check (.*) more details)'
    pattern +=   '|(Sorry, but JDK \'(.*)\' is not known)'
    pattern +=   '|(Execution failed for task \'(.*)\'.(\r)?\n> (.*))'
    pattern +=   '|(undefined local variable or method (.*) (for|on) (.*) \(NameError\))'
    pattern +=   '|(method (.*) not defined (.*) \(NameError\))'
    pattern +=   '|(NameError: undefined (local variable or )?method(.*))'
    pattern +=   '|(NameError: global name (.*) is not defined)'
    pattern +=   '|(uninitialized constant(.*)\(NameError\))'
    pattern +=   '|(NameError: uninitialized (class|variable|method|function|constant) (.*))'
    pattern +=   '|(rake aborted!(\r)?\nundefined local variable or method(.*)(for|on)(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?(.*)uninitialized constant(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?empty range in (.*) class)'
    pattern +=   '|(rake aborted!(\r)?\nNameError: wrong constant name(.*))'
    pattern +=   '|(rake aborted!(\r)?\nThe driver encountered an unknown err(.*))'
    pattern +=   '|(wrong constant name (.*) \(NameError\))'
    pattern +=   '|(Could not find property(.*)on(.*))'
    pattern +=   '|(Unknown ruby interpreter version(.*))'
    pattern +=   '|(Error: Attempt to unlock(.*))'
    pattern +=   '|(Fatal error: Unable to find(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)+PG::Error:(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)+StandardError: An error has occurred, this and all later migrations canceled)'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?is extracted out of Rails into a gem)'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)+PG::UndefinedColumn: ERROR:  column(.*))'
    pattern +=   '|(invalid pattern:(.*)\(ArgumentError\))'
    pattern +=   '|(Could not find shared examples (.*) \(ArgumentError\))'
    pattern +=   '|(ArgumentError: Could not find shared examples (.*))'
    pattern +=   '|(ArgumentError: file not found(.*))'
    pattern +=   '|(ArgumentError:(.*)cannot be overwritten)'
    pattern +=   '|(ArgumentError: (.*)argument not supported)'
    pattern +=   '|(ArgumentError: The (.*) option must be one of (.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?ArgumentError: comparison(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?(.*)Can\'t assign to nil)'
    pattern +=   '|(negative array size \(or size too big\) \(ArgumentError\))'
    pattern +=   '|(: unsupported signal SIGINFO \(ArgumentError\))'
    pattern +=   '|(Illformed requirement(.*)\(ArgumentError\))'
    pattern +=   '|(ArgumentError: Illformed requirement(.*))'
    pattern +=   '|(Buildfile: (.*) does not exist)'
    pattern +=   '|(tried to create (.*) without a block \(ArgumentError\))'
    pattern +=   '|(ArgumentError: wrong number of arguments(.*))'
    pattern +=   '|(ArgumentError: unknown encoding name(.*))'
    pattern +=   '|(Arguments cannot be nil or empty. \(ArgumentError\))'    
    pattern +=   '|(rake aborted!(\r)?\nwrong number of arguments(.*))'
    pattern +=   '|(\[WARNING\] File encoding has not been set, using platform encoding (.*), i.e. build is platform dependent!)'
    pattern +=   '|(rake aborted!(\r)?\n(.*)is deprecated(.*))'
    pattern +=   '|(Could not find(.*)release for(.*))'
    pattern +=   '|(taskdef class (.*) cannot be found)'
    pattern +=   '|(JDK (.*) is no longer supported)'
    pattern +=   '|(ERROR: (.*) no longer supported)'
    pattern +=   '|(The limit on text can be at most 1GB - 1byte)'
    pattern +=   '|(Gemfile syntax error:)'
    pattern +=   '|(ERROR:\s+null value in column (.*) violates not-null constraint)'
    pattern +=   '|(\[ERROR\](.*)cannot find symbol)'
    pattern +=   '|(symbol lookup error(.*)undefined symbol(.*))'
    pattern +=   '|(\[ERROR\](.*)cannot be applied to(.*))'
    pattern +=   '|(\[ERROR\](.*)error: no suitable method found for(.*))'
    pattern +=   '|(\[ERROR\](.*)log has private access in(.*))'
    pattern +=   '|(\[ERROR\](.*)is not abstract and does not override abstract method(.*))'
    pattern +=   '|(\[ERROR\] Internal error: java\.lang\.NullPointerException)'
    pattern +=   '|(\[ERROR\] Two or more projects in the reactor have the same identifier(.*))'
    pattern +=   '|(\[ERROR\] Errors in(.*))'
    pattern +=   '|(This class is not GAE compliant(.*))'
    pattern +=   '|(Parse error at (.*) Found (.*) when expecting (.*))'
    pattern +=   '|(rake aborted!(\r)?\n(.*)undefined symbol:(.*))'
    pattern +=   '|(NameError: cannot load Java class(.*))'
    pattern +=   '|(Exception in (.*) java\.lang\.AbstractMethodError)'
    pattern +=   '|(build file(.*)unexpected token:(.*))'
    pattern +=   '|(unexpected token(.*)\(JSON::ParserError\))'
    pattern +=   '|(couldn\'t parse (.*) \(Psych::SyntaxError\))'
    pattern +=   '|(ERR! 404(.*)is not in the npm registry)'
    pattern +=   '|(ERR! SyntaxError: Unexpected token(.*))'
    pattern +=   '|(Error: shasum check failed for(.*))'
    pattern +=   '|(\[error\]: Missing (.*) for Markdown formatting)'
    pattern +=   '|(Unrecognized option:(.*)(\r)?\nError: Could not create the Java Virtual Machine)'
    pattern +=   '|(A problem occurred(.*)(\r)?\n(.*)java\.lang\.UnsupportedClassVersionError(.*))'
    pattern +=   '|(A problem occurred evaluating(.*)(\r)?\n((\r)?\n)?(.*)Plugin (.*) not found)'
    pattern +=   '|(Exception in(.*)java\.lang\.UnsupportedClassVersionError(.*))'
    pattern +=   '|(TypeError: Coercion error: (.*) failed)'
    pattern +=   '|(Time can\'t be coerced into Float \(TypeError\))'
    pattern +=   '|(: (.*) is not a class \(TypeError\))'
    pattern +=   '|(: can\'t convert (.*) into (.*) \(TypeError\))'
    pattern +=   '|(all Hash keys must be(.*)\(TypeError\))'
    pattern +=   '|(TypeError:(.*)is not an object(.*))'
    pattern +=   '|(no implicit conversion (of|from) (.*) (into|to) (.*) \(TypeError\))'
    pattern +=   '|(rake aborted!((\r)?\n)*no implicit conversion (of|from) (.*) (into|to) (.*))'
    pattern +=   '|(TypeError: no implicit conversion (of|from) (.*) (into|to) (.*))'
    pattern +=   '|(TypeError: Arguments to (.*) must be (.*))'
    pattern +=   '|(Parser does not support parsing(.*)\(NotImplementedError\))'
    pattern +=   '|(NotImplementedError: Parser does not support parsing(.*))'
    pattern +=   '|(rake aborted!(\r)?\nParser does not support parsing(.*))'
    pattern +=   '|(\[(.*)\] error: uncaught exception during compilation(.*))'
    pattern +=   '|(\[(.*)\] error: java\.lang\.(.*)Exception(.*))'
    pattern +=   '|((clang|gcc): error: unknown argument:(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?invalid byte sequence in (.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?(.*)variable be set to(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?Unit is not a module)'
    pattern +=   '|(\[javac\] (.*)error:(.*)does not exist)'
    pattern +=   '|(cp: target(.*)is not(.*))'
    pattern +=   '|(\[get\] Can\'t get(.*))'
    pattern +=   '|(Message: InsufficientInstanceCapacity => We currently do not have sufficient(.*)capacity)'
    pattern +=   '|(\[exec\] Decompile Exception(.*))'
    pattern +=   '|(\[exec\] Something failed(.*))'
    pattern +=   '|(\[SEVERE\] Encountered an unexpected exception(.*))'
    pattern +=   '|(cannot create (.*) Directory nonexistent)'
    pattern +=   '|(javac: directory not found(.*))'
    pattern +=   '|(BUILD FAILED(\s*(\r)?\n\s*)*(.*)Invalid file:)'
    pattern +=   '|(Execution failed for task (.*))'
    pattern +=   '|(Building (.*) errors)'
    pattern +=   '|(> Failed to apply(.*))'
    pattern +=   '|(> No such property(.*))'
    pattern +=   '|(No such property: (.*) for class(.*))'
    pattern +=   '|(failed to find Build Tools(.*))'
    pattern +=   '|(Task(.*)not found in root project(.*))'
    pattern +=   '|(Error: Ignoring unknown package filter(.*))'
    pattern +=   '|(Error: Unknown command: services(.*))'
    pattern +=   '|(PGError: ERROR:(.*))'
    pattern +=   '|(Could not find any version that matches(.*))'
    pattern +=   '|(> startup failed:((\r)?\n)*(.*))'
    ##======= Database related errors =======##
    pattern +=   '|(ERROR 1007(.*)Can\'t create database)'
    pattern +=   '|(Mysql2::Error: Error on rename of(.*))'
    pattern +=   '|(Mysql2::Error:(.*)\(Sequel::DatabaseError\))'
    pattern +=   '|(Mysql2::Error: Table(.*)doesn\'t exist(.*))'
    pattern +=   '|(SQLException: no such table(.*))'
    pattern +=   '|(Couldn\'t create database for(.*))'
    pattern +=   '|(Error: Can\'t create database(.*))'
    pattern +=   '|(Error: Unknown database(.*))'
    pattern +=   '|(ERROR(.*)No database selected)'
    pattern +=   '|(ERROR(.*)Specified key was too long)'
    pattern +=   '|(database(.*)already exists)'
    pattern +=   '|(rake aborted!((\r)?\n)((\r)?\n)?Incorrect MySQL client library version)'
    pattern +=   '|(FATAL:\s+database(.*)does not exist)'
    pattern +=   '|(role(.*)is not permitted to log in)'
    pattern +=   '|(Error:\s(\s)?relation (.*) does not exist)'
    pattern +=   '|(rake aborted!((\r)?\n)((\r)?\n)?Error dumping database)'
    pattern +=   '|(rake aborted!((\r)?\n)((\r)?\n)?ActiveRecord::DuplicateMigrationVersionError: Multiple migrations have the version number)'
    pattern +=   '|(ERROR:  CREATE DATABASE cannot be executed(.*))'
    pattern +=   '|(rake aborted!(\r)?\ndatabase configuration does not specify adapter)'
    pattern +=   '|(No integer type has byte size(.*))'
    pattern +=   '|(rake aborted!(\r)?\nMysql::Error:(.*))'
    pattern +=   '|(rake aborted!(\r)?\nCould not find table(.*))'
    pattern +=   '|(rake aborted!(\r)?\n(.*)Mysql2::Error:(.*))'
    pattern +=   '|(rake aborted!(\r)?\n(.*)Incorrect MySQL client library version!(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?(.*)Could not load database configuration(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?(.*)test database is not configured)'    
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?SQLite3::SQLException(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?missing(.*))'
    pattern +=   '|(psql: FATAL:(.*))'
    ##======= Gem related errors =======##
    pattern +=   '|(ERROR:(.*)Could not find a valid gem(.*)in any repository)'
    pattern +=   '|(Couldn\'t install gem(.*)Could not find a valid gem(.*)in a repository)'
    pattern +=   '|(Could not find gem(.*)at master\))'
    pattern +=   '|(rake aborted!(\r)?\nBundler::GemRequireError:(.*))'
    pattern +=   '|(ERROR:(.*)\(Gem::SpecificGemNotFoundException\))'
    pattern +=   '|(ERROR: Could not find(.*)among(.*))'
    pattern +=   '|(\[java\] Could not find(.*)among(.*))'
    pattern +=   '|(<ActiveModel::Errors:)'
    pattern +=   '|(rake aborted!(\r)?\n(.*)is not available to download, try a different version)'
    pattern +=   '|(: incorrect header check \(Zlib::DataError\))'
    pattern +=   '|(Could not find(.*)(\r)?\n\s+Searched in the following)'
    pattern +=   '|(Error: Could not find or load main class(.*))'
    pattern +=   '|(library not found for(.*)\(LoadError\))'
    pattern +=   '|(jruby: No such file or directory(.*)\(LoadError\))'
    pattern +=   '|(BUILD FAILED(\r)?\n(.*)Class Not Found(.*)could not be loaded)'
    pattern +=   '|(\[java\] Could not find the main class:(.*))'
    pattern +=   '|(Could not resolve all dependencies for(.*)((\r)?\n)+(.*)Artifact(.*)not found)'
    pattern +=   '|(Could not resolve all dependencies for(.*)(\r)?\n((\r)?\n)?((\r)?\n)?(.*)> Could not (resolve|download)(.*))'
    pattern +=   '|(Gemset (.*) does not exist, (.*) first)'
    pattern +=   '|(Could not locate Gemfile)'
    pattern +=   '|(Fatal error: ENOTEMPTY, rename)'
    pattern +=   '|(Error: Specify a version for (.*))'
    pattern +=   '|(Your Gemfile requires gems that depend( depend)? on each other, creating(?s:.)*again)'
    pattern +=   '|(There was a (.*) while loading(.*))'
    pattern +=   '|(Buildfile: (.*) does not exist!(\r)?\nBuild failed)'
    pattern +=   '|(There is no checksum for (.*) not possible to validate it.(\r)?\nThis could be because your RVM install\'s list of versions is out of date)'
    pattern +=   '|(Gemfile syntax error:(\r)?\n(.*)syntax error(.*))'
    pattern +=   '|(Depending on your version of (.*), you may need to install (.*) data)'
    pattern +=   '|(ERROR:\s+Error installing (.*):(\r)?\n((\r)?\n)?(.*)requires(.*))'
    pattern +=   '|(Your Gemfile lists the gem (.*) more than once)'
    pattern +=   '|(Your Gemfile.lock is corrupt.(.*)(\r)?\n(.*)(\r)?\nDEPENDENCIES section(.*))'
    pattern +=   '|(rake aborted!(\r)?\nPlease install the (.*) adapter:(.*))'
    pattern +=   '|(You cannot specify the same gem twice(.*)((\r)?\n)?((.*)(\r)?\n)?You specified(.*))'
    pattern +=   '|(The source (.*) is deprecated because HTTP requests are insecure)'
    pattern +=   '|(ERROR:\s+While executing gem(.*)(\r)?\n\s+BUG: chdir not supported)'
    pattern +=   '|(ERROR:\s+While executing gem(.*)\(ArgumentError\))'
    pattern +=   '|(ERROR:\s+While executing gem (.*) \(NoMethodError\))'
    pattern +=   '|(ERROR:\s+While executing gem (.*) \(Gem::RemoteFetcher::FetchError\))'
    pattern +=   '|(There are multiple gemspecs at(.*))'
    pattern +=   '|(Message: InstanceLimitExceeded => Your quota allows for (.*) more running instance(s)?)'
    pattern +=   '|(Message: Failed to complete #create action: \[The instance ID)'
    pattern +=   '|(Message: Failed to complete #create action: \[stopped waiting due to an unexpected error: The instance ID)'
    pattern +=   '|(dpkg: error processing (.*)(\r)?\n\s*dependency problems - leaving unconfigured)'
    pattern +=   '|(Bundler is not compatible with Rubygems(.*))'
    pattern +=   '|(Could not find gem(.*)(\r)?\n\s*Source (contains|does not contain)(.*))'
    ##======= Rake errors =======##
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?No such file or directory(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?Error trying to compile(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?call/cc is not implemented!)'
    pattern +=   '|(You are using (.*) RSpec requires (.*)\(RSpec::Support::LibraryVersionTooLowError\))'
    pattern +=   '|(You provided(.*)but we need(.*)\(ActiveAdmin::Dependency::Error\))'
    pattern +=   '|(line(.*)No such file or directory)'
    pattern +=   '|(Errno::ENOENT: No such file or directory(.*))'
    pattern +=   '|(err: open(.*)No such file or directory)'
    pattern +=   '|(Errno::ENOEXEC: Exec format error(.*))'
    pattern +=   '|((LoadError: )?((no such file to load)|(cannot load such file)) --(.*))'
    pattern +=   '|(LoadError: load error:(.*))'
    pattern +=   '|(no such file to load -- (.*) \(LoadError\))'
    pattern +=   '|(unable to find (.*) command (.*) \(LoadError\))'
    pattern +=   '|(Read-only file system - (.*) \(Errno::EROFS\))'
    pattern +=   '|(invalid option: (.*) \(defined in (.*)\))'
    pattern +=   '|([a-zA-Z]+: (.*)unknown option to (.*))'
    pattern +=   '|(Cannot remove unknown package \'(.*)\')'
    pattern +=   '|(The command (.*) exited with 126)'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?Don\'t know how to build task (.*))'
    pattern +=   '|(rake aborted!(\r)?\n(.*)loaded before(.*))'
    pattern +=   '|(Failure to find (.*) was cached in the local repository)'
    pattern +=   '|(Could not find artifact(.*)in(.*))'
    pattern +=   '|(java\.net\.MalformedURLException: no protocol:(.*))'
    pattern +=   '|(Failed to transfer file:(.*)Return code is: [1-9][0-9]* , ReasonPhrase:Conflict)'
    pattern +=   '|(You have [1-9][0-9]* pending migration(s)?:(\r)?\n(.*))'
    pattern +=   '|(Missing setting(.*)in(.*))'
    pattern +=   '|(rake aborted!((\r)?\n)*(.*)is not checked out)'
    pattern +=   '|(rake aborted!((\r)?\n)((\r)?\n)?No Rakefile found(.*))'
    pattern +=   '|(rake aborted!((\r)?\n)*Found [1-9][0-9]* error(s))'
    pattern +=   '|(rake aborted!((\r)?\n)*load error:(.*))'
    pattern +=   '|(rake aborted!((\r)?\n)*key not found:(.*))'
    pattern +=   '|(rake aborted!((\r)?\n)*You have already activated(.*), but your Gemfile requires(.*))'
    ##======= Misc errors =======##
    pattern +=   '|(GPG signature verification failed for(.*)!)'
    pattern +=   '|(ThreadError: can\'t create Thread \(11\))'
    pattern +=   '|(The signal (.*) is in use by the JVM and will not work correctly on this platform)'
    pattern +=   '|(\[ERROR\] The projects in (.*) contain a cyclic reference(.*))'
    pattern +=   '|(\[ERROR\] unrecognized configuration parameter(.*))'
    pattern +=   '|(sudo:(.*)command not found)'
    pattern +=   '|(exec:(.*)not found)'
    pattern +=   '|(Is a directory - read\([0-9]*\) failed \(Errno::EISDIR\))'
    pattern +=   '|(\[ERROR\] Could not find the selected project(.*))'
    pattern +=   '|(> failed to find (.*))'
    pattern +=   '|(chown: (.*) Operation not permitted)'
    pattern +=   '|(unknown error: cannot kill(.*))'
    pattern +=   '|(fatal: failed to write ref-pack file: Input/output error)'
    pattern +=   '|(file not added for reaping:(.*))'
    pattern +=   '|(rake aborted!((\r)?\n)*(.*)was not set)'
    pattern +=   '|(rake aborted!((\r)?\n)*Index name(.*)is too long)'
    pattern +=   '|(rake aborted!((\r)?\n)*You should not use the (.*) method in your router without)'
    pattern +=   '|(error:(.*)bad decrypt(.*))'
    pattern +=   '|(error: unable to create file(.*)\(Invalid argument\))'
    pattern +=   '|(fatal: cannot create directory(.*)Invalid argument)'
    pattern +=   '|((RuntimeError: )?No session, please create a session first(.*))'
    pattern +=   '|(Unable to resolve project target(.*))'
    pattern +=   '|(Building(.*)Could not GET(.*))'
    pattern +=   '|(Loading(.*)Could not (GET|HEAD)(.*))'
    pattern +=   '|(rake is not part of the bundle(.*)\(Gem::LoadError\))'
    pattern +=   '|(Gem::LoadError: rake is not part of the bundle)'
    pattern +=   '|(Gem::LoadError: Specified (.*), but the gem is not loaded)'
    pattern +=   '|(rake aborted!((\r)?\n)*Adjust flog score down to(.*))'
    pattern +=   '|(ArgumentError: Invalid route name, already in use(.*))'
    pattern +=   '|(ArgumentError: invalid byte sequence in(.*))'
    pattern +=   '|([a-zA-Z]+:(.*)cannot (.*) No such file or directory)'
    pattern +=   '|(make:(.*)No targets specified and no makefile found)'
    pattern +=   '|(make:(.*)No rule to make target(.*))'
    pattern +=   '|(/usr/bin/(.*): cannot find(.*))'
    pattern +=   '|(unzip:  cannot find zipfile directory in)'
    pattern +=   '|(rake aborted!((\r)?\n)*(.*)Multiple migrations have the name(.*))'
    pattern +=   '|(The command (.*) failed and exited with 20 )'
    pattern +=   '|(fatal error: (.*) No such file or directory(\r)?\ncompilation terminated)'
    pattern +=   '|(Error: error(.*)File to import not found or unreadable)'
    pattern +=   '|(rake aborted!((\r)?\n)*(.*)must be defined)'
    pattern +=   '|(N/A: version (.*) is not yet installed)'
    pattern +=   '|([a-zA-Z]+: Version (.*) was not found)'
    pattern +=   '|(failed with exit status: 63)'
    pattern +=   '|(incompatible marshal file format(.*)\(TypeError\))'
    pattern +=   '|(Could not find method(.*)for arguments)'
    pattern +=   '|(Cannot add task(.*)as a task with that name already exists)'
    pattern +=   '|(Cannot convert(.*)to an object of type(.*))'
    pattern +=   '|(build file(.*)Statement labels may not be used in build scripts)'
    pattern +=   '|(Version(.*)is to confusing to select ruby interpreter)'
    pattern +=   '|(failed: exception happened outside interpreter(.*))'
    pattern +=   '|(rake aborted!(\r)?\ncomparison of(.*)with(.*)failed)'
    pattern +=   '|(BUILD FAILED((\r)?\n)*(.*)is missing)'
    pattern +=   '|(Error validating bytecode: method not initialized properly)'
    pattern +=   '|(BUILD FAILED((\r)?\n)*(.*)?The following error occurred while executing this line:((\r)?\n)*(.*)?)'
    pattern +=   '|(error: device(.*)not found(\r)?\n((\r)?\n)?Failed to start emulator)'
    pattern +=   '|(error: device(.*)not found(\r)?\n((\r)?\n)?Failed to start emulator)'
    pattern +=   '|(ERROR: An error was encountered with the build)'
    pattern +=   '|(ERROR(.*)The engine version is lesser than the minimum required by(.*))'
    pattern +=   '|(rake aborted!(\r)?\nCould not find rspec(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?You have a nil object when you didn\'t expect it!)'
    pattern += ')'

    for result in re.findall(pattern, log, re.IGNORECASE):
        if result[0]:
            msg = re.sub('0[xX][0-9a-fA-F]+', '0X', result[0])
            if msg not in msgs:
                msgs.append(msg)
    if len(msgs) > 0:
        return msgs

    ##======= Time-consuming patterns =======##
    pattern = '('
    pattern +=   '((.*) depends on (.*) however:(\r)?\n\s*Package (.*) is not installed)'
    pattern +=   '|((.*)You have a nil object when you didn\'t expect it! \(NoMethodError\))'
    pattern +=   '|((.*)marshal data too short \(ArgumentError\))'    
    pattern +=   '|((.*): empty string \(ArgumentError\))'    
    pattern +=   '|(AttributeError: (.*) object has no attribute (.*))'    
    pattern +=   '|((.*)line(.*): unbound variable)'
    pattern +=   '|((.*).java:[1-9][0-9]*: error:(.*))'
    pattern +=   '|((.*)doesn\'t exist yet. Run(.*)to create it)'    
    pattern +=   '|((.*) loaded before (.*) \(RuntimeError\))'
    pattern +=   '|((.*) version has changed (.*) \(RuntimeError\))'
    pattern +=   '|((.*)Unable to resolve ip address for(.*)\(RuntimeError\))'
    pattern +=   '|((.*)Unknown Rubinius language mode:\s+\(RuntimeError\))'
    pattern +=   '|((.*)unexpected action:(.*)\(RuntimeError\))'
    pattern +=   '|((.*)cannot execute: Permission denied)'
    pattern +=   '|((.*)Permission denied \(Permission denied\))'
    pattern +=   '|((.*)is not installed(.*)(\r)?\n(.*)To install do:(.*))'
    pattern +=   '|((.*)Unable to autoload constant(.*)\(LoadError\))'
    pattern +=   '|((.*):\s*in(.*): java\.util\.ConcurrentModificationException)'
    pattern +=   '|((.*)system propery is not set. Check(.*))'
    pattern +=   '|((.*)(\r)?\nRuboCop failed!)'
    pattern +=   '|((.*)can not load translations from(.*))'
    pattern +=   '|((.*)Expected response code 200 Error for(.*))'
    pattern +=   '|((.*): java\.lang\.NoClassDefFoundError:(.*))'
    pattern +=   '|((.*)Syntax error(.*)unexpected(.*))'
    pattern +=   '|((.*)No such file or directory(.*)\(Errno::ENOENT\))'
    pattern +=   '|((.*)Exec format error(.*)\(Errno::ENOEXEC\))'
    pattern +=   '|((.*):[0-9]+:in (.*):\s*java\.lang\.(.*)Exception)'
    pattern +=   '|((.*)command not found(.*))'
    pattern +=   '|((.*)invalid option)'
    pattern +=   '|((.*)resolve to a path with no (.*) file for project(.*))'
    pattern +=   '|((.*)Hubs service excludes enterprises without latitude or longitude FAILED(\r)?\n(.*))'
    pattern +=   '|((.*)Reporting when all resources are loaded returns true when Enterprise and EnterpriseFee are loaded FAILED(\r)?\n(.*))'
    pattern +=   '|((.*)does not know where your (.*) file is)'
    pattern +=   '|((.*)version has changed(.*)\(RuntimeError\))'
    pattern +=   '|((.*)was found, but could not be parsed)'
    pattern +=   '|((.*)file not found)'
    pattern +=   '|((.*): image not found)'
    pattern += ')'

    for result in re.findall(pattern, log, re.IGNORECASE):
        if result[0]:
            msg = re.sub('0[xX][0-9a-fA-F]+', '0X', result[0])
            if msg not in msgs:
                msgs.append(msg)
    if len(msgs) > 0:
        return msgs

    ##======= Unexpected errors =======##
    pattern  = '('
    pattern +=   '([1-9][0-9]* steps \(([0-9]+ skipped, )?[1-9][0-9]* pending, [0-9]+ passed\))'
    pattern +=   '|(Coverage (.*) is below the expected minimum coverage (.*))'
    pattern +=   '|(FATAL: no bucket name given)'
    pattern +=   '|(could not open file(.*))'
    pattern +=   '|(\[ERROR\] (.*) Prefer (.*))'
    pattern +=   '|(fatal: repository(.*)does not exist)'
    pattern +=   '|(error: (.*) does not exist)'
    pattern +=   '|(warning: already initialized constant (.*))'
    pattern +=   '|(You are trying to install in deployment mode)'
    pattern +=   '|(What went wrong:(\r)?\nGradle (.*) requires Java (.*) or later to run)'
    pattern +=   '|(What went wrong:(\r)?\nCircular dependency between the following tasks:)'
    pattern +=   '|(Could not (find|resolve)(.*)(\r)?\n(.*)Required by)'
    pattern +=   '|(Project with path (.*) could not be found in project (.*))'
    pattern +=   '|(WARN\s+TCPServer Error: Address already in use)'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)+Command failed with status \([0-9]+\):(.*))'
    pattern +=   '|(rake aborted!(\r)?\n(.*)Coverage must be at least (.*) but was (.*))'
    pattern +=   '|(configure: error: (.*) const and volatile are mandatory)'
    pattern +=   '|(Starting database(.*)\[\[: not found)'
    pattern +=   '|(curl: \(7\) couldn\'t connect to host)'
    pattern +=   '|(curl: \(55\) SSL_write(.*))'
    pattern +=   '|(curl: \(52\) Empty reply from server)'
    pattern +=   '|(curl: \(35\) Unknown SSL protocol error in connection to(.*))'
    pattern +=   '|(curl: no URL specified!)'
    pattern +=   '|(Error while loading (.*) gem)'
    pattern +=   '|(The bundle currently has (.*) locked at(.*))'
    pattern +=   '|(rake aborted!(\r)?\n((\r)?\n)?ruby(.*)failed)'
    pattern +=   '|(The path(.*)does not exist(.*)((\r)?\n)+install: (.*) returned false)'
    pattern +=   '|(The command(.*)exited with 13 )'
    pattern +=   '|(The command(.*)exited with 18 )'
    pattern +=   '|(sudo: must be setuid root)'
    pattern +=   '|(KeyError: \((.*)\))'
    pattern +=   '|(FAILURE: Failed to load (.*) exit code (.*))'
    pattern +=   '|(diff: (.*) No such file or directory)'
    pattern +=   '|(: invalid multibyte escape:(.*)\(RegexpError\))'
    pattern +=   '|(: invalid multibyte escape:(.*)\(RegexpError\))'
    pattern +=   '|(Could not use ruby/gemset from the project file, try (.*))'
    pattern +=   '|(Could not create Neo4j session)'
    pattern +=   '|(BUILD FAILED(\r)?\nTarget (.*) does not exist in the project(.*))'
    pattern +=   '|(BUILD FAILED(\r)?\n(.*)does not exist)'
    pattern +=   '|(BUILD FAILED(\r)?\n(.*)SQL(.*)Exception(.*))'
    pattern +=   '|(BUILD FAILED(\r)?\n(.*)Could not find file(.*))'
    pattern +=   '|(BUILD FAILED(\r)?\n(.*)The element type(.*))'
    pattern +=   '|(BUILD FAILED(\r)?\n(.*)Issue when loading the full project)'
    pattern +=   '|(BUILD FAILED(?s:.)*((doesn\'t exist)|(does not exist)))'
    pattern +=   '|(This migration does not yet support MySQL(.*))'
    pattern +=   '|(Flay total is now (.*), but expected (.*))'
    pattern +=   '|([1-9][0-9]* chunk(s)? have a duplicate mass > [1-9][0-9]*)'
    pattern +=   '|([1-9][0-9]* method(s) have a flog complexity > [1-9][0-9]*)'
    pattern +=   '|([1-9][0-9]* warning(s)?:((\r)?\n(.*))+([1-9][0-9]* total warning(s)?)?(\r)?\nrake aborted!(\r)?\nSmells found!(.*))'
    pattern +=   '|(AllCops/Excludes was renamed to AllCops/Exclude)'
    pattern +=   '|(Error:(.*)(\r)?\nrake aborted!(\r)?\nError compiling)'
    pattern +=   '|(Doc build produced errors:)'
    pattern +=   '|(Do not know how to find binary for(.*)(\r)?\n(\r)?\nThe command(.*)exited with 1)'
    pattern +=   '|(ERR! Test failed(.*))'
    pattern +=   '|(ERR! Failed at the(.*))'
    pattern +=   '|(Rails (.*) requires to run on Ruby (.*) or newer)'
    pattern +=   '|(bundler: command not found: (.*))'
    pattern +=   '|(sh: Can\'t open (.*))'
    pattern +=   '|(sh:(.*)can\'t(.*))'
    pattern +=   '|(make:(.*)Error (1|2))'
    pattern +=   '|(Please run \./configure first)'
    pattern +=   '|(Error: Permission denied(.*))'
    pattern +=   '|(In order to execute tasks please install(.*))'
    pattern +=   '|(Exception:(\r)?\n\s*No parser configured for(.*))'
    pattern +=   '|(warning: singleton on non-persistent Java type(.*))'
    pattern +=   '|(Import of (.*) Failed: No module named (.*))'
    pattern +=   '|(The (.*) is not permitted (.*))'
    pattern +=   '|(BUILD FAILED(\r)?\n(.*)is missing)'
    pattern +=   '|(Error running(.*))'
    pattern +=   '|(\[vdso\]Aborted)'
    pattern +=   '|(\[ERROR\] Making output directory)'
    pattern +=   '|(before_script:(.*)returned false)'
    pattern +=   '|(after_script:(.*)returned false)'
    pattern += ')'
    
    for result in re.findall(pattern, log, re.IGNORECASE):
        if result[0]:
            msg = re.sub('0[xX][0-9a-fA-F]+', '0X', result[0])
            if msg not in msgs:
                msgs.append(msg)
    if len(msgs) == 0:
        if 'The command "export DISPLAY=:99.0 && RUBYOPT=W0 bundle exec rake 2> /dev/null" exited with 1' in log:
            msgs.append('The command "export DISPLAY=:99.0 && RUBYOPT=W0 bundle exec rake 2> /dev/null" exited with 1')
        elif re.search('Offen(s|c)es:(?s:.)*[1-9][0-9]* files inspected, (1|2|3) offen(s|c)e(s)? detected', log, re.IGNORECASE):
            result = re.search('Offen(s|c)es:(?s:.)*[1-9][0-9]* files inspected, [1-9][0-9]* offen(s|c)e(s)? detected', log, re.IGNORECASE)
            if result[0]:
                msg = re.sub('0[xX][0-9a-fA-F]+', '0X', result[0])
                msgs.append(msg)
        elif re.search('[1-9][0-9]* files inspected, [1-9][0-9]* offen(s|c)e(s)? detected', log, re.IGNORECASE):
            result = re.search('[1-9][0-9]* files inspected, [1-9][0-9]* offen(s|c)e(s)? detected', log, re.IGNORECASE)
            if result[0]:
                msg = re.sub('0[xX][0-9a-fA-F]+', '0X', result[0])
                msgs.append(msg)
        elif (re.search('ENOTFOUND(.*)Package angular-truncate not found', log)
          and log.rfind('Package angular-truncate not found') > log.rfind('failed. Retrying, 3 of 3')):
            result = re.search('ENOTFOUND(.*)Package angular-truncate not found', log, re.IGNORECASE)
            if result[0]:
                msg = re.sub('0[xX][0-9a-fA-F]+', '0X', result[0])
                msgs.append(msg)
        elif (re.search('ERR! Error: version not found(.*)', log)
          and log.rfind('ERR! Error: version not found') > log.rfind('failed. Retrying, 3 of 3')):
            result = re.search('ERR! Error: version not found(.*)', log, re.IGNORECASE)
            if result[0]:
                msg = re.sub('0[xX][0-9a-fA-F]+', '0X', result[0])
                msgs.append(msg)
        elif re.search('java\.lang\.NullPointerException', log, re.IGNORECASE):
            result = re.search('java\.lang\.NullPointerException', log, re.IGNORECASE)
            if result[0]:
                msg = result[0]
                msgs.append(msg)
        elif re.search('==> FAILED', log, re.IGNORECASE):
            result = re.search('==> FAILED', log, re.IGNORECASE)
            if result[0]:
                msg = result[0]
                msgs.append(msg)

        ##
        ## In the first round of log analysis, the below code should be commented to identify the specific error messages
		## Then, after in the next passes, it should be uncommented to capture the general error messages
        ##
        
        '''
		elif re.search('(ruby|rbx):(.*)failed', log, re.IGNORECASE):
            result = re.search('(ruby|rbx):(.*)failed', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])                
        elif re.search('/(.*)failed', log, re.IGNORECASE):
            result = re.search('/(.*)failed', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
        elif re.search('rake aborted!(\r)?\n((\r)?\n)?(.*)failed', log, re.IGNORECASE):
            result = re.search('rake aborted!(\r)?\n((\r)?\n)?(.*)failed', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])      
        elif re.search('Rails build FAILED(\r)?\nFailed component(.*)', log, re.IGNORECASE):
            result = re.search('Rails build FAILED(\r)?\nFailed component(.*)', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])    
        elif re.search('Methods exceeded maximum allowed ABC complexity \([1-9][0-9]*\)', log, re.IGNORECASE):
            result = re.search('Methods exceeded maximum allowed ABC complexity \([1-9][0-9]*\)', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
        elif re.search('Class and Module definitions require explanatory comments on previous line \([1-9][0-9]*\)', log, re.IGNORECASE):
            result = re.search('Class and Module definitions require explanatory comments on previous line \([1-9][0-9]*\)', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
        elif re.search('The command(.*)diff(.*) failed and exited with [1-9][0-9]*', log, re.IGNORECASE):
            result = re.search('The command(.*)diff(.*) failed and exited with [1-9][0-9]*', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
        elif re.search('The command (.*) exited with(.*)', log, re.IGNORECASE):
            result = re.search('The command (.*) exited with(.*)', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
        elif re.search('rake aborted!(\r)?\n((\r)?\n)?(.*)', log, re.IGNORECASE):
            result = re.search('rake aborted!(\r)?\n((\r)?\n)?(.*)', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
        elif re.search('(.*)requires(.*) \(hint:(.*)', log, re.IGNORECASE):
            result = re.search('(.*)requires(.*) \(hint:(.*)', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
        elif re.search('(install|before_script):(.*)returned false', log, re.IGNORECASE):
            result = re.search('(install|before_script):(.*)returned false', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
        elif re.search('line(.*)Aborted(.*)', log, re.IGNORECASE):
            result = re.search('line(.*)Aborted(.*)', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
        elif re.search('An exception occurred running(.*)(\r)?\n((\r)?\n)?(.*)', log, re.IGNORECASE):
            result = re.search('An exception occurred running(.*)(\r)?\n((\r)?\n)?(.*)', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
        elif re.search('No python interpreter found on the path. Python will not work!', log, re.IGNORECASE):
            result = re.search('No python interpreter found on the path. Python will not work!', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
        elif re.search('Update (.*) ... Failed', log, re.IGNORECASE):
            result = re.search('Update (.*) ... Failed', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
        elif re.search('Failure/Error:(.*)', log, re.IGNORECASE):
            result = re.search('Failure/Error:(.*)', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
        elif re.search('If you want to run these specs and need the credentials, contact', log, re.IGNORECASE):
            result = re.search('If you want to run these specs and need the credentials, contact', log, re.IGNORECASE)
            if result[0]:
                msgs.append(result[0])
		'''
    return msgs
               
#==============================================================================================================
if __name__ == '__main__':
    start = time.time()
    automated_log_analysis()
    end = time.time()
    elapsed = end - start
    print("Automated log analysis took [[", elapsed/60/60, "]] hours")

#==============================================================================================================