#!/bin/bash

#
# Copyright (c) 2021 Intel Corporation
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

#export DNNL_MAX_CPU_ISA=AVX512_CORE_AMX

ARGS="--benchmark"
precision=fp32

batch_size=224

if [[ "$1" == "bf16" ]]
then
    ARGS="$ARGS --bf16"
    precision=bf16
    batch_size=448
    echo "### running bf16 mode"
elif [[ $1 == "fp32" ]]; then
    echo "### running FP32 mode"

else
    echo "The specified precision '$1' is unsupported."
    echo "Supported precisions are: fp32, bf16"
    exit 1
fi
rm -rf ${OUTPUT_DIR}/throughput_log_phase1*
#this is the path of model and enwiki-20200101 on mlp-sdp-spr-4150 machine 
#you can also refer to https://github.com/mlcommons/training/tree/master/language_model/tensorflow/bert
DATASET_DIR=${DATASET_DIR-/pyt_dataset/enwiki-20200101/dataset/tfrecord_dir}
BERT_MODEL_CONFIG=${BERT_MODEL_CONFIG-/pyt_dataset/enwiki-20200101/training/language_model/tensorflow/bert/cleanup_scripts/wiki/config.json}
TRAIN_SCRIPT=${TRAIN_SCRIPT:-${HOME}/frameworks.ai.models.intel-models/models/language_modeling/pytorch/bert_large/training/run_pretrain_mlperf.py}
OUTPUT_DIR=${OUTPUT_DIR:-${PWD}}
work_space=${work_space:-${OUTPUT_DIR}}
python -m intel_extension_for_pytorch.cpu.launch --socket_id 0 --log_path=${OUTPUT_DIR} --log_file_prefix="./throughput_log_phase1_${precision}" ${TRAIN_SCRIPT} \
    --train_file ${DATASET_DIR}/seq_128/part-00000-of-00500_128 \
    --validation_file ${DATASET_DIR}/seq_128/part-00000-of-00500_128 \
    --model_type 'bert' \
    --benchmark \
    --output_dir model_save \
    $ARGS \
    --config_name ${BERT_MODEL_CONFIG} \
    --per_device_train_batch_size ${batch_size} \

throughput=$(grep 'Throughput:' ${OUTPUT_DIR}/throughput_log_phase1_${precision}* |sed -e 's/.*Throughput//;s/[^0-9.]//g' |awk '
BEGIN {
        sum = 0;
        i = 0;
      }
      {
        sum = sum + $1;
i++;
      }
END   {
sum = sum / i;
printf("%.3f", sum);
}')
echo ""BERT";"training phase1 throughput";${precision}; ${batch_size};${throughput}" | tee -a ${OUTPUT_DIR}/summary.log
