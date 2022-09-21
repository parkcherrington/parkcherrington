""" This script checks if a given survey is in all of the courses in a given
    semester.

    To run this script you will need:
    - a canvas API KEY
    - the qualtrics Survey ID (part of the URL that's like
                               `SV_aYwrUf4n5znh3X7`)
    - The term ID (If you don't know this, there is a help menu later on in the script)
    - The `Account_ID` (which is ALWAYS 31, the DCE sub-account)
    - the `enrollment_term_id` which is canvas' way of saying 20185, 20191
        - the `enrollment_term_id` is in the URL when you search for a course
          in Canvas (as is the account_id)

    Here are the main Survey IDs:
    - Learner Readiness Survey  `SV_9Mr45KbxLqfcJdb`
    - Mid-Course survey         `SV_1AN0abATTLYgzel`
    - End of Course Survey      `SV_aYwrUf4n5znh3X7`

    The following comment is for reference, but will need to be updated in
    future semesters:

    This script has two parts (takes about 5 minutes depending on the number of courses in a given term):
    1. Comb through all the courses in a given semester to look for each survey.
    2. Generate a report of needed changes and additions to survey pages amd send it to Joel and Enoch
    3. Once Joel and Enoch have signed off on the changes found in the script, this script will also carry out the needed changes in qualtrics

    The process that this script acheives actually requires the script to be run twice. The first time, to generate and send a report to Joel
    Hemingway and Enoch Hunsaker. We will run the script a second time once we hear back from them that the proposed changes are good to go. 
    This time, we will actually use the canvas API to make the changes in canvas. You will be asked to determine this partway through the script.

    It is my understanding that these are the semester IDs
    `enrollment_term_id` is the value we will be setting
        - Winter 2018: 49
        - Fall 2018: 50
        - Spring 2018: 51
        - Summer 2018: 52
        - Winter 2019: 53
"""

from datetime import datetime
import json
import os
import re
import requests as r
import sys
import time
import webbrowser as web
import pandas as pd
import win32com.client as win32


# fuzzywuzzy includes a warning to install python-Levenshtein, but it won't install and is not needed. So I ignore the warning
import warnings
warnings.filterwarnings("ignore")
from fuzzywuzzy import fuzz


'''CONSTANTS'''

API_URL = 'https://byu.instructure.com/api/v1'
Account_ID = 31
term_id = '52'
# API_KEY = input('Enter the Canvas API key below and type [ENTER]:\n')
API_KEY = '7407~5VEIbZvI3xnMrb6yc1eCq8rL6KLtlNDsUMXbO3sva6UaYgmzCvHwJihk2k30HnbN'
header = {'Authorization': 'Bearer ' + '%s' % API_KEY}

# Get current date
current_date = datetime.now()

'''DICTIONARIES'''

# List the possible survey types and their Qualtrics IDs here
survey_dict = {'1': ('Learner Readiness', 'SV_9Mr45KbxLqfcJdb'),
               '2': ('Mid-Course', 'SV_1AN0abATTLYgzel'),
               '3': ('End of Course', 'SV_aYwrUf4n5znh3X7'),
               '4': ('All', 'nothing')}


# Semesters/Terms Dictionary
request = r.get(API_URL +
                '/accounts/1/terms?per_page=50',
                headers=header)
json_request = request.json()
all_terms = {}
# Fill all_terms with semesters/terms
for term in json_request['enrollment_terms']:
    all_terms[term['id']] = {
        'name': term['name'],
        'start_date': term['start_at'],
        'end_date': term['end_at']
    }
    if term['start_at'] != None and term['end_at'] != None:
        all_terms[term['id']]['start_date'] = datetime.strptime(term['start_at'].split('T')[0], '%Y-%m-%d')
        all_terms[term['id']]['end_date'] = datetime.strptime(term['end_at'].split('T')[0], '%Y-%m-%d')

"""PROMPT USER FOR DESIRED SURVEY"""

# Print survey options
print("Please select which survey you want to check for:")
print('\nSurvey ID', 'Name', sep='\t')
print("-" * len('Survey ID'), "-" * len('Name'), sep='\t')
for k, v in survey_dict.items():
    print(k, v[0], sep='\t\t')
print()

# Prompt for survey ID
while True:
    try:
        survey_id = input('Enter the Survey ID and press [ENTER]: ')
        survey_name = survey_dict[survey_id][0]
        break
    except:
        print('\n' + 'ERROR: PLEASE ENTER A VALID ID' + '\n')

