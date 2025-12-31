# Core Parsing

This document covers the core parsing functions and types in Kong, including parser creation, context management, and path tracing.

## Parser Creation Functions

```go { .api }
// New creates a new Kong parser on the provided grammar structure.
// The grammar must be a pointer to a struct. Returns a configured Kong
// instance or an error if the grammar is invalid.
func New(grammar any, options ...Option) (*Kong, error)

// Must creates a new Parser or panics if there is an error.
// Useful for initialization where errors are not expected.
func Must(ast any, options ...Option) *Kong

// Parse is a global convenience function that constructs a Kong parser
// and calls Parse on it. Exits on error.
func Parse(cli any, options ...Option) *Context

// Trace traces the path of args through the grammar tree. Returns a
// Context with the path of all commands, arguments, positionals, and flags.
// Does not validate or apply values.
func Trace(k *Kong, args []string) (*Context, error)

// ApplyDefaults applies default values to the target struct without
// parsing command-line arguments.
func ApplyDefaults(target any, options ...Option) error
```

## Usage Examples

### Basic Parser Creation

```go
package main

import "github.com/alecthomas/kong"

type CLI struct {
    Verbose bool   `help:"Enable verbose output."`
    Output  string `help:"Output file." type:"path"`
}

func main() {
    var cli CLI

    // Create parser with New()
    parser, err := kong.New(&cli)
    if err != nil {
        panic(err)
    }

    // Parse command-line arguments
    ctx, err := parser.Parse(os.Args[1:])
    if err != nil {
        parser.FatalIfErrorf(err)
    }

    // Use parsed values
    if cli.Verbose {
        fmt.Println("Verbose mode enabled")
    }
}
```

### Using Must for Simpler Code

```go
func main() {
    var cli CLI

    // Must panics on error - cleaner for applications
    parser := kong.Must(&cli,
        kong.Name("myapp"),
        kong.Description("A simple application"),
        kong.UsageOnError(),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // Application logic here
}
```

### Using Global Parse Function

```go
func main() {
    var cli CLI

    // Parse creates parser, parses, and returns context
    // Exits automatically on error
    ctx := kong.Parse(&cli,
        kong.Name("myapp"),
        kong.UsageOnError(),
    )

    // Ready to use immediately
    fmt.Printf("Verbose: %v\n", cli.Verbose)
}
```

### Applying Defaults Without Parsing

```go
type Config struct {
    Port int    `default:"8080"`
    Host string `default:"localhost"`
}

func main() {
    var config Config

    // Apply defaults without parsing command line
    err := kong.ApplyDefaults(&config)
    if err != nil {
        panic(err)
    }

    // config.Port == 8080
    // config.Host == "localhost"
}
```

## Kong Type

The main parser type.

```go { .api }
// Kong is the main parser type
type Kong struct {
    // Model is the grammar model
    Model *Application

    // Exit is the termination function (defaults to os.Exit)
    Exit func(int)

    // Stdout is the standard output writer
    Stdout io.Writer

    // Stderr is the standard error writer
    Stderr io.Writer
}
```

### Kong Methods

```go { .api }
// Parse parses arguments into the target grammar
func (k *Kong) Parse(args []string) (*Context, error)

// Printf writes a message to Kong.Stdout with the application name prefixed
func (k *Kong) Printf(format string, args ...any) *Kong

// Errorf writes a message to Kong.Stderr with the application name prefixed
func (k *Kong) Errorf(format string, args ...any) *Kong

// Fatalf writes a message to Kong.Stderr then exits with status 1
func (k *Kong) Fatalf(format string, args ...any)

// FatalIfErrorf terminates with an error message if err != nil
func (k *Kong) FatalIfErrorf(err error, args ...any)

// LoadConfig loads configuration from path using the configured loader
func (k *Kong) LoadConfig(path string) (Resolver, error)
```

## Context Type

Contains the current parse context and provides methods for executing commands.

```go { .api }
// Context contains the current parse context
type Context struct {
    *Kong  // Embedded Kong instance

    // Path is the trace through parsed nodes
    Path []*Path

    // Args are the original command-line arguments
    Args []string

    // Error that occurred during trace, if any
    Error error
}
```

### Context Methods - Binding

