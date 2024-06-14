import csv
import os
import numpy as np

#==============================================================================================================
def write_build_data(csvwriter, csvwriter2, build_data, label):
    csvwriter.writerow([build_data[0]["gh_repository_name"], build_data[0]["gh_project_name"], build_data[0]["git_branch"], build_data[0]["build_id"], label])
    for job in build_data:
        csvwriter2.writerow([job["gh_repository_name"], job["gh_project_name"], job["git_branch"], job["build_id"], job["job_id"], job["job_label"], job["allow_failure"].title(), label, job["LANG"], job["ENV"]])

#==============================================================================================================
def is_a_cascading_breakage(prev_build, curr_build):
    if len(curr_build) != len(prev_build): # Check number of jobs
        return False
    else:
        for i in range(len(curr_build)):
            if curr_build[i]["job_status"] != prev_build[i]["job_status"]:
                return False
            else:
                if curr_build[i]["job_label"] != prev_build[i]["job_label"]:
                    return False
                else:
                    if curr_build[i]["allow_failure"].title() != prev_build[i]["allow_failure"].title():
                        return False
                    else:
                        if curr_build[i]["no_of_error_msgs"] != prev_build[i]["no_of_error_msgs"]:
                            return False
                        else:
                            if curr_build[i]["breakage_messages"] != prev_build[i]["breakage_messages"]:
                                return False
        return True

#==============================================================================================================
def look_ahead_to_get_consecutively_passed_builds_in_same_branch(list, start_index, repository_name, branch, build_id, max):
    start_fetching_following_builds = False
    indx = start_index
    max_rows = max
    list_of_builds = []
    branch_found = False
    while True:
        indx += 1
        if indx < max_rows:
            if repository_name == list[indx]["gh_repository_name"] and branch == list[indx]["git_branch"]:
                branch_found = True
                if build_id == list[indx]["build_id"]:
                    start_fetching_following_builds = True
                if start_fetching_following_builds:
                    if list[indx]["build_status"] == "passed":
                        build_jobs_list = [list[indx]]
                        for jobs in range(int(list[indx]["tr_num_jobs"])-1):
                            indx += 1
                            build_jobs_list.append(list[indx])
                        list_of_builds.append(build_jobs_list)
                        #break # only the first passed build after failure
            else:
                if branch_found:
                    break
                else:
                    continue
        else:
            break
    return list_of_builds

