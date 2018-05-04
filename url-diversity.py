import math
import os, sys
from urllib.parse import urlparse
from tldextract import extract

'''
	Implementation of URL diversity measures explained here:
	http://ws-dl.blogspot.com/2018/05/2018-05-04-exploration-of-url-diversity.html
		* WSDL diversity index, 
		* Simpson's diversity index, and 
		* Shannon's diversity index.
'''

#utility functions - start

def getCollection():
	
	uriLst = []

	try:
		infile = open('collection.txt', 'r')
		uriLst = infile.readlines()
		infile.close()
	except:
		genericErrorInfo()

	return uriLst

def genericErrorInfo():
	exc_type, exc_obj, exc_tb = sys.exc_info()
	fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	errorMessage = fname + ', ' + str(exc_tb.tb_lineno)  + ', ' + str(sys.exc_info())
	print('\tERROR:', errorMessage)

def getDedupKeyForURI(uri, exceptionDomains=['www.youtube.com']):

	uri = uri.strip()
	if( len(uri) == 0 ):
		return ''

	try:
		scheme, netloc, path, params, query, fragment = urlparse( uri )
		
		netloc = netloc.strip()
		path = path.strip()
		optionalQuery = ''

		if( len(path) != 0 ):
			if( path[-1] != '/' ):
				path = path + '/'

		if( netloc in exceptionDomains ):
			optionalQuery = query.strip()

		return netloc + path + optionalQuery
	except:
		print('Error uri:', uri)
		genericErrorInfo()

	return ''

def getHostname(url, includeSubdomain=True):

	url = url.strip()
	if( len(url) == 0 ):
		return ''

	if( url.find('http') == -1  ):
		url = 'http://' + url

	domain = ''
	
	try:
		ext = extract(url)
		
		domain = ext.domain.strip()
		subdomain = ext.subdomain.strip()
		suffix = ext.suffix.strip()
		
		if( len(suffix) != 0 ):
			suffix = '.' + suffix 

		if( len(domain) != 0 ):
			domain = domain + suffix

		if( len(subdomain) != 0 ):
			subdomain = subdomain + '.'

		if( includeSubdomain ):
			domain = subdomain + domain
	except:
		genericErrorInfo()
		return ''

	return domain

#utility functions - end

def shannonsEvennessIndex(uriLst):
	
	if( len(uriLst) == 0 ):
		return {}

	uriAndUnifiedDiversity = {'uri-diversity': {}, 'unified-diversity': {}}
	for uri in uriLst:
		#accumulate counts for uri specie
		uriCanon = getDedupKeyForURI(uri)
		if( len(uriCanon) != 0 ):
			uriAndUnifiedDiversity['uri-diversity'].setdefault(uriCanon, 0)
			uriAndUnifiedDiversity['uri-diversity'][uriCanon] += 1

		hostname = getHostname(uri)
		if( len(hostname) != 0 ):
			uriAndUnifiedDiversity['unified-diversity'].setdefault(hostname, 0)
			uriAndUnifiedDiversity['unified-diversity'][hostname] += 1
	
	N = len(uriLst)	
	for policy in uriAndUnifiedDiversity:

		R = len( uriAndUnifiedDiversity[policy] )
		summationOverPropSpecies = 0
		for uri, n in uriAndUnifiedDiversity[policy].items():
			summationOverPropSpecies += n/N * math.log(n/N)

		maxEvenness = math.log(R)
		if( maxEvenness == 0 ):
			uriAndUnifiedDiversity[policy] = 0
		else:
			uriAndUnifiedDiversity[policy] = (summationOverPropSpecies * (-1))/ maxEvenness
	
	return uriAndUnifiedDiversity

def simpsonsDiversityIndex(uriLst):

	if( len(uriLst) == 0 ):
		return {}

	uriAndUnifiedDiversity = {'uri-diversity': {}, 'unified-diversity': {}}
	for uri in uriLst:
		
		#accumulate counts for uri specie
		uriCanon = getDedupKeyForURI(uri)
		if( len(uriCanon) != 0 ):
			uriAndUnifiedDiversity['uri-diversity'].setdefault(uriCanon, 0)
			uriAndUnifiedDiversity['uri-diversity'][uriCanon] += 1

		hostname = getHostname(uri)
		if( len(hostname) != 0 ):
			uriAndUnifiedDiversity['unified-diversity'].setdefault(hostname, 0)
			uriAndUnifiedDiversity['unified-diversity'][hostname] += 1

	N = len(uriLst)
	for policy in uriAndUnifiedDiversity:
		
		summationOverSpecies = 0
		for uri, n in uriAndUnifiedDiversity[policy].items():
			summationOverSpecies += n * (n - 1)

		if( N == 1 ):
			uriAndUnifiedDiversity[policy] = 0
		else:
			D = summationOverSpecies / (N * (N - 1))
			uriAndUnifiedDiversity[policy] = 1 - D

	return uriAndUnifiedDiversity

def wsdlDiversityIndex(uriLst):
	diversityPerPolicy = {'uri-diversity': set(), 'hostname-diversity': set(), 'domain-diversity': set()}
	
	if( len(uriLst) == 0 ):
		return {}

	if( len(uriLst) == 1 ):
		for policy in diversityPerPolicy:
			diversityPerPolicy[policy] = 0
		return diversityPerPolicy

	for uri in uriLst:

		uriCanon = getDedupKeyForURI(uri)
		if( len(uriCanon) != 0 ):
			#get unique uris
			diversityPerPolicy['uri-diversity'].add( uriCanon )						
		
		hostname = getHostname(uri)
		if( len(hostname) != 0 ):
			#get unique hostname
			diversityPerPolicy['hostname-diversity'].add( hostname )					

		domain = getHostname(uri, includeSubdomain=False)
		if( len(domain) != 0 ):
			#get unique domain	
			diversityPerPolicy['domain-diversity'].add( domain )
	
	for policy in diversityPerPolicy:
		U = len(diversityPerPolicy[policy])
		N = len(uriLst)
		diversityPerPolicy[policy] = (U - 1)/(N - 1)

	return diversityPerPolicy

def main():

	uriLst = getCollection()
	if( len(uriLst) == 0 ):
		print('Error: Empty list')
		return

	print('\nURI diversity report for', len(uriLst), 'URIs:')

	print('\nWSDL URI diversity:')
	diversityPerPolicy = wsdlDiversityIndex(uriLst)
	print( '  URI:', diversityPerPolicy['uri-diversity'] )
	print( '  Hostname:', diversityPerPolicy['hostname-diversity'] )
	print( '  Domain:', diversityPerPolicy['domain-diversity'] )

	diversityPerPolicy = simpsonsDiversityIndex(uriLst)
	print( '\nSimpson\'s diversity index:',  )
	print( '  URI:', diversityPerPolicy['uri-diversity'] )
	print( '  Unified (Species: URI, Individuals: Paths):', diversityPerPolicy['unified-diversity'] )

	diversityPerPolicy = shannonsEvennessIndex(uriLst)
	print( '\nShannon\'s evenness index:' )
	print( '  URI:', diversityPerPolicy['uri-diversity'] )
	print( '  Unified (Species: URI, Individuals: Paths):', diversityPerPolicy['unified-diversity'] )

if __name__ == '__main__':
	main()