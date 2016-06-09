''' Used to define Elastic mapping and index data. '''
import logging
from optparse import make_option

from django.core.management.base import BaseCommand

from elastic.management.loaders.alias import AliasManager
from elastic.management.loaders.bed import BEDManager
from elastic.management.loaders.criteria import CriteriaManager
from elastic.management.loaders.gene import GeneManager
from elastic.management.loaders.gene_target import GeneTargetManager
from elastic.management.loaders.gff import GFFManager
from elastic.management.loaders.json import JsonManager
from elastic.management.loaders.marker import MarkerManager, RsMerge
from elastic.management.loaders.region import RegionManager


# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    ''' Elastic index mapping and loading tool. '''
    help = "Use to create Elastic index mappings and load data.\n\n" \
           "Options for markers:\n" \
           " --indexName [index name] --indexSNP All.vcf\n" \
           " --indexName [index name] --indexSNPMerge RsMergeArch.bcp.gz\n" \
           "Options for genes:\n" \
           " --indexName [index name] --indexGene genenames.org.txt --org=human\n" \
           " --indexName [index name] --indexGeneGFF gene.gff --build GRCh38\n" \
           "Options for study hits:\n" \
           " --indexName [index name] --indexType [studies] --addStudyData [csv file] --study [study id]\n" \
           "Options for GFF/GTF:\n" \
           " --indexName [index name] --indexType [gff] --indexGFF file.gff [--isGTF]\n" \
           "Options for BED:\n" \
           " --indexName [index name] --indexType [bed] --indexBED file.bed\n" \
           "Options for t1d/criteria:\n" \
           " indexCriteria 'true' --indexName [index name] --indexProject t1dbase --applyFilter" \
           "Options for imb/criteria:\n" \
           " indexCriteria 'true' --indexName [index name] --indexProject immunobase --applyFilter" \
           "Options for alias/gene:\n" \
           " --indexAlias [dir where files to be indexed are there] --indexFeatureType gene" \


    option_list = BaseCommand.option_list + (
        make_option('--indexSNP',
                    dest='indexSNP',
                    help='VCF file (from dbSNP) to index'),
        ) + (
        make_option('--indexSNPMerge',
                    dest='indexSNPMerge',
                    help='RS Merge (from dbSNP)'),
        ) + (
        make_option('--indexGene',
                    dest='indexGene',
                    help='Genename.org file to index'),
        ) + (
        make_option('--indexGeneGFF',
                    dest='indexGeneGFF',
                    help='GFF gene file used to update a gene index'),
        ) + (
        make_option('--addStudyData',
                    dest='addStudyData',
                    help='CSV file of GWAS data from study'),
        ) + (
        make_option('--study',
                    dest='study_id',
                    help='study id'),
        ) + (
        make_option('--org',
                    dest='org',
                    help='Organism name'),
        ) + (
        make_option('--indexName',
                    dest='indexName',
                    help='Index name'),
        ) + (
        make_option('--build',
                    dest='build',
                    help='Build name (e.g. GRCh38)'),
        ) + (
        make_option('--disease',
                    dest='disease',
                    help='disease code (eg: cel) '),
        ) + (
        make_option('--indexGTarget',
                    dest='indexGTarget',
                    help='Load gene targets'),
        ) + (
        make_option('--indexGFF',
                    dest='indexGFF',
                    help='Load GFF targets'),
        ) + (
        make_option('--isGTF',
                    dest='isGTF',
                    help='GTF file type',
                    action="store_true"),
        ) + (
        make_option('--indexBED',
                    dest='indexBED',
                    help='Load BED file'),
        ) + (
        make_option('--indexType',
                    dest='indexType',
                    help='Index type'),
        ) + (
        make_option('--indexFeatureType',
                    dest='indexFeatureType',
                    help='Index feature type[gene,locus,marker,study]'),
        ) + (
        make_option('--indexAlias',
                    dest='indexAlias',
                    help='Load aliases'),
        ) + (
        make_option('--indexProject',
                    help='Project name to use',
                    action="store", type="string", dest='indexProject'),
        ) + (
        make_option('--applyFilter',
                    help='applyFilter enabled to restrict query for testing',
                    action="store_true"),
        ) + (
        make_option('--indexCriteria',
                    dest='indexCriteria',
                    help='Create and Load Criterias'),
        ) + (
        make_option('--indexJson',
                    dest='indexJson',
                    help='Load json file'),
        ) + (
        make_option('--shards',
                    dest='shards',
                    default=5,
                    help='No. of shards [default: %default]'),
        )

    def handle(self, *args, **options):
        ''' Handle the user options to map or load data. '''
        if options['indexSNP']:
            marker = MarkerManager()
            marker.create_load_snp_index(**options)
        elif options['indexSNPMerge']:
            marker_merge = RsMerge()
            marker_merge.create_load_snp_merge_index(**options)

        elif options['indexGene']:
            gene = GeneManager()
            gene.load_genename(**options)
        elif options['indexGeneGFF']:
            gene = GeneManager()
            gene.update_gene(**options)

        elif options['addStudyData']:
            region = RegionManager()
            region.add_study_data(**options)

        elif options['indexGTarget']:
            gt = GeneTargetManager()
            gt.create_load_gene_target_index(**options)

        elif options['indexGFF']:
            gff = GFFManager()
            gff.create_load_gff_index(**options)

        elif options['indexBED']:
            bed = BEDManager()
            bed.create_load_bed_index(**options)

        elif options['indexAlias']:
            alias = AliasManager()
            alias.create_alias(**options)

        elif options['indexCriteria']:
            criteria = CriteriaManager()
            criteria.create_criteria(**options)

        elif options['indexJson']:
            json = JsonManager()
            json.load_json(**options)

        else:
            print(help)
