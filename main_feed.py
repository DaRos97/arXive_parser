import urllib.request as libreq
import feedparser
from datetime import datetime,timedelta
import time

"""
Here we download the full arxive feed and filter cor cathegory and authors
"""
days_back = 3 if not datetime.now().weekday()==0 else 3     #Change the 1 to 2,3 ecc.. to have earlier dates

# Base api query url
base_url = 'http://export.arxiv.org/api/query?'

initial_r = 0
max_r = 500
wait_time = 3

repeat = True
filter_list = []
while repeat:
    print(initial_r)
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
        print("not right amount iof results")
        continue

    #Filter to have the right date
    today = datetime.now() - timedelta(days = days_back)
    formatted_today = '{:04d}'.format(today.year)+'-'+'{:02d}'.format(today.month)+'-'+'{:02d}'.format(today.day)
    yesterday = datetime.now() - timedelta(days = days_back+1)
    formatted_yesterday = '{:04d}'.format(yesterday.year)+'-'+'{:02d}'.format(yesterday.month)+'-'+'{:02d}'.format(yesterday.day)
    for i in range(len(full_list)):
        if ((full_list[i]['published'][:10]==formatted_today and int(full_list[i]['published'][11:13])<18) or 
            (full_list[i]['published'][:10]==formatted_yesterday and int(full_list[i]['published'][11:13])>=18)):
            filter_list.append(full_list[i])
            if i == len(full_list)-1:
                repeat = True
    if len(filter_list)==0:
        repeat = True
    if repeat:
        initial_r += max_r
        time.sleep(wait_time)

print("Total physics entries: ",len(filter_list))
#Filter for authors
list_names = ['Dario Rossi','Jerome Lloyd','Michael Sonner','Julian Thoenniss','Lorenzo Pizzino','Giacomo Morpurgo','Florian Stabler','Ivo Gabrovski','Anna Efimova',
            'Margherita Melegari','Lucia Varbaro','Ludovica Tovaglieri','Francesco Lonardo','Julia Issing','Michael Straub','Gianmarco Gatti',
            'Alexios Michailidis','Johannes Motruk','Alessio Lerose','Catalin-Mihai Halati','Hepeng Yao','Giulia Venditti','Ilya Vilkoviskiy','Lorenzo Gotta',
            'Dmitry Abanin','Louk Rademaker','Thierry Giamarchi','Michele Filippone','Tony Jin']
author_list = []
for i in range(len(filter_list)):
    for n in range(len(filter_list[i]['authors'])):
        if filter_list[i]['authors'][n]['name'] in list_names:
            author_list.append((filter_list[i],n))

print("Total friends entries: ",len(author_list))

#Filter for category
list_categories = ['cond-mat.str-el','cond-mat.mes-hall','cond-mat.quant-gas']
category_list = []
for i in range(len(filter_list)):
    for c in range(len(filter_list[i]['tags'])):
        if filter_list[i]['tags'][c]['term'] in list_categories:
            category_list.append(filter_list[i])
            break

print("Total category entries: ",len(category_list))

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

if 0:   #Print full list
    considered_list = category_list
    for i in range(len(considered_list)):
        if 0:
            print(considered_list[i].keys())
        if 1:
            print('Entry '+str(i)+':')
            print('Title: ',considered_list[i]['title'])
            print('Authors: ',formatAuthors(considered_list[i]['authors']))
            print('Date: ',considered_list[i]['published'])
            print('Link :',considered_list[i]['link'])
            print('Cat :',considered_list[i]['arxiv_primary_category']['term'])
            print('Tags :',[considered_list[i]['tags'][n]['term'] for n in range(len(considered_list[i]['tags']))])
    exit()

#Create pdf
print("Creating latex file and pdf")
from contextlib import redirect_stdout
from pathlib import Path
import os
#
dirname = 'feeds/'+formatted_today+'/'
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
os.system('pdflatex '+filename+' > '+output_file)
os.system('mv '+formatted_today+'* '+dirname)
os.system('xdg-open '+filename[:-3]+'pdf')



































