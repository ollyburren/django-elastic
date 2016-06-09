'''
Used to build Elastic queries and filters to run searches.

An L{ElasticQuery} is used to build a L{Search} object.
L{Search.search()} runs the search request and returns
the elastic documents and aggregation as a L(Result). Alternatively
L{Search.get_json_response()} returns the JSON response.

An L{ElasticQuery} object can be built from L{Query} and L{Filter}
objects. There are factory methods within L{ElasticQuery} and L{Query}
classes that provide shortcuts to building common types of queries/filters.
When creating a new query the first port of call would therefore be
the factory methods in L{ElasticQuery}. If this does not provide the
exact components needed for the query then look into building it
from the L{Query} and L{Filter} parent and child classes.
'''
from builtins import classmethod
import json
import logging

import requests

from elastic.elastic_settings import ElasticSettings, ElasticUrl
from elastic.query import Query, QueryError, BoolQuery, FilteredQuery, \
    Filter, HasParentQuery, HasChildQuery
from elastic.result import Result, Aggregation


# Get an instance of a logger
logger = logging.getLogger(__name__)


class Search:
    ''' Used to run Elastic queries and return search hits, hit count or the mapping. '''

    def __init__(self, search_query=None, aggs=None, search_from=0, size=20,
                 search_type=None, idx=ElasticSettings.idx('DEFAULT'), idx_type='',
                 qsort=None, elastic_url=None):
        ''' Set up parameters to use in the search. L{ElasticQuery} is used to
        define a search query.
        @type  search_query: L{ElasticQuery}
        @keyword search_query: The elastic query to search (default: None).
        @type  aggs: L{Aggs}
        @keyword aggs: Aggregations used in the search.
        @type  search_from: integer
        @keyword search_from: Offset used in paginations (default: 0).
        @type  size: integer
        @keyword size: maximum number of hits to return (default: 20).
        @type search_type: bool
        @keyword search_type: Set search type = count for aggregations.
        @type  idx: string
        @keyword idx: index to search (default: default index defined in settings).
        @type  idx_type: string
        @keyword idx_type: index type (default: '').
        @type  qsort: Sort
        @keyword qsort: defines sorting for the query.
        @type  url: string
        @keyword url: Elastic URL (default: default cluster URL).
        '''
        if search_query is not None:
            if not isinstance(search_query, ElasticQuery):
                raise QueryError("not an ElasticQuery")
            self.query = search_query.query

        if aggs is not None:
            if hasattr(self, 'query'):
                self.query.update(aggs.aggs)
            else:
                self.query = aggs.aggs

        if qsort is not None:
            if not isinstance(qsort, Sort):
                raise QueryError("not a Sort")
            if hasattr(self, 'query'):
                self.query.update(qsort.qsort)
            else:
                logger.error("no query to sort")

        if elastic_url is None:
            elastic_url = ElasticSettings.url()

        self.size = size
        self.search_from = search_from
        self.search_type = search_type
        self.idx = idx
        self.idx_type = idx_type
        self.elastic_url = elastic_url
        if self.search_type is None:
            self.url = (self.idx + '/' + self.idx_type +
                        '/_search?size=' + str(self.size) + '&from='+str(self.search_from))
        else:
            self.url = (self.idx + '/' + self.idx_type + '/_search?search_type='+search_type)

    @classmethod
    def elastic_request(cls, elastic_url, url, data=None, is_post=True):
        ''' Make GET/POST request and return response from elastic server. '''
        try:
            if is_post:
                response = requests.post(elastic_url + '/' + url, data=data)
            else:
                response = requests.get(elastic_url + '/' + url)
        except requests.exceptions.ConnectionError:
            logger.error('ConnectionError ' + elastic_url)
            ElasticUrl.rotate_url()
            elastic_url = ElasticUrl.get_url()
            if is_post:
                response = requests.post(elastic_url + '/' + url, data=data)
            else:
                response = requests.get(elastic_url + '/' + url)
        return response

    @classmethod
    def index_exists(cls, idx, idx_type='', url=None):
        ''' Check if an index exists. '''
        if url is None:
            elastic_url = ElasticSettings.url()
        url = idx + '/' + idx_type + '/_mapping'
        response = Search.elastic_request(elastic_url, url, is_post=False)
        if "error" in response.json():
            logger.warning(response.json())
            return False
        return True

    @classmethod
    def index_refresh(cls, idx, url=None):
        ''' Refresh to make all operations performed since the last refresh
        available for search'''
        if url is None:
            elastic_url = ElasticSettings.url()
        response = Search.elastic_request(elastic_url, idx + '/_refresh')
        if "error" in response.json():
            logger.warning(response.content.decode("utf-8"))
            return False
        return True

    @classmethod
    def range_overlap_query(cls, seqid, start_range, end_range,
                            search_from=0, size=20, idx=ElasticSettings.idx('DEFAULT'),
                            field_list=None, seqid_param="seqid", start_param="start", end_param="end"):
        ''' Constructs a range overlap query '''
        from elastic import utils
        query = utils.ElasticUtils.range_overlap_query(seqid, start_range, end_range, field_list=field_list,
                                                       seqid_param=seqid_param, start_param=start_param,
                                                       end_param=end_param)
        return cls(search_query=query, search_from=search_from, size=size, idx=idx)

    @classmethod
    def field_search_query(cls, query_term, aggs=None, fields=None, search_from=0,
                           size=20, idx=ElasticSettings.idx('DEFAULT')):
        ''' Constructs a field elastic query '''
        query = ElasticQuery.query_string(query_term, fields=fields)
        return cls(search_query=query, aggs=aggs, search_from=search_from, size=size, idx=idx)

    def get_mapping(self, mapping_type=None):
        ''' Return the mappings for an index (host:port/{index}/_mapping/{type}). '''
        self.mapping_url = (self.idx + '/_mapping')
        if mapping_type is not None:
            self.mapping_url += '/'+mapping_type
        elif self.idx_type is not None:
            self.mapping_url += '/'+self.idx_type
        response = Search.elastic_request(ElasticSettings.url(), self.mapping_url, is_post=False)
        if response.status_code != 200:
            json_err = json.dumps({"error": response.status_code,
                                   "response": response.content.decode("utf-8"),
                                   "url": self.mapping_url})
            logger.warning(json_err)
            return json_err
        return response.json()

    def get_count(self):
        ''' Return the elastic count for a query result '''
        url = self.idx + '/' + self.idx_type + '/_count?'
        data = {}
        if hasattr(self, 'query'):
            data = json.dumps(self.query)
        response = Search.elastic_request(ElasticSettings.url(), url, data=data)
        return response.json()

    def get_json_response(self):
        ''' Return the elastic json response '''
        response = Search.elastic_request(self.elastic_url, self.url, data=json.dumps(self.query))
        logger.debug("curl '" + self.elastic_url + '/' + self.url + "&pretty' -d '" + json.dumps(self.query) + "'")
        if response.status_code != 200:
            logger.warning("Error: elastic response 200:" + self.url)
            json_err = json.dumps({"error": response.status_code,
                                   "response": response.content.decode("utf-8"),
                                   "url": self.url})
            return json_err
        return response.json()

    def search(self, obj_document=ElasticSettings.get_document_factory()):
        ''' Run the search and return a L{Result} that stores the
        L{Document} and L{Aggregation} objects.
        @type  obj_document: L{Document}
        @keyword obj_document: Document object.
        '''
        json_response = self.get_json_response()
        hits = json_response['hits']['hits']
        docs = [obj_document(hit) for hit in hits]
        aggs = Aggregation.build_aggs(json_response)
        return Result(took=json_response['took'],
                      hits_total=json_response['hits']['total'],
                      size=self.size, docs=docs, aggs=aggs,
                      idx=self.idx, query=self.query)


