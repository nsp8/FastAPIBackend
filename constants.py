import os

MODE = 1
PROD_DB = os.environ.get("MONGODB_CONN")
TEST_DB = os.environ.get("MONGODB_TEST")
