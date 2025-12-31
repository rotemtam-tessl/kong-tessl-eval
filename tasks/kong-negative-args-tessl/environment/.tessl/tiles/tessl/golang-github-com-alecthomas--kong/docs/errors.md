# Error Handling

This document covers Kong's error types and error handling patterns.

## Error Types

### ParseError

The error type returned by Kong.Parse().

```go { .api }
// ParseError is the error type returned by Kong.Parse()
type ParseError struct {
    error              // Embedded error
    Context *Context   // Parse context that triggered the error
}
```

### ParseError Methods

```go { .api }
// Unwrap returns the original cause of the error
func (p *ParseError) Unwrap() error

// ExitCode returns the status that Kong should exit with
func (p *ParseError) ExitCode() int
```

## Error Interfaces

### ExitCoder

Interface that may be implemented by an error value to provide an integer exit code.

```go { .api }
// ExitCoder may be implemented by an error value to provide an
// integer exit code
type ExitCoder interface {
    ExitCode() int
}
```

## Usage Examples

### Basic Error Handling

```go
package main

import (
    "fmt"
    "os"
    "github.com/alecthomas/kong"
)

type CLI struct {
    Port int `help:"Port to listen on." required:""`
}

func main() {
    var cli CLI
    parser := kong.Must(&cli)

    ctx, err := parser.Parse(os.Args[1:])
    if err != nil {
        // Error during parsing
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }

    // Use parsed values
    fmt.Printf("Port: %d\n", cli.Port)
}
```

### Using FatalIfErrorf

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli)

    ctx, err := parser.Parse(os.Args[1:])
    // Automatically handles error and exits
    parser.FatalIfErrorf(err)

    // Continues only if no error
    fmt.Printf("Port: %d\n", cli.Port)
}
```

### Handling ParseError

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli)

    ctx, err := parser.Parse(os.Args[1:])
    if err != nil {
        // Type assertion to access ParseError details
        if parseErr, ok := err.(*kong.ParseError); ok {
            fmt.Fprintf(os.Stderr, "Parse error: %v\n", parseErr)

            // Access the context that caused the error
            if parseErr.Context != nil {
                fmt.Fprintf(os.Stderr, "Command: %s\n", parseErr.Context.Command())
                fmt.Fprintf(os.Stderr, "Args: %v\n", parseErr.Context.Args)
            }

            // Get the original error
            originalErr := parseErr.Unwrap()
            fmt.Fprintf(os.Stderr, "Cause: %v\n", originalErr)

            // Exit with appropriate code
            os.Exit(parseErr.ExitCode())
        }

        // Generic error
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
}
```

### Custom Exit Codes

```go
type AppError struct {
    msg  string
    code int
}

func (e *AppError) Error() string {
    return e.msg
}

func (e *AppError) ExitCode() int {
    return e.code
}

type CLI struct {
    Serve struct{} `cmd:""`
}

func (s *Serve) Run() error {
    // Return error with custom exit code
    if !checkPrerequisites() {
        return &AppError{
            msg:  "missing prerequisites",
            code: 2,
        }
    }

    return nil
}

func checkPrerequisites() bool {
    return false
}

func main() {
    var cli CLI
    parser := kong.Must(&cli)

    ctx, err := parser.Parse(os.Args[1:])
    if err != nil {
        if exitErr, ok := err.(kong.ExitCoder); ok {
            os.Exit(exitErr.ExitCode())
        }
        os.Exit(1)
    }

    err = ctx.Run()
    if err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        if exitErr, ok := err.(kong.ExitCoder); ok {
            os.Exit(exitErr.ExitCode())
        }
        os.Exit(1)
    }
}
```

### Error Handling with Usage Display

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli,
        kong.UsageOnError(),
    )

    ctx, err := parser.Parse(os.Args[1:])
    // Usage will be automatically displayed on error
    parser.FatalIfErrorf(err)
}
```

### Short Usage on Error

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli,
        kong.ShortUsageOnError(),
    )

    ctx, err := parser.Parse(os.Args[1:])
    // Short usage will be displayed on error
    parser.FatalIfErrorf(err)
}
```

### Validation Errors

```go
type CLI struct {
    Port int `help:"Port to listen on." required:""`
}

func (c *CLI) AfterApply(ctx *kong.Context) error {
    // Custom validation
    if c.Port < 1 || c.Port > 65535 {
        return fmt.Errorf("port must be between 1 and 65535, got %d", c.Port)
    }
    return nil
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // Validation error will be caught here
    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Context Validation

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli)

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // Manually validate context
    if err := ctx.Validate(); err != nil {
        fmt.Fprintf(os.Stderr, "Validation error: %v\n", err)
        os.Exit(1)
    }
}
```