qualtrics_dict = {'Learner Readiness': 'SV_9Mr45KbxLqfcJdb',
                'Mid-Course': 'SV_1AN0abATTLYgzel',
                'End of Course': 'SV_aYwrUf4n5znh3X7'}

if survey_name != 'All':
    qualtrics_survey_id = qualtrics_dict[survey_name]

# Confirm selection
print('\n' + f'You\'ve selected: {survey_name} Surveys' + '\n')

# region
# # Print term/semester options
# print('Please select the desired semester/term:', '\n')

# # Print terms in table format
# print("AIM Code" + '\t' + "Name")
# print(len("AIM Code") * "-" + '\t' + len("Name") * "-")

# previous_term = None
# previous_term_printed = False

# for term_id in sorted(all_terms):
#     # Show previous semester and on
#     if all_terms[term_id]['start_date'] is not None:
#         if current_date <= all_terms[term_id]['end_date']:
#             if previous_term_printed is False:
#                 print(str(previous_term) + '\t\t' + all_terms[previous_term]['name'])
#                 previous_term_printed = True
                
#             print(str(term_id) + '\t\t' + all_terms[term_id]['name'])
        
#     previous_term = term_id
# print()
# endregion
# Prompt user for term id until valid term id is entered
for term in all_terms.keys():
    if all_terms[term]['start_date'] != None and all_terms[term]['end_date'] != None:
        if all_terms[term]['start_date'] < current_date:
            if all_terms[term]['end_date'] > current_date:
                current_term = all_terms[term]['name']
                print(f'Current term: {current_term}')
                print(f'Term code: {term}')
while True:
    try:
        # Prompt for Term/Semester ID, convert it to int
        term_id = input('Enter the AIM Code of the desired semester/term (type \'help\' to see a list): ')
        if term_id == 'help':
            print("AIM Code" + '\t' + "Name")
            print(len("AIM Code") * "-" + '\t' + len("Name") * "-")
            for k in all_terms.keys():
                print(k, all_terms[k]['name'], sep = '\t\t')
        term_id = int(term_id)
        term = all_terms[term_id]['name']
        break
    except:
        print('\n' + '***ERROR: PLEASE ENTER A VALID ID***' + '\n')
        print('To see possible survey IDs, enter \'help\'')

# Confirm selection
print('\n\n' + f'SELECTED TERM: {term}' + '\n\n')

payload = {'enrollment_term_id': f'{term_id}'}

time.sleep(.75)

'''Prompt user to determine what the script should do'''

while True:
    stage_input = input('Send a report to Joel and Enoch (1) or only generate a report (2): ')
    if stage_input == '1':
        send_email = True
        print('A report will be generated and will be emailed to Joel and Enoch.')
        break
    elif stage_input == '2':
        send_email = False
        print('A report will be generated, but no email will be sent.')
        break
    else:
        print('\nERROR: Please enter either 1 or 2')

print('Getting all courses...')

'''METHODS'''

def get_courses(account_id):
    """returns all the courses that are active in a given account.
    If you have more than 150 courses, make sure and set the counter to stop
    after more pages.
    account_id `31` is Continuing Education.
    """
    courses = []
    """
    'with_enrollments': 'True',
    'workflow_state': 'Available',
    'completed': 'False',
    'hide_enrollmentless_courses': 'True',
    'state[]': 'available'}
    """
    request = r.get(API_URL +
                    '/accounts/' +
                    str(account_id) +
                    '/courses?include[]=total_students',
                    params=payload, headers=header)

    while True:
        json_request = request.json()
        
        for course in json_request:
            if course['total_students'] != 0:
                courses.append((course['id'], course['name']))
        
        if 'last' in request.links:
            if request.links['current']['url'] == request.links['last']['url']:
                break
        
        request = r.get(request.links['next']['url'], headers=header)
    
    return courses

def get_modules(course_id):
    """ takes course_id, and name then all canvas modules associated with the
        given course_id. """

    modules = []

    request = r.get(API_URL +
                    '/courses/' +
                    str(course_id) +
                    '/modules?include[]=items',
                    headers=header)
    
    while True:
        json_request = request.json()

        for module in json_request:
            modules.append(module)
        
        if 'last' in request.links:
            if request.links['current']['url'] == request.links['last']['url']:
                break

        request = r.get(request.links['next']['url'], headers=header)

    return modules
