# Help System

This document covers Kong's comprehensive help system, including help configuration, custom help providers, and help formatting.

## Help Configuration

### HelpOptions

Options for configuring help output.

```go { .api }
// HelpOptions are options for HelpPrinters
type HelpOptions struct {
    // NoAppSummary don't print top-level usage summary
    NoAppSummary bool

    // Summary write a one-line summary of the context
    Summary bool

    // Compact write help in a more compact form
    Compact bool

    // Tree write command chains in a tree structure
    Tree bool

    // FlagsLast place the flags after the commands listing
    FlagsLast bool

    // Indenter modulates the given prefix for the next layer in tree view
    Indenter HelpIndenter

    // NoExpandSubcommands don't show the help associated with subcommands
    NoExpandSubcommands bool

    // WrapUpperBound clamp the help wrap width to a value smaller than
    // the terminal width
    WrapUpperBound int

    // ValueFormatter used to format the help text of flags and positional
    // arguments
    ValueFormatter HelpValueFormatter
}
```

### HelpOptions Methods

```go { .api }
// Apply applies options to Kong as a configuration option
func (h HelpOptions) Apply(k *Kong) error

// CommandTree creates a tree with the given node name as root
func (h HelpOptions) CommandTree(node *Node, prefix string) [][2]string
```

## Help Function Types

### HelpPrinter

Function type used to print help.

```go { .api }
// HelpPrinter is used to print context-sensitive help
type HelpPrinter func(options HelpOptions, ctx *Context) error
```

### HelpValueFormatter

Function type used to format help text for values.

```go { .api }
// HelpValueFormatter is used to format the help text of flags and
// positional arguments
type HelpValueFormatter func(value *Value) string
```

### HelpIndenter

Function type used to indent help tree layers.

```go { .api }
// HelpIndenter is used to indent new layers in the help tree
type HelpIndenter func(prefix string) string
```

## Default Help Functions

### Help Printers

```go { .api }
// DefaultHelpPrinter is the default HelpPrinter implementation that
// prints comprehensive help information
func DefaultHelpPrinter(options HelpOptions, ctx *Context) error

// DefaultShortHelpPrinter is the default HelpPrinter for short help on error
func DefaultShortHelpPrinter(options HelpOptions, ctx *Context) error
```

### Value Formatter

```go { .api }
// DefaultHelpValueFormatter is the default HelpValueFormatter that formats
// help text for flags and positional arguments
func DefaultHelpValueFormatter(value *Value) string
```

### Indenter Functions

```go { .api }
// SpaceIndenter adds a space indent to the given prefix for help tree formatting
func SpaceIndenter(prefix string) string

// LineIndenter adds line points to every new indent for help tree formatting
func LineIndenter(prefix string) string

// TreeIndenter adds line points to every new indent and vertical lines to
// every layer for help tree formatting
func TreeIndenter(prefix string) string
```

## Help Provider Interfaces

### HelpProvider

Interface for commands/args to provide detailed help.

```go { .api }
// HelpProvider can be implemented by commands/args to provide detailed help
type HelpProvider interface {
    // Help returns help string (formatted by go/doc)
    Help() string
}
```

### PlaceHolderProvider

Interface for mappers to provide custom placeholder text.

```go { .api }
// PlaceHolderProvider can be implemented by mappers to provide custom
// placeholder text
type PlaceHolderProvider interface {
    PlaceHolder(flag *Flag) string
}
```

## Usage Examples

### Basic Help Configuration

```go
package main

import (
    "github.com/alecthomas/kong"
)

type CLI struct {
    Debug bool `help:"Enable debug mode."`

    Serve struct {
        Port int `help:"Port to listen on." default:"8080"`
    } `cmd:"" help:"Start the server."`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.Name("myapp"),
        kong.Description("A simple application"),
        kong.ConfigureHelp(kong.HelpOptions{
            Compact: true,
            Summary: false,
        }),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Tree-Style Help

```go
func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.ConfigureHelp(kong.HelpOptions{
            Tree:     true,
            Indenter: kong.TreeIndenter,
        }),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Compact Help with Flags Last

