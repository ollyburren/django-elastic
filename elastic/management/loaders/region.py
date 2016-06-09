'''
Created on 28 Jan 2016

@author: ellen
'''
import csv
import json
import re

from elastic.elastic_settings import ElasticSettings
from elastic.query import Query, BoolQuery, RangeQuery
from elastic.search import ElasticQuery, Search, Sort, Delete


class RegionManager(object):
    '''
    classdocs
    '''

    def add_study_data(self, **options):
        ''' add gwas stats from a study '''
        study = options['study_id']
        file = options['addStudyData']
        message = ""
        print("Deleting study hits for "+study)
        Delete.docs_by_query(ElasticSettings.idx('REGION', 'STUDY_HITS'), query=Query.term("dil_study_id", study))

        with open(file, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in reader:
                if row[0] == 'Marker':
                    continue
                # 0 - Marker
                # 1 - disease
                # 2 - Chromosome
                # 3 - Region Start
                # 4 - Region End
                # 5 - Position
                # 6 - Strand
                # 7 - Major Allele
                # 8 - Minor allele
                # 9 - Minor allele frequency
                # 10 - Discovery P value
                # 11 - Discovery Odds ratio
                # 12 - Discovery 95% confidence interval lower limit
                # 13 - Discovery 95% confidence interval upper limit
                # 14 - Replication P value
                # 15 - Replication Odds ratio
                # 16 - Replication 95% confidence interval lower limit
                # 17 - Replication 95% confidence interval upper limit
                # 18 - Combined P value
                # 19 - Combined Odds ratio
                # 20 - Combined 95% confidence interval lower limit
                # 21 - Combined 95% confidence interval upper limit
                # 22 - PP Colocalisation
                # 23 - Gene
                # 24 - PubMed ID
                # 25 - Other Signal
                # 26 - Notes
                # 27 - Curation status/ failed quality control

                query = ElasticQuery(Query.match("id", row[0]))
                result = Search(search_query=query, idx=ElasticSettings.idx('MARKER', 'MARKER')).search()
                if result.hits_total == 0:
                    result2 = Search(search_query=ElasticQuery(Query.match("rshigh", row[0])),
                                     idx=ElasticSettings.idx('MARKER', 'HISTORY')).search()
                    if result2.hits_total > 0:
                        history_doc = result2.docs[0]
                        new_id = getattr(history_doc, "rscurrent")
                        query = ElasticQuery(Query.match("id", new_id))
                        result = Search(search_query=query, idx=ElasticSettings.idx('MARKER', 'MARKER')).search()

                if result.hits_total != 1:
                    message += "ERROR loading row of gwas data for "+row[0]+" - Marker cannot be found; <br />\n"

                marker = result.docs[0]

                query = ElasticQuery(Query.match("code", row[1]))
                result = Search(query, idx=ElasticSettings.idx('DISEASE', 'DISEASE')).search()
                if result.hits_total != 1:
                    message += "ERROR loading row of gwas data for "+row[0]+" - Disease cannot be found; <br />\n"
                    continue
                disease = result.docs[0]

                if not re.match(r"^\w$", row[7]):
                    message += "ERROR loading row of gwas data for "+row[0]+" - Major allele is not set; <br />\n"
                    continue
                if not re.match(r"^\w$", row[8]):
                    message += "ERROR loading row of gwas data for "+row[0]+" - Minor allele is not set; <br />\n"
                    continue
                if float(row[9]) > 0.5:
                    message += "WARNING - MAF for "+row[0]+" is >0.5; <br />\n"

                strand = row[6]
                if re.match(r"\d", strand):
                    strand = '+' if strand > 0 else '-'
                row[6] = strand

                if not re.match(r"\d+", row[2]): row[2] = getattr(marker, "seqid")
                if not re.match(r"\d+", row[5]): row[5] = getattr(marker, "start")
                if not row[5] == getattr(marker, "start"): row[5] = getattr(marker, "start")

                data = {
                    "chr_band": self._get_chr_band(row[2], row[5]),
                    "other_signal": row[25],
                    "species": "Human",
                    "disease": getattr(disease, "code"),
                    "notes": row[26],
                    "disease_locus": "TBC",
                    "dil_study_id": study,
                    "marker": getattr(marker, "id"),
                    "status": "N",
                    "pp_probability": row[22],
                    "tier": 100,
                    "pmid": row[24],
                    "genes": self._get_ens_gene(row[23])
                    }

                build_info = self._get_current_build_info(row[2], row[5])
                data['build_info'] = [build_info]

                data['p_values'] = {
                    'discovery': row[10],
                    'replication': row[14],
                    'combined': row[18]
                }

                data['odds_ratios'] = {
                    'discovery': {
                        "or": row[11],
                        "lower": row[12],
                        "upper": row[13]
                    },
                    'replication': {
                        "or": row[15],
                        "lower": row[16],
                        "upper": row[17]
                    },
                    'combined': {
                        "or": row[19],
                        "lower": row[20],
                        "upper": row[21]
                    }
                }

                data['alleles'] = {
                    'major': row[7],
                    'minor': row[8],
                    'maf': row[9]
                }

                data['suggest'] = {
                    'input': [],
                    'weight': 1
                }

                r = Search.elastic_request(ElasticSettings.url(), ElasticSettings.idx('REGION', 'STUDY_HITS'),
                                           json.dumps(data))
                if r.status_code != 201:
                    message += "ERROR loading row of gwas data for "+row[0]+" - Failed to create document; <br />\n"

        print("\n\n"+message)

    def _get_ens_gene(self, gene_list):
        genes = re.sub("__", " ",  gene_list)
        query = ElasticQuery(Query.query_string(genes))
        result = Search(query, idx=ElasticSettings.idx('GENE', 'GENE')).search()
        return [doc.doc_id() for doc in result.docs]

    def _get_chr_band(self, seqid, position):
        ''' Get chr band for a given chr/position '''
        if seqid == 6 and position >= 24891793 and position <= 34924245:
            return 'MHC'

        query = ElasticQuery(BoolQuery(must_arr=[
                                                 Query.match("seqid", seqid),
                                                 RangeQuery("start", lte=position),
                                                 RangeQuery("stop", gte=position)
                                                 ]))
        result = Search(query, idx=ElasticSettings.idx('BAND', 'BAND'), size=1).search()
        return (getattr(result.docs[0], "seqid") + getattr(result.docs[0], "name"))

    def _get_current_build_info(self, seqid, position):
        ''' Get upper & lower boundaries for a hit given the position of the marker.'''

        query = ElasticQuery(BoolQuery(must_arr=[
                                                 RangeQuery("position", gte=position),
                                                 Query.match("seqid", seqid)
                                                 ]))
        result = Search(query, idx=ElasticSettings.idx('HAPMAP', 'HAPMAP'), qsort=Sort('position:asc'), size=1).search()
        genetic_map_position = getattr(result.docs[0], "genetic_map_position")

        query = ElasticQuery(BoolQuery(must_arr=[
                                                 RangeQuery("genetic_map_position", gte=(genetic_map_position+0.1)),
                                                 Query.match("seqid", seqid)
                                                 ]))
        result = Search(query, idx=ElasticSettings.idx('HAPMAP', 'HAPMAP'), qsort=Sort('position:asc'), size=1).search()
        start = int(getattr(result.docs[0], "position"))

        query = ElasticQuery(BoolQuery(must_arr=[
                                                 RangeQuery("genetic_map_position", lte=(genetic_map_position-0.1)),
                                                 Query.match("seqid", seqid)
                                                 ]))
        result = Search(query, idx=ElasticSettings.idx('HAPMAP', 'HAPMAP'),
                        qsort=Sort('position:desc'), size=1).search()
        end = int(getattr(result.docs[0], "position"))

        build_info = {
            'build': 38,
            'seqid': seqid,
            'start': start,
            'end': end
        }
        return build_info
