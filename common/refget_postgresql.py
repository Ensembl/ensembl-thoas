import psycopg2



class RefgetDB:
    def __init__(self, config):
        self._config = config
        self.host = self._config.get('REFGET DB', 'host')
        self.port = self._config.getint('REFGET DB', 'port')
        self.user = self._config.get('REFGET DB', 'user')
        self.password = self._config.get('REFGET DB', 'password')
        self.dbname = self._config.get('REFGET DB', 'db')
        with psycopg2.connect(self.connection_info) as connection:
            self.connection = connection


    @property
    def ARGS(self):
        return common.utils.parse_args()

    @property
    def CDNA(self):
        return 'cdna'

    @property
    def CDS(self):
        return 'cds'

    @property
    def PEP(self):
        return 'protein'

    @property
    def NCRNA(self):
        return 'ncrna'

    @property
    def connection_info(self):
        return f"host={self.host} dbname={self.dbname} user={self.user} password={self.password}"

    def get_checksum(self, release_version, assembly, stable_id, sequence_type):
        try:
            with self.connection.cursor() as cur:
                cur.execute("""
                                select seq.md5, species.assembly,species.species_id,species.species, molecule.id, mol_type.type from seq 
                                join molecule using (seq_id)
                                join release using (release_id)
                                join mol_type using(mol_type_id)
                                join species using(species_id)
                                where release.release=%s and species.assembly=%s and molecule.id=%s and type = %s
                                limit 10;
                            """,
                            (release_version, assembly, stable_id, sequence_type))
                result_list = cur.fetchall()

            return result_list[0][0]
        except:
            return ''
