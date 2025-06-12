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

import time
from pathlib import Path
import asyncio

from pyinstrument import Profiler

# Create a profiles directory if it doesn't exist
PROFILE_DIR = "profiles"
Path(PROFILE_DIR).mkdir(exist_ok=True)


def profile_resolver(func):
    """Decorator that profiles a function and saves HTML report."""

    def sync_wrapper(*args, **kwargs):
        profiler = Profiler(interval=0.001)
        profiler.start()
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            profiler.stop()
            end_time = time.time()
            save_profile_report(profiler, func, start_time, end_time)

    async def async_wrapper(*args, **kwargs):
        profiler = Profiler(interval=0.001)
        profiler.start()
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            profiler.stop()
            end_time = time.time()
            save_profile_report(profiler, func, start_time, end_time)

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def save_profile_report(profiler, func, start_time, end_time):
    """Save profiling report to HTML file with timestamp."""
    # Create a filename-safe version of the function name
    func_name = func.__name__.replace('<', '').replace('>', '')

    # Generate timestamp for the report
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    duration = end_time - start_time

    # Create the HTML report
    html_content = profiler.output_html()

    # Save to file
    filename = f"{PROFILE_DIR}/{timestamp}_{func_name}_duration_{duration:.2f}s.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Saved profile report to {filename}")
