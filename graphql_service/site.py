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

import pkg_resources
from starlette.templating import Jinja2Templates

TEMPLATES = Jinja2Templates(directory='templates')

async def doc_page(request):
    '''
    Provide visitors with an introduction and a way to navigate the graphql schema
    '''
    # Ask setuptools what the reported package version is
    thoas_release = pkg_resources.require("ensembl_graphql")[0].version

    return TEMPLATES.TemplateResponse(
        'docs.j2', {'request': request, 'thoas_release': thoas_release}
    )
