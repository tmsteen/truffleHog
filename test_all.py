import unittest
import os
import sys
import json
import io
import re
from truffleHog import truffleHog


class TestStringMethods(unittest.TestCase):

    def test_shannon(self):
        random_stringB64 = "ZWVTjPQSdhwRgl204Hc51YCsritMIzn8B=/p9UyeX7xu6KkAGqfm3FJ+oObLDNEva"
        random_stringHex = "b3A0a1FDfe86dcCE945B72"
        self.assertGreater(truffleHog.shannon_entropy(random_stringB64, truffleHog.BASE64_CHARS), 4.5)
        self.assertGreater(truffleHog.shannon_entropy(random_stringHex, truffleHog.HEX_CHARS), 3)

    def test_cloning(self):
        project_path, _ = truffleHog.clone_git_repo("https://github.com/dxa4481/truffleHog.git")
        license_file = os.path.join(project_path, "LICENSE")
        self.assertTrue(os.path.isfile(license_file))

    def test_unicode_expection(self):
        try:
            truffleHog.find_strings("https://github.com/dxa4481/tst.git")
        except UnicodeEncodeError:
            self.fail("Unicode print error")

    def test_return_correct_commit_hash(self):
        # Start at commit d15627104d07846ac2914a976e8e347a663bbd9b, which
        # is immediately followed by a secret inserting commit:
        # https://github.com/dxa4481/truffleHog/commit/9ed54617547cfca783e0f81f8dc5c927e3d1e345
        since_commit = 'd15627104d07846ac2914a976e8e347a663bbd9b'
        commit_w_secret = '9ed54617547cfca783e0f81f8dc5c927e3d1e345'
        cross_valdiating_commit_w_secret_comment = 'OH no a secret'

        json_result = ''
        if sys.version_info >= (3,):
            tmp_stdout = io.StringIO()
        else:
            tmp_stdout = io.BytesIO()
        bak_stdout = sys.stdout

        # Redirect STDOUT, run scan and re-establish STDOUT
        sys.stdout = tmp_stdout
        try:
            truffleHog.find_strings("https://github.com/dxa4481/truffleHog.git",
                since_commit=since_commit, printJson=True, surpress_output=False)
        finally:
            sys.stdout = bak_stdout

        json_result_list = tmp_stdout.getvalue().split('\n')
        results = [json.loads(r) for r in json_result_list if bool(r.strip())]
        filtered_results = list(filter(lambda r: r['commitHash'] == commit_w_secret, results))
        self.assertEqual(1, len(filtered_results))
        self.assertEqual(commit_w_secret, filtered_results[0]['commitHash'])
        # Additionally, we cross-validate the commit comment matches the expected comment
        self.assertEqual(cross_valdiating_commit_w_secret_comment, filtered_results[0]['commit'].strip())


class TestRepoTypes(unittest.TestCase):
    def test_file_repo(self):
        # First, we'll clone the remote repo
        git_url = "https://github.com/dxa4481/truffleHog.git"
        project_path_1, c = truffleHog.clone_git_repo(git_url)
        self.assertTrue(re.search(r'^/tmp/', project_path_1))

        # Second, we'll use a local repo without cloning
        project_path_2, c = truffleHog.clone_git_repo('file://' + project_path_1)
        self.assertTrue(re.search(r'^/tmp/', project_path_2))
        self.assertEqual(project_path_1, project_path_2)

        # Third, we'll use a sloppy filepath as a project repo address
        project_path_3, c = truffleHog.clone_git_repo(project_path_2)
        self.assertTrue(re.search(r'^/tmp/', project_path_3))
        self.assertEqual(project_path_2, project_path_3)

        # Fourth, we'll force another clone from a local repo
        project_path_4, c = truffleHog.clone_git_repo('file://' + project_path_3, force=True)
        self.assertTrue(re.search(r'^/tmp/', project_path_4))
        self.assertNotEqual(project_path_3, project_path_4)

    def test_remove_only_temp_repos(self):
        # First, we'll clone the remote repo
        git_url = "https://github.com/dxa4481/truffleHog.git"
        project_path, created = truffleHog.clone_git_repo(git_url)
        self.assertTrue(re.search(r'^/tmp/', project_path))
        self.assertTrue(created)

        # Second, we'll use a local repo without cloning to find strigs
        truffleHog.find_strings('file://' + project_path)
        self.assertTrue(os.path.exists(project_path))



if __name__ == '__main__':
    unittest.main()