```go
func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.ConfigureHelp(kong.HelpOptions{
            Compact:   true,
            FlagsLast: true,
        }),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Custom Help Printer

```go
func customHelpPrinter(options kong.HelpOptions, ctx *kong.Context) error {
    fmt.Fprintln(ctx.Stdout, "=== Custom Help ===")
    fmt.Fprintf(ctx.Stdout, "Command: %s\n", ctx.Command())
    fmt.Fprintln(ctx.Stdout)

    // Print flags
    fmt.Fprintln(ctx.Stdout, "Flags:")
    for _, flag := range ctx.Flags() {
        fmt.Fprintf(ctx.Stdout, "  --%s: %s\n", flag.Name, flag.Help)
    }

    return nil
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.Help(customHelpPrinter),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Custom Value Formatter

```go
func customValueFormatter(value *kong.Value) string {
    result := value.Name

    // Add type information
    if value.IsBool() {
        result += " (bool)"
    } else if value.IsSlice() {
        result += " (list)"
    } else if value.IsMap() {
        result += " (map)"
    }

    // Add default
    if value.HasDefault {
        result += fmt.Sprintf(" [default: %s]", value.Default)
    }

    // Add required marker
    if value.Required {
        result += " [required]"
    }

    return result
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.ValueFormatter(customValueFormatter),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Implementing HelpProvider

```go
type ServeCmd struct {
    Port int `help:"Port to listen on." default:"8080"`
}

// Implement HelpProvider interface for detailed help
func (s *ServeCmd) Help() string {
    return `
The serve command starts the application server.

The server will listen on the specified port and handle incoming requests.
It supports graceful shutdown on SIGTERM and SIGINT signals.

Examples:
  myapp serve --port 8080
  myapp serve --port 9000

Environment Variables:
  PORT - Override the default port
`
}

func (s *ServeCmd) Run() error {
    fmt.Printf("Starting server on port %d\n", s.Port)
    return nil
}

type CLI struct {
    Serve ServeCmd `cmd:"" help:"Start the server."`
}

func main() {
    var cli CLI
    ctx := kong.Parse(&cli)

    // Detailed help will be shown with: myapp serve --help
    err := ctx.Run()
    ctx.FatalIfErrorf(err)
}
```

### Custom Placeholder Provider

```go
import "reflect"

type URLMapper struct{}

func (u *URLMapper) Decode(ctx *kong.DecodeContext, target reflect.Value) error {
    var s string
    if err := ctx.Scan.PopValueInto("url", &s); err != nil {
        return err
    }

    // Parse URL
    parsed, err := url.Parse(s)
    if err != nil {
        return err
    }

    target.Set(reflect.ValueOf(parsed))
    return nil
}

// Implement PlaceHolderProvider
func (u *URLMapper) PlaceHolder(flag *kong.Flag) string {
    return "https://example.com"
}

type CLI struct {
    API *url.URL `help:"API endpoint URL."`
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.TypeMapper(reflect.TypeOf(&url.URL{}), &URLMapper{}),
    )

    // Help will show: --api=https://example.com
    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Short Help on Error

```go
func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.ShortUsageOnError(),
    )

    ctx, err := parser.Parse(os.Args[1:])
    if err != nil {
        // Short usage will be automatically printed
        parser.FatalIfErrorf(err)
    }
}
```

### Manual Help Printing

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli)

    ctx, err := parser.Parse(os.Args[1:])
    if err != nil {
        parser.FatalIfErrorf(err)
    }

    // Manually print help
    if needsHelp() {
        // Print full help
        err = ctx.PrintUsage(false)
        if err != nil {
            panic(err)
        }

        // Or print summary
        err = ctx.PrintUsage(true)
        if err != nil {
            panic(err)
        }
    }
}

func needsHelp() bool {
    // Custom logic
    return false
}
```

### Different Indenter Styles

```go
// Space indenter (default)
func exampleSpaceIndenter() {
    var cli CLI
    parser := kong.Must(&cli,
        kong.ConfigureHelp(kong.HelpOptions{
            Tree:     true,
            Indenter: kong.SpaceIndenter,
        }),
    )
    // Output:
    // Commands:
    //   serve    Start the server
    //     start  Start serving
}

// Line indenter
func exampleLineIndenter() {
    var cli CLI
    parser := kong.Must(&cli,
        kong.ConfigureHelp(kong.HelpOptions{
            Tree:     true,
            Indenter: kong.LineIndenter,
        }),
    )
    // Output:
    // Commands:
    // ├─serve    Start the server
    // └──start  Start serving
}

// Tree indenter
func exampleTreeIndenter() {
    var cli CLI
    parser := kong.Must(&cli,
        kong.ConfigureHelp(kong.HelpOptions{
            Tree:     true,
            Indenter: kong.TreeIndenter,
        }),
    )
    // Output:
    // Commands:
    // ├─serve     Start the server
    // │ └─start   Start serving
    // └─version   Show version
}
```

### Custom Indenter

```go
func customIndenter(prefix string) string {
    // Add custom indentation logic
    return prefix + ">> "
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.ConfigureHelp(kong.HelpOptions{
            Tree:     true,
            Indenter: customIndenter,
        }),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Wrapping Help Text

```go
func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.ConfigureHelp(kong.HelpOptions{
            // Limit help text width to 80 columns
            WrapUpperBound: 80,
        }),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### No Subcommand Expansion

```go
func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.ConfigureHelp(kong.HelpOptions{
            // Don't show help for subcommands in parent help
            NoExpandSubcommands: true,
        }),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Building Command Tree

```go
func main() {
    var cli CLI
    parser := kong.Must(&cli)

    options := kong.HelpOptions{
        Tree:     true,
        Indenter: kong.TreeIndenter,
    }

    // Get command tree for a specific node
    tree := options.CommandTree(&parser.Model.Node, "")

    // tree is [][2]string where each element is [prefix, text]
    for _, item := range tree {
        fmt.Printf("%s%s\n", item[0], item[1])
    }
}
```

### Combining Help Options

```go
func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.Name("myapp"),
        kong.Description("A comprehensive example"),
        kong.ConfigureHelp(kong.HelpOptions{
            Compact:             true,
            Tree:                true,
            FlagsLast:           true,
            Indenter:            kong.TreeIndenter,
            NoExpandSubcommands: false,
            WrapUpperBound:      100,
            ValueFormatter:      customValueFormatter,
        }),
        kong.UsageOnError(),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Disabling Default Help

```go
func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.NoDefaultHelp(),
    )

    // No --help flag will be available
    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```

### Custom Short Help

```go
func customShortHelp(options kong.HelpOptions, ctx *kong.Context) error {
    fmt.Fprintf(ctx.Stderr, "Error! Usage: %s <command> [flags]\n", ctx.Model.Name)
    fmt.Fprintf(ctx.Stderr, "Try '%s --help' for more information.\n", ctx.Model.Name)
    return nil
}

func main() {
    var cli CLI

    parser := kong.Must(&cli,
        kong.ShortHelp(customShortHelp),
        kong.ShortUsageOnError(),
    )

    ctx, err := parser.Parse(os.Args[1:])
    parser.FatalIfErrorf(err)
}
```
