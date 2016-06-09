from elastic.management.loaders.loader import DelimeterLoader, MappingProperties
import re


class BEDManager(DelimeterLoader):

    def create_load_bed_index(self, **options):
        ''' Index bed data '''
        self._create_bed_mapping(**options)
        idx_name = self.get_index_name(**options)
        idx_type = self._get_index_type(**options)
        f = self.open_file_to_load('indexBED', **options)
        column_names = ["seqid", "start", "end", "name", "score", "strand",
                        "thickStart", "thickEnd", "itemRgb", "blockCount", "blockSizes", "blockStarts"]
        line = f.readline().decode("utf-8")
        parts = re.split('\t', line)
        column_names = column_names[:len(parts)]
        self.load(column_names, f, idx_name, idx_type)

    def _create_bed_mapping(self, **options):
        ''' Create the mapping for bed index '''
        idx_type = self._get_index_type(**options)
        props = MappingProperties(idx_type)
        props.add_property("seqid", "string", index="not_analyzed") \
             .add_property("start", "integer", index="not_analyzed") \
             .add_property("end", "integer", index="not_analyzed")
        props.add_property("name", "string", index="not_analyzed")
        props.add_property("score", "string", index="no")

        self.mapping(props, idx_type, **options)

    def _get_index_type(self, **options):
        if options['indexType']:
            return options['indexType'].lower()
        return "bed"
