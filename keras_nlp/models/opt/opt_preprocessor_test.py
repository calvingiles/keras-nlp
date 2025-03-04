# Copyright 2023 The KerasNLP Authors
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

import tensorflow as tf

from keras_nlp.backend import keras
from keras_nlp.models.opt.opt_preprocessor import OPTPreprocessor
from keras_nlp.models.opt.opt_tokenizer import OPTTokenizer
from keras_nlp.tests.test_case import TestCase


class OPTPreprocessorTest(TestCase):
    def setUp(self):
        self.vocab = {
            "<pad>": 0,
            "</s>": 1,
            "air": 2,
            "Ġair": 3,
            "plane": 4,
            "Ġat": 5,
            "port": 6,
        }

        merges = ["Ġ a", "Ġ t", "Ġ k", "Ġ i", "Ġ b", "Ġa i", "p l", "n e"]
        merges += ["Ġa t", "p o", "r t", "o h", "l i", "Ġi s", "Ġb e", "s t"]
        merges += ["Ġt h", "Ġai r", "pl a", "Ġk oh", "Ġth e", "Ġbe st", "po rt"]
        merges += ["pla ne"]
        self.merges = merges

        self.preprocessor = OPTPreprocessor(
            tokenizer=OPTTokenizer(
                vocabulary=self.vocab,
                merges=self.merges,
            ),
            sequence_length=8,
        )

    def test_tokenize_strings(self):
        input_data = " airplane at airport"

        x = self.preprocessor(input_data)
        self.assertAllEqual(x["token_ids"], [1, 3, 4, 5, 3, 6, 1, 0])
        self.assertAllEqual(x["padding_mask"], [1, 1, 1, 1, 1, 1, 1, 0])

    def test_tokenize_list_of_strings(self):
        input_data = [" airplane at airport"] * 4

        x = self.preprocessor(input_data)
        self.assertAllEqual(x["token_ids"], [[1, 3, 4, 5, 3, 6, 1, 0]] * 4)
        self.assertAllEqual(x["padding_mask"], [[1, 1, 1, 1, 1, 1, 1, 0]] * 4)

    def test_no_start_end_token(self):
        input_data = [" airplane at airport"] * 4

        preprocessor = OPTPreprocessor(
            tokenizer=OPTTokenizer(
                vocabulary=self.vocab,
                merges=self.merges,
            ),
            sequence_length=8,
            add_start_token=False,
            add_end_token=False,
        )
        x = preprocessor(input_data)
        self.assertAllEqual(x["token_ids"], [[3, 4, 5, 3, 6, 0, 0, 0]] * 4)
        self.assertAllEqual(x["padding_mask"], [[1, 1, 1, 1, 1, 0, 0, 0]] * 4)

    def test_tokenize_labeled_batch(self):
        x = tf.constant([" airplane at airport"] * 4)
        y_in = tf.constant([1] * 4)
        sw_in = tf.constant([1.0] * 4)
        x, y, sw = self.preprocessor(x, y_in, sw_in)
        self.assertAllEqual(x["token_ids"], [[1, 3, 4, 5, 3, 6, 1, 0]] * 4)
        self.assertAllEqual(x["padding_mask"], [[1, 1, 1, 1, 1, 1, 1, 0]] * 4)
        self.assertAllEqual(y, y_in)
        self.assertAllEqual(sw, sw_in)

    def test_tokenize_labeled_dataset(self):
        x = tf.constant([" airplane at airport"] * 4)
        ds = tf.data.Dataset.from_tensor_slices(x)
        ds = ds.map(self.preprocessor)
        x = ds.batch(4).take(1).get_single_element()
        self.assertAllEqual(x["token_ids"], [[1, 3, 4, 5, 3, 6, 1, 0]] * 4)
        self.assertAllEqual(x["padding_mask"], [[1, 1, 1, 1, 1, 1, 1, 0]] * 4)

    def test_sequence_length_override(self):
        input_data = " airplane at airport"
        x = self.preprocessor(input_data, sequence_length=4)
        self.assertAllEqual(x["token_ids"], [1, 3, 4, 1])

    def test_serialization(self):
        config = keras.saving.serialize_keras_object(self.preprocessor)
        new_preprocessor = keras.saving.deserialize_keras_object(config)
        self.assertEqual(
            new_preprocessor.get_config(),
            self.preprocessor.get_config(),
        )