def get_items_in_module(course_id, module_id):
    request = r.get(API_URL + '/courses/' + str(course_id) + '/modules/' + str(module_id) + '/items',
    headers = header)
     
    module_items = []
    while True:
        module_json = request.json()
        for item in module_json:
            module_items.append(item)
        
        if 'last' in request.links:
            if request.links['current']['url'] == request.links['last']['url']:
                break
        request = r.get(request.links['next']['url'])    
    return module_items

def get_pages(course_id):
    pages = []
    request = r.get(API_URL + 
    '/courses/' +
    str(course_id) +
    '/pages', headers = header)
    while True:
        pages_request = request.json()
        for page in pages_request:
            pages.append(page)
        if 'last' in request.links:
            if request.links['current']['url'] == request.links['last']['url']:
                break
        request = r.get(request.links['next']['url'], headers = header)
    return pages

# Kick off the dictionary that will become the excel sheet that will be sent to Enoch and Joel
csv_data = {
    'URL': [],
    'Course': [],
    'Status': [],
    'Action': [],
    'Survey': []
}

def add_to_df(df, URL, Course, Status, Action, Survey):
    df['URL'].append(URL)
    df['Course'].append(Course)
    df['Status'].append(Status)
    df['Survey'].append(Survey)
    df['Action'].append(Action)

# Kick off the dictionary that will be the input document for the 'Alter Surveys in Canvas' script
canvas_data = {
    'URL': [],
    'Course': [],
    'Course ID': [],
    'Item Name': [],
    'Item ID': [],
    'Page Type': [],
    'Status': [],
    'Survey': [],
}
# This will be after all the data is added in, to make it into the .csv file
canvas_columns = ['URL', 'Course', 'Course ID', 'Item Name', 'Item ID', 'Page Type', 'Status', 'Survey']
def add_to_canvas(URL, Course, course_id, Name, item_id, Status, Type, Survey):
    # Course ID is the 4 or 5 digit code that is in the URL. Lets the API know which course it is altering
    # Item Name is just so we know what item is being altered. Item_ID is for the API to know that
    # Status is not used by the API but it lets us know what is going on and what needs to be changed
    # Type is just the type of page that needs to change the survey it has. Only used in a few cases
    canvas_data['URL'].append(URL)
    canvas_data['Course'].append(Course)
    canvas_data['Course ID'].append(course_id)
    canvas_data['Item Name'].append(Name)
    canvas_data['Item ID'].append(item_id)
    canvas_data['Status'].append(Status)
    canvas_data['Page Type'].append(Type)
    canvas_data['Survey'].append(Survey)
    # Survey can only be one of the three string types


'''CODE TO BE EXECUTED'''
# Get a list of all the courses in the given semester (31 is the DCE sub-account)
courses = get_courses(31)
num_courses = len(courses)

print('Number of courses:', num_courses, '\n')

progress_bar_length = 40

# If we are checking for every survey, change the survey_name variable so that the script can repeat the next steps for every type of survey.
if survey_name == 'All':
    surveys = ['Mid-Course', 'End of Course']
else:
    surveys = [survey_name]

