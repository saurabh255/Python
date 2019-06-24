"""
Definition of views.
"""

from django.shortcuts import render
from django.http import HttpRequest
from django.template import RequestContext
from datetime import datetime

import requests
import urllib.request
import time
from bs4 import BeautifulSoup
import re
from django.http import JsonResponse
import json
from .models import Record
from django.conf import settings as djangoSettings
from django.core import serializers
def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/index.html',
        {
            'title':'Home Page',
            'year':datetime.now().year,
        }
    )

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {
            'title':'Contact',
            'message':'Your contact page.',
            'year':datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title':'About',
            'message':'Your application description page.',
            'year':datetime.now().year,
        }
    )
def json_status(request):
    json_data = open(djangoSettings.STATIC_ROOT+'/app/json/status.json')   
    data1 = json.load(json_data)
    return JsonResponse(data1)
def json_sites(request):
    json_data = open(djangoSettings.STATIC_ROOT+'/app/json/sites.json')   
    data1 = json.load(json_data)
    return JsonResponse(data1, safe=False)
def scan_sites(request):
	return render(
		request,
		'app/scan_sites.html',
		{
			'title':'Scan Sites',
			'message':'Collect Source Data by Scan Sites'
		}
	)
def ajax_scan_sites(request):
    data=[]
    count=0
    ## site 1 : brockandscott.com
    site = 'brockandscott.com'
    try:
        with open(djangoSettings.STATIC_ROOT+'/app/json/status.json', 'w') as json_file1:
            json.dump(dict(status='running', message='Started Processing', site=site, count=count), json_file1)
            json_file1.close()
        for page_id in range(31,500000):
            response = requests.get('https://www.brockandscott.com/foreclosure-sales/?_sft_foreclosure_state=nc&sf_paged='+str(page_id))
            soup = BeautifulSoup(response.text, "html.parser")
            notfound = soup.find('h1',{'class':'page-title'})
            if(notfound):
                print('Not Found at page ',page_id)
                break
            for row in soup.findAll('div', {"class": 'record'}):
                count=count + 1
                rec = Record()
                rec.id = count
                rec.site = site
                for cell in row.findAll('div',{'class':'forecol'}):
                    ptags = cell.findAll('p')
                    if(ptags[0].text.strip() == 'County:'):
                        rec.county = ptags[1].text.strip()
                    elif(ptags[0].text.strip() == 'Sale Date:'):
                        rec.sale_date = ptags[1].text.strip()
                    elif(ptags[0].text.strip() == 'Case #:'):
                        rec.case = ptags[1].text.strip()
                    elif(ptags[0].text.strip() == 'Address:'):
                        rec.address = ptags[1].text.strip()
                    elif(ptags[0].text.strip() == 'Opening Bid Amount:'):
                        rec.bid = ptags[1].text.strip()
                    elif(ptags[0].text.strip() == 'Court SP #:'):
                        rec.courtsp = ptags[1].text.strip()
                    #keytext = re.sub('[^A-Za-z]+', '', ptags[0].text)
                    #keytext =  keytext.lower()
                    #row_data.update({keytext:ptags[1].text})
				    ##print(ptags[1].text, end=', ')
			    ##print() 
                with open(djangoSettings.STATIC_ROOT+'/app/json/status.json', 'w') as json_file1:
                    json.dump(dict(status='running', message='Started Processing', site=site, count=count), json_file1)
                data.append(rec.as_json())
    except:
        print('Something Went Wrong '+site)


    ## site 2 : sales.hutchenslawfirm.com
    site = 'sales.hutchenslawfirm.com'
    try:
        #with open(djangoSettings.STATIC_ROOT+'/app/json/status.json', 'w') as json_file1:
        #    json.dump(dict(status='running', message='Started Processing', site=site, count=count), json_file1)
        #    json_file1.close()
        url = 'https://sales.hutchenslawfirm.com/NCfcSalesList.aspx'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        pager_row=soup.findAll('tr', attrs={'class':'GridPager_WebBlue'})
        pager_td=pager_row[0].findAll('td')
        vs = soup.find('input', {'id': '__VIEWSTATE'}).get('value')
        ev = soup.find('input', {'id': '__EVENTVALIDATION'}).get('value')
        vg = soup.find('input', {'id': '__VIEWSTATEGENERATOR'}).get('value')
        words = pager_td[0].text.split()
        total_pages = words[-1]
        print(total_pages)
        for page in range(3,int(total_pages)+1):
            et='SalesListGrid$ctl01$ctl03$ctl01$ctl0'+str(page)
            postdata = {'__EVENTTARGET':et,
                    '__EVENTARGUMENT':'',
                    '__VIEWSTATE':vs,
                    '__EVENTVALIDATION':ev,
                    '__VIEWSTATEGENERATOR':vg,
                    'SearchTextBox':'',
                    'SearchGroup':'AllRadio',
                    'SalesListGridPostDataValue':''}
            r =requests.post(url, data=postdata)
            newsoup = BeautifulSoup(r.text, "html.parser")
            for rows in newsoup.findAll('tr', attrs={'class':['GridRow_WebBlue','GridAltRow_WebBlue']}):
                index=0
                count=count + 1
                rec = Record()
                rec.id = count
                rec.site = site
                for cols in rows.findAll('td'):
                    if(index==0):
                        rec.case = cols.text.strip()
                    elif(index==1):
                        rec.courtsp = cols.text.strip()
                    elif(index==2):
                        rec.county = cols.text.replace(', NC', '').strip()
                    elif(index==3):
                        rec.sale_date = cols.text.strip()
                    elif(index==4):
                        rec.address = cols.text.strip()
                    elif(index==7):
                        rec.bid = cols.text.strip()
                    index = index +1
                with open(djangoSettings.STATIC_ROOT+'/app/json/status.json', 'w') as json_file1:
                    json.dump(dict(status='running', message='Started Processing', site=site, count=count), json_file1)
                data.append(rec.as_json())
    except:
        print('Something Went Wrong '+site)


    ## site 3 : sales.hutchenslawfirm.com
    site = 'shapiro-ingle.com'
    try:
        url = 'https://www.shapiro-ingle.com/sales.aspx?state=NC'
        sale_types = ['upcoming_sales','sales_held']
        for sale_type in sale_types:
            print()
            print(sale_type)
            print()
            response = requests.post(url, data={'db':sale_type,'county':'%','SubmitBtn':'Search'})
            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find('table')
            rows = table.findAll('tr')
            for row in rows:
                index=0
                count=count + 1
                rec = Record()
                rec.id = count
                rec.site = site
                for cols in row.findAll('td'):
                    if(index==0):
                        rec.county = cols.text.replace(', NC', '').strip()
                    elif(index==1):
                        rec.sale_date = cols.text.strip()
                    elif(index==2):
                        rec.case = cols.text.strip()
                    elif(index==3):
                        rec.address = cols.text.strip()
                    elif(index==4):
                        rec.bid = cols.text.strip()
                    index = index +1
                with open(djangoSettings.STATIC_ROOT+'/app/json/status.json', 'w') as json_file1:
                    json.dump(dict(status='running', message='Started Processing', site=site, count=count), json_file1)
                data.append(rec.as_json())
    except:
        print('Something Went Wrong '+site)
    if(len(data)>0):
        with open(djangoSettings.STATIC_ROOT+'/app/json/sites.json', 'w') as json_file:
            json.dump(dict(data=data), json_file)
            json_file.close()
    with open(djangoSettings.STATIC_ROOT+'/app/json/status.json', 'w') as json_file1:
        json.dump(dict(status='completed', message='Scan Completed', site='All Site', count=count), json_file1)
        json_file1.close()
    return JsonResponse({'status':'done'});