```go { .api }
// Bind adds bindings to the Context
func (c *Context) Bind(args ...any)

// BindTo adds a binding to the Context for an interface
func (c *Context) BindTo(impl, iface any)

// BindToProvider allows binding of provider functions
func (c *Context) BindToProvider(provider any) error

// BindSingletonProvider allows binding of singleton provider functions
func (c *Context) BindSingletonProvider(provider any) error
```

### Context Methods - Query

```go { .api }
// Value returns the value for a particular path element
func (c *Context) Value(path *Path) reflect.Value

// Selected returns the selected command or argument
func (c *Context) Selected() *Node

// Empty returns true if there were no arguments provided
func (c *Context) Empty() bool

// Flags returns the accumulated available flags
func (c *Context) Flags() []*Flag

// Command returns the full command path
func (c *Context) Command() string

// FlagValue returns the set value of a flag or its default
func (c *Context) FlagValue(flag *Flag) any
```

### Context Methods - Resolution and Application

```go { .api }
// AddResolver adds a context-specific resolver
func (c *Context) AddResolver(resolver Resolver)

// Reset recursively resets values to defaults
func (c *Context) Reset() error

// Resolve walks through the traced path, applying resolvers
func (c *Context) Resolve() error

// Apply applies traced context to the target grammar
func (c *Context) Apply() (string, error)

// ApplyDefaults applies defaults if they are not already set
func (c *Context) ApplyDefaults() error

// Validate validates the current context
func (c *Context) Validate() error
```

### Context Methods - Execution

```go { .api }
// Run executes the Run() method on the selected command
func (c *Context) Run(binds ...any) error

// RunNode calls the Run() method on an arbitrary node
func (c *Context) RunNode(node *Node, binds ...any) error

// Call calls an arbitrary function with bound values
func (c *Context) Call(fn any, binds ...any) ([]any, error)

// PrintUsage prints usage to Kong's stdout
func (c *Context) PrintUsage(summary bool) error
```

### Context Usage Example

```go
type CLI struct {
    Debug bool `help:"Enable debug mode."`

    Serve struct {
        Port int `help:"Port to listen on." default:"8080"`
    } `cmd:"" help:"Start the server."`
}

func (s *Serve) Run(ctx *kong.Context) error {
    fmt.Printf("Starting server on port %d\n", s.Port)
    // Server logic here
    return nil
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // Run executes the Run() method on the selected command
    // Automatically injects the context
    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

## Path Type

Records the nodes and parsed values from the current command-line.

```go { .api }
// Path records the nodes and parsed values from the current command-line
type Path struct {
    // Parent is the parent node
    Parent *Node

    // App is the application node (one of App, Positional, Flag,
    // Argument, Command will be non-nil)
    App *Application

    // Positional is the positional argument
    Positional *Positional

    // Flag is the flag
    Flag *Flag

    // Argument is the argument
    Argument *Argument

    // Command is the command
    Command *Command

    // Flags added by this node
    Flags []*Flag

    // Resolved is true if created as the result of a resolver
    Resolved bool
}
```

### Path Methods

```go { .api }
// Node returns the Node associated with this Path
func (p *Path) Node() *Node

// Visitable returns the Visitable for this path element
func (p *Path) Visitable() Visitable

// Remainder returns the remaining unparsed args after this Path element
func (p *Path) Remainder() []string
```

### Path Usage Example

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli)

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)

    // Examine the parse path
    for i, p := range ctx.Path {
        node := p.Node()
        if node != nil {
            fmt.Printf("Step %d: %s\n", i, node.Name)
        }

        // Check what was selected at each step
        if p.Command != nil {
            fmt.Printf("  Command: %s\n", p.Command.Name)
        }
        if p.Flag != nil {
            fmt.Printf("  Flag: %s\n", p.Flag.Name)
        }
    }
}
```

## Advanced Tracing

The `Trace` function allows you to analyze what would be parsed without actually applying values.

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli)

    // Trace without applying values
    ctx, err := kong.Trace(parser, []string{"serve", "--port", "9000"})
    if err != nil {
        panic(err)
    }

    // Examine what would be parsed
    fmt.Printf("Command: %s\n", ctx.Command())
    fmt.Printf("Path length: %d\n", len(ctx.Path))

    // Now actually parse and apply
    ctx, err = parser.Parse([]string{"serve", "--port", "9000"})
    if err != nil {
        panic(err)
    }
}
```
