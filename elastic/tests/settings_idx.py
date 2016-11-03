''' Settings used for the tests. '''
import os
from elastic.elastic_settings import ElasticSettings

SEARCH_BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SEARCH_TEST_DATA_PATH = os.path.join(SEARCH_BASE_DIR, 'tests/data/')
SEARCH_SUFFIX = ElasticSettings.getattr('TEST')
if SEARCH_SUFFIX is None:
    SEARCH_SUFFIX = "test"

NUMBER_OF_SHARDS = 1

IDX = {'GENE': {'indexName': 'test__gene_'+SEARCH_SUFFIX,
                'indexGene': SEARCH_TEST_DATA_PATH+'genenames.org.test.txt.gz', 'shards': NUMBER_OF_SHARDS},
       'MARKER': {'indexName': 'test__snp_'+SEARCH_SUFFIX,
                  'indexSNP': SEARCH_TEST_DATA_PATH+'dbsnp144_test.vcf.gz', 'shards': NUMBER_OF_SHARDS},
       'MARKER_RS_HISTORY': {'indexName': 'test__snp_'+SEARCH_SUFFIX, 'indexType': 'rs_merge',
                             'indexSNPMerge': SEARCH_TEST_DATA_PATH+'rs_merge_test.gz', 'shards': NUMBER_OF_SHARDS},
       'JSON': {'indexName': 'test__json_'+SEARCH_SUFFIX, 'indexType': 't1d',
                'indexJson': SEARCH_TEST_DATA_PATH+'publications.json', 'shards': NUMBER_OF_SHARDS},
       'JSON_MARKER_IC': {'indexName': 'test__snp_'+SEARCH_SUFFIX, 'indexType': 'immunochip',
                          'indexJson': SEARCH_TEST_DATA_PATH+'marker_ic.json', 'shards': NUMBER_OF_SHARDS},
       'JSON_NESTED': {'indexName': 'test__json_nested_'+SEARCH_SUFFIX, 'indexType': 'hits',
                       'indexJson': SEARCH_TEST_DATA_PATH+'nested.json', 'shards': NUMBER_OF_SHARDS},
       'BED_GENERIC': {'indexName': 'test__bed_'+SEARCH_SUFFIX, 'indexType': 'bed',
                       'indexBED': SEARCH_TEST_DATA_PATH+'test.bed', 'shards': NUMBER_OF_SHARDS},
       'GFF_GENERIC': {'indexName': 'test__gff_'+SEARCH_SUFFIX, 'indexType': 'gff',
                       'indexGFF': SEARCH_TEST_DATA_PATH+'test.gff.gz', 'shards': NUMBER_OF_SHARDS},
       'GTF_GENERIC': {'indexName': 'test__gtf_'+SEARCH_SUFFIX, 'indexType': 'gtf',
                       'indexGFF': SEARCH_TEST_DATA_PATH+'test.gtf.gz', 'isGTF': True, 'shards': NUMBER_OF_SHARDS},
       'GFF_ERR': {'indexName': 'test__err__gff_'+SEARCH_SUFFIX, 'indexType': 'gff',
                   'indexGFF': SEARCH_TEST_DATA_PATH+'test_error.gff.gz', 'shards': NUMBER_OF_SHARDS},
       'GENE_TARGET': {'indexName': 'test__gene_target_'+SEARCH_SUFFIX,
                       'indexGTarget': SEARCH_TEST_DATA_PATH+'gene_targets.tab.gz', 'shards': NUMBER_OF_SHARDS},
#       'T1D_CRITERIA': {'indexName': 'test__t1d_criteria_'+SEARCH_SUFFIX, 'indexProject': 't1dbase',
#                        'indexCriteria': 'true', 'applyFilter': '1', 'shards': NUMBER_OF_SHARDS},
#       'IMB_CRITERIA': {'indexName': 'test__imb_criteria_'+SEARCH_SUFFIX, 'indexProject': 'immunobase',
#                        'indexCriteria': 'true', 'applyFilter': '1', 'shards': NUMBER_OF_SHARDS},
       'GENE_ALIAS': {'indexName': 'test__gene_alias_'+SEARCH_SUFFIX,
                      'indexAlias': SEARCH_TEST_DATA_PATH + 'alias_test_dir',
                      'indexFeatureType': 'gene', 'shards': NUMBER_OF_SHARDS},
       'LOCUS_ALIAS': {'indexName': 'test__locus_alias_'+SEARCH_SUFFIX,
                       'indexAlias': SEARCH_TEST_DATA_PATH + 'alias_test_dir',
                       'indexFeatureType': 'locus', 'shards': NUMBER_OF_SHARDS},
       'MARKER_ALIAS': {'indexName': 'test__marker_alias_'+SEARCH_SUFFIX,
                        'indexAlias': SEARCH_TEST_DATA_PATH + 'alias_test_dir',
                        'indexFeatureType': 'marker', 'shards': NUMBER_OF_SHARDS},
       'STUDY_ALIAS': {'indexName': 'test__study_alias_'+SEARCH_SUFFIX,
                       'indexAlias': SEARCH_TEST_DATA_PATH + 'alias_test_dir',
                       'indexFeatureType': 'study', 'shards': NUMBER_OF_SHARDS},
       'PRIVATE_REGIONS_GFF': {'indexName': 'test__private_regions_gff_'+SEARCH_SUFFIX, 'indexType': 'gff',
                               'indexGFF': SEARCH_TEST_DATA_PATH+'private_regions.gff.gz', 'shards': NUMBER_OF_SHARDS},
       }

IDX_UPDATE = {'GENE_UPDATE': {'indexName': 'test__gene_'+SEARCH_SUFFIX, 'build': 'GRCh38',
                              'indexGeneGFF': SEARCH_TEST_DATA_PATH+'genespan.gff.gz'},
              }

OVERRIDE_SETTINGS = \
    {'default':
        {'IDX':
            {'MARKER': IDX['MARKER']['indexName'],
             'DEFAULT': IDX['MARKER']['indexName'],
             'GFF_GENES': IDX['GFF_GENERIC']['indexName']
             },
         'ELASTIC_URL': ElasticSettings.url()}
     }

OVERRIDE_SETTINGS2 = \
   {'default': {
        'IDX': {
            'MARKER': {
                'name': 'dbsnp144',
                'idx_type': {
                    'MARKER': {'type': 'marker', 'description': 'dbsnp', 'search': True, 'auth_public': True},
                },
                'label': 'marker storage',
                'auth_public': True,
                'suggester': True
            }
        },
        'ELASTIC_URL': ElasticSettings.url()}
    }

OVERRIDE_SETTINGS3 = \
    {'default': {
        'ELASTIC_URL': ['http://xxx:9200/'],
        'IDX': {'MARKER': IDX['MARKER']['indexName']}}
     }

if isinstance(ElasticSettings.getattr('ELASTIC_URL'), str):
    OVERRIDE_SETTINGS3['default']['ELASTIC_URL'].append(ElasticSettings.getattr('ELASTIC_URL'))
else:
    OVERRIDE_SETTINGS3['default']['ELASTIC_URL'].extend(ElasticSettings.getattr('ELASTIC_URL'))
