"""
setup file for packaging

Copyright 2022 Sean Brogan
SPDX-License-Identifier: Apache-2.0

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

import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rvc2mqtt",
    author="Sean Brogan",
    author_email="spbrogan@live.com",
    description="Python project to bridge RVC devices with MQTT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/spbrogan/rvc2mqtt",
    license='Apache-2',
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache2 License",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers"
    ],
    install_requires=[
        'python-can',
        'ruyaml',
        'paho-mqtt'
    ],
    python_requires='>=3.8'
)
