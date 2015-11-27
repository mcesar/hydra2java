import unittest
import os
import shutil
import tempfile
import hydra2java_lib

class GeneratorTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
    def tearDown(self):
        shutil.rmtree(self.tempdir)
    def assertGeneratedFiles(self, gen, variant):
        for file in os.listdir("fixtures"):
            if file.endswith(".json"):
                input_file = open('fixtures' + os.sep + file)
                gen.generate(input_file)
                expected = open('fixtures' + os.sep + file.replace('.json', '_' + variant+ '.java'))
                result = open(self.tempdir + os.sep + 'EntryPoint.java')
                self.assertEqual(expected.read().strip(), result.read().strip())
                expected.close()
                result.close()
    def test_default(self):
        gen = hydra2java_lib.Generator(destination=self.tempdir)
        self.assertGeneratedFiles(gen, 'default')
    def test_no_annotations(self):
        gen = hydra2java_lib.Generator(no_annotations=True, destination=self.tempdir)
        self.assertGeneratedFiles(gen, 'no_annotations')
