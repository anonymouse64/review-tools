from clickreviews.cr_common import ClickReview
from clickreviews import cr_tests


class ClickReviewTestCase(cr_tests.TestClickReview):

    def setUp(self):
        super().setUp()
        self.review = ClickReview('app.click', 'review_type')

    def test_add_result_default_manual_review(self):
        self.review._add_result('info', 'some-check', 'OK')
        self.assertEqual(self.review.click_report, {
            'info': {
                'some-check': {
                    'text': 'OK',
                    'manual_review': False,
                }
            },
            'warn': {},
            'error': {},
        })

    def test_add_result_custom_manual_review(self):
        self.review._add_result('info', 'some-check', 'OK',
                                manual_review=True)
        self.assertEqual(self.review.click_report, {
            'info': {
                'some-check': {
                    'text': 'OK',
                    'manual_review': True,
                }
            },
            'warn': {},
            'error': {},
        })

    def test_add_result_override_result_type_warn(self):
        self.review._add_result('warn', 'some-check', 'notok',
                                override_result_type='info')
        self.assertEqual(self.review.click_report, {
            'info': {
                'some-check': {
                    'text': '[WARN] notok',
                    'manual_review': False,
                }
            },
            'warn': {},
            'error': {},
        })

    def test_add_result_override_result_type_error(self):
        self.review._add_result('error', 'some-check', 'notok',
                                override_result_type='info')
        self.assertEqual(self.review.click_report, {
            'info': {
                'some-check': {
                    'text': '[ERROR] notok',
                    'manual_review': False,
                }
            },
            'warn': {},
            'error': {},
        })

    def test_add_result_override_result_type_info(self):
        self.review._add_result('info', 'some-check', 'ok',
                                override_result_type='warn')
        self.assertEqual(self.review.click_report, {
            'warn': {
                'some-check': {
                    'text': '[INFO] ok',
                    'manual_review': False,
                }
            },
            'info': {},
            'error': {},
        })

    def test_verify_peer_hooks_empty(self):
        '''Check verify_peer_hooks() - empty'''
        peer_hooks = dict()
        my_hook = "foo"
        peer_hooks[my_hook] = dict()
        peer_hooks[my_hook]['allowed'] = []
        peer_hooks[my_hook]['required'] = []
        self.review.peer_hooks = peer_hooks

        d = self.review._verify_peer_hooks(my_hook)
        self.assertEqual(0, len(d.keys()))

    def test_verify_peer_hooks_missing(self):
        '''Check verify_peer_hooks() - missing required'''
        peer_hooks = dict()
        my_hook = "desktop"
        peer_hooks[my_hook] = dict()
        peer_hooks[my_hook]['allowed'] = ["apparmor", "urls"]
        peer_hooks[my_hook]['required'] = ["nonexistent"]
        self.review.peer_hooks = peer_hooks

        d = self.review._verify_peer_hooks(my_hook)
        self.assertEqual(1, len(d.keys()))
        self.assertTrue('missing' in d.keys())
        self.assertTrue('nonexistent' in d['missing'][self.default_appname])

    def test_verify_peer_hooks_disallowed(self):
        '''Check verify_peer_hooks() - disallowed'''
        peer_hooks = dict()
        my_hook = "desktop"
        peer_hooks[my_hook] = dict()
        peer_hooks[my_hook]['allowed'] = ["apparmor"]
        peer_hooks[my_hook]['required'] = []
        self.review.peer_hooks = peer_hooks

        d = self.review._verify_peer_hooks(my_hook)
        self.assertEqual(1, len(d.keys()))
        self.assertTrue('disallowed' in d.keys())
        self.assertTrue('urls' in d['disallowed'][self.default_appname])

    def test_get_check_name(self):
        name = self.review._get_check_name('prefix')
        self.assertEqual(name, 'review_type:prefix')

    def test_get_check_name_with_app(self):
        name = self.review._get_check_name('prefix', app='app')
        self.assertEqual(name, 'review_type:prefix:app')

    def test_get_check_name_with_extra(self):
        name = self.review._get_check_name('prefix', extra='extra')
        self.assertEqual(name, 'review_type:prefix:extra')

    def test_get_check_name_with_app_and_extra(self):
        name = self.review._get_check_name('prefix', app='app', extra='extra')
        self.assertEqual(name, 'review_type:prefix:app:extra')

    def test_check_if_message_catalog_true(self):
        self.assertTrue(self.review._check_if_message_catalog('/a/b/foo.mo'))

    def test_check_if_message_catalog_false(self):
        self.assertFalse(self.review._check_if_message_catalog('/a/b/foo.txt'))
