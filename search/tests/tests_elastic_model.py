from django.test import TestCase, override_settings
from django.core.management import call_command
from search.tests.settings_idx import IDX
import requests
from search.elastic_model import Elastic
from search.elastic_settings import ElasticSettings


@override_settings(SEARCH={'default': {'IDX': {'DEFAULT': IDX['MARKER']['indexName']},
                                       'ELASTIC_URL': ElasticSettings.url()}})
def setUpModule():
    ''' Load test indices (marker) '''
    call_command('index_search', **IDX['MARKER'])


@override_settings(SEARCH={'default': {'IDX': {'DEFAULT': IDX['MARKER']['indexName']},
                                       'ELASTIC_URL': ElasticSettings.url()}})
def tearDownModule():
    ''' Remove test indices '''
    requests.delete(ElasticSettings.url() + '/' + IDX['MARKER']['indexName'])


@override_settings(SEARCH={'default': {'IDX': {'DEFAULT': IDX['MARKER']['indexName']},
                                       'ELASTIC_URL': ElasticSettings.url()}})
class ElasticModelTest(TestCase):

    def test_mapping(self):
        elastic = Elastic(db=ElasticSettings.idx('DEFAULT'))
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