### Graceful Error Handling

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli,
        kong.Exit(func(code int) {
            // Custom exit handler
            if code != 0 {
                fmt.Fprintf(os.Stderr, "Application exiting with code %d\n", code)
            }
            os.Exit(code)
        }),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    err = ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Error Messages with Printf/Errorf

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli,
        kong.Name("myapp"),
    )

    ctx, err := parser.Parse(os.Args[1:])
    if err != nil {
        // Print error with application name prefix
        parser.Errorf("failed to parse: %v", err)
        os.Exit(1)
    }

    // Print informational messages
    parser.Printf("Starting application...")

    err = ctx.Run()
    if err != nil {
        // Fatalf prints error and exits
        parser.Fatalf("execution failed: %v", err)
    }
}
```

### Wrapped Errors

```go
import "errors"

func (s *Serve) Run() error {
    if err := startServer(); err != nil {
        // Wrap error with context
        return fmt.Errorf("failed to start server: %w", err)
    }
    return nil
}

func startServer() error {
    return fmt.Errorf("port already in use")
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    err := ctx.Run()
    if err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)

        // Unwrap to get original error
        var originalErr error = err
        for {
            unwrapped := errors.Unwrap(originalErr)
            if unwrapped == nil {
                break
            }
            originalErr = unwrapped
            fmt.Fprintf(os.Stderr, "Caused by: %v\n", originalErr)
        }

        os.Exit(1)
    }
}
```

### Testing Error Handling

```go
import (
    "bytes"
    "testing"
)

func TestErrorHandling(t *testing.T) {
    var cli CLI
    var stderr bytes.Buffer

    parser := kong.Must(&cli,
        kong.Writers(nil, &stderr),
        kong.Exit(func(code int) {
            // Don't actually exit in tests
            if code != 0 {
                t.Logf("Would exit with code %d", code)
            }
        }),
    )

    // Parse with invalid arguments
    _, err := parser.Parse([]string{"--invalid-flag"})
    if err == nil {
        t.Fatal("Expected error for invalid flag")
    }

    // Check error type
    if _, ok := err.(*kong.ParseError); !ok {
        t.Errorf("Expected ParseError, got %T", err)
    }

    // Check stderr output
    if stderr.Len() == 0 {
        t.Error("Expected error message in stderr")
    }
}
```

### Hook Error Propagation

```go
type CLI struct {
    Serve struct{} `cmd:""`
}

func (c *CLI) BeforeApply(ctx *kong.Context) error {
    // Validation error in hook
    if !systemReady() {
        return fmt.Errorf("system not ready")
    }
    return nil
}

func (s *Serve) Run() error {
    // Error during execution
    if err := doWork(); err != nil {
        return err
    }
    return nil
}

func (s *Serve) AfterRun(ctx *kong.Context) error {
    // Cleanup error
    if err := cleanup(); err != nil {
        return fmt.Errorf("cleanup failed: %w", err)
    }
    return nil
}

func systemReady() bool   { return false }
func doWork() error       { return nil }
func cleanup() error      { return nil }

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // All hook and Run errors are propagated
    err := ctx.Run()
    if err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
}
```

### Multi-Error Collection

```go
type ValidationErrors struct {
    errors []error
}

func (v *ValidationErrors) Error() string {
    if len(v.errors) == 0 {
        return "no errors"
    }
    if len(v.errors) == 1 {
        return v.errors[0].Error()
    }
    return fmt.Sprintf("%d validation errors: %v", len(v.errors), v.errors[0])
}

func (v *ValidationErrors) Add(err error) {
    if err != nil {
        v.errors = append(v.errors, err)
    }
}

func (v *ValidationErrors) HasErrors() bool {
    return len(v.errors) > 0
}

type CLI struct {
    Host string `help:"Server host."`
    Port int    `help:"Server port."`
}

func (c *CLI) AfterApply(ctx *kong.Context) error {
    var errs ValidationErrors

    if c.Host == "" {
        errs.Add(fmt.Errorf("host is required"))
    }

    if c.Port < 1 || c.Port > 65535 {
        errs.Add(fmt.Errorf("port must be between 1 and 65535"))
    }

    if errs.HasErrors() {
        return &errs
    }

    return nil
}
```

### Panic Recovery

```go
func main() {
    var cli CLI

    // Use Must which panics on error
    parser := kong.Must(&cli)

    // Recover from panics
    defer func() {
        if r := recover(); r != nil {
            fmt.Fprintf(os.Stderr, "Panic recovered: %v\n", r)
            os.Exit(1)
        }
    }()

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    err = ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Distinguishing Error Types

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli)

    ctx, err := parser.Parse(os.Args[1:])
    if err != nil {
        switch e := err.(type) {
        case *kong.ParseError:
            fmt.Fprintf(os.Stderr, "Parse error: %v\n", e)
            os.Exit(e.ExitCode())

        case kong.ExitCoder:
            fmt.Fprintf(os.Stderr, "Error with exit code: %v\n", e)
            os.Exit(e.ExitCode())

        default:
            fmt.Fprintf(os.Stderr, "Unknown error: %v\n", e)
            os.Exit(1)
        }
    }

    err = ctx.Run()
    if err != nil {
        handleExecutionError(err)
    }
}

func handleExecutionError(err error) {
    // Custom error handling logic
    fmt.Fprintf(os.Stderr, "Execution error: %v\n", err)
    os.Exit(1)
}
```
