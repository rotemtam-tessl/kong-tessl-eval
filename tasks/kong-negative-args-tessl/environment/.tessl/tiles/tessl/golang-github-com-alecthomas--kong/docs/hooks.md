# Hooks and Lifecycle

This document covers Kong's hook interfaces that allow you to execute custom logic at various stages of the parsing lifecycle.

## Hook Interfaces

### BeforeReset

Called before values are reset to their defaults.

```go { .api }
// BeforeReset is a hook interface called before values are reset to defaults
type BeforeReset interface {
    BeforeReset(ctx *Context) error
}
```

### BeforeResolve

Called before resolvers are applied.

```go { .api }
// BeforeResolve is a hook interface called before resolvers are applied
type BeforeResolve interface {
    BeforeResolve(ctx *Context) error
}
```

### BeforeApply

Called before values are applied to the target.

```go { .api }
// BeforeApply is a hook interface called before values are applied to the target
type BeforeApply interface {
    BeforeApply(ctx *Context) error
}
```

### AfterApply

Called after values are applied and validated.

```go { .api }
// AfterApply is a hook interface called after values are applied and validated
type AfterApply interface {
    AfterApply(ctx *Context) error
}
```

### AfterRun

Called after Run() is called.

```go { .api }
// AfterRun is a hook interface called after Run() is called
type AfterRun interface {
    AfterRun(ctx *Context) error
}
```

### IgnoreDefault

Can be implemented by flags that want to be applied before any default commands.

```go { .api }
// IgnoreDefault can be implemented by flags that want to be applied
// before any default commands
type IgnoreDefault interface {
    IgnoreDefault()
}
```

## Hook Registration Options

```go { .api }
// WithBeforeReset registers a hook to run before field values are
// reset to their defaults
func WithBeforeReset(fn any) Option

// WithBeforeResolve registers a hook to run before resolvers are applied
func WithBeforeResolve(fn any) Option

// WithBeforeApply registers a hook to run before command line arguments
// are applied
func WithBeforeApply(fn any) Option

// WithAfterApply registers a hook to run after values are applied
// and validated
func WithAfterApply(fn any) Option
```

## Usage Examples

### Implementing BeforeReset Hook

```go
package main

import (
    "fmt"
    "github.com/alecthomas/kong"
)

type CLI struct {
    Debug bool `help:"Enable debug mode."`

    Serve struct {
        Port int `help:"Port to listen on." default:"8080"`
    } `cmd:"" help:"Start the server."`
}

// Implement BeforeReset on the CLI struct
func (c *CLI) BeforeReset(ctx *kong.Context) error {
    fmt.Println("Resetting configuration to defaults...")
    return nil
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // BeforeReset will be called automatically during parsing
    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Implementing BeforeResolve Hook

```go
type CLI struct {
    ConfigFile string `type:"path" help:"Configuration file."`
    Host       string `help:"Server host."`
    Port       int    `help:"Server port."`
}