#==============================================================================================================
def identify_environmental_breakages_at_build_level(source_path, num):
    global available_builds
    input_file = source_path
    reader = csv.DictReader(open(input_file, newline='', encoding="latin-1"))

    i                  		      = 0
    first_row                     = True
    prev_project                  = ""
    prev_repository               = ""
    prev_branch                   = ""
    last_project                  = ""
    last_repository               = ""
    last_branch                   = ""
    prev_build_id                 = ""
    num_allow_failure             = 0
    num_noisy_jobs                = 0
    prj_environmental_breakages   = 0
    totl_prj_broken_builds        = 0
    totl_prj_builds    		      = 0
    totl_prj_brkn_jobs 		      = 0

    build_num_strict_jobs         = 0
    build_passed_jobs             = 0
    build_canceled_jobs           = 0
    build_jobs_list               = []
    prj_jobs_passed_but_build_broken = 0
    total_jobs_passed_but_build_broken = 0
    projects_with_jobs_passed_but_build_broken = 0

    csvfile   = open('dataset/builds_data/build_labels_after_criterion_1.csv', 'w', newline='', encoding="utf8")
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow (["gh_repository_name", "gh_project_name", "git_branch", "build_id", "build_label_criterion_1"])

    csvfile2   = open('dataset/builds_data/build_jobs_labels_after_criterion_1.csv', 'w', newline='', encoding="utf8")
    csvwriter2 = csv.writer(csvfile2)
    csvwriter2.writerow(["gh_repository_name", "gh_project_name", "git_branch", "build_id", "job_id", "job_label_criterion_1", "allow_failure", "build_label_criterion_1"])
    
    csvfile3   = open('dataset/builds_data/builds_with_jobs_passed_but_build_broken_'+num+'.csv', 'w', newline='', encoding="utf8")
    csvwriter3 = csv.writer(csvfile3)
    csvwriter3.writerow(["gh_repository_name", "build_id", "num_strict_jobs", 'build_label', 'no_of_error_msgs', 'breakage_messages', 'category', 'sub_category', 'examples'])
    
    for row in reader:
        repository_name = row["gh_repository_name"]
        project_name    = row["gh_project_name"]
        branch          = row["git_branch"]
        build_status    = row["build_status"]
        build_id        = row["build_id"]
        job_id          = row["job_id"]
        job_label       = row["job_label"]
        allow_failure   = row["allow_failure"].title()
        
        if repository_name != prev_repository:
            if prev_project != "":
                i += 1
                print("--", '{0: <3}'.format(i), ":", '{0: <43}'.format(prev_project), '{0: <5}'.format(prj_environmental_breakages), "out of", '{0: <5}'.format(totl_prj_broken_builds-1), "broken builds - of", '{0: <5}'.format(totl_prj_builds), "total builds")
                
                if prj_jobs_passed_but_build_broken > 0:
                    total_jobs_passed_but_build_broken += prj_jobs_passed_but_build_broken
                    projects_with_jobs_passed_but_build_broken += 1

            prev_project = project_name
            prev_repository = repository_name
            prj_environmental_breakages = 0
            totl_prj_broken_builds = 0
            totl_prj_builds = 0
            totl_prj_brkn_jobs = 0
            num_allow_failure = 0
            prj_jobs_passed_but_build_broken = 0

        if branch != prev_branch:
            prev_branch        = branch

        if build_id != prev_build_id:
            totl_prj_builds += 1
            if not first_row:
                if build_passed_jobs == build_num_strict_jobs: 
                    if prev_build_status not in ["passed", "canceled"]:
                        csvwriter3.writerow([repository_name, build_id, build_num_strict_jobs, "environmental_breakage", 0, "[ENVIRONMENTAL BREAKAGE] jobs passed but build broken", "10-Buggy build status", "10.01-Jobs passing but build broken"])
                        prj_jobs_passed_but_build_broken += 1
                        build_label = "environmental_breakage"
                    else:
                        build_label = prev_build_status
                else:
                    if build_developer_breakage == False and num_noisy_jobs > 0:
                        prj_environmental_breakages  += 1
                        build_label = "environmental_breakage"
                        totl_prj_broken_builds += 1
                    elif build_developer_breakage == True:
                        build_label = "developer_breakage"
                        totl_prj_broken_builds += 1
                    else:
                        build_label = prev_build_status

                csvwriter.writerow([last_repository, last_project, last_branch, prev_build_id, build_label])
                for job in build_jobs_list:
                    csvwriter2.writerow([last_repository, last_project, last_branch, prev_build_id, job[0], job[1], job[2], build_label])                
        
            first_row                = False
            build_developer_breakage = False
            last_project             = prev_project
            last_repository          = prev_repository
            last_branch              = prev_branch
            prev_build_status        = build_status
            prev_build_id            = build_id
            num_allow_failure        = 0
            num_noisy_jobs           = 0
            build_num_strict_jobs    = 0
            build_passed_jobs        = 0
            build_jobs_list          = []

        build_jobs_list.append([job_id, job_label, allow_failure])
        if job_label == "environmental_breakage" or job_label == "suspicious_breakage" or job_label == "developer_breakage":
            totl_prj_brkn_jobs += 1
        if allow_failure == "False":
            build_num_strict_jobs += 1
            if job_label == "developer_breakage":
                build_developer_breakage = True
            elif job_label == "environmental_breakage" or job_label == "suspicious_breakage":
                num_noisy_jobs += 1
            elif job_label == "passed":
                build_passed_jobs += 1
            elif job_label == "canceled":
                build_canceled_jobs += 1
        else:
            num_allow_failure  += 1

    if build_passed_jobs == build_num_strict_jobs: 
        if prev_build_status not in ["passed", "canceled"]:
            csvwriter3.writerow([repository_name, build_id, build_num_strict_jobs, "environmental_breakage", 0, "[ENVIRONMENTAL BREAKAGE] jobs passed but build broken", "10-Buggy build status", "10.01-Jobs passing but build broken"])
            prj_jobs_passed_but_build_broken += 1
            build_label = "environmental_breakage"

    else:
        if (build_developer_breakage == False and num_noisy_jobs > 0):
            prj_environmental_breakages  += 1
            build_label = "environmental_breakage"
            totl_prj_broken_builds += 1
        elif build_developer_breakage == True:
            build_label = "developer_breakage"
            totl_prj_broken_builds += 1
        else:
            build_label = prev_build_status

    csvwriter.writerow([last_repository, last_project, last_branch, prev_build_id, build_label])
    for job in build_jobs_list:
        csvwriter2.writerow([last_repository, last_project, last_branch, prev_build_id, job[0], job[1], job[2], build_label])                
    csvfile.close()
    csvfile2.close()
    csvfile3.close()
    
    print("--", '{0: <3}'.format(i+1), ":", '{0: <43}'.format(prev_project), '{0: <5}'.format(prj_environmental_breakages-1), "out of", '{0: <5}'.format(totl_prj_broken_builds-1), "broken builds - of", '{0: <5}'.format(totl_prj_builds), "total builds")
    if prj_jobs_passed_but_build_broken > 0:
        total_jobs_passed_but_build_broken += prj_jobs_passed_but_build_broken
        projects_with_jobs_passed_but_build_broken += 1
    print("Total jobs passed but build broken:", total_jobs_passed_but_build_broken)
    print("Projects with passed but build broken:", projects_with_jobs_passed_but_build_broken)

    print("===============================================================================================================")

