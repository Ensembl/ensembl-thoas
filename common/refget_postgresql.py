"""Utility class for Refget DB connections"""

import psycopg2


class RefgetDB:
    def __init__(self, release, assembly, config):
        self.release_version = release
        self.assembly = assembly
        self._config = config

        # Set RefgetDB Connection Parameters from config file
        self.host = self._config.get("REFGET DB", "host")
        self.port = self._config.getint("REFGET DB", "port")
        self.user = self._config.get("REFGET DB", "user")
        self.password = self._config.get("REFGET DB", "password")
        self.dbname = self._config.get("REFGET DB", "db")

        with psycopg2.connect(self.connection_info) as connection:
            self.connection = connection

    @property
    def cdna(self):
        return "cdna"

    @property
    def cds(self):
        return "cds"

    @property
    def pep(self):
        return "protein"

    @property
    def ncrna(self):
        return "ncrna"

    @property
    def connection_info(self):
        return f"host={self.host} dbname={self.dbname} user={self.user} password={self.password}"

    def get_checksum_and_length(self, stable_id, sequence_type):
        with self.connection.cursor() as cur:
            cur.execute(
                """
                            select seq.md5, seq.size from seq
                            join molecule using (seq_id)
                            join release using (release_id)
                            join mol_type using(mol_type_id)
                            join species using(species_id)
                            where release.release=%s and species.assembly=%s and molecule.id=%s and type = %s
                            limit 1;
                        """,
                (self.release_version, self.assembly.lower(), stable_id, sequence_type),
            )

            result = cur.fetchone()
            if result is None:
                return None, None
            return result


class MockRefgetDB:
    @property
    def cds(self):
        return "cds"

    @property
    def cdna(self):
        return "cdna"

    @property
    def pep(self):
        return "protein"

    def get_checksum_and_length(self, stable_id, sequence_type):
        return "1f47b55923e2d23090f894c439974b55", 10
