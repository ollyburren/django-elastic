from django.test import TestCase
from django.conf import settings
import requests


class EsTest(TestCase):
    '''
    Test elasticsearch server is running and status
    '''
    def test_es(self):
        try:
            resp = requests.get(settings.ELASTICSEARCH_URL +
                                '/_cluster/health/'+settings.MARKERDB)
            self.assertEqual(resp.status_code, 200, "Health page status code")
            self.assertFalse(resp.json()['status'] == 'red',
                             'Health report - red')
        except requests.exceptions.Timeout:
            self.assertTrue(False, 'timeout exception')
        except requests.exceptions.TooManyRedirects:
            self.assertTrue(False, 'too many redirects exception')
        except requests.exceptions.ConnectionError:
            self.assertTrue(False, 'request connection exception')
        except requests.exceptions.RequestException:
            self.assertTrue(False, 'request exception')

    '''
    Test a single SNP search
    '''
    def test_snp_search(self):
        resp = self.client.get('/search/rs333/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('data' in resp.context)
        snp = resp.context['data'][0]
        self._SNPtest(snp)

    '''
    Test a wild card search
    '''
    def test_snp_wildcard(self):
        resp = self.client.get('/search/rs33311*/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('data' in resp.context)

        for snp in resp.context['data']:
            self._SNPtest(snp)

    '''
    Test a range query
    '''
    def test_range(self):
        resp = self.client.get('/search/chr4:10000-10050/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('data' in resp.context)

        for snp in resp.context['data']:
            self._SNPtest(snp)

    '''
    Test the elements of a SNP result
    '''
    def _SNPtest(self, snp):
        self.assertTrue(snp['POS'])
        self.assertTrue(snp['ID'])
        self.assertTrue(snp['REF'])
        self.assertTrue(snp['ALT'])
        self.assertTrue(snp['SRC'])

        self.assertTrue(isinstance(snp['POS'], int))

    '''
    Test Region Index
    '''
    def test_region_index(self):
        index_name = settings.REGIONDB
        try:
            # Test if region index exists
            resp = requests.head(settings.ELASTICSEARCH_URL + '/' + index_name)
            self.assertEqual(resp.status_code, 200, "Region Index " +
                             index_name + "exists")
            # Test if type aa exists
            index_type = 'aa'
            resp = requests.head(settings.ELASTICSEARCH_URL +
                                 '/' + index_name +
                                 '/' + index_type)
            self.assertEqual(resp.status_code, 200, "Region Index: " +
                             index_name + " and Region Index Type: " +
                             index_type + " exists")
            # Test if type celiac exists
            index_type = 'cel'
            resp = requests.head(settings.ELASTICSEARCH_URL +
                                 '/' + index_name +
                                 '/' + index_type)
            self.assertEqual(resp.status_code, 200, "Region Index: " +
                             index_name + " and Region Index Type: " +
                             index_type + " exists")
            # Test if type t1d exists
            index_type = 't1d'
            resp = requests.head(settings.ELASTICSEARCH_URL + '/' +
                                 index_name + '/' + index_type)
            self.assertEqual(resp.status_code, 200, "Region Index " +
                             index_name + "exists")
        except requests.exceptions.Timeout:
            self.assertTrue(False, 'timeout exception')
        except requests.exceptions.TooManyRedirects:
            self.assertTrue(False, 'too many redirects exception')
        except requests.exceptions.ConnectionError:
            self.assertTrue(False, 'request connection exception')
        except requests.exceptions.RequestException:
            self.assertTrue(False, 'request exception')
