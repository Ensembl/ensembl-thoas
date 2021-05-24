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

from common.transcript_metadata import *

def test_parse_input_tsl1():
	'''
	Ensure TSL input tslN (e.g tsl1, tsl2, tsl3 etc) is parsed correctly
	'''
	tsl = TSL("tsl1")
	parse_success = tsl.parse_input()
	assert tsl.toJson()['value'] == '1'

def test_parse_input_tsl3_extra():
	'''
	Ensure TSL input tslN (with some extra text) is parsed correctly
	'''
	tsl = TSL("tsl3 (version 9)")
	parse_success = tsl.parse_input()
	assert tsl.toJson()['value'] == '3'

def test_parse_input_tslNA():
	'''
	Ensure TSL input tslNA is parsed correctly
	'''
	tsl = TSL("tslNA")
	parse_success = tsl.parse_input()
	assert tsl.toJson()['value'] == 'NA'

def test_parse_input_failure():
	'''
	Ensure any other input is not parsed
	'''
	tsl = TSL("random")
	parse_success = tsl.parse_input()
	assert parse_success == False

def test_appris_parse_input_principal1():
	'''
	Ensure APPRIS input principal1 is parsed correctly
	'''
	appris = APPRIS("principal1")
	parse_success = appris.parse_input()
	assert appris.toJson()['value'] == 'principal1'

def test_appris_parse_input_principal1():
	'''
	Ensure APPRIS input alternative2 is parsed correctly
	'''
	appris = APPRIS("alternative2")
	parse_success = appris.parse_input()
	assert appris.toJson()['value'] == 'alternative2'

def test_appris_parse_input_failure():
	'''
	Ensure Failure of any other input e.g random
	'''
	appris = APPRIS("random")
	parse_success = appris.parse_input()
	assert parse_success == False

def test_parse_input_mane_select():
	'''
	Ensure MANE input mane select is parsed correctly
	'''
	mane = MANE("select", "NM_015694.3")
	assert mane.toJson()['value'] == 'select'
	assert mane.toJson()['label'] == 'MANE Select'

def test_parse_input_mane_plus_clinical():
	'''
	Ensure MANE input mane plus clinical is parsed correctly
	'''
	mane = MANE("plus_clinical", "NM_015694.3")
	assert mane.toJson()['value'] == 'plus_clinical'
	assert mane.toJson()['label'] == 'MANE Plus Clinical'
