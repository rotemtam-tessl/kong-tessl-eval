#!/bin/bash

cd /workspace
mkdir -p /logs/verifier

# Expected hash of main_test.go - agent must NOT modify the test file
EXPECTED_HASH="c65fd421240c68e113491b0d4e32fa2330a940e6e1aef26802f26ddc6e6bfc3e"
ACTUAL_HASH=$(sha256sum main_test.go | cut -d' ' -f1)

if [ "$ACTUAL_HASH" != "$EXPECTED_HASH" ]; then
    echo "FAIL: main_test.go was modified (not allowed)"
    echo "Expected: $EXPECTED_HASH"
    echo "Got:      $ACTUAL_HASH"
    echo "0.0" > /logs/verifier/reward.txt
    exit 0
fi

echo "main_test.go integrity verified"
echo ""
echo "Running go test..."
go test -v ./... 2>&1 | tee /logs/verifier/test_output.txt
TEST_EXIT_CODE=${PIPESTATUS[0]}

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "All tests passed!"
    echo "1.0" > /logs/verifier/reward.txt
else
    echo "Tests failed!"
    echo "0.0" > /logs/verifier/reward.txt
fi

echo "Reward: $(cat /logs/verifier/reward.txt)"
