import urllib.request as libreq
import feedparser
from datetime import datetime,timedelta
import time
from pathlib import Path

"""
Here we download the full arxive feed and filter for cathegory and authors
"""
days_back = 1 if not datetime.now().weekday()==0 else 3     #Change the 1 to 2,3 ecc.. to have earlier dates
today = datetime.now() - timedelta(days = days_back)
formatted_today = '{:04d}'.format(today.year)+'-'+'{:02d}'.format(today.month)+'-'+'{:02d}'.format(today.day)
yesterday = datetime.now() - timedelta(days = days_back+1)
formatted_yesterday = '{:04d}'.format(yesterday.year)+'-'+'{:02d}'.format(yesterday.month)+'-'+'{:02d}'.format(yesterday.day)
print("Downloading articles up to date "+formatted_today)

# Base api query url
base_url = 'http://export.arxiv.org/api/query?'

initial_r = 0
max_r = 500
wait_time = 5

repeat = True
filter_list = []
while repeat:
    print("start: ",initial_r)
    repeat = False
    #Extract first max_r last papers
    full_list = []
    query = 'search_query=grp_physics'
    query += '&start=%i&max_results=%i' % (initial_r,max_r)
    query += '&sortBy=submittedDate&sortOrder=descending'
    #Put results in a list
    with libreq.urlopen(base_url+query) as url:
        r = url.read()
        s = feedparser.parse(r)
    for i in range(len(s['entries'])):
        full_list.append(s['entries'][i])
    if not max_r == len(full_list):
        repeat = True
        time.sleep(wait_time)
        print("not right amount of results")
        continue

    #Filter to have the right date
    for i in range(len(full_list)):
        if ((full_list[i]['published'][:10]==formatted_today and int(full_list[i]['published'][11:13])<18) or 
            (full_list[i]['published'][:10]==formatted_yesterday and int(full_list[i]['published'][11:13])>=18)):
            filter_list.append(full_list[i])
            if i == len(full_list)-1:
                repeat = True
    if len(filter_list)==0:
#        repeat = True
        print("Something wrong with the search")
        max_r *= 2
        repeat = True
        continue
    if repeat:
        initial_r += max_r
        time.sleep(wait_time)

print("Total physics entries: ",len(filter_list))
#Filter for authors
author_list = []
if Path('authors.txt').is_file():
    with open('authors.txt','r') as f:
        list_names = f.read().split('\n')[:-1]
    for i in range(len(filter_list)):
        for n in range(len(filter_list[i]['authors'])):
            if filter_list[i]['authors'][n]['name'] in list_names:
                author_list.append((filter_list[i],n))
    print("Total selected authors entries: ",len(author_list))
else:
    print("No file \"authors.txt\" found")

#Filter for category
category_list = []
if Path('categories.txt').is_file():
    with open('categories.txt','r') as f:
        list_categories = f.read().split('\n')[:-1]
    for i in range(len(filter_list)):
        for c in range(len(filter_list[i]['tags'])):
            if filter_list[i]['tags'][c]['term'] in list_categories:
                category_list.append(filter_list[i])
                break
    print("Total category entries: ",len(category_list))
else:
    print("No file \"categories.txt\" found")

def formatAuthors(authors_list,ind=-1):
    formatted_list = ''
    for i in range(len(authors_list)):
        if i==ind or ind==-1:
            full_name = authors_list[i]['name']
            names = full_name.split()
            for l in range(len(names)-1):
                formatted_list += names[l][0]+'. '
            formatted_list += names[-1]
            if not i==len(authors_list)-1 and ind==-1:
                formatted_list += ', '
    return formatted_list

###################################################################################################
###################################################################################################
###################################################################################################
#Create pdf
print("Creating latex file and pdf")
from contextlib import redirect_stdout
from pathlib import Path
import os
cwd = os.getcwd()
#
dirname = cwd+'/feeds/'+formatted_today+'/'
if not Path(dirname).is_dir():
    os.system('mkdir '+dirname)
#
filename = dirname+formatted_today+'.tex'
output_file = dirname+'output_pdflatex.txt'
with open(filename, 'w') as f:
    with redirect_stdout(f):
        #Documentclass and dependencies
        print("\\documentclass{article}\n\\usepackage[hidelinks]{hyperref}\n\\usepackage{color}")
        #Title
        print("\\title{arXiv daily feed}\n\\author{}\n\\date{"+formatted_today+"}")
        #Start document, maketitle
        print("\\begin{document}\n\\maketitle\n")
        #
        print("\\section*{Articles from selected authors ("+str(len(author_list))+" articles)}")
        if len(author_list)>0:  #Entries
            print("\\begin{enumerate}")
            for i in range(len(author_list)):
                #Title with url link
                title_text = author_list[i][0]['title']
                print("\\item\\href{"+author_list[i][0]['link']+"}{\\textsf{"+title_text+"}}\\\\")
                #Authors
                print("{\\small")
                for n in range(len(author_list[i][0]['authors'])):
                    author_name = formatAuthors(author_list[i][0]['authors'],n)
                    color='red' if n == author_list[i][1] else 'blue'
                    print("{\\color{"+color+"}\\textsl{"+author_name+"}}")
                    if not n==len(author_list[i][0]['authors'])-1:
                        print("{\\color{blue}, }")
                print("}")
            print("\\end{enumerate}")
        #
        print("\\section*{Relevant categories ("+str(len(category_list))+" articles): ")
        if len(category_list)>0: #Cathegory
            for i in range(len(list_categories)):
                print(list_categories[i])
                if not i==len(list_categories)-1:
                    print(', ')
            print("}")
            #Entries
            print("\\begin{enumerate}")
            for i in range(len(category_list)):
                #Title with url link
                title_text = category_list[i]['title']
                print("\\item\\href{"+category_list[i]['link']+"}{\\textsf{"+title_text+"}}\\\\")
                #Authors
                authors = formatAuthors(category_list[i]['authors'])
                print("{\\small\\color{blue}\\textsl{"+authors+"}}")
            print("\\end{enumerate}")
        print("\\end{document}")
#Create .* files to create the pdf and move them to the folder
os.system('pdflatex -interaction nonstopmode '+filename+' > '+output_file)
os.system('mv '+cwd+'/'+formatted_today+'* '+dirname)
os.system('xdg-open '+filename[:-3]+'pdf')



































