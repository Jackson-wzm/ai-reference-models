#!/bin/bash
set -e

echo "Setup ITEX-XPU Test Enviroment for EfficientNet Inference"

MODEL_NAME=$1
OUTPUT_DIR=${OUTPUT_DIR-"$(pwd)/tests/cicd/tensorflow/efficientnet/inference/gpu/output/${MODEL_NAME}"}
is_lkg_drop=$2

# Create the output directory in case it doesn't already exist
mkdir -p ${OUTPUT_DIR}

if [[ "${is_lkg_drop}" == "true" ]]; then
  source ${WORKSPACE}/tensorflow_setup/bin/activate tensorflow
else
  source /oneapi/compiler/latest/env/vars.sh
  source /oneapi/mpi/latest/env/vars.sh
  source /oneapi/mkl/latest/env/vars.sh
  source /oneapi/tbb/latest/env/vars.sh
  source /oneapi/ccl/latest/env/vars.sh
fi

# run following script
cd models_v2/tensorflow/efficientnet/inference/gpu
./setup.sh

OUTPUT_DIR=${OUTPUT_DIR} MODEL_NAME=${MODEL_NAME} ./run_model.sh
cd -
