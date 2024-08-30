import urllib.request as libreq
import feedparser
from datetime import datetime,timedelta
import time
from pathlib import Path
import os,sys
from contextlib import redirect_stdout


###########################################################
# Select date window
###########################################################

cwd = os.path.dirname(os.path.realpath(__file__))
def format_day(day):
    return '{:04d}'.format(day.year)+'-'+'{:02d}'.format(day.month)+'-'+'{:02d}'.format(day.day)
days_back = int(sys.argv[1]) #if not datetime.now().weekday()==0 else 3     #Change the 1 to 2,3 ecc.. to have earlier dates
announced_day = datetime.now() - timedelta(days = days_back)
fad = format_day(announced_day)
if announced_day.weekday()==5 or announced_day.weekday()==6:  #weekend is always special
    print("Chose a weekend-> going back to the previous friday")
    days_back += +announced_day.weekday()//3
    announced_day = datetime.now() - timedelta(days = days_back)
    fad = format_day(announced_day)
if announced_day.weekday()==0:  #monday is special
    end_days_back = 3
    in_days_back = 4
elif announced_day.weekday()==1:  #tuesday is also special
    end_days_back = 1
    in_days_back = 4
else:
    end_days_back = 1
    in_days_back = 2
end_sub_day = datetime.now() - timedelta(days = days_back+end_days_back)
fesd = format_day(end_sub_day)
in_sub_day = datetime.now() - timedelta(days = days_back+in_days_back)
fisd = format_day(in_sub_day)
print("Downloading articles of date "+fad+" (from 18:01 of "+fisd+" to 18:00 of "+fesd+")")

###########################################################
# Download papers
###########################################################

base_url = 'http://export.arxiv.org/api/query?'

initial_r = 0
max_r = 1000
wait_time = 3

repeat = True
filter_list = []
fetched_0 = False
while repeat:
    if not fetched_0:
        print("start: ",initial_r,", n_results: ",max_r)
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
    #
    if len(full_list)==0:
        print("fetched 0 results.. -> repeat")
        repeat = True
        time.sleep(wait_time)
        fetched_0 = True
        continue
    else:
        print("fetched ",len(full_list)," results")
        fetched_0 = False
    #Filter to have the right date
    for i in range(len(full_list)):
        if ((full_list[i]['published'][:10]==fesd and int(full_list[i]['published'][11:13])<18) or 
            (full_list[i]['published'][:10]==fisd and int(full_list[i]['published'][11:13])>=18)):
            filter_list.append(full_list[i])
            if i == len(full_list)-1:
                repeat = True
                print("Last element fetched still in the day of the search -> repeat")
    if len(filter_list)==0:
        print("Something wrong with the search, no elements fetched are in the rigt day -> repeat")
        repeat = True
    if repeat:
        initial_r += len(full_list)
        time.sleep(wait_time)
print("Total physics entries: ",len(filter_list))

###########################################################
# Filter for authors and categories
###########################################################

#Filter for authors
def find_author(name,list_name):
    result = False
    for n in list_name:
        ln = []
        #Full name
        ln.append(n)
        #Abbreviations
        ns = n.split()
        for j in range(len(ns)-1): #all first names except the last name (hopefully is only one)
            nwn = ''
            if not j==0:
                for i in range(j):
                    nwn += ns[i]+' '
            nwn += ns[j][0]+'. '
            if not j==len(ns)-2:
                for i in range(j+1,len(ns)-1):
                    nwn += ns[i]+' '
            nwn += ns[-1]
            ln.append(nwn)
        #
        if name in ln:
            return True
    return result

author_list = []
if Path(cwd+'/authors.txt').is_file():
    with open(cwd+'/authors.txt','r') as f:
        list_names = f.read().split('\n')[:-1]
    for i in range(len(filter_list)):
        for n in range(len(filter_list[i]['authors'])):
            if find_author(filter_list[i]['authors'][n]['name'],list_names):
                author_list.append((filter_list[i],n))
    print("Total selected authors entries: ",len(author_list))
else:
    print("No file \"authors.txt\" found")

#Filter for category
category_list = []
if Path(cwd+'/categories.txt').is_file():
    with open(cwd+'/categories.txt','r') as f:
        list_categories = f.read().split('\n')[:-1]
    for i in range(len(filter_list)):
        for c in range(len(filter_list[i]['tags'])):
            if filter_list[i]['tags'][c]['term'] in list_categories:
                category_list.append(filter_list[i])
                break
    print("Total category entries: ",len(category_list))
else:
    print("No file \"categories.txt\" found")

###########################################################
# Create pdf latex file
###########################################################

print("Creating latex file and pdf")

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

def formatTitle(text):
    special_characters = ['%',]
    for sc in special_characters:   #hope there is at most one for each special character
        if sc in text:
            ind = text.index(sc)
            text = text[:ind] + '\\' + text[ind:]
    return text

#
dirname_y = cwd+'/feeds/'+fad[:4]+'/'    #year
if not Path(dirname_y).is_dir():
    os.system('mkdir '+dirname_y)
#
dirname_m = dirname_y+fad[5:7]+'/'    #month
if not Path(dirname_m).is_dir():
    os.system('mkdir '+dirname_m)
#
dirname = dirname_m+fad[8:10]+'/'    #day
if not Path(dirname).is_dir():
    os.system('mkdir '+dirname)
#
filename = dirname+fad+'.tex'
output_file = dirname+'output_pdflatex.txt'
with open(filename, 'w') as f:
    with redirect_stdout(f):
        #Documentclass and dependencies
        print("\\documentclass{article}\n\\usepackage[hidelinks]{hyperref}\n\\usepackage{color}")
        #Title
        print("\\title{arXiv daily feed}\n\\author{}\n\\date{"+fad+"}")
        #Start document, maketitle
        print("\\begin{document}\n\\maketitle\n")
        #
        print("\\section*{Articles from selected authors ("+str(len(author_list))+" articles)}")
        if len(author_list)>0:  #Entries
            print("\\begin{enumerate}")
            for i in range(len(author_list)):
                #Title with url link
                title_text = formatTitle(author_list[i][0]['title'])
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
                title_text = formatTitle(category_list[i]['title'])
                print("\\item\\href{"+category_list[i]['link']+"}{\\textsf{"+title_text+"}}\\\\")
                #Authors
                authors = formatAuthors(category_list[i]['authors'])
                print("{\\small\\color{blue}\\textsl{"+authors+"}}")
            print("\\end{enumerate}")
        print("\\end{document}")
#Create .* files to create the pdf and move them to the folder
os.system('pdflatex -interaction nonstopmode -output-directory '+dirname+' '+filename+' > '+output_file)
#Open pdf
os.system('xdg-open '+filename[:-3]+'pdf')



































