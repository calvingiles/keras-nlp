# Copyright 2021 The KerasNLP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# sentencepiece is segfaulting on tf-nightly if tensorflow is imported first.
# This is a temporary fix to restore our nightly testing to green, while we look
# for a longer term solution.
try:
    import sentencepiece
except ImportError:
    pass

from keras_nlp import layers
from keras_nlp import metrics
from keras_nlp import models
from keras_nlp import samplers
from keras_nlp import tokenizers
from keras_nlp import utils

# This is the global source of truth for the version number.
__version__ = "0.7.0.dev0"
