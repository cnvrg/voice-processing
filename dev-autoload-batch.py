# Copyright (c) 2023 Intel Corporation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

import os
import yaml
import tarfile
import requests

##### THIS IS A DEV AUTOLOAD #####

# CHANGE THESE VARIABLES TO AUTO GENERATE BLUEPRINT
base_url = "https://metacloud.cloud.cnvrg.io/marketplace/api/v1"
api_token = "K3lZTEQrL1F0TUtCbWcySmVWWWVwdz09OmtMK2tWZ3pBR3dNMVRsZFJBNmtxWFE9PQ=="
admin_token = "UktZOEBZS1U8Y1BWaXtVU1oyJDc/TXUr"  # prod

# train
default_version = "18.8.45"
library_files = ['s3-connector',
                 'stt_batch']
blueprint_file = "train_blueprint_batch.yaml"
readme_file = 'train_readme_batch.md'
#library_files = ['inference']
#blueprint_file = "inference_blueprint.yaml"
#readme_file = 'inference_readme.md'

headers = {"api-token": api_token}


# GENERATE LIBRARIES
def create_library_version(library_name, path):
    with open(f"{path}/library.yaml", 'r') as f:
        schema = f.read()
        schema_dict = yaml.safe_load(schema)
        schema_dict["version"] = default_version
        schema_dict['title'] = 'dev-' + schema_dict['title']
        schema = yaml.dump(schema_dict)

    with open(f"{path}/README.md", 'r') as f:
        readme = f.read()

    with open(f"{path}/requirements.txt", 'r') as f:
        dependencies = f.read()

    payload = {
        "data": {
            "type": "string",
            "attributes": {
                "schema_file": {
                    "raw": schema
                },
                "description": {
                    "raw": readme,
                    "content_type": "text/plain"
                },
                "dependency": {
                    "raw": dependencies,
                    "language": "python"
                }
            }
        }
    }

    response = requests.request(
        method="POST",
        url=f"{base_url}/libraries/{library_name}/versions/",
        headers=headers,
        json=payload
    )

    if response.status_code == 201:
        print(f"Library version for {library_name} created")
    else:
        print(f"Failed creating version for {library_name}")
        print(response.content.decode())


def create_library(library_name):
    payload = {
        "data": {
            "attributes": {
                "name": library_name,
                "slug": library_name,
                "public": False,
            }
        }
    }

    response = requests.request("POST", f"{base_url}/libraries/", json=payload, headers=headers)

    if response.status_code == 201:
        print(f"Library {library_name} created")
    else:
        print(f"Failed creating {library_name} library")
        print(response.content.decode())


def upload_library_version(library_name, path):
    library_file = "library.tar.gz"

    with tarfile.open(library_file, "w:gz") as tar:
        tar.add(path, arcname=os.path.basename(path))

    files = {'file': open(library_file, 'rb')}

    response = requests.request(
        method="PUT",
        url=f"{base_url}/libraries/{library_name}/versions/{default_version}",
        headers=headers,
        files=files
    )

    if response.status_code == 204:
        print(f"Library files for {library_name} were uploaded")
    else:
        print(f"Failed upload for {library_name}")
        print(response.content.decode())


# CREATE BLUEPRINT
def create_blueprint_version(blueprint_name):
    with open(blueprint_file, 'r') as f:
        schema = f.read()
        schema_dict = yaml.safe_load(schema)
        schema_dict["version"] = default_version
        schema_dict['title'] = 'dev-' + schema_dict['title']
        for library in schema_dict["tasks"]:
            library["library_version"] = default_version
            library['library'] = 'dev-' + library['library']
        schema = yaml.dump(schema_dict)

    with open(readme_file, 'r') as f:
        readme = f.read()

    # create version
    payload = {
        "data": {
            "attributes": {
                "schema_file": {
                    "raw": schema
                },
                "description": {
                    "raw": readme,
                    "content_type": "text/plain"
                }
            }
        }
    }

    response = requests.request(
        method="POST",
        url=f"{base_url}/blueprints/{blueprint_name}/versions/",
        headers=headers,
        json=payload
    )

    if response.status_code == 201:
        print(f"Blueprint version for {blueprint_name} created")
    else:
        print(f"Failed creating blueprint version for {blueprint_name}")
        print(response.content.decode())


def create_blueprint(blueprint_name):
    payload = {
        "data": {
            "attributes": {
                "name": blueprint_name,
                "public": False
            }
        }
    }

    response = requests.request("POST", f"{base_url}/blueprints/", json=payload, headers=headers)

    if response.status_code == 201:
        print(f"Blueprint {blueprint_name} created")
    else:
        print(f"Failed creating {blueprint_name} blueprint")
        print(response.content.decode())


def build_blueprint(blueprint_name):
    admin_headers = {"api-token": admin_token}
    response = requests.request("POST", f"{base_url}/blueprints/{blueprint_name}/build", headers=admin_headers)

    if response.status_code == 202:
        print(f"Blueprint {blueprint_name} is being built")
    else:
        print(f"Failed building {blueprint_name} {response.text} blueprint")
        print(response.content.decode())


for library_path in library_files:
    with open(f"{library_path}/library.yaml", 'r') as f:
        schema_yaml = f.read()
        schema_json = yaml.safe_load(schema_yaml)

    schema_json['title'] = 'dev-' + schema_json['title']
    library_name = schema_json["title"].replace(" ", "-").lower()
    create_library(library_name)
    create_library_version(library_name, library_path)
    upload_library_version(library_name, library_path)

with open(blueprint_file, 'r') as f:
    schema_yaml = f.read()
    schema_json = yaml.safe_load(schema_yaml)

schema_json['title'] = 'dev-' + schema_json['title']
for task in schema_json['tasks']:
    task['library'] = 'dev-' + task['library']
blueprint_name = schema_json["title"]
blueprint_slug = blueprint_name.replace(" ", "-").lower()
create_blueprint(blueprint_name)
create_blueprint_version(blueprint_slug)
build_blueprint(blueprint_slug)