#==============================================================================================================
def identify_cascading_breakages_at_build_level(source_path, num, max):
    global available_builds
    input_file = source_path
    reader = csv.DictReader(open(input_file, newline='', encoding="latin-1"))

    i                       = 0
    first_row               = True
    prev_project            = ""
    prev_repository         = ""
    prev_branch             = ""
    last_project            = ""
    last_repository         = ""
    last_branch             = ""
    prev_build_id           = ""
    prj_cascading_breakages = 0
    totl_prj_broken_builds  = 0
    totl_prj_builds         = 0

    build1_jobs_list = []
    build2_jobs_list = []

    csvfile   = open('dataset/builds_data/build_labels_after_criterion_2.csv', 'w', newline='', encoding="utf8")
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow (["gh_repository_name", "gh_project_name", "git_branch", "build_id", "build_label_criterion_2"])

    csvfile2   = open('dataset/builds_data/build_jobs_labels_after_criterion_2.csv', 'w', newline='', encoding="utf8")
    csvwriter2 = csv.writer(csvfile2)
    csvwriter2.writerow(["gh_repository_name", "gh_project_name", "git_branch", "build_id", "job_id", "job_label_criterion_2", "allow_failure", "build_label_criterion_2"])
    
    index    = 1
    max_rows = max
    next_row = reader.__next__()
    while index < max_rows:
        row = next_row
        repository_name   = row["gh_repository_name"]
        project_name      = row["gh_project_name"]
        branch            = row["git_branch"]
        build_id          = row["build_id"]
        build_label       = row["build_status"]
        tr_num_jobs       = row["tr_num_jobs"]
        job_id            = row["job_id"]
        job_number        = row["job_number"]
        job_label         = row["job_label"]
        allow_failure     = row["allow_failure"].title()
        queue             = row["queue"]
        lang              = row["LANG"]
        env               = row["ENV"]
        no_of_error_msgs  = row["no_of_error_msgs"]
        breakage_messages = row["breakage_messages"]
        
        if repository_name != prev_repository:
            if prev_project != "":
                i += 1
                print("--", '{0: <3}'.format(i), ":", '{0: <43}'.format(prev_project), '{0: <5}'.format(prj_cascading_breakages), "out of", '{0: <5}'.format(totl_prj_broken_builds), "broken builds - of", '{0: <5}'.format(totl_prj_builds), "total builds")

            prev_project       = project_name
            prev_repository    = repository_name
            prev_branch        = ""
            prj_cascading_breakages   = 0
            totl_prj_broken_builds = 0
            totl_prj_builds    = 0
            first_row          = True

        if branch != prev_branch:
            prev_branch        = branch
            first_row          = True

        prev_build_id = build_id
        build1_jobs_list = [row]
        for jobs in range(int(tr_num_jobs)-1):
            index += 1
            next_row = reader.__next__()
            build1_jobs_list.append(next_row)

        if build_label == "passed" or build_label == "canceled": ## Skip passed and canceled builds
            write_build_data(csvwriter, csvwriter2, build1_jobs_list, build_label)
            index += 1
            if index < max_rows:
                totl_prj_builds += 1
                next_row = reader.__next__()
                continue
        else:
            ## Compare broken builds in the sequence of breakages
            while True:
                totl_prj_builds += 1
                write_build_data(csvwriter, csvwriter2, build1_jobs_list, build_label)
                index += 1
                totl_prj_broken_builds += 1
                if index < max_rows:
                    next_build = reader.__next__()
                    if repository_name != next_build["gh_repository_name"] or branch != next_build["git_branch"] or next_build["build_status"] == "passed":
                        next_row = next_build
                        break

                    build2_jobs_list =[next_build]
                    for jobs in range(int(next_build["tr_num_jobs"])-1):
                        index += 1
                        next_row = reader.__next__()
                        build2_jobs_list.append(next_row)
                        
                    if is_a_cascading_breakage(build1_jobs_list, build2_jobs_list):
                        build_label = "cascading_breakage"
                        prj_cascading_breakages += 1
                    else:
                        build_label = "broken"
                    
                    build_id = build2_jobs_list[0]["build_id"]
                    repository_name = build2_jobs_list[0]["gh_repository_name"]
                    branch = build2_jobs_list[0]["git_branch"]
                    build1_jobs_list = build2_jobs_list
                else:
                    break

    csvfile.close()
    csvfile2.close()
    print("--", '{0: <3}'.format(i+1), ":", '{0: <43}'.format(prev_project), '{0: <5}'.format(prj_cascading_breakages-1), "out of", '{0: <5}'.format(totl_prj_broken_builds), "broken builds - of", '{0: <5}'.format(totl_prj_builds), "total builds")
    print("===============================================================================================================")

