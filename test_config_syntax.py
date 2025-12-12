class Config:
    @staticmethod
    def _get_value(key):
        return f"value_of_{key}"

    # Test calling it during class creation
    try:
        TEST_VAL = _get_value.__func__("test_key")
    except Exception as e:
        TEST_VAL = f"ERROR: {e}"

print(f"Result: {Config.TEST_VAL}")
