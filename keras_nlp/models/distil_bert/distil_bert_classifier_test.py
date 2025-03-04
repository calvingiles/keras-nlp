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

import os

import numpy as np
import pytest
import tensorflow as tf

from keras_nlp.backend import keras
from keras_nlp.backend import ops
from keras_nlp.models.distil_bert.distil_bert_backbone import DistilBertBackbone
from keras_nlp.models.distil_bert.distil_bert_classifier import (
    DistilBertClassifier,
)
from keras_nlp.models.distil_bert.distil_bert_preprocessor import (
    DistilBertPreprocessor,
)
from keras_nlp.models.distil_bert.distil_bert_tokenizer import (
    DistilBertTokenizer,
)
from keras_nlp.tests.test_case import TestCase


class DistilBertClassifierTest(TestCase):
    def setUp(self):
        # Setup model

        self.vocab = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"]
        self.vocab += ["the", "quick", "brown", "fox", "."]
        self.preprocessor = DistilBertPreprocessor(
            DistilBertTokenizer(vocabulary=self.vocab),
            sequence_length=8,
        )
        self.backbone = DistilBertBackbone(
            vocabulary_size=self.preprocessor.tokenizer.vocabulary_size(),
            num_layers=2,
            num_heads=2,
            hidden_dim=2,
            intermediate_dim=4,
            max_sequence_length=self.preprocessor.packer.sequence_length,
        )
        self.classifier = DistilBertClassifier(
            self.backbone,
            num_classes=4,
            preprocessor=self.preprocessor,
            # Check we handle serialization correctly.
            activation=keras.activations.softmax,
            hidden_dim=4,
        )

        self.raw_batch = [
            "the quick brown fox.",
            "the slow brown fox.",
        ]
        self.preprocessed_batch = self.preprocessor(self.raw_batch)
        self.raw_dataset = tf.data.Dataset.from_tensor_slices(
            (self.raw_batch, np.ones((2,)))
        ).batch(2)
        self.preprocessed_dataset = self.raw_dataset.map(self.preprocessor)

    def test_valid_call_classifier(self):
        self.classifier(self.preprocessed_batch)

    def test_classifier_predict(self):
        preds1 = self.classifier.predict(self.raw_batch)
        self.classifier.preprocessor = None
        preds2 = self.classifier.predict(self.preprocessed_batch)
        # Assert predictions match.
        self.assertAllClose(preds1, preds2)
        # Assert valid softmax output.
        self.assertAllClose(ops.sum(preds2, axis=-1), [1.0, 1.0])

    def test_classifier_fit(self):
        self.classifier.fit(self.raw_dataset)
        self.classifier.preprocessor = None
        self.classifier.fit(self.preprocessed_dataset)

    def test_classifier_fit_no_xla(self):
        self.classifier.preprocessor = None
        self.classifier.compile(
            loss="sparse_categorical_crossentropy",
            jit_compile=False,
        )
        self.classifier.fit(self.preprocessed_dataset)

    def test_serialization(self):
        # Defaults.
        original = DistilBertClassifier(
            self.backbone,
            num_classes=2,
        )
        config = keras.saving.serialize_keras_object(original)
        restored = keras.saving.deserialize_keras_object(config)
        self.assertEqual(restored.get_config(), original.get_config())
        # With options.
        original = DistilBertClassifier(
            self.backbone,
            num_classes=4,
            preprocessor=self.preprocessor,
            activation=keras.activations.softmax,
            hidden_dim=4,
            name="test",
            trainable=False,
        )
        config = keras.saving.serialize_keras_object(original)
        restored = keras.saving.deserialize_keras_object(config)
        self.assertEqual(restored.get_config(), original.get_config())

    @pytest.mark.large
    def test_saving_model(self):
        model_output = self.classifier.predict(self.raw_batch)
        path = os.path.join(self.get_temp_dir(), "model.keras")
        self.classifier.save(path, save_format="keras_v3")
        restored_model = keras.models.load_model(path)

        # Check we got the real object back.
        self.assertIsInstance(restored_model, DistilBertClassifier)

        # Check that output matches.
        restored_output = restored_model.predict(self.raw_batch)
        self.assertAllClose(model_output, restored_output)
