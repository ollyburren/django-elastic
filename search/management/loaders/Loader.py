import gzip
import json
import requests
from django.conf import settings
import re


class Loader:

    KEYWORD_ANALYZER = \
        {"analysis":
         {"analyzer":
          {"full_name":
           {"filter": ["standard", "lowercase"],
            "tokenizer": "keyword"}
           }
          }
         }

    def mapping(self, mapping_json, analyzer=None, **options):
        ''' Put the mapping to the Elastic server '''
        index_name = self.get_index_name(**options)
        resp = requests.get(settings.SEARCH_ELASTIC_URL + '/' + index_name)
        if(resp.status_code == 200):
            print('WARNING: '+index_name + ' mapping already exists!')

        if analyzer is not None:
            mapping_json = self.append_analyzer(mapping_json, analyzer)
        resp = requests.put(settings.SEARCH_ELASTIC_URL+'/' + index_name, data=json.dumps(mapping_json))

        if(resp.status_code != 200):
            print('WARNING: ' + index_name + ' mapping status: ' + str(resp.status_code))

    def append_analyzer(self, json, analyzer):
        ''' Append analyzer to mapping '''
        json['settings'] = analyzer
        return json

    def get_index_name(self, **options):
        ''' Get indexName option '''
        if options['indexName']:
            return options['indexName'].lower()
        return self.__class__.__name__

    def open_file_to_load(self, file_name, **options):
        ''' Open the given file '''
        if options[file_name].endswith('.gz'):
            return gzip.open(options[file_name], 'rb')
        else:
            return open(options[file_name], 'rb')


class DelimeterLoader(Loader):

    def load(self, column_names, file_handle, idx_name, idx_type='tab', delim='\t',
             is_GFF=False, is_GTF=False):
        ''' Index tab data '''
        json_data = ''
        line_num = 0
        auto_num = 1

        try:
            for line in file_handle:
                line = line.rstrip().decode("utf-8")
                current_line = line
                if(current_line.startswith("#")):
                    continue
                parts = re.split(delim, current_line)
                if len(parts) != len(column_names):
                    continue

                idx_id = str(auto_num)
                json_data += '{"index": {"_id": "%s"}}\n' % idx_id

                doc_data = {}
                attrs = {}
                for idx, p in enumerate(parts):
                    if (is_GFF or is_GTF) and idx == len(parts)-1:
                        if is_GTF:
                            attrs = self._getAttributes(p, key_value_delim=' ')
                        else:
                            attrs = self._getAttributes(p)
                        doc_data[column_names[idx]] = attrs
                        continue

                    if p.isdigit():
                        doc_data[column_names[idx]] = int(p)
                    elif self._isfloat(p):
                        doc_data[column_names[idx]] = float(p)
                    else:
                        doc_data[column_names[idx]] = p

                json_data += json.dumps(doc_data) + '\n'

                line_num += 1
                auto_num += 1
                if(line_num > 5000):
                    line_num = 0
                    print('.', end="", flush=True)
                    requests.put(settings.SEARCH_ELASTIC_URL+'/' + idx_name+'/' + idx_type +
                                 '/_bulk', data=json_data)
                    json_data = ''
        finally:
            requests.put(settings.SEARCH_ELASTIC_URL+'/' + idx_name+'/' + idx_type +
                         '/_bulk', data=json_data)

    def _getAttributes(self, attrs, key_value_delim='='):
        ''' Parse the attributes column '''
        parts = re.split(';', attrs)
        attrs_arr = {}
        for p in parts:
            if(p == ''):
                continue
            at = re.split(key_value_delim, p.strip())
            if len(at) == 2:
                attrs_arr[at[0]] = at[1]
            else:
                attrs_arr[at[0]] = ""
        return attrs_arr

    def _isfloat(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False
