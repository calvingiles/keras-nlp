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
from keras_nlp.models.bart.bart_seq_2_seq_lm_preprocessor import (
    BartSeq2SeqLMPreprocessor,
)
from keras_nlp.models.bart.bart_tokenizer import BartTokenizer
from keras_nlp.tests.test_case import TestCase


class BartSeq2SeqLMPreprocessorTest(TestCase):
    def setUp(self):
        vocab = {
            "<s>": 0,
            "<pad>": 1,
            "</s>": 2,
            "Ġair": 3,
            "plane": 4,
            "Ġat": 5,
            "port": 6,
            "Ġkoh": 7,
            "li": 8,
            "Ġis": 9,
            "Ġthe": 10,
            "Ġbest": 11,
            "<mask>": 12,
        }

        merges = ["Ġ a", "Ġ t", "Ġ k", "Ġ i", "Ġ b", "Ġa i", "p l", "n e"]
        merges += ["Ġa t", "p o", "r t", "o h", "l i", "Ġi s", "Ġb e", "s t"]
        merges += ["Ġt h", "Ġai r", "pl a", "Ġk oh", "Ġth e", "Ġbe st", "po rt"]
        merges += ["pla ne"]

        self.preprocessor = BartSeq2SeqLMPreprocessor(
            tokenizer=BartTokenizer(
                vocabulary=vocab,
                merges=merges,
            ),
            encoder_sequence_length=10,
            decoder_sequence_length=9,
        )

    def test_tokenize_strings(self):
        input_data = {
            "encoder_text": " airplane at airport",
            "decoder_text": " kohli is the best",
        }

        x_out, y_out, sw_out = self.preprocessor(input_data)
        self.assertAllEqual(
            x_out["encoder_token_ids"], [0, 3, 4, 5, 3, 6, 2, 1, 1, 1]
        )
        self.assertAllEqual(
            x_out["encoder_padding_mask"], [1, 1, 1, 1, 1, 1, 1, 0, 0, 0]
        )
        self.assertAllEqual(
            x_out["decoder_token_ids"], [2, 0, 7, 8, 9, 10, 11, 2, 1]
        )
        self.assertAllEqual(
            x_out["decoder_padding_mask"], [1, 1, 1, 1, 1, 1, 1, 1, 0]
        )
        self.assertAllEqual(y_out, [0, 7, 8, 9, 10, 11, 2, 1, 1])
        self.assertAllEqual(sw_out, [1, 1, 1, 1, 1, 1, 1, 0, 0])

    def test_tokenize_list_of_strings(self):
        input_data = {
            "encoder_text": [" airplane at airport"] * 4,
            "decoder_text": [" kohli is the best"] * 4,
        }

        x_out, y_out, sw_out = self.preprocessor(input_data)
        self.assertAllEqual(
            x_out["encoder_token_ids"], [[0, 3, 4, 5, 3, 6, 2, 1, 1, 1]] * 4
        )
        self.assertAllEqual(
            x_out["encoder_padding_mask"],
            [[1, 1, 1, 1, 1, 1, 1, 0, 0, 0]] * 4,
        )
        self.assertAllEqual(
            x_out["decoder_token_ids"], [[2, 0, 7, 8, 9, 10, 11, 2, 1]] * 4
        )
        self.assertAllEqual(
            x_out["decoder_padding_mask"], [[1, 1, 1, 1, 1, 1, 1, 1, 0]] * 4
        )
        self.assertAllEqual(y_out, [[0, 7, 8, 9, 10, 11, 2, 1, 1]] * 4)
        self.assertAllEqual(sw_out, [[1, 1, 1, 1, 1, 1, 1, 0, 0]] * 4)

    def test_error_multi_segment_input(self):
        input_data = {
            "encoder_text": (
                tf.constant([" airplane at airport"] * 2),
                tf.constant([" airplane"] * 2),
            ),
            "decoder_text": (
                tf.constant([" kohli is the best"] * 2),
                tf.constant([" kohli"] * 2),
            ),
        }

        with self.assertRaises(ValueError):
            self.preprocessor(input_data)

    def test_generate_preprocess(self):
        input_data = {
            "encoder_text": tf.convert_to_tensor([" airplane at airport"]),
            "decoder_text": tf.convert_to_tensor([" kohli is the best"]),
        }
        x_out = self.preprocessor.generate_preprocess(input_data)
        self.assertAllEqual(
            x_out["encoder_token_ids"], [[0, 3, 4, 5, 3, 6, 2, 1, 1, 1]]
        )
        self.assertAllEqual(
            x_out["encoder_padding_mask"], [[1, 1, 1, 1, 1, 1, 1, 0, 0, 0]]
        )
        self.assertAllEqual(
            x_out["decoder_token_ids"], [[2, 0, 7, 8, 9, 10, 11, 1, 1]]
        )
        self.assertAllEqual(
            x_out["decoder_padding_mask"], [[1, 1, 1, 1, 1, 1, 1, 0, 0]]
        )

    def test_generate_postprocess(self):
        input_data = {
            "decoder_token_ids": tf.constant([2, 0, 7, 8, 9, 10, 11, 1, 1]),
            "decoder_padding_mask": tf.cast(
                [1, 1, 1, 1, 1, 1, 1, 0, 0], dtype="bool"
            ),
        }
        x = self.preprocessor.generate_postprocess(input_data)
        self.assertAllEqual(x, " kohli is the best")

    def test_serialization(self):
        new_preprocessor = keras.saving.deserialize_keras_object(
            keras.saving.serialize_keras_object(self.preprocessor)
        )
        self.assertEqual(
            new_preprocessor.get_config(), self.preprocessor.get_config()
        )