func (c *CLI) BeforeResolve(ctx *kong.Context) error {
    fmt.Println("About to resolve configuration...")

    // Load custom resolver if config file is specified
    if c.ConfigFile != "" {
        file, err := os.Open(c.ConfigFile)
        if err != nil {
            return err
        }
        defer file.Close()

        resolver, err := kong.JSON(file)
        if err != nil {
            return err
        }

        ctx.AddResolver(resolver)
    }

    return nil
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Implementing BeforeApply Hook

```go
type CLI struct {
    Verbose bool   `help:"Enable verbose output."`
    Output  string `help:"Output file." type:"path"`
}

func (c *CLI) BeforeApply(ctx *kong.Context) error {
    fmt.Println("About to apply command-line arguments...")

    // Validate combinations before applying
    if c.Verbose && c.Output != "" {
        return fmt.Errorf("verbose mode not supported with output file")
    }

    return nil
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Implementing AfterApply Hook

```go
type CLI struct {
    Debug bool `help:"Enable debug mode."`

    Serve struct {
        Port int    `help:"Port to listen on." default:"8080"`
        Host string `help:"Host to bind to." default:"localhost"`
    } `cmd:"" help:"Start the server."`
}

func (c *CLI) AfterApply(ctx *kong.Context) error {
    fmt.Println("Configuration applied successfully")

    // Perform post-application validation
    if c.Debug {
        fmt.Printf("Debug mode enabled\n")
        fmt.Printf("Command: %s\n", ctx.Command())
    }

    return nil
}

func (s *Serve) AfterApply(ctx *kong.Context) error {
    // Command-specific validation
    if s.Port < 1024 && os.Geteuid() != 0 {
        return fmt.Errorf("privileged ports require root access")
    }

    return nil
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // AfterApply hooks will be called automatically
    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Implementing AfterRun Hook

```go
type CLI struct {
    Serve struct {
        Port int `help:"Port to listen on." default:"8080"`
    } `cmd:"" help:"Start the server."`
}

func (s *Serve) Run() error {
    fmt.Printf("Server started on port %d\n", s.Port)
    // Server logic here
    return nil
}

func (s *Serve) AfterRun(ctx *kong.Context) error {
    fmt.Println("Server stopped, cleaning up...")

    // Cleanup logic here
    return nil
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    err := ctx.Run()
    ctx.FatalIfErrorf(err)

    // AfterRun will be called after Run() completes
}
```

### Using Hook Registration Functions

```go
func beforeResetHook(ctx *kong.Context) error {
    fmt.Println("Global before reset hook")
    return nil
}

func afterApplyHook(ctx *kong.Context) error {
    fmt.Println("Global after apply hook")
    return nil
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.WithBeforeReset(beforeResetHook),
        kong.WithAfterApply(afterApplyHook),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    err = ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Multiple Hooks with Dependency Injection

```go
type Logger interface {
    Log(msg string)
}

type ConsoleLogger struct{}

func (c *ConsoleLogger) Log(msg string) {
    fmt.Println(msg)
}

func beforeApplyHook(ctx *kong.Context, logger Logger) error {
    logger.Log("Before apply hook with injected logger")
    return nil
}

func afterApplyHook(ctx *kong.Context, logger Logger) error {
    logger.Log("After apply hook with injected logger")
    return nil
}

func main() {
    var cli CLI
    logger := &ConsoleLogger{}

    parser := kong.Must(&cli,
        kong.Bind(logger),
        kong.WithBeforeApply(beforeApplyHook),
        kong.WithAfterApply(afterApplyHook),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    err = ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Hook Ordering

```go
type CLI struct {
    Serve struct{} `cmd:""`
}

func (c *CLI) BeforeReset(ctx *kong.Context) error {
    fmt.Println("1. CLI.BeforeReset")
    return nil
}

func (c *CLI) BeforeResolve(ctx *kong.Context) error {
    fmt.Println("2. CLI.BeforeResolve")
    return nil
}

func (c *CLI) BeforeApply(ctx *kong.Context) error {
    fmt.Println("3. CLI.BeforeApply")
    return nil
}

func (c *CLI) AfterApply(ctx *kong.Context) error {
    fmt.Println("4. CLI.AfterApply")
    return nil
}

func (s *Serve) Run() error {
    fmt.Println("5. Serve.Run")
    return nil
}

func (s *Serve) AfterRun(ctx *kong.Context) error {
    fmt.Println("6. Serve.AfterRun")
    return nil
}

// Execution order:
// 1. BeforeReset hooks
// 2. BeforeResolve hooks
// 3. BeforeApply hooks
// 4. AfterApply hooks
// 5. Run() method
// 6. AfterRun hooks
```

### Error Handling in Hooks

```go
type CLI struct {
    ConfigFile string `type:"path" help:"Configuration file."`
}

func (c *CLI) BeforeResolve(ctx *kong.Context) error {
    if c.ConfigFile == "" {
        return fmt.Errorf("configuration file is required")
    }

    if _, err := os.Stat(c.ConfigFile); os.IsNotExist(err) {
        return fmt.Errorf("configuration file not found: %s", c.ConfigFile)
    }

    return nil
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // If BeforeResolve returns an error, parsing will fail
    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Conditional Hook Logic

```go
type CLI struct {
    Debug bool `help:"Enable debug mode."`

    Serve struct {
        Port int `help:"Port to listen on." default:"8080"`
    } `cmd:"" help:"Start the server."`

    Build struct {
        Output string `help:"Output directory."`
    } `cmd:"" help:"Build the project."`
}

func (c *CLI) AfterApply(ctx *kong.Context) error {
    command := ctx.Command()

    switch command {
    case "serve":
        fmt.Println("Preparing to start server...")
        // Server-specific setup

    case "build":
        fmt.Println("Preparing to build project...")
        // Build-specific setup
    }

    return nil
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Using Context in Hooks

```go
type CLI struct {
    Verbose bool `help:"Enable verbose output."`

    Serve struct {
        Port int `help:"Port to listen on." default:"8080"`
    } `cmd:"" help:"Start the server."`
}

func (c *CLI) AfterApply(ctx *kong.Context) error {
    // Access context information
    fmt.Printf("Application: %s\n", ctx.Model.Name)
    fmt.Printf("Command: %s\n", ctx.Command())
    fmt.Printf("Args: %v\n", ctx.Args)

    // Examine flags
    flags := ctx.Flags()
    fmt.Printf("Available flags: %d\n", len(flags))

    // Check selected command
    if selected := ctx.Selected(); selected != nil {
        fmt.Printf("Selected: %s\n", selected.Name)
    }

    return nil
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### IgnoreDefault Implementation

```go
// HelpFlag that ignores default commands
type CustomHelpFlag bool

func (h CustomHelpFlag) IgnoreDefault() {
    // Marker method - no implementation needed
}

func (h CustomHelpFlag) BeforeApply(ctx *kong.Context) error {
    // Print help and exit
    ctx.PrintUsage(false)
    os.Exit(0)
    return nil
}

type CLI struct {
    Help CustomHelpFlag `short:"h" help:"Show help."`

    Serve struct {
        Port int `help:"Port to listen on." default:"8080"`
    } `cmd:"" default:"1" help:"Start the server."`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // --help will be processed before the default "serve" command
    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Stateful Hooks

```go
type CLI struct {
    startTime time.Time

    Serve struct{} `cmd:""`
}

func (c *CLI) BeforeApply(ctx *kong.Context) error {
    // Store state in the CLI struct
    c.startTime = time.Now()
    fmt.Println("Starting execution...")
    return nil
}

func (c *CLI) AfterRun(ctx *kong.Context) error {
    // Use stored state
    duration := time.Since(c.startTime)
    fmt.Printf("Execution completed in %v\n", duration)
    return nil
}

func (s *Serve) Run(cli *CLI) error {
    fmt.Println("Running serve command...")
    // Access parent CLI state
    fmt.Printf("Started at: %v\n", cli.startTime)
    return nil
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli,
        kong.Bind(&cli),
    )

    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Combining All Hooks

```go
type CLI struct {
    Verbose bool `help:"Enable verbose output."`

    Serve struct {
        Port int `help:"Port to listen on." default:"8080"`
    } `cmd:"" help:"Start the server."`
}

func (c *CLI) BeforeReset(ctx *kong.Context) error {
    if c.Verbose {
        fmt.Println("[1] BeforeReset: Resetting to defaults")
    }
    return nil
}

func (c *CLI) BeforeResolve(ctx *kong.Context) error {
    if c.Verbose {
        fmt.Println("[2] BeforeResolve: About to resolve from external sources")
    }
    return nil
}

func (c *CLI) BeforeApply(ctx *kong.Context) error {
    if c.Verbose {
        fmt.Println("[3] BeforeApply: About to apply parsed values")
    }
    return nil
}

func (c *CLI) AfterApply(ctx *kong.Context) error {
    if c.Verbose {
        fmt.Println("[4] AfterApply: Values applied successfully")
    }
    return nil
}

func (s *Serve) Run(cli *CLI) error {
    if cli.Verbose {
        fmt.Println("[5] Run: Executing command")
    }
    fmt.Printf("Starting server on port %d\n", s.Port)
    return nil
}

func (s *Serve) AfterRun(ctx *kong.Context) error {
    cli := ctx.Model.Target.Interface().(*CLI)
    if cli.Verbose {
        fmt.Println("[6] AfterRun: Command completed")
    }
    return nil
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli,
        kong.Bind(&cli),
    )

    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```
