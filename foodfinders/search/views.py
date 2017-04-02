from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator
from firebase import firebase

# Create your views here.
#To Do:
#format html
#add firebase to remember all search terms
def sendFirebase(info, parent):
        fbase=firebase.FirebaseApplication('https://storesearch-4fd17.firebaseio.com', None)
        fbase.post(parent, info)
        return 0
def authorization():
	auth = Oauth1Authenticator(
		consumer_key = "qPax5LNdfH6cqZGxigS1Rg",
		consumer_secret = "h3Tqfk7nUvW2krMVBEGB5TmCtWA",
		token = "gCTsxxm_N98BczBYfpW8Z2Zx05HFwjP0",
		token_secret = "Kc2LMgNiUhFJN_-A6ltygKzD_c4"

		)	
	client = Client(auth)
	return client;
#set unused business attributes, business.eat24_url and bussiness.menu_provider to have deals information available on results.hml
def addDeals(busiList):
        newURL = ""
        newTitle=""
        newBusiList=[]
        for busi in busiList:
            for deal in busi.deals:
                newURL=newURL+deal.url+" "
                newTitle=newTitle+deal.title+" "
            busi.eat24_url=newURL
            busi.is_claimed=1
            busi.menu_provider=newTitle
            newBusiList.append(busi)
            newURL=""
            newTitle=""
        return newBusiList 
def addAddress(busiList):
        newString = ""
        newBusiList=[]
        for busi in busiList:
            for line in busi.location.display_address:
                newString+=line+" "
            busi.cross_streets=newString+" "
            newBusiList.append(busi)
            newString=""
        
        return newBusiList
def findParams(request):
        #read in values posted by home.html using .get
	terms=request.POST.get("term")
	location=request.POST.get("location")
	limit=request.POST.get("limit")
##	#Make sure limit is within range 1-40
	if(limit<1):
                limit = 1
        elif(limit>40):
                limit=40
        deal=request.POST.get("deal")
        if(deal==None):
                deal=0
	sort=request.POST.get("sort")
	sort=convertSort(sort)
	radius=request.POST.get("distance")
        radius=convertDist(radius)
##        firebase(terms)
	params = {
	'location': location,
	'term': terms,
	'limit': limit,
	'sort': sort,
	'radius_filter': radius,
        'offset': 0,
        'deals_filter': deal
	}
	return params;
def makeListTags(busiList):
        newList = []
        a=0
        while(a<len(busiList)):
              newList.append(busiList[a].categories)
              a=a+1
        return newList
def makeListLoc(busiList):
        newList = []
        a=0
        while(a<len(busiList)):
              newList.append(busiList[a].location)
              a=a+1
        return newList
def deletePermClosed(busiList, params):
        trueClosed=0
        deleteParams=params
        deleteParams['limit']=1
        offset=0
        length=0
        openList=[]
        for business in busiList:
                if(business.is_closed):
                        trueClosed=1;
        if(trueClosed):
                #itterate through many l 1 searches and then throw into return list if not closed permanetly
                while(length<len(busiList)):
                        deleteParams['offset']=offset
                        search=client.search(**deleteParams)
                        if(1!=search[0].is_closed):
                                openList.append(search)
                                length=1+length
                        offset=offset+1
        else:
                openList=busiList
        return openList              
def convertDist(distance):
        if(distance=="5 mi or 8 km"):
           radius=8000
        elif(distance=="10 mi or 16 km"):
           radius=16000
        elif(distance=="15 mi or 24 km"):
           radius=24000
        elif(distance=="20 mi or 32 km"):
           radius=32000
        elif(distance=="25 mi or 40 km"):
           radius=40000
        else:
           radius=40000
        return radius
def convertSort(sort):
        if(sort=="By Best Match"):
           num=0
        elif(sort=="By Distance"):
           num=1
        elif(sort=="Highest Rated"):
           num=2
        else:
           num=0
        return num
def getTopTrends(trends):
        fullList=trends.values()
        newList =[]
        for string in fullList:
                string=string.lower()
                newList.append(string)
        fullList=newList
        noDoubl=list(set(fullList))
        numList=[]
        for item in noDoubl:
                num=fullList.count(item)
                numList.append(num)
        matchDict=dict(zip(noDoubl, numList))
        topTrends=[]
        for key, value in sorted(matchDict.iteritems(),key=lambda (k,v): (v,k), reverse=True):
                topTrends.append(key)
        topCounter=0
        top5=[]
        while(topCounter<5 and topCounter<len(topTrends)):
                top5.append(topTrends[topCounter])
                topCounter+=1
        return top5
def loadCatagory(busiList):
        tag = ''
        catagoryList=[]
        for busi in busiList:
                for catagory in busi.categories:
                        tag +=catagory.name + ', '
                #change unused member .mobile_url into string list of catagories Jinja can parse
                tag=tag[:-2]
                busi.mobile_url=tag
                tag=''
        counter=0
        while(counter<10 and counter<len(busiList)):
                for category in busiList[counter].categories:
                        sendFirebase(category.name, '/Category')
                counter+=1
        return busiList
                        
        
def index(request):
        #first search page
        fbase=firebase.FirebaseApplication('https://storesearch-4fd17.firebaseio.com', None)
        topTrends=fbase.get('/Tags',None)
        topCate=fbase.get('/Category',None)
        topList=getTopTrends(topTrends)
        topCateList=getTopTrends(topCate)
        topDict={'trends': topList, 'category': topCateList}
        
        return render(request, 'search/home.html', topDict)
def results(request):
    #gets search terms, passes params to search results
        params=findParams(request)
        client=authorization()
        search=client.search(**params)
        cBusiness=search.businesses
        openBusi=deletePermClosed(cBusiness,params)
        openBusi=addAddress(openBusi)
        openBusi=loadCatagory(openBusi)
        if(len(openBusi) and params['term']):
                sendFirebase(params['term'],'/Tags')
        if(params['deals_filter']):
                openBusi=addDeals(openBusi)
        else:
                counter=0
                while(counter<len(openBusi)):
                        openBusi[counter].is_claimed=0
                        counter +=1
        results={'place': openBusi,'location': makeListLoc(openBusi), 'tags': makeListTags(openBusi)}
        
        #reads in based on key name-find way to stack everything in one entry on a dictionary?
        
        return render(request, 'search/results.html', results)
