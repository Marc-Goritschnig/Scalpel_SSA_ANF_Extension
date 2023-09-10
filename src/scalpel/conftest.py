import pytest

# Skip the test link function which is only imported and should not be used as a test itself
def pytest_collection_modifyitems(session, config, items):
    for i, item in enumerate(items):
        if item.name == 'test_link':
            item.add_marker(pytest.mark.skip(reason="test_link is not a test function"))