class Sort():
    ''' Specify the sorting by specific fields. e.g. Sort('_score'), Sort('seq:desc').
    U{Sort<https://www.elastic.co/guide/en/elasticsearch/reference/current/search-request-sort.html>}
    '''
    def __init__(self, sort_by):
        ''' Given a comma separate string of field names, create the sort. Default
        sort is desc but can be assigned e.g. Sort('seq:asc,start). Alternatively
        more complex sorts can be constructed by providing a dictionary.  '''
        if isinstance(sort_by, str):
            if ',' in sort_by:
                sort_list = sort_by.split(',')
            else:
                sort_list = [sort_by]
            expanded_sort = {"sort": []}
            for s in sort_list:
                if ':' in s:
                    sort_parts = s.split(':')
                    expanded_sort["sort"].append({sort_parts[0]: sort_parts[1]})
                else:
                    expanded_sort["sort"].append(s)
            self.qsort = expanded_sort
        elif isinstance(sort_by, dict):
            self.qsort = sort_by
        else:
            raise QueryError("sort by option not recognised: " + str(sort_by))


class ScanAndScroll(object):
    ''' Use Elastic scan and scroll api. '''

    @classmethod
    def scan_and_scroll(self, idx, call_fun=None, idx_type='', url=None,
                        time_to_keep_scoll=1, query=None):
        ''' Scan and scroll an index and optionally provide a function argument to
        process the hits. '''
        if url is None:
            url = ElasticSettings.url()

        url_search_scan = (idx + '/' + idx_type + '/_search?search_type=scan&scroll=' +
                           str(time_to_keep_scoll) + 'm')
        if query is None:
            query = {
                "query": {"match_all": {}},
                "size":  1000
            }
        else:
            if not isinstance(query, ElasticQuery):
                raise QueryError("not a Query")
            query = query.query

        response = Search.elastic_request(url, url_search_scan, data=json.dumps(query))
        _scroll_id = response.json()['_scroll_id']
        url_scan_scroll = '_search/scroll?scroll=' + str(time_to_keep_scoll) + 'm'

        count = 0
        while True:
            response = Search.elastic_request(url, url_scan_scroll, data=_scroll_id)
            _scroll_id = response.json()['_scroll_id']
            hits = response.json()['hits']['hits']
            nhits = len(hits)
            if nhits == 0:
                break
            count += nhits
            if call_fun is not None:
                call_fun(response.json())
        logger.debug("Scanned No. Docs ( "+idx+"/"+idx_type+" ) = "+str(count))


