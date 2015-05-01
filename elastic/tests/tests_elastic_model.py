from django.test import TestCase, override_settings
from django.core.management import call_command
from elastic.tests.settings_idx import IDX
import requests
from elastic.elastic_model import Search, BoolQuery, Query, ElasticQuery, \
    RangeQuery, OrFilter, AndFilter, Filter, NotFilter, TermsFilter, Highlight
from elastic.elastic_settings import ElasticSettings
import time


@override_settings(ELASTIC={'default': {'IDX': {'DEFAULT': IDX['MARKER']['indexName']},
                                        'ELASTIC_URL': ElasticSettings.url()}})
def setUpModule():
    ''' Load test indices (marker) '''
    call_command('index_search', **IDX['MARKER'])
    time.sleep(2)


@override_settings(ELASTIC={'default': {'IDX': {'DEFAULT': IDX['MARKER']['indexName']},
                                        'ELASTIC_URL': ElasticSettings.url()}})
def tearDownModule():
    ''' Remove test indices '''
    requests.delete(ElasticSettings.url() + '/' + IDX['MARKER']['indexName'])


@override_settings(ELASTIC={'default': {'IDX': {'DEFAULT': IDX['MARKER']['indexName']},
                                        'ELASTIC_URL': ElasticSettings.url()}})
