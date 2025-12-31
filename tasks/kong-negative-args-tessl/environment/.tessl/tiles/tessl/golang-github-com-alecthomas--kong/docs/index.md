# Kong Command-Line Parser

Kong is a command-line parser for Go that enables building complex CLI applications through declarative struct-based grammar definitions. It maps command-line arguments to Go struct fields using struct tags, supporting arbitrarily complex command hierarchies with minimal developer effort.

## Package Information

- **Package Name**: github.com/alecthomas/kong
- **Package Type**: golang
- **Language**: Go
- **Version**: v1.13.0
- **License**: MIT
- **Installation**: `go get github.com/alecthomas/kong@v1.13.0`

## Core Imports

```go
import "github.com/alecthomas/kong"
```

## Basic Usage

```go
package main

import (
    "github.com/alecthomas/kong"
)

// Define your CLI structure
type CLI struct {
    Debug bool `help:"Enable debug mode."`

    Install struct {
        Package string `arg:"" name:"package" help:"Package to install."`
        Force   bool   `help:"Force installation."`
    } `cmd:"" help:"Install a package."`

    Remove struct {
        Package string `arg:"" name:"package" help:"Package to remove."`
    } `cmd:"" help:"Remove a package."`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // Execute the selected command
    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

## Architecture

Kong uses a **declarative grammar model** where CLI structure is expressed as Go types:

- **Struct fields** become flags and positional arguments
- **Nested structs** with `cmd` tag become subcommands
- **Struct tags** configure behavior (help text, defaults, validation, etc.)
- **Parser** builds an internal model from the struct and parses arguments against it
- **Context** represents the parse result and provides execution methods

Key components:
- **Grammar Definition**: Go structs with tags define the CLI structure
- **Parser (Kong)**: Builds and validates the grammar model
- **Context**: Contains parse results and execution methods
- **Mappers**: Convert string arguments to Go types
- **Resolvers**: Load configuration from external sources (files, environment)
- **Hooks**: Lifecycle callbacks for custom logic

## Capabilities

### Core Parsing

Create parsers and parse command-line arguments.

```go { .api }
// Creates a new Kong parser on the provided grammar structure.
// Grammar must be a pointer to a struct.
func New(grammar any, options ...Option) (*Kong, error)

// Creates a new Parser or panics if there is an error.
func Must(ast any, options ...Option) *Kong

// Global convenience function that constructs a Kong parser and calls Parse on it.
// Exits on error.
func Parse(cli any, options ...Option) *Context
```

[Core Parsing Documentation](./core-parsing.md)

### Model Types

Types representing the parsed CLI structure.

```go { .api }
// The root of the Kong model
type Application struct {
    *Node
    HelpFlag *Flag  // Help flag, if NoDefaultHelp() option not specified
}

// A branch in the CLI (command or positional argument)
type Node struct {
    Type       NodeType
    Parent     *Node
    Name       string
    Help       string
    Detail     string
    Flags      []*Flag
    Positional []*Positional
    Children   []*Node
    Target     reflect.Value
    // ... additional fields
}

// Either a flag or a variable positional argument
type Value struct {
    Name         string
    Help         string
    Default      string
    Required     bool
    Mapper       Mapper
    Target       reflect.Value
    // ... additional fields
}
```

[Model Types Documentation](./model.md)

### Configuration Options

Customize parser behavior with extensive options.

```go { .api }
type Option interface {
    Apply(k *Kong) error
}

// Key option functions:
func Name(name string) Option
func Description(description string) Option
func ConfigureHelp(options HelpOptions) Option
func Bind(args ...any) Option
func Resolvers(resolvers ...Resolver) Option
func DefaultEnvars(prefix string) Option
func UsageOnError() Option
```

[Options Documentation](./options.md)

### Type Mappers

Convert command-line strings to Go types.

```go { .api }
// Represents how a field is mapped from command-line values to Go
type Mapper interface {
    Decode(ctx *DecodeContext, target reflect.Value) error
}

// Registry contains a set of mappers and supporting lookup methods
type Registry struct {
    // methods for registering and looking up mappers
}

// Context passed to a Mapper's Decode()
type DecodeContext struct {
    Value *Value
    Scan  *Scanner
}
```

[Mappers Documentation](./mappers.md)

### Scanner and Tokenization

Low-level token scanning for command-line arguments.

```go { .api }
// A stack-based scanner over command-line tokens
type Scanner struct {
    // methods for manipulating token stream
}

// Token created by Scanner
type Token struct {
    Value any
    Type  TokenType
}

// Creates a new Scanner from args with untyped tokens
func Scan(args ...string) *Scanner
```

[Scanner Documentation](./scanner.md)

### Help System

Comprehensive help text generation and customization.

```go { .api }
// Options for HelpPrinters
type HelpOptions struct {
    NoAppSummary       bool
    Summary            bool
    Compact            bool
    Tree               bool
    FlagsLast          bool
    Indenter           HelpIndenter
    NoExpandSubcommands bool
    WrapUpperBound     int
    ValueFormatter     HelpValueFormatter
}

// The default HelpPrinter implementation
func DefaultHelpPrinter(options HelpOptions, ctx *Context) error
```

[Help System Documentation](./help.md)

### Resolvers

Load configuration from external sources.

```go { .api }
// Resolves a Flag value from an external source
type Resolver interface {
    Validate(app *Application) error
    Resolve(context *Context, parent *Path, flag *Flag) (any, error)
}

// Returns a Resolver that retrieves values from a JSON source
func JSON(r io.Reader) (Resolver, error)
```

[Resolvers Documentation](./resolvers.md)

### Hooks and Lifecycle

Execute custom logic at various parsing stages.

```go { .api }
// Hook interface called before values are reset to defaults
type BeforeReset interface {
    BeforeReset(ctx *Context) error
}

// Hook interface called before resolvers are applied
type BeforeResolve interface {
    BeforeResolve(ctx *Context) error
}

// Hook interface called before values are applied to the target
type BeforeApply interface {
    BeforeApply(ctx *Context) error
}

// Hook interface called after values are applied and validated
type AfterApply interface {
    AfterApply(ctx *Context) error
}
```

[Hooks Documentation](./hooks.md)

### Tags

Struct tag parsing and configuration.

```go { .api }
// Represents the parsed state of Kong tags in a struct field tag
type Tag struct {
    Ignored      bool
    Cmd          bool
    Arg          bool
    Required     bool
    Name         string
    Help         string
    Default      string
    Short        rune
    Envs         []string
    Hidden       bool
    // ... additional fields
}

// Indicates how parameters are passed through
type PassthroughMode int
```

[Tags Documentation](./tags.md)

### Error Handling

Error types and exit code handling.

```go { .api }
// The error type returned by Kong.Parse()
type ParseError struct {
    error
    Context *Context
}

// May be implemented by an error value to provide an integer exit code
type ExitCoder interface {
    ExitCode() int
}
```

[Error Handling Documentation](./errors.md)

### Utilities

Helper types and functions for common patterns.

```go { .api }
// Uses configured loader to load configuration from a file
type ConfigFlag string

// A flag type that displays a version number
type VersionFlag bool

// Changes working directory early in parsing process
type ChangeDirFlag string

// Helper to expand relative or home-relative paths
func ExpandPath(path string) string
```

[Utilities Documentation](./utilities.md)
