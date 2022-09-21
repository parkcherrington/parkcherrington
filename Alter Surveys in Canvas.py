'''
The purpose of this script is to alter Canvas to make sure that each course in a given term
is not missing any surveys.
This script is meant to run in conjunction with the 'Check for Surveys' script, which scans through
canvas to find all instances of missing and unpublished surveys. That script makes and returns two
excel spreadsheets. The first is a report that is sent to Joel and Enoch so that they have a chance
to review the proposed changes and make sure that everything is alright. The second contains all
the information needed to perform an API call that makes the proposed changes in Canvas. 

This script will typically be run at the beginning of each term, but don't run this code file until
you have received the OK from Joel and/or Enoch. They will help point out instances of when an 
instructor has opted out of surveys, or anything else that we need to be aware of.

This first report is called 'Check for (All) Surveys - Summer 2022.csv'
It includes the following instances:
- A survey page is not found anywhere in the course:
- A survey page exists, but is not published (and has not been added to a module)
- A survey page exists and is published, buut has not been added to a Canvas module
The columns in this report are: URL, Course, Status, Action, and Survey.

The second report contains more detailed information. It is not sent to Joel and Enoch, and serves as
the input for this script. It includes the same instances as above, but also contains the following
scenarios:
- A survey page exists, but it contains the wrong type of Qualtrics survey.
- A survey page exists, but it contains a non-Qualtrics survey.
This second report has the same columns as above, but in addition, it has these: Course ID, Item Name, Item ID,
and Page Type. It does not include the Action column, as that was to help Joel and Enoch understand the process.

The code in this script has the potential to ruin lots of stuff in Canvas, which could cause headaches for many
people. Be very careful and make sure that you know what you are doing as you run it. If you want, you can run 
the script within the test environment of Canvas first, so you can see exactly what each call is doing. 
To enter the test environment, change the API_URL value from https://byu.instructure.com/api/v1 to 
https://byu.test.instructure.com/api/vi. You will also need to go to byu.test.instructure.com and create a
seperate API KEY that specifically works for the test environment. There are also safeguards in the code that
give you a chance to review the change you are about to make in Canvas before proceeding, one API call at a time.
If you are confident that everything is set up properly and want to go through the script more quickly, you can
also choose to bypass the safeguards at the beginning of the script.

HELPS (If you get stuck later while running the code)
Safeguards: You have the option to impliment safeguards as you alter Canvas. If you choose to do so, you can 
make sure everything looks good before making a change. Here is what it would look like. Before every change,
the console will tell you about what you are about to do. Here is an example:
'You are about to publish the Mid-Course Survey page in the M COM 320-010 course.'
Then after you have checked everything and feel good about it, you can hit enter and the program will proceed.
It will then continue on to the next change, and so forth.

Adding a page to a module: The link should have taken you to the modules page. Go to the new one you just made. 
Its name will be the type of survey that you are adding to a module. Once you are at the right module, click on
the plus sign to add a page to it. Make the addition type 'Page'. From here, you should see a list of eligible 
pages that can be added to the module. Select that one and you should be good to go. Once the module is actually
created, it will be at the top of the modules list. We need to get it to the right spot, so make sure that you
know where it should be. This is particularly true of Mid-Course survey modules.


'''

import requests as r
import webbrowser as web
import pandas as pd
import time
import os

# Set up all the needed components of the API call
API_URL = 'https://byu.test.instructure.com/api/v1'
API_KEY = '7407~zFneB7wNyTiY2xM4aPWkPpR8Adm3EOvgCspvv0zuIIWhDhekE9HLkN4FEO27H30u'
header = {'Authorization': 'Bearer ' + '%s' % API_KEY}
# Specify the browser
# chrome = web.get('chrome')

# region user-defined functions
# A POST API page that creates a new survey page
def create_page(survey_type, course_id, survey_id):
    payload = {
    'wiki_page[title]': f'{survey_type} Survey',
    'wiki_page[body]': '<p><iframe src="https://byu.az1.qualtrics.com/jfe/form/' + survey_id + '" width="800px" height="1000px"></iframe></p>',
    'wiki_page[editing_roles]': 'teachers',
    'wiki_page[published]': True
    }

    page = r.post(API_URL + '/courses/' + str(course_id) + '/pages',
     params = payload, headers = header)

    # After the page has been created, open the webpage to actually add it to a module
    return page.json()

    #  A PUT call to publish unpublished survey pages
