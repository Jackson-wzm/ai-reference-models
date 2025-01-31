#
# Copyright (c) 2023 Intel Corporation
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
# @lint-ignore-every LICENSELINT
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.


"""
Utilities for MLPerf logging
"""
import os

import torch

try:
    from mlperf_logging import mllog
    from mlperf_logging.mllog import constants

    _MLLOGGER = mllog.get_mllogger()
except ImportError as error:
    print("Unable to import mlperf_logging, ", error)


def log_start(*args, **kwargs):
    "log with start tag"
    _log_print(_MLLOGGER.start, *args, **kwargs)


def log_end(*args, **kwargs):
    "log with end tag"
    _log_print(_MLLOGGER.end, *args, **kwargs)


def log_event(*args, **kwargs):
    "log with event tag"
    _log_print(_MLLOGGER.event, *args, **kwargs)


def _log_print(logger, *args, **kwargs):
    "makes mlperf logger aware of distributed execution"
    if "stack_offset" not in kwargs:
        kwargs["stack_offset"] = 3
    if "value" not in kwargs:
        kwargs["value"] = None

    if kwargs.pop("log_all_ranks", False):
        log = True
    else:
        log = get_rank() == 0

    if log:
        logger(*args, **kwargs)


def config_logger(benchmark):
    "initiates mlperf logger"
    mllog.config(
        filename=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), f"{benchmark}.log"
        )
    )
    _MLLOGGER.logger.propagate = False


def barrier(use_device="cpu"):
    """
    Works as a temporary distributed barrier, currently pytorch
    doesn't implement barrier for NCCL backend.
    Calls all_reduce on dummy tensor and synchronizes with GPU.
    """
    if torch.distributed.is_available() and torch.distributed.is_initialized():
        if use_device == "cuda":
            torch.distributed.all_reduce(torch.cuda.FloatTensor(1))
            torch.cuda.synchronize()
        elif use_device == "xpu":
            torch.distributed.all_reduce(torch.xpu.FloatTensor(1))
            torch.xpu.synchronize()
        else:
            pass


def get_rank():
    """
    Gets distributed rank or returns zero if distributed is not initialized.
    """
    if torch.distributed.is_available() and torch.distributed.is_initialized():
        rank = torch.distributed.get_rank()
    else:
        rank = 0
    return rank


def mlperf_submission_log(benchmark):
    """
    Logs information needed for MLPerf submission
    """

    config_logger(benchmark)

    log_event(
        key=constants.SUBMISSION_BENCHMARK,
        value=benchmark,
    )

    log_event(key=constants.SUBMISSION_ORG, value="reference_implementation")

    log_event(key=constants.SUBMISSION_DIVISION, value="closed")

    log_event(key=constants.SUBMISSION_STATUS, value="onprem")

    log_event(key=constants.SUBMISSION_PLATFORM, value="reference_implementation")

    log_event(key=constants.SUBMISSION_ENTRY, value="reference_implementation")

    log_event(key=constants.SUBMISSION_POC_NAME, value="reference_implementation")

    log_event(key=constants.SUBMISSION_POC_EMAIL, value="reference_implementation")
