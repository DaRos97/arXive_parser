import urllib.request as libreq
import feedparser
from datetime import datetime,timedelta

"""
Here we extract the daily digest of arXiv articles, already filtered to avoid double reading of same paper.
"""
debug = False
days_back = 1 if not datetime.now().weekday()==0 else 3

# Base api query url
base_url = 'http://export.arxiv.org/api/query?';

max_r = 100
repeat = True
while repeat:
    repeat = False
    #Extract first N last papers from the 3 main categories
    full_list = []
    subcat_list = ['str-el','mes-hall','quant-gas']
    query = 'search_query='
    for subcat in subcat_list:
        query += 'cat:cond-mat.'+subcat
        if not subcat_list.index(subcat) == len(subcat_list)-1:
            query += '+OR+'
    start = 0
    max_results = max_r
    query += '&start=%i&max_results=%i' % (start,max_results)
    query += '&sortBy=submittedDate&sortOrder=descending'

    with libreq.urlopen(base_url+query) as url:
        r = url.read()
        s = feedparser.parse(r)
    for i in range(len(s['entries'])):
        full_list.append(s['entries'][i])

    
    #Filter to have the right date
    today = datetime.now() - timedelta(days = days_back)
    formatted_today = '{:04d}'.format(today.year)+'-'+'{:02d}'.format(today.month)+'-'+'{:02d}'.format(today.day)
    yesterday = datetime.now() - timedelta(days = days_back+1)
    formatted_yesterday = '{:04d}'.format(yesterday.year)+'-'+'{:02d}'.format(yesterday.month)+'-'+'{:02d}'.format(yesterday.day)
    filter_list = []
    for i in range(len(full_list)):
        if (full_list[i]['published'][:10]==formatted_today or 
            (full_list[i]['published'][:10]==formatted_yesterday and int(full_list[i]['published'][11:13])>=18)):
            filter_list.append(full_list[i])
            if i == len(full_list)-1 and not debug:
                repeat = True
    if repeat:
        max_r *= 2

print("Total entries: ",len(filter_list))

def formatAuthors(authors_list):
    formatted_list = ''
    for i in range(len(authors_list)):
        full_name = authors_list[i]['name']
        names = full_name.split()
        for l in range(len(names)-1):
            formatted_list += names[l][0]+'. '
        formatted_list += names[-1]
        if not i==len(authors_list)-1:
            formatted_list += ', '
    return formatted_list

if 0:   #Print full list
    for i in range(len(filter_list)):
        if 1:
            print(filter_list[i].keys())
        if 1:
            print('Entry '+str(i)+':')
            print('Title: ',filter_list[i]['title'])
            print('Authors: ',formatAuthors(filter_list[i]['authors']))
            print('Date: ',filter_list[i]['published'])
            print('Link :',filter_list[i]['link'])
            print('Cat :',filter_list[i]['arxiv_primary_category']['term'])
            print('Tags :',[filter_list[i]['tags'][n]['term'] for n in range(len(filter_list[i]['tags']))])

    #exit()


#Create pdf using latex
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
with open(filename, 'w') as f:
    with redirect_stdout(f):
        #Documentclass and dependencies
        print("\\documentclass{article}\n\\usepackage[hidelinks]{hyperref}\n\\usepackage{color}")
        #Title
        print("\\title{arXiv daily feed}\n\\author{}")
        #Start document, maketitle and list
        print("\\begin{document}\n\\maketitle\n")
        print(str(len(filter_list))+" articles found")
        #Entries
        print("\\begin{enumerate}")
        for i in range(len(filter_list)):
            #Title with url link
            title_text = filter_list[i]['title']
            print("\\item\\href{"+filter_list[i]['link']+"}{\\textsf{"+title_text+"}}\\\\")
            #Authors
            authors = formatAuthors(filter_list[i]['authors'])
            print("{\\small\\color{blue}\\textsl{"+authors+"}}")
        print("\\end{enumerate}\n\\end{document}")
#Create .* files to create the pdf and move them to the folder
os.system('pdflatex '+filename)
os.system('mv '+formatted_today+'* '+dirname)
os.system('xdg-open '+filename[:-3]+'pdf')





if 0:#not debug: #Create PDF with entries using reportlab
    filename = 'feeds/feed_'+formatted_today+'.pdf'
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.units import cm,inch
    from reportlab.lib.colors import blue,black

    from reportlab import platypus
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.pagesizes import A4
    from reportlab.rl_config import defaultPageSize
    from reportlab.lib.styles import ParagraphStyle as PS
    PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0]

    title_style = PS(
                    'mystyle',
                    fontName='Times-Roman',
                    fontSize=12,
                    textColor=black
                    )
    authors_style = PS(
                    'mystyle',
                    fontName='Times-Roman',
                    fontSize=8,
                    textColor=blue
                    )

    doc = SimpleDocTemplate(filename, pagesize = A4)

    Story = []
    #Put this more as a title
    Story.append(Paragraph('arXiv entries of '+formatted_today))
    #Put this as full line on all page width
    Story.append(Paragraph('---------------------------------------------------------------------'))
    for i in range(len(filter_list)):
        #Put this as numbered list
        title_text = '{:02d}'.format(i+1)+'/'+str(len(filter_list))+': '+filter_list[i]['title']
        title = '<link href="' + filter_list[i]['link'] + '">' + title_text + '</link>'#'<br/>'
        Story.append(Paragraph(title,title_style))
        #
        #Put this aligned with title
        authors = formatAuthors(filter_list[i]['authors'])
        Story.append(Paragraph(authors,authors_style))
        #Put more space between titles

    doc.build(Story)




