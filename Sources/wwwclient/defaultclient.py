#!/usr/bin/env python
# Encoding: iso-8859-1
# -----------------------------------------------------------------------------
# Project   : WWWClient
# -----------------------------------------------------------------------------
# Author    : Sebastien Pierre                               <sebastien@ivy.fr>
# -----------------------------------------------------------------------------
# License   : GNU Lesser General Public License
# Credits   : Xprima.com
# -----------------------------------------------------------------------------
# Creation  : 04-Jun-2006
# Last mod  : 11-Jun-2012
# -----------------------------------------------------------------------------

import httplib, urlparse, client

# TODO: Add retry support
class HTTPClient(client.HTTPClient):
	"""Sends and manages HTTP requests using the 'httplib' and 'urlparse'
	modules. Using the 'curlclient' may be more efficient than using this one."""

	def __init__( self, encoding="latin-1" ):
		client.HTTPClient.__init__(self, encoding)
		self._http = None

	def GET( self, url, headers=None ):
		"""Gets the given URL, setting the given headers (as a list of
		strings)."""
		# We prepare the request
		response = None
		if headers == None: headers = ()
		if self._cache:
			response = self._cache.get(url)
		if not response:
			self._prepareRequest(method="GET", url=url, headers=headers)
			# And get the response
			response = self._performRequest()
			if self._cache:
				self._cache.set(url, response)
		return self._finaliseRequest(response, url)

	def POST( self, url, data=None, mimetype=None, fields=None, attach=None, headers=None ):
		# If there is already data given, we check that there is no fields or
		# attachments
		if data:
			assert not fields, "Fields must be empty when data is provided"
			assert not attach, "No attachment is allowed when data is provided"
			data = self._valueToPostData(data)
		# Otherwise we encode the data as multipart
		if data == None:
			assert mimetype == None, "Mimetype is ignored when no data is given."
			attach = self._ensureAttachment(attach)
			data, mimetype = self.encode(fields, attach)
		# In case we have a mimetype, we update the list of headers
		# appropriately
		if mimetype:
			if headers == None: headers = []
			headers = list(filter(lambda x: client.RE_CONTENT_TYPE.match(x) == None, headers))
			headers.append("Content-Type: " + mimetype)
		# We add the Content-Length header to the headers list
		headers.append("Content-Length: " + self._valueToString(len(data)))
		# We prepare the request
		self._prepareRequest(method="POST", url=url, headers=headers, body=data)
		# And get the response
		response = self._performRequest()
		return self._finaliseRequest(response, url)

	def _prepareRequest( self, url, headers=(), body=None, method="GET" ):
		assert self._http == None, "Only one request is allowed per instance"
		url_parsed = urlparse.urlparse(url)
		host       = url_parsed[1] or self.host()
		if not host:
			raise Exception("No host defined for request: %s" % (url))
		i = url.find(host)
		if i == -1:
			raise Exception("URL does not correspond to current host (%s): %s " % (host, url))
		url_path = url[i+len(host):]
		if url_parsed[0] == "http":
			self._http = httplib.HTTPConnection(host)
		elif url_parsed[0] == "https":
			self._http = httplib.HTTPSConnection(host)
		else:
			raise Exception("Protocol not supported: "  + str(url_parsed[0]))
		http_headers = {}
		for header in headers:
			colon = header.find(":")
			http_headers[header[:colon].strip()] = header[colon+1:]
		#print "=---------------------------------------"
		#print host
		#print method, url_path
		#print headers
		#print body
		#print "=---------------------------------------"
		request  = self._http.request(method, url_path, body, http_headers)
		return request

	def _performRequest( self, counter=0 ):
		try:
			response = self._http.getresponse()
			if response.version == 10: res = "HTTP/1.0 "
			else: res = "HTTP/1.1 "
			res += str(response.status) + " "
			res += str(response.reason) + client.CRLF
			res += str(response.msg) + client.CRLF
			res += response.read()
			if self._http: self._http.close()
			self._http = None
			return res
		except Exception, e:
			if self._http: self._http.close()
			self._http = None
			raise e

	def _finaliseRequest( self, response, url ):
			self._url    = self._absoluteURL(url)
			# Copied from perform request
			self._status = response.split()[1]
			res          = self._parseResponse(response)
			self._protocol, self._host, _, _, _, _ = urlparse.urlparse(self._url)
			if self.verbose >= 1:
				self._log(self.info())
			return res
			
# EOF - vim: tw=80 ts=4 sw=4 noet
