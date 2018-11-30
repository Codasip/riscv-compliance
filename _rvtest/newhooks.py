# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

import pytest

@pytest.mark.firstresult
def pytest_rvtest_model_init(config, model_path):
    """ called during pytest_configure """