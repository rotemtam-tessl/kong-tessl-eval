#!/bin/bash

cd /workspace
mkdir -p /logs/verifier

# Expected hash of main_test.go - agent must NOT modify the test file
EXPECTED_HASH="8d4355e5a1aaa0cce6f5b62d73ce7422e84bea919fb1f21accd3aab5c874a4a9"
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