class Suggest(object):
    ''' Suggest handles requests for populating search auto completion. '''

    @classmethod
    def suggest(cls, term, idx, elastic_url=ElasticSettings.url(),
                name='data', field='suggest', context=None, size=5):
        ''' Auto completion suggestions for a given term. '''
        if elastic_url is None:
            elastic_url = ElasticSettings.url()

        url = (idx + '/' + '/_suggest')
        suggest = {
            name: {
                "text": term,
                "completion": {
                    "field": field,
                    "size": size
                }
            }
        }
        if context is not None:
            suggest[name]['completion'].update(context)
        response = Search.elastic_request(elastic_url, url, data=json.dumps(suggest))
        logger.debug("curl -XPOST '" + elastic_url + '/' + url + "' -d '" + json.dumps(suggest) + "'")
        if response.status_code != 200:
            logger.warning("Suggeter Error: elastic response 200:" + url)
            logger.warning(response.json())
        return response.json()


class Update(object):
    ''' Update API. '''

    @classmethod
    def update_doc(cls, doc, part_doc, elastic_url=None):
        ''' Update a document with a partial document.  '''
        if elastic_url is None:
            elastic_url = ElasticSettings.url()
        url = (doc._meta['_index'] + '/' +
               doc.type() + '/' + doc._meta['_id'] + '/_update')
        response = Search.elastic_request(elastic_url, url, data=json.dumps(part_doc))

        logger.debug("curl -XPOST '" + elastic_url + url + "' -d '" + json.dumps(part_doc) + "'")
        if response.status_code != 200:
            logger.warning("Error: elastic response 200:" + url)
            logger.warning(response.json())
        return response.json()


class Delete(object):

    @classmethod
    def docs_by_query(cls, idx, idx_type='', query=Query.match_all()):
        ''' Delete all documents specified by a Query. '''
        def delete_docs(resp_json):
            hits = resp_json['hits']['hits']
            json_data = ''
            for hit in hits:
                json_data += '{"delete": {"_index": "%s", "_type": "%s", "_id": "%s"}}\n' % \
                             (hit['_index'], hit['_type'], hit['_id'])
            Bulk.load(idx, idx_type, json_data)

        query = ElasticQuery(query, sources='_id')
        ScanAndScroll.scan_and_scroll(idx, idx_type=idx_type, call_fun=delete_docs, query=query)