#==============================================================================================================
def identify_allowed_breakages_at_build_level(source_path, num, max):
    global available_builds
    input_file = source_path
    reader = csv.DictReader(open(input_file, newline='', encoding="latin-1"))

    csv_file = open(input_file, newline='', encoding="utf8")
    sub_reader = csv.DictReader(csv_file)
    list_of_rows = [r for r in sub_reader]
    csv_file.close()

    first_row          = True
    prev_lang          = ""
    prev_project       = ""
    prev_repository    = ""
    prev_branch        = ""
    last_project       = ""
    last_repository    = ""
    last_branch        = ""
    prev_build_id      = ""
    totl_prj_broken_builds = 0
    prj_allowed_breakages = 0
    totl_prj_builds = 0
    totl_builds_affected_by_excluded_jobs = 0
    totl_builds_affected_by_transfered_jobs = 0
    totl_builds_affected_by_both_transfered_and_excluded_jobs = 0
    i                  = 0

    build1_jobs_list    = []
    build2_jobs_list    = []
    broken_jobs_platforms_dic  = dict()
    excluded_jobs_dic   = dict()
    transfered_jobs_dic = dict()
    
    csvfile   = open('dataset/builds_data/build_labels_after_criterion_3.csv', 'w', newline='', encoding="utf8")
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow (["gh_repository_name", "gh_project_name", "git_branch", "build_id", "build_label_criterion_3"])

    csvfile2   = open('dataset/builds_data/build_jobs_labels_after_criterion_3.csv', 'w', newline='', encoding="utf8")
    csvwriter2 = csv.writer(csvfile2)
    csvwriter2.writerow(["gh_repository_name", "gh_project_name", "git_branch", "build_id", "job_id", "job_label_criterion_3", "allow_failure", "build_label_criterion_3"])
    
    csvfile3   = open('dataset/builds_data/builds_where_jobs_are_marked_allow_failure_'+num+'.csv', 'w', newline='', encoding="utf8")
    csvwriter3 = csv.writer(csvfile3)
    csvwriter3.writerow(['gh_repository_name', 'git_branch', 'build_id', 'build_link', 'reason', 'category'])
    
    index    = 1
    max_rows = max
    next_row = reader.__next__()
    builds_where_jobs_are_marked_allow_failure = {}
    while index < max_rows:
        row = next_row
        repository_name   = row["gh_repository_name"]
        project_name      = row["gh_project_name"]
        prog_lang         = row["gh_lang"]
        branch            = row["git_branch"]
        build_id          = row["build_id"]
        build_label       = row["build_status"]
        tr_num_jobs       = row["tr_num_jobs"]
        job_id            = row["job_id"]
        job_number        = row["job_number"]
        job_label         = row["job_label"]
        allow_failure     = row["allow_failure"].title()
        job_state         = row["job_state"]
        queue             = row["queue"]
        lang              = row["LANG"]
        env               = row["ENV"]
        no_of_error_msgs  = row["no_of_error_msgs"]
        breakage_messages = row["breakage_messages"]
        
        if repository_name != prev_repository:
            if prev_repository != "":
                i += 1
                print("--", '{0: <3}'.format(i), ":", '{0: <43}'.format(prev_repository), '{0: <5}'.format(prj_allowed_breakages), "out of", '{0: <5}'.format(totl_prj_broken_builds), "broken builds - of", '{0: <5}'.format(totl_prj_builds), "total builds -- ", prev_lang)

            prev_project           = project_name
            prev_repository        = repository_name
            first_row              = True
            totl_prj_broken_builds = 0
            prj_allowed_breakages  = 0
            totl_prj_builds        = 0

        if branch != prev_branch:
            prev_branch        = branch
            first_row          = True

        prev_lang = prog_lang
        prev_build_id = build_id
        build1_jobs_list = [row]
        job_platform_identifier = repository_name+"@"+branch+"@"+lang+"@"+env
        totl_prj_builds += 1
        broken_jobs_platforms_dic[job_platform_identifier] = 0
        for jobs in range(int(tr_num_jobs)-1):
            index += 1
            next_row = reader.__next__()
            build1_jobs_list.append(next_row)
            if row["build_id"] != next_row["build_id"] or row["gh_repository_name"] != next_row["gh_repository_name"]:
                print("--- missing jobs records for build:", row["build_id"], " @ ", row["gh_repository_name"])
                quit()

        if build_label == "passed" or build_label == "canceled": ## Skip passed and canceled builds
            write_build_data(csvwriter, csvwriter2, build1_jobs_list, build_label)
            index += 1
            if index < max_rows:
                next_row = reader.__next__()
                continue
        else:
            ## Compare broken builds in the sequence of breakages
            totl_prj_broken_builds += 1
            list_of_builds = look_ahead_to_get_consecutively_passed_builds_in_same_branch(list_of_rows, index-len(build1_jobs_list)-1, repository_name, branch, build_id, max)
            num_broken_jobs = 0
            num_excluded_jobs = 0
            num_transfered_jobs = 0
            transfered_from_job_ids = []
            excluded_from_job_ids = []
            transfered_jobs_build_ids = []
            excluded_jobs_build_ids = []
            transfered_to_job_ids = []
            if len(list_of_builds) > 0:
                for job in build1_jobs_list:
                    if job["job_state"] == "broken" and job["allow_failure"].title() == "False":
                        job_platform_identifier = job["gh_repository_name"]+"@"+job["git_branch"]+"@"+job["LANG"]+"@"+job["ENV"]
                        found_fixed = False
                        found_broken = False
                        found_allow_failure = False
                        num_broken_jobs += 1
                        for inner_build in list_of_builds:
                            for inner_job in inner_build:
                                if inner_job["LANG"] == job["LANG"] and inner_job["ENV"] == job["ENV"]:
                                    if inner_job["job_state"] == "passed":
                                        if inner_job["allow_failure"].title() == "False":
                                            found_fixed = True
                                            break
                                        else:
                                            found_allow_failure = True
                                            transfered_from_job_ids.append(job["job_id"])
                                            transfered_to_job_ids.append(inner_job["job_id"])
                                            if job_platform_identifier not in builds_where_jobs_are_marked_allow_failure.keys():
                                                builds_where_jobs_are_marked_allow_failure[job_platform_identifier] = [inner_job["gh_repository_name"], inner_job["git_branch"], inner_job["build_id"]]
                                    else:
                                        found_broken = True
                                        if inner_job["allow_failure"].title() == "True":# and inner_job["job_state"] == "broken":
                                            found_allow_failure = True
                                            transfered_from_job_ids.append(job["job_id"])
                                            transfered_to_job_ids.append(inner_job["job_id"])
                                            if job_platform_identifier not in builds_where_jobs_are_marked_allow_failure.keys():
                                                builds_where_jobs_are_marked_allow_failure[job_platform_identifier] = [inner_job["gh_repository_name"], inner_job["git_branch"], inner_job["build_id"]]
                                            csvfile3.flush()
                        if found_allow_failure:
                            num_transfered_jobs += 1
                            if (job_platform_identifier) not in transfered_jobs_dic:
                                transfered_jobs_dic[job_platform_identifier] = 1
                            else:
                                transfered_jobs_dic[job_platform_identifier] = transfered_jobs_dic[job_platform_identifier] + 1
                        elif not found_fixed:
                            num_excluded_jobs += 1
                            excluded_from_job_ids.append(job["job_id"])
                            if job_platform_identifier not in excluded_jobs_dic:
                                excluded_jobs_dic[job_platform_identifier] = 1
                            else:
                                excluded_jobs_dic[job_platform_identifier] = excluded_jobs_dic[job_platform_identifier] + 1

            if num_broken_jobs == (num_excluded_jobs + num_transfered_jobs) and num_broken_jobs != 0:
                if num_transfered_jobs > 0 and num_excluded_jobs > 0:
                    totl_builds_affected_by_both_transfered_and_excluded_jobs += 1
                else:
                    if num_transfered_jobs > 0:
                        totl_builds_affected_by_transfered_jobs += 1
                    if num_excluded_jobs > 0:
                        totl_builds_affected_by_excluded_jobs += 1
    
                build_label = "allowed_breakage"
                prj_allowed_breakages += 1
            else:
                build_label = build_label

            write_build_data(csvwriter, csvwriter2, build1_jobs_list, build_label)
            index += 1
            if index < max_rows:
                next_row = reader.__next__()

    job_iden_builds = []
    for job_iden in builds_where_jobs_are_marked_allow_failure:
        job_details = builds_where_jobs_are_marked_allow_failure[job_iden]
        repo     = job_details[0]
        branch   = job_details[1]
        build_id = job_details[2]
        if build_id not in job_iden_builds:
            job_iden_builds.append(build_id)
            csvwriter3.writerow([repo, branch, build_id, "https://travis-ci.org/"+repo+"/builds/"+build_id, ""])

    csvfile.close()
    csvfile2.close()
    csvfile3.close()
	
    print("--", '{0: <3}'.format(i+1), ":", '{0: <43}'.format(prev_project), '{0: <5}'.format(prj_allowed_breakages-1), "out of", '{0: <5}'.format(totl_prj_broken_builds), "broken builds - of", '{0: <5}'.format(totl_prj_builds), "total builds -- ", prev_lang)
    print("=============================================================================================================")
    print("Affected builds by jobs transfered to allow failure:", totl_builds_affected_by_transfered_jobs)
    print("Affected builds by jobs that are later excluded:", totl_builds_affected_by_excluded_jobs)
    print("Affected builds by jobs that are either later excluded or transfered to allow failure:", totl_builds_affected_by_both_transfered_and_excluded_jobs)
    print("# Unique jobs platforms:", len(broken_jobs_platforms_dic))
    print("# Jobs transfered to allow failure:", len(transfered_jobs_dic))
    print("# Jobs excluded later on:", len(excluded_jobs_dic))
    builds_having_transfered_jobs = 0
    builds_having_excluded_jobs = 0
    for j in transfered_jobs_dic.keys():
        builds_having_transfered_jobs += int(transfered_jobs_dic[j])
    for j in excluded_jobs_dic.keys():
        builds_having_excluded_jobs += int(excluded_jobs_dic[j])
    print("# Builds having transfered jobs:", builds_having_transfered_jobs)
    print("# Builds having excluded jobs:", builds_having_excluded_jobs)
    #if prj_jobs_passed_but_build_broken > 0:
    #    print("--", '{0: <2}'.format(i+1), ":", '{0: <43}'.format(prev_project), prj_jobs_passed_but_build_broken)

#==============================================================================================================
max_jobs = 1928313

identify_environmental_breakages_at_build_level("dataset/builds_data/build_jobs_info_projects_all.csv")
identify_cascading_breakages_at_build_level("dataset/builds_data/build_jobs_info_projects_all.csv", max_jobs)
identify_allowed_breakages_at_build_level("dataset/builds_data/build_jobs_info_projects_all.csv", max_jobs)
