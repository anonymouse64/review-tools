import glob
import reviewtools
from reviewtools import modules, sr_tests


class TestModules(sr_tests.TestSnapReview):
    '''Tests for the modules module.'''
    def setUp(self):
        '''setup'''
        self.modules = modules.get_modules()
        super().setUp()

    def test_number_of_suitable_modules(self):
        '''Verify number of modules'''
        path = reviewtools.__path__[0]
        module_files = glob.glob(path + '/*.py')
        relevant_module_files = modules.narrow_down_modules(module_files)
        self.assertEqual(len(relevant_module_files),
                         len(self.modules))

    def test_num_suitable_modules_gt0(self):
        '''Verify number of modules is more than 0'''
        self.assertTrue(len(self.modules) > 0)

    def test_num_avail_review_classes(self):
        '''Verify have all the review classes'''
        count = 0
        for module_name in self.modules:
            review = modules.find_main_class(module_name)
            if review:
                count += 1
        self.assertEqual(count, len(self.modules),
                         'Not all files in reviewtools/sr_*.py contain '
                         'classes named Snap*Review.')