class ElasticModelTest(TestCase):

    def test_idx_exists(self):
        ''' Test that index_exists() method. '''
        self.assertTrue(Search.index_exists(idx=ElasticSettings.idx('DEFAULT')),
                        "Index exists")
        self.assertFalse(Search.index_exists("xyz123"))

    def test_mapping(self):
        ''' Test retrieving the mapping for an index. '''
        elastic = Search(idx=ElasticSettings.idx('DEFAULT'))
        mapping = elastic.get_mapping()
        self.assertTrue(ElasticSettings.idx('DEFAULT') in mapping, "Database name in mapping result")
        if ElasticSettings.idx('DEFAULT') in mapping:
            self.assertTrue("mappings" in mapping[ElasticSettings.idx('DEFAULT')], "Mapping result found")

        # check using the index type
        mapping = elastic.get_mapping('marker')
        self.assertTrue(ElasticSettings.idx('DEFAULT') in mapping, "Database name in mapping result")

        # err check
        mapping = elastic.get_mapping('marker/xx')
        self.assertTrue('error' in mapping, "Database name in mapping result")

    def test_bool_filtered_query(self):
        ''' Test building and running a filtered boolean query. '''
        query_bool = BoolQuery()
        query_bool.must([Query.term("id", "rs373328635")]) \
                  .must_not([Query.term("seqid", 2)]) \
                  .should(RangeQuery("start", gte=10054)) \
                  .should([RangeQuery("start", gte=10050)])
        query = ElasticQuery.filtered_bool(Query.match_all(), query_bool, sources=["id", "seqid"])
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] == 1, "Elastic filtered query retrieved marker (rs373328635)")

    def test_bool_filtered_query2(self):
        ''' Test building and running a filtered boolean query. '''
        query_bool = BoolQuery()
        query_bool.should(RangeQuery("start", lte=20000)) \
                  .should(Query.term("seqid", 2)) \
                  .must(Query.term("seqid", 1))
        query_string = Query.query_string("rs373328635", fields=["id", "seqid"])
        query = ElasticQuery.filtered_bool(query_string, query_bool, sources=["id", "seqid", "start"])
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] == 1, "Elastic filtered query retrieved marker (rs373328635)")

    def test_bool_filtered_query3(self):
        ''' Test building and running a filtered boolean query. Note:
        ElasticQuery used to wrap query_string in a query object. '''
        query_bool = BoolQuery()
        query_bool.should(RangeQuery("start", lte=20000)) \
                  .should(Query.term("seqid", 2)) \
                  .must(Query.query_string("rs373328635", fields=["id", "seqid"]).query_wrap()) \
                  .must(Query.term("seqid", 1))

        query = ElasticQuery.filtered_bool(Query.match_all(), query_bool, sources=["id", "seqid", "start"])
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] == 1, "Elastic filtered query retrieved marker (rs373328635)")

    def test_bool_filtered_query4(self):
        ''' Test building and running a filtered boolean query.
        Note: ElasticQuery used to wrap match in a query object. '''
        query_bool = BoolQuery()
        query_bool.should(RangeQuery("start", lte=20000)) \
                  .should(Query.term("seqid", 2)) \
                  .must(Query.match("id", "rs373328635").query_wrap()) \
                  .must(Query.term("seqid", 1))

        query = ElasticQuery.filtered_bool(Query.match_all(), query_bool, sources=["id", "seqid", "start"])
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] == 1, "Elastic filtered query retrieved marker (rs373328635)")

    def test_or_filtered_query(self):
        ''' Test building and running a filtered query. '''
        highlight = Highlight(["id", "seqid"])
        query_bool = BoolQuery(must_arr=[RangeQuery("start", lte=1),
                                         RangeQuery("end", gte=100000)])
        or_filter = OrFilter(RangeQuery("start", gte=1, lte=100000))
        or_filter.extend(query_bool) \
                 .extend(Query.query_string("rs*", fields=["id", "seqid"]).query_wrap())
        query = ElasticQuery.filtered(Query.term("seqid", 1), or_filter, highlight=highlight)
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] >= 1, "Elastic filtered query retrieved marker(s)")

    def test_and_filtered_query(self):
        ''' Test building and running a filtered query. '''
        query_bool = BoolQuery(must_arr=[RangeQuery("start", gte=1)])
        and_filter = AndFilter(query_bool)
        and_filter.extend(RangeQuery("start", gte=1)) \
                  .extend(Query.term("seqid", 1))
        query = ElasticQuery.filtered(Query.term("seqid", 1), and_filter)
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] >= 1, "Elastic filtered query retrieved marker(s)")

    def test_not_filtered_query(self):
        ''' Test building and running a filtered query. '''
        not_filter = NotFilter(RangeQuery("start", lte=10000))
        query = ElasticQuery.filtered(Query.term("seqid", 1), not_filter)
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] >= 1, "Elastic filtered query retrieved marker(s)")

    def test_term_filtered_query(self):
        ''' Test filtered query with a term filter. '''
        query = ElasticQuery.filtered(Query.term("seqid", 1), Filter(Query.term("id", "rs373328635")))
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] == 1, "Elastic filtered query retrieved marker")

    def test_terms_filtered_query(self):
        ''' Test filtered query with a terms filter. '''
        terms_filter = TermsFilter.get_terms_filter("id", ["rs2476601", "rs373328635"])
        query = ElasticQuery.filtered(Query.term("seqid", 1), terms_filter)
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] >= 1, "Elastic filtered query retrieved marker(s)")

    def test_string_query(self):
        ''' Test building and running a string query. '''
        query = ElasticQuery.query_string("rs2476601", fields=["id"])
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] == 1, "Elastic string query retrieved marker (rs2476601)")

    def test_string_query_with_wildcard(self):
        query = ElasticQuery.query_string("rs*", fields=["id"])
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'), size=5)
        self.assertTrue(elastic.get_result()['total'] > 1, "Elastic string query retrieved marker (rs*)")

    def test_match_query(self):
        ''' Test building and running a match query. '''
        query = ElasticQuery.query_match("id", "rs2476601")
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] == 1, "Elastic string query retrieved marker (rs2476601)")

    def test_term_query(self):
        ''' Test building and running a match query. '''
        query = ElasticQuery(Query.term("id", "rs2476601"))
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] == 1, "Elastic string query retrieved marker (rs2476601)")

        query = ElasticQuery(Query.term("seqid", "1", boost=3.0))
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] > 1, "Elastic string query retrieved markers  on chr1")

    def test_terms_query(self):
        ''' Test building and running a match query. '''
        highlight = Highlight(["id"])
        query = ElasticQuery(Query.terms("id", ["rs2476601", "rs373328635"]), highlight=highlight)
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] == 2,
                        "Elastic string query retrieved markers (rs2476601, rs373328635)")

    def test_bool_query(self):
        ''' Test a bool query. '''
        query_bool = BoolQuery()
        highlight = Highlight(["id", "seqid"])
        query_bool.must(Query.term("id", "rs373328635")) \
                  .must(RangeQuery("start", gt=1000)) \
                  .must_not(Query.match("seqid", "2")) \
                  .should(Query.match("seqid", "3")) \
                  .should(Query.match("seqid", "1"))
        query = ElasticQuery.bool(query_bool, highlight=highlight)
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_result()['total'] == 1, "Elastic string query retrieved marker (rs373328635)")

    def test_string_query_with_wildcard_and_highlight(self):
        highlight = Highlight("id", pre_tags="<strong>", post_tags="</strong>")
        query = ElasticQuery.query_string("rs*", fields=["id"], highlight=highlight)
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'), size=5)
        self.assertTrue(elastic.get_result()['total'] > 1, "Elastic string query retrieved marker (rs*)")

    def test_count(self):
        ''' Test count the number of documents in an index. '''
        elastic = Search(idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_count()['count'] > 1, "Elastic count documents in an index")

    def test_count_with_query(self):
        ''' Test count the number of documents returned by a query. '''
        query = ElasticQuery(Query.term("id", "rs373328635"))
        elastic = Search(query, idx=ElasticSettings.idx('DEFAULT'))
        self.assertTrue(elastic.get_count()['count'] == 1, "Elastic count with a query")
