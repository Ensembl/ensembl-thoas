import mysql.connector
import pymongo

config = {
    'host': '10.42.24.29',
    'port': 27017,
    'user': 'mdb-ens-cdl-rw',
    'password': 'mtG4IRYKsPQ',
    'db': 'apps_data'
}


ens_config = {
    'host': 'mysql-ens-mirror-1.ebi.ac.uk',
    'port': 4240,
    'user': 'anonymous',
    'db': 'homo_sapiens_core_98_38'
}


def connect(config):
    'Fill MongoDB with goodness(?)'

    host = config.get('host')
    port = config.get('port')
    user = config.get('user')
    password = config.get('password')
    db = config.get('db')

    client = pymongo.MongoClient(
        host,
        port,
        read_preference=pymongo.ReadPreference.SECONDARY_PREFERRED
    )
    client.admin.authenticate(user, password)
    return client[db]


def connect_mysql(config):
    'Get features from MySQL'

    connection = mysql.connector.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        database=config['db']
    )
    return connection


def populate_mongo():
    db_handle = connect(config)

    mysql_handle = connect_mysql(ens_config)

    # Start loading genes
    db_cursor = mysql_handle.cursor()

    db_cursor.execute('''
        SELECT g.stable_id, g.biotype ,x.display_label, g.description, sr.name,
            g.seq_region_start, g.seq_region_end, g.seq_region_strand,
            t.stable_id
        FROM gene g, xref x, seq_region sr, transcript t
        WHERE t.gene_id = g.gene_id
        AND g.display_xref_id = x.xref_id
        AND g.seq_region_id = sr.seq_region_id
    ''')

    current_gene_id = None
    document = {}

    i = 1
    for (
        gene_stable_id, so_term, gene_name, gene_description, region_name,
        region_start, region_end, region_strand, transcript_stable_id
    ) in db_cursor:

        if current_gene_id == gene_stable_id:
            # adding transcripts to gene
            document['transcripts'].append(transcript_stable_id)
            i += 1
            if i % 1000 == 0:
                print(i)
        else:
            # starting a new document, finishing the previous
            db_handle['graphql-test'].insert_one(document)
            i += 1

            document = {}

            document['type'] = 'Gene'
            document['stable_id'] = gene_stable_id
            document['so_term'] = so_term
            document['name'] = gene_name
            document['description'] = gene_description
            document['slice'] = {
                'region': {
                    'name': region_name,
                    'strand': {
                        'code': 'forward' if region_strand > 0 else 'reverse',
                        'value': region_strand
                    },
                    'assembly': 'GRCh38'
                },
                'location': {
                    'start': region_start,
                    'end': region_end,
                    'length': region_end - region_start + 1,
                    'location_type': 'chromosome'
                },
                'default': True
            }
            document['transcripts'] = [transcript_stable_id]

            current_gene_id = gene_stable_id

    db_cursor.close()
    db_cursor = mysql_handle.cursor()

    # Now load transcripts
    db_cursor.execute('''
        SELECT t.stable_id, t.biotype, x.display_label, t.seq_region_start,
            t.seq_region_end, t.seq_region_strand, g.stable_id, sr.name,
            e.stable_id, e.seq_region_start, e.seq_region_end,
            e.seq_region_strand
        FROM transcript t, gene g, xref x, seq_region sr, exon e,
            exon_transcript et
        WHERE t.gene_id = g.gene_id
        AND t.seq_region_id = sr.seq_region_id
        AND t.display_xref_id = x.xref_id
        AND t.transcript_id = et.transcript_id
        AND e.exon_id = et.exon_id
        ORDER BY t.stable_id, et.rank
    ''')

    document = {}
    current_transcript_id = None
    i = 1

    for (
        transcript_stable_id, so_term, transcript_name, region_start,
        region_end, region_strand, gene_stable_id, region_name,
        exon_stable_id, exon_start, exon_end, exon_strand,
    ) in db_cursor:

        if current_transcript_id == transcript_stable_id:
            document['exons'].append(
                format_exon(exon_stable_id, region_name, region_strand,
                            exon_start, exon_end)
            )
            i += 1
            if i % 1000 == 0:
                print(i)
        else:
            db_handle['graphql-test'].insert_one(document)
            i += 1
            document = {}
            current_transcript_id = transcript_stable_id

            document['type'] = 'Transcript'
            document['stable_id'] = transcript_stable_id
            document['so_term'] = so_term
            document['gene'] = gene_stable_id
            document['slice'] = {
                'region': {
                    'name': region_name,
                    'strand': {
                        'code': 'forward' if region_strand > 0 else 'reverse',
                        'value': region_strand
                    },
                    'assembly': 'GRCh38'
                },
                'location': {
                    'start': region_start,
                    'end': region_end,
                    'length': region_end - region_start + 1,
                    'location_type': 'chromosome'
                },
                'default': True
            }
            document['exons'] = [
                format_exon(exon_stable_id, region_name, region_strand,
                            exon_start, exon_end)
            ]


def format_exon(exon_stable_id, region_name, region_strand, exon_start,
                exon_end):
    return {
        'type': 'Exon',
        'stable_id': exon_stable_id,
        'slice': {
            'region': {
                'name': region_name,
                'strand': {
                    'code': 'forward' if region_strand > 0 else 'reverse',
                    'value': region_strand
                },
                'assembly': 'GRCh38'
            },
            'location': {
                'start': exon_start,
                'end': exon_end,
                'length': exon_end - exon_start + 1,
                'location_type': 'chromosome'
            },
            'default': True
        }
    }


if __name__ == '__main__':
    populate_mongo()
