import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 1,
  duration: '5s',
};

export default function main() {
  let response;
  // Thoas URL 
  const url = 'http://hx-rke-wp-webadmin-13-worker-1.caas.ebi.ac.uk:31497/';
  // thoas
  response = http.post(
    url,
    '{\n  "query": "query {\\n gene(byId: { genome_id: \\"homo_sapiens_GCA_000001405_28\\", stable_id: \\"ENSG00000109339\\" }) {\\n       stable_id\\n       symbol\\n       unversioned_stable_id\\n       version\\n       slice {\\n         location {\\n           start\\n           end\\n           length\\n         }\\n         strand {\\n           code\\n         }\\n       }\\n       transcripts {\\n         stable_id\\n         unversioned_stable_id\\n         slice {\\n           location {\\n             start\\n             end\\n             length\\n           }\\n           region {\\n             name\\n           }\\n           strand {\\n             code\\n           }\\n         }\\n         relative_location {\\n           start\\n           end\\n         }\\n         spliced_exons {\\n           relative_location {\\n             start\\n             end\\n           }\\n           exon {\\n             stable_id\\n             slice {\\n               location {\\n                 length\\n               }\\n             }\\n           }\\n         }\\n         product_generating_contexts {\\n           product_type\\n           cds {\\n             relative_start\\n             relative_end\\n           }\\n           cdna {\\n             length\\n           }\\n           phased_exons {\\n             start_phase\\n             end_phase\\n             exon {\\n               stable_id\\n             }\\n           }\\n           product {\\n             stable_id\\n             unversioned_stable_id\\n             length\\n             external_references {\\n               accession_id\\n               name\\n               description\\n               source {\\n                 id\\n               }\\n             }\\n           }\\n         }\\n         external_references {\\n           accession_id\\n           name\\n           url\\n           source {\\n             id\\n             name\\n           }\\n         }\\n         metadata {\\n           biotype {\\n             label\\n             value\\n             definition\\n           }\\n           tsl {\\n             label\\n             value\\n           }\\n           appris {\\n             label\\n             value\\n           }\\n           canonical {\\n             value\\n             label\\n             definition\\n           }\\n           mane {\\n             value\\n             label\\n             definition\\n             ncbi_transcript {\\n               id\\n               url\\n             }\\n           }\\n           gencode_basic {\\n             label\\n           }\\n         }\\n       }\\n     }\\n }",\n  "variables": {}\n}\n',
    {
      headers: {
        "Content-Type": "application/json",
      },
    }
  );
  check(response, {
    "status equals 200": response => response.status.toString() === "200",
  });

  // Automatically added sleep
  // sleep(1);
}
