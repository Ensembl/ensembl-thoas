"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import json
import argparse
import ijson


def get_jsons(infile_name, sample_size):
    counter = 0
    with open(infile_name, encoding='UTF-8') as infile, open('sample_jsons.jsonl', 'w+', encoding='UTF-8') as outfile:
        for gene in ijson.items(infile, 'item'):
            outfile.write(json.dumps(gene, indent=2, sort_keys=True) + "\n")
            counter += 1
            if counter == sample_size:
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get a sample of JSONs and write them to sample_jsons.jsonl.  "
                                                 "This script is useful for sampling from the production JSON dumps, "
                                                 "which are dumped as one enormous JSON.  The location of the JSON "
                                                 "dumps is given by the value of the base_data_path in the "
                                                 "load.conf file")

    parser.add_argument(
        '--input_file',
        help='File to get the JSONs from')

    parser.add_argument('--sample_size', type=int)

    args = parser.parse_args()

    get_jsons(args.input_file, args.sample_size)
