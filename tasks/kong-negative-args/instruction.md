# Fix the Failing Test

The test `TestAddNegative` in `main_test.go` is failing. Fix `main.go` to make it pass.

**Constraints:**

- Do NOT modify `main_test.go`
- Use the Kong API to fix parsing of negative flag values (e.g., `--b -2`)
- Do NOT require users to use `=` syntax (e.g., `--b=-2`)
- The fix is short (one line change)

**Verify:**

```bash
go test -v ./...
```