def publish_page(course_id, item_id):
    payload = {
        'wiki_page[published]': True
    }
    r.put(API_URL + '/courses/' + str(course_id) + '/pages/' + item_id,
     params = payload, headers = header)
    # Since the page wasn't published, it also wasn't part of a module.


def create_module(course_id, survey_type):
    mod_payload = {
        'module[name]': f'{survey_type} Survey',
        'module[position]': 0,
    }
    r.post(API_URL + '/courses/' + str(course_id) + 'modules', headers = header)

    # Opens the webpage to put the page in a module or to make a new module and put that page in it
    print('Opening a webpage of the newly created module... ')
    time.sleep(3)
    web.open(f'https://byu.instructure.com/courses/{course_id}/modules')
    help = input('Type "help" if you need help, otherwise hit enter to continue')
    if help == 'help':
        print('Refer to line 47 of the script')
        time.sleep(1)
        input('Hit enter to continue')

def update_survey(course_id, survey_type, item_id, qualtrics_survey_id):
    # print('Adding qualtrics survey to existing survey modules...')
    payload = {
        'wiki_page[title]': survey_type + ' Survey',
        'wiki_page[body]': '<p><iframe src="https://byu.az1.qualtrics.com/jfe/form/' + qualtrics_survey_id + '" width="800px" height="1000px"></iframe></p>',
        'wiki_page[editing_roles]': 'teachers',
        'wiki_page[published]': True
    }
    r.put(API_URL +
        '/courses/' +
        str(course_id) +
        '/pages/' +
        str(item_id),
        params=payload, headers=header)

def options(link = 'byu.instructure.com'):
    # Function that can perform one of many possible options before an API call is made
    skip = False
    review = False
    remove_safeguards = False
    while True:
        action = input('Hit enter to continue.')
        if action == 'options':
            header = 'Input' + '\t' + 'Action'
            print(header)
            print('_' * len(header))
            print('(Enter)' + '\t' + 'Run the next API call')
            print('skip' + '\t' + 'Skip the next API call')
            print('web' + '\t' + 'Open the webpage')
            print('review' + '\t' + 'Show a page after its creation')
            print('exit' + '\t' + 'Remove safeguards')
        elif action == 'skip':
            print('The next API call will be skipped and the proposed Canvas change will not go into effect.')
            skip = True
            break
        elif action == 'web':
            web.open(link)
        elif action == 'exit':
            print('You are about to remove API safeguards. The rest of the proposed changes in Canvas will be enacted without further review.')
            confirm = input('Hit enter to confirm and continue. Enter "no" to go back. ')
            if confirm != 'no':
                remove_safeguards = True
                break
        elif action == 'review':
            print('If the next API call is to create or edit a page, that webpage will open after its creation')
            review = True
        elif action == '':
            # This option means run the API call
            break
        else:
            print('ERROR: Input (Enter) or one of the valid options. For a list of options, enter \'options\': ')
    return skip, review, remove_safeguards
# endregion user-defined functions

# Read in the data by selecting which spreadsheet to be read in
current_dir = os.listdir()
files_in_directory = {}
counter = 0
print('Choose an excel file:')
for item in current_dir:
    counter += 1
    files_in_directory[str(counter)] = item
    print(f'{counter}\t{item}')

while True:
    try:
        file_num_input = input('Enter the number next to the input spreadsheet: ')
        file_num = files_in_directory[file_num_input]
        break
    except:
        print(f'\nERROR: Please enter a number between 1 and {counter - 1}\n')
print(f'You have entered {files_in_directory[file_num_input]}\n')

home = os.getcwd()
df = pd.read_csv(os.path.join(home, file_num))

# Choose at what pace to make the API calls.
while True:
    safeguard_input = input('Do you want to make the changes one at a time (1) or not (2)? ')
    if safeguard_input == '1':
        safeguard = True
        print('You will be given a chance to review each proposed change in Canvas before making it.')
        break
    elif safeguard_input == '2':
        safeguard_input = False
        print('The code will perform each API call one after another with only a few pauses.')
        break
    else:
        print('ERROR: Please enter either 1 or 2.')
        print('For an explanation on how this works, refer to line 40\n')

# test out the feature that returns a page
# exsc_page = create_page(survey_type = 'Learner Readiness', course_id = 13735, survey_id = 'SV_9Mr45KbxLqfcJdb')
# web.open(exsc_page['html_url'])
# print('pause')

input('\nHit enter to continue')

# Testing different ways to slice data
# print('New way:')
# print(df.loc[25, 'Course ID'])
# print(df.loc[10])

