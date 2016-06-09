''' Loader for gene target data. '''
import logging
import re

from elastic.management.loaders.loader import DelimeterLoader
from elastic.management.loaders.mapping import MappingProperties


# Get an instance of a logger
logger = logging.getLogger(__name__)


# Get an instance of a logger
logger = logging.getLogger(__name__)


class GeneTargetManager(DelimeterLoader):
    tissue_types = []

    def create_load_gene_target_index(self, **options):
        ''' Index gene target data '''
        idx_name = self.get_index_name(**options)
        f = self.open_file_to_load('indexGTarget', **options)
        column_names = ["ensg", "name", "biotype", "strand",
                        "baitChr", "baitStart", "baitEnd", "baitID", "baitName",
                        "oeChr", "oeStart", "oeEnd", "oeID", "oeName", "dist"]
        line = f.readline().strip()
        line = line.decode("utf-8")
        parts = re.split("\t", line)
        GeneTargetManager.tissue_types = parts[len(column_names):]
        column_names.extend(GeneTargetManager.tissue_types)
        self._create_gene_mapping(**options)
        self.load(column_names, f, idx_name, 'gene_target')

    def _create_gene_mapping(self, **options):
        ''' Create the mapping for gene target index '''
        props = MappingProperties("gene_target")
        props.add_property("ensg", "string", index="not_analyzed") \
             .add_property("name", "string", index="not_analyzed") \
             .add_property("biotype", "string", index="not_analyzed") \
             .add_property("strand", "string", index="no") \
             .add_property("baitChr", "string", index="not_analyzed") \
             .add_property("baitStart", "integer", index="not_analyzed") \
             .add_property("baitEnd", "integer", index="not_analyzed") \
             .add_property("baitID", "string", index="no") \
             .add_property("baitName", "string", index="no") \
             .add_property("oeChr", "string", index="not_analyzed") \
             .add_property("oeStart", "integer", index="not_analyzed") \
             .add_property("oeEnd", "integer", index="not_analyzed") \
             .add_property("oeID", "string", index="no") \
             .add_property("oeName", "string", index="no") \
             .add_property("dist", "integer", index="not_analyzed")

        meta = {"tissue_type": {}}
        for tt in GeneTargetManager.tissue_types:
            props.add_property(tt, "float")
            meta["tissue_type"][tt] = "tissue_type"

        self.mapping(props, idx_type='gene_target', meta=meta, **options)
