from bandit.core import config, manager
from bandit.core.docs_utils import get_url


def run_bandit(filename):
    "Run bandit security-check against a given file"

    # initialize bandit
    bandit_manager = manager.BanditManager(config.BanditConfig(), "file")

    # fetch files to be tested
    bandit_manager.discover_files([filename])

    # run the tests
    bandit_manager.run_tests()

    # fetch results
    results = bandit_manager.get_issue_list()

    # format output
    output = []
    for issue in results:
        output.append(
            {
                "description": issue.text,
                "test": issue.test,
                "test_id": issue.test_id,
                "test_link": get_url(issue.test_id),
                "cwe_id": issue.cwe.id,
                "cwe_link": issue.cwe.link(),
                "severity": issue.severity,
                "confidence": issue.confidence,
                "object": issue.ident,
                "line": min(issue.linerange),
                "line_end": max(issue.linerange),
                "col": issue.col_offset,
                "col_end": issue.end_col_offset,
            }
        )
    return output