length = df.shape[0]
print(f'\nNumber of rows in df (and number of changes to make): {length - 1}')
time.sleep(2)
for i in range(df.shape[0]):
    print(' ') # For nice, organized spacing in the terminal, print an empty space
    while True:
        try:
            status = df.loc[i, 'Status']
            survey = df.loc[i, 'Survey']
            break
        except:
            i += 1
            # This is just a way for the script to not freak out when we delete rows and the val in the index column is no longer incremental

    # print(f'Status: {status}')
    # Assign the qualtrics ID based on the survey
    if 'Learner Readiness' in survey:
        qualtrics_id = 'SV_9Mr45KbxLqfcJdb'
        # survey = 'Learner Readiness'
    elif 'Mid-Course' in survey:
        qualtrics_id = 'SV_1AN0abATTLYgzel'
        # survey = 'Mid-Course'
    elif 'End of Course' in survey:
        qualtrics_id = 'SV_aYwrUf4n5znh3X7'
        # survey = 'End of Course'
    else:
        print('We still have a problem.')
        print('pause')
    # Assign some values
    course_name = df.loc[i,'Course']
    # print(f'Course Name: {course_name}')
    course_id = df.loc[i, 'Course ID']
    item_id = df.loc[i, 'Item ID']
    page_name = df.loc[i,'Item Name']
    web_url = df.loc[i, 'URL']
    if 'Page not in course' in status:
        if safeguard:
            print(f'You are about to create a new {survey} page in {course_name}, publish it, and add it to a module.')
            skip, review, remove = options(link = web_url)
            if skip == False:
                created_page = create_page(survey_type = survey, course_id = course_id, survey_id = qualtrics_id)
            if review == True:
                web.open(created_page['html_url'])
        else:
            created_page = create_page(survey_type = survey, course_id = course_id, survey_id = qualtrics_id)          
    elif 'Survey page exists but is not published' in status:
        if safeguard:
            print(f'You are about to publish the {page_name} page in the {course_name} course and add it to a module.')
            skip, review, remove = options(link = web_url)
            steps = input('Hit enter to continue. To view the webpage, enter 1: ')
            if review:
                web.open(web_url)
            if skip == False:
                publish_page(course_id = course_id, item_id = item_id)
        else:
            publish_page(course_id = course_id, item_id = item_id)
    # elif 'Survey page not added to a module' in status:
    #     if safeguard:
    #         print(f'You are about to create a new module and add the {page_name} page to it.')
    #         steps = input('Hit enter to continue. To view the webpage, enter 1: ')
    #         if steps == '1':
    #             web.open(web_url)
        # create_module(course_id = course_id, survey_type = survey)
        # TODO See if this is even necessary and where to put the newly-created modules
    elif 'Update Qualtrics Survey ID' in status:
        page_type = df.loc[i, 'Page Type']
        if page_type == 'Page':
            if safeguard:
                print(f'You are about to change the Qualtrics survey in the {page_name} page within {course_name} to a {str(survey)} survey.')
                skip, review, remove = options(link = web_url)
                if skip == False:
                    update_survey(course_id = course_id, item_id = item_id, survey_type = survey, qualtrics_survey_id = qualtrics_id)
                if review:
                    web.open(web_url)
            else:
                update_survey(course_id = course_id, item_id = item_id, survey_type = survey, qualtrics_survey_id = qualtrics_id)
        elif page_type is not None:
            # This means that the type is something other than Page. The API calls are not tailored for these, so we open the webpage and manually make sure it's good.
            print(f'A Qualtrics survey with an invalid survey ID was found in a(n) {page_type} page. Opening webpage...')
            time.sleep(2)
            # TODO maybe find a way to delete the old page and make a new page (of page type) with the right qualtrics ID
            web.open(web_url)
            input('Hit enter to continue.')

    else:
        # This case should be one of the 'These may or may not be ___ modules'
        print(f'Other status: {status}')
        time.sleep(2)
        # Simply open a page to it and make sure that the survey page is working.
        # TODO See what this situation looks like and how to fix it
        web.open(web_url)
        input('Hit enter to continue')
    if i > 0 and i % 10 == 0:
        print(f'\n You have made {i} changes. You have {length - i} changes remaining.')
        percentage = i / length
        print(f'{round((percentage * 100), 2)}% done.')
        time.sleep(1)
    if remove == True:
        safeguard == False

print('End of script')
# TODO take away the testing print statements after testing works