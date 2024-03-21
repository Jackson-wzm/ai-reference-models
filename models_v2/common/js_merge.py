# Copyright (c) 2023-2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
import os
import sys

def merge(a: dict, b: dict, path=[]):
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif type(a[key]) != type(b[key]):
                print('error: type conflict at ' + '.'.join(path + [str(key)]))
                sys.exit(1)
            elif a[key] != b[key]:
                print('warning: different values at +' '.'.join(path + [str(key)]), file=sys.stderr)
        else:
            a[key] = b[key]
    return a

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='js_merge',
          description='Merge few JSON files together',
          epilog='Copyright (c) 2024 Intel Corporation')

    parser.add_argument('--indent', default=None, help='indent for json.dump()')
    parser.add_argument('file', help='JSON file to merge', nargs='+')

    args = parser.parse_args()

    data = {}
    for file in args.file:
        try:
            f = open(file)
        except Exception as e:
            print('error: ' + str(e), file=sys.stderr)
            sys.exit(1)
        merge(data, json.load(f))
        f.close()

    json.dump(data, sys.stdout,
        indent=(int(args.indent) if args.indent and args.indent.isdecimal() else args.indent))