# retrieves all modules from all courses in given semester
for type in surveys:
    print(f'Checking for {type} surveys...')
    course_counter = 1
    qualtrics_survey_id = qualtrics_dict[type]

    for course_id, course_name in courses:
        modules = get_modules(course_id)
        link = f'https://byu.instructure.com/courses/{str(course_id)}/modules'
        good_match = False
        item_count = 0
        for module in modules:
            mod = dict(module)
            for item in mod['items']:
                item_count += 1
                item_type = item['type']
                # partial_ratio checks to see if the words in text A are anywhere in text B, no matter the position in text B
                partial_ratio = fuzz.partial_ratio(item['title'], type)
                # ratio does a direct comparison of text A and text B
                ratio = fuzz.ratio(item['title'], type)
                # If the module is an Adobe Connect Survey, contains a question mark (because these are usually
                # "Did you complete the survey?" modules and don't contain the survey), or is a subheader, ignore it
                if '?' in item['title'] or 'adobe' in item['title'].lower() or item_type == 'SubHeader':
                    pass
                elif partial_ratio in range(79, 101) and 'survey' in item['title'].lower():
                    good_match = True

                    # Set the link to be the link of the individual module
                    # ExternalUrls are different
                    if item_type == 'ExternalUrl':
                        link += f'/items/{item["id"]}'
                    elif 'html_url' in item:
                        link = item['html_url']
                    # after doing a partial_ratio check, do a direct comparison
                    if ratio in range(39, 101):
                        has_survey = []
                        survey_in_description = False

                        # set request URL
                        if 'url' in item:
                            json_request = r.get(item['url'], params=payload, headers=header).json()

                            # Quizzes are different, in that the survey is located either in the description or in the item['url']/questions
                            if item_type == 'Quiz':
                                if 'qualtrics' in json_request['description']:
                                    survey_in_description = True
                                else:
                                    json_request = r.get(item['url'] + '/questions', params=payload, headers=header).json()

                        # assign survey locations
                        if item_type == 'Page':
                            survey_location = json_request['body']
                        elif item_type == 'Assignment':
                            survey_location = json_request['description']
                        elif item_type == 'ExternalUrl':
                            survey_location = item['external_url']
                        elif item_type == 'Quiz':
                            if survey_in_description == True:
                                survey_location = json_request['description']
                            else:
                                if len(json_request) > 0:
                                    survey_location = json_request[0]['question_text']
                                else:
                                    survey_location = ''
                        else:
                            print('ERROR. This item type has not been allowed for in the code.')

                        # check to see if item has a Qualtrics survey.
                        has_survey = re.findall('qualtrics', survey_location)

                        # If it has a Qualtrics survey, check to see if item has the correct Qualtrics survey.
                        if has_survey:
                            has_correct_survey = re.findall(qualtrics_survey_id, survey_location)
                            for val in survey_dict.values():
                                if val[0] != type:
                                    has_wrong_survey = re.findall(val[1], survey_location)
                            if has_wrong_survey:
                                status = 'Wrong Qualtrics survey embedded in page'
                                print('Wrong survey id found!!')
                                add_to_canvas(URL = item['html_url'], Course = course_name, course_id = course_id,
                                name = item['title'], item_id = item['page_url'], Status = status, type = None, Survey = type)

                            # if the correct survey id is not found, add to update_survey array
                            if not has_correct_survey and not has_wrong_survey:
                                if item['type'] == 'Page':
                                    item_ID = item['page_url']
                                else:
                                    item_ID = None
                                    # Some courses embed the surveys within a quiz or assignment page so students can do them for credit.
                                    # In this case, just want to open the page to manually take care of it, so no item ID is added here.
                                    link = f"https://byu.test.instructure.com/courses/{course_id}/modules/items/{item['id']}"
                                add_to_canvas(URL = link, Course = course_name, course_id = course_id, Name = item['title'],
                                item_id = item_ID, Status = 'Update Qualtrics Survey ID', Type = item['type'], Survey = type)
                            else:
                                # check if module is published
                                if module['published'] == False:
                                    add_to_df(df = csv_data,
                                        URL = item['html_url'],
                                        Course = course_name, Survey = type,
                                        Status = 'Survey found in an unpublished module', Action = 'Publish Module')
                                    if item['type'] != 'Page':
                                        id = ''
                                    else:
                                        id = item['page_url']
                                    add_to_canvas(URL = item['html_url'], Course = course_name, course_id = course_id,
                                    Name = item['title'], item_id = id, Status = 'Survey found in an unpublished module', Type = None, Survey = type)
                        else:
                            status = 'Survey page found that does not contain a Qualtrics survey'
                            add_to_canvas(URL = item['html_url'], Course = course_name, course_id = course_id,
                            Name = item['title'], item_id = None, Status = status,
                            Type = None, Survey = type)
                    else:
                        if item_type == 'ExternalUrl':
                            link += f'/items/{item["id"]}'
                        Status = f'These may or may not be {type} survey modules'
                        add_to_canvas(URL = item['html_url'], Course = course_name, course_id = course_id,
                        Name = item['title'], item_id = item['page_url'], Status = Status, Type = None, Survey = type)
                else:
                    pass
        # if there are modules, but no good match, then survey is simply missing
        if good_match is False:
            # Meaning after going through each page in each module in the course, a good match still hasn't been found
            # If the survey page is not found in any modules, check all pages of the course to see if it exists and if it is pubished
            pages = get_pages(course_id)
            in_course = False
            for page in pages:
                ratio = fuzz.ratio(page['title'], type)
                partial_ratio = fuzz.partial_ratio(page['title'], type)
                if partial_ratio in range(70, 101) and ratio in range(60, 101):
                    in_course = True
                    if page['published'] == False:
                        published_status = f'Survey page exists but is not published'
                        add_to_df(df = csv_data, URL = page['html_url'],
                        Course = course_name, Survey = type,
                        Status = published_status, Action = f'Publish {type} survey page and add to module')
                        add_to_canvas(URL = page['html_url'], Course = course_name, course_id = course_id,
                        Name = page['title'], item_id = page['url'], Status = published_status,
                        Type = None, Survey = type)
                        if stage_input == '2':
                            print(f'Now publishing the {type} survey page in {course_name}...')
                    else:
                        # Meaning that a match was not found in any of the modules, but one WAS found in the list of pages
                        # The needed action is to add the already published page to a module.
                        status = 'Survey page not added to a module'
                        action = f'Create module and add {type} survey'
                        add_to_df(df = csv_data, URL = link, Course = course_name,
                        Survey = type, Status = status, Action = action)
                        add_to_canvas(URL = link, Course = course_name, course_id = course_id,
                        Name = page['title'], item_id = page['url'], Status = status, Type = None, Survey = type)
            if in_course == False:
                link = f'https://byu.instructure.com/courses/{str(course_id)}/pages'
                not_found_action = f'Create page, publish, and add {type} survey page to module'
                add_to_df(df = csv_data, URL = link, Course = course_name,
                Survey = type, Status = f'{type} survey page not in course', Action = not_found_action)
                add_to_canvas(URL = link, Course = course_name, course_id = course_id, Name = f'{type} Survey',
                item_id = None, Status = 'Page not in course', Type = None, Survey = type)

        # Print progress bar
        sys.stdout.write('\r')
        sys.stdout.write(f'|%-{progress_bar_length}s| %d%%' % ('█' * round(course_counter / num_courses * progress_bar_length), course_counter / num_courses * 100))
        sys.stdout.flush()
        course_counter += 1

    print('\n' + f'SEARCH COMPLETE. Searched all courses for {type} Surveys')
    