class Bulk(object):
    ''' Bulk API. '''

    @classmethod
    def load(self, idx, idx_type, json_data, elastic_url=None):
        ''' Bulk load documents. '''
        if elastic_url is None:
            elastic_url = ElasticSettings.url()
        resp = requests.put(ElasticSettings.url()+'/' + idx+'/' + idx_type +
                            '/_bulk', data=json_data)
        if(resp.status_code != 200):
            logger.error('ERROR: '+idx+' load status: '+str(resp.status_code)+' '+str(resp.content))

        # report errors found during loading
        if 'errors' in resp.json() and resp.json()['errors']:
            logger.error("ERROR: bulk load error found")
            for item in resp.json()['items']:
                for key in item.keys():
                    if 'error' in item[key]:
                        logger.error("ERROR LOADING:")
                        logger.error(item)
        return resp


class ElasticQuery():
    ''' Takes a Query to be used to construct Elastic query which can be
    used in L{Search<elastic_model.Search>}.

    I{Advanced options:}
    Sources can be defined to set the fields that operations return (see
    U{source filtering<www.elastic.co/guide/en/elasticsearch/reference/current/search-request-source-filtering.html>}).
    Also
    U{highlighting<www.elastic.co/guide/en/elasticsearch/reference/current/search-request-highlighting.html>}
    can be defined for one or more fields in search results.  '''

    def __init__(self, query, sources=None, highlight=None):
        ''' Query the elastic server for given elastic query.

        @type  query: Query
        @param query: The query to build the ElasticQuery from.
        @type  sources: array of result fields
        @keyword sources: The _source filtering to be used (default: None).
        @type  highlight: Highlight
        @keyword highlight: Define the highlighting of results (default: None).
        '''
        if not isinstance(query, Query):
            raise QueryError("not a Query")
        self.query = {"query": query.query}
        if sources is not None:
            self.query["_source"] = sources
        if highlight is not None:
            if not isinstance(highlight, Highlight):
                raise QueryError("not a Highlight")
            self.query.update(highlight.highlight)

    @classmethod
    def bool(cls, query_bool, sources=None, highlight=None):
        ''' Factory method for creating elastic Bool Query.

        @type  query_bool: L{BoolQuery}
        @param query_bool: The bool query to build the ElasticQuery from.
        @type  sources: array of result fields
        @keyword sources: The _source filtering to be used (default: None).
        @type  highlight: L{Highlight}
        @keyword highlight: Define the highlighting of results (default: None).
        @return L{ElasticQuery}
        '''
        if not isinstance(query_bool, BoolQuery):
            raise QueryError("not a BoolQuery")
        return cls(query_bool, sources, highlight)

    @classmethod
    def filtered_bool(cls, query_match, query_bool, sources=None, highlight=None):
        ''' Factory method for creating an elastic
        U{Filtered Query<www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-filtered-query.html>}
        (L{FilteredQuery<elastic_model.FilteredQuery>}) using a Bool filter.

        @type  query_bool: Query
        @param query_bool: The query to be used.
        @type  query_bool: BoolQuery
        @param query_bool: The bool query to used in the filter.
        @type  sources: array of result fields
        @keyword sources: The _source filtering to be used (default: None).
        @type  highlight: Highlight
        @keyword highlight: Define the highlighting of results (default: None).
        @return: L{ElasticQuery}
        '''
        if not isinstance(query_bool, BoolQuery):
            raise QueryError("not a BoolQuery")
        return ElasticQuery.filtered(query_match, Filter(query_bool), sources, highlight)

    @classmethod
    def filtered(cls, query_match, query_filter, sources=None, highlight=None):
        ''' Factory method for creating an elastic
        U{Filtered Query<www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-filtered-query.html>}
        (L{FilteredQuery<elastic_model.FilteredQuery>}).

        @type  query_bool: Query
        @param query_bool: The query to be used.
        @type  query_filter: Filter
        @param query_filter: The filter to be used.
        @type  sources: array of result fields
        @keyword sources: The _source filtering to be used (default: None).
        @type  highlight: Highlight
        @keyword highlight: Define the highlighting of results (default: None).
        @return: L{ElasticQuery}
        '''

        query = FilteredQuery(query_match, query_filter)
        return cls(query, sources, highlight)

    @classmethod
    def has_parent(cls, parent_type, query, sources=None, highlight=None):
        ''' Factory method for creating an elastic
        U{Has Parent Query<www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-has-parent-query.html>}.

        @type  parent_type: str
        @param parent_type: Parent type.
        @type  query_bool: Query
        @param query_bool: The query to be used.
        @type  sources: array of result fields
        @keyword sources: The _source filtering to be used (default: None).
        @type  highlight: Highlight
        @keyword highlight: Define the highlighting of results (default: None).
        @return: L{ElasticQuery}
        '''
        return cls(HasParentQuery(parent_type, query), sources, highlight)

    @classmethod
    def has_child(cls, child_type, query, sources=None, highlight=None):
        ''' Factory method for creating an elastic
        U{Has Child Query<www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-has-child-query.html>}.

        @type  parent_type: str
        @param parent_type: Child type.
        @type  query_bool: Query
        @param query_bool: The query to be used.
        @type  sources: array of result fields
        @keyword sources: The _source filtering to be used (default: None).
        @type  highlight: Highlight
        @keyword highlight: Define the highlighting of results (default: None).
        @return: L{ElasticQuery}
        '''
        return cls(HasChildQuery(child_type, query), sources, highlight)

    @classmethod
    def query_string(cls, query_term, sources=None, highlight=None, query_filter=None, **string_opts):
        ''' Factory method for creating elastic Query String Query.

        @type  query_term: string
        @param query_term: The string to use in the query.
        @type  sources: array of result fields
        @keyword sources: The _source filtering to be used (default: None).
        @type  highlight: Highlight
        @keyword highlight: Define the highlighting of results (default: None).
        @type query_filter: Filter
        @keyword query_filter: Optional filter for query.
        @return: L{ElasticQuery}
        '''
        if query_filter is None:
            query = Query.query_string(query_term, **string_opts)
        else:
            query = FilteredQuery(Query.query_string(query_term, **string_opts), query_filter)
        return cls(query, sources, highlight)

    @classmethod
    def query_match(cls, match_id, match_str, sources=None, highlight=None):
        ''' Factory method for creating elastic Match Query.

        @type  match_id: string
        @param match_id: The match id.
        @type  match_str: string
        @param match_str: The string value to match.
        @type  sources: array of result fields
        @keyword sources: The _source filtering to be used (default: None).
        @type  highlight: Highlight
        @keyword highlight: Define the highlighting of results (default: None).
        @return: L{ElasticQuery}
        '''
        query = Query.match(match_id, match_str)
        return cls(query, sources, highlight)


class Highlight():
    ''' Used in highlighting search result fields, see U{Elastic highlighting docs
    <www.elastic.co/guide/en/elasticsearch/reference/current/search-request-highlighting.html>}.
    '''
    def __init__(self, fields, pre_tags=None, post_tags=None, number_of_fragments=None, fragment_size=None):
        ''' Highlight one or more fields in the search results. '''
        if not isinstance(fields, list):
            fields = [fields]
        self.highlight = {"highlight": {"fields": {}}}
        for field in fields:
            self.highlight["highlight"]["fields"][field] = {}

        if pre_tags is not None:
            if not isinstance(pre_tags, list):
                pre_tags = [pre_tags]
            self.highlight["highlight"].update({"pre_tags": pre_tags})
        if post_tags is not None:
            if not isinstance(post_tags, list):
                post_tags = [post_tags]
            self.highlight["highlight"].update({"post_tags": post_tags})
        if number_of_fragments is not None:
            self.highlight["highlight"].update({"number_of_fragments": number_of_fragments})
        if fragment_size is not None:
            self.highlight["highlight"].update({"fragment_size": fragment_size})
