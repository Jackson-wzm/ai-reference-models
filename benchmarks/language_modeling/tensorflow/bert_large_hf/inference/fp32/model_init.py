#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Intel Corporation
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
#
# SPDX-License-Identifier: EPL-2.0
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from common.base_model_init import BaseModelInitializer
from common.base_model_init import set_env_var

import os
import sys
from argparse import ArgumentParser


class ModelInitializer(BaseModelInitializer):
    """Initialize mode and run benchmark"""

    def __init__(self, args, custom_args=[], platform_util=None):
        super(ModelInitializer, self).__init__(args, custom_args, platform_util)

        self.benchmark_command = ""
        if not platform_util:
            raise ValueError("Did not find any platform info.")

        # Multi-instance runs on BERT-HF require each instance to have separate output folders
        # and the output folders should be empty to prevent conflicts with previous runs
        if self.args.numa_cores_per_instance and os.path.exists(
                self.args.output_dir):
            if os.listdir(self.args.output_dir):
                sys.exit(
                    "ERROR: The output directory ({}) is not empty. BERT-HF multi-instance "
                    "runs require empty output directories in order to prevent conflicts "
                    "with files generated by previous runs. Please provide an empty folder "
                    "using the --output-dir argument.".format(self.args.output_dir))

        # Use default batch size of 128 if it's -1
        if self.args.batch_size == -1:
            self.args.batch_size = 128

        self.set_num_inter_intra_threads()

        arg_parser = ArgumentParser(description="Parse bert-hf inference args")

        arg_parser.add_argument('--model-name-or-path', help='Path to pretrained model '
                                ' or model identifier from huggingface.co/models',
                                dest='model_name_or_path',
                                default='bert-large-uncased-whole-word-masking')
        arg_parser.add_argument('--dataset-name', help='Dataset name to use via datasets '
                                'library', dest='dataset_name', default='squad')
        arg_parser.add_argument("--warmup-steps", dest='warmup_steps',
                                type=int, default=10,
                                help="number of warmup steps for training and evaluation")
        arg_parser.add_argument("--steps", dest='steps', type=int, default=30,
                                help="number of steps for benchmarking")
        arg_parser.add_argument("--num-inter-threads", dest="num_inter_threads",
                                type=int, default=self.args.num_inter_threads,
                                help="Number of inter-op parallelism threads")
        arg_parser.add_argument("--num-intra-threads", dest="num_intra_threads",
                                type=int, default=self.args.num_intra_threads,
                                help="Number of intra-op parallelism threads")
        self.args = arg_parser.parse_args(self.custom_args, namespace=self.args)

        # Set KMP env vars, if they haven't already been set, but override the default KMP_BLOCKTIME value
        config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")
        self.set_kmp_vars(config_file_path)

        if not os.getenv("OMP_NUM_THREADS"):
            if self.args.num_intra_threads:
                set_env_var("OMP_NUM_THREADS", self.args.num_intra_threads)
            else:
                set_env_var("OMP_NUM_THREADS", platform_util.num_cores_per_socket)

        model_script = os.path.join(
            self.args.intelai_models, self.args.mode, "run_qa.py")

        model_args = " --output_dir=" + str(self.args.output_dir) + \
                     " --batch_size=" + str(self.args.batch_size) + \
                     " --dataset_name=" + str(self.args.dataset_name) + \
                     " --per_device_eval_batch_size=" + str(self.args.batch_size) + \
                     " --per_device_train_batch_size=" + str(self.args.batch_size)

        if self.args.data_location:
            model_args += " --model_name_or_path=" + str(self.args.data_location)
        else:
            model_args += " --model_name_or_path=" + str(self.args.model_name_or_path)

        if self.args.num_inter_threads:
            model_args += " --num_inter_threads=" + str(self.args.num_inter_threads)

        if self.args.num_intra_threads:
            model_args += " --num_intra_threads=" + str(self.args.num_intra_threads)

        if self.args.benchmark_only:
            model_args += " --mode=benchmark"

        if self.args.accuracy_only:
            model_args += " --mode=accuracy"

        if self.args.warmup_steps:
            model_args += " --train_eval_warmup_steps=" + str(self.args.warmup_steps)

        if self.args.steps:
            model_args += " --steps=" + str(self.args.steps)

        if self.args.precision:
            model_args += " --precision=" + str(self.args.precision)

        tf_xla_enabled = False
        if "TF_XLA_FLAGS" in os.environ:
            tf_xla_flags = os.environ["TF_XLA_FLAGS"].split(sep=" ")
            tf_xla_enabled = "--tf_xla_auto_jit=2" in tf_xla_flags and \
                "--tf_xla_cpu_global_jit" in tf_xla_flags
        if tf_xla_enabled:
            model_args += " --xla"

        self.benchmark_command = self.get_command_prefix(args.socket_id) + \
            self.python_exe + " " + model_script + model_args

    def run(self):
        if self.benchmark_command:
            # BERT-HF needs to have unique output directories for every instance, so pass the output_dir
            # string to the run_command function so that unique dirs get swapped in to the commands
            self.run_command(self.benchmark_command,
                             replace_unique_output_dir=str(self.args.output_dir))