# Create the report that would be sent to Joel and Enoch and others
file_name = f'Check For {survey_name} Surveys - {term}.csv'
csv_df = pd.DataFrame(data = csv_data, columns = ['URL', 'Course', 'Status', 'Action', 'Survey'])
csv_df.to_csv(file_name, index = False)

# Create the csv file that has everything needed for the API call to change canvas
canvas_file_name = f'Alter {survey_name} Surveys - {term}.csv'
canvas_df = pd.DataFrame(data = canvas_data, columns = canvas_columns)
canvas_df.to_csv(canvas_file_name, index = True)


if send_email:
    # Sending the email to Joel and Enoch:
    outlook = win32.Dispatch('outlook.application')
    while True:
        try:
            name = outlook.Session.CurrentUser.AddressEntry.GetExchangeUser().Name
            break
        except:
            print("Please open up Outlook")
            time.sleep(5)

    mail = outlook.CreateItem(0)
    mail.to = 'joel_hemingway@byu.edu'
    mail.CC = 'kirk.parry@byu.edu'
    mail.CC += '; ' + 'enoch_hunsaker@byu.edu'
    mail.CC += '; ' + 'dustin.jones@byu.edu; '
    mail.CC += '; ' + 'kristi.aase@byu.edu'
    # TODO Make sure that this works okay
    path = os.getcwd()
    mail.subject = f'{term} {survey_name} Survey Actions Report'
    #The file attachment that will be added on will already be decided between .txt and .csv
    mail.Attachments.Add(os.path.join(path, file_name))
    mail.body = '''Hello,
This is a report of the needed actions regarding surveys in canvas. Attached is a file that contains all the needed actions and their corresponding courses.
There are a few different scenarios that can occur. This will be indicated by the "Status" column in the file.
Survey page not in course means that the program could not find that type of survey anywhere in the course. 'Page exists but is not publised' means a survey page was found, but it has not been published, and thus is not in any module. Not In Module means that the page exists and is published but is not in the normal flow of the course. Students may come across these surveys at times, but the number of responses is significantly lower.    
If any of these do not make sense to you, there is also an "Action" column that describes the needed changes that the program will enact in Canvas.
Please note that some of these surveys may be hidden or removed from the course on purpose because some instructors prefer to opt-out of certain surveys for their course. If you know of any such instances that appear in this report, please let us know so we can refrain from altering their courses against their wishes.
Please reply and let us know which of the proposed survey changes in this report look good to you. Once you do, we will run a script that makes the changes in Canvas.
Lastly, let us know if you have any questions. If there is anything that you don't understand, let us know so we can get this right. Thank you so much for your time and your help!'''
    
    signature = 'Best,\n' + name + """\nBYU Online Team"""
    mail.body += signature
    mail.display(True)
print('\nEnd of Script')